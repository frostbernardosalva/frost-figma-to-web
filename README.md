# frost-webflow

Frost's Figma → Webflow conversion workflow, as a Claude Code plugin. It carries the Webflow MCP and
custom-code rules this team has already paid for once, so the next project does not rediscover them.

## Install

Once per developer, from any directory:

```
/plugin marketplace add frostbernardosalva/frost-figma-to-webflow
/plugin install frost-webflow@frost-tools
```

Restart Claude Code. The skill is then available in **every** folder, which is the point — each
client project is a different directory.

To update later:

```
/plugin marketplace update frost-tools
```

## Use

Open Claude Code in the project folder, with the Figma file open in the desktop app, and say:

> Convert the hero section of `<figma url>` into the Webflow site `<name>`

The skill runs in stages and stops for your input at each gate.

## Permissions

Copy into the project's `.claude/settings.local.json` so the build is not interrupted by approvals.
**Read-only Figma** — the default:

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Webflow__data_sites_tool",
      "mcp__claude_ai_Webflow__data_pages_tool",
      "mcp__claude_ai_Webflow__data_agent_instructions_tool",
      "mcp__claude_ai_Webflow__data_element_tool",
      "mcp__claude_ai_Webflow__data_variable_tool",
      "mcp__claude_ai_Webflow__data_style_tool",
      "mcp__claude_ai_Webflow__data_fonts_tool",
      "mcp__claude_ai_Webflow__data_scripts_tool",
      "mcp__claude_ai_Webflow__data_assets_tool",
      "mcp__claude_ai_Webflow__data_whtml_builder",
      "mcp__claude_ai_Webflow__data_element_settings_tool",
      "mcp__claude_ai_Figma__get_design_context"
    ]
  }
}
```

Only one Figma tool is listed, and that is deliberate: it makes "do not modify the design" a
property of the configuration rather than a rule someone has to remember. **If a project decides
annotations may be written into Figma, a write-capable Figma tool has to be added here** — which
means the decision gets made explicitly, in a file, rather than by accident mid-build.

## The stages

| Stage | Produces | Gate |
|---|---|---|
| 0 · Audit | Findings — what is here, missing, or drift | |
| 1 · Annotate | `annotation-spec.md` | |
| 2 · Decide | Breakpoint map · behaviour · fonts | **No build while open** |
| 3 · Relationship table | `relationship-table.md` | **All three frames, ≥2 sections per row** |
| 4 · Design system | Variables and classes | |
| 5 · Build section | The section, plus a deviation log entry | **Verified at three breakpoints** |
| 6 · Behaviours | Custom code, kept minimal | |
| 7 · Fidelity pass | Should find little | |

Stage 5 repeats per section. That is the change that matters most: the gate is inside the loop, not
at the end.

## Why the gates produce documents

A rule in a file is advisory, and a teammate on a deadline skips steps nobody can see were skipped.
Each gate here produces an artifact whose *incompleteness is visible* — an unmeasured breakpoint is
an empty cell in the relationship table, and an unrecorded change is a missing row in the deviation
log. That is what makes the process survive contact with a second person.

## What this is derived from, and what that means

One project, and one measurement. The rules in `skills/figma-to-webflow/references/` describe
Webflow and the browser and generalise safely.

**The method has been tested once.** A reader given only a Figma file key, three node ids and the
table structure — no access to the source project and no knowledge of what it was expected to find —
re-derived **seven of the nine** responsive relationships that a hand pass had originally caught only
*after* the build was already wrong. It correctly separated two curves that agree at desktop and
diverge below, which is the conflation that caused the original defect. It missed one element width
and merged three gaps sharing a desktop value into one row; both are fixed in the template. Full
record in `method-test.md`.

**What that does not show:** whether the workflow is faster end to end. It front-loads measurement
to remove rework, and that trade has never been measured on a complete project. Do not claim it is.

The failure it exists to prevent: a value that is correct at desktop and wrong below it. In the
project this came from, that single pattern accounted for nine spacing relationships, four type
roles collapsed onto two classes, and a type ramp wrong at all three breakpoints — because the token
system had no semantic layer to express a responsive relationship, and verification checked desktop
first.

## Layout

```
skills/figma-to-webflow/
  SKILL.md                          the staged workflow and its gates
  references/
    webflow-mcp.md                  write rules — read before any Webflow write
    custom-code.md                  paste discipline, fonts.ready, combo display, clobbering
  templates/
    relationship-table.md           Stage 3, with a worked example
    annotation-spec.md              Stage 1 — behaviour, states, identity, deliberate-vs-drift
    CLAUDE.md                       per-project facts and the deviation log
```

## Not included, by design

- **No agent.** The plausible one — "measure a section at three breakpoints, return only the table" —
  would keep node dumps out of the conversation, but nothing has established that reading is where
  the context goes. Add it when the need is observed, and bundle it in here rather than beside it.
- **No behaviour library.** Accordions, carousels and scroll animations are browser code, not
  instructions for Claude. They belong in their own repo, loaded by the site at runtime.
- **No project facts.** Site IDs, file keys and node ids go in the per-project `CLAUDE.md`.
