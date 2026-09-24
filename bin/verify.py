#!/usr/bin/env python3
"""Render a page headless at a real width and run the Stage 5 gate against it.

    python bin/verify.py dist/index.html --width 1440
    python bin/verify.py https://example.com --width 480 --container ".fr_container"

WHY HEADLESS AND NOT THE BROWSER EXTENSION

    The Claude-in-Chrome extension refuses both `file://` and `http://localhost`.
    Measured: a local server logged zero requests while Chrome showed
    `chrome-error://chromewebdata`, with no proxy configured. Headless Chrome
    with --allow-file-access-from-files opens file:// without complaint.

    So for a target that writes files, this is the only verification loop that
    works. It is also the one that can run in CI.

WHY AN IFRAME AND NOT --window-size

    Headless Chrome will not give you a narrow viewport. Measured:

        --window-size=1440  ->  viewport 1424     (a constant -16)
        --window-size=1456  ->  viewport 1440
        --window-size=480   ->  viewport 500      <-- clamped
        --window-size=496   ->  viewport 500      <-- still clamped

    There is a ~500px floor, so a 480 breakpoint cannot be tested by sizing the
    window, and would silently be measured at 500 - across a breakpoint
    boundary. An iframe has no floor: media queries inside it evaluate against
    the iframe's own width at any size.

    This is NOT the same as padding a width to compensate for a scrollbar, which
    references/verification.md warns against. That pushes the media width PAST
    the breakpoint. Here the iframe IS the viewport, exactly as requested, and
    the runner asserts it came back right.

WHY A REAL WIDTH MATTERS

    The first audit on this workflow reported 41%, every failure at exactly 85%
    of expected. Not a build fault: a 1536px host window resolved a fluid root
    font-size to 13.6px against 1920px design figures. --width sets the real
    window size, and row 0 asserts the root font-size before anything else is
    believed.

Exit codes
    0   every row passed
    1   at least one row failed, or the page could not be rendered
"""

from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "gate.js"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
]


def find_chrome(explicit: str | None) -> str:
    import os

    for c in ([explicit] if explicit else []) + CANDIDATES:
        if not c:
            continue
        if os.path.isfile(c):
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.stderr.write(
        "verify: no Chrome found. Pass --chrome PATH.\nLooked in:\n  "
        + "\n  ".join(CANDIDATES) + "\n"
    )
    raise SystemExit(1)


def target_url(target: str) -> str:
    if re.match(r"^https?://", target):
        return target
    p = Path(target).resolve()
    if not p.exists():
        sys.stderr.write(f"verify: no such file: {p}\n")
        raise SystemExit(1)
    return p.as_uri()


def build_harness(container_sel: str, text_sel: str | None, src: str,
                  width: int, height: int, section_sel: str | None = None) -> str:
    """JS appended after gate.js: render `src` in an iframe at exactly `width`,
    run the rows against it, and print one JSON blob."""
    lines_call = ("safe('lines', function () { return G.lineEnds(d.querySelector("
                  + json.dumps(text_sel) + ")); });") if text_sel else ""
    return """
(function () {
  var G = window.__frostGate, out = {};
  var f = document.createElement('iframe');
  f.style.cssText = 'position:absolute;left:0;top:0;border:0;visibility:hidden';
  f.width = __W__; f.height = __H__;
  f.src = __SRC__;
  document.body.appendChild(f);

  function emit() {
    var pre = document.createElement('pre');
    pre.id = 'frost-verify';
    pre.textContent = JSON.stringify(out);
    document.body.appendChild(pre);
  }
  function safe(name, fn) {
    try { out[name] = fn(); }
    catch (e) { out[name] = {status: 'fail', detail: 'THREW: ' + e.message}; }
  }

  f.onload = function () {
    var d;
    try { d = f.contentDocument; }
    catch (e) { out.error = 'cannot reach the iframe document: ' + e.message; emit(); return; }

    var go = function () {
      try {
        var st = d.createElement('style');
        st.textContent = 'html{scrollbar-width:none}::-webkit-scrollbar{display:none}';
        d.head.appendChild(st);
      } catch (e) {}
      safe('root',       function () { return G.rootFontSize(d); });
      safe('containers', function () { return G.containers(d, __CONTAINER__); });
      safe('assets',     function () { return G.legacyAssets(d); });
      safe('alt',        function () { return G.altAudit(d); });
      safe('breaks',     function () { return G.glue(d); });
      safe('units',      function () { return G.unitAudit(d); });
      __LINES__
      // scrollHeight reports the IFRAME height whenever the content is
      // shorter than it, which silently turns every short page into "1200".
      // body's bounding rect is the content height regardless.
      out.page = {width: f.contentWindow.innerWidth,
                  height: Math.round(d.body.getBoundingClientRect().height * 100) / 100,
                  scrollHeight: d.documentElement.scrollHeight};
      var sel = __SECTION__;
      if (sel) {
        var el = d.querySelector(sel);
        out.page.section = el ? Math.round(el.getBoundingClientRect().height * 100) / 100
                              : 'not found: ' + sel;
      }
      emit();
    };
    // text measurements are wrong until webfonts have landed
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(function () { setTimeout(go, 250); });
    else setTimeout(go, 1200);
  };
})();
""".replace('__W__', str(width)).replace('__H__', str(height))    .replace('__SRC__', json.dumps(src))    .replace('__CONTAINER__', json.dumps(container_sel))    .replace('__LINES__', lines_call)    .replace('__SECTION__', json.dumps(section_sel))


def main() -> int:
    ap = argparse.ArgumentParser(prog="verify")
    ap.add_argument("target", help="a local path or an http(s) URL")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=1200)
    ap.add_argument("--container", default='[class*="_inner"], [class*="container"]',
                    help="selector for the elements that must all report ONE width")
    ap.add_argument("--section", default=None,
                    help="selector whose height to report (a section, for height locks)")
    ap.add_argument("--text", default=None,
                    help="selector for a text block whose rendered line breaks to report")
    ap.add_argument("--chrome", default=None)
    ap.add_argument("--json", action="store_true", help="print raw JSON and nothing else")
    args = ap.parse_args()

    chrome = find_chrome(args.chrome)
    url = target_url(args.target)

    # Chrome has no "evaluate this script" flag, so the probes run from a
    # throwaway wrapper page that iframes the target. The wrapper sits beside
    # the target so a relative iframe src resolves, and is deleted in `finally`.
    profile = tempfile.mkdtemp(prefix="frost-verify-")
    temp_page = None
    try:
        if url.startswith("file://"):
            src = Path(args.target).resolve()
            temp_page = src.with_name(f".verify-{src.name}")
            harness = build_harness(args.container, args.text, src.name,
                                    args.width, args.height, args.section)
            temp_page.write_text(
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<style>html,body{margin:0;padding:0;overflow:hidden}</style></head><body>"
                f'<script src="{GATE.as_uri()}"></script>'
                f"<script>{harness}</script>"
                "</body></html>", encoding="utf-8")
            url = temp_page.as_uri()
        else:
            sys.stderr.write(
                "verify: remote URLs need the gate injected by the browser tool, not this runner.\n"
                "        Use a local build, or evaluate bin/gate.js in the page directly.\n"
            )
            return 1

        proc = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--allow-file-access-from-files", "--virtual-time-budget=5000",
             # The window size is irrelevant now: the IFRAME is the viewport,
             # and it is exactly --width. A fixed host window also sidesteps
             # Chrome's ~500px minimum window width, which made 480 untestable.
             "--hide-scrollbars", "--window-size=1200,900",
             f"--user-data-dir={profile}", "--dump-dom", url],
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write("verify: Chrome timed out\n")
        return 1
    finally:
        shutil.rmtree(profile, ignore_errors=True)
        if temp_page and temp_page.exists():
            temp_page.unlink()

    blocks = re.findall(r'<pre id="frost-verify">(.*?)</pre>', proc.stdout, re.S)
    if not blocks:
        sys.stderr.write("verify: the gate produced no result block — did bin/gate.js load?\n")
        return 1
    data = json.loads(htmllib.unescape(blocks[-1]))

    if args.json:
        print(json.dumps(data, indent=2))
        return 0 if not any(
            isinstance(v, dict) and v.get("status") == "fail" for v in data.values()) else 1

    actual = data["page"]["width"]
    sec = data["page"].get("section")
    print(f"  {args.target}  @ {actual}px   content height {data['page']['height']}"
          + (f"   section {sec}" if sec is not None else ""))
    if actual != args.width:
        print(f"  !!    width came back {actual}, not {args.width}. Every measurement below is "
              f"at the wrong viewport - fix this before reading them.")
    failed = 0
    for name, r in data.items():
        if name == "page":
            continue
        status = r.get("status", "?") if isinstance(r, dict) else "?"
        mark = {"pass": "ok  ", "fail": "FAIL", "info": "--  "}.get(status, "??  ")
        if status == "fail":
            failed += 1
        detail = r.get("detail") if isinstance(r, dict) else r
        if not isinstance(detail, str):
            detail = json.dumps(detail)
        print(f"  {mark}  {name:11} {detail[:120]}")
    print(f"\n  {failed} row(s) failed" if failed else "\n  all rows passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
