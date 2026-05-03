"""Capture des screenshots du dashboard pour le PDF / PPT / portfolio.

Démarre l'API + un serveur HTTP statique sur le frontend, puis Playwright
chromium fait le tour des 5 vues de référence et écrit des PNG dans
`docs/screenshots/`.

Usage::

    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "frontend"
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

API_PORT = 8765
WEB_PORT = 5765
API_URL = f"http://127.0.0.1:{API_PORT}"
WEB_URL = f"http://127.0.0.1:{WEB_PORT}"


def _start_api():
    env = os.environ.copy()
    env.setdefault("JWT_SECRET", "shots-secret-thirty-two-chars-aaaaa")
    env.setdefault("DEMO_USER", "admin")
    env.setdefault("DEMO_PASSWORD", "admin")
    env.setdefault("GOLD_DUCKDB_PATH", str(ROOT / "data" / "demo" / "urban.duckdb"))
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--host", "127.0.0.1", "--port", str(API_PORT), "--log-level", "warning"],
        cwd=ROOT, env=env,
    )


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(FRONT), **kw)

    def log_message(self, *_):
        pass


def _start_web():
    httpd = socketserver.TCPServer(("127.0.0.1", WEB_PORT), _Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def _wait_health():
    for _ in range(40):
        try:
            if httpx.get(f"{API_URL}/health", timeout=1).status_code == 200:
                return True
        except httpx.RequestError:
            time.sleep(0.4)
    return False


def main():
    # patch the meta tag in the served frontend so it points to our temp API
    index = FRONT / "index.html"
    original = index.read_text(encoding="utf-8")
    patched = original.replace(
        'content="http://localhost:8000"',
        f'content="{API_URL}"',
    )
    if patched != original:
        index.write_text(patched, encoding="utf-8")

    api_proc = _start_api()
    web_srv = _start_web()
    try:
        if not _wait_health():
            print("ERROR · API failed to come up", file=sys.stderr)
            return 1

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(args=[
                "--no-sandbox",
                "--use-gl=swiftshader",
                "--enable-webgl",
                "--ignore-gpu-blocklist",
            ])
            ctx = browser.new_context(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=2,
            )
            page = ctx.new_page()

            # 01 · landing (login form visible)
            page.goto(WEB_URL)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(OUT / "01-landing.png"), full_page=False)

            # log in
            page.click("#login-btn")
            page.wait_for_function(
                "document.getElementById('filters-section').classList.contains('hidden') === false",
                timeout=10_000,
            )
            # Wait for MapLibre canvas to be present and tiles loaded
            page.wait_for_selector(".maplibregl-canvas", timeout=15_000)
            page.wait_for_function(
                "() => window.map && window.map.loaded() && window.map.areTilesLoaded()",
                timeout=20_000,
            )
            page.wait_for_timeout(3000)  # extra safety for paint

            # 02 · choropleth with prix_m2
            page.screenshot(path=str(OUT / "02-choropleth-prix.png"), full_page=False)

            # 03 · switch to attractivity
            page.select_option("#indicator-select", "idx_attractivite")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "03-choropleth-attractivite.png"), full_page=False)

            # 04 · activate culture + sante + transport POI layers
            for cat in ("culture", "sante", "transport"):
                page.locator(f'.layers input[data-cat="{cat}"]').check()
                page.wait_for_timeout(800)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "04-poi-layers.png"), full_page=False)

            # 05 · trigger compare mode
            page.select_option("#compare-a", "75116")
            page.select_option("#compare-b", "75119")
            page.click("#compare-btn")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "05-compare-radar.png"), full_page=False)

            browser.close()

        for f in sorted(OUT.glob("*.png")):
            print(f"  {f.name} · {f.stat().st_size // 1024} KB")

    finally:
        web_srv.shutdown()
        api_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()

        # Restore index.html
        index.write_text(original, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
