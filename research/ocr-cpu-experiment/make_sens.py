#!/usr/bin/env python3
"""Sensitivity copy of the 220-screenshot folder: wrong-language screens, one deleted file. Writes fixtures/sens/ and prints the cases."""
import shutil, sys
from pathlib import Path
base, sens = Path(sys.argv[1]), Path(sys.argv[2])
shutil.rmtree(sens, ignore_errors=True); shutil.copytree(base, sens)
# (target folder, file, source folder): the file in the target folder is replaced by the same-named screenshot of the source language
swaps = [("de-DE", "iphone-69-01-jobs-list.png", "en-US"), ("de-DE", "iphone-69-03-saved-pipeline.png", "en-US"),
         ("de-DE", "ipad-13-02-fit-trust.png", "en-US"),                      # English in the German folder (3 screens)
         ("uk", "iphone-69-02-fit-trust.png", "ru"), ("uk", "iphone-69-05-weekly-briefing.png", "ru"),  # Russian in the Ukrainian folder
         ("fr-FR", "iphone-69-03-saved-pipeline.png", "ru"),                  # Russian in the French folder (other script entirely)
         ("nl-NL", "iphone-69-04-application-tracker.png", "de-DE"),          # German in the Dutch folder (close Latin pair)
         ("ja", "iphone-69-05-weekly-briefing.png", "zh-Hans"),               # Chinese in the Japanese folder
         ("ko", "iphone-69-02-fit-trust.png", "ja"),                          # Japanese in the Korean folder
         ("hi", "iphone-69-06-paywall.png", "en-US")]                         # English in the Hindi folder
for t, f, s in swaps:
    shutil.copy(base / s / f, sens / t / f); print(f"swap  {t}/{f}  <-  {s}")
(sens / "ja" / "iphone-69-04-application-tracker.png").unlink(); print("delete ja/iphone-69-04-application-tracker.png")
