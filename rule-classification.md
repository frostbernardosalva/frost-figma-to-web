# Every rule, classified: browser truth or Webflow scar

Written before the target split, because the split is only safe if this is right.

**A truth** is a fact about browsers, CSS, images or Figma. It holds on every target and belongs in
`SKILL.md` or `references/`.

**A scar** is a rule that exists to work around something Webflow does. It is not wrong — it was
earned — but carrying it to another target makes that target permanently worse for no reason. Scars
live in `targets/webflow.md`, and `targets/html.md` says what replaces them, or that nothing does.

The distinction matters because scars do not announce themselves. "Never build a responsive break on
`<br>`" reads like a web-development principle. It is not. It is a fact about Webflow's publisher.

---

## Truths — portable to every target

| Rule | Where it lives | Why it holds everywhere |
|---|---|---|
| Measure in a true viewport | `references/verification.md` | A fluid root font-size resolves against the real width. The 41%-vs-63/63 audit was one window size |
| Assert root font-size before trusting any rem figure | `verification.md` | Same trap, one line earlier |
| Group rendered lines by **vertical overlap**, never `top` | `verification.md`, `bin/gate.js` | Glyph boxes on one line differ in `top` at any size or weight change. Pure text-layout fact |
| `Range.getClientRects().length` is not a line count | `verification.md` | Returns one rect per child node |
| Measure after `document.fonts.ready`, not `DOMContentLoaded` | `verification.md` | Webfonts load after DCL; fallback metrics are wrong by pixels per line |
| Do not compensate for the iframe scrollbar | `verification.md` | Padding the width moves the *media* width past the breakpoint |
| `background-size: cover` on a content-sized box re-crops the photo | `SKILL.md` layout contract | CSS behaviour. Caused every mis-crop in project one |
| `background-size` = the image's **intrinsic width** | `SKILL.md` | An image's intrinsic size is a pixel fact |
| Section holds the padding; container holds the `max-width` | `SKILL.md` | Box-model consequence. Two ladders drift apart on any platform |
| No `max-width` on the container at mobile | `SKILL.md` | The viewport is already the constraint |
| Section padding flat; `max-width` does the work | `SKILL.md` | Apparent desktop gutters are centring residue, not authored insets |
| Header and footer are page landmarks, not section content | `SKILL.md` | Document outline / a11y |
| rem everywhere; em for `letter-spacing`; px only for `background-size` | `SKILL.md` | CSS unit semantics |
| A correct rem conversion changes **nothing** | `SKILL.md` | At a 16px root the numbers are identical. The falsifier |
| Figma `leading-[normal]` ≠ browser `normal` (1.25 vs ~1.45) | `SKILL.md` | Two renderers, two defaults |
| Export → rename → AVIF → commit, before building | `SKILL.md` Stage 0.5 | Asset discipline. Format is a web fact |
| AVIF quality 70 photo / 85 flat, 4096-colour threshold, `speed=4` | `bin/to-avif.py` | Measured encoder behaviour |
| Alpha dropped only when provably unused | `bin/to-avif.py` | 14 of 16 Figma exports carry an opaque alpha channel |
| Content images get descriptive alt; decorative get explicit empty alt | `SKILL.md` | HTML semantics |
| Line breaks: read the design's break before fixing it | `SKILL.md` Stage 5 | Method, not mechanism |
| Assert **which words** end each line, never a line count | `SKILL.md` | A build where every break fires at every width counts the same as a correct one |
| Wrap the text in the span; never toggle an empty marker | `SKILL.md` | An empty hidden element leaves no whitespace. DOM fact |
| Block spans cannot overlap | `SKILL.md` | Two breakpoints breaking at different mid-sentence words cannot share one set |
| Check the ranges, not just the three widths | `verification.md` | Breakpoint bands exist between the designed widths |
| Re-run the whole gate after every fix | `verification.md` | A fix broke the section it was fixing |
| Layer names may lie — read rendered content | `SKILL.md` Stage 0 | Figma fact |
| Raw x/y mislead on rotated and auto-layout nodes | `SKILL.md` Stage 0 | Figma fact |
| `get_metadata` gives structure, not style values | `references/figma.md` | Figma API fact |
| `get_design_context` needs its skill loaded first | `references/figma.md` | Figma MCP fact |
| Refuse to proceed without three distinct frames at three widths | `SKILL.md` Stage 0 | Measuring one frame thrice makes everything look non-responsive |
| Two styling systems on two breakpoint maps will disagree | `SKILL.md` Stage 6 | The *principle*. Its Webflow mechanics are a scar — see below |
| A check that shares the build's assumption confirms it | `SKILL.md` Status | The lesson from four probe bugs |

## Scars — Webflow only

| Rule | Replaced on the HTML target by |
|---|---|
| Anything the API cannot write goes in the repo as a paste | **Nothing.** You write files; there is no API to refuse you |
| Keep a source of truth outside the Designer | **Nothing.** The repo *is* the source |
| Pastes arrive truncated — compare character counts | **Nothing.** No paste box |
| API writes and Designer saves clobber each other | **Nothing.** No second writer |
| Size variables reject CSS expressions (`clamp()` fails) | **Nothing.** `clamp()` is just CSS |
| Responsive values live in **variable modes** | CSS custom properties redefined per media query. *Principle survives, mechanism changes* |
| Styles are class-based, not selector-based; no descendant selectors | **Relaxes.** Write `.nav.is-scrolled .link` |
| A modifier needs a standalone style block for IX3 to address it | **Nothing.** No IX3 |
| Combo classes bake in `display`; set it inline from script | **Nothing.** No combos |
| Never build a responsive break on `<br>` — classes are stripped | **Relaxes.** `<br class>` survives. Method 2 is no longer forced |
| Reserved class names silently dropped (`.label`) — query utilities back | **Relaxes.** No reserved names |
| Client-First underscores become Designer folders | Convention kept for consistency; **this rationale does not apply** |
| Why not BEM: `--` fights Webflow's modifier mechanism | **Moot.** Either convention works |
| `alt` is a setting, not an attribute (`set_settings`/`altText`) | `alt=""` in the markup |
| `grid-row-gap` accepts variables; `row-gap` does not | **Relaxes.** Use `row-gap` |
| `-webkit-appearance` rejected; use unprefixed | **Relaxes.** Write either |
| Large WHTML payloads fail with `ECONNRESET` — split the build | **Nothing.** Writing a file has no payload limit |
| The WHTML builder puts a form's class on the `.w-form` wrapper | **Nothing.** You write the `<form>` |
| Asset deletes are soft; identical bytes resurrect the old record | **Nothing.** Files are files |
| `publish_site` returns before the CSS is live | **Nothing.** No publish step |
| Rate limits | **Nothing** |
| IX3 may be stored, accepted, listed — and never published | **Nothing.** You write the JS |
| Prefer page-level custom code over site-wide | **Nothing.** Scope is whatever you author |
| Webflow lazy-loads images by default (`loading="lazy"`) | **Partially relaxes.** Still set it deliberately; `gate.js` already treats *not loaded* as not a verdict |
| Breakpoint ladder `xxl/xl/large/main/medium/small/tiny` | **Relaxes, and improves.** Choose breakpoints from the design's own frames. The Frost build had to map 1920→`xxl`, 1440→`main`, and leave `large`/`xl` unused |

## Mixed — split, do not move whole

| Item | Truth half | Scar half |
|---|---|---|
| `## Do not grow a parallel responsive layer` | Two styling systems on two breakpoint maps disagree in the bands between them | "A variable's modes bind to Webflow's breakpoints" — the binding mechanism |
| `## Stage 4 — design system` | Semantic layer above primitives; primitives never responsive; minimum token set; every token traces to a measured value | Variable modes as the delivery mechanism |
| `## Class naming — Client-First` | The three-type convention (custom / utility / `is-` modifier) | Underscore→folder, the BEM argument, reserved names |
| `## Image metadata` | Descriptive vs explicitly-decorative alt, set at both levels | `altText` as a setting; `set_attributes` failing |
| `references/custom-code.md` | `document.fonts.ready`; the parallel-layer principle | The other five sections |

---

## Count

**33 truths · 26 scars · 5 mixed.** The scars are almost entirely in `references/webflow-mcp.md`
(185 lines, 95% Webflow — only its 5-line "Figma read tools" section is portable) and
`references/custom-code.md` (86 lines, of which 2 sections are truths).

`SKILL.md` itself is 50% fully portable, 42% mostly portable, 8% Webflow-specific — which is why the
stages survive the split unchanged and only their target bindings move.
