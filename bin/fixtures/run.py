#!/usr/bin/env python3
"""Run gate.js against the fixture in headless Chrome. Exit non-zero on failure.

    python bin/fixtures/run.py [--chrome PATH]

The fixture is a page that is wrong on purpose, in the ways this workflow has
shipped wrong before. The probes in bin/gate.js have to find every defect and
flag none of the deliberate non-defects.

Headless Chrome rather than a browser session, because a test you can only run
by hand is a test that stops being run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "gate-fixture.html"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
]


def find_chrome(explicit: str | None) -> str:
    for c in ([explicit] if explicit else []) + CANDIDATES:
        if not c:
            continue
        if os.path.isfile(c):
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.stderr.write(
        "run.py: no Chrome found. Pass --chrome PATH.\n"
        "Looked in:\n  " + "\n  ".join(CANDIDATES) + "\n"
    )
    raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome", default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    chrome = find_chrome(args.chrome)
    profile = tempfile.mkdtemp(prefix="gate-fixture-")

    try:
        proc = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--allow-file-access-from-files", "--virtual-time-budget=4000",
             f"--user-data-dir={profile}", "--dump-dom", FIXTURE.as_uri()],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write("run.py: Chrome timed out\n")
        return 1
    finally:
        shutil.rmtree(profile, ignore_errors=True)

    # findall + last: an earlier literal mention of the tag (in a comment, say)
    # must not win over the real element.
    blocks = re.findall(r'<pre id="gate-results">(.*?)</pre>', proc.stdout, re.S)
    if not blocks:
        sys.stderr.write(
            "run.py: the fixture produced no results block.\n"
            "The harness scripts did not run — check that bin/gate.js loaded.\n"
        )
        if args.verbose:
            sys.stderr.write(proc.stdout[:2000] + "\n" + proc.stderr[:2000] + "\n")
        return 1

    import html as htmllib
    data = json.loads(htmllib.unescape(blocks[-1]))

    width = max(len(r["name"]) for r in data["results"])
    for r in data["results"]:
        mark = "ok  " if r["pass"] else "FAIL"
        print(f"  {mark}  {r['name']:<{width}}")
        if not r["pass"] or args.verbose:
            print(f"        expected: {json.dumps(r['expected'])}")
            print(f"        actual:   {json.dumps(r['actual'])}")
            if r.get("note"):
                print(f"        {r['note']}")

    passed = data["total"] - data["failures"]
    print(f"\n  {passed}/{data['total']} checks passed")
    return 0 if data["failures"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
