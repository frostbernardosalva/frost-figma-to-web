#!/usr/bin/env python3
"""
timer.py - how long a page conversion actually took.

Opinion is cheap: "page two felt slower" is worth nothing next to "page two took
1h42m and nine of those minutes were the build". This records the second kind.

    timer.py start "About Us"        open a run (opens the 'prep' phase)
    timer.py mark build              close the current phase, open 'build'
    timer.py pause  /  resume        stop the clock for a break
    timer.py stop --publishes 6      close the run, append it to the ledger
    timer.py status                  what is running, and for how long
    timer.py report                  print the ledger and what it implies
    timer.py html                    write the ledger as a readable HTML page
    timer.py add "Old Page" ...      backfill a run that predates the tracker

The recommended phases, in order, because they are the ones that turned out to
differ by an order of magnitude:

    prep     reading the design frames, writing the prediction
    build    creating the page and its content
    gate     measuring against the frames and fixing what that finds
    row7     the visual pass, whole page, every width
    rework   anything found AFTER the page was reported done

That last one is the point. A run with a fat 'rework' phase is a run whose gate
let something through, and it is the only phase you can drive to zero.

Data lives in <ledger>.json; the markdown and the HTML are regenerated from it
and are views, never the source. Both are rewritten on every stop, add and
report, so neither can become the stale copy. Default location is the working
directory, or set CONVERSION_LEDGER to a path (with or without an extension).
"""

import argparse
import datetime as dt
import html as _html
import json
import os
import sys

PHASES = ["prep", "build", "gate", "row7", "rework"]
FMT = "%Y-%m-%d %H:%M:%S"

# Categorical slots 1-5 of the validated default chart palette, in fixed order -
# the phases are identities, not magnitudes, so the hues never get cycled or
# re-sorted. Checked with the palette validator rather than by eye, in both
# modes: worst adjacent CVD dE 9.1 light / 8.4 dark, worst adjacent
# normal-vision dE 19.6 light / 19.3 dark.
#
# Rework is magenta and NOT red, which was the first choice. Red beside the
# yellow of row7 scores a normal-vision dE of 13.0 on the dark surface - under
# the hard floor of 15, so full-colour readers cannot reliably tell the two
# apart either. Secondary encoding does not excuse that one. The phase worth
# driving to zero is called out in the summary instead.
PHASE_COLOURS = [
    ("prep",   "#2a78d6", "#3987e5"),
    ("build",  "#eb6834", "#d95926"),
    ("gate",   "#1baf7a", "#199e70"),
    ("row7",   "#eda100", "#c98500"),
    ("rework", "#e87ba4", "#d55181"),
]


# ---------------------------------------------------------------- paths / io

def ledger_paths(explicit=None):
    base = explicit or os.environ.get("CONVERSION_LEDGER") or "conversion-times"
    base = os.path.splitext(base)[0]
    return base + ".json", base + ".md"


def load(path):
    if not os.path.exists(path):
        return {"runs": [], "open": None}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path, data):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def now(override=None):
    if override:
        for f in (FMT, "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
            try:
                t = dt.datetime.strptime(override, f)
            except ValueError:
                continue
            if f.startswith("%H"):
                today = dt.date.today()
                t = t.replace(year=today.year, month=today.month, day=today.day)
            return t
        sys.exit(f"timer: could not read the time '{override}'")
    return dt.datetime.now().replace(microsecond=0)


def mins(a, b):
    return round((b - a).total_seconds() / 60.0, 1)


def hm(minutes):
    if minutes is None:
        return "-"
    minutes = int(round(minutes))
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


# ------------------------------------------------------------------ commands

def cmd_start(a, jpath, data):
    if data["open"]:
        sys.exit(
            f"timer: '{data['open']['page']}' is still running. "
            f"Stop it first, or `timer.py mark` to change phase."
        )
    t = now(a.at)
    data["open"] = {
        "page": a.page,
        "pages": a.pages,
        "started": t.strftime(FMT),
        "phases": [{"name": a.phase, "from": t.strftime(FMT)}],
        "paused": [],
    }
    save(jpath, data)
    print(f"started  {a.page}  at {t.strftime('%H:%M')}  (phase: {a.phase})")


def cmd_mark(a, jpath, data):
    run = require_open(data)
    if run.get("paused") and run["paused"][-1].get("to") is None:
        sys.exit("timer: the clock is paused. `timer.py resume` first.")
    t = now(a.at)
    run["phases"][-1]["to"] = t.strftime(FMT)
    prev = run["phases"][-1]
    run["phases"].append({"name": a.phase, "from": t.strftime(FMT)})
    save(jpath, data)
    took = span_minutes(run, dt.datetime.strptime(prev["from"], FMT), t)
    print(f"{prev['name']} took {hm(took)}  ->  now in {a.phase}")


def cmd_pause(a, jpath, data):
    run = require_open(data)
    if run["paused"] and run["paused"][-1].get("to") is None:
        sys.exit("timer: already paused.")
    run["paused"].append({"from": now(a.at).strftime(FMT)})
    save(jpath, data)
    print("paused")


def cmd_resume(a, jpath, data):
    run = require_open(data)
    if not run["paused"] or run["paused"][-1].get("to") is not None:
        sys.exit("timer: not paused.")
    run["paused"][-1]["to"] = now(a.at).strftime(FMT)
    save(jpath, data)
    print("resumed")


def cmd_stop(a, jpath, data):
    run = require_open(data)
    t = now(a.at)
    if run["paused"] and run["paused"][-1].get("to") is None:
        run["paused"][-1]["to"] = t.strftime(FMT)
    run["phases"][-1]["to"] = t.strftime(FMT)
    run["ended"] = t.strftime(FMT)
    run["publishes"] = a.publishes
    run["deviation"] = a.dev
    run["note"] = a.note
    run["source"] = "measured"
    data["runs"].append(run)
    data["open"] = None
    save(jpath, data)
    write_markdown(jpath, data)
    write_html(jpath, data)
    tot, _ = totals(run)
    print(f"stopped  {run['page']}  total {hm(tot)}")
    for w in warnings_for(run):
        print("  ! " + w)


def cmd_add(a, jpath, data):
    start, end = now(a.start), now(a.end)
    phases = []
    marks = [(now(v), k) for k, v in (p.split("=", 1) for p in a.phase or [])]
    marks.sort()
    cursor, name = start, a.first_phase
    for at, nxt in marks:
        phases.append({"name": name, "from": cursor.strftime(FMT), "to": at.strftime(FMT)})
        cursor, name = at, nxt
    phases.append({"name": name, "from": cursor.strftime(FMT), "to": end.strftime(FMT)})
    data["runs"].append({
        "page": a.page, "started": start.strftime(FMT), "ended": end.strftime(FMT),
        "pages": a.pages, "phases": phases, "paused": [], "publishes": a.publishes,
        "deviation": a.dev, "note": a.note, "source": a.source,
    })
    data["runs"].sort(key=lambda r: r["started"])
    save(jpath, data)
    write_markdown(jpath, data)
    write_html(jpath, data)
    print(f"added  {a.page}  ({a.source})")


def cmd_status(a, jpath, data):
    run = data.get("open")
    if not run:
        print("nothing running.")
        if data["runs"]:
            last = data["runs"][-1]
            print(f"last: {last['page']}, {hm(totals(last)[0])}, {last['started'][:10]}")
        return
    t = now()
    cur = run["phases"][-1]
    paused = run["paused"] and run["paused"][-1].get("to") is None
    elapsed = mins(dt.datetime.strptime(run["started"], FMT), t) - paused_minutes(run, t)
    print(f"{run['page']}  {'PAUSED' if paused else 'running'}  {hm(elapsed)} active")
    print(f"  phase {cur['name']}, {hm(mins(dt.datetime.strptime(cur['from'], FMT), t))}")


def cmd_report(a, jpath, data):
    write_markdown(jpath, data)
    write_html(jpath, data)
    print(render(data))


def cmd_html(a, jpath, data):
    """write the ledger as an HTML page"""
    print(write_html(jpath, data))


# ------------------------------------------------------------------- helpers

def require_open(data):
    if not data.get("open"):
        sys.exit("timer: nothing running. `timer.py start \"<page>\"` first.")
    return data["open"]


def paused_minutes(run, upto=None):
    total = 0.0
    for p in run.get("paused", []):
        a = dt.datetime.strptime(p["from"], FMT)
        b = dt.datetime.strptime(p["to"], FMT) if p.get("to") else (upto or a)
        total += mins(a, b)
    return total


def span_minutes(run, a, b):
    """Minutes between a and b with any paused stretches taken out."""
    gap = sum(
        mins(max(a, dt.datetime.strptime(p["from"], FMT)),
             min(b, dt.datetime.strptime(p["to"], FMT)))
        for p in run.get("paused", [])
        if p.get("to")
        and dt.datetime.strptime(p["from"], FMT) < b
        and dt.datetime.strptime(p["to"], FMT) > a
    )
    return round(mins(a, b) - gap, 1)


def totals(run):
    """(active total, {phase: minutes}). Paused time is never charged to a phase."""
    per = {}
    for ph in run["phases"]:
        if not ph.get("to"):
            continue
        a = dt.datetime.strptime(ph["from"], FMT)
        b = dt.datetime.strptime(ph["to"], FMT)
        per[ph["name"]] = round(per.get(ph["name"], 0.0) + span_minutes(run, a, b), 1)
    return round(sum(per.values()), 1), per


def warnings_for(run):
    """Make a skipped step visible. Silence is how these get skipped."""
    out = []
    _, per = totals(run)
    if "row7" not in per:
        out.append("no row7 phase - was the whole page looked at, at every width?")
    if per.get("rework"):
        out.append(f"{hm(per['rework'])} of rework: the gate let something through.")
    if run.get("publishes") is None:
        out.append("publish count not recorded (--publishes N); it is a fixed tax worth tracking.")
    if not run.get("deviation"):
        out.append("no final deviation recorded (--dev); the time means little without the result.")
    return out


def stats(rows):
    """The headline figures, derived once.

    Both views read these, so the table and the page cannot drift apart - the
    way a number quoted in two places eventually does.
    """
    L = sorted(t for _, t, _ in rows)
    med = L[len(L) // 2] if len(L) % 2 else (L[len(L) // 2 - 1] + L[len(L) // 2]) / 2
    # Only runs that actually recorded a build phase can answer this, so the
    # denominator is their totals - not every run's.
    withbuild = [(t, per["build"]) for _, t, per in rows if per.get("build")]
    rw = [per.get("rework", 0) for _, _, per in rows]
    return {
        "n": len(L),
        "median": med,
        "fastest": L[0],
        "slowest": L[-1],
        "build_runs": len(withbuild),
        "build_share": (100.0 * sum(b for _, b in withbuild)
                        / sum(t for t, _ in withbuild)) if withbuild else None,
        "rework_total": round(sum(rw), 1),
        "rework_runs": sum(1 for x in rw if x),
        "reconstructed": sum(1 for r, _, _ in rows if r.get("source") != "measured"),
    }


def render(data):
    runs = data.get("runs", [])
    if not runs:
        return "No conversions recorded yet.\n"
    rows = []
    for r in runs:
        tot, per = totals(r)
        rows.append((r, tot, per))
    w = max(len(r["page"]) for r, _, _ in rows) + 1
    multi = any((r.get("pages") or 1) > 1 for r, _, _ in rows)
    per_col = f" {'/page':>7} " if multi else ""
    out = ["", f"{'Page'.ljust(w)} {'Date':<11} {'Total':>7}{per_col}  {'build':>6} {'gate':>6} "
               f"{'row7':>6} {'rework':>7}  {'pub':>4}  worst dev"]
    out.append("-" * (w + 66 + len(per_col)))
    for r, tot, per in rows:
        tag = "" if r.get("source") == "measured" else "  ~"
        n = r.get("pages") or 1
        per_val = f" {hm(tot / n):>7} " if multi else ""
        out.append(
            f"{r['page'].ljust(w)} {r['started'][:10]:<11} {hm(tot):>7}{per_val}  "
            f"{hm(per.get('build')):>6} {hm(per.get('gate')):>6} "
            f"{hm(per.get('row7')):>6} {hm(per.get('rework')):>7}  "
            f"{str(r.get('publishes') or '-'):>4}  {r.get('deviation') or '-'}{tag}"
        )
    out.append("-" * (w + 66 + len(per_col)))
    st = stats(rows)
    out.append(f"{st['n']} conversion{'s' if st['n'] > 1 else ''} · median {hm(st['median'])}"
               f" · fastest {hm(st['fastest'])} · slowest {hm(st['slowest'])}")
    if st["build_share"] is not None:
        n = st["build_runs"]
        out.append(f"across the {n} run{'s' if n > 1 else ''} with a build phase, building was "
                   f"{st['build_share']:.0f}% of the time; the rest was proving it right.")
    if st["rework_runs"]:
        out.append(f"rework on {st['rework_runs']} of {st['n']}: {hm(st['rework_total'])}"
                   f" total - the phase to drive to zero.")
    if st["reconstructed"]:
        out.append("~ = reconstructed after the fact, not timed live.")
    out.append("")
    return "\n".join(out)


def write_markdown(jpath, data):
    _, mpath = ledger_paths(os.path.splitext(jpath)[0])
    body = render(data)
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write("# Conversion times\n\n")
        fh.write("How long each page actually took, written by `bin/timer.py`. **This file is a\n"
                 "view** - the data is in the `.json` beside it, and editing this by hand will be\n"
                 "overwritten on the next `timer.py report`.\n\n")
        fh.write("Phases: `prep` (read the frames, write the prediction) · `build` (create the page\n"
                 "and its content) · `gate` (measure against the frames, fix what that finds) ·\n"
                 "`row7` (the visual pass, whole page, every width) · `rework` (found *after* the\n"
                 "page was called done).\n\n")
        fh.write("```\n" + body.strip("\n") + "\n```\n")
        notes = [r for r in data.get("runs", []) if r.get("note")]
        if notes:
            fh.write("\n## Notes\n\n")
            for r in notes:
                fh.write(f"- **{r['page']}** ({r['started'][:10]}) — {r['note']}\n")
    return mpath


CSS = """
*{box-sizing:border-box}
:root{
  color-scheme:light;
  --surface:#fcfcfb; --raised:#ffffff; --ink:#1a1a19; --ink-2:#55544e; --ink-3:#86857c;
  --line:#e6e5df; --line-2:#f0efe9;
  --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100; --c5:#e87ba4;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --surface:#1a1a19; --raised:#232321; --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#8a8980;
    --line:#35342f; --line-2:#2a2a27;
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --surface:#1a1a19; --raised:#232321; --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#8a8980;
  --line:#35342f; --line-2:#2a2a27;
  --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181;
}
body{
  margin:0; background:var(--surface); color:var(--ink);
  font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1060px;margin:0 auto;padding:40px 16px 72px}
h1{font-size:26px;line-height:1.2;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:15px;margin:40px 0 12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);font-weight:600}
.sub{color:var(--ink-2);margin:0 0 4px;max-width:70ch}
.sub code{background:var(--line-2);padding:1px 5px;border-radius:4px;font-size:13px}
.banner{margin:20px 0 0;padding:10px 14px;border:1px solid var(--line);border-left:3px solid var(--c4);
  border-radius:6px;background:var(--raised);color:var(--ink-2);font-size:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(142px,1fr));gap:10px;margin-top:26px}
.tile{background:var(--raised);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.tile .n{font-size:25px;font-weight:650;letter-spacing:-.02em;line-height:1.1}
.tile .k{font-size:12px;color:var(--ink-3);margin-top:3px}
.tile .k b{color:var(--ink-2);font-weight:600}
.bar-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 18px}
.seg-btn{font:inherit;font-size:13px;padding:5px 12px;border:1px solid var(--line);background:var(--raised);
  color:var(--ink-2);border-radius:999px;cursor:pointer}
.seg-btn[aria-pressed="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.hint{color:var(--ink-3);font-size:13px}
.chart{display:flex;flex-direction:column;gap:14px}
.row-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;margin-bottom:5px}
.row-name{font-weight:600;font-size:14px}
.row-meta{color:var(--ink-3);font-size:12px;white-space:nowrap}
.track{display:flex;align-items:center;gap:10px}
.bar{display:flex;gap:2px;height:26px;flex:1;min-width:0}
.seg{display:block;height:100%;width:var(--t);min-width:3px;border-radius:2px;cursor:default;
  transition:width .18s ease}
.bar .seg:first-child{border-radius:4px 2px 2px 4px}
.bar .seg:last-child{border-radius:2px 4px 4px 2px}
body[data-view="page"] .seg{width:var(--p)}
.tot{font-variant-numeric:tabular-nums;font-size:13px;font-weight:600;white-space:nowrap;min-width:62px;text-align:right}
.tot b{font-weight:600}
.v-page{display:none}
body[data-view="page"] .v-total{display:none}
body[data-view="page"] .v-page{display:inline}
.recon{color:var(--ink-3);font-weight:400}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:18px;font-size:13px;color:var(--ink-2)}
.legend span{display:flex;align-items:center;gap:6px}
.sw{width:11px;height:11px;border-radius:3px;flex:none}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:4px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line-2);vertical-align:top}
th{color:var(--ink-3);font-weight:600;font-size:12px;letter-spacing:.03em;border-bottom-color:var(--line)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.date{white-space:nowrap;color:var(--ink-2)}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);color:var(--ink-3)}
.tag.warn{border-color:var(--c4);color:var(--c4)}
.dev{color:var(--ink-2);font-size:12px}
.notes li{margin-bottom:10px;color:var(--ink-2)}
.notes b{color:var(--ink)}
.caveat{background:var(--raised);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin-top:4px}
.caveat p{margin:0 0 10px;color:var(--ink-2)}
.caveat p:last-child{margin-bottom:0}
.caveat b{color:var(--ink)}
#tip{position:fixed;pointer-events:none;opacity:0;transition:opacity .1s;background:var(--ink);color:var(--surface);
  font-size:12px;padding:6px 9px;border-radius:6px;white-space:nowrap;z-index:9;transform:translate(-50%,-140%)}
#tip.on{opacity:1}
@media (max-width:620px){
  .wrap{padding:28px 16px 56px}
  .row-meta{display:none}
  .track{flex-wrap:wrap}
  .tot{min-width:0}
  table{display:block;overflow-x:auto;white-space:nowrap}
}
"""

JS = """
(function(){
  var b=document.body, tip=document.getElementById('tip');
  document.querySelectorAll('.seg-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      b.setAttribute('data-view',btn.dataset.view);
      document.querySelectorAll('.seg-btn').forEach(function(o){
        o.setAttribute('aria-pressed', String(o===btn));
      });
    });
  });
  document.addEventListener('mouseover',function(e){
    var s=e.target.closest('.seg'); if(!s) return;
    tip.textContent=s.dataset.l; tip.classList.add('on');
  });
  document.addEventListener('mousemove',function(e){
    if(tip.classList.contains('on')){ tip.style.left=e.clientX+'px'; tip.style.top=e.clientY+'px'; }
  });
  document.addEventListener('mouseout',function(e){
    if(e.target.closest('.seg')) tip.classList.remove('on');
  });
})();
"""


def write_html(jpath, data):
    """The same ledger, as a page you can read without counting columns.

    A view like the markdown: regenerated from the json on every stop, add and
    report, so it cannot become the stale copy.
    """
    hpath = os.path.splitext(jpath)[0] + ".html"
    runs = data.get("runs", [])
    rows = [(r,) + totals(r) for r in runs]
    colour = {n: i + 1 for i, (n, _, _) in enumerate(PHASE_COLOURS)}

    o = ['<!doctype html>', '<html lang="en">', '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Conversion times</title>', '<style>' + CSS + '</style>',
         '<body data-view="total"><div id="tip"></div><div class="wrap">',
         '<h1>Conversion times</h1>',
         '<p class="sub">How long each page actually took. Regenerated by '
         '<code>bin/timer.py</code> from the ledger beside it &mdash; this page is a view, '
         'never the source, so editing it by hand is overwritten on the next run.</p>']

    # The banner comes before the empty check on purpose: the very first run on a
    # new ledger is open with nothing finished behind it, and that is exactly when
    # "nothing recorded yet" on its own would be misleading.
    op = data.get("open")
    if op:
        o.append('<p class="banner"><b>%s</b> is running right now, so it is not in the '
                 'figures below.</p>' % _esc(op.get("page", "a run")))

    if not rows:
        o.append('<p class="sub" style="margin-top:24px">No finished conversions recorded yet.</p>'
                 '</div></body></html>')
        with open(hpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(o) + "\n")
        return hpath

    st = stats(rows)
    multi = any((r.get("pages") or 1) > 1 for r, _, _ in rows)

    # ---- the headline numbers
    tiles = [(str(st["n"]), "runs recorded"),
             (hm(st["median"]), "median"),
             (hm(st["fastest"]), "fastest"),
             (hm(st["slowest"]), "slowest")]
    if st["build_share"] is not None:
        tiles.append(("%.0f%%" % st["build_share"],
                      "was <b>building</b>, across the %d with a build phase. The rest was "
                      "proving it right" % st["build_runs"]))
    if st["rework_runs"]:
        tiles.append((hm(st["rework_total"]),
                      "of <b>rework</b>, on %d of %d &mdash; the phase to drive to zero"
                      % (st["rework_runs"], st["n"])))
    o.append('<div class="tiles">')
    for n, k in tiles:
        o.append('<div class="tile"><div class="n">%s</div><div class="k">%s</div></div>' % (n, k))
    o.append('</div>')

    # ---- the chart
    scale_t = max(t for _, t, _ in rows) or 1
    scale_p = max(t / (r.get("pages") or 1) for r, t, _ in rows) or 1
    o.append('<h2>Where the time went</h2>')
    o.append('<div class="bar-controls">'
             '<button class="seg-btn" data-view="total" aria-pressed="true">Total</button>'
             '<button class="seg-btn" data-view="page" aria-pressed="false">Per page</button>')
    if multi:
        o.append('<span class="hint">&mdash; one run covers more than one page, so raw '
                 'totals are not a ranking</span>')
    o.append('</div><div class="chart">')

    for r, tot, per in rows:
        n = r.get("pages") or 1
        recon = r.get("source") != "measured"
        o.append('<div><div class="row-head"><span class="row-name">%s%s</span>'
                 '<span class="row-meta">%s &middot; %s</span></div><div class="track"><div class="bar">'
                 % (_esc(r["page"]),
                    ' <span class="tag">reconstructed</span>' if recon else '',
                    _esc(r["started"][:10]),
                    "%d pages" % n if n > 1 else "1 page"))
        for name, _, _ in PHASE_COLOURS:
            v = per.get(name)
            if not v:
                continue
            o.append('<i class="seg" style="--t:%.2f%%;--p:%.2f%%;background:var(--c%d)" '
                     'data-l="%s &middot; %s &middot; %.0f%% of the run"></i>'
                     % (100.0 * v / scale_t, 100.0 * (v / n) / scale_p, colour[name],
                        name, hm(v), 100.0 * v / tot if tot else 0))
        o.append('</div><span class="tot"><b class="v-total">%s</b>'
                 '<b class="v-page">%s</b>%s</span></div></div>'
                 % (hm(tot), hm(tot / n),
                    ' <span class="recon">~</span>' if recon else ''))
    o.append('</div><div class="legend">')
    for i, (name, _, _) in enumerate(PHASE_COLOURS, 1):
        o.append('<span><i class="sw" style="background:var(--c%d)"></i>%s</span>' % (i, name))
    o.append('</div>')

    # ---- every number, which is also the table view the chart owes
    o.append('<h2>Every run</h2><table><thead><tr><th>Page</th><th>Date</th>'
             '<th class="n">Total</th>')
    if multi:
        o.append('<th class="n">/page</th>')
    o.append('<th class="n">prep</th><th class="n">build</th><th class="n">gate</th>'
             '<th class="n">row7</th><th class="n">rework</th><th class="n">pub</th>'
             '<th>Worst deviation</th></tr></thead><tbody>')
    for r, tot, per in rows:
        n = r.get("pages") or 1
        o.append('<tr><td>%s%s</td><td class="date">%s</td><td class="n"><b>%s</b></td>'
                 % (_esc(r["page"]),
                    ' <span class="tag">~</span>' if r.get("source") != "measured" else '',
                    _esc(r["started"][:10]), hm(tot)))
        if multi:
            o.append('<td class="n">%s</td>' % hm(tot / n))
        for name, _, _ in PHASE_COLOURS:
            o.append('<td class="n">%s</td>' % hm(per.get(name)))
        o.append('<td class="n">%s</td><td class="dev">%s</td></tr>'
                 % (r.get("publishes") or "&ndash;",
                    _esc(r["deviation"]) if r.get("deviation") else "&ndash;"))
        warn = warnings_for(r)
        if warn:
            o.append('<tr><td colspan="%d" style="padding-top:0;border-bottom:1px solid var(--line-2)">'
                     % (11 if multi else 10))
            for wmsg in warn:
                o.append('<span class="tag warn">%s</span> ' % _esc(wmsg))
            o.append('</td></tr>')
    o.append('</tbody></table>')

    notes = [r for r, _, _ in rows if r.get("note")]
    if notes:
        o.append('<h2>What each run was</h2><ul class="notes">')
        for r in notes:
            o.append('<li><b>%s</b> &mdash; %s</li>' % (_esc(r["page"]), _esc(r["note"])))
        o.append('</ul>')

    o.append('<h2>How to read this</h2><div class="caveat">')
    if st["reconstructed"]:
        o.append('<p><b>%d of these were reconstructed</b>, not timed live &mdash; their phase '
                 'boundaries were inferred from artefact timestamps afterwards. They are marked '
                 'and they are weaker evidence than the rest.</p>' % st["reconstructed"])
    o.append('<p><b>Do not quote the build figure as the page figure.</b> Building is the '
             'minority of every run here; the rest is proving it right, and that part scales '
             'with how much content the page has.</p>')
    o.append('<p><b>Pages are not the same size, so raw minutes are not a league table.</b> '
             'A long content page and a short form page cost different amounts for reasons that '
             'have nothing to do with how well either went. Compare the shape of the bar &mdash; '
             'how much was gate and rework &mdash; before comparing its length.</p>')
    o.append('<p>Phases: <b>prep</b> read the frames and write the prediction &middot; '
             '<b>build</b> create the page and its content &middot; <b>gate</b> measure against '
             'the frames and fix what that finds &middot; <b>row7</b> the visual pass, whole '
             'page, every width &middot; <b>rework</b> anything found <i>after</i> the page was '
             'called done.</p></div>')

    o.append('</div><script>' + JS + '</script></body></html>')
    with open(hpath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o) + "\n")
    return hpath


def _esc(s):
    return _html.escape(str(s), quote=True)


# ---------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(prog="timer.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger", help="ledger path (default $CONVERSION_LEDGER or ./conversion-times)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="open a run")
    s.add_argument("page")
    s.add_argument("--phase", default="prep", help=f"opening phase (default prep; usual: {', '.join(PHASES)})")
    s.add_argument("--pages", type=int, default=1,
                   help="how many pages this run covers - >1 for a parallel run, so the report can divide")
    s.add_argument("--at", help="override the time, e.g. 14:05")
    s.set_defaults(fn=cmd_start)

    s = sub.add_parser("mark", help="close the current phase and open another")
    s.add_argument("phase")
    s.add_argument("--at")
    s.set_defaults(fn=cmd_mark)

    for name, fn in (("pause", cmd_pause), ("resume", cmd_resume)):
        s = sub.add_parser(name, help=f"{name} the clock")
        s.add_argument("--at")
        s.set_defaults(fn=fn)

    s = sub.add_parser("stop", help="close the run and append it to the ledger")
    s.add_argument("--at")
    s.add_argument("--publishes", type=int, help="how many publish+verify cycles it cost")
    s.add_argument("--dev", help='final deviation, e.g. "1440:+0.26%%, 980:+1.35%%"')
    s.add_argument("--note")
    s.set_defaults(fn=cmd_stop)

    s = sub.add_parser("add", help="backfill a run that predates the tracker")
    s.add_argument("page")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--phase", action="append",
                   help="phase boundary as NAME=TIME, repeatable; NAME is the phase STARTING then")
    s.add_argument("--first-phase", default="prep")
    s.add_argument("--publishes", type=int)
    s.add_argument("--dev")
    s.add_argument("--note")
    s.add_argument("--pages", type=int, default=1)
    s.add_argument("--source", default="reconstructed", choices=["measured", "reconstructed"])
    s.set_defaults(fn=cmd_add)

    for name, fn in (("status", cmd_status), ("report", cmd_report), ("html", cmd_html)):
        s = sub.add_parser(name, help=fn.__doc__ or name)
        s.set_defaults(fn=fn)

    a = p.parse_args()
    jpath, _ = ledger_paths(a.ledger)
    a.fn(a, jpath, load(jpath))


if __name__ == "__main__":
    main()
