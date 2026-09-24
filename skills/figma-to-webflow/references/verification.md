# Verification — running the Stage 5 gate

Rows 1–6 of the gate are a script. Row 7 is a screenshot, at 1:1, per element.

**The probes live in `bin/gate.js`. Do not retype them from this file.**

Read that file and evaluate its contents in the page under test; it defines `window.__frostGate`.
Every check returns `{ row, status, detail }`, and `detail` is the evidence that goes in the build
log — never "looks right".

```js
const G = window.__frostGate;
G.rootFontSize(doc)                 // ALWAYS first, or every number below is fiction
G.lineEnds(doc.querySelector(sel))  // row 6 — the words per line
G.glue(doc)                         // row 6 — hidden markers with no whitespace
G.containers(doc, sel)              // row 1 — one number per width
G.legacyAssets(doc)                 // row 5
G.altAudit(doc)                     // image metadata
G.unitAudit(doc)                    // rem/em
```

`python bin/fixtures/run.py` runs them against a page that is wrong on purpose and exits non-zero
on any regression. **It has already caught four bugs in the probes themselves** — see the bottom of
this file. That is the argument for the file existing: prose cannot be run, so prose cannot be
wrong in a way anything notices.

Everything here was written by debugging it against a real build. The false positives in the last
section cost more time than the true positives did, which is why they sit beside the checks rather
than in a footnote.

## Measure in a true viewport, or the numbers are fiction

**The first audit on this workflow reported 41%. Every failure was at exactly 85% of expected.**

That was not a build fault. The host window was 1536px wide, the page carried a fluid root
font-size, and `0.25rem + 0.625vw` at 1536 resolves to **13.6px** — 85% of 16. Every `rem` value was
being compared against a 1920px design figure. Re-run inside a true 1920 viewport: **63/63**.

So: render the page in an **iframe at the real width**, scaled down visually with a CSS transform if
it has to fit the screen. Never measure in a window that merely approximates the breakpoint.

`G.harness(path, w, h)` does this, and hides the iframe scrollbar rather than padding for it.

Confirm `getComputedStyle(doc.documentElement).fontSize` is what the design assumes **before**
trusting a single measurement.

## Row 4 — text content

Diff the rendered text of each block against the Figma text, whitespace-normalised. This catches
dropped copy and, more importantly, words fused together at an element boundary.

## Row 5 — assets resolve

An asset is fine only if it is present **and** painted. See the SVG and hidden-image traps below
before writing the assertion.

## Row 6 — break points, not break counts

Counting `<br>`/`<span>` elements proves nothing: a build where every break fires at every width
counts the same as one where they fire correctly. **Assert which word each rendered line ends on.**

`G.lineEnds(el)` returns `{ lines, text, ends }`. `ends` is the last word of each rendered line.

Compare that array against the frame, per breakpoint. A mismatch names the exact word.

### Glue detector

For every break marker, read the character immediately before and after it in document order. Flag
it when the marker is hidden and **neither** side carries whitespace — that is the
`craftingend-to-end` defect, and it is invisible to both a value audit and a casual read.

`G.glue(doc)` does this. The version that lived here was pseudocode — the walk was a comment —
so it could never have run at all.

## Four false positives — check for these before reporting a failure

All four fired during one build. Each produced a defect report that was wrong, and two of them cost
an hour apiece.

| Symptom | Why it is not a defect |
|---|---|
| `img.naturalWidth === 0` on a visible SVG | **SVG has no intrinsic raster size.** `naturalWidth` is legitimately `0` while the image renders perfectly. Test SVG by `getBoundingClientRect()` instead. |
| `img.complete === false` | An image inside a `display: none` subtree never starts loading. It is hidden, not broken. Skip anything whose layout box is zero. |
| "Only N logo rows — expected M" | Counting distinct `top` values counts **differing item heights**, not rows. Items of unequal height on the same row report different `top`. Group by row midpoint, or compare against the container instead. |
| A layout check fails with `NaN` | `Math.abs(actual - expected)` on non-numeric values — `"none" - "none"` is `NaN`, and `NaN` fails every comparison. Use a type-aware comparator: strings compare with `===`, numbers with a tolerance. |

**A gate that cries wolf gets switched off.** If a row fails, reproduce the failure by hand once
before writing it down as a defect.

## Recording the result

Write pass/fail per row per section as you go, not at the end. A row that was never run is not a
pass, and the record should make that visible rather than silently absorb it.

## Two more false positives

### `Range.getClientRects().length` is not a line count

It returns one rect per child node, so a paragraph with three `<br>`s reports 5 "lines" and a
two-`<p>` block reports 4. Use `height / lineHeight`, or the overlap-grouping probe in SKILL.md.

### Grouping characters by `top` splits a line at every weight change

Bold and regular glyphs on the same line have different rect tops. A per-character probe that keys
on `top` will report an orphaned word that does not exist. Group by **vertical overlap** — a
character belongs to the running line if its midpoint falls inside that line's band.

## Do not compensate for the iframe scrollbar

Padding the iframe width so `clientWidth` equals the design width pushes the **media** width past
the breakpoint — media queries match the viewport *including* the scrollbar. A 980 test silently
rendered the desktop layout and reported desktop values as if they were tablet. Hide the scrollbar
instead, so measured width and media width are the same number:

```js
html { scrollbar-width: none }
html::-webkit-scrollbar { display: none }
```

## Assert the URL, not the element

`loading="lazy"` makes every `<img>` report `complete: false` with an empty `currentSrc`. Fetch the
URL and check for **HTTP 200**. The same check should sweep for legacy formats after an asset
migration — `document.images` and every `url(...)` in `document.styleSheets`.

## Re-run the whole gate after every fix

Not the row that failed — the whole gate, on every section. See the section-3 regression in SKILL.md
Stage 5: a fix broke the section it was fixing, and only the end-of-build audit caught it.

## Four bugs the fixture caught in the probes themselves

`bin/fixtures/` exists because these were all invisible to review. Each is now a committed check.

| Bug | Why nothing noticed |
|---|---|
| The line-break probe grouped by rect `top` | This file **already warned against it**, 66 lines from the code that did it. Prose and code disagreed and neither could tell. It reported an orphaned word that did not exist |
| `/\.(png\|jpe?g)(\?\|#\|$)/` never matched a CSS background | In a stylesheet the extension is followed by `")`, not end-of-string. It returned a clean "zero legacy references" over a sheet full of PNGs |
| `if (rule.cssRules) { …; return; }` skipped every plain rule | CSS Nesting gave `CSSStyleRule` a `cssRules` property, and an **empty `CSSRuleList` is truthy**. The unit audit reported "no stray px" against 14 px declarations |
| `!img.complete` reported lazy images as BROKEN | Webflow lazy-loads by default, so everything below the fold looks broken. Five false positives on the Frost page. A load that **finished** with no pixels is broken; one still in flight is not a verdict |

The pattern in all four: **a check that agrees with the build's own assumption confirms it.** Three
of them returned `pass`. A probe that cannot fail is not a probe, and the only thing that
distinguished them was running the code against a page whose answer was known in advance.
