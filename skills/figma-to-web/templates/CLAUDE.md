# CLAUDE.md — <project>

Per-project facts. **Universal knowledge does not belong here** — the stages, the layout contract
and the target rules live in the `frost-figma-to-web` plugin, so they reach every project instead of
one. What belongs here is everything true of *this* project only.

**Figma is always the source.** Where the output goes depends on the target — a platform reached
through MCP, or files in this repo. Record which below, because most of this file depends on it.

## Files

| File | What it is |
|---|---|
| `annotation-spec.md` | What the design leaves unstated — Stage 1 |
| `relationship-table.md` | Responsive relationships, every breakpoint frame — Stage 3 |
| `custom-code/` | *Platform targets only.* Source of truth for anything pasted into the platform. **Not wired to anything** — editing a file here changes nothing until it is pasted and published. On a file target, delete this row: the repo *is* the source |

## Decisions made

**Target:** `<webflow | html>` — read `targets/<target>.md` before Stage 4. It decides how tokens are
delivered, how Stage 5 writes, and which constraints apply at all. Several rules in the skill exist
only to work around one platform; `rule-classification.md` records which.

**Breakpoint map:** `<the ladder you adopted | the widths taken from the design's frames>`. One map
for the whole project — record it and do not let a second one appear. Two styling systems on two
maps disagree in the bands between them, and the disagreement surfaces at one viewport width and
nowhere else.

**Class namespace:** `<ns>` — every custom class is `<ns>_component_element`, modifiers are `is-`
prefixed, utilities are dash-only. Client-First; see the skill's **Class naming** section. The
convention is fixed, the namespace is this project's alone.

**Annotations live in:** `<spec doc | Figma Dev Mode | duplicate file>`.

**Figma is:** `<read-only | annotatable>`. If read-only, say what the restriction covers — a ban on
editing, renaming and restructuring is a ban on changing the design, which is not the same as a ban
on annotation. Record the intent, not just the rule.

## Identifiers

**Figma** — always
```
file key   <key>
<name>     <node-id>    <w> × <h>
<name>     <node-id>    <w> × <h>
<name>     <node-id>    <w> × <h>
```

Then **one** of the following. Delete the other.

**Webflow target**
```
site                 <id>    <subdomain>.webflow.io
pages                <id>    "<slug>"
root element         <id>    ← append new sections here
variable collection  <id>
  ├ Tablet mode      <id>    bound to breakpoint "medium"
  └ Mobile mode      <id>    bound to breakpoint "small"
```

**HTML target**
```
output      <dir>/index.html · styles.css
assets      <dir>/assets/     committed AVIFs and SVGs
breakpoints <list>            taken from the design's frames
served by   <local path | url>   for bin/verify.py
```

## Token architecture

```
<collections or :root blocks, with counts and what each layer is for>
```

Rules that hold on every target, restated because they are easy to violate:
- Components reference the **semantic** layer, never primitives.
- **A token resolves to its own per-breakpoint value; components carry no override** for type or
  semantic spacing. The delivery mechanism is the target's — variable modes, or custom properties
  redefined inside each media query — but the principle does not change.
- Primitive spacing is never responsive; semantic spacing usually is.
- **Every measurement is `rem`** (÷ 16 from the design's px). `letter-spacing` is **`em`**.
  `background-size` is the one px exception — an image's intrinsic size is a pixel fact.
- **Never write `line-height: normal`.** Figma's `leading-[normal]` and the CSS keyword are
  different numbers on the same face. Record the measured ratio as a token.

*Webflow target only:* gaps must be written as the legacy `grid-row-gap` / `grid-column-gap`, which
accept variables where `row-gap` does not, and modifiers are combo classes rather than descendant
selectors. Both are platform constraints — see `targets/webflow.md`. Neither applies to a file
target; do not carry them there.

### Container ladder

```
section      padding-block: <responsive>   padding-inline: <flat, = the mobile gutter>
  container  max-width: <content width per breakpoint>   margin-inline: auto   — no padding
```

| | <bp1> | <bp2> | <bp3> | <bp4> |
|---|---|---|---|---|
| Section `padding-inline` | | | | |
| Container `max-width` | | | | **none** — `width: 100%` |
| Resulting content width | | | | |

Every container on the page returns the **same** number at each width — the footer included. Check
them together, not one at a time.

## Deviation log

**Required deliverable, written as changes are made — not at audit time.** An undocumented change
reads as a defect later even when the reasoning was sound.

| Date | What | Design said | Built as | Why |
|---|---|---|---|---|
| | | | | |

## State and open decisions

Built and verified: `<summary>`

Blocking further work:
- `<decision>` — what it blocks, and what the options are

Assumptions needing design sign-off: `<list — anything derived rather than measured>`
