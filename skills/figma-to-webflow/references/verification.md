# Verification — running the Stage 5 gate

Rows 1–6 of the gate are a script. Row 7 is a screenshot, at 1:1, per element.

Everything here was written by debugging it against a real build. The false positives in the last
section cost more time than the true positives did, which is why they sit beside the checks rather
than in a footnote.

## Measure in a true viewport, or the numbers are fiction

**The first audit on this workflow reported 41%. Every failure was at exactly 85% of expected.**

That was not a build fault. The host window was 1536px wide, the page carried a fluid root
font-size, and `0.25rem + 0.625vw` at 1536 resolves to **13.6px** — 85% of 16. Every `rem` value was
being compared against a 1920px design figure. Re-run inside a true 1920 viewport: **63/63**.

So: render the page in an **iframe at the real width**, scaled down visually with a CSS transform if
it has to fit the screen. Never measure in a window that merely approximates the breakpoint.

```js
// harness: real-width iframe, visually scaled to fit
document.documentElement.innerHTML =
  '<head><style>*{margin:0;padding:0}body{background:#222;overflow:hidden}' +
  '#wrap{transform-origin:0 0}#f{border:0;display:block}</style></head>' +
  '<body><div id="wrap"><iframe id="f"></iframe></div></body>';

window.__show = (path, w, h) => new Promise(res => {
  const f = document.getElementById('f'), wrap = document.getElementById('wrap');
  f.style.width = w + 'px'; f.style.height = h + 'px';
  wrap.style.transform = 'scale(' + Math.min(innerWidth / w, innerHeight / h) + ')';
  f.onload = () => setTimeout(() => res(f.contentDocument), 1500);
  f.src = path;
});
```

Confirm `getComputedStyle(doc.documentElement).fontSize` is what the design assumes **before**
trusting a single measurement.

## Row 4 — text content

Diff the rendered text of each block against the Figma text, whitespace-normalised. This catches
dropped copy and, more importantly, words fused together at an element boundary.

## Row 5 — assets resolve

An asset is fine only if it is present **and** painted. See the SVG and hidden-image traps below
before writing the assertion.

## Row 6 — break points, not break counts

Counting `<br>`/`<span>` elements proves nothing: a build where every break fires at every width
counts the same as one where they fire correctly. **Assert which word each rendered line ends on.**

```js
// last word of every rendered line in a text block
function lineEnds(el) {
  const node = [...el.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
  if (!node) return [];
  const r = document.createRange(), out = [];
  let top = null, lastWord = '';
  const words = node.textContent.split(/(\s+)/);
  let i = 0;
  for (const w of words) {
    r.setStart(node, i); r.setEnd(node, i + w.length);
    const t = Math.round(r.getBoundingClientRect().top);
    if (top !== null && t !== top) out.push(lastWord);
    if (w.trim()) { lastWord = w; top = t; }
    i += w.length;
  }
  out.push(lastWord);
  return out;
}
```

Compare that array against the frame, per breakpoint. A mismatch names the exact word.

### Glue detector

For every break marker, read the character immediately before and after it in document order. Flag
it when the marker is hidden and **neither** side carries whitespace — that is the
`craftingend-to-end` defect, and it is invisible to both a value audit and a casual read.

```js
const glued = [];
doc.querySelectorAll('[class*="brk"], br').forEach(el => {
  if (getComputedStyle(el).display !== 'none') return;
  const w = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  // walk to find the text node before and after `el`, then:
  //   if (!/\s$/.test(before) && !/^\s/.test(after)) glued.push(before.slice(-14) + '|' + after.slice(0, 14));
});
```

## Four false positives — check for these before reporting a failure

All four fired during one build. Each produced a defect report that was wrong, and two of them cost
an hour apiece.

| Symptom | Why it is not a defect |
|---|---|
| `img.naturalWidth === 0` on a visible SVG | **SVG has no intrinsic raster size.** `naturalWidth` is legitimately `0` while the image renders perfectly. Test SVG by `getBoundingClientRect()` instead. |
| `img.complete === false` | An image inside a `display: none` subtree never starts loading. It is hidden, not broken. Skip anything whose layout box is zero. |
| "Only N logo rows — expected M" | Counting distinct `top` values counts **differing item heights**, not rows. Items of unequal height on the same row report different `top`. Group by row midpoint, or compare against the container instead. |
| A layout check fails with `NaN` | `Math.abs(actual - expected)` on non-numeric values — `"none" - "none"` is `NaN`, and `NaN` fails every comparison. Use a type-aware comparator: strings compare with `===`, numbers with a tolerance. |

**A gate that cries wolf gets switched off.** If a row fails, reproduce the failure by hand once
before writing it down as a defect.

## Recording the result

Write pass/fail per row per section as you go, not at the end. A row that was never run is not a
pass, and the record should make that visible rather than silently absorb it.
