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

## Findings from the Frost landing build

Each of these cost time on a real conversion.

### The WHTML builder puts a `<form>`'s class on the `.w-form` wrapper

The real `<form>` is created **unclassed and unsized**. If the wrapper's class makes it a flex or
grid container, the unclassed form shrink-to-fits and every field inside collapses to the `<input>`'s
intrinsic ~195px — at every breakpoint, which is the giveaway (a constant where a responsive value
should be). Style the FormForm element separately, by id, after the build. **This is the highest
value item here**: it is the collapsed-form defect from the previous project, reached by a different
route, and it will recur on every form built through this path.

### `grid-row-gap` accepts variables; `row-gap` does not

`row-gap` returns *"Property row-gap does not support setting a variable of type length"* and the
whole `update_style` action fails atomically, taking its other properties with it. The legacy
aliases `grid-row-gap` / `grid-column-gap` accept variable ids — Webflow's own design-system classes
use them. Remove the modern longhand when you switch, or both land in the CSS and cascade order
decides.

### `-webkit-appearance` is rejected

*"Invalid style property -webkit-appearance"*, and it fails the whole action. Unprefixed
`appearance` is accepted and is enough for `<select>` on current browsers.

### `alt` is a setting, not an attribute

`data_element_tool > set_attributes` with `name: "alt"` fails with `An internal error occurred`.
Use `data_element_settings_tool > set_settings` with `key: "altText"`.

### Builder CSS written as `.is-x` creates a stray unprefixed global

Passing `.is-x { … }` in the builder's `css` produces an **empty combo** plus a global `.is-x`
holding the rules. Renaming the combo later strands the rules on the old global name and the element
silently loses them. Write `.parent.is-x { … }`.

### Large WHTML payloads fail with `ECONNRESET`

One action carrying ~40 CSS rules and a full section of markup dropped the socket. Nothing is
applied, so retrying is safe, but split into three or four actions.

### AVIF is supported natively

`create_asset` on a `.avif` returns `contentType: "image/avif"`. No `compress_assets` step needed.

### Asset deletes are soft, and identical bytes resurrect the old record

Re-uploading a byte-identical file returns the **old asset id**, still carrying the old display
name. Rename it, or the asset library keeps showing a name from a different project.

### `publish_site` returns before the CSS is live

Verify the published stylesheet **hash changed** before trusting any post-publish measurement.
Otherwise a correct fix reads as a failure and gets "fixed" twice.

### Rate limits

10 parallel `delete_asset` actions returned 429 and the batch was refused whole. Five at a time
works.

## Interactions — verify on the published page, not the response

### IX3 interactions may never reach the published output

On the Frost site, two `wf:scroll` interactions were created, accepted, read back byte-correct, and
returned by `list_interactions` with `visibleOnPageId` as visible on the page. **They never fired.**
The published HTML contains **zero `data-w-id` attributes** and no ix3 chunk — on that page and on
every other page of the site. Interactions are stored and scoped, and simply do not publish.

Everything an automated check could reach said pass. The guide's own warning — *"a successful create
is not proof it played"* — is exactly this. **Grep the published page for `data-w-id` before
believing an interaction exists**, and fall back to a pasted snippet when it does not.

### The right shape, for when they do publish

- Toggles (`enter`, `leave`, `enterBack`, `leaveBack`) live **inside `scrollTriggerConfig`**,
  alongside the required `start` and `end`.
- A class toggle is a Set: `tt: 3`, `timing: {duration: 0}`,
  `properties: {"wf:class": {"class": {"operation": "addClass", "selectors": [styleBlockId]}}}`.
- **Two interactions are needed for an on/off state.** Scroll triggers ignore `assignedGroupId`, so
  one interaction cannot route different toggles to different timelines, and `reverse` is
  meaningless on a Set.

## Styles are class-based, not selector-based

There is no way to express `.wrapper.is-active .child` through the style API. A state that changes
several elements is **the same modifier class added to all of them**, each with its own combo:

```
.nav_band.is-scrolled              background
.nav_link.is-scrolled              color
.nav_icon.is-light.is-scrolled     display
```

One `wf:class` action carries up to 20 targets, so a single action can add the modifier to all of
them at once. The modifier must also exist as a **standalone style block** for IX3 to address it by
id — the one case where the "stray unprefixed global" is deliberate rather than a mistake.

`backdrop-filter` is accepted by `update_style`, and Webflow adds the `-webkit-` prefix itself.
