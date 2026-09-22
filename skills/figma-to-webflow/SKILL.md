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

## Stage 5 — Build section by section, gated

**Gate: nothing is recorded as matching until all three breakpoints are checked.**

Build one section, verify it at all three, fix, then move to the next. Not build-everything-then-
audit-once: a fix applied to a build nobody is watching any more is how a fidelity pass ends at
"19 fixed, 5 still wrong" instead of converging.

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
- `references/custom-code.md` — **read before writing or pasting any snippet.**
- `templates/relationship-table.md` · `templates/annotation-spec.md` · `templates/CLAUDE.md`
