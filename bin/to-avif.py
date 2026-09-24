#!/usr/bin/env python3
"""Convert raster exports to AVIF, and write the asset map the build reads back.

Stage 0.5 of the figma-to-webflow skill. This exists as a script rather than as
instructions because it is the one rule in the workflow that can silently not
happen: on a machine with no AVIF encoder, prose telling you to convert produces
PNGs that upload fine, render fine, and cost 20x the bytes with nobody the wiser.

So this never degrades. No encoder means exit 1 and a message naming the fix.

    python bin/to-avif.py <src> [--out DIR] [--map AVIF-MAP.md]

Exit codes
    0   every raster converted
    1   no usable AVIF encoder (nothing was written)
    2   at least one file failed to convert
"""

from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RASTER = {".png", ".jpg", ".jpeg"}

# Above this many distinct colours an image is treated as photographic.
#
# Not arbitrary, and 256 is too low: the Frost client-logo sprite is a flat
# graphic with 2967 colours (antialiased edges against a light ground), and at a
# 256 threshold it is misfiled as a photograph and encoded 15 points too soft.
# 4096 puts every real photograph on one side and every flat graphic on the
# other for the assets measured so far.
FLAT_MAX_COLOURS = 4096

# libavif effort, 0 (slowest) to 10 (fastest). Pillow's default is 6.
#
# Measured on the Frost photographic exports, and it is not monotonic — slower
# is NOT smaller. At quality 70, one 1440x930 photo encodes to:
#
#     speed 0  101.0K  16.3s        speed 6  100.4K  0.3s
#     speed 2  100.5K   8.2s        speed 8  101.3K  0.1s
#     speed 4   98.6K   2.3s        speed 10 109.4K  0.1s
#
# 4 is both the smallest and cheap enough for a one-time asset pass, so it is
# the default. Do not "optimise" this to 0.
SPEED = 4


@dataclass
class Result:
    src: Path
    dst: Path | None
    width: int
    height: int
    src_bytes: int
    dst_bytes: int
    quality: int
    kind: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


# --------------------------------------------------------------------------
# encoders
# --------------------------------------------------------------------------

def find_encoder() -> tuple[str, str]:
    """Return (name, detail). Raises SystemExit(1) when nothing can encode AVIF."""
    try:
        from PIL import features, __version__ as pil_version

        if features.check("avif"):
            return "pillow", f"Pillow {pil_version}"
        pillow_note = f"Pillow {pil_version} is installed but built without AVIF"
    except ImportError:
        pillow_note = "Pillow is not installed"

    if shutil.which("ffmpeg"):
        return "ffmpeg", "ffmpeg (libaom-av1)"

    sys.stderr.write(
        "to-avif: no AVIF encoder available, and nothing was written.\n"
        f"  {pillow_note}\n"
        "  ffmpeg is not on PATH\n"
        "\n"
        "Install either (ASCII only - the Windows console is cp1252):\n"
        "  pip install --upgrade 'Pillow>=11.3'    preferred: native AVIF, no system\n"
        "                                          deps, and ~40% smaller than ffmpeg\n"
        "  winget install ffmpeg                   Windows\n"
        "  brew install ffmpeg                     macOS\n"
        "  sudo apt install ffmpeg                 Linux\n"
        "\n"
        "This is deliberately fatal. Shipping the PNGs instead is the failure\n"
        "this script exists to prevent.\n"
    )
    raise SystemExit(1)


def alpha_is_used(im) -> bool:
    """True when at least one pixel is not fully opaque.

    Figma exports RGBA whether or not anything is transparent: of the 16 Frost
    assets, 14 carried a fully-opaque alpha channel that cost bytes and encoded
    nothing. Dropping it is free on those and destructive on the other two, so
    the decision is measured rather than guessed. `getextrema()[0] == 255` means
    no pixel is even slightly transparent.
    """
    if "A" not in im.getbands():
        return False
    return im.convert("RGBA").getchannel("A").getextrema()[0] < 255


def encode_pillow(src: Path, dst: Path, quality: int, speed: int = SPEED) -> None:
    from PIL import Image

    with Image.open(src) as im:
        im = im.convert("RGBA" if alpha_is_used(im) else "RGB")
        im.save(dst, format="AVIF", quality=quality, speed=speed)


def encode_ffmpeg(src: Path, dst: Path, quality: int, speed: int = SPEED) -> None:
    # libaom crf runs 0 (best) to 63 (worst), inverse of Pillow's quality.
    crf = max(0, min(63, round((100 - quality) * 63 / 100)))
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         # -still-picture takes a value. Without the "1" ffmpeg consumes the
         # output path as its argument and dies on "At least one output file
         # must be specified", which reads like a bug in the caller.
         "-c:v", "libaom-av1", "-crf", str(crf), "-cpu-used", str(speed),
         "-still-picture", "1", str(dst)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip().splitlines()[-1] if proc.stderr else "ffmpeg failed")


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

def classify(src: Path, flat_globs: list[str]) -> str:
    """'flat' or 'photo'. An explicit --flat glob always wins over the guess."""
    for pattern in flat_globs:
        if fnmatch.fnmatch(src.name, pattern):
            return "flat"
    try:
        from PIL import Image

        with Image.open(src) as im:
            colours = im.convert("RGBA").getcolors(maxcolors=FLAT_MAX_COLOURS)
        return "photo" if colours is None else "flat"
    except Exception:
        # No decoder, so no colour count. Guessing wrong toward 'photo' costs a
        # few KiB; guessing wrong toward 'flat' costs visible artefacts on text
        # and thin strokes. Name flat graphics with --flat on the ffmpeg path.
        return "photo"


def probe_header(path: Path) -> tuple[int, int, bool]:
    """(width, height, has_alpha) straight from the file header, no decoder.

    The ffmpeg path exists precisely for machines with no Pillow, so it cannot
    use Pillow to measure. PNG carries its dimensions and colour type in the
    IHDR chunk; JPEG never has alpha and carries dimensions in its SOF marker.

    `has_alpha` here means "the format declares a channel", not "a pixel is
    transparent" — that needs a decode. Keeping an unused channel costs a little
    size; dropping a used one is destructive, so this errs toward keeping.
    """
    data = path.read_bytes()

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w = int.from_bytes(data[16:20], "big")
        h = int.from_bytes(data[20:24], "big")
        colour_type = data[25]          # 4 = grey+alpha, 6 = RGBA
        return w, h, colour_type in (4, 6)

    if data[:2] == b"\xff\xd8":         # JPEG: walk the marker segments
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h = int.from_bytes(data[i + 5:i + 7], "big")
                w = int.from_bytes(data[i + 7:i + 9], "big")
                return w, h, False
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")

    raise ValueError(f"cannot read dimensions from {path.name}")


def probe(path: Path) -> tuple[int, int, bool]:
    """(width, height, keeps_alpha). Uses Pillow when present, headers otherwise."""
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size[0], im.size[1], alpha_is_used(im)
    except ImportError:
        return probe_header(path)


# --------------------------------------------------------------------------
# asset map
# --------------------------------------------------------------------------

def write_map(path: Path, results: list[Result], encoder_detail: str,
              q_photo: int, q_flat: int) -> None:
    done = [r for r in results if r.ok]
    src_total = sum(r.src_bytes for r in done)
    dst_total = sum(r.dst_bytes for r in done)
    ratio = (dst_total / src_total * 100) if src_total else 0

    lines = [
        f"# AVIF asset map — {path.parent.name}",
        "",
        "Generated by `bin/to-avif.py`. Do not hand-edit the table: re-run the script.",
        "The **asset id** and **used at** columns are yours to fill after upload.",
        "",
        "| file | intrinsic | asset id | used at |",
        "|---|---|---|---|",
    ]
    for r in done:
        lines.append(f"| {r.dst.name} | {r.width}x{r.height} | | |")

    lines += [
        "",
        "SVGs stay SVG — AVIF is raster only.",
        "`background-size` uses the intrinsic **width** in px (rule 4); every other "
        "measurement is rem.",
        "",
        f"Encoded with {encoder_detail}: quality {q_photo} for photographs, "
        f"{q_flat} for flat graphics.",
        f"**{src_total / 1024 / 1024:.2f} MiB → {dst_total / 1024:.1f} KiB "
        f"({ratio:.1f}%)** across {len(done)} files.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="to-avif",
        description="Convert raster exports to AVIF and write the asset map.",
    )
    ap.add_argument("src", type=Path, help="directory of exports, or a single file")
    ap.add_argument("--out", type=Path, default=None,
                    help="output directory (default: alongside the sources)")
    ap.add_argument("--map", dest="map_path", type=Path, default=None,
                    help="write the asset map here (default: <out>/AVIF-MAP.md)")
    ap.add_argument("--quality-photo", type=int, default=70)
    ap.add_argument("--quality-flat", type=int, default=85)
    ap.add_argument("--speed", type=int, default=SPEED,
                    help=f"libavif effort 0-10 (default {SPEED}; see SPEED in this file)")
    ap.add_argument("--flat", default="",
                    help="comma-separated globs always treated as flat graphics")
    ap.add_argument("--dry-run", action="store_true",
                    help="classify and report, write nothing")
    args = ap.parse_args()

    encoder, detail = find_encoder()

    if args.src.is_file():
        sources = [args.src] if args.src.suffix.lower() in RASTER else []
        root = args.src.parent
    else:
        sources = sorted(p for p in args.src.iterdir()
                         if p.suffix.lower() in RASTER and p.is_file())
        root = args.src

    if not sources:
        sys.stderr.write(f"to-avif: no .png/.jpg/.jpeg found in {args.src}\n")
        return 2

    out_dir = args.out or root
    out_dir.mkdir(parents=True, exist_ok=True)
    flat_globs = [g.strip() for g in args.flat.split(",") if g.strip()]

    print(f"to-avif: {detail}, {len(sources)} raster file(s)"
          f"{' [dry run]' if args.dry_run else ''}\n")

    results: list[Result] = []
    for src in sources:
        kind = classify(src, flat_globs)
        quality = args.quality_flat if kind == "flat" else args.quality_photo
        dst = out_dir / (src.stem + ".avif")
        w, h, keeps_alpha = probe(src)
        alpha = "alpha" if keeps_alpha else "  -  "
        src_bytes = src.stat().st_size

        if args.dry_run:
            results.append(Result(src, dst, w, h, src_bytes, 0, quality, kind))
            print(f"  {src.name:30} {kind:5} q{quality} {alpha}  {w}x{h}")
            continue

        try:
            encode = encode_pillow if encoder == "pillow" else encode_ffmpeg
            encode(src, dst, quality, args.speed)
            dst_bytes = dst.stat().st_size
            results.append(Result(src, dst, w, h, src_bytes, dst_bytes, quality, kind))
            print(f"  {src.name:30} {kind:5} q{quality} {alpha}  {w}x{h:<6} "
                  f"{src_bytes / 1024:8.1f}K -> {dst_bytes / 1024:7.1f}K "
                  f"({dst_bytes / src_bytes * 100:4.1f}%)")
        except Exception as exc:  # noqa: BLE001 - reported per file, never swallowed
            results.append(Result(src, None, w, h, src_bytes, 0, quality, kind, str(exc)))
            print(f"  {src.name:30} FAILED  {exc}")

    done = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    if not args.dry_run and done:
        map_path = args.map_path or (out_dir / "AVIF-MAP.md")
        write_map(map_path, done, detail, args.quality_photo, args.quality_flat)
        src_total = sum(r.src_bytes for r in done)
        dst_total = sum(r.dst_bytes for r in done)
        print(f"\n  {'TOTAL':30} {'':12} {src_total / 1024 / 1024:7.2f}M -> "
              f"{dst_total / 1024:7.1f}K ({dst_total / src_total * 100:4.1f}%)")
        print(f"  map written: {map_path}")

    if failed:
        sys.stderr.write(f"\nto-avif: {len(failed)} file(s) failed\n")
        return 2

    if not args.dry_run:
        print("\n  Sources are kept as the source of truth. Upload the AVIFs, rebind every\n"
              "  reference, verify zero legacy references, and only then delete the old ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
