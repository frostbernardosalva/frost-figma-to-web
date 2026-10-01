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
- ~~**No API write path for page custom code.**~~ **Corrected 2026-10-01 — there is one.**
  `data_scripts_tool` carries `set_site_freeform_code` and `set_page_freeform_code`, both of which
  write and read back byte-correct. The limitation is real but belongs to a *different* call:
  `update_page_settings` covers only SEO, Open Graph, slug and JSON-LD. A whole behaviour layer was
  written and published through the scripts tool without pasting anything by hand. See
  **Custom code in Webflow** below before using it — a publish can leave more than one copy.
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

## Findings from the Frost landing build

Each of these cost time on a real conversion.

### The WHTML builder puts a `<form>`'s class on the `.w-form` wrapper

The real `<form>` is created **unclassed and unsized**. If the wrapper's class makes it a flex or
grid container, the unclassed form shrink-to-fits and every field inside collapses to the `<input>`'s
intrinsic ~195px — at every breakpoint, which is the giveaway (a constant where a responsive value
should be). Style the FormForm element separately, by id, after the build. **This is the highest
value item here**: it is the collapsed-form defect from the previous project, reached by a different
route, and it will recur on every form built through this path.

**A text input cannot exist outside a form.** The builder rejects it outright — *"Text Field can
only be placed in a Form"* — so a lone field specimen has to be wrapped in a `FormForm` even when
the design shows no form. That wrapper then takes the class you meant for the form, per the trap
above.

**Styling the real form takes two calls, not one.** `data_style_tool > create_style` to make the
class, then `data_element_tool > set_style` with `style_names` on the `FormForm` element's id.
Passing the class in the markup lands it on the wrapper every time.

**The general shape is worth more than the instance: when a target silently inserts a wrapper, a
correct measurement of the wrapper is not a measurement of the thing you meant.**

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

## Replacing a live site's assets — the rebind procedure

**Status: built and dry-tested, never run on a real conversion.** The Frost site has no legacy
raster left to rebind, so phases 1–5 below are reasoned from the recorded traps and exercised
against fixtures — not demonstrated end to end. **Run it on one asset, on a page you can afford to
break, before it goes near a client site.**

`bin/audit-assets.py` sizes the opportunity. `bin/rebind-plan.py` turns page scans into an ordered
plan that is also the rollback record. This is the execution.

**The danger that shapes all of it:** `gate.js legacyAssets()` inspects **one rendered page at one
width**. An asset can also be referenced on a page you did not scan, or only at a breakpoint you did
not render — a mobile-only background is invisible at 1440. Deleting because one page looks clean is
how you silently break another. **Phase 5 is gated on coverage, not on a single green check.**

1. **Upload**, using the name in the plan. Verify each returns `contentType: "image/avif"` **and a
   new asset id** — identical bytes return the *old* id under its old display name.
2. **Rebind** one reference at a time from the plan. `img` entries are element bindings; `css`
   entries are `background-image` on the named selector.
3. **Publish, then confirm the stylesheet hash changed.** `publish_site` returns before the CSS is
   live, so a correct fix otherwise reads as a failure and gets "fixed" twice.
4. **Re-scan every page at every width in the plan's coverage list** and require
   `legacyAssets()` → **zero** on all of them.
5. **Only then delete, five at a time.** Ten in parallel returned 429 and the batch was refused
   whole. **Refuse this phase if phase 4 is incomplete for any scanned page.**

Never automate phase 5, and never fold it into an earlier phase. Assets the plan could not replace
are listed as warnings and must not be deleted at all.

**Out of scope, deliberately:** assets referenced only from CMS items are invisible to a
rendered-page scan. Do not assume a clean scan means an unused asset.

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

**Give each element its own combo, and understand why** — the section below is the reason.

`backdrop-filter` is accepted by `update_style`, and Webflow adds the `-webkit-` prefix itself.

## A combo must be registered against the exact class chain the element wears

`create_style` with `parent_style_names` builds the combo against **the chain you name**, and
Webflow rejects it — *"One or more styles not found"* — if no element wears that exact chain. A
modifier scoped to `["mt_badge"]` will not attach to an element wearing `mt_badge mt_badge-generic`.

Read the element's `styleNames` first and pass the whole chain. The order matters too: it is the
chain, not a set.

## Components, and the page shell that makes page two cheap

**Promote, do not rebuild.** `transform_element_to_component` turns an existing, already-gated
element into a component in place. Nothing is reconstructed, and re-measuring after promotion
returned figures identical to the pre-component ones at all three widths — which is the check worth
running, because it is the one that would catch a promotion that quietly re-laid-out its contents.

**Then make a shell page** holding the component instances in page order with one placeholder
section. `create_page` takes `duplicateOf`, so a new page is one call and arrives with every shared
block correct and gated. **Element ids are preserved through duplication**, scoped to the new page,
so the same ids address the instances on every page made from the shell — which makes setting props
across several new pages a batch rather than a hunt.

**What a prop can and cannot do:**

- **A text prop needs a default before anything binds to it.** Binding without one *empties the
  element*, and it still publishes, still renders, and still looks like a component — only the
  measurement catches it.
- **A boolean bound to visibility** is the right tool for a block that some pages drop. It is one
  prop and no extra style scope, where a variant would carry a whole scope for a show/hide.
- **A prop cannot change a class**, and a variant keys on a class name rather than an element, so
  "which nav item is active" is not expressible as either. That is Stage 6 script.
- **Slots accept component instances only, never markup.** Where a page needs to wrap something else
  in a shared band, it uses the band's *classes* directly rather than the component.

## Component variants enlist an element only via its FIRST class

`set_variant_styles` publishes exactly the rule you ask for:

```css
.the_class:where(.w-variant-<variant-id>) { background-color: …; }
```

**Webflow adds the `w-variant-<id>` class to an element only when the variant styles the class that
element wears FIRST.** Style a second or later class and the rule publishes and matches nothing.

| Element wears | Variant styles | Enlisted? |
|---|---|---|
| `nav` | `nav` | **yes** |
| `nav_link nav_link-active` | `nav_link` (first) | **yes** |
| `section hero` | `hero` (second) | **no** |
| `container hero_content` | `hero_content` (second) | **no** |

**The fix is not a workaround — style the first class too.** Any property on the first class enlists
the element, and the rules already written against later classes start matching by themselves.
Webflow inserts the class directly after the first one, which is how you confirm it:

```html
<div class="section w-variant-877bbd96-… hero">
```

**Two escape routes that do not exist**, both tested rather than assumed:

- **A component instance root cannot take a class.** `set_style` on the instance answers
  *"This element doesn't support styles"*, so a combo class is not available.
- **A base-breakpoint override does not enlist.** It is the class that decides, not the breakpoint.

**Why this one is worth the space.** It passes every check short of the render: the write succeeds,
the read-back returns the stored value, and the published CSS contains the rule. Only the element's
class list disagrees, silently. On the project that found it, this shipped a themed band **still
wearing the wrong background, with the new ink already applied to the text on top of it** — through
a numeric gate that passed, because a theme changes no dimensions.

Where the class API genuinely cannot reach — a descendant selector, say — Webflow does emit
`data-wf--<component>--variant="<name>"` on the instance root, which is a reliable hook for custom
code and cannot match an instance still on its base variant.

## A value you have only ever seen through a variant is not the base value

A variant exists to *change* values, so reading a class's behaviour off a page that uses one tells
you **the variant's** value, not the class's.

On the project that found this, three consecutive pages used a "Light" hero variant, which flattens
the label's line-height to 1. The base carries 1.4. The fourth page used the base, reused the same
class, and came out **+5.59px** — exactly `14 × 0.4`.

**Before reusing a class on a page that does not carry the variant, read the base rule** — or
measure on a page that uses the base. The variant's own published rule states it plainly:

```css
.the_label:where(.w-variant-…) { line-height: var(--lh-flat); }
```

Anything listed there is a value you have *not* seen at base.

**The same shape applies to platform resets.** Webflow's base stylesheet puts `margin-bottom: 10px`
on every `<p>`. If each page carries its own reset in page CSS, the page that forgets it ships 10px
under every paragraph, silently — and "remember to copy the reset" is a step nobody can see was
skipped. Put it in **site-level** custom code once, where a new page inherits it by existing.

## Regrouping across breakpoints: `display: contents`

Webflow cannot re-parent an element per breakpoint, and it has no descendant selectors, so a block
whose three breakpoints are three different *groupings* — not one layout reflowing — looks like it
needs its markup duplicated.

It usually does not. **`display: contents` on a wrapper removes that wrapper's box while keeping its
children**, so one markup can produce several groupings by switching wrappers between `contents` and
`flex` per breakpoint. No duplicated elements, no second component, and nothing to keep in sync.

Reach for this before shipping an element twice and hiding one copy.

## The cascade: source order decides, and source order is creation order

**Webflow emits every base rule before every media query.** Two selectors of equal specificity are
therefore settled by *when the class was created*, not by where you would expect the cascade to put
them. Both failures below store correctly, read back correctly, publish, and do nothing. Neither is
visible to any check except rendering at the right state **and** the right width.

**A breakpoint override on a base class defeats a modifier that only sets the property at base.**
`.box` sets `border-color` at `medium`; `.box-open` sets it at base. At 980 the media rule wins,
because a media rule beats a base rule regardless of which class is "more specific" in intent — the
two selectors are tied at one class each. An open dropdown lost its border below 992 this way.

> **If a base class overrides a property at a breakpoint, every modifier that sets that same
> property must override it at that breakpoint too.**

**A shared modifier only works on blocks whose base class is older than it.** A modifier reused
across blocks — `_field_box-focus` on both `_field_box` and `_sel_box` — is a single class competing
with a single class. It wins on the base class that existed before it and loses on every block built
afterwards. It works on the first block you built and silently fails on the rest.

> **Scope a reused modifier as a combo.** `update_style` with
> `parent_style_names: ["<base>"]` produces `.base.modifier` at (0,2,0), which beats any single
> class whatever the order. One call per block that reuses the modifier.

**A combo can only be created where an element already wears the chain.** Scoping a modifier to a
class no element has yet paired it with fails with *"Style &lt;base&gt; > &lt;modifier&gt; not found"*. Build
the element first, then scope.

## Cleanup leaves the classes behind

**Removing an element does not remove its classes, and the rebuild silently renames.** Delete a
block's elements, rebuild it with the same markup, and the builder finds the old class names still
occupied — so it creates `_btn_icon-1`, `_btn_icon-2` beside them. The build looks correct and every
selector is subtly wrong.

**Delete an element's classes before rebuilding it.** `remove_style`, then `rename_style` if a
suffixed twin already exists. Standing check after any teardown-and-rebuild: grep the published CSS
for `-[0-9]$` on your own prefix.

## Assets upload without the Designer; the builder will not place them

`create_asset` plus the S3 form post works headlessly and the asset is live and addressable. But
`data_whtml_builder` refuses to place a freshly created asset in an `<img>` — it reports *"the image
does not exist in asset library"* and **skips the element silently**, leaving the surrounding markup
built and the image absent. On one build that dropped 44 `<img>` elements.

**Reference the asset from CSS instead.** `background-image: url(<hostedUrl>)` with an explicit
`background-size` and `background-repeat: no-repeat` is written by `data_style_tool` without
complaint, and it collapses many elements into one class. 44 skipped images became 3 classes.

---

# Custom code in Webflow

For behaviour Webflow cannot express: accordions, carousels, scroll-triggered animation, form
prefill. Each rule below traces to a defect that shipped.

**None of this applies to a target you write files for.** On the HTML target there is no API to
refuse you, no paste box to truncate your script, and no second writer to clobber it — see
`targets/html.md`.

### Custom code HAS an API write path — use it, then count the copies

**`data_scripts_tool` writes custom code.** `set_site_freeform_code` and `set_page_freeform_code`
both store and read back byte-correct, and `get_*` reads the existing block. A complete behaviour
layer — accordions, a dropdown, an expand-all control, a hover reveal across five pages — was
written, published and verified this way with **nothing pasted by hand**. Read the existing block
first and merge: these calls replace the whole field, so a blind write destroys what is already
there.

**The mirror rule still stands, and matters more now, not less.** Code that lives only in a Webflow
settings box exists nowhere else. Keep the complete paste — including its `<script>` / `<style>`
tags — in the project's `custom-code/` folder with a header comment naming where it goes, and diff
the published page against that mirror after every push. On one project the page-level CSS for
three pages existed *only* inside Webflow until the behaviour pass went looking for it.

### Standing rule: anything the API genuinely cannot write goes in the repo as a paste

**When a Webflow API call refuses something, do not work around it by changing the design
decision.** Write the thing as a complete, paste-ready file in the project's `custom-code/`
folder, with a header comment naming exactly where it goes, and tell the developer to paste it.

The API refuses more than it documents. Known so far:

- **Size variables reject CSS expressions.** `create_size_variable` and `update_size_variable` both
  fail with *"An internal error occurred"* on a `custom_value` such as
  `clamp(1.5rem, 2.0833vw, 2.5rem)` — despite the field being documented as accepting an arbitrary
  CSS expression. So fluid type and spacing scales cannot be built as variables.
- **IX3 interactions may be stored but never published.** Authored through
  `data_interactions_tool`, accepted, and listed as visible on the page — yet absent from the
  published HTML, which carried zero `data-w-id`. Scroll-state toggling fell back to a paste.
- **A style write can succeed, be stored, and never reach the published CSS.** Writing breakpoint
  rules returned success; `query_styles` read them back correctly; two publishes later the
  stylesheet contained none of them and its hash had not changed — while other components' rules
  from the same session published fine. Re-issuing the identical writes produced a new hash and
  the correct CSS. **Reproduced twice in one session.**

  The consequence is bigger than the bug: **API read-back is not verification on this target.**
  A style is not built until it is present in the published CSS or visible in a render. Symptom:
  one component's breakpoint rules missing while others are fine, plus an unchanged stylesheet
  hash across a publish. Remedy: re-issue the same writes, publish, confirm against the CSS.

- **Positioning is not writable through `data_style_tool` either.** `position`, `right`, `bottom`,
  `z-index` and `pointer-events` are accepted, appear in the read-back, and never reach the
  published CSS — same failure shape as `box-shadow`. To overlay an element without them, use
  `width: fit-content` + `margin-left: auto` + a negative `margin-top` equal to its own height.
  **Keep a running list of non-writable properties**; rediscovering each one costs a publish cycle.

- **`box-shadow` cannot be written through `data_style_tool`.** Passing
  `inset 0 -1px 0 0 var(--token)` is accepted, and the style reads back with `box-shadow` bound to
  the variable — but the geometry is gone and the published page computes `box-shadow: none`. The
  API keeps the colour and discards the rest. Verified on a live build.
- ~~**No write path for page custom code** at all~~ — **wrong, corrected 2026-10-01.** That is true
  of `update_page_settings`, which covers SEO, Open Graph, slug and JSON-LD only and silently drops
  its `draft` flag. Custom code has its own tool and it works: `set_site_freeform_code` and
  `set_page_freeform_code` on `data_scripts_tool`.

**Prefer page-level custom code over site-wide.** A root font-size rule pasted site-wide rescales
every other page on that site, including design systems built earlier. Page settings scope it to
the one page being built. Only go site-wide when the effect is genuinely meant to be global.

### Keep a source of truth outside the Designer

Snippets pasted into Webflow exist nowhere else unless you mirror them in the project repo. A
mirrored file is **not wired to anything** — editing it changes nothing until it is pasted and
published. Keep the two in sync by hand and say so in the project's README, or the mirror silently
becomes fiction.

Each mirrored file should be the complete paste, including its `<script>` / `<style>` tags, with a
header comment naming what it does, where it lives, and what it depends on.

### Paste carefully — pastes arrive truncated

**Three pastes in one project arrived with lines silently missing.** One lost a key and a closing
brace from an array; another lost a transition line and an entire loop. Both produced a syntax
error, and **a syntax error kills the whole file** — so the symptom is "nothing happens at all", not
"one feature is broken".

Before publishing:

1. Compare the character count against the source file.
2. Open the DevTools console on the published page. A syntax error shows immediately and names the
   token, which is far faster than inferring it from behaviour.

### A publish can leave a SECOND, stale copy of your script in the page

**Write your script so a second copy is harmless, because you cannot stop one arriving.** Site-level
footer code was pushed through the API and read back byte-correct. The published page then carried
it **twice** — once reformatted inside a `w-embed w-script` div mid-body, once near `</body>`. A
later publish left a copy of the **previous version** of the script beside the current one, on one
page out of five. `query_elements` finds no embed element and the page's own custom-code slots are
empty, so neither copy is visible or deletable in the Designer. Republishing converged it to one.

This is the `box-shadow` / breakpoint-write family again: **stored correctly, published wrong, fixed
by re-issuing.**

**Why it is worse than a normal duplicate.** Two copies of a toggle means every click runs two
handlers and the second undoes the first, so the symptom is *"the accordion does nothing"* —
identical to a script that never loaded, and it sends you hunting the wrong bug.

Two defences, both one line:

```js
if (window.__myNamespace) return;   // a second copy no-ops
window.__myNamespace = 1;
```

and, because the first copy can land **mid-body**, never depend on parse position — defer to
`DOMContentLoaded` rather than assuming the markup above the script is all there is.

**Then count.** After publishing, fetch the page and count occurrences of a token from your script.
`grep -c` counts *lines*, and one of the copies is reformatted — count occurrences, not lines, or
the check silently passes.

### Combo classes can bake in `display`

Webflow writes an element's *current* display state into a combo created while the element is
visible. Four accordion panels picked up `display: block` this way and were forced permanently open.

Set `display` **inline** from script, which outranks any class, so it cannot happen again.

### API writes and Designer saves clobber each other

A `margin-top: auto` written through the API was silently replaced by a Designer save. **If the
Designer is open, prefer making style changes there.** Otherwise the last writer wins and neither
side reports a conflict.

### Do not grow a parallel responsive layer

A hand-written CSS block in Page Settings is a second styling system. If it uses different
breakpoints from Webflow's native ones, the two disagree in the bands between them, and the
disagreement surfaces as a bug that appears at one viewport width and nowhere else.

Worse, it constrains the design system: a variable's modes bind to Webflow's breakpoints, so a token
minted while the two maps disagree applies its values into a band the custom layer treats
differently. **Settle the breakpoint map before writing responsive custom CSS**, and keep the layer
shrinking rather than growing.
