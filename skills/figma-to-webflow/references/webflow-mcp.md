# Webflow MCP — behaviours learned the hard way

Platform facts, not project preferences. Every one of these cost real time to find once.

Call `webflow_guide_tool` once per session before anything else.

## `data_whtml_builder`

**One action per call.** Multi-action calls blow the JSON payload limit and fail to parse before
reaching the server. There is no partial success to recover from — the call simply does not arrive.

**No descendant selectors.** `.card .title` is rejected outright. Single-class selectors only. This
is a constraint on the architecture, not just the syntax: structure has to be expressible in flat
classes and combos.

**Only `:hover`, `:focus`, `:active`.** `:focus-visible` is rejected here. Add it afterwards via
`data_style_tool` with `pseudo: "focus-visible"`, which does support it.

**Reserved class names are silently dropped**, with a `dropped_style` warning. `.label` is one.
**Always read the warnings array** — the call otherwise looks like it succeeded.

**Every class used alongside another becomes a combo, *and* a global is created from the CSS rule.**
You end up with both `.sp-16` and `.ds-sp-bar.sp-16`. Put the real properties on the **combo**, or
Webflow's "clean up unused styles" will strip the globals and break the layout.

**`missing_font` warnings are cosmetic.** Custom uploaded fonts resolve correctly by family name;
Webflow just does not recognise them as installable. Verify by reading the style back, not by
trusting the warning.

## Reading styles — two ways to reach a wrong conclusion

**`truncated: true` means you did not see everything.** Re-query with a higher `limit` or a narrower
`name_path` before concluding a property is absent. A truncated result once hid a global carrying
`margin-top: 5rem`, and the conclusion drawn from it — "desktop has no margin" — was wrong.

**A value may live on the bare global, not the combo chain.** Querying `["cols-3","stack-xl"]`
returns only the two-class combo; the standalone `.stack-xl` global is a separate style with its own
properties. When a value seems missing from a combo, query the bare class name too.

## Writing values

**Write literal values with `whtml_builder`, then rewire to tokens with `data_style_tool >
update_style` using `variable_as_value`.** That two-step is the working pattern. Attempting to write
the token binding directly in the builder call does not.

Colour variables accept `hsla()` and `rgba()`, not just hex.

## Things the platform will not do

- **No shadow variable type.** Shadows ship as global classes.
- **Breakpoints are fixed** — `main` / `medium` ≤991 / `small` ≤767 / `tiny` ≤479 — and **cannot be
  variables**. A design frame at 480px maps to both `small` and `tiny`, so decide which one owns it.
- **No API write path for page custom code.** `update_page_settings` covers only SEO, Open Graph,
  slug and JSON-LD. Page-level snippets must go into section-level HTML Embeds instead, or be
  pasted by hand in the Designer.
- **No `delete_page`.** `data_pages_tool` has create, update and branch actions only. A page can be
  emptied via `remove_element`, but removing the page entry itself is a Designer action.
- **`draft: true` is silently dropped.** `bulk_update_pages` accepts it, returns 200, advances
  `lastUpdated` — and `get_page_metadata` still reports `draft: false`. Do not rely on it to take a
  page out of publishing; verify with a read, and expect to unpublish by hand.

## Cleanup

**`remove_style` works, and it is the fast path.** Earlier notes in this project recorded it as
returning a 500. Re-tested 23 Sep 2026: **212 classes removed with zero failures**, batched ~25
actions per call. Two rules:

- **Combos before their parent globals.** Remove `.a.b` before `.a`.
- **A combo and a global can share a name.** `gb2-brk-t` existed as both. Removing one leaves the
  other; `query_styles` distinguishes them by `isComboClass` and `selector`.

**`delete_variable` works too — aliases before their targets.** A variable whose value is
`{id: <another variable>}` must go first, or you are deleting a token something still points at.

**Rate limits bite on bulk deletes.** Ten `delete_asset` actions in one call returned `429
too_many_requests` for **all ten** — the batch is not partially applied, it is refused whole. Style
and variable batches of 25-28 went through fine, so the ceiling is per-endpoint, not per-action.
Back off ~60s and retry; do not assume a 429 means partial success, re-read and check.

## Figma read tools

`get_design_context` requires loading its skill first — `ReadMcpResourceTool` on
`skill://figma/figma-design-to-code/SKILL.md` — then pass
`skillNames: "resource:figma-design-to-code"`.
