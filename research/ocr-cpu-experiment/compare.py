#!/usr/bin/env python3
"""Per-language comparison of a CPU/Tesseract reader against Vision, and verdict agreement from two check.json files.
  compare.py lines  <vision_json_dir> <reader.jsonl> <app>        per-locale: lines found, lines equal after norm(), string hits
  compare.py verdict <vision_check.json> <reader_check.json>      per-script verdict agreement + the disagreeing screenshots"""
import json, hashlib, sys, collections
from pathlib import Path
sys.path.insert(0, "/Users/manu/Developer/shotfleet/.claude/worktrees/silly-faraday-1a606a")
import shotfleet as sf
GROUP = {"Latin": "da de en es fr id it nb nl pl pt ro sv tr".split(), "ar": ["ar"], "Cyrillic": ["ru", "uk"], "ja": ["ja"], "ko": ["ko"], "zh-Hans": ["zh"], "hi": ["hi"]}
def group(label):
    b = label.split("-")[0]
    return next((g for g, ls in GROUP.items() if b in ls), "other")
def lines_of(text): return {n for l in text if len(n := sf.norm(l)) > 1}

def cmd_lines(vdir, jsonl, app):
    tables = sf.string_tables(sf.load_strings_apk(Path(app)) if str(app).endswith('.apk') else sf.load_strings(Path(app))) if app else {}
    per = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0])  # files, vision lines, reader lines, equal, vision hits, reader hits, both-hit-equal
    for l in map(json.loads, Path(jsonl).read_text().splitlines()):
        p = Path(l["path"]); v = json.loads((Path(vdir) / (hashlib.sha256(p.read_bytes()).hexdigest() + ".json")).read_text())
        V, R = lines_of(v["text"].splitlines()), lines_of(l["lines"])
        lp = sf.app_locale(l["lang"], tables) if tables else None; t = tables.get(lp, frozenset())
        r = per[l["lang"]]; r[0] += 1; r[1] += len(V); r[2] += len(R); r[3] += len(V & R); r[4] += len(V & t); r[5] += len(R & t)
    print("| locale | screens | Vision lines | reader lines | equal after norm() | equal / Vision | app-string lines Vision | app-string lines reader |\n|---|---|---|---|---|---|---|---|")
    tot = [0] * 7
    for k, r in sorted(per.items()):
        print(f"| {k} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {100 * r[3] / max(r[1], 1):.0f}% | {r[4]} | {r[5]} |"); tot = [a + b for a, b in zip(tot, r)]
    print(f"| all | {tot[0]} | {tot[1]} | {tot[2]} | {tot[3]} | {100 * tot[3] / max(tot[1], 1):.0f}% | {tot[4]} | {tot[5]} |")
    g = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0])
    for k, r in per.items(): g[group(k)] = [a + b for a, b in zip(g[group(k)], r)]
    print("\n| script | screens | Vision lines | reader lines | equal | equal / Vision | string lines V | string lines R |\n|---|---|---|---|---|---|---|---|")
    for k, r in g.items(): print(f"| {k} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {100 * r[3] / max(r[1], 1):.0f}% | {r[4]} | {r[5]} |")

def verdicts(path):
    d = json.loads(Path(path).read_text()); out = {r["file"]: "ok" if r["lang"] else "unverified" for r in d["screenshots"]}
    for p in d["problems"]:
        if p.startswith("identical image") or "missing" in p.split(":")[1][:10]: continue  # decided by file hashes and names, not by the reader
        elif "/" in p.split(":")[0]: out[p.split(":")[0]] = "problem: " + p.split(":", 1)[1].strip()[:80]
        else: out[p.split(":")[0]] = out.get(p.split(":")[0], "") or "problem: " + p[:80]
    for n in d["notes"]:
        f = n.split(":")[0]
        if f in out and out[f] == "ok" and "could not read" in n: out[f] = "unverified"
    return out, d

def kind(v): return v.split(":")[0]
def cmd_verdict(a, b):
    A, da = verdicts(a); B, db = verdicts(b)
    print(f"problems: A {len(da['problems'])}, B {len(db['problems'])}")
    g = collections.defaultdict(lambda: [0, 0, 0, 0]); bad = []
    for f in sorted(set(A) | set(B)):
        if f not in A or f not in B: bad.append((f, A.get(f, "absent"), B.get(f, "absent"))); continue
        gr = group(f.split("/")[0]); g[gr][0] += 1; same = kind(A[f]) == kind(B[f]); g[gr][1] += same
        g[gr][2] += A[f] == B[f]
        if not same: bad.append((f, A[f], B[f]))
    print("| script | screens | same verdict (ok / unverified / problem) | agreement | identical reason too |\n|---|---|---|---|---|")
    n = s = 0
    for k, r in g.items(): print(f"| {k} | {r[0]} | {r[1]} | {100 * r[1] / r[0]:.0f}% | {r[2]} |"); n += r[0]; s += r[1]
    print(f"| all | {n} | {s} | {100 * s / max(n, 1):.0f}% | |\nDISAGREE:"); [print("  ", *b) for b in bad]
if __name__ == "__main__":
    {"planted": lambda: None, "lines": lambda: cmd_lines(*sys.argv[2:5] if len(sys.argv) > 4 else (*sys.argv[2:4], None)), "verdict": lambda: cmd_verdict(*sys.argv[2:4])}[sys.argv[1]]()

PLANTED = ["de-DE/iphone-69-01-jobs-list.png", "de-DE/iphone-69-03-saved-pipeline.png", "de-DE/ipad-13-02-fit-trust.png", "uk/iphone-69-02-fit-trust.png",
           "uk/iphone-69-05-weekly-briefing.png", "fr-FR/iphone-69-03-saved-pipeline.png", "nl-NL/iphone-69-04-application-tracker.png",
           "ja/iphone-69-05-weekly-briefing.png", "ko/iphone-69-02-fit-trust.png", "hi/iphone-69-06-paywall.png"]
def planted(*paths):
    vs = [verdicts(p)[0] for p in paths]
    print("| planted wrong-language screenshot | " + " | ".join(Path(p).parent.name.replace("report_", "") for p in paths) + " |\n|---|" + "---|" * len(paths))
    caught = [0] * len(paths)
    for f in PLANTED:
        cells = [v.get(f, "ok") for v in vs]; caught = [c + (x.startswith("problem")) for c, x in zip(caught, cells)]
        print(f"| {f} | " + " | ".join(x.replace("problem: ", "FLAGGED: ") for x in cells) + " |")
    print(f"| flagged of {len(PLANTED)} | " + " | ".join(map(str, caught)) + " |")
if __name__ == "__main__" and sys.argv[1] == "planted": planted(*sys.argv[2:])
