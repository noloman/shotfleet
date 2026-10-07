# Maestro 2.11.0 on 0.1.6: fixture e2e, 2026-10-07

Question (Manu): is shotfleet only tested on Maestro 2.0.10? `MAESTRO_TESTED` was already `("2.0.10", "2.11.0")` (2.11.0 is still the newest upstream release, 2026-09-29), but the 0.1.4 to 0.1.6 changes (hierarchy text, XCUITest capture, BYOC), the 0.1.6 gate (65/65) and the Kuokka and BYOC runs used `~/.maestro/bin/maestro`, which is 2.0.10. This run puts 0.1.6 on 2.11.0.

Setup: main b8c9305 (0.1.6), `~/.maestro-tests/2.11.0/bin` first on PATH (`maestro --version` 2.11.0; `tools/maestro-compat.py` 28/28), `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios|android --keep`, iOS 26.4 pinned by a temporary uncommitted `runtime` line in the iOS config (same patch as the 0.1.6 gate), device lock `/tmp/shotfleet-devices.lock` held for the run, 45 min kill limit per platform.

| Run | Result | Log |
|---|---|---|
| Android fixture e2e | 30/30, 108 s; every screenshot's text came from the UI hierarchy | `logs/android-30of30.log` |
| iOS attempt 1 (16:01) | 17/36: iPhone half passed (4 languages, 8 screenshots, 0 problems, `ar` and `tr` retried, 2 simulators, 309 s); iPad half 0/4: all four simulators stopped answering at `simctl uninstall` (60 s) with 18 to 21 GB of swap in use | `logs/ios-attempt1-iphone-pass-ipad-machine-hang.log` |
| iOS attempt 2 (17:24) | 36/36, 518 s: iPhone 74 s, iPad 271 s, 4 languages each, 0 problems, no retries; shotfleet ran 1 simulator at a time because macOS reported elevated memory pressure (17 to 19 GB of stale swap, load 4) | `logs/ios-rerun-36of36.log`, `logs/ios-rerun-run.log`, `logs/ios-rerun-doctor.log` |

Why attempt 1 is the machine, not Maestro: the same iPad-simulator hang ended the 0.1.6 gate that morning on Maestro 2.0.10 ("iPad sims stopped answering at simctl uninstall"), shotfleet printed its own thrash warning (above 10 GB of swap), and iPhone on the same Maestro passed in the same run.

Start rule for attempt 2 (coordinator, 17:21): not actively swapping (`vm_stat` Swapouts +< 2000 pages per 60 s, three windows in a row), load < 100, free memory >= 40 %, pressure <= 2, lock free, no `xcodebuild` naming remoti-w6 or simulator D8640B97, disk >= 15 GB. Stale swap does not shrink without processes exiting, so a "swap < 60 %" rule never fired.

Not covered: real apps (CrossfitTracker and others ran on 2.11.0 on 2026-10-04, before 0.1.4 to 0.1.6), the guide's manual per-locale routes, 4 simulators in parallel (the capacity planner chose 1 to 2), clean timings (loaded Mac, 1 simulator at a time), Android on 2 emulators at once.
