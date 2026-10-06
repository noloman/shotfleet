# CPU-only text reader against macOS Vision: what was measured (2026-10-06)

Branch `claude/ocr-cpu-reader-measure`. Follows section 7 of `research/ocr-cpu-reader-2026-10-06.md` (the candidate: PP-OCRv5 mobile models through RapidOCR and ONNX Runtime on the CPU).
Every number below is **measured** unless the word *inference* is next to it. Load = 1-minute load average on this 10-core Mac, shown wherever a time is given.
Scripts and small result files are in `research/ocr-cpu-experiment/` (paths inside the scripts point at my work folder, `/Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment`).

## 1. Answer

**Conditional GO: build the add-on, but not on the strength of the pass mark alone, because two parts of the pass mark could not be run.**

| Criterion (coordinator and note section 7) | Result |
|---|---|
| Verdict agreement with Vision >= 95% on Latin, Cyrillic, ja, ko, th, ar; hi and mr separate | **Met on every script that has screenshots here**: 100% on the 220 iOS and the 72 Android screenshots (0 problems from both readers); on the planted wrong-language copies, Latin 99% (iOS) and 96% (Android), Cyrillic, ja, ar, hi 100%, ko 100% (iOS) and 75% (Android, 1 of 4). **th: NOT TESTED** (no Thai screenshots exist in this repo's fixtures). **mr: NOT TESTED** (same). |
| Reader answers while a cold Vision compile is running | **Not tested against a long episode.** A short natural episode happened (about 2 minutes, section 6) and the reader was not delayed by it. No 40-minute wedge occurred, and I did not trigger one. |
| Install size and speed per screenshot | Section 7 and 8: 2.4 to 4.5 s per phone screenshot at load 24 to 31; 0.5 to 1.0 GB of memory; 60 MB (33 languages) or 12.7 MB (Latin only) of models, 79 MB compressed for the frozen helper. |

Why it is only conditional:

1. **A base-folder agreement of 100% proves little.** Tesseract also scored 100% on the 220 screenshots, because the check decides a screen from the app's own strings and nearly any reader finds enough of them. The planted wrong-language screens are what separate readers: Vision caught 18 of 18, PP-OCRv5 14 of 18, Tesseract 6 of 18 (section 4).
2. **The 4 misses all have one cause, and it is a design gap, not a model flaw.** The reader picks its model from the expected locale. A Cyrillic, Arabic or Japanese screen filed under a Latin or Korean locale is read by the wrong-script model and comes back as garbage, so the check calls it fine. One test of the obvious fix (also read with the Cyrillic model) turned the French-folder case into 9 Russian string matches against 1 French, which is what Vision reports. A real add-on has to read with a second script model, or classify the script first. That fix is **not built or measured end to end** (inference: it costs one extra read for each screenshot).
3. th, mr and the long ANE test are open (sections 5, 6, 9).

What I would build: PP-OCRv5 for everything, **PP-OCRv6 small for the Latin path** (section 5), and the second-model read above.

## 2. What was run

- **Reader under test:** `cpu_ocr.py` (about 45 lines): RapidOCR 3.9.2, ONNX Runtime 1.20.1 (CPU provider), PP-OCRv5 mobile detector plus the recogniser for the locale (Latin, Eastern Slavic, Korean, Devanagari, Chinese/Japanese, Thai, Arabic), models by explicit path, angle classifier off, one text line per detected box. Prints lines in the form `--ocr-command` expects.
- **How `check` judges it.** Read first: `external_ocr()` runs your command per screenshot and takes its printed lines as the text; `judge_screen()` counts how many lines equal the app's strings of each locale and picks the best. With macOS text recognition working, `--ocr-command` is only used for scripts Vision cannot read, so a CPU reader would never be asked about the iOS set. To judge the CPU reader on **every** screenshot with the same logic, `run_check.py` imports the repo's `shotfleet.py` (origin/main, 3643061) and makes the warm-up report "not answering". That is the state `check` really enters when macOS recognition is stuck: Vision is skipped and `--ocr-command` reads everything. Nothing else in the check was changed.
- **Baseline.** The live 0.1.4 binary on the folder: `checked 220 screenshots in 20 languages: 0 problem(s)`. Cross-check: the repo code fed Vision's saved per-image answers ("replay") gives the identical result on the base folder (0 problems) and on the planted folder (the same 21 problems as the live binary).
- **Corpora.** (a) The 220 iOS screenshots, 20 locales, 11 per locale, from the c030 retime folder (copied, never modified). (b) Android: 72 screenshots in 18 locales including Arabic, from `docker-check/data/clean` with its `app.apk`, because no iOS fixture has Arabic. The iOS set has **no ar, th or mr**.
- **Third reader:** Tesseract 5 from `/opt/homebrew/bin` with the installed data, `-l <code> --psm 6`.
- **Not Vision, not ground truth.** "Lines equal" below means equal to Vision's lines after the repo's `norm()`; Vision is also wrong sometimes.

## 3. Lines, per language (iOS, 220 screenshots)

Format: lines the reader found / lines equal to Vision's after `norm()` (percent of Vision's lines) / screenshots with the same `check` verdict as Vision out of 11. "v6 (Latin)" is PP-OCRv6 small for the 14 Latin locales (other locales use v5 in that run). Measured, no load effect on accuracy.

| locale | Vision lines | PP-OCRv5 | PP-OCRv6 small (Latin) | Tesseract psm 6 |
|---|---|---|---|---|
| de-DE | 356 | 386 / 260 (73%) / 11 | 352 / 283 (79%) / 11 | 223 / 85 (24%) / 11 |
| en-GB | 345 | 373 / 253 (73%) / 11 | 343 / 269 (78%) / 11 | 216 / 84 (24%) / 11 |
| en-US | 342 | 370 / 250 (73%) / 11 | 341 / 267 (78%) / 11 | 215 / 81 (24%) / 11 |
| es-ES | 352 | 387 / 260 (74%) / 11 | 357 / 284 (81%) / 11 | 229 / 83 (24%) / 11 |
| es-MX | 349 | 384 / 258 (74%) / 11 | 352 / 282 (81%) / 11 | 223 / 82 (23%) / 11 |
| fr-FR | 351 | 396 / 258 (74%) / 11 | 356 / 282 (80%) / 11 | 228 / 90 (26%) / 11 |
| id | 316 | 344 / 236 (75%) / 11 | 313 / 250 (79%) / 11 | 197 / 85 (27%) / 11 |
| it | 310 | 339 / 235 (76%) / 11 | 311 / 246 (79%) / 11 | 202 / 71 (23%) / 11 |
| nl-NL | 353 | 374 / 270 (76%) / 11 | 355 / 279 (79%) / 11 | 216 / 82 (23%) / 11 |
| pl | 354 | 386 / 244 (69%) / 11 | 354 / 284 (80%) / 11 | 223 / 84 (24%) / 11 |
| pt-BR | 311 | 334 / 228 (73%) / 11 | 305 / 243 (78%) / 11 | 197 / 79 (25%) / 11 |
| ro | 352 | 380 / 160 (**45%**) / 11 | 345 / 274 (78%) / 11 | 230 / 83 (24%) / 11 |
| sv | 337 | 372 / 255 (76%) / 11 | 342 / 266 (79%) / 11 | 218 / 81 (24%) / 11 |
| tr | 305 | 344 / 144 (**47%**) / 11 | 307 / 216 (71%) / 11 | 188 / 70 (23%) / 11 |
| ru | 320 | 357 / 216 (68%) / 11 | n/a | 206 / 60 (19%) / 11 |
| uk | 359 | 387 / 250 (70%) / 11 | n/a | 222 / 69 (19%) / 11 |
| ja | 341 | 344 / 238 (70%) / 11 | n/a | 192 / 64 (19%) / 11 |
| zh-Hans | 332 | 339 / 226 (68%) / 11 | n/a | 200 / 55 (17%) / 11 |
| ko | 335 | 355 / 137 (**41%**) / 11 | n/a | 222 / 56 (17%) / 11 |
| hi | 312 | 358 / 171 (55%) / 11 | n/a | 197 / 43 (14%) / 11 |

Per script, PP-OCRv5, equal / Vision lines: Latin 70% (v6: 79%), Cyrillic 69%, ja 70%, zh-Hans 68%, hi 55%, ko 41%. Android (72 screenshots, v5): 79% overall, **ar 74%** (76 lines against Vision's 74; 48 app-string lines against Vision's 47), table in `results/verdicts.txt`.

What the low rows are (read from the actual lines, not guessed):

- **Romanian and Turkish (v5 Latin model):** the model drops letters its dictionary lacks, so "Setează preferințele" comes back as "Seteaz preferinele". `norm()` removes accents but cannot restore a missing letter, so 55% of lines differ. The verdict still agreed because the other lines matched. **PP-OCRv6 small fixes it** (ro 45% to 78%, tr 47% to 71%).
- **Korean:** the model leaves out spaces inside lines ("근무지명확함" for "근무지 명확함"). A space difference counts as a different line.
- **Hindi:** conjunct letters and nukta marks differ in places.
- A reader that joins a whole row ("Quality 70 Salary shown ...") scored 36% in my first run; that was my own line-merging, removed, and that run is discarded (`out_merged_v0/`).

## 4. Verdict agreement and the planted cases

**Base folders (no planted problems), `check` problems and per-screenshot verdict, compared with Vision (0 problems):**

| Folder | PP-OCRv5 | PP-OCRv6 Latin | Tesseract |
|---|---|---|---|
| iOS 220 | 0 problems, 220/220 same | 0 problems, 220/220 | 0 problems, 220/220 |
| Android 72 (with ar) | 0 problems, 72/72 same | not run | 0 problems, 72/72 |

**Planted wrong-language copies** (a copy of the folder, original untouched). iOS: English into de-DE (3 files), Russian into uk (2) and fr-FR (1), German into nl-NL, Chinese into ja, Japanese into ko, English into hi, one ja file deleted. Android: Arabic into de, English into ar, German into ar, Polish into ru, Chinese into ja, Japanese into ko, English into hi, Russian into fr. File hashes and missing files are found without any reader, so they are left out of the comparison.

| Case (file in folder, what is in it) | Vision (live binary) | PP-OCRv5 | PP-OCRv6 Latin | Tesseract |
|---|---|---|---|---|
| iOS de-DE x3, English | flagged x3 | flagged x3 | flagged x3 | flagged x3 |
| iOS uk x2, Russian | flagged x2 | flagged x2 | flagged x2 | flagged x2 |
| iOS nl-NL, German | flagged | flagged | flagged | flagged |
| iOS fr-FR, Russian | flagged | **missed** | **missed** | **missed** |
| iOS ja, Chinese | flagged | flagged | flagged | **missed** |
| iOS ko, Japanese | flagged (as ja) | flagged (as en) | flagged (as en) | **missed** |
| iOS hi, English | flagged | flagged | flagged | **missed** |
| iOS flagged / 10 | 10 | 9 | 9 | 6 |
| Android ar, English | flagged | flagged | n/a | missed |
| Android ar, German | flagged | flagged | n/a | missed |
| Android de, Arabic | flagged | **missed** | n/a | missed |
| Android fr, Russian | flagged | **missed** | n/a | missed |
| Android ko, Japanese | flagged | **missed** | n/a | missed |
| Android ru, Polish | flagged | flagged | n/a | missed |
| Android ja, Chinese | flagged | flagged | n/a | missed |
| Android hi, English | flagged | flagged | n/a | missed |
| Android flagged / 8 | 8 (replay of Vision's answers) | 5 | n/a | 0 |

Per-script agreement with Vision on the planted folders (same verdict: fine, not verified, or problem), PP-OCRv5: iOS Latin 153/154 (99%), Cyrillic 22/22, ja 10/10, ko 11/11, zh-Hans 11/11, hi 11/11; Android Latin 46/48 (96%), ar 4/4, hi 4/4, ja 4/4, ko 3/4 (75%), Cyrillic 4/4. Tesseract: iOS hi 10/11, ja 9/10, ko 10/11; Android ar 2/4. Full tables: `results/verdicts.txt`.

Reading these honestly: the pass mark is met on paper, but all 4 misses are wrong-script screens read by the wrong model (section 1, point 2), and a Latin-only mix-up (nl, de, en, pl) is caught. Those 4 misses are the whole gap between "14 of 18" and "18 of 18".

Tesseract's `osd` script detection was also tried with the CPU reader (`results/` runs `cpu_base_osd`, `cpu_sens_osd`): no change in any verdict.

## 5. PP-OCRv6 small for the Latin path

On the 154 Latin screenshots: **79% of Vision's lines equal against 70% for v5**; Romanian 78 against 45, Turkish 71 against 47, Polish 80 against 69; same `check` verdicts as v5 on base and planted folders (same 9 of 10 iOS planted cases). Cost: models 31.2 MB (detector 9.9 + recogniser 21.2) against 12.7 MB (4.8 + 7.9), and **slower, not faster**: 3.7 to 5.1 s against 3.0 to 4.4 s per screenshot, one thread, same three screenshots, two repeats each, load 27 to 31 (`results/speed_v5_v6.tsv`). The research note's expectation "smaller and faster" was wrong on both counts for this stack. Memory about the same (640 to 1090 MB).

## 6. Does it avoid the ANE? (step 2)

- **Read from the files (measured):** `otool -L` shows `libonnxruntime.1.20.1.dylib` and the Python module **are linked against CoreML.framework**. RapidOCR's own config (`config.yaml`, read) has `use_coreml: false`, and the execution provider list is CPU only. After one real read, the process's loaded image list (`dyld_check.py`) contains CoreML, Espresso, AppleNeuralEngine, ANECompiler and ANEServices, pulled in as dependencies of CoreML. So the claim in the note, "never touches Core ML", is wrong as worded: **it loads the frameworks and does not use them.** Building ONNX Runtime without its Core ML provider would remove even the load (inference).
- **Quiet-window test (measured):** ANECompilerService CPU time over 30 s windows: +10.8 s (others' work, before), **+0.0 s while 10 screenshots were being read** (load 37), +0.0 s after. The first attempt, a 20-screenshot run (62 s, 3.1 s per screenshot), saw the service gain 50 s, but other agents' Vision jobs were running then, so that window proves nothing either way and I do not count it.
- **Natural ANE episode (not triggered by me):** 15:56 to 15:58, load 125 to 147. ANECompilerService gained 30.6 s of CPU in 44 s, my own `check` warm-up and two other agents' Vision helpers were all still waiting on it (1:55 old in `ps`), and my 3 reads (ru, ja, hi iPhone screenshots, fresh process each) returned in 12.3, 9.9 and 12.2 s wall (load 136 to 147, three other CPU jobs of mine running). The episode lasted about 2 minutes. **This shows the reader is not blocked by a compile in progress. It is not the 40-minute wedge and I mark the criterion "long cold compile: NOT TESTED".** Log: `results/ane_episode.txt`.
- **Other Vision trouble seen while doing this (measured, not caused on purpose):** the first Vision run on the planted iOS folder (load 140 to 175) stopped with `text recognition failed ... e5rtError ... 13`, the mid-check error the later `check` change retries. The 0.1.4 binary does not retry. A rerun at load 38 finished normally. The base-folder Vision run took about 6.5 minutes at load 200 to 260 instead of ~60 s warm.

## 7. Speed and memory (step 5)

One fresh process per screenshot, so model loading is inside the time. `/usr/bin/time -l`. Load 24 to 31 (the quietest window I got; at load 100 to 250 each read took 10 to 25 s and those times are **unreliable**, not reported as speed). `cpu` is user plus system CPU seconds and is the load-proof figure.

| Variant | iPhone 1320x2868 (de-DE) | iPhone (ja) | iPad 2752x2064 (ru) |
|---|---|---|---|
| 1 thread, longer side capped at 2000 (default) | 4.5 s wall, 9.0 cpu, 640 MB | 3.3 s, 6.5, 687 MB | 4.5 s, 9.0, 985 MB |
| 4 threads | 2.4 s, 4.7 cpu, 648 MB | 2.4 s, 4.7, 687 MB | 2.8 s, 5.7, 1037 MB |
| 10 threads | 2.6 s, 5.2 cpu, 664 MB | 2.8 s, 5.7, 683 MB | 3.9 s, 7.7, 1038 MB |
| 1 thread, cap 1600 | 2.7 s, 5.4 cpu, 499 MB | 3.3 s, 6.6, 478 MB | 3.9 s, 7.8, 705 MB |
| 1 thread, cap 1200 | 2.8 s, 5.5 cpu, 472 MB | 3.1 s, 6.2, 480 MB | 3.6 s, 7.3, 522 MB |

- **About 3 s and 0.65 GB per phone screenshot, about 4.5 s and 1 GB per iPad screenshot**, one thread. 4 threads is the sweet spot; 10 is no better. A cap at 1600 or 1200 lowers memory by a quarter to a half and time by 0 to 40%; **accuracy with a cap was not measured**, so I do not recommend one yet.
- 20 screenshots in one process, one thread, load 30: 62 s, 3.1 s each. 220 screenshots would take about 11 minutes in one process (inference from that), or about 4 minutes with three processes. For comparison Vision's helper, one process per screenshot: median 2.0 s on the iOS set (load 100 to 260, slowest 143 s while macOS compiled) and median 1.1 s on the Android set (load about 40), so the CPU reader is about 2 to 3 times slower than a warm Vision, not 10 times (the Vision times are as unreliable as the load).
- Peak memory of a long batch process that loaded several script models: 0.9 to 1.8 GB. One process per screenshot stays near 0.5 to 1 GB.
- **`check` itself is slow with an external reader.** `judge_screen`'s external branch runs a regex search per string per locale over the joined text: 190 to 290 CPU seconds per 220-screenshot run in the Python process, even with all reader output cached (the Vision path takes a small fraction of that). Not part of this experiment's question, but a CPU reader would inherit it. Logs: `logs/check_*.log` (not in the repo, `Σ real` lines).

## 8. Install size and freezing (steps 1 and 3)

Installed into the throwaway venv with Python 3.13.16 (Homebrew; 3.14 not tried), `uv pip install`, versions in `results/pip-freeze.txt`:
`rapidocr 3.9.2, onnxruntime 1.20.1, numpy 2.5.3, opencv-python 5.0.0.93 (the full one, not headless, pulled in by rapidocr), pillow 12.3.0, pyclipper 1.4.0, shapely 2.1.2, omegaconf 2.3.1, pyyaml 6.0.3, python-bidi 0.6.11 (needed by the Arabic model), plus requests, protobuf, sympy and others; PyInstaller 6.22.3 and pyinstaller-hooks-contrib 2026.8 for the freeze.`

| What | Size (measured with du) |
|---|---|
| venv, packages only | 344 MB (355 MB with PyInstaller). Largest: opencv 120 MB, onnxruntime 111 MB (two copies of the 52 MB library), sympy 29 MB, numpy 22 MB |
| Models downloaded (ModelScope, RapidOCR release v3.9.2) | 117 MB: v5 detector 4.8, Latin 7.9, Eastern Slavic 7.9, Cyrillic 8.1, Korean 13.5, Devanagari 7.9, Chinese/Japanese 16.6, Thai 7.9, Arabic 8.0, Greek 7.8; v6 small detector 9.9 and recogniser 21.2; classifier 0.6 |
| Models for the 33 Vision languages (det + Latin + ES + KO + HI + CH + TH + AR) | 74.5 MB raw, **60.5 MB compressed** |
| Latin only | v5: 12.7 MB; v6: 31.2 MB |
| Frozen helper (PyInstaller onedir, `--collect-all rapidocr onnxruntime`) | 246 MB unpacked, 105 MB as .tar.gz; **215 MB and 79 MB without the 32 MB of models PyInstaller bundled by accident**; opencv is 116 MB of it (full build; the headless one should be about half, inference) |
| Models are not in the frozen folder | they are read from `CPU_OCR_MODELS`; the frozen helper answered with no network (proxy variables pointed at nothing, models by path). **It was not run with the network really off.** |

Frozen helper: the first launch took 26.9 s wall (2.6 s CPU; cold file cache and first-run checks on an unsigned binary, load 35), later launches 2.8 s wall and 684 MB (load 23).

**macOS floor (`otool -l`, per package, max `minos`):** onnxruntime 13.3, opencv 13.0, **numpy 14.0** (numpy 2.5.3's wheel), Pillow/shapely/pyclipper/yaml 11.0. The Homebrew Python here is 27.0 (the interpreter files and one library), which is not what a release would use: `tools/macho-minos.py` over the frozen folder reports 27.0 because of that. With the pinned 3.14 standalone build (minos 11) the add-on's floor would be **14 with these pins**, **13.3 with an older numpy** (inference: not built). **Not done:** a freeze with the pinned Python 3.14.2 (not installed here, not downloaded); signing and notarizing.

## 9. What was NOT run, and limits

- **th and mr:** no screenshots in the iOS or Android fixtures, so no agreement figure exists for Thai (a pass-mark script) or Marathi. The Thai and Devanagari models downloaded and read other text; they were never judged on Thai screens.
- **Hebrew, Greek:** models downloaded for Greek, no fixtures; Hebrew has no model.
- **Cyrillic model vs the Eastern Slavic model:** both downloaded, only the Eastern Slavic one was measured (ru, uk).
- **Long cold-Vision-compile test:** not run (section 6). **Real network-off test and freeze on Python 3.14.2:** not run.
- **Live Vision on the Android folder:** not run. The Android "Vision" column is Vision's saved answers (live helper, per image) judged by the repo code, which was shown to match the live binary on the iOS base and planted folders (0 and 21 problems, identical).
- **Accuracy with a longer-side cap, 4-thread parallel `check` runs, the second-model read:** not measured.
- **Sample size:** 11 screenshots per iOS locale, 4 per Android locale, one app each, English UI strings: this says nothing about screenshots with large photos, small text or dense content.
- **Load:** the accuracy runs and the first batch ran at load 175 to 285 (below the 300 limit the coordinator set; one pause of 33 s at load 306 by my governor script, `results/governor.log`); times from those runs are not used. Speed numbers are from load 24 to 31.
- **Time used:** about 1 h 35 min of the 3 h budget (start 15:25, measurements done 16:47).

## 10. After this note (deleted, as agreed)

Deleted after the commit and push: the venv (355 MB), the models (117 MB), the frozen helper (275 MB), the iOS and Android fixture copies (345 MB), the throwaway HOME, and the uv cache entries this run created (14 package archives and their index files: rapidocr, onnxruntime 1.20.1, opencv-python, pyclipper, shapely, omegaconf, antlr4, python-bidi, PyInstaller and its hooks, altgraph, macholib, colorlog, setuptools 84.0.0). The rest of the shared uv cache (16 GB) was not touched; `uv cache clean` hung on it (a lock or the size) and I stopped that command, so the removal was done by path, only for entries created after 15:20 today. Kept in the work folder (7 MB): logs, Vision's saved answers, the readers' saved lines, every `check.json` and report, the scripts. Sizes before deletion are in `results/sizes-before-delete.txt`.

To repeat: `uv venv --python 3.13`, `uv pip install rapidocr "onnxruntime==1.20.1" python-bidi`, run `cpu_ocr.py` once per language to download the models, then the scripts in `research/ocr-cpu-experiment/` in the order of `run_all_checks.sh`, `run_all_checks2.sh`, `run_all_checks3.sh` (the fixtures are the folders named in section 2).
