# Does the workflow beat a careful conversion without it?

**Pre-registered · NOT YET RUN · written 2026-09-24, before any arm exists**

This file is committed before the experiment so it cannot be retrofitted to the result. If the
outcome contradicts what is written below, the outcome wins.

---

## The claim under test

The plugin front-loads measurement — audit, annotate, a relationship table built from every
breakpoint frame, a token system, then a seven-row gate per section — on the argument that this
removes rework and prevents defects a desktop-first pass ships.

**That claim has never been tested.** Two things are already known and neither is this:

- `method-test.md` showed Stage 3 **finds** the relationships (7 of 9, blinded). That is one stage.
- `golden-bull-build/v1-v2-comparison.md` compared an **ungated** build to a **gated** one from the
  same table and token set. That isolates the gate, holding the method constant.

Neither compares the workflow to **not using it**. Every claim in `SKILL.md` about the workflow's
value currently rests on "the gate caught X", never on "X would have shipped otherwise".

## Design

Two arms, one design, one scorer, all blind.

| | Arm A | Arm B |
|---|---|---|
| Skill | `figma-to-webflow` installed | none |
| Brief | identical | identical |
| Figma + Webflow MCP access | identical | identical |
| Target | its own new blank page | its own new blank page |

**The brief, identical to both, and the only instruction either receives:**

> Convert this Figma design into the Webflow page `<url>`. Match the design at every breakpoint it
> defines. Tell me when you consider it done.

Arm B is **not** told to work badly, is not time-limited, and is not denied any tool. It is a
competent conversion without the method. That is the comparison that matters — a strawman arm
proves nothing.

### Blinding

- Neither arm sees this conversation, the other arm, `method-test.md`, or either `*-build/` folder.
- The **scorer is a third agent** that sees two published URLs labelled only `1` and `2`, in an
  order decided by coin flip and recorded separately. It does not know which arm produced which,
  nor that a skill is under test.
- The scorer grades against the Figma frames using the seven-row gate, and is given the gate rows
  **as a checklist only**, not the skill.

### The design must be one neither arm has seen

**This is the blocking prerequisite.** Both Figma files used so far are contaminated:

- `<design-A>` — the `method-test.md` design; its nine-relationship answer key is
  published in this repo.
- `<design-B>` — the Frost landing page; a 818-line build log recording every defect
  and every measurement is in the workspace repo.

Running on either would measure how well the artefacts were fitted to answers already known. A
third design is required, with **no build log, no relationship table and no audit** in any repo
either arm can read.

## Pre-registered prediction

Arm B produces something that matches at the widest design width and degrades below it: fixed
gutters rather than a container rule, at least one photograph cropped by `cover` on a
content-sized box, and line breaks that follow the desktop frame at every width. Arm A produces
fewer defects in those categories and takes materially longer.

**Stated plainly because it is the uncomfortable possibility:** Arm B may do well. A careful
conversion that simply checks three breakpoints could land close, and if it does, most of the eight
stages are ceremony and the plugin should shrink to the gate.

## Thresholds, set in advance

Primary outcome is **defect count against the frames**, by the scorer, in the categories the skill
claims to address: responsive relationships, section heights and crops, line breaks, container
structure, and asset handling.

| Result | Verdict |
|---|---|
| A has **≥50% fewer** defects than B | The method earns its cost. Ship as is |
| A has **20–50% fewer** | The gate is doing the work. Keep the gate, cut the stages that no defect traces back to |
| A has **<20% fewer**, or more | The staged workflow is not earning its cost. Reduce the plugin to the gate and the platform references |

**Cost is recorded, not scored:** tool calls and wall-clock for each arm. A 3× cost for a 20%
improvement is a different verdict from 2× for 80%, and the table above deliberately does not
capture that — it is for the reader to weigh, and it must be reported alongside.

## What would falsify the claim

Arm B producing a build with no breakpoint-specific defects. That single outcome would mean the
relationship table, the token modes and the gate are all solving a problem that a careful reader
does not have.

## Known limits before it runs

- **One design, one run per arm.** No statistical claim is available from n=1. This can show a
  large effect or fail to; it cannot measure a small one.
- **The scorer uses the seven-row gate**, which comes from the skill. That favours Arm A on
  anything the rows look at, and is blind to whatever neither arm thought of — exactly the gap a
  human reviewer found on project two. Report it as a limit; do not correct for it.
- **Model variance is uncontrolled.** Two agents on the same brief differ for reasons unrelated to
  the skill.
- **Arm A benefits from the writing, not just the reading**, unless its agent is genuinely fresh.
  If it is not, this measures memory rather than the artefact.

## Status

**Blocked, pending an uncontaminated design.** Everything else — brief, blinding, thresholds,
falsification — is fixed by this commit.
