# RESUME (branch claude/workarounds-text-recognition)

Goal: research/workarounds-text-recognition-2026-10-05.md. Can Vision's ANECompilerService wedge be avoided without a reboot; language
coverage per macOS; is bundled Tesseract worth it; design as a patch under research/proposed-ocr/ (NOT applied to shotfleet.py).
Constraints: light CPU, no repo test suites (only tests.test_docs), no builds of the product, no sudo, do not kill ANECompilerService, git via
/usr/bin/git, commit messages end [skip ci].

## PAUSED (coordinator, device gate): NO Vision / OCR / Tesseract runs until /tmp/shotfleet-rc-gate-done exists.
Writing only until then. `ps` (read only) is fine.

## Done (all pushed)
- Deliverable written: research/workarounds-text-recognition-2026-10-05.md (229 lines). Verdict: CPU-only (usesCPUOnly and compute-device
  API), revision 2, the macOS 15 Swift API and cancel() do NOT avoid the ANE compile; only .fast answers during it (junk text). The old wedge
  pid 69742 was gone (no reboot), so "while truly wedged" is untested; cold compile used as proxy (35-122 s under load 550-890).
- research/proposed-ocr/: ocr.swift (exit codes, --rev2), shotfleet-ocr.patch (patient warm-up, messages, exit-2 handling, Latin-unlisted rule),
  test_proposed_ocr.py (16 pass, fake helpers, no Vision), vtest.swift, vtest15.swift, nlprobe.swift, run_modes.py, patient.py, helper_smoke.py.

## Left (after the gate file appears)
Run section 9 of the deliverable, one at a time, each under 30 s hard timeout (run_modes.py), `ps ... | grep ANECompilerService` before and after;
report whether a NEW ANECompilerService pid appears and whether usesCPUOnly / compute device avoids it (expected: no). Then update sections 1, 2, 8.
Binaries are in the scratchpad (vtest, vtest15, ocr2, vtestB..F): rebuild from research/proposed-ocr/*.swift with swiftc -target arm64-apple-macos13.0
(vtest15: macos15.0) if the scratchpad is gone. Copy a binary to a NEW path to get a cold compile.

## Next step
Wait for /tmp/shotfleet-rc-gate-done; then experiment 1 of section 9.
