"""Drives the configurator page in headless Edge (or Chrome): builds each
configuration below in the browser and saves its 3MF, checks and timings.

    uv run --no-project --python 3.12 --with build123d --with pyyaml --with playwright python configurator/test_page.py [out folder]

Writes <out>/results.json and the 3MFs (default: configurator/test-prints/,
git-ignored). Needs the internet for the CAD engine.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "test-prints"
PORT = 8766
CONFIGS = [   # the address after #: type & field=value
    "tool-bin&cells=3&rows=2",
    "tool-bin&cells=4&rows=3&depth=80&front=tall&insert=hex",
    "lean-bin&cells=4&rows=4&insert=screwdriver",
    "tray&cells=4&depth=90&style=dish",
    "arc-drawer&cells=3&rows=2&depth=80",
]

OUT.mkdir(parents=True, exist_ok=True)
server = subprocess.Popen([sys.executable, str(HERE / "serve.py"), str(PORT), "--no-browser"])
for _ in range(240):   # it imports the catalog first, which can take half a minute
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/configurator/", timeout=2)
        break
    except OSError:
        if server.poll() is not None:
            sys.exit("serve.py exited")
        time.sleep(0.5)
results = []
try:
    with sync_playwright() as pw:
        browser = None
        for channel in ("msedge", "chrome", None):
            try:
                browser = pw.chromium.launch(channel=channel) if channel else pw.chromium.launch()
                break
            except Exception as e:  # noqa: BLE001
                print(f"{channel}: {e}".splitlines()[0])
        page = browser.new_page(accept_downloads=True, viewport={"width": 1280, "height": 1100})
        page.on("console", lambda m: m.type == "error" and print("console:", m.text))
        page.on("pageerror", lambda e: print("pageerror:", e))
        t0 = time.time()
        page.goto(f"http://127.0.0.1:{PORT}/configurator/#{CONFIGS[0]}")
        page.wait_for_function("document.getElementById('engine').classList.contains('ready') || "
                               "document.getElementById('engine').classList.contains('failed')", timeout=600_000)
        engine = {"text": page.text_content("#engine-text"), "seconds": round(time.time() - t0, 1)}
        print("engine:", engine)
        for i, cfg in enumerate(CONFIGS):
            page.evaluate(f"location.hash = {json.dumps(cfg)}")
            page.wait_for_timeout(300)
            t = time.time()
            page.click("#build")
            page.wait_for_function("!document.querySelector('.cfg-busy') && !document.getElementById('build').disabled", timeout=900_000)
            r = {"config": cfg, "seconds": round(time.time() - t, 1), "title": page.text_content("#result-title"),
                 "chip": page.inner_text("#result-chip"),
                 "checks": [li.inner_text().replace("\n", " | ") for li in page.query_selector_all("#checks li")],
                 "files": [a.get_attribute("download") for a in page.query_selector_all("#files a")]}
            link = page.query_selector("#files li.main a")
            if link:
                with page.expect_download() as dl:
                    link.click()
                dl.value.save_as(OUT / dl.value.suggested_filename)
                r["saved"] = dl.value.suggested_filename
            page.screenshot(path=str(OUT / f"page_{i + 1}.png"), full_page=True)
            print(json.dumps(r, indent=1))
            results.append(r)
        browser.close()
finally:
    server.terminate()
(OUT / "results.json").write_text(json.dumps({"engine": engine, "builds": results}, indent=1), encoding="utf-8")
print("written", OUT / "results.json")
