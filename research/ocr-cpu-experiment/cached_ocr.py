#!/usr/bin/env python3
"""--ocr-command wrapper: `cached_ocr.py <image> <lang>` = cpu_ocr.read(), but answers from a cache keyed by (image sha256, recogniser, settings)
so the same screenshot under a different folder name is not read twice. CPU_OCR_CACHE = cache folder (default ./cache). A miss reads for real."""
import hashlib, json, os, sys
from pathlib import Path
import cpu_ocr

def key(path, lang):
    lang = lang.split("-")[0].lower()
    rec = os.environ.get("CPU_OCR_REC") or cpu_ocr.REC.get(lang, "latin")
    tag = "v6" if os.environ.get("CPU_OCR_V6") == "1" and rec == "latin" else "v5"
    return f"{hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]}_{tag}_{rec}_{os.environ.get('CPU_OCR_MAXSIDE', '2000')}"

if __name__ == "__main__":
    f = Path(os.environ.get("CPU_OCR_CACHE", "cache")) / (key(sys.argv[1], sys.argv[2]) + ".json")
    if f.exists(): lines = json.loads(f.read_text())
    else:
        lines = cpu_ocr.read(sys.argv[1], sys.argv[2]); f.parent.mkdir(exist_ok=True); f.write_text(json.dumps(lines, ensure_ascii=False))
    print("\n".join(lines))
