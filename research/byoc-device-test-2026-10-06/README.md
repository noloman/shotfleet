# BYOC device test, first run (2026-10-06)

What this is: the one run of `tools/fixture-byoc-e2e.sh` (the device test for the `[capture]` feature: your own XCUITest screenshot tests on iOS simulators), copied from `shotfleet-rc-build/0.1.6/` on 2026-10-06. The run started at 22:57 and took 28 minutes.

Result: **14 of 20 assertions passed. The test as a whole did not pass.** The Mac was overloaded (load 300 to 800, about 10 GB of swap in use), and simulators stopped answering `simctl uninstall` during the run.

| Case | Result | Notes |
|---|---|---|
| XCTAttachment (`run-attachments`) | passed | German and Japanese saved 2 screenshots each, the two languages differ, `run.json` says both ok, the build ran once, no `.xctestrun` copy was left. One of the 2 simulators stopped answering, so the run finished on 1 simulator (German was retried): "several simulators at once" was not shown on a device. |
| Test without `.keepAlways` (`run-nokeep`) | passed | The languages failed with the `.keepAlways` hint, exit 1. Weak evidence: a simulator stopped answering again and one `.xcresult` was unreadable in that run. |
| fastlane `SnapshotHelper` (`run-fastlane`) | failed (6 assertions) | 0 screenshots in both languages: the simulator hung at `simctl uninstall` and the run was stopped after no progress for 240 s. The check that the fastlane folder is left as it was passed. This case has not run on a device. |

Files:

- `byoc-e2e.log`: the script's own output (what the waiter, the lock and each assertion said).
- `byoc-evidence/logs/run-attachments.log`, `run-fastlane.log`, `run-nokeep.log`: what `shotfleet run` printed in each case.
- `byoc-evidence/out-attachments/run.json`: the `run.json` of the passing XCTAttachment run (`"simulators": 1`).
- `byoc-evidence/out-attachments/build.log`: the `xcodebuild build-for-testing` log of that run (128 KB).

Not copied: the screenshots and `.xcresult` bundles (none were in the evidence folder). Nothing was redacted: a search for key, token, secret, password, `SHOTFLEET_KEY` and `@` found only compiler command lines (`@/var/folders/...` response files) in `build.log`. The logs hold absolute paths under `/Users/manu` and `/var/folders`.

Next: one passing run on a quiet Mac. Until then the README, docs, home page and skill say the feature is new in 0.1.6 and not run end to end on a device yet (claims C231, C232, C235).
