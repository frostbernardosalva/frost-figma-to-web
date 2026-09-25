#!/usr/bin/env python3
"""Diff the design's line breaks against the built page's, word by word.

    python bin/break-diff.py --design design-breaks.json --built built-breaks.json

WHY THIS IS A PURE DIFF

    It launches no browser and reads no page. That is deliberate: `verify.py`
    refuses remote URLs, so a comparison that drove it directly would be useless
    against a live site, which is the main place this is wanted.

    Splitting the inputs covers both targets with one tool:

        local build   verify.py --json --text <sel> --width N
        live site     evaluate bin/gate.js in the page, call lineEnds()

    It also means this can be tested from two files, with no browser at all --
    which matters, because four of these probes have been wrong already and
    three of them returned "pass".

WHY WORDS AND NOT A COUNT

    On project two the S1 headline shipped INVERTED between desktop and mobile:
    "Frost has worked" / "with industry titans." at 1920 where the design breaks
    after *with*, and the reverse at 480. Both widths were two lines. A count
    check passed it. Only the words catch it.

INPUT SHAPE

    {"blocks": {"<block name>": {"1920": [...lines...], "1440": [...]}}}

    A width's value may be a bare list of lines, or any of the shapes the two
    producers emit -- see `lines_of()`. Extra keys are ignored, so the design
    file can carry derivedLineCount, agrees, method and so on.

Exit codes
    0   every block matches at every shared width
    1   at least one mismatch, or the inputs cannot be read
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def lines_of(value):
    """Normalise the shapes the producers actually emit, into a list of lines.

    - a bare list                          -> itself
    - {"lines": [...]}                     -> the design file's own shape
    - {"text": [...]}                      -> gate.js lineEnds().detail
    - {"detail": {"text": [...]}}          -> a whole gate.js row
    - {"lines": {"detail": {"text": [..]}}} -> verify.py --json, whole blob
    """
    if value is None:
        return None
    if isinstance(value, list):
        # gate.js returns `lines` as word ARRAYS and `text` as joined strings.
        # Join defensively so either survives being passed in directly.
        return [" ".join(str(w) for w in x) if isinstance(x, list) else str(x)
                for x in value]
    if isinstance(value, dict):
        # "text" before "lines": a gate.js detail carries BOTH, and `lines` is
        # the word-array form. Preferring `lines` stringifies the arrays and
        # every comparison fails on the first word.
        for key in ("text", "lines"):
            if key in value:
                return lines_of(value[key])
        if "detail" in value:
            return lines_of(value["detail"])
    return None


def first_difference(a: list[str], b: list[str]) -> str:
    """Name the first differing WORD, not just the line. The failure is subtle."""
    for i in range(max(len(a), len(b))):
        la = a[i] if i < len(a) else None
        lb = b[i] if i < len(b) else None
        if la == lb:
            continue
        if la is None:
            return f"design has {len(a)} line(s), built has {len(b)} — extra built line {i+1}: {lb!r}"
        if lb is None:
            return f"design has {len(a)} line(s), built has {len(b)} — missing line {i+1}: {la!r}"
        wa, wb = la.split(), lb.split()
        for j in range(max(len(wa), len(wb))):
            xa = wa[j] if j < len(wa) else "(end of line)"
            xb = wb[j] if j < len(wb) else "(end of line)"
            if xa != xb:
                return (f"line {i+1} word {j+1}: design {xa!r}, built {xb!r}\n"
                        f"            design: {la}\n"
                        f"            built:  {lb}")
        return f"line {i+1} differs in whitespace only:\n            design: {la!r}\n            built:  {lb!r}"
    return ""


def load(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"break-diff: no such {label} file: {path}\n")
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"break-diff: {label} file is not valid JSON: {exc}\n")
        raise SystemExit(1)
    blocks = data.get("blocks")
    if not isinstance(blocks, dict):
        sys.stderr.write(f"break-diff: {label} file has no 'blocks' object\n")
        raise SystemExit(1)
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(prog="break-diff")
    ap.add_argument("--design", required=True, type=Path,
                    help="what the Figma design does (agents/break-reader)")
    ap.add_argument("--built", required=True, type=Path,
                    help="what the page does (verify.py --json, or gate.js in the browser)")
    ap.add_argument("--quiet", action="store_true", help="print only mismatches")
    args = ap.parse_args()

    design = load(args.design, "design")
    built = load(args.built, "built")

    mismatches = 0
    checked = 0
    skipped: list[str] = []

    for block, widths in design.items():
        if block not in built:
            skipped.append(f"{block}: not in the built file")
            continue
        for width, dval in widths.items():
            dlines = lines_of(dval)
            bval = built[block].get(width)
            blines = lines_of(bval)
            if dlines is None:
                skipped.append(f"{block} @ {width}: design lines unreadable")
                continue
            if blines is None:
                skipped.append(f"{block} @ {width}: not in the built file")
                continue
            checked += 1
            if dlines == blines:
                if not args.quiet:
                    print(f"  ok    {block} @ {width}  {' / '.join(dlines)}")
            else:
                mismatches += 1
                print(f"  FAIL  {block} @ {width}")
                print("        " + first_difference(dlines, blines))

            # the design file may carry the agent's own disagreement flag
            if isinstance(dval, dict) and dval.get("agrees") is False:
                print(f"  !!    {block} @ {width}: the reader's screenshot words and its "
                      f"height-derived line count DISAGREE — resolve before trusting this row")

    for s in skipped:
        print(f"  --    {s}")

    print(f"\n  {checked} compared, {mismatches} mismatch(es)"
          + (f", {len(skipped)} skipped" if skipped else ""))
    if mismatches:
        print("\n  Fix with Method 1 (widen the box) first; Method 2 (a span that wraps its own\n"
              "  text, display:block at that breakpoint only) when Method 1's window is too\n"
              "  narrow. Then re-run the WHOLE gate, not just this row.")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
