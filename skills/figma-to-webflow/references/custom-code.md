# Custom code in Webflow

For behaviour Webflow cannot express: accordions, carousels, scroll-triggered animation, form
prefill. Each rule below traces to a defect that shipped.

## Standing rule: anything the API cannot write goes in the repo as a paste

**When a Webflow API call refuses something, do not work around it by changing the design
decision.** Write the thing as a complete, paste-ready file in the project's `custom-code/`
folder, with a header comment naming exactly where it goes, and tell the developer to paste it.

The API refuses more than it documents. Known so far:

- **Size variables reject CSS expressions.** `create_size_variable` and `update_size_variable` both
  fail with *"An internal error occurred"* on a `custom_value` such as
  `clamp(1.5rem, 2.0833vw, 2.5rem)` — despite the field being documented as accepting an arbitrary
  CSS expression. So fluid type and spacing scales cannot be built as variables.
- **No write path for page custom code** at all — `update_page_settings` covers SEO, Open Graph,
  slug and JSON-LD only, and its `draft` flag is silently dropped.

**Prefer page-level custom code over site-wide.** A root font-size rule pasted site-wide rescales
every other page on that site, including design systems built earlier. Page settings scope it to
the one page being built. Only go site-wide when the effect is genuinely meant to be global.

## Keep a source of truth outside the Designer

Snippets pasted into Webflow exist nowhere else unless you mirror them in the project repo. A
mirrored file is **not wired to anything** — editing it changes nothing until it is pasted and
published. Keep the two in sync by hand and say so in the project's README, or the mirror silently
becomes fiction.

Each mirrored file should be the complete paste, including its `<script>` / `<style>` tags, with a
header comment naming what it does, where it lives, and what it depends on.

## Paste carefully — pastes arrive truncated

**Three pastes in one project arrived with lines silently missing.** One lost a key and a closing
brace from an array; another lost a transition line and an entire loop. Both produced a syntax
error, and **a syntax error kills the whole file** — so the symptom is "nothing happens at all", not
"one feature is broken".

Before publishing:

1. Compare the character count against the source file.
2. Open the DevTools console on the published page. A syntax error shows immediately and names the
   token, which is far faster than inferring it from behaviour.

## Measure after the page settles, not at `DOMContentLoaded`

**Anything that measures rendered text must wait for `document.fonts.ready`.** `DOMContentLoaded`
fires before webfonts load, so measurements taken there use fallback metrics and are wrong by a few
pixels per line — enough to break a height lock.

**Three separate defects in one project traced back to exactly this.** The symptom is always
intermittent and always worse on a cold cache, which makes it easy to dismiss as fixed: with fonts
already cached they load before `DOMContentLoaded` and nothing goes wrong.

To reproduce: DevTools → Network → **Disable cache**, ideally throttled to Slow 3G. That widens the
gap between `DOMContentLoaded` and fonts arriving.

## Combo classes can bake in `display`

Webflow writes an element's *current* display state into a combo created while the element is
visible. Four accordion panels picked up `display: block` this way and were forced permanently open.

Set `display` **inline** from script, which outranks any class, so it cannot happen again.

## API writes and Designer saves clobber each other

A `margin-top: auto` written through the API was silently replaced by a Designer save. **If the
Designer is open, prefer making style changes there.** Otherwise the last writer wins and neither
side reports a conflict.

## Do not grow a parallel responsive layer

A hand-written CSS block in Page Settings is a second styling system. If it uses different
breakpoints from Webflow's native ones, the two disagree in the bands between them, and the
disagreement surfaces as a bug that appears at one viewport width and nowhere else.

Worse, it constrains the design system: a variable's modes bind to Webflow's breakpoints, so a token
minted while the two maps disagree applies its values into a band the custom layer treats
differently. **Settle the breakpoint map before writing responsive custom CSS**, and keep the layer
shrinking rather than growing.
