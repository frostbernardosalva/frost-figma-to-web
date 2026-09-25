---
name: figma-to-web
description: Convert a Figma design into a built page — audit the design file, record what it leaves unspecified, prepare assets, derive a responsive token system from every breakpoint frame, then build section by section behind a seven-row verification gate. Targets Webflow or vanilla HTML/CSS/JS. Use when converting a Figma design to Webflow or to HTML, building a design system or token set from a design file, auditing a built page against its Figma source, or writing custom code for behaviour the target cannot express.
---

# Figma → Web

A staged conversion workflow. Each stage produces an artifact, and the next stage does not start
until that artifact is complete. The artifacts are the point: a skipped step has to leave a visible
hole in a document, not just an undone thought.

## The defect this exists to prevent

One failure pattern dominated the build this workflow was derived from: **a value that is correct at
desktop and wrong below it.** It accounted for nine spacing relationships, four type roles collapsed
onto two classes, and a type ramp applied at the wrong size at all three breakpoints.

It had two causes, and the first is the one people miss:

1. **The token system could not express a responsive relationship.** The system had primitive
   spacing (`spacing/N` where N × 4 = px) and nothing above it, so every responsive relationship had
   to be flattened to a single primitive. The build could not have been right. A semantic layer —
   tokens carrying a designed *relationship*, free to take per-breakpoint modes and under no
   obligation to sit on the grid — fixed it, but only after the cost was paid.

2. **Verification was desktop-first**, and the resulting pass table read as if everything in it had
   been checked at all three breakpoints, because most of it had.

**Neither cause is fixed by annotating, renaming or tidying the Figma file.** The design stated
those values correctly. Do not reach for file cleanup to solve this.

## Status: two projects, one claim proven

Derived from **two projects** and measured properly once. The platform facts in `references/`
describe the browser, Figma and the image encoders, and are safe to rely on. Everything else below is the evidence,
stated plainly, including what it does not cover.

### What is proven

The Stage 3 method was tested by giving a reader nothing but a Figma file key, three node ids and
the relationship-table structure, then scoring its output against nine responsive relationships that
a hand pass had originally found only *after* the build was already wrong. Pre-registered, blinded,
with the scorer separate from the reader.

**It re-derived seven of the nine**, correctly separating two curves that agree at desktop and
diverge below — the conflation that had caused the original defect. It missed one element width and
merged three gaps that share a desktop value; both shortfalls are now in the template. It also
re-derived two values the original hand audit had got wrong.

**Stage 3 finds the relationships.** That is the one claim with real evidence behind it.

### What the first project established

Two builds of that design measured **63/63, 100%**, twice. A screenshot comparison against the
source frames then found **eight defects neither audit could see** — every photograph mis-cropped at
every breakpoint, three run-together words, a form whose fields sat at 43% of their container, and a
line-break system inert in one build and suppressed at desktop in the other.

**Seven of the eight were assertable as numbers.** They were missed not because numbers are the
wrong instrument but because the workflow never asked for those values — section height was not in
the relationship table at all. That is where the Stage 3 measurement rows and the seven-row Stage 5
gate come from.

### What the second project established — and this is the important part

A six-section landing page, built behind the seven-row gate. The gate **caught seven defects**,
three of which no measurement could have found: modifier classes named after the *previous* client's
brands, two words running together in `textContent` while rendering correctly, and a section broken
by its own fix after it had already passed.

Then a review of the finished page found **eight further classes of defect the gate passed**:
container and padding structure, backgrounds built as positioned children, units, asset format,
image metadata, the mobile container rule, and two line breaks that were inverted between desktop
and mobile. A later pass found a ninth — the header and footer buried inside content sections.

**So: the gate is reliable at what it inspects. Choosing what to inspect is still the weak half**,
and on this project that scope came from a human reviewer, not from the method. Read the gate as a
floor, not a ceiling, and expect the first review of any new page to find a class of thing the rows
do not cover. Add it to Stage 3, not to the gate.

### What the probes themselves turned out to be

The Stage 5 probes used to be eight code blocks across `SKILL.md` and `references/verification.md`,
retyped from memory each build. Moving them into `bin/gate.js` and running them against a
deliberately-wrong page found **four bugs in the probes**, three of which returned a confident
`pass`: line grouping by rect `top` (which this skill already warned against, 66 lines from the
code that did it), a legacy-asset regex that never matched a CSS background, a `cssRules` check made
truthy for every rule by CSS Nesting, and lazy images reported as broken.

**A check that shares the build's assumption confirms it.** That is the same failure as the
desktop-first pass table in the first project, one level up: the instrument agreed with the thing it
was measuring. Prose cannot be run, so prose cannot be caught being wrong.

### What the second target established

The stages were split from the platform and re-run against vanilla HTML/CSS. **One section**
(Frost's Clients section, chosen because it is small and its numbers were already recorded), four
breakpoints, gated with `bin/verify.py`:

**Containers exact at all four widths — 1100 / 848 / 640 / 400 — and every section height inside
0.9px of the design.** The Webflow build of the same section landed 1-2px over, so this is the same
order of fidelity by a different route. `bin/gate.js` needed no change; it never knew what produced
the page.

The gate also earned its place: the first run failed at **1920 only**, by 45.67px. The cause was
real and specific — the blurb rendered on one line where the design has two, because the test uses
a substitute face and Sailec is wider. Confirmed against the live build at a true 1920 before
touching anything.

**This is one section, on a design that had already been built once.** It shows the stages survive a
change of target. It does not show the HTML target works on a full page, on behaviours, or on a
design nobody has solved before.

### What is still unmeasured

- **The direct-conversion control has never been run.** Nothing here shows the workflow beats a
  careful conversion *without* it. The evidence shows a seven-row gate beats a three-row gate, which
  is a much smaller claim.
- **Speed.** The workflow deliberately front-loads measurement to remove rework. That trade has
  never been timed on a complete project. Say so if asked.
- **Whether it survives a cold read.** Both projects were built by the same reader who wrote these
  rules. Nobody has yet run this file who did not also write it. `evals/` now tests exactly this —
  two cases, sandboxed, fresh config — but it **has not produced a score**: both need a shell, and
  the runner refuses to grant one without a sandbox backend, which Windows does not have. Authored,
  parsing, unrun. Do not cite it as evidence until it has a number.

## Stage 0 — Audit the design file

**First: verify the frames.** Resolve every frame id and report each one's `name` and `width`.
**Refuse to proceed unless there are three distinct frames at three distinct widths.** Supplied
links routinely carry the same `node-id` three times, or point at a different page entirely.
Measuring one frame three times produces a table in which every relationship looks non-responsive —
the exact defect this workflow exists to prevent, reached backwards and with false confidence.

Then read all three frames. Report what exists, what is missing, and what is drift.

Three traps, all of which have produced wrong conclusions before:

- **Layer names may lie.** Blocks get pasted between projects and never renamed, so a layer can
  carry one project's names while rendering another's text. **Always read the rendered content
  before drawing a conclusion about content.** A finding was once escalated to Blocker on layer
  names alone and was simply wrong.
- **`get_metadata` gives structure, not style values.** Do not infer spacing or type from it.
- **Raw x/y coordinates mislead** on rotated and auto-layout nodes. Two elements that looked like
  they overlapped by 36px were a 6px flex gap.

When correcting a contrast value, **compute it** — composite the alpha against its actual ground and
apply the WCAG 2.2 relative-luminance formula. Never estimate. A single alpha token cannot serve
both light and dark grounds.

## Stage 0.5 — Prepare every asset before building

**All of it happens before the first element is created.** Building first and collecting images as
you go is how a page ends up half-converted, with one section still pointing at a stale export.

### 0 · Check the converter runs, before exporting anything

```
python "${CLAUDE_PLUGIN_ROOT}/bin/to-avif.py" --help
```

One command, and a machine that cannot do this step is found now rather than after a full export
pass. **If `${CLAUDE_PLUGIN_ROOT}` does not resolve**, find `bin/to-avif.py` under the installed
plugin directory and use that path — do not skip the step because a variable was empty.

**If the command does not run at all** — no interpreter, `command not found`, or on Windows the
Microsoft Store advert instead of an error — **or if it exits 1** (that is the no-encoder case, and
the script prints the fix itself), then:

1. **Say exactly what is missing, with the command for their platform.**

   ```
   Python    winget install Python.Python.3.12       Windows
             brew install python@3.12                macOS
             sudo apt install python3 python3-pip    Linux

   Encoder   pip install --upgrade 'Pillow>=11.3'    preferred, ~40% smaller than ffmpeg
             winget install ffmpeg / brew install ffmpeg / sudo apt install ffmpeg
   ```

2. **Offer to run it. Wait for a yes.** Installing software changes the user's machine, so it is
   their call, not yours. Never run a `sudo` command without explicit agreement.
3. **Stop before upload, and keep the exports.** Steps 1 and 2 below may finish; step 3 blocks.
   Nothing unconverted reaches the build, and nothing is thrown away — the run resumes at step 3 once
   the tool is there.
4. **Never improvise another encoder, and never treat unconverted PNGs as ready.** "The page works"
   is not the test; it works at 20x the bytes, which is the whole failure this step exists to
   prevent.

**The backstop, if all of that is somehow missed:** rule 5 — `G.legacyAssets(doc)` must return
**zero** legacy references before any build is called done. If PNGs reached the page, that check
fails, whatever happened here.

### The steps

1. **Export** every image from Figma at each breakpoint that needs its own crop. Check the set is
   complete against the section list — the last build reached section 5 before noticing the 1920
   export had never been taken, and the 1440 image had been stretched to cover it.
2. **Rename** to a descriptive, sortable scheme: `<ns>-<section>-<role>-<breakpoint>` —
   `fr-s1-photo-xxl.avif`, `fr-s4-bg-md.avif`. The breakpoint suffix is what makes a missing export
   visible at a glance.
3. **Convert rasters to AVIF — run the script, do not hand-roll it.**

   ```
   python "${CLAUDE_PLUGIN_ROOT}/bin/to-avif.py" <src-dir> --out <dir>
   ```

   It refuses to run without an encoder (**exit 1**, nothing written) rather than leaving you with
   PNGs and no warning, and it writes the asset map, so step 5 is done for you.

   **The script can only protect the case where it runs.** If Python itself is absent the script
   never executes and cannot report anything — which is why step 0 above checks first, and why the
   stop rule there is the actual guarantee. This is the one rule in the workflow that can silently
   not happen, so it is covered twice on purpose.

   What it encodes, and why — all measured on the Frost assets, all overridable:

   - **quality 70 photographs / 85 flat graphics**, chosen by unique-colour count. The threshold is
     4096, not 256: the client-logo sprite is a flat graphic with **2967 colours** from antialiased
     edges, and at 256 it is misfiled as a photograph. `--flat "*logo*"` overrides the guess.
   - **`speed=4`**, and this is not monotonic — slower is *not* smaller. Same photo at quality 70:
     speed 0 → 101.0K, speed 4 → **98.6K**, speed 6 → 100.4K, speed 10 → 109.4K.
   - **alpha is dropped only when provably unused.** Figma exports RGBA regardless; 14 of the 16
     Frost assets carried a fully-opaque alpha channel. The two that used it kept it.
   - ffmpeg is a working fallback but compresses worse — 10.3K against Pillow's 7.3K on the same
     file. Prefer `Pillow >= 11.3`.

   Result on the Frost set: **14.60 MiB → 705.1 KiB (4.7%)** across 16 files, byte-for-byte
   identical to the hand-run it replaces.

4. **Commit them to the repo** next to the PNG exports. The PNGs stay as the source of truth; the
   AVIFs are what ship.
5. **The asset map is generated** — filename, intrinsic width × height, and the compression
   achieved. Fill in the asset id and the breakpoint after upload. `background-size` needs the
   intrinsic width, and you will need it again at Stage 5. Do not hand-edit the table; re-run.

Whether the target accepts AVIF directly is a target question — see `targets/<target>.md`. Both
current targets do.

**Replacing assets on a build that already shipped:** upload the new ones, rebind every reference,
verify **zero** legacy references remain, and only then delete the old ones. `bin/audit-assets.py`
sizes the saving without touching anything; `bin/rebind-plan.py` turns page scans into an ordered
plan that doubles as the rollback record; the target file carries the procedure and the four traps
that shape it. The check is one line:

```js
G.legacyAssets(doc)   // bin/gate.js — images AND every url(...) in document.styleSheets
```

Use the function, not a regex you write on the spot. The obvious one —
`/\.(png|jpe?g)(\?|$)/` — is **wrong** and passes every CSS background, because in a stylesheet
the extension is followed by `")`, not end-of-string. It shipped in this skill until a fixture
caught it.

Deleting first leaves a section with a dead URL and no error anywhere.

## Image metadata — every image, at both levels

- **Content images get descriptive alt text** — what the image *shows*, not what it is called.
  `"Great Place To Work certified badge for Frost, March 2024 to March 2025"`, not `"gptw"`.
- **Decorative images are marked decorative** — explicitly empty alt. Chevrons, rules, scroll cues,
  arrows. Empty because the decision was made, not because nobody set it.
- Set it on the **asset** (so future placements inherit it) and on the **element**.

**`alt` is a setting, not an attribute.** `data_element_tool > set_attributes` with `name: "alt"`
fails with `An internal error occurred` — an opaque message for a real constraint. Use
the target file: on some platforms `alt` is a *setting*, not an attribute.

## Stage 1 — Annotate what the audit found unspecified

Order matters: the audit runs first and hands over the list. Annotating before auditing is guessing
at what needs saying.

Use `templates/annotation-spec.md`. Six types, all of them things the design file cannot supply:

| Type | Records |
|---|---|
| **Behaviour** | Scroller type and interaction. Marquee, slider and static crop are three different element trees, so this changes structure, not styling |
| **States** | Hover, focus, active, disabled, loading, error, empty — commonly absent from a design file entirely |
| **Component identity** | Which repeated elements are one component and which differences are variants. Repetition alone does not reveal it |
| **Deliberate vs drift** | Whether an off-pattern value is intentional. The highest-value type: a value appearing at 14px in five sections is a decision, while a lone off-grid value is drift, and nothing in the file distinguishes them |
| **Page landmarks** | Header and footer placement and scroll behaviour. A sticky header needs a **scrolled state**, and the file almost never has one — check the header's text colour against every section it passes over. Blocking at Stage 2, not inventable at build time |
| **Asset inventory** | One row per image per breakpoint that crops differently, with intrinsic width and its alt text or decorative mark. Feeds Stage 0.5; a missing row is a missing export |

**Default to a spec document, not the design file.** Annotations in Figma are unreviewable and
undiffable, and Figma metadata has already proven unreliable in practice. If the team decides
annotations belong in Dev Mode, that is a deliberate upgrade — not the starting point.

Some project specs forbid writing to Figma outright. Check before assuming. Where such a rule
exists, read it carefully: a ban on *editing, renaming, restructuring and pushing changes back* is
a ban on modifying the design, and an annotation modifies nothing that renders — but that is the
project owner's call to make, not yours.

## Stage 2 — Resolve blocking decisions

**Gate: no build starts while any of these is open.**

- **The target.** `targets/webflow.md` or `targets/html.md`. This decides how Stage 4 delivers
  tokens, how Stage 5 writes, and which constraints apply at all — several rules in this file exist
  only to work around one platform, and `rule-classification.md` records which. **Read the target
  file before Stage 4.**

  - **If the request names one, use it.** "convert this to Webflow", "build this as HTML" — the
    decision is made. Do not re-ask.
  - **If it does not, ask before Stage 3.** One sentence is enough: a Webflow site, or files in a
    repo. Asking costs a turn; guessing costs the token layer and the whole of Stage 5, because
    those are the two things the target decides.
  - **Never default to Webflow because it is better documented.** `targets/webflow.md` is twice the
    size of `targets/html.md` and has two projects of evidence behind it — that is an artefact of
    which target came first, not a recommendation. An unstated target is a question, not a lean.
  - **Record the answer** in the project's `CLAUDE.md` under `Target:`, so it survives the
    conversation.
- **One breakpoint map for the whole project**, and only one. Two styling systems on two breakpoint
  maps disagree in the bands between them, and the disagreement surfaces as a bug that appears at
  one viewport width and nowhere else. On a platform with a fixed ladder you adopt it; where you
  choose, take the widths from the design's own frames. This is the cheapest decision available and
  the most expensive to defer.
- **Behaviour for anything that scrolls, animates or has states** — it determines the element tree.
- **Font licensing**, before any type token is built on a face that cannot ship.
- **The project's namespace.** The convention itself is fixed — see **Class naming** below — but the
  namespace is per project, and every class minted afterwards carries it. Same logic as the
  breakpoint map: cheapest decision available, most expensive to defer.

## Stage 3 — Responsive relationship table

**Gate: built from all three frames, before any token exists.**

Use `templates/relationship-table.md`. One row per recurring relationship, one column per
breakpoint, plus the sections it was measured in. Three rules, all learned by breaking them:

- **Three measurements before a value enters the build.** An empty cell means unmeasured, and is
  visible to anyone reviewing the table. That visibility is the enforcement mechanism.
- **Three measurements also make a relationship *eligible*.** One measured at all three breakpoints
  is fully known even if it appears in a single section — it becomes a **scoped** token rather than
  a global one. Section count governs scope, never eligibility. An earlier version of this rule
  demanded two sections and would have blocked three tokens the real build needed.
- **One row per relationship.** Two relationships that share a value at one breakpoint and differ at
  another are two rows. A cell needing a qualifier — "24 for cards, 16 for the footer" — is two
  relationships wearing one name, which is the original defect in miniature.
- **Measure what the design does not declare.** Two rows get skipped because nothing in the file
  *states* them — they are outcomes of the layout, not declarations:
  - **Section height**, every section, all three breakpoints.
  - **Image box** dimensions for every photographic element — the box, not the asset.

  Omitting these shipped the single largest defect this workflow has produced. Sections were built
  content-height (562px where the design was 705px) with `background-size: cover`, which re-cropped
  every photograph at every breakpoint — while all 159 measured values inside them stayed correct.
  A value audit cannot see a number that was never taken.

Then: **new token when values diverge across breakpoints; reuse with an override when they agree.**
Rows whose three values differ become semantic tokens carrying modes. Rows that agree become
primitives.

## Stage 4 — Build the design system

- **Semantic layer above primitives**, present from the outset. Components reference the semantic
  layer, never primitives, so a change propagates in one edit.
- **A token resolves to its own per-breakpoint value; components carry no override** for type or
  semantic spacing. The delivery mechanism is per target — variable modes, or custom properties
  redefined inside each media query — but the principle does not change.
- **Primitive spacing is never responsive; semantic spacing usually is.** A primitive named for its
  pixel value must mean that at every breakpoint or the name lies. A semantic token carries a
  relationship and has no obligation to sit on any scale — which is how a 14px mobile value with no
  primitive equivalent becomes expressible.
- **Minimum practical token set.** Every token traces to a measured value. Do not create tokens
  because other systems have them.

**Read `targets/<target>.md` before the first write.** It is the difference between a clean build
and a day spent on silently dropped styles.

## Layout contract — every section, no exceptions

Four rules. They are not style preferences; each one is a defect that shipped and was sent back.

### 1 · The section holds the padding. The container holds the max-width.

```
section      padding-block: <responsive>   padding-inline: <responsive>
  container  max-width: <token>   margin-inline: auto     ← no padding
    content
```

Nothing else. A container that also carries padding double-insets the moment anyone adds padding to
the section, and the two rules drift apart. **On the last build the hero used a second container
ladder** — `max-width: 1440/1024` with `padding-inline: 170/88`, against every other section's
`1148/896` with `24` — and produced the same content width by a different route. It looked right and
was unmaintainable. One ladder, or the drift is only a matter of time.

**Verify by measuring every container at once.** All of them must return the same number:

```js
['.x_case_inner','.x_hero_inner','.x_clients_inner', …]
  .map(s => document.querySelector(s).getBoundingClientRect().width)
// 1100,1100,1100,1100,1100,1100   ← one ladder
// 1100,1020,1100,1100,1100,1100   ← two ladders, and you would never see it by eye
```

`G.containers(doc, sel)` in `bin/gate.js` does this and reports the distinct widths.

### 2 · No `max-width` on the container at mobile

At the smallest breakpoint the container is `width: 100%` and `max-width: none`. The viewport is
already the constraint; a max-width there only invents a second one.

### 3 · Section padding is flat, max-width does the work

The gutters a design *appears* to have at desktop — 410 at 1920, 296 at 1440 — are not authored
insets. They are what is left after centring a fixed content width. The only authored gutter is the
mobile one.

So: **section `padding-inline` = the mobile gutter, flat at every breakpoint**; container
`max-width` = the design's content width per breakpoint. Check it lands:

| | viewport | − 2 × padding | max-width | content |
|---|---|---|---|---|
| 1920 | 1920 | 1840 | 1100 | **1100** ✓ |
| 1440 | 1440 | 1360 | 848 | **848** ✓ |
| 980 | 980 | 900 | 640 | **640** ✓ |
| 480 | 480 | **400** | none | **400** ✓ |

Every design width exact, and nothing collapses in between. Writing the *apparent* gutter (170 at
980) as section padding instead produces 428px of content at 768 and a 260px jump at the breakpoint.

**A full-bleed child inside a padded section** — a nav band, a rule that must touch both edges —
needs `width: calc(100% + 2 × padding)` **and** the matching negative margins. The negative margins
alone shift it; they do not widen it.

### 4 · Backgrounds go on the section, never on a positioned child

```css
background-image: url(<asset>);
background-size: <the image's intrinsic width>px;   /* px — not rem */
background-repeat: no-repeat;
background-position: center center;
```

No absolutely positioned `<div>` or `<img>` behind the content. The section carries the image.

- **`background-size` is the image's real width in px**, per breakpoint, and is the one measurement
  that stays in px — an intrinsic pixel fact, not a layout measurement.
- **The section still needs its explicit height.** Moving the image to the background does not
  remove the mandatory Stage 3 height row; it is still what stops the crop defect.
- **An absolutely positioned sibling is offset from the *border* box**, so section padding does not
  move it. Do not "compensate" for the padding — on the last build that pushed a floating badge
  8px outside the section, where `overflow: hidden` clipped it.

### 5 · The header and footer are page landmarks, not section content

They are **body-level siblings of the sections** — `<header>` first, `<footer>` last — never inside
one. A header placed inside the first section has to fight that section's padding to reach the page
edges; on the last build that cost a `width: calc(100% + 2 × padding)` plus matching negative
margins, a hack that existed **only** because of where the element sat. At body level `left: 0;
right: 0` is the whole rule.

The footer borrows three things from the section it sits in, and needs all three back when it moves
out: its **own container** (max-width + `margin-inline: auto`, none at mobile), its **own
`padding-inline`**, and its **own `background-color`**. Miss the background and the page shows
through.

Two knock-on effects to handle in the same pass:

- **A fixed header is paid for by the first section**, with `padding-top` = a `size/nav-height`
  token. The page total must not change.
- **The section the footer left sheds the footer block from its height token** — gap + footer
  height. Anything absolutely positioned against that section and anchored to its *bottom* moves
  with the footer.

## Units — rem everywhere, em for letter-spacing

Every measurement is **rem** (÷16 from the design's px). `letter-spacing` is **em**, so it tracks the
font size instead of fighting it. `background-size` is the only px exception.

Converting an existing build: set each token's **base** value first, then re-read with
`include_all_modes`. Modes that resolve to the base inherit the new unit automatically; only modes
holding a genuine override still read `px` and need setting. On the last build that was 59 base
writes and 71 mode writes instead of 240.

**A correct rem conversion changes nothing.** At a 16px root the numbers are identical — every
section height, every content width, the page total. If the page moves, the conversion is wrong.

## Class naming — Client-First

**Every class follows Client-First.** Three types, and the type is readable from the name alone:

| Type | Syntax | Example |
|---|---|---|
| **Custom** — a component, element or grouping | underscores, keywords **general → specific** | `gb_testimonial-slider_headshot` |
| **Utility** — global, one job, reusable anywhere | dashes only, **never** an underscore | `text-size-large` · `margin-large` |
| **Modifier / variant** | a second class prefixed `is-` | `.gb_tab.is-active` |

The namespace is the first segment and belongs in Stage 2, because every class minted afterwards
carries it. On some targets the underscore also organises the style panel — see
`targets/webflow.md`.

Where a project requires that an existing design system not be touched, the namespace *is* the
protection: a first segment nothing else uses cannot collide.

**Why not BEM.** BEM is not wrong, and on a target where you write the CSS yourself either works.
The `is-` form is kept for both targets so the team learns one convention — and because on Webflow
`block--modifier` actively fights the platform's own modifier mechanism. That argument is in
`targets/webflow.md`.

**One hazard to check, not assume.** Some platforms silently drop reserved class names. Short
utility names sit closer to that hazard than namespaced custom classes do, so where the target
warns of it, **query a utility back after creating it.**

## Stage 5 — Build section by section, gated

**Gate: a section is not done until every row passes. No next section until it does.**

| # | Check | Catches |
|---|---|---|
| 1 | Values at the three design widths | the relationship table, verified |
| 2 | Range sample at ~600, ~800, and the low end of `tiny` | a value right at 980 and catastrophic at 520 |
| 3 | No horizontal scroll at any width tested | container collapse |
| 4 | **Text content diffed against the Figma text** | run-together words, dropped or altered copy |
| 5 | **Every asset resolves, renders, and carries alt text** | placeholder boxes, blank squares, images with no metadata |
| 6 | **Break points match the reference at each width** — which word each line ends on, not how many breaks exist | breaks that never fire, fire everywhere, or land on the wrong word |
| 7 | **Screenshot against the Figma node, 1:1, per element** | crop, overlap, gradient — the residue nothing numeric catches |

**Re-run the gate after every fix, not just after the build.** A section can pass its gate and then
be broken by its own fix. On the last build, row 7 caught the client-logo modifiers being named
after the *previous* project's clients; the rename that followed stranded their crop rules on the
old class names, three of five logos collapsed to zero width, and the section lost a whole row —
592px became 480. Nothing re-measured, and only the end-of-build full audit found it. The fix is the
most dangerous edit in the process, because it arrives after the checking has stopped.

**Row 1 includes alignment, which no table row states.** Elements the design sets flush must come
out flush. This one needs no reference to check: compare siblings against **each other**. A heading
block starting 78px right of its own body copy is wrong whatever the design says, and that shipped —
at tablet, in a build that passed every measured value.

Build one section, run all seven, fix, then move to the next. Not build-everything-then-audit-once:
a fix applied to a build nobody is watching any more is how a fidelity pass ends at "19 fixed, 5
still wrong" instead of converging.

`references/verification.md` has the script for rows 1–6 and the false positives to expect from it.

### Row 7 is the one that gets faked

It has already been run and passed a build that was visibly wrong. Two rules, both learned that way:

- **1:1, element by element.** At section scale and ~60% zoom, a 191px form field and a 442px form
  field both read as "a form, in the right place". They were not the same. Compare the element
  against its Figma node at full size, or the row is decorative.
- **Re-measure after swapping a styled `div` for a real control.** `<input>` and `<select>` do not
  inherit the width a `div` took by default. That is precisely how the 191px field shipped.

### Check the ranges, not just the three widths

**The three design widths are three points. The browser is continuous.** A breakpoint covers a
*range* — a "tablet" band may span 480–991 — and a value that is correct at the design's width can
be nonsense everywhere else in that range.

This has already shipped a defect. A tablet gutter measured at 274px — correct at the 980px design
frame — was built as fixed `padding-x`. At 980 it verified perfectly. At 600 it left 52px for
content; at 520 the container collapsed to **zero width** and the page scrolled sideways. The
measurement was right; the *rule* was wrong.

So, after the three design widths pass, **sample the middle of every range**: roughly 600 and 800
for `medium`, and the low end of `tiny`. Look for a container narrower than intended, text crushed
or wrapping far more than the design, a section far taller than the design, and any horizontal
scroll at all.

The underlying habit: **a fixed gutter is almost always the wrong translation of a centred column.**
The design says "432px of content centred in a 980px frame". Written as `padding: 274px` that is
true at exactly one width. Written as `max-width: 432px` plus a small safe gutter, it is true
everywhere — and still produces 274px gutters at 980. Prefer the rule that states the intent over
the number that was measured.

**The same error in its other costume: a fixed-frame photo does not become `cover` on a
content-sized box.** In the design the photo is a fixed frame with a known crop. Built as a
background on a box whose height is whatever the copy happens to need, `cover` re-crops it — and
keeps re-cropping it as the copy reflows. Set the height, or set `aspect-ratio` from the export.
Every value inside such a section still measures correct, which is exactly why this survives a
value audit.

### Text line-break fidelity

### Reading the break before fixing it

The failure is almost never the fixing. It is asserting a **line count** and calling it verified.
On the last build, section 1's gate entry read *"no hard breaks at 1920/1440/980 — those wrap
naturally"*, and the breaks shipped **inverted** between desktop and mobile. Two lines at both
widths, both wrong, and the count said pass.

**1 · Get the design's break, in this order of reliability.**

- `get_design_context` on the text node. An authored break is **structural** — separate `<p>`
  elements inside one text block, or an explicit `<br aria-hidden />` inside a span run.
- If the text returns as one unbroken string, the break is a **natural wrap** and the file does not
  say where it lands. Then `get_metadata` gives the node's box: **width**, and
  `height ÷ (fontSize × line-height)` = the line count.
- `get_screenshot` of that node and **read the words off the render**. For a natural wrap this is
  the only source that gives the actual words per line. This is the step that gets skipped.

A frame's `get_metadata` gives every text box on that frame in one call — box width and height for
each — so **four calls produce the whole break table**. Do that once at Stage 3 rather than
per-section at Stage 5.

**Both halves of this can be mechanical.** The three steps above are what the `break-reader` agent
does; `bin/gate.js` `lineEnds()` already does the built-page side, and `bin/break-diff.py` compares
the two word by word and exits non-zero on any mismatch:

```
break-reader            -> design-breaks.json      (the design's words per line)
verify.py --json --text -> built-breaks.json       local build
gate.js in the browser  -> built-breaks.json       live site - verify.py refuses remote URLs
break-diff.py --design … --built …                 names the width and the first differing word
```

**Read it by hand when you prefer.** The agent is an accelerator, not a dependency, and it is
calibrated against one recorded case rather than regression-tested — `agents/break-reader.md` says
so in its own file. What is not optional is comparing **words**, not counts: the inverted headline
above was two lines at both widths, and a count check passed it.

**2 · Decide the method with a measurement, not a guess.** Measure the string up to the required
break in the real font, and compare it with the design's box:

```js
const m = document.createElement('span');
m.style.cssText = 'position:fixed;left:-9999px;white-space:nowrap;visibility:hidden';
m.style.font = "400 48px Sailec"; m.style.letterSpacing = '-0.02em';
m.textContent = 'Frost has worked with';
document.body.appendChild(m); m.getBoundingClientRect().width;   // 485.4 against a 478 box
```

Fits → **Method 1**. Does not fit → widen past the design (a logged deviation) or **Method 2**.

**3 · Allow for the metric gap.** Figma and the browser disagree about the same font. On this
project Sailec renders **~1.6% wider** in the browser (a footer line measured 530.6 against a design
522), and Figma's `leading-[normal]` is **1.25** where the CSS keyword gives **1.45**. A string that
fits at 478 in Figma may not fit at 478 in a browser — that exact case needed `max-width: 486`.
Method 1 needs a tolerance; anything past a few px is a deviation to log, not to absorb silently.

**4 · Verify with a probe that reports words, not counts.**

```js
G.lineEnds(el).detail.text    // bin/gate.js — ["Frost has worked", "with industry titans."]
```

It groups by **vertical overlap**, never by `top`: a word joins the running line when either
midpoint falls inside the other's band, so it holds whether the new word is taller or shorter.
Keying on `top` starts a new line at every size change and at every weight change on a family whose
weights differ in metrics — which is how a word that was never orphaned got reported as orphaned.

**Grouping by `top` is a false positive generator.** Bold and regular glyphs on the same line have
different rect tops, so a weight change mid-sentence splits one line into two. That probe reported
an orphaned `"with"` that did not exist, and sent the diagnosis down the wrong path for an hour.
Overlap grouping is what makes the probe trustworthy.

Then look at it. A break can be correct and still sit 1px from re-wrapping.


**Line breaks shown in the Figma frame are exact, not illustrative.** Match them at each breakpoint
independently. Natural word-wrap is not sufficient on its own; it must be *verified* to produce the
same break points as the reference at each of the three breakpoints — not just approximately
similar.

**Method 1 — `max-width`, try this first.** Adjust the container's `max-width` until natural
wrapping produces the same break points as the frame at that breakpoint's specific width. Verify
against the export. Do not assume a plausible-looking `max-width` is correct without checking the
rendered break points.

**Method 2 — forced break, when `max-width` alone cannot match it.** Wrap the text from the break
point onward in a `<span>` set to `display: block`. That forces the exact break regardless of
container width:

```html
<p>
  The Emerging Bull Award is presented to
  <span class="ns_line">Asia-Pacific businesses that demonstrate</span>
  <span class="ns_line">rapid growth, strong business fundamentals,</span>
  and potential for future expansion.
</p>
```

**Per-breakpoint re-verification is non-negotiable.** A forced break defined at one breakpoint does
not carry to the others. A `display: block` span that is correct at 1920 will very likely be wrong
at 980 and 430, because the design re-flows differently at each width. Re-check against the
reference at every breakpoint — never assume a break survives a width change.

Three things this project already paid for:

- **Wrap the text; never toggle an empty marker.** An empty `<span>` switched between `block` and
  `none` leaves **no whitespace** when hidden, which is how `craftingend-to-end` and
  `EmergingBull Award` shipped. Method 2 avoids this because the span *contains* the text. If an
  empty marker is genuinely unavoidable, the space goes **before** it —
  `crafting <span class="ns_brk"></span>end-to-end` reads correctly in both states.
- **Block spans cannot overlap.** Where two breakpoints break at different words mid-sentence, one
  set of block spans cannot express both. Use Method 1 for the breakpoint that conflicts, and say
  which approach each breakpoint uses. This is a real limit, not something to improvise past.
- **Check whether `<br>` can carry a class on your target before relying on it.** On Webflow it
  cannot — the publisher strips the class, so every `<br>` fires at every width at once, and Method
  2 is forced. Where classes survive (plain HTML), a classed `<br>` is fine and simpler. This is a
  target constraint, not a web principle; `bin/gate.js` flags a classed `<br>` so the choice is
  visible either way.

**Record every deliberate deviation as it is made**, in the project's `CLAUDE.md`. Undocumented
changes read as defects later, even when the reasoning was sound. This log is a required
deliverable, not a courtesy.

## Stage 6 — Behaviours

**Keep one styling system.** Two systems on two breakpoint maps will disagree somewhere, and the
disagreement surfaces as a bug that appears at one viewport width and nowhere else. Where the
platform expresses a behaviour natively, use it and let any hand-written layer shrink toward zero;
where you are writing files anyway, there is only one layer and this costs nothing.

**A successful create is not proof it played.** Verify behaviour on the *published* output, not on
the API response — one platform accepted scroll interactions, listed them as present, and never
emitted them. See `targets/<target>.md` before writing or pasting any snippet.

## Stage 7 — Fidelity pass

Should now find little, because Stage 5 gated each section. If it finds a lot, the Stage 5 gate is
not being applied — say so rather than silently absorbing the rework.

## Flag rather than fix

Stop and ask on: two plausible readings of a design decision; a value that appears off-pattern but
may be deliberate; missing states; placeholder copy; anything that looks left in by accident. A
standardisation proposed on an incomplete reading has to be retracted later, which costs more than
asking.

## References

- `targets/webflow.md` · `targets/html.md` — **read the one you chose at Stage 2, before Stage 4.**
- `references/verification.md` — **read before running the Stage 5 gate.**
- `references/figma.md` — reading the design file.
- `templates/relationship-table.md` · `templates/annotation-spec.md` · `templates/CLAUDE.md`
- `../../rule-classification.md` — every rule labelled *browser truth* or *platform scar*. Read it
  before carrying a rule to a new target, and before adding one.

## Tools

- `bin/to-avif.py` — Stage 0.5. Converts, or exits 1 naming the install.
- `bin/gate.js` — the Stage 5 probes. Evaluate in the page under test.
- `bin/verify.py` — render a page headless at a given width and run the gate.
- `bin/fixtures/run.py` — the probes' own regression suite.
