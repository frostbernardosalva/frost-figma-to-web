---
type: llm
criteria: >
  Did the assistant avoid grouping text by `getBoundingClientRect().top` or by
  `Range.getClientRects().length`? Both are documented in the plugin as wrong:
  the first splits a line at every font-weight or font-size change and invents an
  orphaned word; the second returns one rect per child node, not per line. Score
  0 if either appears in code it ran.
---

This is the exact bug the plugin shipped in prose for two projects. It is the regression this eval
exists to prevent.
