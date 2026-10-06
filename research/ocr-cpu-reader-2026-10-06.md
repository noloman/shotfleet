# A CPU-only text reader for shotfleet: what exists, what fits (2026-10-06)

Branch `claude/ocr-cpu-reader-research`. Docs only: nothing installed, nothing downloaded, no code touched. Web reading on 2026-10-06 plus the repo.
Labels: **C** = CONFIRMED, read in the named source (keys at the end, URLs there). **I** = INFERENCE, my reasoning, not shown by a source.
"Published" = a number from a vendor or third party page, measured on their hardware (never an Apple chip here). "Inference" = my estimate.
Why: on 2026-10-06 `ANECompilerService` compiled for ~40 min and `shotfleet check` failed twice. Rebooting is not acceptable; the ruled-out list is in
`research/workarounds-text-recognition-2026-10-05.md` (L1). This note asks only: can a reader that never touches Vision, Core ML or the ANE be shipped?

## 1. Verdict

- **Yes, one candidate fits: PP-OCRv5 mobile models (PaddleOCR) run through ONNX Runtime on the CPU.** All 33 of Vision's languages have a model in it, plus
  Greek, Catalan, Croatian, Hungarian, Slovak and Slovene, which Vision lacks. Licences are Apache 2.0 and MIT. [C S1 S5 S8]
- **It does not fit inside the ~10 MB tarball.** Models for the scripts are ~80 MB and the runtime plus its Python libraries add tens of MB more. It should be an
  optional add-on helper, reached through the `--ocr-command` hook that already exists (L3). [C S2 S3 S8 for the model sizes; I for the total]
- **Nothing here is proven on UI text.** Every accuracy number I found is on PaddleOCR's own mixed benchmark, not on app screenshots. The 220-screenshot
  measurement in section 7 decides it, and it is cheap.
- **Hebrew has no official model** in any PP-OCR version (only community fine-tunes). Tesseract is the only candidate that reads it. Vision does not read
  Hebrew or Greek either, so this is a gap against the wish list, not against Vision. [C S1 S5 S11]
- **Second choice: a Tesseract built from source (static, macOS 13+) with tessdata_fast.** Smallest runtime, widest coverage, same licence family, but the weakest
  reader on UI text on this repo's own samples (L1 section 7). It removes the `brew install` step; it does not remove the "unverified" verdicts.
- **Rejected:** EasyOCR (PyTorch, no Greek or Hebrew), docTR (PyTorch or TensorFlow, models mostly one Latin vocabulary), a Core ML model pinned to CPU,
  Accelerate-based reading (nothing to run).
- Cost of the best one as an optional add-on: **M**. Cost of the measurement that decides whether to start: **S**.

## 2. Fixed facts from this repo that shape the answer

- The frozen app is standard library only. `packaging/requirements-build.txt` pins PyInstaller, its hooks, certifi, setuptools, packaging: no numpy, no
  OpenCV. [C L2] So any Python OCR stack (numpy, OpenCV, ONNX Runtime) would change what the main binary is. Put it in a separate helper.
- `external_ocr(command, png, lp)` already runs a user command with `{image}`, `{lang}`, `{tesseract}` filled in; `TESSERACT_COMMAND` is the default
  shape. [C L3, shotfleet.py near lines 2709 and 2790] A CPU reader that prints text per line fits there without touching `check`.
- The Swift helper targets macOS 13.0; the bundled Python is built for macOS 11 (`MINOS_MAX=11`), and the program runs on 13+. [C L2]
  So a fallback has to run on macOS 13 and up. It need not run on 11 or 12.
- How the check uses text: the expected language comes from the folder or locale name, then strings are compared with the app's own tables. [I from L1/L3]
  So a reader does not have to guess among 30 scripts blind: pick the script model from the expected locale and read; run the Latin model too when
  "wrong language" has to be told apart from "right language, bad read".

## 3. Language coverage against Vision's 33

Vision (accurate, revision 3, macOS 27, from L1 section 4): en fr it de es pt zh-Hans zh-Hant yue ko ja ru uk th vi ar ars tr id cs da nl no nn nb ms pl ro sv fi hi mr.

| Vision language group | PP-OCRv5 model that covers it | Source |
|---|---|---|
| en, fr, it, de, es, pt, nl, sv, da, no, fi, pl, cs, ro, tr, id, ms, vi | `latin_PP-OCRv5_mobile_rec`: its list of 45 includes all of these | C S1 |
| ca, hr, hu, sk, sl (Vision does not list them) | the same Latin model lists Catalan, Croatian, Hungarian, Slovak, Slovenian | C S1 |
| ru, uk | `eslav_` (Russian, Belarusian, Ukrainian, English) or `cyrillic_` (about 33 languages) | C S1 |
| ar (ars) | `arabic_` (Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi) | C S1 |
| hi, mr | `devanagari_` (Hindi, Marathi, Nepali, Sanskrit and others) | C S1 |
| th | `th_` | C S1 |
| ko | `korean_` | C S1 |
| zh-Hans, zh-Hant, ja | the default model: "Simplified Chinese, Chinese Pinyin, Traditional Chinese, English, Japanese" | C S1 |
| yue (Cantonese) | not named anywhere; written with traditional characters, so the zh model should read it | I |
| el (Greek) | `el_PP-OCRv5_mobile_rec` | C S1 |
| he (Hebrew) | **none** in PP-OCR; only community models on Hugging Face (Rivok, gigapdf) | C S1 S5 |

PP-OCRv6 (published 2026, `PaddleOCR 3.7.0`): one unified small or medium model for zh, zh-Hant, en, ja and 46 Latin languages only. Cyrillic, Arabic,
Devanagari, Thai, Greek and Korean still need the v5 script models. RapidOCR lists v6 as "excluding Korean, Arabic, Tibetan, Yi". [C S5 S6]
So v6 helps the Latin path (smaller, faster) and nothing else.

Tesseract: all of them, including Hebrew and Greek (tessdata_fast has per-language files and 37 script models). [C S11]

## 4. The candidates

| | PP-OCRv5 mobile via ONNX Runtime (RapidOCR or own code) | Tesseract 5, own static build | EasyOCR | docTR | Core ML on CPU / Accelerate |
|---|---|---|---|---|---|
| Never touches ANE/Core ML/Vision | **C** for ORT's default: the Core ML provider "must be explicitly registered" (S8). RapidOCR's own default provider: **I**, check in the plan | **I** (pure C++ on CPU; no Apple ML framework in its dependency list, S11) | I (PyTorch CPU) | I (PyTorch or TF) | Core ML: **no**, still the Core ML stack; whether `cpuOnly` skips the ANE compile for a model of ours is **I**, and Vision itself compiled with the CPU device set (L1) |
| Licence for a paid closed binary | PaddleOCR Apache 2.0, RapidOCR Apache 2.0, ORT MIT, v6 small rec Apache 2.0 [C S1 S5 S6 S8] | Tesseract and tessdata_fast Apache 2.0; Leptonica BSD-2 [C S11] | Apache 2.0 [C S9] | Apache 2.0 [C S10] | n/a |
| Languages | 33 of 33 plus el ca hr hu sk sl; no he (section 3) | all, incl. he, el | no Greek, no Hebrew in `all_lang_list` [C S9] | vocabularies: latin, french, german, arabic, cyrillic, devanagari, greek, thai; most models "trained on a French vocabulary" [C S10]; CJK not listed | n/a |
| Added size | models ~80 MB for the scripts (below); ORT wheel 21.5 to 31 MB; Python stack more | binary a few MB (I); data below | PyTorch "roughly 2 GB", weights 94 MB, 985 MiB peak RAM (published, English test) [C S9] | PyTorch or TF: same class as EasyOCR [I] | n/a |
| Frozen arm64, minos <= 13 | see section 5 | yes: built by us with `-mmacosx-version-min=13.0` [I]; Homebrew's is minos 27 (L1 section 7) | heavy, no [I] | heavy, no [I] | n/a |
| Speed per screenshot | published 1.3 to 2.0 s (CPU, Xeon) | not published for this size; L1 saw 0.1 to 0.5 s on 257x560 copies | published 0.06 s per clean line (warm) | not read | n/a |
| Short UI text accuracy | not published; PaddleOCR's own mixed set: 80 to 89% line accuracy per model | worst on this repo's samples (L1) | published: collapses below ~10 px text height | not read | n/a |
| Maintenance risk | low-medium: PaddleOCR 3.7.0 on 2026-06-11, RapidOCR 3.9.2 on 2026-07-21, 90.7k stars [C S5 S6] | low: mature, but 5.5.x is not changing fast and the training-free path is stable [I] | high: last release 1.7.2 in Sept 2024 [C S9] | medium | n/a |

### 4.1 PP-OCRv5 mobile via ONNX Runtime (the candidate)

- **Models.** Detector `PP-OCRv5_mobile_det` 4.7 MB (server one 84.3 MB). Recognizers: default zh/ja/en 16 MB, latin 14, korean 14, cyrillic 7.7, arabic 7.6,
  devanagari 7.5, th 7.5, el 7.5. [C S2 S3] Sum for all 33 Vision languages (det + zh + latin + korean + cyrillic + arabic + devanagari + th) = **~79 MB**;
  with Greek ~87 MB. Those are PaddlePaddle sizes. A Hugging Face ONNX conversion lists latin and slavic at 7.5 MB, Korean 13, zh/ja 81 (that one is the
  server model), so the ONNX figures differ [C S7]; plan for 50 to 90 MB and measure.
- **Latin only** (the three or four screens Vision cannot read plus every Latin language): det 4.7 + latin 14 = ~19 MB. [C S2 S3]
- **Runtime.** ONNX Runtime macOS wheel: 21.5 MB (1.30.0) and 31.0 MB (1.20.1). [C S8] RapidOCR needs, besides ORT: numpy, opencv-python-headless, pyclipper,
  Shapely, Pillow, PyYAML and more; ONNX Runtime is no longer pulled in by `pip install rapidocr`. [C S6] A frozen second helper with all of that:
  **I: 80 to 150 MB unpacked, 40 to 70 MB compressed**, on top of the models. This is why it is an add-on.
- **macOS floor.** ORT docs: "by default ... a minimum target macOS version of 13.3". [C S8] The 1.20.1 wheels are tagged `macosx_13_0_universal2`; 1.30.0 is
  `macosx_14_0_arm64`, so a current wheel would raise the floor to 14. [C S8] Pin 1.20.x for 13, or build ORT from source. The ORT docs do not describe a lower target. [C S8]
  Fine for a fallback that only has to run where the Vision helper does (13+). Check the real `minos` with `otool -l` (plan, step 3).
- **Offline.** RapidOCR downloads models on first run by default, but accepts explicit `Det.model_path`, `Rec.model_path`, and a `download_models` command. [C S6]
  For shipping, give explicit paths so the helper never needs the network.
- **Speed.** Published: PP-OCRv5 mobile, 1.75 s per image at the default (shorter side at least 736), 1.31 s at 640 max, 2.00 s at 1280, on an Intel Xeon Gold 6271C
  over 200 general and document images. [C S4] The 1290x2796 screenshot is taller than most of that set, so **I: 2 to 4 s each on an M1 Pro**, about 7 to 15 minutes
  for 220 screenshots; fine for a fallback, not for the default. PP-OCRv6 small: 0.59 s per image on a Xeon 8350C with OpenVINO (published, S5).
- **Accuracy.** Recognition accuracy per model on PaddleOCR's multilingual sets: latin 84.7%, arabic 81.27%, cyrillic 80.27%, devanagari 84.96%, th 82.68%,
  el 89.28%, korean 88.0%, zh/ja default 81.29%. [C S1 S2] It is a line-level score on their data; the docs give no screenshot or UI figure. [C S4]
  Whether it beats Tesseract on app screens is **I: likely yes** (a deep recogniser trained on varied scenes; Tesseract is measured weak in L1), **not shown**.
- **Other builds of the same models, to avoid Python:**
  - MNN (Apache 2.0) via the Rust crate `ocr-rs` / `rust-paddle-ocr`: v4, v5, v6 models, all the script models listed, macOS x86_64 and ARM listed, 332 stars,
    one maintainer. [C S12] MNN's own page does not state macOS support. [C S12] One small native binary, no Python: the best shape, the least proven.
  - ncnn (BSD-3, no external dependencies, macOS listed). [C S12] I found no maintained PP-OCRv5 ncnn pipeline; conversion would be ours (I).
  - `RapidOcrOnnx` (C++, ORT 1.15.1 and OpenCV 4.8.1, macOS binaries, last release Jan 2024): too old for v5 scripts [C S12].
  - `oar-ocr` (Rust over the `ort` crate): v4 and v5, but only Chinese, English, Eastern Slavic, Korean, Latin dictionaries [C S12]: no Arabic, Devanagari, Thai.

### 4.2 Tesseract, our own static build

- **Licence.** Tesseract and tessdata_fast Apache 2.0 [C S11]; Leptonica BSD-2, libpng/jpeg/tiff under their own [C S11 libtesseract README].
- **Build.** The official page lists Leptonica as required and zlib, libpng, libjpeg, libtiff, giflib, openjpeg, webp, archive, curl as optional; training tools are optional. [C S11]
  For one PNG input only libpng and zlib are needed [I]. Build with `MACOSX_DEPLOYMENT_TARGET=13.0` (or 11.0), `-DBUILD_SHARED_LIBS=OFF`,
  training tools off. OpenMP is an extra install on macOS; without it Tesseract is single-threaded, which `tesseract_env()` already forces (L3). [C S11 for OpenMP; I for the rest]
  The `libtesseract` Swift package did this once (macOS 10.13 minimum, MIT) but "is no longer maintained". [C S11] Homebrew's bottle is minos 27 (L1).
- **Size (tessdata_fast, per-language files, bytes from the GitHub contents listing, S11):** eng 4.1 MB, deu 1.5, fra 1.1, spa 2.3, ita 2.7, por 2.0, rus 3.9, ara 1.4, fas 0.4,
  heb 1.0, hin 1.1, ell 1.4, jpn 2.5, kor 1.7, chi_sim 2.5, chi_tra 2.4, pol 4.8, nld 6.1, swe 4.2, hun 5.3, hrv 4.1, cat 1.1. 22 languages ≈ 59 MB; 30 would be ~75 MB (I).
  The script models are far bigger: Latin 89 MB, Cyrillic 29, Devanagari 18, Arabic 9.3, Hebrew 4.9, Greek 3.0, Thai 4.2, Hangul 4.8, HanS 6.0. [C S11] Use per-language files.
  (The listing did not show ukr, tha, tur, vie in the fetch; they exist in the repo: unconfirmed here.)
- **Accuracy.** Tesseract's own guide asks for "at least 300 dpi" and dark text on light for 4.x. [C S11] Measured on this repo (L1 section 7): German settings sheet 8 lines,
  several wrong, against Vision's 17 correct; Arabic partial. Third-party blog benchmarks (one says 453 ms CPU, another says it "struggles with anything beyond clean, straight,
  printed text") are not on screenshots and I did not use them. [I]
- **Maintenance.** The `tesseract` project is stable; no urgent risk. The risk is ours: a new build stage in the release (signing every dylib), which the product avoided until now (L2).

### 4.3 Rejected, with the reason

- **EasyOCR:** PyTorch CPU, "roughly 2 GB" install, 985 MiB peak RAM, English-only test; character error rate 0.04 at 12 px text and 0.77 at 8 px; no Greek or
  Hebrew in `all_lang_list`; last release Sept 2024. [C S9] Our screenshots are large, so the size cliff is not the issue; the install size and coverage are.
- **docTR:** PyTorch or TensorFlow, speeds quoted on an Intel i7, models mostly on a French vocabulary, no CJK vocabulary in the list. [C S10]
- **Core ML model pinned to CPU:** it is still the Core ML runtime that the wedge lives in. `MLComputeUnits.cpuOnly` exists (S8 for ORT's mirror of it) but L1 measured Vision with the CPU
  device assigned and it still queued behind the ANE compile; for a model of our own I have no evidence either way (I). We would also have to convert and own the models. Not worth it when ORT's CPU
  provider never loads Core ML.
- **Accelerate:** gives matrix and signal routines, not a text reader. Writing an inference engine on it would be L and pointless next to ORT or MNN. [I]

## 5. Ranked recommendation

1. **PP-OCRv5 mobile + ONNX Runtime CPU, as an optional add-on helper** (`shotfleet-ocr-cpu`), called through `--ocr-command`. It picks the recogniser from the expected locale,
   reads, and prints lines. Ship Latin first (19 MB of models), then Cyrillic, Arabic, Devanagari, Thai, Korean, zh/ja, Greek as extra packs. Use PP-OCRv6 small for the Latin pack if the plan
   shows it is as good (smaller and faster, Apache 2.0).
2. **Tesseract, own static build, with a per-language data pack.** Do this if (1) fails the measurement, or in addition for Hebrew. Smaller and simpler at run time, weaker reader.
3. **Native PP-OCR (Rust + MNN, or C++ + ORT) later,** only if the Python add-on's size or start time hurts buyers. One binary, no Python; largest build effort and the least proven crate.
4. Everything else: do not pursue (section 4.3).

Cost to build (1) as an add-on: **M.** A helper script around RapidOCR (about 100 lines), routing locale to model pack, a PyInstaller build of the helper on the pinned Python (3.14.2: **I**,
check that numpy, OpenCV and ORT publish 3.14 wheels; ORT 1.30.0 does, 1.20.1 only lists 3.10 to 3.13 [C S8], and RapidOCR lists Python 3.8 to 3.13 [C S6]), signing and notarizing it with the
existing loop in `packaging/build.sh`, tests with fake models, a docs section. The Python version point could add a second pinned interpreter for the helper (S to M extra).
The decision experiment (section 7) is **S** and needs no release code.

## 6. What Manu must approve (nothing has been done)

- **Downloads for the experiment, in a throwaway folder outside the repo:** `rapidocr`, `onnxruntime` (MIT), `numpy`, `opencv-python-headless`, `pyclipper`, `Shapely`, `Pillow`, `PyYAML`, `omegaconf`
  and so on from PyPI (~150 to 250 MB, I); PP-OCRv5 models (~90 MB, sizes in section 4.1) from the RapidOCR host (ModelScope: a Chinese-hosted site) or Hugging Face. Pin by SHA-256 if it ships.
- **Size:** the add-on, not the main tarball, carries the weight: Latin pack ~19 MB of models + helper stack tens of MB; all scripts ~90 MB of models. Main tarball stays ~10 MB. Gumroad file limit not checked here.
- **Licence:** Apache 2.0 (PaddleOCR models, RapidOCR, OpenCV 4.5+: **I** for OpenCV), MIT (ONNX Runtime), BSD (numpy, Shapely): all allow a paid closed binary with notices. A
  `NOTICE`/`THIRD-PARTY` file in the add-on is needed. For Tesseract: Apache 2.0 + Leptonica BSD-2, the same.
- **A second pinned Python for the helper** may be needed (the 3.14 wheel question above), and a second signed and notarized artifact in the release.

## 7. Minimal measurement plan (this Mac, no device, after approval)

Corpus: the 220 iOS screenshots and the Arabic, German, Catalan samples under `research/real-apps-*` and the article-01 set (0 problems with Vision, 0.1.4). Throwaway venv outside the repo.

1. **Install and pin** (needs the approval above): `rapidocr`, `onnxruntime` 1.20.1, plus models by explicit path. Record versions and file sizes (`du -sh`).
2. **Does it avoid the ANE?** `ps -axo pid,time,command | grep ANECompilerService` before and after a 20-screenshot run: CPU time unchanged. Then the real test: start a cold Vision
   compile on a new-path helper copy (L1 section 9 experiment 2), and while the service is at ~100%, run the CPU reader on three screenshots: expect answers, not a wait.
   Also `otool -L` on the onnxruntime library for `CoreML.framework`, and `otool -l | grep -A3 LC_BUILD_VERSION` for `minos`.
3. **Floor and freezing:** build the helper with PyInstaller on 3.14.2 if wheels exist, else on 3.13; `tools/macho-minos.py dist/<helper>` must report 13.x or lower; run it from a folder with the network off.
4. **Accuracy against Vision:** for each screenshot, run Vision (warm) and the CPU reader; compare line sets after `norm()`; report per language: lines found, lines equal, and `check` verdict agreement
   (the metric that matters, since `check` compares to expected strings). Add Tesseract `-l <lang> --psm 6` as the third column. Pass mark to continue: verdict agreement >= 95% on Latin, Cyrillic, ja, ko, th, ar;
   report hi and mr separately (small samples).
5. **Speed and memory:** wall time per full-size screenshot (1290x2796) and `/usr/bin/time -l` peak RSS; one thread versus all cores; with the longer side capped at 1600 and 2000.
6. **The Latin path with v6 small** against v5 latin on the same set: same table, expect smaller and faster.
7. **Write the numbers into `research/ocr-cpu-reader-measure-<date>.md`;** the go/no-go on building the add-on follows from step 4 alone.

## 8. What I could not verify

- Accuracy on UI text for any candidate. All figures are on the vendors' own sets.
- Apple-silicon speed: every published figure is on Xeon hardware (S4 S5); Hugging Face and the docs do not say which CPU the model-size table timings used.
- That RapidOCR's default execution provider is CPU only; that `onnxruntime` freezes cleanly with PyInstaller (a hook for it in `pyinstaller-hooks-contrib` is plausible, not confirmed: I searched for it and found no page).
- The ONNX file sizes of the PP-OCRv5 packs (the two sources disagree), and the unpacked size of a frozen helper.
- Whether ORT 1.20.x lists a Python 3.14 wheel (the 1.20.1 page shows 3.10 to 3.13; 1.30.0 shows 3.11 to 3.14).
- Tesseract built with `-mmacosx-version-min=13.0` and statically: plausible, no one has built it here; static binary size is an estimate.
- tessdata_fast file sizes came from the GitHub API through a summarising fetch; ukr, tha, tur, vie did not appear there.
- Sources I could not read in full: Apple's `MLComputeUnits` page (search snippet only), the WebPII benchmark PDF (the fetch returned file structure, not text), MNN's macOS statement.

## Sources

- S1 PaddleOCR PP-OCRv5 multilingual: https://www.paddleocr.ai/v3.3.2/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html and https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
- S2 PaddleOCR recognition table (sizes, accuracy): https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html
- S3 PaddleOCR detection table: https://www.paddleocr.ai/main/en/version3.x/module_usage/text_detection.html
- S4 PP-OCRv5 speed: https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html
- S5 PP-OCRv6: https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html ; https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec ; repo (Apache 2.0, 3.7.0): https://github.com/PaddlePaddle/PaddleOCR
- S6 RapidOCR: https://github.com/RapidAI/RapidOCR (Apache 2.0, LICENSE file read) ; https://pypi.org/project/rapidocr/ ; https://rapidai.github.io/RapidOCRDocs/main/model_list/ ; .../install_usage/rapidocr/install/ ; .../usage/ ; https://raw.githubusercontent.com/RapidAI/RapidOCR/main/python/requirements.txt
- S7 ONNX conversions: https://huggingface.co/monkt/paddleocr-onnx/blob/main/README.md
- S8 ONNX Runtime: https://pypi.org/project/onnxruntime/ (1.30.0) ; https://pypi.org/project/onnxruntime/1.20.1/ ; https://onnxruntime.ai/docs/build/inferencing.html ; https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html
- S9 EasyOCR: https://github.com/JaidedAI/EasyOCR ; https://github.com/JaidedAI/EasyOCR/blob/master/easyocr/config.py ; https://thunderbit.com/blog/easyocr-review
- S10 docTR: https://mindee.github.io/doctr/using_doctr/using_models.html ; https://github.com/mindee/doctr
- S11 Tesseract: https://github.com/tesseract-ocr/tessdata_fast (+ LICENSE, + API listing https://api.github.com/repos/tesseract-ocr/tessdata_fast/contents/ and /contents/script) ; https://tesseract-ocr.github.io/tessdoc/Compiling.html ; https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html ; https://github.com/SwiftyTesseract/libtesseract
- S12 Other builds: https://docs.rs/crate/ocr-rs/2.3.4 ; https://github.com/zibo-chen/rust-paddle-ocr ; https://docs.rs/crate/oar-ocr/0.2.1 ; https://github.com/RapidAI/RapidOcrOnnx ; https://github.com/alibaba/MNN ; https://github.com/Tencent/ncnn
- L1 `research/workarounds-text-recognition-2026-10-05.md`; L2 `packaging/build.sh`, `packaging/requirements-build.txt`; L3 `shotfleet.py` (`external_ocr`, `TESSERACT_COMMAND`, `tesseract_env`, `read_text`)
