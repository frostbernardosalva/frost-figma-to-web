/**
 * The expected result of running gate.js against gate-fixture.html.
 *
 * This is the regression test. Every expectation below is a defect that shipped
 * on a real build, and is the reason the matching probe exists. Run it with:
 *
 *     python bin/fixtures/run.py
 *
 * which drives headless Chrome and exits non-zero on any failure.
 *
 * Each check takes a FUNCTION, not a value, so that a probe returning an
 * unexpected shape becomes one failed check with its stack — not a dead page
 * with no output. The first version of this file threw on
 * `glue.detail.glued[0]` and produced absolutely nothing, which is the worst
 * possible behaviour for a test harness.
 */
(function () {
  'use strict';

  function emit(out) {
    const pre = document.createElement('pre');
    pre.id = 'gate-results';
    pre.textContent = JSON.stringify(out, null, 2);
    document.body.appendChild(pre);
  }

  const G = window.__frostGate;
  if (!G) {
    emit({ failures: 1, total: 1, results: [{
      name: 'gate.js loaded', pass: false, actual: 'window.__frostGate is undefined',
      expected: 'the probe object', note: 'bin/gate.js did not load or threw while evaluating',
    }] });
    return;
  }

  const results = [];
  let failures = 0;

  function check(name, fn, expected, note) {
    let actual, pass;
    try {
      actual = fn();
      pass = JSON.stringify(actual) === JSON.stringify(expected);
    } catch (e) {
      actual = 'THREW: ' + e.message;
      pass = false;
    }
    if (!pass) failures++;
    results.push({ name, pass, actual, expected, note: pass ? undefined : note });
  }

  // -------------------------------------------------------------------------
  // THE ONE THIS FILE EXISTS FOR
  //
  // A probe that groups words by rect `top` starts a new line wherever glyph
  // boxes on the SAME line sit at different tops — at a size change always, at
  // a weight change on families whose weights differ in metrics. It then
  // reports a word as orphaned that is not. That is what shipped, and what
  // cost time on the Frost headline.
  // -------------------------------------------------------------------------

  // Both expectations below were read off a RENDER, not off a probe. That
  // distinction is the whole lesson: the original defect was diagnosed from a
  // probe's output and chased in the wrong direction until a screenshot showed
  // two lines where the probe insisted on three.
  check('lineEnds: mixed font-weight matches the render',
        () => G.lineEnds(document.getElementById('mixed-weight')).detail.text,
        ['Frost has worked', 'with industry', 'titans.'],
        'does not match what the page actually draws');

  check('lineEnds: mixed font-size matches the render',
        () => G.lineEnds(document.getElementById('mixed-size')).detail.text,
        ['We are a design', 'agency built for', 'scale.'],
        'grouping regressed to `top` — a size change is being read as a line break');

  // Prove the fixture still reproduces the bug. If the OLD grouping stops
  // over-splitting, the two checks above are no longer proving anything.
  const oldGrouping = (el) => {
    const lines = [];
    let top = null;
    for (const b of G.wordBoxes(el)) {
      const t = Math.round(b.top);
      if (t !== top) { lines.push([]); top = t; }
      lines[lines.length - 1].push(b.word);
    }
    return lines.map((l) => l.join(' '));
  };
  // #mixed-size is the load-bearing case. A size change ALWAYS moves the rect
  // top, so old grouping splits "We are" from "a design" and reports 4 lines
  // where the page draws 3.
  //
  // #mixed-weight does NOT reproduce it here: Georgia's 400 and 700 share a
  // rect top at 40px, so old and new agree. Weight only triggers the bug on
  // families whose weights carry different metrics — Sailec, on the Frost
  // build, did. Keep both cases; only assert the discriminator on the one that
  // is guaranteed.
  check('fixture still reproduces the bug: old `top` grouping over-splits',
        () => [oldGrouping(document.getElementById('mixed-size')).length,
               G.lineEnds(document.getElementById('mixed-size')).detail.text.length],
        [4, 3],
        'the fixture no longer triggers the bug — the checks above prove nothing now');

  // -------------------------------------------------------------------------
  // glue: flags the empty hidden marker, leaves the correctly-wrapped one alone
  // -------------------------------------------------------------------------

  check('glue: finds exactly one glued marker',
        () => (G.glue(document).detail.glued || []).length, 1,
        'either the empty-marker defect is missed, or the wrapped span is a false positive');

  check('glue: does NOT flag unclassed visible <br> (the footer-address false positive)',
        () => (G.glue(document).detail.glued || []).some((g) => /ADB Ave|Garnet|Pasig/.test(g.glued)),
        false,
        'a visible <br> always renders its break and cannot glue anything');

  check('glue: flags a responsive break built on <br>, separately from glue',
        () => (G.glue(document).detail.classedBr || []), ['fr_brk-sm'],
        'Webflow strips classes off <br>, so a classed <br> fires at every width');

  check('glue: names the right join',
        () => (G.glue(document).detail.glued || [{}])[0].glued,
        'e are crafting|end-to-end exp',   // 14 chars each side, per glue()
        'the wrong marker was flagged');

  // -------------------------------------------------------------------------
  // altAudit / legacyAssets / containers / unitAudit
  // -------------------------------------------------------------------------

  check('altAudit: one image missing alt entirely',
        () => G.altAudit(document).detail.missing.length, 1);

  check('altAudit: counts described and decorative separately',
        () => [G.altAudit(document).detail.described, G.altAudit(document).detail.decorative],
        [2, 1],   // img-described + img-broken carry alt; img-decorative is empty
        'an explicitly-empty alt must count as decorative, not as missing');

  check('legacyAssets: finds the unconverted .png in CSS',
        () => G.legacyAssets(document).detail.hits.some((h) => /never-converted\.png/.test(h.url)),
        true,
        'the regex must match url("x.png") — quote and paren, not end-of-string');

  check('legacyAssets: flags an image that finished loading with no pixels',
        () => G.legacyAssets(document).detail.hits.some(
          (h) => h.where === '<img> BROKEN' && /does-not-exist\.svg/.test(h.url)),
        true,
        'a completed load with naturalWidth 0 is genuinely broken');

  check('containers: fails on three containers with two widths',
        () => G.containers(document, '.probe-container').status, 'fail');

  check('containers: reports both distinct widths',
        () => G.containers(document, '.probe-container').detail.distinct.slice().sort((a, b) => a - b),
        [560, 600]);

  check('unitAudit: flags padding px and letter-spacing px',
        () => {
          const props = G.unitAudit(document).detail.sample.map((h) => h.prop);
          // `padding: 24px` reaches the CSSOM as four longhands, never as the
          // shorthand, so assert on what the browser actually exposes.
          return props.includes('letter-spacing') && props.includes('padding-top');
        }, true);

  check('unitAudit: does NOT flag background-size, 0px, rem or em',
        () => G.unitAudit(document).detail.sample.some(
          (h) => h.prop === 'background-size' || h.value.trim() === '0px' ||
                 /\d(rem|em)\b/.test(h.value)),
        false,
        'the documented exceptions are being reported as failures');

  emit({ failures, total: results.length, results });
})();
