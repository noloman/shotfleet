#!/usr/bin/env python3
"""seed_cache.py <batch.jsonl> [cache_dir]: put a batch run's lines into cached_ocr's cache, so check runs reuse them (deterministic reader, same image + model)."""
import json, os, sys
from pathlib import Path
import cached_ocr
d = Path(sys.argv[2] if len(sys.argv) > 2 else "cache"); d.mkdir(exist_ok=True)
for l in map(json.loads, Path(sys.argv[1]).read_text().splitlines()):
    (d / (cached_ocr.key(l["path"], l["lang"]) + ".json")).write_text(json.dumps(l["lines"], ensure_ascii=False))
