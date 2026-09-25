#!/usr/bin/env python3
"""What would an already-built site save by converting its images to AVIF?

    python bin/audit-assets.py --dir <folder>              a local folder
    python bin/audit-assets.py --from-gate legacy.json     a live site
    python bin/audit-assets.py --from-gate legacy.json --out ./converted

WHY THIS EXISTS SEPARATELY FROM to-avif.py

    to-avif.py converts a Figma export during a build. This answers a different
    question about a site that already shipped: not "convert everything" but
    "what would it save?" -- because that number is the decision.

    `to-avif.py --dry-run` cannot answer it. It classifies but never encodes, so
    it has no output size to report. Encoding is the only way to know, so this
    encodes into a temp directory and throws the result away unless --out is
    given.

WHY IT IMPORTS to-avif.py INSTEAD OF REIMPLEMENTING IT

    A second encoder drifts from the first, and then the audit reports savings
    you do not actually get. The classification threshold (4096 colours), the
    speed setting (4, measured and NOT monotonic) and the provable-alpha rule
    all live in one place.

WHAT IT DOES NOT DO

    It writes nothing to any site. No upload, no rebind, no delete. Replacing
    assets on a live build has an order that must be followed -- upload, rebind
    every reference, verify zero legacy references, and only then delete -- and
    a trap: re-uploading byte-identical bytes returns the OLD asset id. See
    SKILL.md Stage 0.5 and targets/webflow.md.

Exit codes
    0   report produced (the default; this is a report, not a gate)
    1   nothing readable, or --fail-if-any and convertible rasters were found
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Platform assets you do not control and cannot replace. The Frost site's only
# remaining raster is Webflow's own webclip.
DEFAULT_SKIP = ["*/img/webclip.png", "*favicon*"]


def load_converter():
    """Import to-avif.py. The hyphen stops a plain import, not importlib."""
    spec = importlib.util.spec_from_file_location("to_avif", HERE / "to-avif.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["to_avif"] = mod
    spec.loader.exec_module(mod)
    return mod


def gather_from_gate(path: Path) -> list[tuple[str, str]]:
    """(label, url) from whatever gate.js legacyAssets() emitted.

    Accepts the pass shape, the fail shape, or a bare list of urls -- the probe
    returns a string on pass and {hits, pending} on fail, and a caller may well
    hand over just the hits.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    urls: list[str] = []

    def walk(node):
        if isinstance(node, str):
            if node.startswith(("http://", "https://")):
                urls.append(node)
        elif isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            if "url" in node and isinstance(node["url"], str):
                # css backgrounds arrive as url("...")
                raw = node["url"]
                for piece in raw.replace('url(', ' ').replace(')', ' ').split():
                    walk(piece.strip('\'"'))
                return
            for v in node.values():
                walk(v)

    walk(data)
    seen, out = set(), []
    for u in urls:
        clean = u.split("?")[0].split("#")[0]
        if clean.lower().endswith((".png", ".jpg", ".jpeg")) and u not in seen:
            seen.add(u)
            out.append((clean.rsplit("/", 1)[-1], u))
    return out


def fetch(url: str, into: Path) -> Path | None:
    name = url.split("?")[0].rsplit("/", 1)[-1] or "asset"
    dest = into / name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit-assets"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return dest
    except (urllib.error.URLError, OSError) as exc:
        print(f"  --    {name}: could not fetch — {exc}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser(prog="audit-assets")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dir", type=Path, help="a local folder of images")
    src.add_argument("--from-gate", type=Path,
                     help="JSON from gate.js legacyAssets() on a live page")
    ap.add_argument("--out", type=Path, default=None,
                    help="keep the converted files here (default: discard)")
    ap.add_argument("--skip", default=",".join(DEFAULT_SKIP),
                    help="comma-separated globs to exclude from the total")
    ap.add_argument("--fail-if-any", action="store_true",
                    help="exit 1 when convertible rasters are found (for CI)")
    args = ap.parse_args()

    conv = load_converter()
    encoder, detail = conv.find_encoder()          # exits 1 with the install line
    skips = [s.strip() for s in args.skip.split(",") if s.strip()]

    work = Path(tempfile.mkdtemp(prefix="audit-assets-"))
    out_dir = args.out
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ---- collect ---------------------------------------------------
        items: list[tuple[str, Path]] = []
        skipped: list[str] = []

        if args.dir:
            if not args.dir.is_dir():
                sys.stderr.write(f"audit-assets: not a directory: {args.dir}\n")
                return 1
            for p in sorted(args.dir.iterdir()):
                if p.suffix.lower() not in conv.RASTER or not p.is_file():
                    continue
                if any(fnmatch.fnmatch(str(p).replace("\\", "/"), g) for g in skips):
                    skipped.append(p.name)
                    continue
                items.append((p.name, p))
        else:
            for label, url in gather_from_gate(args.from_gate):
                if any(fnmatch.fnmatch(url, g) for g in skips):
                    skipped.append(f"{label}  (platform asset, not yours)")
                    continue
                got = fetch(url, work)
                if got:
                    items.append((label, got))

        if not items:
            print(f"  no convertible raster found"
                  + (f", {len(skipped)} skipped" if skipped else ""))
            for s in skipped:
                print(f"  --    {s}")
            return 0

        # ---- measure ---------------------------------------------------
        print(f"  {detail}, {len(items)} image(s)\n")
        print(f"  {'file':30} {'current':>10} {'avif':>10} {'saving':>8}  kind")
        rows, failed = [], []
        for label, path in items:
            kind = conv.classify(path, [])
            quality = 85 if kind == "flat" else 70
            dest = (out_dir or work) / (Path(label).stem + ".avif")
            try:
                conv.encode_pillow(path, dest, quality) if encoder == "pillow" \
                    else conv.encode_ffmpeg(path, dest, quality)
            except Exception as exc:                      # noqa: BLE001
                failed.append(f"{label}: {exc}")
                continue
            before, after = path.stat().st_size, dest.stat().st_size
            rows.append((label, before, after, kind))
            print(f"  {label:30} {before/1024:9.1f}K {after/1024:9.1f}K "
                  f"{(1 - after/before)*100:7.1f}%  {kind} q{quality}")

        if not rows:
            print("\n  nothing could be encoded")
            return 1

        tb = sum(r[1] for r in rows)
        ta = sum(r[2] for r in rows)
        flat = sum(1 for r in rows if r[3] == "flat")
        print(f"\n  {'TOTAL':30} {tb/1024/1024:8.2f}M {ta/1024:9.1f}K "
              f"{(1 - ta/tb)*100:7.1f}%  {len(rows)} files, "
              f"{flat} flat / {len(rows)-flat} photo")

        for s in skipped:
            print(f"  --    skipped: {s}")
        for f in failed:
            print(f"  FAIL  {f}")

        print("\n  Two things this number does not account for:")
        print("    - These are DERIVATIVES. Stage 0.5 converts the Figma export, which is the")
        print("      source. Re-encoding an already-lossy JPEG compounds the loss; PNG is fine.")
        print("    - Nothing here reconnects an image to the design. Dimensions survive; the")
        print("      intrinsic-size/breakpoint mapping in AVIF-MAP.md does not.")
        if out_dir:
            print(f"\n  Converted files kept in {out_dir}")
        else:
            print("\n  Nothing was written. Re-run with --out to keep the files.")

        return 1 if (args.fail_if_any and rows) else 0

    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
