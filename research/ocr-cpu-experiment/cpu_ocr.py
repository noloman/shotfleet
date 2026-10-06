#!/usr/bin/env python3
"""CPU-only text reader for the shotfleet --ocr-command contract: `cpu_ocr.py <image> <lang>` prints one line per text box.
PP-OCRv5 mobile models through RapidOCR + ONNX Runtime (CPU provider only; use_coreml is false in RapidOCR's config).
Env: CPU_OCR_THREADS (ORT threads, default 1), CPU_OCR_MAXSIDE (longer side cap, default 2000), CPU_OCR_REC (force a recogniser name),
CPU_OCR_MODELS (model folder), CPU_OCR_V6=1 (PP-OCRv6 small for the Latin path).
`cpu_ocr.py --batch <list.tsv> <out.jsonl>` reads 'path<TAB>lang' lines, loads each model once, writes {path, lang, lines, secs}."""
import json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LATIN = "en de fr es it pt nl sv da no nb fi pl cs ro tr id ms vi ca hr hu sk sl in".split()
REC = {**{l: "latin" for l in LATIN}, "ru": "eslav", "uk": "eslav", "ko": "korean", "hi": "devanagari",
       "mr": "devanagari", "ja": "ch", "zh": "ch", "th": "th", "ar": "arabic", "el": "el"}
_engines = {}

def engine(rec):
    if rec not in _engines:
        from rapidocr import RapidOCR, LangRec, LangDet, OCRVersion, ModelType
        n = int(os.environ.get("CPU_OCR_THREADS", "1"))
        v6 = os.environ.get("CPU_OCR_V6") == "1" and rec == "latin"
        ver, mt = (OCRVersion.PPOCRV6, ModelType.SMALL) if v6 else (OCRVersion.PPOCRV5, ModelType.MOBILE)
        _engines[rec] = RapidOCR(params={
            "Global.model_root_dir": os.environ.get("CPU_OCR_MODELS", str(HERE / "models")), "Global.use_cls": False,
            "Global.max_side_len": int(os.environ.get("CPU_OCR_MAXSIDE", "2000")), "Global.log_level": "warning",
            "EngineConfig.onnxruntime.intra_op_num_threads": n, "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "Det.ocr_version": ver, "Det.lang_type": LangDet.CH, "Det.model_type": mt,
            "Rec.ocr_version": ver, "Rec.lang_type": LangRec("ch" if v6 else rec), "Rec.model_type": mt})
    return _engines[rec]

def read(path, lang):
    """One text line per box RapidOCR detected, top to bottom (judge_screen compares sets of lines, so order is for people only)."""
    lang = lang.split("-")[0].lower()
    rec = os.environ.get("CPU_OCR_REC") or REC.get(lang, "latin")
    out = engine(rec)(str(path))
    if not len(out): return []
    return [t for _, _, t in sorted((b[:, 1].mean(), b[:, 0].min(), t) for b, t in zip(out.boxes, out.txts))]

if __name__ == "__main__":
    if sys.argv[1] == "--batch":
        with open(sys.argv[3], "a") as f:
            for l in Path(sys.argv[2]).read_text().splitlines():
                p, lang = l.split("\t"); t = time.time()
                f.write(json.dumps({"path": p, "lang": lang, "lines": read(p, lang), "secs": round(time.time() - t, 2)}, ensure_ascii=False) + "\n"); f.flush()
    else:
        print("\n".join(read(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "en")))
