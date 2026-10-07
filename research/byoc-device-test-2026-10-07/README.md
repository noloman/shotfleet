# BYOC (your own XCUITest tests) device test, 2026-10-07: PASSED

`tools/fixture-byoc-e2e.sh` at commit 285e099, run with the signed 0.1.6 binary (`SHOTFLEET_BIN=.../0.1.6/unpacked/shotfleet/shotfleet`), on 2026-10-07 from 12:59 to 13:12 (12 min 46 s).
Result: `PASS: all 20 assertions passed` (`e2e.log`; per-case logs in `logs/`; start and end stats of the machine in `waiter-progress.log`).

- iOS 26.4 simulators, pinned in the generated config (`runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"`).
- Three cases: `run-attachments` (XCTAttachment, 198 s), `run-fastlane` (fastlane SnapshotHelper, 327 s), `run-nokeep` (a test without `.keepAlways`, correctly reported as a failed language, exit 1, 241 s).
- Each passing case: de and ja screenshots saved, de and ja differ, run.json says both languages ok, the build ran once, no `.xctestrun` copies left; the fastlane folder was as it was afterwards.
- Load on the Mac went from 7 at the start to 354 at the end (the run itself is heavy).

Earlier attempts, for the record: 2026-10-06 failed under heavy load (simulator uninstall hung; 14 of 20 assertions, see `../byoc-device-test-2026-10-06/`), and 2026-10-07 12:28 was killed by the hard limit because iOS 27.0 simulators froze at boot. Both were the test machine, not the feature; pinning iOS 26.4 fixed the second one.
No screenshots are kept here, and no secrets are in these logs.
