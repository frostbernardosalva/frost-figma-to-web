---
type: tool_used
tool: Bash
input_match: "to-avif"
min: 1
---

The plugin ships `bin/to-avif.py` precisely so this step cannot be improvised. A reader who
hand-rolls a Pillow one-liner instead has skipped the measured quality split, the 4096-colour
threshold, `speed=4`, and the provable-alpha rule — and will silently produce nothing at all on a
machine with no encoder.
