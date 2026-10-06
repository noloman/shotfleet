#!/usr/bin/env python3
"""One markdown table: per locale, lines found by Vision and by each reader, lines equal after norm(), and the base-run verdict agreement."""
import hashlib, json, sys, collections
from pathlib import Path
sys.argv = sys.argv[:1]
import compare, shotfleet as sf
V = "vision_json"; readers = {"PP-OCRv5": "out/cpu_v5_all.jsonl", "PP-OCRv6 (Latin)": "out/cpu_v6_all.jsonl", "Tesseract psm 6": "out/tess_psm6.jsonl"}
vl = lambda p: compare.lines_of(json.loads((Path(V) / (hashlib.sha256(Path(p).read_bytes()).hexdigest() + ".json")).read_text())["text"].splitlines())
stat = {n: collections.defaultdict(lambda: [0, 0, 0, 0]) for n in readers}  # screens, vision lines, reader lines, equal
for n, f in readers.items():
    for l in map(json.loads, Path(f).read_text().splitlines()):
        v, r = vl(l["path"]), compare.lines_of(l["lines"]); s = stat[n][l["lang"]]
        s[0] += 1; s[1] += len(v); s[2] += len(r); s[3] += len(v & r)
agree = {}
for n, rep in {"PP-OCRv5": "report_cpu_base", "PP-OCRv6 (Latin)": "report_cpu_v6_base", "Tesseract psm 6": "report_tess6_base"}.items():
    A, _ = compare.verdicts("report_vis_base/check.json"); B, _ = compare.verdicts(rep + "/check.json")
    c = collections.defaultdict(lambda: [0, 0])
    for f in A: c[f.split("/")[0]][0] += 1; c[f.split("/")[0]][1] += A[f].split(":")[0] == B[f].split(":")[0]
    agree[n] = c
print("| locale | Vision lines | " + " | ".join(f"{n}: lines / equal / verdict" for n in readers) + " |\n|---|---|---|---|---|")
for loc in sorted(stat["PP-OCRv5"]):
    row = [str(stat["PP-OCRv5"][loc][1])]
    for n in readers:
        s = stat[n].get(loc)
        row.append("n/a" if not s else f"{s[2]} / {s[3]} ({100 * s[3] / s[1]:.0f}%) / {agree[n][loc][1]}/{agree[n][loc][0]}")
    print(f"| {loc} | " + " | ".join(row) + " |")
