#!/usr/bin/env python3
"""Run the repo's `shotfleet check` with a chosen text reader, so every reader is judged by the same check logic.
  run_check.py cmd    <folder> <app> <report> '<ocr-command>'   force the fallback path: --ocr-command reads EVERY screenshot (what check does
                                                                when macOS text recognition is wedged: warm-up fails -> use_vision False)
  run_check.py replay <folder> <app> <report> <vision_json_dir> Vision's own answers (saved per image sha256 by vision_json.py) fed through the
                                                                same code: proves the repo logic gives the binary's verdict
Env NO_OSD=1: drop Tesseract's script detection (tesseract_script) so only the reader under test speaks."""
import json, os, sys, hashlib
from pathlib import Path
sys.path.insert(0, "/Users/manu/Developer/shotfleet/.claude/worktrees/silly-faraday-1a606a")
import shotfleet as sf
mode, folder, app, report, arg = sys.argv[1:6]
sf.ocr_tool = lambda: "/Users/manu/Developer/shotfleet-rc-build/c030-retime/home/Library/Application Support/shotfleet/app/_internal/ocr"
if os.environ.get("NO_OSD") == "1": sf.tesseract_script = lambda png, lp: {}
if mode == "cmd":
    sf.warm_up_ocr = lambda *a, **k: False
    argv = ["check", folder, "--app", app, "--report", report, "--ocr-command", arg]
else:
    sf.warm_up_ocr = lambda *a, **k: True
    sf.read_text = lambda ocr, png, **k: json.loads((Path(arg) / (hashlib.sha256(Path(png).read_bytes()).hexdigest() + ".json")).read_text())
    argv = ["check", folder, "--app", app, "--report", report]
    os.environ["PATH"] = "/usr/bin:/bin"  # no Tesseract: like the baseline
    sf.tesseract_languages.cache_clear() if hasattr(sf.tesseract_languages, "cache_clear") else None
sys.exit(sf.main(argv))
