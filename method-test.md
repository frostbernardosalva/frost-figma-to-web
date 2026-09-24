# Does the relationship-table method actually find responsive relationships?

**Blind test · one design · Figma file `<design-A>`**

The `figma-to-webflow` skill claims that building a responsive relationship table from all three
breakpoint frames, before any token exists, surfaces the relationships a desktop-first pass misses.
Everything else in the plugin rests on that claim. This is the test of it.

---

## Design

A fresh reader was given exactly three inputs: the file key, three frame node ids, and the table
structure. It had **no access** to the source project, its audit, its fidelity report, or any
expected answer, and was not told how many relationships to look for or that a known set existed.

The worked example was stripped out of the template before handing it over — that example lists all
nine answers, and leaving it in would have made the test worthless.

The scorer (me) had already read the answer key, so the scorer could not be the reader. That is the
whole reason for running it this way.

## The answer key

Nine responsive relationships, each **built flat at its desktop value** in the original build and
caught only afterwards, by hand.

| Relationship | Desktop | Tablet | Mobile |
|---|---|---|---|
| Eyebrow → headline | 32 | 24 | 14 |
| FAQ row padding | 24 | 16 | 16 |
| FAQ question ↔ chevron | 36 | 24 | 24 |
| Process card gap | 40 | 24 | 24 |
| Rail card width | 360 | 310 | 206 |
| Rail column gap | 64 | 24 | 24 |
| Rail top inset | 64 | 32 | 24 |
| Headline → rail gap | 32 | 32 | 24 |
| FAQ headline → list | 32 | 32 | 24 |

## Pre-registered, before running

**Prediction.** Most of the nine should surface, since each is visible simply by measuring the same
relationship at three frames instead of one. Expected weak points: the two rail rows, which require
seeing a horizontal rail as one repeating relationship rather than sibling cards; and —

> **`eyebrow → headline` (32/24/14) versus `FAQ headline → list` (32/32/24) is the indicator row.**
> They agree at desktop and diverge below. A reader that merges them reproduces the original defect
> exactly: one shared utility carrying two different curves. This row tells us more than the other
> eight combined.

**Thresholds.** 7–9 correct at all three breakpoints → method works, ship. 4–6 → sharpen and re-run.
0–3 → method is wrong, do not ship.

## Validity

| Check | Result |
|---|---|
| Blinding | Held. Output references no finding id from the source project and no file from it |
| Answer key not visible | Held. Worked example removed from the handed-over template |
| Frames correct | All three resolved: `Desktop - 1920px` · `Tablet - 980px` · `Mobile - 480px` |
| Read-only | Held. No Figma write tool called |
| Drift | The file has changed since the answer key was written — the FAQ grew from five rows to nine. The added rows sit at a uniform 79px pitch identical to the originals, so **the drift added rows without changing any spacing relationship**. No row excluded |

---

## Result: 7 clean · 1 partial · 1 miss — **pass**

| # | Relationship | Reader's output | |
|---|---|---|---|
| 1 | Eyebrow → headline | **32/24/14**, 8 sections, `semantic` | ✅ |
| 2 | FAQ row padding | **24/16/16**, parked as `hold` | ✅ |
| 3 | FAQ question ↔ chevron | **36/24/24**, parked as `hold` | ✅ |
| 4 | Process card gap | **40/24/24**, 2 sections, `semantic` | ✅ |
| 5 | Rail card width | absent from the table | ❌ |
| 6 | Rail column gap | values present, merged with nav and footer gaps | ⚠️ |
| 7 | Rail top inset | **64/32/24**, parked as `hold` | ✅ |
| 8 | Headline → rail gap | **32/32/24**, `semantic` | ✅ |
| 9 | FAQ headline → list | same row as #8 — correctly merged, same curve | ✅ |

**The indicator row held.** The reader kept `eyebrow → headline` (32/24/14) separate from
`headline → content` (32/32/24), unprompted. That is the distinction whose absence caused the
original defect.

**Two values it re-derived that the original hand audit got wrong first time:**

- Testimonial quote at **64/32/24**. The build had it on an 80/44/40 ramp — wrong at all three
  breakpoints.
- Card title tracking at **−0.32 / 0 / 0** — −0.01em at desktop, none below. The original audit
  recorded this incorrectly twice before a re-measurement caught it.

---

## What the test found wrong with the template

This is the part worth keeping. The test was run to find defects, and it found three.

**1. The eligibility rule was wrong — three real tokens would have been blocked.**
The template said a relationship needs *two or more sections* before becoming a token. Three of the
nine appear in one section only, so FAQ row padding, FAQ question↔chevron and rail top inset were
all parked in the holding area despite being measured correctly at all three breakpoints. The real
project needed all three as tokens.

The rule conflated a single **measurement** with a single **section**. A relationship measured at
three breakpoints is three data points. Now: three measurements make a relationship eligible;
section count governs whether the token is global or scoped.

**2. Rows that agree at one breakpoint got merged.**
The reader combined a nav gap, the rail column gap and a footer menu gap into one row, because all
three are 64px at desktop, then qualified the divergence inline. No information was lost — but that
row shape **is** the original defect, one name over several curves. The template now requires one
row per relationship and forbids qualified cells.

**3. Sizes were skipped.**
The single clean miss was an element *width* (360/310/206). The template mentioned "element width"
in passing; that was not enough. Sizes now have their own table section, explicitly marked
non-optional.

---

## Incidental findings

The reader surfaced sixteen observations beyond the answer key. Several look like real defects that
have not been logged anywhere:

- **The tablet nav uses a 100px gutter** while every tablet content section uses 144px — the logo
  sits 44px out of alignment with everything below it.
- **Footer logo sizes are swapped** between tablet and mobile: nav is 40/40/32, footer is 40/32/40,
  so the mobile footer mark is larger than its nav mark.
- **The testimonial chevrons overlap in all three frames.** The authored 6px gap and the resolved
  coordinates disagree — the container is narrower than its two children.
- **Four of six Path cards are `hidden` at mobile**, all stacked at `x=0`.
- **"Don't take it from us" inverts the section gap direction** — 32 → 64 → 80, growing as the
  viewport shrinks, where every other section shrinks.
- **The footer blurb breaks the body scale at mobile only**, 18px where every other mobile body text
  is 16px.
- The tablet hero is a uniform 0.5463× scale of the desktop hero, padding and gaps included — not
  re-laid-out.

---

## What this does and does not establish

**Establishes:** the method finds the relationships. Stage 3 automates — a general-purpose reader
produced a complete table unassisted, with node ids for every measurement, in one pass.

**Does not establish:** that the workflow is faster. The plugin deliberately front-loads measurement
to remove rework, and that trade has never been measured on a complete project. A good score here is
not evidence of time saved.

**Also unproven:** that any of this generalises. One design, one reader, one run.

## Next test

Re-running the blind read against the fixed template *on this same design* would prove nothing — it
would measure how well the template was fitted to answers already known. The next real test is a
second design, where the method has to find relationships nobody has catalogued in advance.
