#!/usr/bin/env python3
"""helper_smoke.py <compiled proposed ocr helper> <png>: the helper's modes and exit codes, one run each (needs macOS)."""
import json, subprocess, sys, time

exe, png = sys.argv[1:3]
for args in (["--langs"], ["--rev2", "--langs"], [png], ["--rev2", png], ["/nonexistent.png"], ["--rev2", "/nonexistent.png"], []):
    t0 = time.time()
    r = subprocess.run([exe, *args], capture_output=True, text=True, timeout=240)
    out = r.stdout.strip()
    try:
        d = json.loads(out); out = f"lang={d.get('lang')} chars={d.get('chars')} reader={d.get('reader')}" if isinstance(d, dict) else f"{len(d)} languages"
    except ValueError:
        pass
    print(f"{' '.join(a if not a.endswith('.png') else '<png>' for a in args) or '(no args)':24} exit={r.returncode} {time.time() - t0:5.1f}s {out[:60]!r} stderr={r.stderr.strip()[:90]!r}")
