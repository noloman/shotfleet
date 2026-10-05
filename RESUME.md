# RESUME (branch claude/workarounds-text-recognition)

Goal: research/workarounds-text-recognition-2026-10-05.md (<300 lines): can Vision's ANE wedge be avoided without reboot
(usesCPUOnly / compute-device API / timeouts / fast level), per-macOS language coverage, bundled Tesseract worth it, design
as patch under research/proposed-ocr/ (NOT applied to shotfleet.py). Every claim CONFIRMED or INFERENCE.
Constraints: light CPU (device gate running, load ~800), no repo test suites (only tests.test_docs), no builds, no sudo,
do not kill ANECompilerService, git via /usr/bin/git, commit messages end [skip ci].

## Done
- ocr.swift, shotfleet.py (ocr_tool, warm_up_ocr 90 s with fallback, read_text 120 s x2, cmd_check fallback) read.
- research/proposed-ocr/vtest.swift (+ run_modes.py harness, hard 30 s): modes default|cpu14|cpuold|fast|fast+cpu14|devices|langs.
- langs on macOS 27: rev1 en-US; rev2 8; rev3 33 (accurate); fast: 6 (rev2 and 3).
- Coordinator note: usesCPUOnly deprecated macOS 14 -> setComputeDevice(.cpu, for: .main) via supportedComputeStageDevices;
  supportedRecognitionLanguages(for:revision:) deprecated macOS 12 -> instance supportedRecognitionLanguages().
  vtest uses both new APIs; compiles with no warnings at -target arm64-apple-macos13.0.
- First timing run (the old pid 69742 is gone; new ANECompilerService pid 25561 was idle 0% before the run):
  accurate default / cpu14 / cpuold: NO ANSWER in 30 s each; ANECompilerService went to ~92% CPU afterwards.
  fast and fast+cpu14: answer in 0.2 s but German text is garbled.

## Left
- check whether cpu-only accurate is merely slow (poll ps; one run with a longer limit once idle) vs wedged; sample the hung client stack
- Tesseract on 3-4 screenshots (de/ca/ar), licence/size facts, older-macOS language lists (Apple docs, mark INFERENCE)
- design: proposed ocr.swift (exit codes, timeout), check messages, fake-helper tests under research/proposed-ocr/
- write the deliverable, push

## Next step
Poll `ps` for ANECompilerService, then sample the client.
