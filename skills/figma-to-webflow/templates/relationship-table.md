# Responsive relationship table — <project>

Built at Stage 3, from **all three frames**, before any token exists.

Frames measured: Desktop `<w>px` · Tablet `<w>px` · Mobile `<w>px`

## Rules

- **An empty cell means unmeasured.** Write `?`. Never carry a value across from another breakpoint
  to fill a gap — that manufactures the exact defect this table exists to catch.
- **Three measurements make a relationship eligible.** One relationship measured at all three
  breakpoints is three data points, not one, and is eligible even if it appears in a single section.
  The holding area is for relationships measured at **fewer than three breakpoints** — not for ones
  found in fewer than two sections.
- **Section count governs scope, not eligibility.** A relationship found in several sections becomes
  a global token; one found in a single section becomes a **scoped** token. Both are real.
- **One row per relationship.** If two relationships share a value at one breakpoint and differ at
  another, they are **two rows**. Never write a cell like "24 (cards) / 16 (footer)" — a row that
  needs a qualifier is two rows wearing one name, and that is precisely the shape of the original
  defect: one class carrying several curves that happen to agree at desktop.
- **New token when values diverge; reuse with an override when they agree.** Values that differ
  across breakpoints become **semantic** tokens carrying modes. Values identical at all three become
  **primitives**.

## Spacing relationships

| Relationship | Desktop | Tablet | Mobile | Sections measured in | Verdict |
|---|---|---|---|---|---|
| | | | | | |

Verdict is one of: `semantic` (values diverge) · `primitive` (values agree) · `hold` (measured at
fewer than three breakpoints) · `drift` (off-pattern and confirmed unintentional).

## Sizes

**Fill this in — it is not optional, and it is the section most often skipped.** Gaps are the
obvious relationships; sizes are the ones that get missed, and a width built flat is as wrong as a
gap built flat. A card that is 360px at desktop and 206px at mobile is a responsive relationship
even though nothing about it looks like a gap.

| Thing | Desktop | Tablet | Mobile | Sections | Node ids | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |

Cover at least: content/element widths, media and image heights, control and hit-target sizes, icon
boxes, and any max-width.

### Two rows that are mandatory and always get skipped

Nothing in the design *declares* these — they are outcomes of the layout, so there is no value to
read off and they never make it into the table. Measure them anyway.

| Thing | Desktop | Tablet | Mobile | Sections | Node ids | Verdict |
|---|---|---|---|---|---|---|
| Section height — hero | 1025 | 646 | 963 | Hero | | |
| Section height — asset block | 705 | | | Asset Block | | |
| Image box — hero photo | | | | Hero | | |
| Image box — asset block photo | | | | Asset Block | | |

Those desktop numbers are the real ones from the build that got this wrong, kept as the worked
example. **The asset block was built 562px tall against a designed 705.** With
`background-size: cover` on a content-sized box, that re-cropped the photograph at every
breakpoint — cutting one person out of the frame entirely — while all 159 measured values inside
the section stayed correct.

A blank height cell means unmeasured and blocks the build, exactly like every other cell here.

## Type roles

One row per **role**, not per class. Two roles whose values coincide at desktop are still two roles;
collapsing them is the single most common way this goes wrong.

| Role | Size D/T/M | Line-height | Tracking | Used by | Verdict |
|---|---|---|---|---|---|
| | | | | | |

## Holding area — measured at fewer than three breakpoints

Only for rows with a `?` in them. A relationship measured at all three breakpoints does **not**
belong here, however few sections it appears in.

| Candidate | Values | Seen in | Which breakpoint is missing, and why |
|---|---|---|---|
| | | | |

---

## Worked example

From a completed project, showing what a finished table looks like and the kind of divergence it
catches. These are that design's values, not defaults — do not carry them into a new project.

| Relationship | Desktop | Tablet | Mobile | Verdict |
|---|---|---|---|---|
| Eyebrow → headline | 32 | 24 | 14 | semantic |
| FAQ row padding | 24 | 16 | 16 | semantic |
| FAQ question ↔ chevron | 36 | 24 | 24 | semantic |
| Process card gap | 40 | 24 | 24 | semantic |
| Rail card width | 360 | 310 | 206 | semantic |
| Rail column gap | 64 | 24 | 24 | semantic |
| Rail top inset | 64 | 32 | 24 | semantic |
| Headline → rail gap | 32 | 32 | 24 | semantic |
| FAQ headline → list | 32 | 32 | 24 | semantic |

**All nine were built flat at their desktop value** because the table did not exist and the token
system had no semantic layer to put them in. Note the last two: identical curves, and a utility
class was made to carry both — but it was *also* carrying the eyebrow gap, which is a different
curve agreeing only at desktop.

Note too that the mobile column contains a 14px value. A primitive on a 4pt grid cannot express it
without its own name lying; a semantic token carries a relationship and can. A proposal to round it
up to 16px was made twice and retracted once the table showed it appearing deliberately in five
separate sections.

**Three of those nine appear in one section only** — the two FAQ rows and the rail top inset. Under
an earlier version of this template they were parked in the holding area and would never have become
tokens, even though the real build needed all three. That is why eligibility is now three
*measurements* rather than two *sections*: a single-section relationship measured at all three
breakpoints is fully known, and becomes a scoped token rather than waiting for a second sighting
that may never come.

**One more trap the same test exposed.** A reader working from this table merged three different
horizontal gaps — a nav gap, the rail column gap and a footer menu gap — into one row, because all
three are 64px at desktop. Below desktop they diverge completely. That merged row is the original
defect in miniature, so the one-row-per-relationship rule above is not a formatting preference.
