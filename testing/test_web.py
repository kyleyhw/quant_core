"""
The dashboard's service module, web server and static export.

Runs on a synthetic price file written to a temporary folder, so it needs no
data from the repository and works from an installed wheel.
"""

import json
import shlex
import threading
import urllib.error
import urllib.request

import pytest

from quant_core import service
from quant_core.backtest import run_backtest
from quant_core.web import server


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory, ohlcv):
    folder = tmp_path_factory.mktemp("prices")
    ohlcv.rename_axis("Date").to_csv(folder / "FIX_2020-01-01_2021-12-31.csv")
    ohlcv.rename_axis("Date").mul(1.5).to_csv(folder / "ALT_2020-01-01_2021-12-31.csv")
    return folder


@pytest.fixture(scope="module")
def result(data_dir):
    return service.run_backtest("SimpleMACrossover", ["FIX"], data_dir=data_dir)


# --- service ----------------------------------------------------------------
def test_meta_lists_public_strategies_with_parameters(data_dir):
    meta = service.meta(data_dir)
    by_name = {s["name"]: s for s in meta["strategies"]}
    assert {"SimpleMACrossover", "BollingerBandsStrategy", "RSI2PeriodStrategy"} <= set(by_name)
    params = {p["name"]: p for p in by_name["BollingerBandsStrategy"]["params"]}
    assert params["bb_period"] == {
        "name": "bb_period",
        "default": 20,
        "kind": "int",
        "group": "strategy",
    }
    assert params["stop_loss_pct"]["group"] == "risk"
    assert meta["assets"] == ["ALT", "FIX"]
    assert meta["defaults"]["strategy"] == "BollingerBandsStrategy"
    assert meta["defaults"]["asset"] == "ALT"


def test_labels_read_as_names():
    assert service._label("BollingerBandsStrategy") == "Bollinger Bands"
    assert service._label("SimpleMACrossover") == "Simple MA Crossover"
    assert service._label("BuyAndHoldStrategy") == "Buy and Hold"


def test_result_is_consistent(result):
    m, series = result["metrics"], result["series"]
    assert (
        len(series["dates"]) == len(series["equity"]) == len(series["hold"]) == len(series["close"])
    )
    assert series["equity"][-1] == pytest.approx(m["equity_final"], abs=0.01)
    assert m["trades"] == len(result["trades"])
    assert sum(t["pnl"] for t in result["trades"]) == pytest.approx(
        m["equity_final"] - result["run"]["cash"], abs=0.05
    )
    for t in result["trades"]:
        assert 0 <= t["entry_bar"] <= t["exit_bar"] < len(series["dates"])
        assert series["dates"][t["entry_bar"]] == t["entry"]
    assert [g["title"] for g in result["groups"]] == [
        "Returns",
        "Risk",
        "Trade quality",
        "Run details",
    ]
    json.dumps(result)  # JSON-ready: no NaN, timestamps or numpy types


def test_hold_baseline_blanks_what_it_cannot_measure(result):
    assert result["hold"]["trades"] is None
    assert result["hold"]["exposure"] is None
    assert result["hold"]["return"] is not None


def test_summary_states_the_headline(result):
    first = result["summary"][0]
    assert first.startswith("Simple MA Crossover on FIX returned")
    assert "Buying and holding FIX" in first
    assert result["summary"][-1].startswith("This is one period of history")


def test_reproduce_command_gives_the_same_numbers(result, tmp_path, capsys):
    argv = shlex.split(result["run"]["command"])
    assert argv[:2] == ["qc", "backtest"]
    run_backtest.main(argv[2:] + ["--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    line = next(ln for ln in out.splitlines() if ln.startswith("Return [%]"))
    assert float(line.split()[-1]) == pytest.approx(result["metrics"]["return"], abs=1e-4)


def test_parameter_overrides_are_applied_and_reproducible(data_dir):
    r = service.run_backtest(
        "SimpleMACrossover",
        ["FIX"],
        params={"fast_ma_period": "5", "stop_loss_pct": 0.03},
        data_dir=data_dir,
    )
    assert r["run"]["params"]["fast_ma_period"] == 5
    assert r["run"]["params"]["stop_loss_pct"] == 0.03
    assert "--param fast_ma_period=5" in r["run"]["command"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"strategy": "Nope", "assets": ["FIX"]}, "Unknown strategy"),
        ({"strategy": "SimpleMACrossover", "assets": ["ZZZ"]}, "No local data for ZZZ"),
        ({"strategy": "SimpleMACrossover", "assets": ["FIX", "ALT"]}, "trades 1 asset"),
        (
            {"strategy": "SimpleMACrossover", "assets": ["FIX"], "params": {"nope": 1}},
            "no parameter",
        ),
        (
            {"strategy": "SimpleMACrossover", "assets": ["FIX"], "params": {"fast_ma_period": "x"}},
            "must be an int",
        ),
        ({"strategy": "SimpleMACrossover", "assets": ["FIX"], "commission": "Free"}, "commission"),
        ({"strategy": "SimpleMACrossover", "assets": ["../../etc/x"]}, "is not a ticker"),
        (
            {"strategy": "SimpleMACrossover", "assets": ["NEW"], "start": "2024", "end": "2025"},
            "must be YYYY-MM-DD",
        ),
        ({"strategy": "SimpleMACrossover", "assets": ["FIX"], "params": [1]}, "must be an object"),
    ],
)
def test_bad_requests_explain_themselves(data_dir, kwargs, message):
    with pytest.raises(service.RunError, match=message):
        service.run_backtest(data_dir=data_dir, **kwargs)


def test_best_stretch_names_the_months_that_made_the_money():
    trades = [
        {"exit": "2024-11-10", "pnl": 10.0},
        {"exit": "2025-03-03", "pnl": 200.0},
        {"exit": "2025-03-20", "pnl": 150.0},
        {"exit": "2025-09-01", "pnl": -20.0},
    ]
    line = service.best_stretch(trades)
    assert line == (
        "The 2 trades that closed in March 2025 made $350.00. "
        "The other 2 trades lost $10.00, leaving $340.00."
    )
    assert service.best_stretch(trades[:3] + [{"exit": "2025-12-01", "pnl": -400.0}]) is None


# --- server -----------------------------------------------------------------
@pytest.fixture(scope="module")
def base_url(data_dir):
    httpd = server.make_server("127.0.0.1", 0, data_dir, quiet=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def _get(url):
    with urllib.request.urlopen(url, timeout=30) as res:
        return res.status, res.headers.get("Content-Type"), res.read()


def _post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def test_server_serves_the_page_and_its_files(base_url):
    status, ctype, body = _get(base_url + "/")
    assert status == 200 and ctype.startswith("text/html")
    assert b'src="static/app.js"' in body
    for name in ("app.js", "app.css"):
        status, _, body = _get(f"{base_url}/static/{name}")
        assert status == 200 and body


def test_server_refuses_paths_outside_static(base_url):
    for path in ("/static/../service.py", "/static/%2e%2e/service.py", "/nothing"):
        with pytest.raises(urllib.error.HTTPError) as err:
            _get(base_url + path)
        assert err.value.code == 404


def test_server_meta_and_backtest(base_url):
    _, _, body = _get(base_url + "/api/meta.json")
    meta = json.loads(body)
    assert meta["mode"] == "live" and "FIX" in meta["assets"]

    status, result = _post(
        base_url + "/api/backtest", {"strategy": "SimpleMACrossover", "assets": ["FIX"]}
    )
    assert status == 200
    assert result["run"]["assets"] == ["FIX"]

    status, error = _post(base_url + "/api/backtest", {"strategy": "Nope", "assets": ["FIX"]})
    assert status == 400 and "Unknown strategy" in error["error"]


# --- static export ----------------------------------------------------------
def test_export_writes_a_complete_static_site(data_dir, tmp_path):
    out = tmp_path / "site"
    n = server.export_site(
        out,
        data_dir,
        strategies=["SimpleMACrossover", "BuyAndHoldStrategy"],
        commissions=["IBKR Tiered", "Zero Commission"],
    )
    assert n == 2 * 2 * 2
    assert (out / "index.html").is_file()
    assert (out / "static" / "app.js").is_file()
    meta = json.loads((out / "api" / "meta.json").read_text())
    assert meta["mode"] == "static"
    assert meta["data_dir"] is None
    assert [s["name"] for s in meta["strategies"]] == ["BuyAndHoldStrategy", "SimpleMACrossover"]
    key = server.run_key("SimpleMACrossover", "FIX", "Zero Commission")
    assert key == "SimpleMACrossover__FIX__zero-commission"
    run = json.loads((out / "api" / "runs" / f"{key}.json").read_text())
    assert run["run"]["commission"] == "Zero Commission"


def test_server_refuses_cross_site_requests(base_url):
    body = json.dumps({"strategy": "SimpleMACrossover", "assets": ["FIX"]}).encode()
    plain = urllib.request.Request(
        base_url + "/api/backtest", data=body, headers={"Content-Type": "text/plain"}
    )
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(plain, timeout=30)
    assert err.value.code == 415

    rebound = urllib.request.Request(base_url + "/api/meta.json", headers={"Host": "evil.example"})
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(rebound, timeout=30)
    assert err.value.code == 403
