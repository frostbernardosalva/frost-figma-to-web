# Annotation spec — <project>

Written at Stage 1, **after** the audit, recording only what the audit found the design file does
not state. Lives beside the design, in this repo, unless the team has decided otherwise.

This document is the answer to "what did the designer mean". Anything inferable from the design file
itself does not belong here.

## 1. Behaviour

For anything that scrolls, animates, plays or responds. **This determines the element tree** — a
marquee, a slider and a static crop are three different structures, so an unanswered row here blocks
building, not just styling.

| Element | Behaviour | Trigger | Timing / easing | Pauses on | Reduced-motion fallback |
|---|---|---|---|---|---|
| | | | | | |

## 2. States

Design files routinely ship with none of these. Absent does not mean "not needed".

| Component | Hover | Focus | Active | Disabled | Loading | Error | Empty |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Where a state *does* exist in the design, record it here anyway — a state present in the file and
missed by the build is as expensive as one that was never specified.

## 3. Component identity

Repetition alone does not reveal a component. A page can hold forty repeated elements and two real
instances.

| Pattern | Instances | Variants | Differences that are variants | Differences that are drift |
|---|---|---|---|---|
| | | | | |

## 4. Deliberate vs drift

**The highest-value section.** A value that sits off the pattern is either a decision or a mistake,
and nothing in the design file distinguishes them. Only the designer knows.

| Value | Where it appears | Deliberate? | Note |
|---|---|---|---|
| | | | |

Guidance: a value recurring in several sections is almost always a decision. A lone off-grid value
is usually drift. Ask rather than standardise — a standardisation reversed later costs more than the
question did.

## 5. Page landmarks

The header and footer are **body-level siblings of the sections**, never inside one. Decide these
before building, because both were decided ad hoc on the last two projects and both had to be
retrofitted.

| Question | Answer | Source |
|---|---|---|
| Header scroll behaviour — scrolls away, sticky, or hides on scroll down? | | |
| If sticky: what does the **scrolled** state look like? | | |
| Does the header overlay the first section, or sit above it? | | |
| Footer: part of the last section's background, or its own? | | |

**A sticky header almost always needs a scrolled state, and the design almost never has one.**
Check the header's text colour against *every* section it will pass over. On the last project the
nav links were `#0c0c30` and four of six sections were `#000001` — a transparent sticky header
would have been invisible over most of the page. If the file defines no scrolled state, that is a
**blocking question for Stage 2**, not something to invent at build time.

## 6. Asset inventory

Fill this before Stage 0.5. A missing row is a missing export, and it is much cheaper to find here
than at section five.

| Section | Role | Breakpoints needing their own crop | Intrinsic w × h | Format | Alt text / decorative |
|---|---|---|---|---|---|
| | | | | | |

- One row per image **per breakpoint that crops differently**. The last project reached section 5
  before noticing one breakpoint's export had never been taken.
- `background-size` needs the **intrinsic width**, so record it here rather than re-deriving it.
- Decide alt text now: a descriptive label for content images, explicitly **decorative** for
  chevrons, rules and scroll cues.

## 7. Unresolved

Anything asked and not yet answered. Rows here block the stages they feed.

| Question | Blocks | Asked of | Status |
|---|---|---|---|
| | | | |

---

**Where this lives.** Default is this file, in the project repo — reviewable, diffable, and unable
to rot silently. Figma Dev Mode annotations put the information where the developer already is, but
have no review and no history, and design-file metadata has already proven unreliable in practice.
Treat moving into Figma as a later upgrade for information that has proved its worth, not as the
starting point. Where a project spec forbids writing to Figma, that decision belongs to whoever owns
the spec.
