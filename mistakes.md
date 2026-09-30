# Every mistake, by the shape it takes

`rule-classification.md` indexes every **rule** and says where it belongs. This file indexes every
**mistake** and says where its guard went. They are read at the same moment: when you are about to
add a rule, and at the end of a project.

**Organised by failure mode, not by project.** A mistake is recognised by its shape long before it
is recognised by its details, and the same seven shapes have now produced every defect across four
conversions. The instances underneath each one are evidence, not a catalogue to memorise.

**Six of the seven are a check failing. The seventh is a step that never ran**, and it is the one
this whole plugin was designed around — see shape 7. The first version of this file had six, which
is how a register of mistakes came to omit the mistake its own design exists to prevent.

**The last column is the point.** An empty *Guard lives* cell is a lesson that has not been written
down anywhere a future project will read it. Those cells are the backlog.

---

## The seven tests, short

Ask these before believing a check, and again before writing a finding down.

| # | Shape | The question |
|---|---|---|
| 1 | The instrument was wrong | Has this probe ever been run against a page known to be broken? |
| 2 | The check could not have failed | What would have to be wrong for this to fail? If nothing, it is not a check |
| 3 | Nobody asked for the value | Is the thing I am worried about *in* the measurement set at all? |
| 4 | A conclusion wider than its source | Could this source show me the absence I am inferring? |
| 5 | The target was stale | Did I measure the published thing, or the authoring store? |
| 6 | The fix arrived after the checking stopped | Has the gate run *since* the last edit? |
| 7 | **The step never ran** | What would be visibly missing if I skipped this? If nothing, it will get skipped |

`SKILL.md` already carries the sentence shapes 1–6 descend from: **"A check that shares the build's
assumption confirms it."** Shape 7 descends from a different one, in the README: **"a teammate on a
deadline skips steps nobody can see were skipped."** This file is those two sentences with their
evidence attached.

---

## 1 · The instrument was wrong

The check reported a defect that was not there, or passed one that was, because the measuring code
was broken. **Every false positive on the Golden Bull build came from the verification code, not
from the build** — that project named the pattern itself after the third one.

These are the cheapest to prevent and the most expensive to chase: a broken instrument produces a
*coherent* wrong answer, which reads as a systematic build defect rather than an artefact.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| Audit read **41 %** on a correct build. Every failure at exactly **85 %** of expected — a fluid root font-size resolved to 13.6px in a 1536 window against 1920 design figures. Re-run at a true 1920: **63/63** | Golden Bull | Assert root font-size before trusting any rem figure, and set a real viewport | `bin/gate.js` `rootFontSize` · `references/verification.md` |
| Comparator did `Math.abs(act - exp)` on strings. `"none" - "none"` is `NaN`, and `NaN` never satisfies a tolerance — **7 correct checks failed** | Golden Bull | Type-aware comparison; validate a comparator against known-good input before trusting its failures | — |
| The harness padded iframe width so `clientWidth` matched the design. Media queries match the viewport **including** the scrollbar, so a 980 test ran at 995 and silently rendered desktop | Frost landing | Hide the scrollbar; never pad the width | `bin/gate.js:68` · `references/verification.md` |
| `Range.getClientRects().length` used as a line count. It returns one rect per **child node** — a 3-line address reported 5 | Frost landing | Use `height / lineHeight`; a rect count is not a line count | `references/verification.md` |
| Characters grouped into lines by rect `top`. Regular and Bold on the same line have different tops, so the probe split every weight change. **An hour spent on a `display:block` span that does not exist** | Frost landing | Group by **vertical overlap**, never by `top` | `bin/gate.js` `groupLines` |
| `naturalWidth: 0` reported **"2/6 images broken"**. Chrome reports 0 for SVGs that render correctly at 40×44 | Golden Bull | Check `getBoundingClientRect()` and `complete`, not `naturalWidth` | **partial** — `bin/gate.js` handles the lazy case; the SVG case still flags |
| A `display:none` image reported `complete: false` and read as breakage. Webflow sets `loading="lazy"`, so five images below the fold reported broken | Frost landing | A load still in flight is not a verdict. Report pending separately | `bin/gate.js` `legacyAssets` |
| `unitAudit` flagged all **16** `--sN-bg-w: 1440px` values — the documented `background-size` exception | HTML target | A probe cannot know what a custom property is *for*. Report, do not judge | `bin/gate.js:343` |
| Probed at exactly **479px**. Sub-pixel rounding put the viewport just above the boundary, `matchMedia('(max-width: 479px)')` returned false, and tablet padding read as a container collapsed to zero | Golden Bull | Never probe on a breakpoint edge. Sample inside the band | `references/verification.md` |
| A section screenshotted **blank** — the harness iframe was shorter than the page and the section sat at y=26212 in a 26000px frame. Separately, a hidden iframe photographs as a blank page, **which looks done** | Mynt | Make the capture iframe visible and taller than the page, and assert the region was captured before reporting a defect from it | `references/verification.md` · `bin/verify.py` |

---

## 2 · The check ran, passed, and could not have failed

Structurally blind. The check was sound, ran correctly, and had no path to failure for the class of
defect present. This is the most dangerous shape, because it produces a confident number.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| **63/63, twice.** Both builds scored 100 % on values and were visibly wrong. **159/159 measured values correct** while `background-size: cover` re-cropped every photograph at every breakpoint | Golden Bull | The seven-row gate, and row 7 in particular | `SKILL.md` Stage 5 |
| Page totals landed **+16 / +18 / +78 / −2** while the build was wrong in about thirty places. Two sections measured **exactly right** with their content 238px and 179px out of position — a bottom-aligned block built as a fixed gap keeps the section's height | HTML target | **Height agreement and visual agreement are not the same measurement** | `SKILL.md` Stage 5, row 7 |
| The screenshot row **was run** and passed a form field at **191px — 43 % of its container** — and a photograph 35 % oversized. Compared at section scale and ~60 % zoom, both read as "the right thing in the right place" | Golden Bull | 1:1, element by element. **A gate that is satisfied by a glance is not a gate** | `SKILL.md` "Row 7 is the one that gets faked" |
| Row 4 compared `textContent` strings, not rendered lines. Two words ran together at 980 and 480 and stayed live. The inverse also happened — geometry correct, `textContent` reading `Phone:+63…` | Frost landing | Assert **which words end each line**, and diff the copy character by character | `SKILL.md` Stage 5 row 4/6 |
| `unitAudit` **cannot see the mistake it exists to catch.** It explicitly does not judge custom properties — and Webflow variables *are* custom properties. Only the class literals would ever have been flagged | Mynt | On a target whose variables compile to custom properties, check units by reading the collection back per mode | — |
| Row 6 **cannot go green at all** on a shared stylesheet. Webflow serves every design system on the site in one file: 250 px hits, none in the page's own classes | Mynt | Check units by prefix against the published CSS, not by the row | `SKILL.md` "Checking the units on a live site" |
| **Learning transfers along the path already walked.** After three pages built on one component variant, a fourth built on the **base** variant inherited two values nobody had ever measured at base — a line-height that the variant flattens, and a platform default whose reset the other pages carried in their own page CSS. Both were invisible until the gate | Mynt | **A value seen only through a variant is not the base value**, and a reset copied per page is a step that can be skipped. Read the base rule before reusing a class off-variant; put platform resets in ONE site-level place | `SKILL.md`, `targets/webflow.md` |
| **"Row 7 was run" — against my own expectation.** The very next build, with the crop lesson already written down, opened the tablet render, looked at it, and called it correct. It shipped a table of contents built as a **stacked list** where the design makes it a **dropdown** — a trigger carrying the active section plus a panel of the rest. The reviewer spotted it immediately. No numeric row could have: the two shapes total nearly the same | Mynt | **Row 7 is a comparison, so the design node has to be on screen.** Looking at your own output and judging it plausible is not row 7 — a stacked list of section names looks entirely reasonable. Put the two images side by side, literally. And count children per width: the design's panel held **16** links where the desktop column held 17, which is the mechanical tell that a block changed *kind* | `SKILL.md` "Row 7 is the one that gets faked" |
| **"Row 7 was run" — on three crops of one component.** A 12-item content page was screenshotted at its accordion lists, compared, and reported as gated. The **navbar was the wrong theme, the hero band was still the wrong colour with the new ink already on it, and the footer breadcrumb still read the previous page's text**. A hero crop had been taken and never opened. The user saw all three in seconds | Mynt | **A crop of one component is not row 7 for a page.** Open a whole-page render at every width and name each page-level block — nav, hero, footer — against its own design node. A theme changes no dimensions, so no numeric row can ever catch it | `SKILL.md` "Row 7 is the one that gets faked" |
| **The page total passed because the errors cancelled.** A 12-item content page measured **+0.22 % — inside a tolerance pre-registered before the build.** Three items were a line too long, one was three lines too short, and the sums nearly annulled each other. Fixing the real defects made the headline number **worse** before it got better | Mynt | On a content-driven page a page total is a weak gate. **Pull per-item targets out of the frame metadata and compare item by item** — one call per width, and every deviation then resolves to a whole number of lines | `SKILL.md` Stage 5 |
| **No row checks which font face resolved.** `font-weight: 400` was requested everywhere and only 500 and 700 were loaded, so every "Regular" run rendered Medium — on both builds. Every recorded measurement came from a Medium-rendered page | HTML target | Assert the resolved face, not that the family is available. `document.fonts.check()` answers the wrong question | — |

---

## 3 · Nobody asked for the value

Absent by construction. The measurement set never contained the thing that was wrong, so no check
could have found it however well it ran. **The gate verifies a section against its own
measurements; it has nothing to say about which measurements to take.**

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| **Section height was never in the relationship table**, because the design does not declare it — it is an outcome. Sections were built content-height, 562px where the design is 705, and `cover` then re-cropped every photograph | Golden Bull | Measure section height, every section, all three breakpoints | `SKILL.md` Stage 3 |
| **No weight or colour column.** Eight headings shipped at 400 that are 700, and eleven elements shipped the wrong colour, because both were inferred rather than read | HTML target | Weight and colour are columns, and colour is recorded as base **plus opacity** | `templates/relationship-table.md` |
| Header geometry was never entered, so the navigation built ~200px too far left — logo at x=296 against a design 116 | Frost landing | Only the visual comparison caught it. Landmarks get measured like everything else | `SKILL.md` Stage 3 |
| Two components built **mirrored** — `image \| text \| chevron` where the design is `chevron \| text \| image`. Component *order* is not a measured value | HTML target | Row 7, per element | `SKILL.md` Stage 5 |
| A later review returned eight rules. **Every one described something the seven-row gate had passed** | Frost landing | Read the gate as a floor, not a ceiling. **Add it to Stage 3, not to the gate** | `SKILL.md` Status |

---

## 4 · A conclusion wider than its source

Something partial was read, and the conclusion drawn covered more than the source could support.
Each time, the source felt authoritative — and in three of these the *second*, more rigorous-feeling
reading was also wrong.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| A badge was read wrong **twice**: "present at all five frames" from the inventory, then "1440 frame only" from a section-scoped `get_metadata`. It is at all four, collapsed at 480. It is parented **above** the section node, so any section-scoped read misses it — and acting on the wrong reading created a real defect | Frost landing | A read scoped below the thing cannot show its absence. Read the frame roots | `references/figma.md` |
| **"Does not exist" concluded from a filtered list.** A component was absent from the *published* component list and reported as non-existent. It exists, and carries a deprecation note — and its instances are on every page of that type | Mynt | Absence from a filtered view is not absence. Resolve the name against the file | `SKILL.md` Stage 0 |
| Values resolved against a **previous build** instead of the design node. Separately, muted text is stated in the design as a colour **plus an opacity**; reading the composite as a flat colour invented two tokens that do not exist | HTML target | Values come from `get_design_context` on the design nodes. Record colour and opacity as two facts | `SKILL.md` Stage 3 |
| Layer names read as content. A "double space" in a layer name was a `<br>` | Frost landing | **Layer names may lie — read rendered content** | `SKILL.md` Stage 0 |
| One `500` response cached as a permanent capability claim: `remove_style` was recorded as broken and written into the shared reference. Re-tested: **212 classes removed, zero failures** | Golden Bull | Re-test before recording a capability, and date the record | `targets/webflow.md` `## Cleanup` |
| A platform rule generalised from one property name — *"`row-gap` rejects a length variable"* — was **reversed by finding 7 in its own list**. The legacy aliases accept variables and Webflow's own classes use them | Frost landing | Test the alias before writing the rule | `targets/webflow.md` |
| The mobile frame is **480**; real devices report **390–428**. Every mobile number in the table describes a width no device has, and the build and the checks inherited the same wrong reference, so their agreement proved nothing | Golden Bull | Sample the band the product ships to, not only the drawn widths | `SKILL.md` "Check the ranges" |

---

## 5 · The target was stale

The check measured the wrong copy — the authoring store instead of the published output, or a page
whose fixes had not landed yet. Every one of these returned a confident answer about something that
was not the thing under test.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| `publish_site` **returns before the CSS is live.** Two consecutive re-measures read the old values and a correct fix read as a failure | Frost landing | Verify the stylesheet hash changed before trusting a post-publish measurement | `targets/webflow.md` |
| A **100 % audit** was run against a page whose fixes sat unpublished in the Designer. `br[class*=…]` returned **0** | Golden Bull | Assert published state equals authored state before measuring | `targets/webflow.md` |
| Scroll interactions were created, read back, and listed as visible on the page. They never fired: the site publishes **zero `data-w-id`**. **Everything a check could reach said pass** | Frost landing | Grep the published page, not the create response | `targets/webflow.md` · `SKILL.md` Stage 6 |
| `update_page_settings` returns **200**, advances `lastUpdated`, and changes nothing | Golden Bull | A success response is not a write. Re-query the field | `targets/webflow.md` |
| A style write was accepted, stored, returned by the read-back, and **absent from the published CSS**. Reproduced twice in one session | Mynt | **API read-back is not verification on this target** | `targets/webflow.md` · `SKILL.md` |

---

## 6 · The fix arrived after the checking stopped

The most dangerous edit in the process is the one that follows a pass, because the checking has
already finished.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| A section passed its gate. The row-7 fix then renamed its modifiers, which stranded three crop rules on the old global names — **three of five logos collapsed to 0 wide** and the section went from 592 to **480**, a 19–20 % shortfall at every width. Found only by the end-of-build audit | Frost landing | **Re-run the whole gate after every fix, not just after the build** | `SKILL.md` Stage 5 · `references/verification.md` |
| A defect created **by** a verification conclusion: acting on the wrong badge reading set `display: none` at one breakpoint and pushed the element 8.35px outside the section, where `overflow: hidden` clipped it | Frost landing | A conclusion that changes the build is an edit, and re-triggers the gate | `SKILL.md` Stage 5 |
| A finding was written up as **closed** while the render still showed it open | Mynt | Do not record a claim as closed without re-reading the render that decides it | `SKILL.md` Stage 7 (disposition) |

---

## 7 · The step never ran, and nothing showed its absence

**Not a checking problem — a visibility problem, and it takes a different kind of guard.** Shapes 1
to 6 are fixed by a better check. This one is fixed by making the omission *leave a hole*: an
artifact that is visibly empty, a flag whose absence is announced, a number computed rather than
carried forward. A better check cannot help, because the check is the thing that did not happen.

This is the shape the plugin's own design targets — *"a rule in a file is advisory, and a teammate
on a deadline skips steps nobody can see were skipped"* — and it is the one that has cost the most.

| What happened | Project | Guard | Guard lives |
|---|---|---|---|
| **The project `CLAUDE.md` was never seeded from `templates/CLAUDE.md`, so the rem rule never reached the project and the entire variable collection was built in px.** Undoing it cost 33 base and 15 mode variable writes plus ~34 class literals. The rule was written down, classified, machine-checked — and it never arrived | Mynt | Stage 2 does not start until the project file exists and was copied from the template. The units line in it is the falsifier | `SKILL.md` Stage 2 |
| **Six of seven gate rows run, success reported, and the page never looked at.** Heights and container widths matched, so the build was called done; row 7 then found **31 defects across seven sections**. `verify.py` printed six rows and produced no image, so a six-row run looked like a complete one | HTML target | `--shot` writes the render from the same command that prints the rows, and a run without it now says row 7 did not happen | `bin/verify.py` |
| Deviation-log entries appended after the fact — *"(Found during section 6, recorded now.)"* — against a rule that says *"written as changes are made, not at audit time"* | Frost landing | Nothing enforces contemporaneity. A log is prose, and a missing entry has no signature until someone asks why a value differs | — |
| Findings stayed in the project. Of the late findings on one build, **two of nine** reached the plugin, and nobody could see the gap until it was tabulated | Mynt | Every finding gets a disposition before the project closes, and the ledger below is where that is visible | `SKILL.md` Stage 7 |
| `rule-classification.md` fell behind its own `SKILL.md` — four rules added across three commits, none classified — **and its stated total was wrong by one on two of three tables**, from before anyone noticed | plugin | Recount from the tables. Never increment a carried-forward number | `rule-classification.md` |

**The last row is this failure happening inside the fix for this failure.** The count was wrong
while the file was being edited to fix exactly this class of problem, and it surfaced only because
the verification step recounted instead of trusting the stated figure. **Recompute, do not
increment** — that is the whole of shape 7 in three words.

---

## The flow-back ledger

Findings live in the project. Rules live here. **This table is the only place the gap between them
is visible.** An outstanding item is a lesson the next project will have to learn again.

| Project | Findings live in | Landed | Outstanding |
|---|---|---|---|
| **Mynt** | `audit.md` F1–F38 | **all of F27–F38.** F32, F33, F34, F35, F36 → `targets/webflow.md` · F37's fix, F38 → `SKILL.md` layout contract | `unitAudit` is blind on a target whose variables compile to custom properties |
| **Golden Bull** | `accuracy-audit.md`, `v2-build-log.md`, `visual-comparison.md` | row 7 at 1:1 · section height as a measured value · range sampling · the `remove_style` correction · breakpoint-edge probing | the comparator type guard |
| **Frost landing** | `v3-build-log.md` | re-run after every fix · scrollbar · line grouping · the form-wrapper trap · publish-hash · IX3 grep · the filtered-source trap | — |
| **HTML target** | `html-target-full/README.md` | `--shot` · weight and colour columns · custom-property reporting | the resolved-font-face check · the SVG `naturalWidth` case |

**F35 and F36 were the two that cost most by staying out.** `targets/webflow.md` already said to
give each element *"its own combo"*, which is the right shape — but it never said what happens if
you do not, and never named `parent_style_names`. A reader following the letter of it could still
share one bare modifier across blocks and watch it work on the first and fail silently on the rest.
Both now have their own section, with the reason.

---


**2026-09-30, Mynt page two.** Four findings, three of them platform or format facts and one
methodological:

| Finding | Where it went |
|---|---|
| A component variant cannot enlist an element it never had. The rule publishes; the `w-variant-` class is never added; nothing matches | `targets/webflow.md` |
| A combo must be registered against the **exact** class chain the element wears | `targets/webflow.md` |
| `display: contents` regroups markup across breakpoints without duplicating elements | `targets/webflow.md` |
| A Figma text node is one string and your HTML is blocks: trailing `<br>` renders nothing, the platform's base CSS spaces your blocks, and list markers are per-list with a marker size that is sometimes literally zero | `SKILL.md`, under text line-break fidelity |
| **Errors that cancel** — the row above | this file, shape 2 |
| A variant enlists an element only via its **first** class — replacing an earlier, wrong version of this finding | `targets/webflow.md` |
| A component instance root cannot take a class at all | `targets/webflow.md` |
| **Row 7 run on crops of one component** — the row above | this file, shape 2 |
| **Row 7 run against expectation rather than the design node** — the row above | this file, shape 2 |
| A block can change *kind* across breakpoints; child count per width is the tell | `SKILL.md` |
| An element-rect overflow probe and `scrollWidth > clientWidth` catch different defects | `SKILL.md` |
| Inserting a node silently breaks `:first-child` rules aimed at its siblings | `SKILL.md` |
| A value seen only through a variant is not the base value | `targets/webflow.md` |

## What this file is not

- **Not a copy of the rules.** It holds the mistake and a pointer. The rule itself lives where
  `rule-classification.md` sends it — `SKILL.md` for a truth, `targets/<target>.md` for a scar.
- **Not the findings register.** Per-project platform findings belong in that project's audit file,
  numbered. Only the *shape* and the disposition come here.
- **Not a blame log.** Every entry is a defect in a check or a conclusion, which is why it is
  organised by mechanism. Three of the four projects scored 100 % on something while being wrong.
