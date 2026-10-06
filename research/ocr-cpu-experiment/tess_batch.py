#!/usr/bin/env python3
"""tess_batch.py <list.tsv> <out.jsonl> [psm]: Tesseract (/opt/homebrew/bin/tesseract, tessdata as installed) per image, -l <code> --psm N, same jsonl as cpu_ocr --batch."""
import json, os, subprocess, sys, time
sys.path.insert(0, "/Users/manu/Developer/shotfleet/.claude/worktrees/silly-faraday-1a606a")
import shotfleet as sf
psm = sys.argv[3] if len(sys.argv) > 3 else "6"
with open(sys.argv[2], "a") as f:
    for l in open(sys.argv[1]).read().splitlines():
        p, lang = l.split("\t"); code = sf.tesseract_code(lang); t = time.time()
        r = subprocess.run(["tesseract", p, "stdout", "-l", code, "--psm", psm], capture_output=True, text=True, timeout=600, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        f.write(json.dumps({"path": p, "lang": lang, "lines": [x for x in r.stdout.splitlines() if x.strip()], "secs": round(time.time() - t, 2), "rc": r.returncode}, ensure_ascii=False) + "\n"); f.flush()
