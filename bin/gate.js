/**
 * gate.js — the Stage 5 verification probes, as one file that can be run.
 * =============================================================================
 *
 * WHY THIS IS A FILE AND NOT A CODE BLOCK IN THE SKILL
 *
 *   These probes used to live as eight snippets across SKILL.md and
 *   references/verification.md, retyped from memory each build. One of them —
 *   the line-break probe — grouped characters by `getBoundingClientRect().top`,
 *   which the SAME FILE warned against 66 lines further down, because bold and
 *   regular glyphs on one line have different tops. The prose was right and the
 *   code was wrong and nothing could tell, because the code was never run as
 *   code. It cost real time on the Frost headline: the probe reported an
 *   orphaned word that did not exist, and the fix chased it for a while.
 *
 *   A file can have a fixture. bin/fixtures/gate-fixture.html contains the exact
 *   mixed-weight case that produced the phantom word, so it cannot come back.
 *
 * HOW TO RUN IT
 *
 *   This is browser code, not Node. Read the file and evaluate its contents in
 *   the page under test (Chrome MCP `javascript_tool`, or devtools). It defines
 *   window.__frostGate and returns nothing.
 *
 *     const G = window.__frostGate;
 *     G.rootFontSize(doc)        // ALWAYS first — see below
 *     G.lineEnds(doc.querySelector('.fr_hero_title'))
 *     G.containers(doc, '[class*="_inner"], .fr_container')
 *     G.legacyAssets(doc); G.altAudit(doc); G.unitAudit(doc); G.glue(doc)
 *
 *   Every check returns { row, status: 'pass'|'fail'|'info', detail }.
 *   `status` is advisory. `detail` is the evidence, and the evidence is what
 *   goes in the build log — never "looks right".
 *
 * THE TRAP THAT INVALIDATES EVERYTHING ELSE
 *
 *   Measure in a TRUE viewport or the numbers are fiction. The first audit on
 *   this workflow reported 41%, with every failure at exactly 85% of expected —
 *   not a build fault, but a 1536px host window resolving a fluid root font-size
 *   to 13.6px against 1920px design figures. Re-run at a real width: 63/63.
 *   Use G.harness(), and call G.rootFontSize() before trusting one measurement.
 */

(function () {
  'use strict';

  const ok = (row, detail) => ({ row, status: 'pass', detail });
  const no = (row, detail) => ({ row, status: 'fail', detail });
  const info = (row, detail) => ({ row, status: 'info', detail });

  // ---------------------------------------------------------------------------
  // harness — render at the real width, scale only for looking at it
  // ---------------------------------------------------------------------------

  function harness(path, w, h) {
    document.documentElement.innerHTML =
      '<head><style>*{margin:0;padding:0}body{background:#222;overflow:hidden}' +
      '#wrap{transform-origin:0 0}#f{border:0;display:block}</style></head>' +
      '<body><div id="wrap"><iframe id="f"></iframe></div></body>';

    return new Promise((res) => {
      const f = document.getElementById('f');
      const wrap = document.getElementById('wrap');
      f.style.width = w + 'px';
      f.style.height = h + 'px';
      // Visual scale only. NEVER pad the width to compensate for a scrollbar:
      // that pushes the MEDIA width past the breakpoint and silently renders
      // the desktop layout at a "980" test. Hide the scrollbar instead.
      wrap.style.transform = 'scale(' + Math.min(innerWidth / w, innerHeight / h) + ')';
      f.onload = () => setTimeout(() => {
        try {
          const d = f.contentDocument;
          const s = d.createElement('style');
          s.textContent = 'html{scrollbar-width:none}::-webkit-scrollbar{display:none}';
          d.head.appendChild(s);
        } catch (e) { /* cross-origin: caller will see it */ }
        res(f.contentDocument);
      }, 1500);
      f.src = path;
    });
  }

  function rootFontSize(doc) {
    const px = parseFloat(getComputedStyle(doc.documentElement).fontSize);
    return px === 16
      ? ok(0, 'root font-size 16px — rem figures are comparable to the design')
      : no(0, `root font-size ${px}px, not 16px. Every rem measurement below is ` +
              `scaled by ${(px / 16).toFixed(3)}. Fix the viewport before reading anything else.`);
  }

  // ---------------------------------------------------------------------------
  // row 6 — line breaks: the words, not the count
  // ---------------------------------------------------------------------------

  /**
   * Every rendered word with its box, in document order, skipping hidden nodes.
   */
  function wordBoxes(el) {
    const doc = el.ownerDocument;
    const win = doc.defaultView;
    const walker = doc.createTreeWalker(el, win.NodeFilter.SHOW_TEXT);
    const range = doc.createRange();
    const out = [];
    let node;

    while ((node = walker.nextNode())) {
      if (!node.textContent.trim()) continue;
      const parent = node.parentElement;
      if (parent && win.getComputedStyle(parent).display === 'none') continue;

      const re = /\S+/g;
      let m;
      while ((m = re.exec(node.textContent))) {
        range.setStart(node, m.index);
        range.setEnd(node, m.index + m[0].length);
        const r = range.getBoundingClientRect();
        if (r.width || r.height) {
          out.push({ word: m[0], top: r.top, bottom: r.bottom, mid: (r.top + r.bottom) / 2 });
        }
      }
    }
    return out;
  }

  /**
   * Group words into rendered lines by VERTICAL OVERLAP, not by `top`.
   *
   * This is the fix. A 700-weight glyph and a 400-weight glyph on the same line
   * report different rect tops, so keying on `top` starts a new line at every
   * font-weight change and invents an orphaned word. Two boxes are on the same
   * line when either one's midpoint falls inside the other's band — mutual, so
   * it holds whether the new word is taller or shorter than the run so far.
   */
  function groupLines(boxes) {
    const lines = [];
    for (const b of boxes) {
      const cur = lines[lines.length - 1];
      const curMid = cur ? (cur.top + cur.bottom) / 2 : null;
      const sameLine = cur &&
        ((b.mid >= cur.top && b.mid <= cur.bottom) ||
         (curMid >= b.top && curMid <= b.bottom));

      if (sameLine) {
        cur.words.push(b.word);
        cur.top = Math.min(cur.top, b.top);
        cur.bottom = Math.max(cur.bottom, b.bottom);
      } else {
        lines.push({ top: b.top, bottom: b.bottom, words: [b.word] });
      }
    }
    return lines;
  }

  /**
   * The rendered lines of a text block, as arrays of words.
   * Returns { row, status, detail: { lines: [[w,…],…], text: ['…','…'], ends: […] } }
   *
   * `ends` is the last word of each line — compare it against the Figma frame
   * per breakpoint. A mismatch names the exact word. Do NOT assert a line COUNT:
   * a build where every break fires at every width counts the same as one where
   * they fire correctly.
   */
  function lineEnds(el) {
    if (!el) return no(6, 'element not found');
    const lines = groupLines(wordBoxes(el));
    return info(6, {
      lines: lines.map((l) => l.words),
      text: lines.map((l) => l.words.join(' ')),
      ends: lines.map((l) => l.words[l.words.length - 1]),
    });
  }

  /**
   * Hidden break markers with no whitespace on either side.
   *
   * An empty <span> toggled between block and none leaves NO space when hidden,
   * which is how `craftingend-to-end` and `EmergingBull Award` shipped — invisible
   * to a value audit and to a casual read, because it only appears at the
   * breakpoints where the marker is off.
   */
  function glue(doc) {
    const win = doc.defaultView;
    const found = [];

    const looseBr = [];

    doc.querySelectorAll('[class*="brk"], br').forEach((el) => {
      // A VISIBLE marker always renders its break, so it cannot glue anything.
      // Only a hidden one can. The first version exempted <br> from this check,
      // and flagged the two genuine address line breaks in the Frost footer.
      if (win.getComputedStyle(el).display === 'none') {
        if (el.textContent && el.textContent.trim()) return;   // Method 2: wraps its text, fine
      } else {
        // Separate concern, not glue: a <br> carrying a class is an attempt at
        // a responsive break, and Webflow strips those classes — so it fires at
        // every width at once. An unclassed <br> is a real line break and fine.
        if (el.tagName === 'BR' && String(el.className).trim()) {
          looseBr.push(String(el.className).trim());
        }
        return;
      }

      const walker = doc.createTreeWalker(doc.body, win.NodeFilter.SHOW_TEXT);
      let before = '', after = '', passed = false, node;
      while ((node = walker.nextNode())) {
        const pos = el.compareDocumentPosition(node);
        if (pos & Node.DOCUMENT_POSITION_FOLLOWING) { after = node.textContent; passed = true; break; }
        if (node.textContent.trim()) before = node.textContent;
      }
      if (!passed) after = '';

      if (before && after && !/\s$/.test(before) && !/^\s/.test(after)) {
        found.push({
          marker: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().replace(/\s+/g, '.') : ''),
          glued: before.slice(-14) + '|' + after.slice(0, 14),
        });
      }
    });

    if (found.length || looseBr.length) {
      return no(6, {
        glued: found,
        classedBr: looseBr,
        fix: 'glued: wrap the text in the span (Method 2), or put the space BEFORE the marker. ' +
             'classedBr: never build a responsive break on <br> — Webflow strips its classes, ' +
             'so it fires at every width. Use a span.',
      });
    }
    return ok(6, 'no glued break markers, no responsive breaks built on <br>');
  }

  // ---------------------------------------------------------------------------
  // row 1 — one container rule, everywhere
  // ---------------------------------------------------------------------------

  function containers(doc, selector) {
    const els = [...doc.querySelectorAll(selector)];
    if (!els.length) return no(1, `no elements match ${selector}`);

    const widths = els.map((el) => ({
      cls: (el.className || '(unclassed)').toString().trim().split(/\s+/)[0],
      w: Math.round(el.getBoundingClientRect().width * 100) / 100,
    }));
    const distinct = [...new Set(widths.map((x) => x.w))];

    return distinct.length === 1
      ? ok(1, `${els.length} containers, all ${distinct[0]}px`)
      : no(1, { distinct, widths, note: 'every container must return ONE number per width — the footer included' });
  }

  // ---------------------------------------------------------------------------
  // row 5 — assets resolve, and none of them are legacy rasters
  // ---------------------------------------------------------------------------

  function legacyAssets(doc) {
    // The terminator class matters. `/\.(png|jpe?g)(\?|#|$)/` looks right and
    // silently passes EVERY css background, because in a stylesheet the
    // extension is followed by a quote and a paren — `url("photo.png")` — not
    // by end-of-string. That bug shipped in this probe until the fixture caught
    // it.
    const legacy = /\.(png|jpe?g)(["')\?#]|$)/i;
    const hits = [];

    const pending = [];
    [...doc.images].forEach((i) => {
      const url = i.currentSrc || i.src;
      if (legacy.test(url)) hits.push({ where: '<img>', url });

      // `!i.complete || i.naturalWidth === 0` reports every lazy image below
      // the fold as BROKEN. Webflow sets loading="lazy" by default, so on the
      // Frost page that was five false positives — two hamburger icons hidden
      // above 991 and three section-6 assets that simply had not loaded.
      //
      // A load that FINISHED with no pixels is broken. A load still in flight
      // is not a verdict: scroll it into view, or re-run after load, and only
      // then believe it.
      if (i.complete && i.naturalWidth === 0) hits.push({ where: '<img> BROKEN', url });
      else if (!i.complete) pending.push(url.split('/').pop());
    });

    [...doc.styleSheets].forEach((sheet) => {
      let rules;
      try { rules = sheet.cssRules; } catch (e) { return; }   // cross-origin, skip
      [...(rules || [])].forEach((rule) => {
        const bg = rule.style && rule.style.backgroundImage;
        if (bg && legacy.test(bg)) hits.push({ where: rule.selectorText, url: bg });
      });
    });

    if (hits.length) return no(5, { hits, pending });
    return ok(5, 'zero legacy png/jpg references, no broken images' +
      (pending.length ? ` (${pending.length} lazy image(s) not yet loaded — not a failure: ${pending.join(', ')})` : ''));
  }

  // ---------------------------------------------------------------------------
  // rule 8 — every image has alt text, or is explicitly decorative
  // ---------------------------------------------------------------------------

  function altAudit(doc) {
    const missing = [];
    let described = 0, decorative = 0;

    [...doc.images].forEach((i) => {
      const src = (i.currentSrc || i.src || '').split('/').pop();
      if (!i.hasAttribute('alt')) missing.push({ src, why: 'no alt attribute at all' });
      else if (i.alt.trim() === '') decorative++;
      else described++;
    });

    return missing.length
      ? no(8, { missing, described, decorative,
                note: 'empty alt is correct for decorative images — but only when it was DECIDED, which means the attribute is present' })
      : ok(8, `${described} described, ${decorative} explicitly decorative, 0 missing`);
  }

  // ---------------------------------------------------------------------------
  // rule 6 — rem everywhere, em for letter-spacing, px only for background-size
  // ---------------------------------------------------------------------------

  function unitAudit(doc) {
    const exempt = new Set(['background-size', 'background-position', 'border-width',
                            'border-top-width', 'border-right-width',
                            'border-bottom-width', 'border-left-width']);
    const hits = [];

    [...doc.styleSheets].forEach((sheet) => {
      let rules;
      try { rules = sheet.cssRules; } catch (e) { return; }
      [...(rules || [])].forEach(function walk(rule) {
        // Recurse into @media and CSS-nested rules, then STILL read this rule's
        // own declarations. `if (rule.cssRules) { …; return; }` looks correct
        // and skips every plain rule, because CSS Nesting gave CSSStyleRule a
        // `cssRules` property and an empty CSSRuleList is truthy. That produced
        // a clean "no stray px" pass over a stylesheet full of px.
        if (rule.cssRules && rule.cssRules.length) [...rule.cssRules].forEach(walk);
        if (!rule.style) return;
        for (const prop of rule.style) {
          const v = rule.style.getPropertyValue(prop);
          if (exempt.has(prop)) continue;
          if (prop === 'letter-spacing' && /px/.test(v)) {
            hits.push({ selector: rule.selectorText, prop, value: v, want: 'em' });
          } else if (/(^|\s|\()(-?\d*\.?\d+)px/.test(v) && !/^0px$/.test(v.trim())) {
            hits.push({ selector: rule.selectorText, prop, value: v, want: 'rem' });
          }
        }
      });
    });

    return hits.length
      ? no(6, { count: hits.length, sample: hits.slice(0, 25) })
      : ok(6, 'no stray px outside the background-size exception');
  }

  window.__frostGate = {
    harness, rootFontSize,
    lineEnds, groupLines, wordBoxes, glue,
    containers, legacyAssets, altAudit, unitAudit,
  };
})();
