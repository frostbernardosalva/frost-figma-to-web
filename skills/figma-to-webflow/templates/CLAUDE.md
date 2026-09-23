# CLAUDE.md — <project>

Per-project facts. **Universal knowledge does not belong here** — the Webflow MCP rules and the
custom-code rules live in the `frost-webflow` plugin, so they reach every project instead of one.
What belongs here is everything true of *this* project only.

The actual work happens in **Webflow** and **Figma**, reached through MCP. Treat those as the
codebase.

## Files

| File | What it is |
|---|---|
| `annotation-spec.md` | What the design leaves unstated — Stage 1 |
| `relationship-table.md` | Responsive relationships, all three frames — Stage 3 |
| `custom-code/` | Source of truth for anything pasted into Webflow. **Not wired to anything** — editing a file here changes nothing until it is pasted and published |

## Identifiers

**Webflow**
```
site                 <id>    <subdomain>.webflow.io
pages                <id>    "<slug>"
root element         <id>    ← append new sections here
variable collection  <id>
  ├ Tablet mode      <id>    bound to breakpoint "medium"
  └ Mobile mode      <id>    bound to breakpoint "small"
```

**Figma**
```
file key   <key>
Desktop    <node-id>    <w> × <h>
Tablet     <node-id>    <w> × <h>
Mobile     <node-id>    <w> × <h>
```

## Decisions made

**Breakpoint map:** `<native ≤991/≤767>` or `<custom>`. One map for the whole project — record which
and do not let a second one appear.

**Class namespace:** `<ns>` — every custom class is `<ns>_component_element`, modifiers are `is-`
combo classes, utilities are dash-only. Client-First; see the skill's **Class naming** section. The
convention is fixed, the namespace is this project's alone.

**Annotations live in:** `<spec doc | Figma Dev Mode | duplicate file>`.

**Figma is:** `<read-only | annotatable>`. If read-only, say what the restriction covers — a ban on
editing, renaming and restructuring is a ban on changing the design, which is not the same as a ban
on annotation. Record the intent, not just the rule.

## Token architecture

```
<collections, with counts and what each layer is for>
```

Rules that apply everywhere and are worth restating per project because they are easy to violate:
- Components reference the **semantic** layer, never primitives.
- Responsive values live in **variable modes**, not breakpoint overrides.
- Primitive spacing is never responsive; semantic spacing usually is.

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
