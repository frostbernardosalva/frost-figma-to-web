---
type: llm
criteria: >
  Did the assistant convert the rasters to AVIF, or — if no AVIF encoder was
  available — state plainly that the conversion did NOT happen and what to
  install? Score 0 if it shipped, uploaded or declared the PNGs ready without
  converting and without saying the conversion was skipped. Reporting a clean
  failure is a PASS; quietly proceeding is the failure this grader exists for.
---

The one rule in this workflow that can silently not happen. A page built from unconverted PNGs
works, renders correctly, and ships 20x the bytes, so nothing downstream catches it.
