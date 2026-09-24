# Figma read tools

Target-neutral: this is how the design is read, whatever gets built from it.

`get_design_context` requires loading its skill first — `ReadMcpResourceTool` on
`skill://figma/figma-design-to-code/SKILL.md` — then pass
`skillNames: "resource:figma-design-to-code"`.

## `leading-[normal]` is not the browser's `normal`

Figma's `normal` for Sailec is **1.25**; a browser's for the same face is ~**1.45**. Transcribing
the keyword one-to-one made a heading 92.8px against a design of 80 and cascaded 14px of drift down
the column. Carry the measured ratio as a token, never the keyword.
