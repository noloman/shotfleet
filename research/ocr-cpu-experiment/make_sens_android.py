#!/usr/bin/env python3
"""Android sensitivity copy: wrong-language screens incl. Arabic. make_sens_android.py <clean folder> <out folder>"""
import shutil, sys
from pathlib import Path
base, sens = Path(sys.argv[1]), Path(sys.argv[2])
shutil.rmtree(sens, ignore_errors=True); shutil.copytree(base, sens)
for t, f, s in [("de", "02_log.png", "ar"), ("ar", "03_progress.png", "en"), ("ru", "01_train.png", "pl"), ("ja", "01_train.png", "zh-CN"),
                ("ko", "02_log.png", "ja"), ("hi", "04_profile.png", "en"), ("fr", "03_progress.png", "ru"), ("ar", "04_profile.png", "de")]:
    shutil.copy(base / s / f, sens / t / f); print(f"swap  {t}/{f}  <-  {s}")
