# Target: vanilla HTML / CSS / JS

**Status: a full page, measured.** The Frost landing page — six sections, header, footer — was
built to this file and gated at four breakpoints. Every gate row passes at every width. **Five of
seven sections are exact at all four widths**; page totals land +7 / +9 / +69 / −6 against the
Webflow build of the same design, which itself landed +9 / +9 / +8 / +4 against the frames. The
seven containers return one number at twelve widths from 1920 down to 375, with no horizontal
scroll. The S1 headline inversion reproduces — the defect that shipped on the Webflow build and
that a line-count check passes.

Three things it does **not** show, and they are the honest limits:

- **No behaviours.** No sticky header, no hamburger, no carousel. All JavaScript is unbuilt.
- **The design was already solved.** An 818-line build log records every defect and measurement, and
  Stages 0–3 were reused rather than redone. This tests the target, not the workflow.
- **One section is 74px over at one width.** Section 6 at 980, whose design frame carries 102px of
  unexplained slack. Left visible rather than shaved to fit.

See `../../rule-classification.md` for which rules carried to this target and which did not.

The stages in `SKILL.md` are unchanged. Only the bindings below differ.

---

## Output shape

```
dist/
  index.html
  styles.css
  assets/            the AVIFs and SVGs from Stage 0.5, committed
```

One stylesheet, in token order: `:root` custom properties, then media queries redefining them, then
layout, then sections. A second stylesheet is a second styling system — the thing Stage 2 exists to
prevent.

**Stage 5 writes files.** That removes, entirely, a category of failure the other target spends 260
lines on: no atomic action that fails and applies nothing, no `ECONNRESET` on a large payload, no
rate limit, no soft deletes, no publish step that returns before the CSS is live, no second writer
clobbering yours. Write the file, reload the page.

## Stage 4 — the design system

Webflow variable modes map **one to one** onto custom properties redefined per media query. The
Stage 4 principle is unchanged: a token resolves to its own per-breakpoint value, and components
carry no override.

```css
:root {
  --container-max: 68.75rem;   /* 1100 */
  --section-px:     2.5rem;    /* 40, flat - see the layout contract */
  --text-display:   4rem;
}
@media (max-width: 991px)  { :root { --container-max: 40rem;   --text-display: 3rem;   } }
@media (max-width: 767px)  { :root { --container-max: none;    --text-display: 2.25rem; } }
```

- **Primitives are never responsive; semantic tokens usually are.** A token named for its pixel
  value must mean that at every width or the name lies.
- **Components reference the semantic layer**, never primitives.
- `clamp()` works here. On the other target it does not — size variables reject CSS expressions —
  which is why the layout contract reaches its widths with `max-width` rather than fluid type. That
  constraint does not apply; the contract still does, because it is a box-model fact.

## Breakpoints — you choose them, and that is better

Take the widths from the design's own frames. No fixed ladder to fit.

The Frost build had to map 1920 → `xxl`, 1440 → `main`, 980 → `medium`, 480 → `small`, and leave
`large` and `xl` unused — then live with `medium` spanning 480–991. Here the bands are the design's
bands. **Stage 5's "check the ranges, not just the three widths" still applies**: the browser is
continuous whatever you named the breakpoints.

Write them **mobile-first or desktop-first, but pick one**, and put it in the project `CLAUDE.md`.

## Class naming

Client-First as in `SKILL.md` — custom / utility / `is-` modifier. Two differences:

- The underscore is a readability convention here, nothing more. It does not create a folder.
- **Descendant selectors are allowed.** `.fr_nav.is-scrolled .fr_nav_link { }` is one rule. On the
  other target that is impossible, which is why a scrolled header there needed the same modifier
  class added to three separate elements with four combo records. Do not carry that shape here.

## Behaviours — just write the code

No interactions payload to author, and no need to verify it published, because nothing translates
it. A scroll listener is a scroll listener.

Two rules from the other target still hold, because they are browser facts:

- **Measure after `document.fonts.ready`**, never at `DOMContentLoaded`. See
  `../references/verification.md`.
- **Set `display` inline from script** when toggling visibility, so no stylesheet rule outranks it.

## Verification — headless, not the browser extension

```
python bin/verify.py dist/index.html --width 1440
```

**This is not a preference.** The Claude-in-Chrome extension refuses both `file://` and
`http://localhost` — measured: a local server logged zero requests while Chrome showed
`chrome-error://chromewebdata`, with no proxy configured. Headless Chrome with
`--allow-file-access-from-files` opens `file://` without complaint, which is how
`bin/fixtures/run.py` already works.

So the loop is: write files → `bin/verify.py` at each design width → read the gate rows. The gate
itself is unchanged; `bin/gate.js` never knew what produced the page.

## What relaxes here

Carried from `rule-classification.md`, so none of it is carried by accident:

| Rule on the other target | Here |
|---|---|
| No descendant selectors; a state needs the class on every element | Write one descendant rule |
| `<br>` loses its class, so Method 2 is forced | `<br class>` survives; either method works |
| `grid-row-gap` accepts variables, `row-gap` does not | Use `row-gap` |
| `-webkit-appearance` rejected | Write either form |
| Reserved class names silently dropped | No reserved names |
| `alt` is a setting, not an attribute | `alt="…"` in the markup |
| Anything the API refuses goes in the repo as a paste | Nothing refuses you |
| Combo classes bake in `display` | No combos |
| Size variables reject `clamp()` | `clamp()` is just CSS |

## What does not relax

Everything in the layout contract, the units rule, Stage 0.5 and the whole of Stage 5. Those are
facts about boxes, units, images and text layout. A different generator does not change them —
and the eight defects a human review found on project two were *all* in this category, not in the
platform category.
