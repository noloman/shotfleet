# RESUME: claude/013-android-hierarchy (PR #44 brought up to date for 0.1.3)

Branch `claude/013-android-hierarchy`, cut from `origin/claude/android-hierarchy-text` (PR #44, not force-pushed) and merged with `origin/main`.
No new PR opened: the owner decides.

## State
- [x] Merge with origin/main. Conflicts:
  - `shotfleet.py` check row dict: kept #44's `"evidence": "hierarchy" if r.get("ocr") == "app" else "ocr"`, main's `if no_language:` note block and
    main's `unread = ... and r["file"] not in unread_files` line.
  - `tests/claims.json`: main took C131 (macOS 13 build) for itself, so #44's claim is now **C132** (text unchanged). No doc referenced #44's id.
- [x] Version gate intact: `hierarchy_supported()` needs `maestro --version` >= 2.7.0 (`HIER_MIN`); below or unreadable, a note and OCR. Blank-frame
  check (`blank_note`, `blank_screenshot`) untouched and runs before `save_hierarchy_texts` in the Android round.
- [x] Targeted tests green (420 tests, 2 skipped): tests.test_android_hierarchy tests.test_fixture_e2e tests.test_agent_skills tests.test_shotfleet
  tests.test_check_quality tests.test_json_multi_report tests.test_android_apk tests.test_claims tests.test_claims_unit tests.test_docs.
- [x] Docs: README line 23, SKILL.md, docs/handoff.md, research/limits-text.md 1g already consistent after the merge; CHANGELOG Unreleased has one line.
- [ ] Device run (coordinator, later): below. Not run: this session was device-free.

## Device run for the coordinator (Android only, two Maestro versions, one after the other)

Before: take the device lock per `docs/device-queue.md` (`mkdir /tmp/shotfleet-devices.lock`, holder line), quiet check (free memory >= 20 %,
load < 300, no emulator on ports 57xx). AVD `shotfleet_android` must exist. Run from this branch's checkout.

1. Maestro 2.11.0 (markers on):
   `PATH=$HOME/.maestro-tests/2.11.0/bin:$PATH SHOTFLEET_E2E=1 perl -e 'alarm 1500; exec @ARGV' tools/fixture-e2e.sh --platform-only android --keep`
   Assert: exit 0; 30 of 30 assertions, including "every screenshot's text came from the UI hierarchy"; `run.json` `hierarchy_markers: true`;
   `check.json` `evidence: "hierarchy"` on 8 of 8 screenshots; the run prints "screen text from the UI hierarchy for 8 of 8 screenshots";
   `raw/ja/*.texts.json` holds `ようこそ` and no clock/wifi/battery lines; 0 problems.
   Expected: about 200 s for the `run` step, about 6 minutes for the whole script (2026-10-05: lock 10:17 to 10:23).
2. Maestro 2.0.10 (default `~/.maestro/bin/maestro`, markers off):
   `SHOTFLEET_E2E=1 perl -e 'alarm 1500; exec @ARGV' tools/fixture-e2e.sh --platform-only android --keep`
   Assert: exit 0; 29 of 29 assertions (the hierarchy assertion is not added); the note
   "Maestro 2.0.10 saves no per-step screen hierarchy (needs 2.7.0) ... read from pixels (OCR)" is printed; `run.json` `hierarchy_markers: false`;
   every `check.json` row has `evidence: "ocr"`. Expected: similar, about 6 to 8 minutes.

Hard limits: 25 min per run (`perl -e 'alarm 1500; exec @ARGV'`: macOS has no `timeout`; the alarm kills only the script, so then also stop its
children and emulators as below); if a run has printed no new line for 10 minutes, stop it (only your own PIDs: the `fixture-e2e.sh`
process tree you started) and shut down your own emulators (ports 5702/5704: `adb -s emulator-5702 emu kill`). Never kill another session's
emulator. Release the lock (`rm -rf /tmp/shotfleet-devices.lock`) once your emulators are down. A failure keeps the temp dir: note its path.
After both pass: record the two results (date, assertions, wall time, Maestro version) in claim C132's proof and in the PR body.
