/* Quant Core dashboard. Plain JavaScript, no build step.
 *
 * Talks to one of two back ends, which it learns from api/meta.json:
 *   live   - `qc dashboard`: POST api/backtest runs a backtest on request.
 *   static - an export (`qc dashboard --export`): every default run is a file
 *            under api/runs/, so strategy, asset and commission can change
 *            but parameters and cash cannot.
 */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const MINUS = "−";
  const RECENT_MAX = 8;
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const store = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem("qc." + key);
        return raw == null ? fallback : JSON.parse(raw);
      } catch (_) {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem("qc." + key, JSON.stringify(value));
      } catch (_) {
        /* storage may be unavailable; the page works without it */
      }
    },
  };

  const state = {
    meta: null,
    mode: "live",
    result: null,
    view: "equity",
    activeTrade: null,
    hoverIndex: null,
    busy: false,
    params: {}, // strategy name -> {param: value} as typed
    geom: null, // last chart geometry, for hover
  };

  // ------------------------------------------------------------ formatting
  const signed = (s, x) => (x < 0 ? MINUS + s : x > 0 ? "+" + s : s);
  function fmtFixed(x, digits) {
    return Math.abs(x).toLocaleString("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
  function fmtPct(x, opts = {}) {
    if (x == null) return "–";
    const d = opts.digits ?? 2;
    const body = fmtFixed(x, d) + "%";
    if (opts.signed) return signed(body, x);
    return x < 0 ? MINUS + body : body;
  }
  function fmtNum(x, digits = 2, withSign = false) {
    if (x == null) return "–";
    const body = fmtFixed(x, digits);
    if (withSign) return signed(body, x);
    return x < 0 ? MINUS + body : body;
  }
  function fmtUsd(x, digits = 2, withSign = false) {
    if (x == null) return "–";
    const body = "$" + fmtFixed(x, digits);
    if (withSign) return signed(body, x);
    return x < 0 ? MINUS + body : body;
  }
  function fmtUsdShort(x) {
    const a = Math.abs(x);
    const s = a >= 1e6 ? "$" + (a / 1e6).toFixed(a >= 1e7 ? 0 : 1) + "M"
      : a >= 1e3 ? "$" + (a / 1e3).toFixed(a >= 1e5 ? 0 : a % 1000 === 0 ? 0 : 1) + "k"
      : "$" + a.toFixed(0);
    return x < 0 ? MINUS + s : s;
  }
  function fmtUnit(x, unit) {
    if (x == null) return "–";
    switch (unit) {
      case "pct": return fmtPct(x);
      case "usd": return fmtUsd(x);
      case "count": return fmtNum(x, 0);
      case "days": return fmtNum(x, 0) + (Math.round(x) === 1 ? " day" : " days");
      default: return fmtNum(x, 2);
    }
  }
  function parseDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return { y, m: m - 1, d };
  }
  function fmtDate(iso, withYear = true) {
    const { y, m, d } = parseDate(iso);
    return withYear ? `${d} ${MONTHS[m]} ${y}` : `${d} ${MONTHS[m]}`;
  }
  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  // --------------------------------------------------------------- helpers
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children) if (c != null) node.append(c);
    return node;
  }
  const strategyByName = (name) => state.meta.strategies.find((s) => s.name === name);
  const isTyping = (t) =>
    t && (t.tagName === "INPUT" || t.tagName === "SELECT" || t.tagName === "TEXTAREA" || t.isContentEditable);
  const anyDialogOpen = () => $("palette").open || $("keys").open;
  const today = () => new Date().toISOString().slice(0, 10);
  const CUSTOM = "custom";

  // First and last dates of an asset's data. A ticker with no local file is
  // downloaded from meta.download_from up to today.
  function assetRange(asset) {
    const r = state.meta.asset_ranges && state.meta.asset_ranges[asset];
    return r ? { first: r[0], last: r[1] } : { first: state.meta.download_from || "2015-01-01", last: today() };
  }

  // Mirrors service.resolve_period: a named period ends on the last bar.
  function periodWindow(period, asset) {
    const { first, last } = assetRange(asset);
    let start = first;
    if (period === "ytd") start = last.slice(0, 4) + "-01-01";
    else {
      const spec = (state.meta.periods || []).find((p) => p.id === period);
      if (spec && spec.years) {
        const d = new Date(last + "T00:00:00Z");
        d.setUTCFullYear(d.getUTCFullYear() - spec.years);
        d.setUTCDate(d.getUTCDate() + 1);
        start = d.toISOString().slice(0, 10);
      }
    }
    return { start: start < first ? first : start, end: last };
  }

  function periodLabel(req) {
    if (req.period === CUSTOM) return `${req.start || "start"} to ${req.end || "end"}`;
    const spec = (state.meta.periods || []).find((p) => p.id === req.period);
    return spec ? spec.label : "Full history";
  }

  function onPeriodChange() {
    const custom = $("f-period").value === CUSTOM;
    $("field-dates").hidden = !custom;
    $("field-dates-end").hidden = !custom;
    const asset = (assetInput().value || "").trim().toUpperCase();
    const { first, last } = assetRange(asset);
    for (const id of ["f-start", "f-end"]) {
      $(id).min = first;
      $(id).max = last;
    }
    if (custom && !$("f-start").value) {
      const w = periodWindow("1y", asset);
      $("f-start").value = w.start;
      $("f-end").value = w.end;
    }
  }

  // ------------------------------------------------------------------ theme
  function applyTheme(theme) {
    if (theme === "light" || theme === "dark") document.documentElement.setAttribute("data-theme", theme);
  }
  function currentTheme() {
    const set = document.documentElement.getAttribute("data-theme");
    if (set === "light" || set === "dark") return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function toggleTheme() {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store.set("theme", next);
    drawChart();
    renderRecent();
  }

  // ------------------------------------------------------------- controls
  function fillSelect(select, items, selected) {
    select.replaceChildren(
      ...items.map((it) => el("option", { value: it.value, text: it.label, selected: it.value === selected }))
    );
  }

  function populateControls(config) {
    const m = state.meta;
    const standalone = m.strategies.filter((s) => !s.needs_underlying && s.data_assets === 1);
    fillSelect($("f-strategy"), m.strategies.map((s) => ({ value: s.name, label: s.label })), config.strategy);
    fillSelect($("f-underlying"), standalone.map((s) => ({ value: s.name, label: s.label })), config.underlying);
    const assetItems = m.assets.map((a) => ({ value: a, label: a }));
    fillSelect($("f-asset"), assetItems, config.asset);
    fillSelect($("f-asset2"), assetItems, config.asset2 || m.assets.find((a) => a !== config.asset));
    $("asset-list").replaceChildren(...m.assets.map((a) => el("option", { value: a })));
    $("f-asset-text").value = config.asset || "";
    fillSelect($("f-commission"), m.commissions.map((c) => ({ value: c, label: c })), config.commission);
    $("f-cash").value = config.cash;
    const periods = (m.periods || []).map((p) => ({ value: p.id, label: p.label }));
    if (state.mode === "live") periods.push({ value: CUSTOM, label: "Custom dates" });
    fillSelect($("f-period"), periods, config.period || m.defaults.period || "all");
    $("f-start").value = config.start || "";
    $("f-end").value = config.end || "";

    const live = state.mode === "live";
    $("f-asset").hidden = live;
    $("f-asset-text").hidden = !live;
    $("f-asset").id = live ? "f-asset-select" : "f-asset";
    $("f-asset-text").id = live ? "f-asset" : "f-asset-text";
    $("f-cash").disabled = !live;
    onStrategyChange();
  }

  function assetInput() {
    return $("f-asset");
  }

  function onStrategyChange() {
    const s = strategyByName($("f-strategy").value);
    if (!s) return;
    $("field-underlying").hidden = !s.needs_underlying;
    $("field-asset2").hidden = s.data_assets !== 2;
    renderParams(s);
  }

  function renderParams(s) {
    const values = state.params[s.name] || {};
    const live = state.mode === "live";
    for (const group of ["strategy", "risk"]) {
      const host = $("params-" + group);
      const params = s.params.filter((p) => p.group === group);
      host.replaceChildren(
        ...params.map((p) => {
          const id = "p-" + p.name;
          const value = values[p.name] ?? p.default;
          let input;
          if (p.kind === "bool") {
            input = el("select", { id, class: "control", "data-param": p.name, disabled: !live });
            fillSelect(input, [{ value: "true", label: "true" }, { value: "false", label: "false" }], String(value));
          } else {
            input = el("input", {
              id,
              class: "control mono",
              "data-param": p.name,
              type: p.kind === "str" ? "text" : "number",
              step: p.kind === "int" ? "1" : "any",
              value: String(value),
              disabled: !live,
            });
          }
          input.addEventListener("input", () => {
            state.params[s.name] = { ...(state.params[s.name] || {}), [p.name]: input.value };
            updateRiskHint(s);
          });
          return el("div", { class: "field" }, el("label", { for: id, text: p.name }), input);
        })
      );
      if (group === "strategy") {
        host.parentElement.hidden = params.length === 0;
      } else {
        $("risk-block").hidden = params.length === 0;
      }
    }
    updateRiskHint(s);
  }

  function paramValue(s, name) {
    const p = s.params.find((q) => q.name === name);
    if (!p) return null;
    const typed = (state.params[s.name] || {})[name];
    const v = typed == null || typed === "" ? p.default : Number(typed);
    return Number.isFinite(v) ? v : null;
  }

  function updateRiskHint(s) {
    const risk = paramValue(s, "risk_percent");
    const stop = paramValue(s, "stop_loss_pct");
    const hint = $("risk-hint");
    if (risk == null || stop == null) {
      hint.textContent = "";
      return;
    }
    if (stop <= 0) {
      hint.textContent = "With no stop, each entry commits all available equity.";
      return;
    }
    const frac = Math.min(1, risk / stop);
    hint.textContent =
      `Each entry commits ${fmtPct(frac * 100, { digits: 0 })} of equity: ` +
      `a ${fmtPct(risk * 100, { digits: 1 })} loss if the ${fmtPct(stop * 100, { digits: 1 })} stop is hit.`;
  }

  function resetParams() {
    const s = strategyByName($("f-strategy").value);
    if (!s) return;
    delete state.params[s.name];
    renderParams(s);
  }

  function readRequest() {
    const s = strategyByName($("f-strategy").value);
    const asset = (assetInput().value || "").trim().toUpperCase();
    const req = {
      strategy: s ? s.name : "",
      assets: [asset],
      commission: $("f-commission").value,
      cash: Number($("f-cash").value) || state.meta.defaults.cash,
      params: {},
      period: $("f-period").value || "all",
    };
    if (s && s.data_assets === 2) req.assets.push($("f-asset2").value);
    if (s && s.needs_underlying) req.underlying = $("f-underlying").value;
    if (state.mode === "live") {
      if (req.period === CUSTOM) {
        req.start = $("f-start").value || null;
        req.end = $("f-end").value || null;
      } else if (req.period !== "all") {
        const w = periodWindow(req.period, asset);
        req.start = w.start;
        req.end = w.end;
      }
      for (const p of s ? s.params : []) {
        const typed = (state.params[s.name] || {})[p.name];
        if (typed == null || typed === "" || String(typed) === String(p.default)) continue;
        req.params[p.name] = p.kind === "str" ? typed : p.kind === "bool" ? typed === "true" : Number(typed);
      }
    }
    return req;
  }

  function applyRequest(req) {
    const s = strategyByName(req.strategy);
    if (!s) return false;
    $("f-strategy").value = s.name;
    assetInput().value = req.assets[0] || "";
    if (req.assets[1]) $("f-asset2").value = req.assets[1];
    if (req.underlying) $("f-underlying").value = req.underlying;
    if (req.commission && state.meta.commissions.includes(req.commission)) $("f-commission").value = req.commission;
    const periodOk = [...$("f-period").options].some((o) => o.value === req.period);
    $("f-period").value = periodOk ? req.period : state.meta.defaults.period || "all";
    if (req.period === CUSTOM) {
      $("f-start").value = req.start || "";
      $("f-end").value = req.end || "";
    }
    onPeriodChange();
    if (state.mode === "live") {
      if (req.cash) $("f-cash").value = req.cash;
      state.params[s.name] = Object.fromEntries(Object.entries(req.params || {}).map(([k, v]) => [k, String(v)]));
    }
    onStrategyChange();
    return true;
  }

  // ------------------------------------------------------------------ run
  function periodToken(req) {
    return req.period === CUSTOM ? `${req.start || ""}~${req.end || ""}` : req.period || "all";
  }

  function requestKey(req) {
    return [req.strategy, ...req.assets, slug(req.commission), periodToken(req)].join(".");
  }

  function showError(message) {
    const box = $("alert");
    box.textContent = message;
    box.hidden = !message;
  }

  function setBusy(busy) {
    state.busy = busy;
    $("result").setAttribute("aria-busy", String(busy));
    $("run-btn").disabled = busy;
    $("run-label").textContent = busy ? "Running" : "Run";
  }

  async function run(req = readRequest()) {
    if (state.busy) return;
    if (!req.strategy) return showError("Choose a strategy to run.");
    if (!req.assets[0]) return showError("Choose an asset to run it on.");
    if (req.assets.length === 2 && req.assets[0] === req.assets[1]) {
      return showError("Choose two different assets for a pairs strategy.");
    }
    showError("");
    setBusy(true);
    try {
      let result;
      if (state.mode === "static") {
        const key = `${req.strategy}__${req.assets[0]}__${slug(req.commission)}__${req.period || "all"}`;
        const res = await fetch(`api/runs/${encodeURIComponent(key)}.json`);
        if (!res.ok) {
          throw new Error(
            `This copy has no precomputed run of ${strategyByName(req.strategy).label} on ${req.assets[0]} ` +
              `for ${periodLabel(req).toLowerCase()}. Pick one of the listed options, or run qc dashboard locally.`
          );
        }
        result = await res.json();
      } else {
        const res = await fetch("api/backtest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(req),
        });
        const body = await res.json().catch(() => ({ error: `The server answered ${res.status}.` }));
        if (!res.ok) throw new Error(body.error || `The server answered ${res.status}.`);
        result = body;
      }
      state.result = result;
      state.activeTrade = null;
      state.hoverIndex = null;
      render();
      remember(req, result);
      store.set("last", req);
      try {
        history.replaceState(null, "", "#" + requestKey(req));
      } catch (_) {
        /* some frames refuse history changes */
      }
    } catch (err) {
      showError(err.message || String(err));
    } finally {
      setBusy(false);
    }
  }

  // --------------------------------------------------------------- render
  function render() {
    const r = state.result;
    if (!r) return;
    const run = r.run;
    const m = r.metrics;
    const h = r.hold;

    $("r-eyebrow").textContent =
      `${fmtDate(run.first_date)} to ${fmtDate(run.last_date)} · ${run.bars} daily bars · ` +
      `${run.commission} · ${fmtUsd(run.cash, 0)} start`;
    const title = $("r-title");
    title.replaceChildren(
      document.createTextNode(run.label + (run.underlying ? ` over ${strategyLabel(run.underlying)}` : "") + " "),
      el("span", { class: "on", text: "on" }),
      document.createTextNode(" " + run.assets.join(" / "))
    );
    document.title = `${run.label} on ${run.assets.join("/")} · Quant Core`;
    $("r-lede").textContent = r.summary[0] || "";

    renderKpis(m, h, r);
    renderLegend();
    drawChart();
    renderTrades(r);
    renderStats(r);
    renderStory(r);
    renderRepro(run);
  }

  const strategyLabel = (name) => (strategyByName(name) || { label: name }).label;

  function chip(diff, unit, goodWhenHigher = true) {
    if (diff == null) return null;
    const tiny = unit === "pp" ? Math.abs(diff) < 0.005 : Math.abs(diff) < 0.005;
    const cls = tiny ? "chip" : (diff > 0) === goodWhenHigher ? "chip good" : "chip bad";
    const text = unit === "pp" ? fmtNum(diff, 2, true) + " pp" : fmtNum(diff, 2, true);
    return el("span", { class: cls, text: tiny ? "even" : text });
  }

  const KPI_DEFS = {
    return: "Change in equity from the first bar to the last, after commission.",
    sharpe: "Annual return divided by annual volatility. Higher means more return for each unit of risk.",
    max_drawdown: "The largest fall from a peak in equity to a later low.",
    win_rate: "Share of closed trades that made money after commission.",
  };

  function renderKpis(m, h, r) {
    const trades = r.trades.length;
    const won = r.trades.filter((t) => t.pnl > 0).length;
    const isHold = r.run.strategy === "BuyAndHoldStrategy";
    const cards = [
      {
        key: "return",
        label: "Return",
        value: fmtPct(m.return, { signed: true }),
        chip: isHold ? null : chip(m.return != null && h.return != null ? m.return - h.return : null, "pp"),
        note: isHold ? "" : "vs buy and hold",
      },
      {
        key: "sharpe",
        label: "Sharpe ratio",
        value: fmtNum(m.sharpe, 2),
        chip: isHold ? null : chip(m.sharpe != null && h.sharpe != null ? m.sharpe - h.sharpe : null, ""),
        note: isHold ? "" : "vs buy and hold",
      },
      {
        key: "max_drawdown",
        label: "Max drawdown",
        value: fmtPct(m.max_drawdown),
        chip: isHold ? null : chip(
          m.max_drawdown != null && h.max_drawdown != null ? m.max_drawdown - h.max_drawdown : null,
          "pp"
        ),
        note: isHold ? "" : "shallower is better",
      },
      {
        key: "win_rate",
        label: "Win rate",
        value: trades ? fmtPct(m.win_rate, { digits: 1 }) : "–",
        chip: trades ? el("span", { class: "chip", text: `${won} of ${trades}` }) : null,
        note: trades ? "trades won" : "no closed trades",
      },
    ];
    $("kpis").replaceChildren(
      ...cards.map((c) =>
        el(
          "button",
          {
            type: "button",
            class: "kpi",
            title: KPI_DEFS[c.key] + " Select for all statistics.",
            onclick: () => openStat(c.key),
          },
          el("span", { class: "kpi-label", text: c.label }),
          el("span", { class: "kpi-value", text: c.value }),
          el("span", { class: "kpi-foot" }, c.chip, document.createTextNode(c.note))
        )
      )
    );
  }

  function openStat(key) {
    const d = $("d-stats");
    d.open = true;
    const row = $("stat-" + key);
    if (!row) return;
    row.scrollIntoView({ block: "center", behavior: reduceMotion ? "auto" : "smooth" });
    row.classList.remove("flash");
    void row.offsetWidth;
    row.classList.add("flash");
    setTimeout(() => row.classList.remove("flash"), 1600);
  }

  function renderTrades(r) {
    const trades = r.trades;
    const won = trades.filter((t) => t.pnl > 0).length;
    const commission = r.metrics.commission_paid || 0;
    $("d-trades-meta").textContent = trades.length
      ? `${trades.length} closed · ${won} won · ${fmtUsd(commission)} commission`
      : "No closed trades";
    const body = $("trades-table").tBodies[0];
    body.replaceChildren(
      ...trades.map((t, i) => {
        const cls = t.pnl > 0 ? "pos" : t.pnl < 0 ? "neg" : "";
        const row = el(
          "tr",
          {
            tabindex: "0",
            "aria-selected": state.activeTrade === i ? "true" : "false",
            onclick: () => selectTrade(i),
            onkeydown: (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                selectTrade(i);
              }
            },
          },
          el("td", { text: String(i + 1) }),
          el("td", {}, el("span", { class: "side", text: t.side === "long" ? "Long" : "Short" })),
          el("td", { text: t.entry }),
          el("td", { text: t.exit }),
          el("td", { class: "num", text: String(t.days) }),
          el("td", { class: "num", text: String(t.size) }),
          el("td", { class: "num", text: fmtNum(t.entry_price, 2) }),
          el("td", { class: "num", text: fmtNum(t.exit_price, 2) }),
          el("td", { class: "num " + cls, text: fmtPct(t.return_pct, { signed: true }) }),
          el("td", { class: "num " + cls, text: fmtNum(t.pnl, 2, true) })
        );
        return row;
      })
    );
    const table = $("trades-table");
    if (table.tFoot) table.tFoot.remove();
    if (trades.length) {
      const total = trades.reduce((a, t) => a + t.pnl, 0);
      const foot = table.createTFoot();
      foot.append(
        el(
          "tr",
          {},
          el("td", { colspan: "9", text: "Net, after commission" }),
          el("td", { class: "num " + (total >= 0 ? "pos" : "neg"), text: fmtNum(total, 2, true) })
        )
      );
    }
  }

  function selectTrade(i) {
    state.activeTrade = state.activeTrade === i ? null : i;
    for (const [j, row] of [...$("trades-table").tBodies[0].rows].entries()) {
      row.setAttribute("aria-selected", j === state.activeTrade ? "true" : "false");
    }
    if (state.activeTrade != null) setView("price", false);
    else drawChart();
    $("chart-wrap").scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
  }

  function renderStats(r) {
    let count = 0;
    const isHold = r.run.strategy === "BuyAndHoldStrategy";
    $("stat-groups").replaceChildren(
      ...r.groups.map((g) => {
        count += g.rows.length;
        const head = el(
          "tr",
          {},
          el("th", { scope: "col", text: "" }),
          el("th", { scope: "col", text: r.run.label }),
          isHold ? null : el("th", { scope: "col", text: "Hold" })
        );
        const rows = g.rows.map((row) =>
          el(
            "tr",
            { id: "stat-" + row.key },
            el("td", { text: row.label }),
            el("td", { text: fmtUnit(row.value, row.unit) }),
            isHold ? null : el("td", { class: "hold", text: fmtUnit(row.hold, row.unit) })
          )
        );
        return el(
          "section",
          { class: "stat-group" },
          el("h3", { text: g.title }),
          el("table", { class: "stat-table" }, el("thead", {}, head), el("tbody", {}, ...rows))
        );
      })
    );
    $("d-stats-meta").textContent = isHold
      ? `${count} measures`
      : `${count} measures, each beside buy and hold`;
  }

  function renderStory(r) {
    const lines = r.summary;
    $("story").replaceChildren(
      ...lines.map((line, i) => el("p", { class: i === lines.length - 1 ? "caveat" : null, text: line }))
    );
  }

  function renderRepro(run) {
    $("command").textContent = run.command;
    const rows = [
      ["strategy", run.strategy],
      ...(run.underlying ? [["underlying", run.underlying]] : []),
      ["data", run.sources.join(", ")],
      ["commission", run.commission],
      ["cash", fmtUsd(run.cash, 0)],
      ...Object.entries(run.params).map(([k, v]) => [k, String(v)]),
    ];
    $("run-params").replaceChildren(
      ...rows.map(([k, v]) => el("div", {}, el("dt", { text: k }), el("dd", { text: v })))
    );
  }

  async function copyCommand() {
    const text = $("command").textContent;
    const btn = $("copy-command");
    const done = (label) => {
      btn.textContent = label;
      setTimeout(() => (btn.textContent = "Copy"), 1600);
    };
    try {
      await navigator.clipboard.writeText(text);
      done("Copied");
    } catch (_) {
      const range = document.createRange();
      range.selectNodeContents($("command"));
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      done("Selected");
    }
  }

  // ---------------------------------------------------------------- chart
  function setView(view, focus = false) {
    state.view = view;
    for (const b of $("views").querySelectorAll("button")) {
      b.setAttribute("aria-checked", b.dataset.view === view ? "true" : "false");
    }
    renderLegend();
    drawChart();
    if (focus) $("views").querySelector(`[data-view="${view}"]`).focus();
  }

  function renderLegend() {
    const r = state.result;
    if (!r) return;
    const asset = r.run.assets[0];
    const item = (keyClass, color, text) =>
      el("span", { class: "legend-item" }, el("span", { class: "legend-key " + keyClass, style: `color:${color}` }), text);
    const legend = $("legend");
    if (state.view === "price") {
      legend.replaceChildren(
        item("", "var(--ink-2)", `${asset} close`),
        item("dot", "var(--accent)", "Entry"),
        item("dot", "var(--up)", "Winning exit"),
        item("dot", "var(--down)", "Losing exit")
      );
    } else {
      const parts = [item("", "var(--accent)", r.run.label), item("dashed", "var(--hold)", `Hold ${asset}`)];
      if (state.view === "equity" && r.trades.length) parts.push(item("box", "var(--accent)", "In a trade"));
      legend.replaceChildren(...parts);
    }
    state.noteBase = {
      equity: `Account value in dollars, from ${fmtUsd(r.run.cash, 0)}. Hover or use the arrow keys to read values.`,
      drawdown: "How far equity sat below its previous peak, in percent.",
      price: "Daily close, with each trade's entry and exit. Select a trade in the table to highlight it.",
    }[state.view];
  }

  function drawdown(series) {
    let peak = -Infinity;
    return series.map((v) => {
      peak = Math.max(peak, v);
      return (v / peak - 1) * 100;
    });
  }

  function niceStep(span, count) {
    const raw = span / Math.max(1, count);
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const norm = raw / mag;
    const step = norm >= 5 ? 10 : norm >= 2.5 ? 5 : norm >= 2 ? 2.5 : norm >= 1 ? 2 : 1;
    return step * mag;
  }

  function niceTicks(min, max, count) {
    if (min === max) {
      min -= 1;
      max += 1;
    }
    const step = niceStep(max - min, count);
    const lo = Math.floor(min / step) * step;
    const hi = Math.ceil(max / step) * step;
    const ticks = [];
    for (let v = lo; v <= hi + step / 2; v += step) ticks.push(Number(v.toPrecision(12)));
    return { lo, hi, ticks };
  }

  // Ticks at 1, 2 and 5 times powers of ten, thinned to at most maxTicks.
  function logTicks(min, max, maxTicks) {
    const all = [];
    for (let e = Math.floor(Math.log10(min)); e <= Math.ceil(Math.log10(max)); e++) {
      for (const k of [1, 2, 5]) {
        const v = k * Math.pow(10, e);
        if (v >= min && v <= max) all.push(Number(v.toPrecision(6)));
      }
    }
    let ticks = all;
    if (ticks.length > maxTicks) ticks = all.filter((v) => /^1(0*)$/.test(String(v).replace(".", "")) || String(v)[0] === "1");
    if (ticks.length > maxTicks) ticks = ticks.filter((_, i) => i % Math.ceil(ticks.length / maxTicks) === 0);
    if (ticks.length < 2) return { lo: min, hi: max, ticks: niceTicks(min, max, maxTicks).ticks.filter((v) => v >= min && v <= max) };
    return { lo: min, hi: max, ticks };
  }

  function monthTicks(dates, maxLabels) {
    const starts = [];
    let prev = null;
    dates.forEach((iso, i) => {
      const key = iso.slice(0, 7);
      if (key !== prev) {
        if (prev !== null) starts.push(i);
        prev = key;
      }
    });
    const stepMonths = [1, 2, 3, 6, 12].find((s) => Math.ceil(starts.length / s) <= maxLabels) || 12;
    return starts.filter((i) => {
      const { m } = parseDate(dates[i]);
      return m % stepMonths === 0;
    });
  }

  function viewSeries(r) {
    const s = r.series;
    if (state.view === "drawdown") {
      return {
        lines: [
          { cls: "s-hold", area: "area-hold", values: drawdown(s.hold), name: `Hold ${r.run.assets[0]}`, color: "var(--hold)", dashed: true },
          { cls: "s-strategy", area: "area-strategy", values: drawdown(s.equity), name: r.run.label, color: "var(--accent)" },
        ],
        fmt: (v) => fmtPct(v, { digits: 1 }),
        fmtTick: (v) => (v === 0 ? "0%" : fmtNum(v, Math.abs(v) < 1 ? 1 : 0) + "%"),
        areaTo: 0,
        includeZero: true,
      };
    }
    if (state.view === "price") {
      return {
        lines: [{ cls: "s-price", values: s.close, name: `${r.run.assets[0]} close`, color: "var(--ink-2)" }],
        fmt: (v) => fmtUsd(v, 2),
        fmtTick: (v) => fmtNum(v, v >= 100 ? 0 : 2),
        markers: true,
        logable: true,
      };
    }
    return {
      lines: [
        { cls: "s-hold", values: s.hold, name: `Hold ${r.run.assets[0]}`, color: "var(--hold)", dashed: true },
        { cls: "s-strategy", area: "area-strategy", values: s.equity, name: r.run.label, color: "var(--accent)" },
      ],
      fmt: (v) => fmtUsd(v, 2),
      fmtTick: fmtUsdShort,
      areaTo: "bottom",
      logable: true,
      bands: true,
      reference: r.run.cash,
    };
  }

  function drawChart() {
    const r = state.result;
    const svg = $("chart");
    if (!r) return;
    const W = svg.clientWidth || 800;
    const H = svg.clientHeight || 300;
    const narrow = W < 520;
    const pad = { l: narrow ? 46 : 58, r: 12, t: 10, b: 26 };
    const spec = viewSeries(r);
    const dates = r.series.dates;
    const n = dates.length;

    let min = Infinity;
    let max = -Infinity;
    for (const line of spec.lines) {
      for (const v of line.values) {
        if (v < min) min = v;
        if (v > max) max = v;
      }
    }
    if (spec.includeZero) max = 0;
    // Prices and equity that grow several-fold read truthfully only on a log
    // scale, where equal distances are equal percentage moves.
    const log = spec.logable && min > 0 && max / min > 2.5;
    state.logScale = log;
    let lo, hi, ticks;
    if (log) {
      ({ lo, hi, ticks } = logTicks(min / 1.04, max * 1.04, narrow ? 4 : 6));
    } else {
      const span = max - min || Math.abs(max) || 1;
      if (!spec.includeZero) {
        min -= span * 0.04;
        max += span * 0.04;
      } else {
        min -= span * 0.04;
      }
      ({ lo, hi, ticks } = niceTicks(min, max, narrow ? 4 : 5));
    }
    const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, n - 1);
    const f = log ? Math.log : (v) => v;
    const y = (v) => pad.t + ((f(hi) - f(v)) * (H - pad.t - pad.b)) / (f(hi) - f(lo) || 1);
    state.geom = { x, y, pad, W, H, n, spec };

    const parts = [];
    // grid and y labels
    for (const t of ticks) {
      const ty = y(t).toFixed(1);
      const base = spec.reference === t || (spec.includeZero && t === 0);
      parts.push(`<line class="${base ? "baseline" : "grid"}" x1="${pad.l}" x2="${W - pad.r}" y1="${ty}" y2="${ty}"></line>`);
      parts.push(`<text x="${pad.l - 8}" y="${ty}" text-anchor="end" dominant-baseline="middle">${spec.fmtTick(t)}</text>`);
    }
    // x labels
    const months = monthTicks(dates, narrow ? 4 : 7);
    for (const [k, i] of months.entries()) {
      const { y: yr, m } = parseDate(dates[i]);
      const label = m === 0 || k === 0 ? `${MONTHS[m]} ${yr}` : MONTHS[m];
      const tx = x(i);
      if (tx > W - pad.r - 20) continue;
      parts.push(`<line class="grid" x1="${tx.toFixed(1)}" x2="${tx.toFixed(1)}" y1="${H - pad.b}" y2="${H - pad.b + 4}"></line>`);
      parts.push(`<text x="${tx.toFixed(1)}" y="${H - 6}" text-anchor="${k === 0 && tx - pad.l < 30 ? "start" : "middle"}">${label}</text>`);
    }
    // trade spans
    if (spec.bands || spec.markers) {
      r.trades.forEach((t, i) => {
        const x0 = x(t.entry_bar);
        const w = Math.max(2, x(t.exit_bar) - x0);
        const active = state.activeTrade === i ? " active" : "";
        parts.push(`<rect class="band${active}" x="${x0.toFixed(1)}" y="${pad.t}" width="${w.toFixed(1)}" height="${H - pad.t - pad.b}"></rect>`);
      });
    }
    // areas and lines
    const bottom = H - pad.b;
    for (const line of spec.lines) {
      const pts = line.values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
      if (line.area) {
        const base = spec.areaTo === 0 ? y(0) : bottom;
        parts.push(`<polygon class="${line.area}" points="${x(0).toFixed(1)},${base.toFixed(1)} ${pts} ${x(n - 1).toFixed(1)},${base.toFixed(1)}"></polygon>`);
      }
      parts.push(`<polyline class="${line.cls}" points="${pts}"></polyline>`);
    }
    // markers
    if (spec.markers) {
      r.trades.forEach((t) => {
        const ex = x(t.entry_bar);
        const ey = y(t.entry_price);
        const up = t.side === "long";
        const tri = up
          ? `${ex.toFixed(1)},${(ey - 6).toFixed(1)} ${(ex - 5.5).toFixed(1)},${(ey + 4).toFixed(1)} ${(ex + 5.5).toFixed(1)},${(ey + 4).toFixed(1)}`
          : `${ex.toFixed(1)},${(ey + 6).toFixed(1)} ${(ex - 5.5).toFixed(1)},${(ey - 4).toFixed(1)} ${(ex + 5.5).toFixed(1)},${(ey - 4).toFixed(1)}`;
        parts.push(`<polygon class="m-entry" points="${tri}"></polygon>`);
        parts.push(`<circle class="${t.pnl >= 0 ? "m-exit-win" : "m-exit-loss"}" cx="${x(t.exit_bar).toFixed(1)}" cy="${y(t.exit_price).toFixed(1)}" r="4.5"></circle>`);
      });
    } else {
      // endpoint emphasis
      for (const line of spec.lines) {
        const v = line.values[n - 1];
        parts.push(`<circle class="end-dot" cx="${x(n - 1).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4" style="fill:${line.color}"></circle>`);
      }
    }
    parts.push('<g id="hover-layer"></g>');
    parts.push(`<rect id="hit" x="${pad.l}" y="${pad.t}" width="${W - pad.l - pad.r}" height="${H - pad.t - pad.b}" fill="transparent"></rect>`);

    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = parts.join("");
    svg.setAttribute("aria-label", chartLabel(r, spec));
    $("chart-note").textContent =
      (state.noteBase || "") + (log ? " Log scale: equal heights are equal percentage moves." : "");
    if (state.hoverIndex != null) showHover(state.hoverIndex);
  }

  function chartLabel(r, spec) {
    const n = r.series.dates.length;
    const describe = (line) => `${line.name} ends at ${spec.fmt(line.values[n - 1])}`;
    const view = { equity: "Equity", drawdown: "Drawdown", price: "Price" }[state.view];
    return `${view} chart, ${fmtDate(r.series.dates[0])} to ${fmtDate(r.series.dates[n - 1])}. ` +
      spec.lines.map(describe).join("; ") + ".";
  }

  function tradeAt(i) {
    const r = state.result;
    const idx = r.trades.findIndex((t) => i >= t.entry_bar && i <= t.exit_bar);
    return idx === -1 ? null : idx;
  }

  function showHover(i) {
    const g = state.geom;
    const r = state.result;
    if (!g || !r) return;
    i = Math.max(0, Math.min(g.n - 1, i));
    state.hoverIndex = i;
    const layer = document.getElementById("hover-layer");
    if (!layer) return;
    const cx = g.x(i);
    const dots = g.spec.lines
      .map((line) => `<circle class="hover-dot" cx="${cx.toFixed(1)}" cy="${g.y(line.values[i]).toFixed(1)}" r="4.5" style="fill:${line.color}"></circle>`)
      .join("");
    layer.innerHTML = `<line class="crosshair" x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="${g.pad.t}" y2="${g.H - g.pad.b}"></line>${dots}`;

    const tip = $("tooltip");
    const rows = [...g.spec.lines]
      .reverse()
      .map((line) =>
        el(
          "div",
          { class: "tt-row" },
          el("span", { class: "tt-key" + (line.dashed ? " dashed" : ""), style: `color:${line.color}` }),
          el("span", { class: "tt-val", text: g.spec.fmt(line.values[i]) }),
          el("span", { class: "tt-name", text: line.name })
        )
      );
    const children = [el("div", { class: "tt-date", text: fmtDate(r.series.dates[i]) }), ...rows];
    const t = tradeAt(i);
    if (t != null) {
      const trade = r.trades[t];
      const what = i === trade.entry_bar ? "entry" : i === trade.exit_bar ? "exit" : "held";
      children.push(
        el("div", {
          class: "tt-extra",
          text: `Trade ${t + 1}, ${what} · ${fmtPct(trade.return_pct, { signed: true })}, ${fmtUsd(trade.pnl, 2, true)}`,
        })
      );
    }
    tip.replaceChildren(...children);
    tip.hidden = false;
    const wrap = $("chart-wrap").getBoundingClientRect();
    const tw = tip.offsetWidth;
    let left = cx + 14;
    if (left + tw > wrap.width) left = cx - tw - 14;
    tip.style.left = `${Math.max(0, left)}px`;
    tip.style.top = `${g.pad.t + 4}px`;
  }

  function hideHover() {
    state.hoverIndex = null;
    const layer = document.getElementById("hover-layer");
    if (layer) layer.innerHTML = "";
    $("tooltip").hidden = true;
  }

  function onChartPointer(e) {
    const g = state.geom;
    if (!g) return;
    const rect = $("chart").getBoundingClientRect();
    const px = ((e.clientX - rect.left) * g.W) / rect.width;
    const frac = (px - g.pad.l) / (g.W - g.pad.l - g.pad.r);
    if (frac < -0.02 || frac > 1.02) return hideHover();
    showHover(Math.round(frac * (g.n - 1)));
  }

  function onChartKey(e) {
    const g = state.geom;
    if (!g) return;
    const cur = state.hoverIndex ?? g.n - 1;
    const step = e.shiftKey ? 20 : 1;
    const map = { ArrowLeft: cur - step, ArrowRight: cur + step, Home: 0, End: g.n - 1 };
    if (e.key in map) {
      e.preventDefault();
      showHover(map[e.key]);
    } else if (e.key === "Escape") {
      hideHover();
    }
  }

  // ---------------------------------------------------------- recent runs
  function remember(req, result) {
    const eq = result.series.equity;
    const step = Math.max(1, Math.floor(eq.length / 40));
    const spark = eq.filter((_, i) => i % step === 0).concat(eq[eq.length - 1]);
    const entry = {
      key: requestKey(req) + (Object.keys(req.params || {}).length ? "." + JSON.stringify(req.params) : ""),
      req,
      label: result.run.label,
      assets: result.run.assets.join("/"),
      span: `${result.run.first_date.slice(0, 4)}\u2013${result.run.last_date.slice(2, 4)}`,
      ret: result.metrics.return,
      spark,
    };
    const list = recentRuns().filter((x) => x.key !== entry.key);
    list.unshift(entry);
    store.set("recent", list.slice(0, RECENT_MAX));
    state.currentKey = entry.key;
    renderRecent();
  }

  // Entries come from this browser's storage; keep only well-formed ones.
  function recentRuns() {
    if (!state.meta) return [];
    const list = store.get("recent", []);
    return (Array.isArray(list) ? list : []).filter(
      (x) =>
        x && x.req && typeof x.label === "string" && typeof x.assets === "string" &&
        Array.isArray(x.req.assets) && strategyByName(x.req.strategy) &&
        Array.isArray(x.spark) && x.spark.length > 1 && x.spark.every(Number.isFinite)
    );
  }

  function renderRecent() {
    const list = recentRuns();
    $("recent-empty").hidden = list.length > 0;
    $("recent").replaceChildren(
      ...list.map((x) => {
        const lo = Math.min(...x.spark);
        const hi = Math.max(...x.spark);
        const pts = x.spark
          .map((v, i) => `${((i * 60) / (x.spark.length - 1)).toFixed(1)},${(20 - ((v - lo) / (hi - lo || 1)) * 18).toFixed(1)}`)
          .join(" ");
        const spark = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        spark.setAttribute("viewBox", "0 0 60 22");
        spark.setAttribute("preserveAspectRatio", "none");
        spark.setAttribute("class", "recent-spark");
        spark.setAttribute("aria-hidden", "true");
        spark.innerHTML = `<polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="1.6" vector-effect="non-scaling-stroke" stroke-linejoin="round"></polyline>`;
        return el(
          "li",
          {},
          el(
            "button",
            {
              type: "button",
              class: "recent-btn",
              "aria-current": x.key === state.currentKey ? "true" : "false",
              onclick: () => {
                if (applyRequest(x.req)) run(readRequest());
              },
            },
            el(
              "span",
              { class: "recent-text" },
              el("span", { class: "recent-name", text: x.label }),
              el("span", {
                class: "recent-sub",
                text: `${x.assets} \u00b7 ${x.span ? x.span + " \u00b7 " : ""}${fmtPct(x.ret, { signed: true })}`,
              })
            ),
            spark
          )
        );
      })
    );
  }

  // ------------------------------------------------------ command palette
  const ACTIONS = [
    { title: "Show trades", hint: "T", run: () => toggleDetails("d-trades", true) },
    { title: "Show all statistics", hint: "M", run: () => toggleDetails("d-stats", true) },
    { title: "Show what happened", hint: "W", run: () => toggleDetails("d-story", true) },
    { title: "Show the reproduce command", hint: "", run: () => toggleDetails("d-repro", true) },
    { title: "Copy the reproduce command", hint: "C", run: () => copyCommand() },
    { title: "Equity chart", hint: "1", run: () => setView("equity") },
    { title: "Drawdown chart", hint: "2", run: () => setView("drawdown") },
    { title: "Price and trades chart", hint: "3", run: () => setView("price") },
    { title: "Open settings", hint: ",", run: () => toggleSettings(true) },
    { title: "Switch colour theme", hint: "", run: () => toggleTheme() },
    { title: "Keyboard shortcuts", hint: "?", run: () => $("keys").showModal() },
  ];

  const COMMISSION_WORDS = [
    [/^(zero|free|nocost|no-cost)$/, (c) => /zero/i.test(c)],
    [/^(ibkr|tiered|ib)$/, (c) => /ibkr|tiered/i.test(c)],
    [/^0?\.1%?$/, (c) => /0\.1%/.test(c)],
    [/^0?\.5%?$/, (c) => /0\.5%/.test(c)],
  ];

  function parseCommand(text) {
    const m = state.meta;
    const raw = text.trim().split(/\s+/).filter(Boolean);
    const out = { strategy: null, assets: [], commission: null, cash: null, params: {}, period: null, used: new Set() };
    for (const tok of raw) {
      const low = tok.toLowerCase();
      const kv = low.match(/^([a-z_][a-z0-9_]*)=(.+)$/);
      if (kv) {
        if (kv[1] === "cash") out.cash = Number(kv[2].replace(/[$,_k]/g, "")) * (/k$/.test(kv[2]) ? 1000 : 1);
        else out.params[kv[1]] = kv[2];
        out.used.add(tok);
        continue;
      }
      const cash = low.match(/^\$(\d[\d,_]*)(k?)$/);
      if (cash) {
        out.cash = Number(cash[1].replace(/[,_]/g, "")) * (cash[2] ? 1000 : 1);
        out.used.add(tok);
        continue;
      }
      const preset = low === "full" ? "all" : (m.periods || []).some((p) => p.id === low) ? low : null;
      if (preset) {
        out.period = preset;
        out.used.add(tok);
        continue;
      }
      const years = low.match(/^(\d{4})(?:-(\d{4}))?$/);
      if (years && state.mode === "live") {
        Object.assign(out, { period: CUSTOM, start: `${years[1]}-01-01`, end: `${years[2] || years[1]}-12-31` });
        out.used.add(tok);
        continue;
      }
      const comm = COMMISSION_WORDS.find(([re]) => re.test(low));
      if (comm) {
        const name = m.commissions.find(comm[1]);
        if (name) {
          out.commission = name;
          out.used.add(tok);
          continue;
        }
      }
      if (m.assets.includes(tok.toUpperCase())) {
        out.assets.push(tok.toUpperCase());
        out.used.add(tok);
        continue;
      }
      if (low.length >= 2 && !out.strategy) {
        const hit = m.strategies.find((s) => {
          const words = s.label.toLowerCase().split(/\s+/).concat(s.name.toLowerCase());
          return words.some((w) => w.startsWith(low));
        });
        if (hit) {
          out.strategy = hit.name;
          out.used.add(tok);
          continue;
        }
      }
      if (state.mode === "live" && /^[A-Z][A-Z0-9.\-^]{0,7}$/.test(tok)) {
        out.assets.push(tok);
        out.used.add(tok);
      }
    }
    return out;
  }

  function paletteItems(text) {
    const items = [];
    const q = text.trim().toLowerCase();
    if (q) {
      const p = parseCommand(text);
      if (p.strategy || p.assets.length || p.period) {
        const current = readRequest();
        const s = strategyByName(p.strategy || current.strategy);
        let assets = p.assets.length ? p.assets : current.assets;
        if (s.data_assets === 2 && assets.length < 2) assets = [assets[0], current.assets[1] || state.meta.assets.find((a) => a !== assets[0])];
        if (s.data_assets === 1) assets = assets.slice(0, 1);
        const req = {
          ...current,
          strategy: s.name,
          assets,
          commission: p.commission || current.commission,
          cash: p.cash || current.cash,
          params: { ...current.params, ...p.params },
        };
        if (p.period) Object.assign(req, { period: p.period, start: p.start || null, end: p.end || null });
        const extras = [periodLabel(req), req.commission];
        if (state.mode === "live") {
          extras.push(fmtUsd(req.cash, 0));
          for (const [k, v] of Object.entries(p.params)) extras.push(`${k}=${v}`);
        } else if (p.cash || Object.keys(p.params).length) {
          extras.push("cash and parameters are fixed in this copy");
        }
        items.push({
          kind: "Run",
          title: `Run ${s.label} on ${assets.join(" / ")}`,
          sub: extras.join(" · "),
          run: () => {
            applyRequest(req);
            run(readRequest());
          },
        });
      }
    }
    for (const a of ACTIONS) {
      if (!q || q.split(/\s+/).every((w) => a.title.toLowerCase().includes(w))) {
        items.push({ kind: a.hint ? a.hint : "", title: a.title, sub: "", run: a.run });
      }
    }
    for (const x of recentRuns()) {
      const title = `Open ${x.label} on ${x.assets}`;
      if (q && !q.split(/\s+/).every((w) => title.toLowerCase().includes(w))) continue;
      if (!strategyByName(x.req.strategy)) continue;
      items.push({
        kind: "Recent",
        title,
        sub: `${x.req.commission} · ${fmtPct(x.ret, { signed: true })}`,
        run: () => {
          applyRequest(x.req);
          run(readRequest());
        },
      });
    }
    return items.slice(0, 12);
  }

  let paletteState = { items: [], index: 0 };

  function renderPalette() {
    const text = $("palette-input").value;
    paletteState.items = paletteItems(text);
    paletteState.index = Math.min(paletteState.index, Math.max(0, paletteState.items.length - 1));
    const list = $("palette-list");
    if (!paletteState.items.length) {
      list.replaceChildren(el("li", { class: "palette-item", "aria-disabled": "true" }, el("span", { class: "pi-sub", text: "No match. Try a strategy and an asset, such as rsi spy." })));
      return;
    }
    list.replaceChildren(
      ...paletteState.items.map((it, i) =>
        el(
          "li",
          {
            class: "palette-item",
            role: "option",
            id: "pi-" + i,
            "aria-selected": i === paletteState.index ? "true" : "false",
            onmousemove: () => {
              if (paletteState.index !== i) {
                paletteState.index = i;
                renderPalette();
              }
            },
            onclick: () => executePalette(i),
          },
          el(
            "span",
            { class: "pi-main" },
            el("span", { class: "pi-title", text: it.title }),
            it.sub ? el("span", { class: "pi-sub", text: it.sub }) : null
          ),
          el("span", { class: "pi-kind", text: it.kind })
        )
      )
    );
    $("palette-input").setAttribute("aria-activedescendant", "pi-" + paletteState.index);
  }

  function openPalette(prefill = "") {
    if ($("palette").open) return;
    $("palette-input").value = prefill;
    paletteState.index = 0;
    renderPalette();
    $("palette").showModal();
    $("palette-input").focus();
  }

  function executePalette(i) {
    const it = paletteState.items[i];
    $("palette").close();
    if (it) it.run();
  }

  // ------------------------------------------------------------ disclosure
  function toggleDetails(id, forceOpen) {
    const d = $(id);
    d.open = forceOpen === undefined ? !d.open : forceOpen;
    if (d.open) d.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
  }

  function toggleSettings(forceOpen) {
    const panel = $("settings");
    const open = forceOpen === undefined ? panel.hidden : forceOpen;
    panel.hidden = !open;
    $("toggle-settings").setAttribute("aria-expanded", String(open));
    if (open) {
      const first = panel.querySelector("select:not(:disabled), input:not(:disabled)");
      if (first) first.focus();
    }
  }

  // ------------------------------------------------------------- keyboard
  function onKey(e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      return openPalette();
    }
    if (anyDialogOpen() || e.metaKey || e.ctrlKey || e.altKey) return;
    if (isTyping(e.target)) {
      if (e.key === "Escape") e.target.blur();
      return;
    }
    const actions = {
      "/": () => openPalette(),
      "?": () => $("keys").showModal(),
      r: () => run(),
      s: () => $("f-strategy").focus(),
      a: () => assetInput().focus(),
      ",": () => toggleSettings(),
      1: () => setView("equity"),
      2: () => setView("drawdown"),
      3: () => setView("price"),
      t: () => toggleDetails("d-trades"),
      m: () => toggleDetails("d-stats"),
      w: () => toggleDetails("d-story"),
      c: () => {
        toggleDetails("d-repro", true);
        copyCommand();
      },
      Escape: () => toggleSettings(false),
    };
    const fn = actions[e.key] || actions[e.key.toLowerCase()];
    if (fn && !(e.target.closest && e.target.closest("summary") && e.key === " ")) {
      e.preventDefault();
      fn();
    }
  }

  // ------------------------------------------------------------------ boot
  function initialRequest() {
    const m = state.meta;
    const hash = decodeURIComponent(location.hash.slice(1));
    if (hash) {
      const [strategy, ...rest] = hash.split(".");
      const s = strategyByName(strategy);
      if (s) {
        const assets = rest.slice(0, s.data_assets).map((a) => a.toUpperCase());
        const commission = m.commissions.find((c) => slug(c) === rest[s.data_assets]) || m.defaults.commission;
        const token = rest[s.data_assets + 1] || m.defaults.period || "all";
        const req = { strategy, assets, commission, cash: m.defaults.cash, params: {}, period: token };
        if (token.includes("~")) {
          const [start, end] = token.split("~");
          Object.assign(req, { period: CUSTOM, start: start || null, end: end || null });
        }
        if (assets.length === s.data_assets) return req;
      }
    }
    const last = store.get("last", null);
    if (last && strategyByName(last.strategy) && (state.mode === "live" || m.assets.includes(last.assets[0]))) {
      return last;
    }
    return {
      strategy: m.defaults.strategy,
      assets: [m.defaults.asset],
      commission: m.defaults.commission,
      cash: m.defaults.cash,
      params: {},
      period: m.defaults.period || "all",
    };
  }

  function bind() {
    $("runbar").addEventListener("submit", (e) => {
      e.preventDefault();
      run();
    });
    $("f-strategy").addEventListener("change", onStrategyChange);
    $("f-period").addEventListener("change", onPeriodChange);
    // Both asset controls: the live mode swaps which one is labelled f-asset.
    $("f-asset").addEventListener("change", onPeriodChange);
    $("f-asset-text").addEventListener("change", onPeriodChange);
    $("toggle-settings").addEventListener("click", () => toggleSettings());
    $("reset-params").addEventListener("click", resetParams);
    $("copy-command").addEventListener("click", copyCommand);
    $("open-palette").addEventListener("click", () => openPalette());
    $("open-keys").addEventListener("click", () => $("keys").showModal());
    $("close-keys").addEventListener("click", () => $("keys").close());
    $("theme-toggle").addEventListener("click", toggleTheme);
    for (const b of $("views").querySelectorAll("button")) b.addEventListener("click", () => setView(b.dataset.view));
    $("views").addEventListener("keydown", (e) => {
      const order = ["equity", "drawdown", "price"];
      const i = order.indexOf(state.view);
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        setView(order[(i + (e.key === "ArrowRight" ? 1 : 2)) % 3], true);
      }
    });
    const chart = $("chart");
    chart.addEventListener("pointermove", onChartPointer);
    chart.addEventListener("pointerdown", onChartPointer);
    chart.addEventListener("pointerleave", hideHover);
    chart.addEventListener("keydown", onChartKey);
    chart.addEventListener("focus", () => showHover(state.hoverIndex ?? (state.geom ? state.geom.n - 1 : 0)));
    chart.addEventListener("blur", hideHover);
    $("palette-input").addEventListener("input", () => {
      paletteState.index = 0;
      renderPalette();
    });
    $("palette-input").addEventListener("keydown", (e) => {
      const n = paletteState.items.length;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!n) return;
        paletteState.index = (paletteState.index + (e.key === "ArrowDown" ? 1 : n - 1)) % n;
        renderPalette();
        const node = $("pi-" + paletteState.index);
        if (node) node.scrollIntoView({ block: "nearest" });
      }
    });
    $("palette-form").addEventListener("submit", (e) => {
      e.preventDefault();
      executePalette(paletteState.index);
    });
    for (const d of [$("palette"), $("keys")]) {
      d.addEventListener("click", (e) => {
        if (e.target === d) d.close();
      });
    }
    document.addEventListener("keydown", onKey);
    if ("ResizeObserver" in window) new ResizeObserver(() => drawChart()).observe($("chart-wrap"));
    else window.addEventListener("resize", drawChart);
    const mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
    $("palette-kbd").textContent = mac ? "⌘K" : "Ctrl K";
  }

  async function boot() {
    applyTheme(store.get("theme", null));
    bind();
    try {
      const res = await fetch("api/meta.json", { cache: "no-store" });
      if (!res.ok) throw new Error(`api/meta.json answered ${res.status}`);
      state.meta = await res.json();
    } catch (err) {
      $("mode-badge").textContent = "Offline";
      setBusy(false);
      showError(`Could not load the dashboard's data (${err.message}). Start it with qc dashboard.`);
      return;
    }
    const m = state.meta;
    state.mode = m.mode === "static" ? "static" : "live";
    document.body.classList.add(state.mode + "-mode");
    const badge = $("mode-badge");
    badge.dataset.mode = state.mode;
    badge.textContent = state.mode === "static" ? "Hosted demo" : "Live";
    badge.title = state.mode === "static"
      ? "Every run here was computed ahead of time at default settings."
      : "Runs are computed by the local qc dashboard server.";
    $("version").textContent = "quant-core " + (m.version || "");
    for (const e of m.errors || []) console.warn(e);

    if (!m.strategies.length) {
      setBusy(false);
      return showError("No strategies are installed. Install quant-core, or a package that registers strategies.");
    }
    if (!m.assets.length && state.mode === "static") {
      setBusy(false);
      return showError("This copy was exported without any price data.");
    }
    const req = initialRequest();
    populateControls({
      strategy: req.strategy,
      asset: req.assets[0],
      asset2: req.assets[1],
      underlying: req.underlying,
      commission: req.commission || m.defaults.commission,
      cash: req.cash || m.defaults.cash,
      period: req.period || m.defaults.period,
      start: req.start,
      end: req.end,
    });
    applyRequest(req);
    renderRecent();
    if (!m.assets.length) {
      setBusy(false);
      showError(
        `No price data in ${m.data_dir}. Type a ticker such as SPY and press Run to download a year of it, ` +
          `or fetch data first with qc download.`
      );
      return;
    }
    setBusy(false);
    run(readRequest());
  }

  boot();
})();
