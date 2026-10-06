#!/usr/bin/env python3
"""Save Vision's answer (the live 0.1.4 helper `_internal/ocr`) for every png under a folder, by image sha256; prints seconds per image."""
import hashlib, json, subprocess, sys, time
from pathlib import Path
OCR = "/Users/manu/Developer/shotfleet-rc-build/c030-retime/home/Library/Application Support/shotfleet/app/_internal/ocr"
out = Path(sys.argv[2]); out.mkdir(exist_ok=True)
for p in sorted(Path(sys.argv[1]).glob("*/*.png")):
    f = out / (hashlib.sha256(p.read_bytes()).hexdigest() + ".json")
    if f.exists(): continue
    t = time.time(); r = subprocess.run([OCR, str(p)], capture_output=True, text=True, timeout=600)
    if r.returncode: print("FAIL", p, r.stderr[-200:]); continue
    f.write_text(r.stdout); print(p.parent.name, p.name, round(time.time() - t, 2), flush=True)
