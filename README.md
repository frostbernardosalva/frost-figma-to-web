# frost-figma-to-web

Frost's Figma → Webflow conversion workflow, as a Claude Code plugin. It carries the Webflow MCP and
custom-code rules this team has already paid for once, so the next project does not rediscover them.

## Install

Once per developer, from any directory:

```
/plugin marketplace add frostbernardosalva/frost-figma-to-web
/plugin install frost-figma-to-web@frost-tools
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
rule-classification.md              every rule labelled browser-truth or platform-scar
agents/
  break-reader.md                   reads the DESIGN's line breaks. Returns a table, never a verdict
bin/
  to-avif.py                        Stage 0.5 — converts, or exits 1 with the install command
  gate.js                           the Stage 5 probes, as code that can be run
  verify.py                         render a page headless at a real width, run the gate
  break-diff.py                     diff design breaks against built breaks, word by word
  audit-assets.py                   what an already-built site would save by going AVIF
  check-deps.py                     warns about a missing AVIF encoder. Never blocks
  fixtures/
    gate-fixture.html               a page that is wrong on purpose
    gate-fixture.test.js            the expectations, read off a render
    run.py                          drives headless Chrome; exit 1 on regression
hooks/
  hooks.json                        SessionStart only — the dependency warning
evals/
  asset-prep/                       does a fresh reader actually run the converter?
  gate-probe/                       does it use the shipped probe, or reinvent the broken one?
  scaffold.py                       generates the inputs both cases need
skills/figma-to-web/
  SKILL.md                          the staged workflow and its gates, target-neutral
  targets/
    webflow.md                      the MCP write rules, quirks and custom-code discipline
    html.md                         vanilla HTML/CSS/JS — write files, verify headless
  references/
    verification.md                 how to run the gate, and the false positives
    figma.md                        reading the design file
  templates/
    relationship-table.md           Stage 3, with a worked example
    annotation-spec.md              Stage 1 — behaviour, states, identity, deliberate-vs-drift
    CLAUDE.md                       per-project facts and the deviation log
```

### Two targets, one set of stages

`SKILL.md` holds the stages; `targets/` holds what changes between platforms. The split was made by
classifying every rule as a **browser truth** (holds everywhere) or a **platform scar** (exists only
to work around one platform) — `rule-classification.md`, 33 truths, 26 scars, 5 that split.

The distinction matters because scars do not announce themselves. *"Never build a responsive break
on `<br>`"* reads like a web-development principle; it is a fact about one publisher stripping
classes. Carry it to another target and it becomes permanent cruft.

Measured before the split: `SKILL.md` was **50% fully portable, 42% mostly, 8% platform-specific** —
and the one claim with a blinded test behind it, Stage 3, had zero platform references.

**Evidence, honestly:** Webflow has two full projects behind it. The HTML target has **one section**,
gated at four breakpoints — containers exact, heights within 0.9px. That shows the stages survive a
change of target. It does not show the HTML target works on a full page.

### Two rules execute; the rest are instructions

Most rules here are followed by being followed: a reader writes `rem` instead of `px` and the rule
has happened. Two are not like that, and both were failing silently.

**AVIF conversion needs a tool that may not be installed.** `bin/to-avif.py` exits **1** with the
install command for the platform rather than leaving you with PNGs and no warning. It reproduces
the hand-run it replaces byte-for-byte across 16 files (14.60 MiB → 705.1 KiB).

That covers the case where the **encoder** is missing. It cannot cover the case where **Python** is
missing, because the script — and the dependency checker — are written in it. So the interpreter
case is handled where Python is not required:

| Missing | What happens |
|---|---|
| Encoder | `to-avif.py` exits 1, writes nothing, names the install |
| Encoder | the `SessionStart` hook warns before any work starts |
| **Python** | the hook's shell guard prints the install line and still exits 0 |
| **Python** | Stage 0.5 step 0 runs `--help` first, and stops before upload |
| Either, all missed | rule 5 (`legacyAssets`) fails the build on leftover `.png` references |

Claude **offers** to run the install and waits for a yes. It never installs unasked — that changes
what is on someone's machine.

**The verification probes need to be run to be known correct.** They used to live as eight snippets
across two markdown files, retyped each build. Running them as code against a deliberately-wrong
page found **four bugs in the probes themselves**, three of which returned a confident `pass`:

| | |
|---|---|
| grouped lines by rect `top` | the same file warned against it 66 lines away |
| the legacy-asset regex | never matched `url("x.png")` — quote and paren, not end-of-string |
| `if (rule.cssRules)` | CSS Nesting made it truthy for every plain rule; the unit audit skipped them all |
| `!img.complete` | reported every lazy image as BROKEN; Webflow lazy-loads by default |

```
python bin/fixtures/run.py        # 15 checks, exit 1 on regression
```

### Running the evals

```
claude plugin eval . --scaffold --allow-tools Bash Read Glob Grep Skill Write Edit
```

Both cases need a shell, and the runner refuses to grant one without a sandbox backend — so they do
**not** run on Windows (`sandbox is enabled but the Windows sandbox is not active`). Linux, macOS or
CI. The suite is authored and parses; it has not yet produced a score, and no claim here rests on
one.

Note `--ablation with-without` is the default: the runner adds a no-plugin baseline arm on its own.
That is the shape `control-test.md` pre-registers, but not the experiment — the control grades
build fidelity against a real design, and is still blocked on an uncontaminated one.

## Not included, by design

- **Only one agent, and only where a script cannot reach.** `break-reader` exists because a natural
  wrap is not in the Figma file — you have to look at a rendered picture and read the words, which
  no CLI can do. It returns measurements, never a verdict, and the comparison is `break-diff.py`.
  Nothing else here is an agent: the build path is serial and stateful, and parallelising it would
  save minutes while risking conflicting writes.
- **No `Stop` hook.** It would fire on every session where the plugin is installed, including work
  with nothing to do with Webflow, and add latency to every turn to nag about a gate that is usually
  irrelevant. The gate stays explicit. The only hook is a `SessionStart` warning that never blocks.
- **No behaviour library.** Accordions, carousels and scroll animations are browser code, not
  instructions for Claude. They belong in their own repo, loaded by the site at runtime.
- **No project facts.** Site IDs, file keys and node ids go in the per-project `CLAUDE.md`.
