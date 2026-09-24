#!/usr/bin/env python3
"""Create the input each eval case expects.

    python evals/scaffold.py <target-dir>

asset-prep needs ./exports — a handful of PNGs shaped like a real Figma export
set: four breakpoints of one photograph plus one flat graphic, all RGBA with an
unused alpha channel, which is what Figma actually produces.

gate-probe needs ./page.html — a heading whose rendered line breaks are known,
containing the mixed-font-size case that makes a `top`-keyed probe report a line
that is not there.
"""

from __future__ import annotations

import sys
from pathlib import Path


def make_exports(root: Path) -> None:
    from PIL import Image, ImageDraw

    out = root / "exports"
    out.mkdir(parents=True, exist_ok=True)

    # Photographic: smooth multi-channel gradients plus mild noise.
    #
    # This has to behave like a photograph in TWO ways or the eval measures the
    # wrong thing. The first attempt used `(x*7 + y*13) % 256`, which produces
    # only 256 distinct colours — so it was classified FLAT — and 3px vertical
    # striping, which is pathological for AVIF: the output came out 13x LARGER
    # than the PNG. A synthetic pattern is not a photograph.
    #
    # Smooth gradients give the >4096 colours that drive the photo branch, and
    # the low-frequency structure that makes AVIF actually compress.
    import random

    for w, h, bp in [(1920, 1021, "xxl"), (1440, 930, "main"), (980, 753, "md"), (480, 940, "sm")]:
        rnd = random.Random(bp)                    # deterministic per breakpoint
        im = Image.new("RGB", (w, h))
        px = im.load()
        for y in range(h):
            fy = y / h
            row_jitter = rnd.randint(-4, 4)
            for x in range(w):
                fx = x / w
                r = int(30 + 200 * fx + 20 * fy) + row_jitter
                g = int(60 + 120 * fy + 60 * (1 - fx))
                b = int(90 + 140 * (fx * fy) ** 0.5)
                px[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        # Figma exports RGBA even with nothing transparent — reproduce that, so
        # the converter's provable-alpha path is exercised.
        im.convert("RGBA").save(out / f"hero-photo-{bp}.png")

    # Flat graphic: few colours, must be classified flat and encoded at 85.
    logo = Image.new("RGBA", (1200, 140), (255, 255, 255, 255))
    d = ImageDraw.Draw(logo)
    for i in range(5):
        d.rectangle([i * 240 + 20, 40, i * 240 + 200, 100], fill=(20, 20, 40, 255))
    logo.save(out / "client-logos.png")

    print(f"  exports/      6 PNGs  ({sum(p.stat().st_size for p in out.glob('*.png')) / 1024 / 1024:.1f} MiB)")


PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Line break probe</title>
<style>
  body { font-family: Georgia, serif; margin: 0; padding: 32px; }
  h1 { width: 340px; font-size: 40px; line-height: 1.25; font-weight: 400; }
  h1 .small { font-size: 28px; }
</style></head>
<body>
  <h1 id="headline">We are <span class="small">a design</span> agency built for scale.</h1>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        return 2
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    print(f"scaffolding into {root}")
    make_exports(root)
    (root / "page.html").write_text(PAGE, encoding="utf-8")
    print("  page.html     renders as 3 lines: "
          "'We are a design' / 'agency built for' / 'scale.'")
    print("                a `top`-keyed probe reports 4, splitting 'We are' from 'a design'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
