#!/usr/bin/env python3
"""Turn page scans into an ordered, reversible plan for replacing live assets.

    python bin/rebind-plan.py --scan home-1920.json --scan home-480.json \
                              --converted ./converted --out rebind-plan.json

READ-ONLY. It makes no Webflow call and no network request. It produces the plan
that a human reads before anything is written, and the record that reverses it
afterwards.

THE DANGER THIS EXISTS FOR

    gate.js legacyAssets() inspects ONE RENDERED PAGE AT ONE WIDTH. An asset can
    also be referenced:

        - on a page you did not scan
        - only at a breakpoint you did not render -- a mobile-only background is
          invisible at 1440
        - by CSS matching a state or media query you did not trigger

    Deleting an asset because one page looks clean is how you silently break
    another page. So this reports COVERAGE first, flags every asset seen at only
    some of the scanned widths, and puts delete last and batched.

    The delete phase is gated on coverage, not on a single green check.

THE ORDER, WHICH IS NOT NEGOTIABLE

    upload -> rebind every reference -> verify zero legacy refs on EVERY scanned
    page -> only then delete, five at a time.

    Four traps make it so, all recorded in targets/webflow.md:
      - deletes are soft, and identical bytes return the OLD asset id and name
      - publish_site returns BEFORE the CSS is live; check the stylesheet hash
      - 10 parallel deletes returned 429 and the batch was refused whole
      - the obvious legacy regex passes every CSS background

Exit codes
    0   plan written
    1   nothing to plan, or an input could not be read
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DELETE_BATCH = 5          # 10 parallel deletes returned 429, refused whole


def scan_label(path: Path, data: dict) -> tuple[str, str]:
    """(page, width). From _page/_width if present, else the filename."""
    page = data.get("_page")
    width = data.get("_width")
    if page and width:
        return str(page), str(width)
    m = re.match(r"^(.*?)[-_](\d{3,4})$", path.stem)
    if m:
        return m.group(1), m.group(2)
    return path.stem, "?"


def hits_of(data) -> list[dict]:
    """Every {where, url} in a legacyAssets() result, whatever shape it took."""
    out: list[dict] = []

    def walk(node):
        if isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            if "url" in node and isinstance(node["url"], str):
                out.append({"where": str(node.get("where", "?")), "url": node["url"]})
                return
            for v in node.values():
                walk(v)

    walk(data)
    return out


def clean_url(raw: str) -> str:
    """CSS backgrounds arrive as url("..."). Strip to the bare address."""
    m = re.search(r'url\(\s*[\'"]?([^\'")]+)', raw)
    url = m.group(1) if m else raw
    return url.strip().strip('\'"')


def main() -> int:
    ap = argparse.ArgumentParser(prog="rebind-plan")
    ap.add_argument("--scan", action="append", required=True, type=Path,
                    help="a gate.js legacyAssets() result. Repeat, one per page x width. "
                         "Label it with _page/_width in the JSON, or name it <page>-<width>.json")
    ap.add_argument("--converted", required=True, type=Path,
                    help="the AVIFs from audit-assets.py --out")
    ap.add_argument("--out", type=Path, default=Path("rebind-plan.json"))
    args = ap.parse_args()

    if not args.converted.is_dir():
        sys.stderr.write(f"rebind-plan: not a directory: {args.converted}\n")
        return 1
    replacements = {p.stem: p for p in args.converted.glob("*.avif")}

    # ---- read every scan -------------------------------------------------
    coverage: dict[str, set[str]] = {}
    refs: dict[str, list[dict]] = {}
    for s in args.scan:
        try:
            data = json.loads(s.read_text(encoding="utf-8"))
        except Exception as exc:                       # noqa: BLE001
            sys.stderr.write(f"rebind-plan: cannot read {s}: {exc}\n")
            return 1
        page, width = scan_label(s, data)
        coverage.setdefault(page, set()).add(width)
        for h in hits_of(data):
            url = clean_url(h["url"])
            if not re.search(r"\.(png|jpe?g)$", url, re.I):
                continue
            kind = "img" if h["where"].strip().startswith("<img") else "css"
            refs.setdefault(url, []).append(
                {"page": page, "width": width, "where": h["where"], "kind": kind})

    if not refs:
        print("  no legacy raster references in any scan - nothing to plan")
        return 1

    warnings: list[str] = []
    all_widths = sorted({w for ws in coverage.values() for w in ws})

    # ---- COVERAGE, first, because delete depends on it -------------------
    print("  COVERAGE - what was actually looked at\n")
    for page, widths in sorted(coverage.items()):
        print(f"    {page:24} {', '.join(sorted(widths))}")
    print(f"\n    {len(args.scan)} scan(s), {len(coverage)} page(s), widths {', '.join(all_widths)}")

    if len(args.scan) == 1:
        warnings.append("ONLY ONE SCAN. An asset referenced on any other page, or at any other "
                        "width, is invisible here. Do not delete on this basis.")
    if "?" in all_widths:
        warnings.append("A scan had no width label - name it <page>-<width>.json or set _width.")

    # ---- build the plan --------------------------------------------------
    upload, rebind, deletable, unreplaceable = [], [], [], []
    for url, places in sorted(refs.items()):
        stem = Path(url.split("?")[0].rsplit("/", 1)[-1]).stem
        new = replacements.get(stem)
        seen_widths = {p["width"] for p in places}
        if new is None:
            unreplaceable.append((url, stem))
            continue
        upload.append({"file": str(new), "uploadAs": new.name, "replaces": url})
        for p in places:
            rebind.append({"old": url, "new": new.name, "kind": p["kind"],
                           "page": p["page"], "width": p["width"], "where": p["where"]})
        deletable.append(url)
        if seen_widths != set(all_widths):
            missing = sorted(set(all_widths) - seen_widths)
            warnings.append(f"{stem}: seen at {', '.join(sorted(seen_widths))} but NOT at "
                            f"{', '.join(missing)} - confirm it is genuinely unused there")

    for url, stem in unreplaceable:
        warnings.append(f"{stem}: no {stem}.avif in {args.converted} - not uploaded, not rebound, "
                        f"NOT deleted")

    # ---- print it in execution order -------------------------------------
    print(f"\n  1 - UPLOAD  {len(upload)} file(s)")
    print("      Verify each returns contentType image/avif AND A NEW ASSET ID.")
    print("      Identical bytes return the OLD id under its OLD display name.")
    for u in upload:
        print(f"      {u['uploadAs']}")

    print(f"\n  2 - REBIND  {len(rebind)} reference(s)")
    for r in rebind:
        print(f"      [{r['kind']:3}] {r['page']}@{r['width']:<5} {r['where'][:34]:34} -> {r['new']}")

    print("\n  3 - PUBLISH, then confirm the STYLESHEET HASH CHANGED.")
    print("      publish_site returns before the CSS is live; a correct fix otherwise")
    print("      reads as a failure and gets 'fixed' twice.")

    print("\n  4 - RE-SCAN every page at every width above, require legacyAssets() -> zero.")

    batches = [deletable[i:i + DELETE_BATCH] for i in range(0, len(deletable), DELETE_BATCH)]
    print(f"\n  5 - DELETE  {len(deletable)} asset(s) in {len(batches)} batch(es) of "
          f"{DELETE_BATCH} - 10 at once returned 429 and the batch was refused whole.")
    print("      DO NOT RUN THIS UNTIL STEP 4 IS GREEN ON EVERY SCANNED PAGE.")

    if warnings:
        print(f"\n  WARNINGS  ({len(warnings)})")
        for w in warnings:
            print(f"    !!  {w}")

    plan = {
        "_what": "Ordered plan AND rollback record. Each rebind carries old and new.",
        "coverage": {p: sorted(w) for p, w in coverage.items()},
        "widths": all_widths,
        "upload": upload,
        "rebind": rebind,
        "deleteBatches": batches,
        "warnings": warnings,
    }
    args.out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"\n  plan + rollback record: {args.out}")
    print("  Every rebind entry carries old and new, so this file alone reverses the change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
