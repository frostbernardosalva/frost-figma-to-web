#!/usr/bin/env python3
"""Report missing tools this plugin's scripts need. NEVER blocks.

Run from the SessionStart hook. Its whole job is to make one failure mode
visible early: bin/to-avif.py cannot convert without an AVIF encoder, and a
conversion that skips the AVIF step produces a page that works, renders
correctly, and ships 20x the bytes. Nobody notices that at review time.

This warns and gets out of the way. A session that has nothing to do with
Webflow must not be interrupted because ffmpeg is absent, so every exit path
here is 0.
"""

from __future__ import annotations

import shutil
import sys


def main() -> int:
    missing = []

    try:
        from PIL import features, __version__ as pil_version
        if features.check("avif"):
            return 0                                    # silent when fine
        missing.append(f"Pillow {pil_version} has no AVIF support")
    except ImportError:
        missing.append("Pillow is not installed")

    if shutil.which("ffmpeg"):
        # Usable, but worth saying: on the Frost assets ffmpeg produced a file
        # 41% larger than Pillow at the same quality (10.3K vs 7.3K).
        print("[frost-webflow] AVIF via ffmpeg. Pillow compresses better "
              "(~40% smaller) - pip install --upgrade 'Pillow>=11.3'")
        return 0

    print("[frost-webflow] No AVIF encoder found - " + "; ".join(missing) +
          ", ffmpeg not on PATH.\n"
          "                Stage 0.5 (asset conversion) will refuse to run.\n"
          "                Fix: pip install --upgrade 'Pillow>=11.3'")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:                            # noqa: BLE001
        # A broken dependency check must never be the thing that breaks a
        # session. Say what happened, exit clean.
        print(f"[frost-webflow] dependency check failed to run: {exc}")
        sys.exit(0)
