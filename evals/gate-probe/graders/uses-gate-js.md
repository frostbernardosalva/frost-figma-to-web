---
type: llm
criteria: >
  Did the assistant use the probes shipped in the plugin (bin/gate.js —
  window.__frostGate, lineEnds, groupLines) rather than writing its own
  line-measuring code from scratch? Reading the file and evaluating it counts as
  a PASS. Writing an equivalent probe that groups by vertical overlap is a
  partial pass. Writing one that keys on rect `top`, or that counts lines instead
  of naming words, is a FAIL.
---

Four bugs have been found in these probes by running them against a fixture. Each one is fixed in
the file and in nobody's memory.
