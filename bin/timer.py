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

Data lives in <ledger>.json; the markdown is regenerated from it and is a view,
never the source. Default location is the working directory, or set
CONVERSION_LEDGER to a path (with or without an extension).
"""

import argparse
import datetime as dt
import json
import os
import sys

PHASES = ["prep", "build", "gate", "row7", "rework"]
FMT = "%Y-%m-%d %H:%M:%S"


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
    print(render(data))


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


def render(data):
    runs = data.get("runs", [])
    if not runs:
        return "No conversions recorded yet.\n"
    rows, L = [], []
    for r in runs:
        tot, per = totals(r)
        rows.append((r, tot, per))
        L.append(tot)
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
    L.sort()
    med = L[len(L) // 2] if len(L) % 2 else (L[len(L) // 2 - 1] + L[len(L) // 2]) / 2
    out.append(f"{len(L)} conversion{'s' if len(L) > 1 else ''} · median {hm(med)} · fastest {hm(L[0])} · slowest {hm(L[-1])}")

    # Only runs that actually recorded a build phase can answer this, so the
    # denominator is their totals - not every run's.
    withbuild = [(tot, per["build"]) for _, tot, per in rows if per.get("build")]
    if withbuild:
        share = 100.0 * sum(b for _, b in withbuild) / sum(t for t, _ in withbuild)
        n = len(withbuild)
        out.append(f"across the {n} run{'s' if n > 1 else ''} with a build phase, building was "
                   f"{share:.0f}% of the time; the rest was proving it right.")
    rw = [per.get("rework", 0) for _, _, per in rows]
    if any(rw):
        n = sum(1 for x in rw if x)
        out.append(f"rework on {n} of {len(rw)}: {hm(sum(rw))} total - the phase to drive to zero.")
    if any(r.get("source") != "measured" for r, _, _ in rows):
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

    for name, fn in (("status", cmd_status), ("report", cmd_report)):
        s = sub.add_parser(name, help=fn.__doc__ or name)
        s.set_defaults(fn=fn)

    a = p.parse_args()
    jpath, _ = ledger_paths(a.ledger)
    a.fn(a, jpath, load(jpath))


if __name__ == "__main__":
    main()
