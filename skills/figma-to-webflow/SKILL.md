---
name: figma-to-webflow
description: Convert a Figma design into a Webflow build — audit the design file, record what it leaves unspecified, derive a responsive token system from all three breakpoint frames, then build section by section behind a three-breakpoint verification gate. Use when converting a Figma design to Webflow, building a Webflow design system or variable set from a design file, auditing a Webflow build against its Figma source, or writing custom code for behaviour Webflow cannot express.
---

# Figma → Webflow

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

## Status: tested once

Derived from **one project**, and measured once. The platform facts in `references/` describe
Webflow and the browser and are safe to rely on.

The method was tested by giving a reader nothing but a Figma file key, three node ids and the
relationship-table structure, then scoring its output against nine responsive relationships that a
hand pass had originally found only *after* the build was already wrong. **It re-derived seven of
the nine**, correctly separating two curves that agree at desktop and diverge below — the
conflation that had caused the original defect. It missed one element width, and merged three gaps
that share a desktop value into a single row. Both shortfalls are now addressed in the template.

That is one design, and it tests whether the method *finds* the relationships — **not** whether the
workflow is faster end to end. Nothing has measured that yet. Say so if asked.

### What a visual comparison then found

Two builds of that design were measured at **63/63, 100%**, twice. A screenshot comparison against
the source frames afterwards found **eight defects neither audit could see** — every photograph
mis-cropped at every breakpoint, three run-together words, a form whose fields sat at 43% of their
container, and a line-break system that was inert in one build and suppressed at desktop in the
other.

**Seven of the eight were assertable as numbers.** They were missed not because numbers are the
wrong instrument, but because the workflow never asked for those values — section height was not in
the relationship table at all. Only one finding genuinely required an eye.

That is where the Stage 3 measurement rows and the seven-row Stage 5 gate come from. They are not
ceremony; each row maps to a defect that reached a published page.

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

## Stage 1 — Annotate what the audit found unspecified

Order matters: the audit runs first and hands over the list. Annotating before auditing is guessing
at what needs saying.

Use `templates/annotation-spec.md`. Four types, all of them things the design file cannot supply:

| Type | Records |
|---|---|
| **Behaviour** | Scroller type and interaction. Marquee, slider and static crop are three different element trees, so this changes structure, not styling |
| **States** | Hover, focus, active, disabled, loading, error, empty — commonly absent from a design file entirely |
| **Component identity** | Which repeated elements are one component and which differences are variants. Repetition alone does not reveal it |
| **Deliberate vs drift** | Whether an off-pattern value is intentional. The highest-value type: a value appearing at 14px in five sections is a decision, while a lone off-grid value is drift, and nothing in the file distinguishes them |

**Default to a spec document, not the design file.** Annotations in Figma are unreviewable and
undiffable, and Figma metadata has already proven unreliable in practice. If the team decides
annotations belong in Dev Mode, that is a deliberate upgrade — not the starting point.

Some project specs forbid writing to Figma outright. Check before assuming. Where such a rule
exists, read it carefully: a ban on *editing, renaming, restructuring and pushing changes back* is
a ban on modifying the design, and an annotation modifies nothing that renders — but that is the
project owner's call to make, not yours.

## Stage 2 — Resolve blocking decisions

**Gate: no build starts while any of these is open.**

- **One breakpoint map for the whole project.** If custom CSS uses different breakpoints from
  Webflow's native `main` / `medium` ≤991 / `small` ≤767 / `tiny` ≤479, the bands between them
  disagree and every token minted afterwards inherits the ambiguity. This is the cheapest decision
  available and the most expensive to defer.
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
- **Responsive values live in variable modes, not breakpoint overrides.** A token should resolve to
  its own per-breakpoint value; components should carry no override for type or semantic spacing.
- **Primitive spacing is never responsive; semantic spacing usually is.** A primitive named for its
  pixel value must mean that at every breakpoint or the name lies. A semantic token carries a
  relationship and has no obligation to sit on any scale — which is how a 14px mobile value with no
  primitive equivalent becomes expressible.
- **Minimum practical token set.** Every token traces to a measured value. Do not create tokens
  because other systems have them.

Read `references/webflow-mcp.md` before the first write. It is the difference between a clean build
and a day spent on silently dropped styles.

## Class naming — Client-First

**Every class follows Client-First.** Three types, and the type is readable from the name alone:

| Type | Syntax | Example |
|---|---|---|
| **Custom** — a component, element or grouping | underscores, keywords **general → specific** | `gb_testimonial-slider_headshot` |
| **Utility** — global, one job, reusable anywhere | dashes only, **never** an underscore | `text-size-large` · `margin-large` |
| **Modifier / variant** | a **combo class** prefixed `is-` | `.gb_tab.is-active` |

**The underscore is not decoration — Webflow's Designer turns it into a real folder.**
`gb_hero_title` files itself under `gb ▸ hero ▸ title`. This is why the project namespace and the
style-panel organisation are the same decision, and why the namespace belongs in Stage 2.

Where a project requires that an existing design system not be touched, the namespace *is* the
protection: a first segment nothing else uses cannot collide.

**Why not BEM.** Webflow publishes a BEM guide, so it is not wrong. But `block--modifier` as a
standalone global class fights Webflow's own modifier mechanism, and `references/webflow-mcp.md`
records the trap that follows: **properties land on the combo, not the global.** `is-` makes that
relationship visible in the name; `--` hides it.

**One hazard to check, not assume.** Reserved class names are silently dropped — `.label` is one
(see `references/webflow-mcp.md`). Short utility names sit closer to that hazard than namespaced
custom classes do, so **query a utility back after creating it**.

## Stage 5 — Build section by section, gated

**Gate: a section is not done until every row passes. No next section until it does.**

| # | Check | Catches |
|---|---|---|
| 1 | Values at the three design widths | the relationship table, verified |
| 2 | Range sample at ~600, ~800, and the low end of `tiny` | a value right at 980 and catastrophic at 520 |
| 3 | No horizontal scroll at any width tested | container collapse |
| 4 | **Text content diffed against the Figma text** | run-together words, dropped or altered copy |
| 5 | **Every asset resolves and renders** | placeholder boxes, blank squares |
| 6 | **Break points match the reference at each width** — which word each line ends on, not how many breaks exist | breaks that never fire, fire everywhere, or land on the wrong word |
| 7 | **Screenshot against the Figma node, 1:1, per element** | crop, overlap, gradient — the residue nothing numeric catches |

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
*range* — Webflow's `medium` spans 480–991 — and a value that is correct at the design's width can
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
- **Never build a responsive break on `<br>`.** Webflow strips its classes, so every `<br>` fires at
  every width at once. Spans keep their classes.

**Record every deliberate deviation as it is made**, in the project's `CLAUDE.md`. Undocumented
changes read as defects later, even when the reasoning was sound. This log is a required
deliverable, not a courtesy.

## Stage 6 — Behaviours

Everything expressible in Webflow-native stays there. A parallel hand-written CSS layer should
shrink toward zero, never grow — two styling systems on two breakpoint maps will disagree somewhere,
and the disagreement surfaces as a bug nobody can locate.

Read `references/custom-code.md` before writing or pasting any snippet.

## Stage 7 — Fidelity pass

Should now find little, because Stage 5 gated each section. If it finds a lot, the Stage 5 gate is
not being applied — say so rather than silently absorbing the rework.

## Flag rather than fix

Stop and ask on: two plausible readings of a design decision; a value that appears off-pattern but
may be deliberate; missing states; placeholder copy; anything that looks left in by accident. A
standardisation proposed on an incomplete reading has to be retracted later, which costs more than
asking.

## References

- `references/webflow-mcp.md` — **read before any Webflow write.**
- `references/verification.md` — **read before running the Stage 5 gate.**
- `references/custom-code.md` — **read before writing or pasting any snippet.**
- `templates/relationship-table.md` · `templates/annotation-spec.md` · `templates/CLAUDE.md`
