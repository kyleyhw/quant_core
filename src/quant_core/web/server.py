"""
The dashboard's web server and its static export.

``serve`` runs a small local HTTP server: it serves the page in ``static/`` and
answers two JSON endpoints backed by :mod:`quant_core.service`::

    GET  /api/meta.json   strategies, parameters, local assets, commission models
    POST /api/backtest    run one backtest; the body names the strategy and inputs

``export_site`` writes the same page with every default run computed ahead of
time, as plain files a static host such as GitHub Pages can serve. The page reads
``meta.json`` to learn which of the two it is talking to.
"""

from __future__ import annotations

import json
import mimetypes
import re
import shutil
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quant_core import __version__, service

STATIC = Path(__file__).parent / "static"
MAX_BODY = 64 * 1024


def run_key(strategy: str, asset: str, commission: str, period: str = "all") -> str:
    """The file name, without extension, of a precomputed run in a static export."""
    slug = re.sub(r"[^a-z0-9]+", "-", commission.lower()).strip("-")
    return f"{strategy}__{asset.upper()}__{slug}__{period}"


def site_meta(data_dir: Path | str, mode: str) -> dict[str, Any]:
    meta = service.meta(data_dir)
    meta["mode"] = mode
    meta["version"] = __version__
    return meta


# ---------------------------------------------------------------------------
# Live server
# ---------------------------------------------------------------------------
class DashboardHandler(BaseHTTPRequestHandler):
    server_version = f"quant-core/{__version__}"
    data_dir: Path = service.DEFAULT_DATA_DIR
    quiet = False

    # -- responses ---------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        if not self.quiet:
            super().log_message(format, *args)

    # -- routes ------------------------------------------------------------
    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._static("index.html")
        if path.startswith("/static/"):
            return self._static(path[len("/static/") :])
        if path == "/api/meta.json":
            if not self._trusted_host():
                return self._error(HTTPStatus.FORBIDDEN, "Unrecognised host.")
            return self._json(HTTPStatus.OK, site_meta(self.data_dir, "live"))
        return self._error(HTTPStatus.NOT_FOUND, f"Nothing at {path}.")

    def _trusted_host(self) -> bool:
        """
        Refuses requests addressed to another host name. A page on another site
        could otherwise point a name it controls at 127.0.0.1 and read the API.
        """
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        bound = str(getattr(self.server, "server_name", "") or "")
        address = self.server.server_address
        if isinstance(address, tuple):
            bound = str(address[0])
        if bound in ("0.0.0.0", "::"):
            return True
        return host in ("localhost", "127.0.0.1", "::1", bound.lower())

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/backtest":
            return self._error(HTTPStatus.NOT_FOUND, f"Nothing at {self.path}.")
        if not self._trusted_host():
            return self._error(HTTPStatus.FORBIDDEN, "Unrecognised host.")
        # Requiring JSON makes a cross-site form or script post fail the
        # browser's preflight check, which this server never answers.
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            return self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Send application/json.")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            return self._error(HTTPStatus.BAD_REQUEST, "Send a JSON body under 64 KB.")
        try:
            req = json.loads(self.rfile.read(length))
            if not isinstance(req, dict):
                raise ValueError
        except ValueError:
            return self._error(HTTPStatus.BAD_REQUEST, "The request body is not a JSON object.")
        try:
            result = service.run_backtest(
                str(req.get("strategy") or ""),
                [str(a) for a in req.get("assets") or []],
                commission=str(req.get("commission") or service.DEFAULT_COMMISSION),
                cash=float(req.get("cash") or service.DEFAULT_CASH),
                params=req.get("params") or {},
                underlying=req.get("underlying") or None,
                data_dir=self.data_dir,
                start=req.get("start") or None,
                end=req.get("end") or None,
            )
        except (service.RunError, TypeError, ValueError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        return self._json(HTTPStatus.OK, result)

    def _static(self, name: str) -> None:
        # Only plain file names directly inside static/: no directories, no traversal.
        if not re.fullmatch(r"[A-Za-z0-9_-]+\.(html|css|js|svg|json)", name):
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        target = STATIC / name
        if not target.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or name.endswith((".js", ".json", ".svg")):
            content_type += "; charset=utf-8"
        self._send(HTTPStatus.OK, target.read_bytes(), content_type)


def make_server(
    host: str = "127.0.0.1",
    port: int = 8501,
    data_dir: Path | str = service.DEFAULT_DATA_DIR,
    quiet: bool = False,
) -> ThreadingHTTPServer:
    handler = type("Handler", (DashboardHandler,), {"data_dir": Path(data_dir), "quiet": quiet})
    return ThreadingHTTPServer((host, port), handler)


def serve(
    host: str = "127.0.0.1",
    port: int = 8501,
    data_dir: Path | str = service.DEFAULT_DATA_DIR,
    open_browser: bool = True,
) -> None:
    """Serves the dashboard until interrupted."""
    httpd = make_server(host, port, data_dir)
    url = f"http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{httpd.server_port}"
    assets = service.list_assets(data_dir)
    print(f"quant-core dashboard at {url}")
    if assets:
        print(f"Local data: {len(assets)} assets in {Path(data_dir).resolve()}")
    else:
        print(
            f"No price data in {Path(data_dir).resolve()}. Download some with\n"
            f"  qc download --tickers SPY MSFT --start 2024-01-01 --end 2025-01-01 "
            f"--output {data_dir}\nor type a ticker in the dashboard to fetch it."
        )
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()


# ---------------------------------------------------------------------------
# Static export
# ---------------------------------------------------------------------------
# What a static export precomputes by default: every period and commission model
# multiplies the number of runs, so the export keeps to the ones people compare.
EXPORT_PERIODS = ("all", "5y", "1y")
EXPORT_COMMISSIONS = ("IBKR Tiered", "Zero Commission")


def _export_one(job: tuple[str, str, str, str, str, str | None, str | None, str]) -> str:
    strategy, asset, commission, period, data_dir, start, end, path = job
    result = service.run_backtest(
        strategy, [asset], commission=commission, data_dir=data_dir, start=start, end=end
    )
    result["run"]["period"] = period
    Path(path).write_text(json.dumps(result, separators=(",", ":")))
    return path


def export_site(
    out_dir: Path | str,
    data_dir: Path | str = service.DEFAULT_DATA_DIR,
    strategies: list[str] | None = None,
    assets: list[str] | None = None,
    commissions: list[str] | tuple[str, ...] = EXPORT_COMMISSIONS,
    periods: list[str] | tuple[str, ...] = EXPORT_PERIODS,
    workers: int | None = None,
) -> int:
    """
    Writes the dashboard as static files, with every single-asset strategy run on
    every local asset for each of ``periods`` under each of ``commissions``, at
    default parameters. Returns the number of runs written.
    """
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    (out / "static").mkdir(parents=True)
    (out / "api" / "runs").mkdir(parents=True)
    shutil.copy2(STATIC / "index.html", out / "index.html")
    for f in STATIC.iterdir():
        if f.is_file() and f.name != "index.html":
            shutil.copy2(f, out / "static" / f.name)

    meta = site_meta(data_dir, "static")
    runnable = [
        s for s in meta["strategies"] if s["data_assets"] == 1 and not s["needs_underlying"]
    ]
    if strategies:
        runnable = [s for s in runnable if s["name"] in strategies]
    meta["strategies"] = runnable
    meta["assets"] = [a for a in meta["assets"] if not assets or a in assets]
    meta["asset_ranges"] = {a: r for a, r in meta["asset_ranges"].items() if a in meta["assets"]}
    meta["commissions"] = [c for c in meta["commissions"] if c in commissions]
    meta["periods"] = [p for p in meta["periods"] if p["id"] in periods]
    if meta["defaults"]["asset"] not in meta["assets"]:
        meta["defaults"]["asset"] = meta["assets"][0] if meta["assets"] else None
    if meta["defaults"]["commission"] not in meta["commissions"]:
        meta["defaults"]["commission"] = meta["commissions"][0] if meta["commissions"] else None
    if meta["defaults"]["period"] not in [p["id"] for p in meta["periods"]]:
        meta["defaults"]["period"] = meta["periods"][0]["id"] if meta["periods"] else None
    meta["data_dir"] = None
    (out / "api" / "meta.json").write_text(json.dumps(meta))

    jobs = []
    for s in runnable:
        for asset in meta["assets"]:
            first, last = meta["asset_ranges"][asset]
            for period in [p["id"] for p in meta["periods"]]:
                start, end = service.resolve_period(period, first, last)
                window = (None, None) if period == "all" else (start, end)
                for commission in meta["commissions"]:
                    key = run_key(s["name"], asset, commission, period)
                    path = str(out / "api" / "runs" / f"{key}.json")
                    jobs.append(
                        (s["name"], asset, commission, period, str(data_dir), *window, path)
                    )

    if workers == 1 or len(jobs) < 8:
        for job in jobs:
            _export_one(job)
    else:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(workers) as pool:
            for i, _ in enumerate(pool.map(_export_one, jobs, chunksize=4), start=1):
                if i % 50 == 0 or i == len(jobs):
                    print(f"  {i}/{len(jobs)} runs")
    (out / ".nojekyll").write_text("")
    return len(jobs)


def main_export(out_dir: str, data_dir: str) -> None:
    if not service.list_assets(data_dir):
        sys.exit(f"No CSV files in {data_dir}; nothing to export.")
    print(f"Exporting the dashboard to {out_dir} from {data_dir}")
    n = export_site(out_dir, data_dir)
    print(f"Wrote {n} runs. Serve {out_dir} with any static host.")
