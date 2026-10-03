# Verify shotfleet on Xcode 27 final (Device Hub)

**Needs:** your Mac with Xcode 27 final (14 Sep 2026) and an iOS 27 simulator runtime; about 1 hour.

## Context

Xcode 27 removed Simulator.app and replaced it with Device Hub (`DeviceHub.app`, bundle id `com.apple.dt.Devices`); other tools broke on `open -a Simulator` (expo/expo#46671, callstackincubator/rock#731, anthropics/claude-code#95085). Static analysis (`docs/compat.md`): shotfleet only calls `xcrun simctl` (list, create, delete, boot, bootstatus, status_bar, install, shutdown, help) and never opens Simulator.app; Maestro 2.0.10 and 2.11.0 contain `open -a .../Simulator.app --args -CurrentDeviceUDID` in `LocalSimulatorUtils.launchSimulator`, reachable only from `DeviceService.startDevice` (`maestro start-device` and the interactive device picker). shotfleet boots its own simulators and hands Maestro their ids, so that path should not run. This is an inference. No record says which Xcode the real runs used, and the core product's selling point on iOS depends on this.

## Steps

1. Record `xcodebuild -version`, `xcrun simctl list runtimes`, `sw_vers` in the PR.
2. `python3 shotfleet.py doctor` must report `xcrun simctl` ok. Also try each simctl verb shotfleet uses by hand on a throwaway device (`create`, `boot`, `bootstatus -b`, `status_bar override`, `install`, `shutdown`, `delete`) and note any that changed.
3. `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` with Maestro 2.0.10 (36 assertions). While it runs, in another terminal: `pgrep -fl "open -a"` and `log stream --predicate 'process == "open"'` (or `ps` sampling) to confirm nothing runs `open -a Simulator`.
4. Check that the status bar override works (`xcrun simctl status_bar <udid> override ...`; the fixture screenshots must show 9:41) and that screenshots are the right size for the 6.9" class (1320x2868).
5. Check which iOS runtime shotfleet picks by default (`default_runtime`, near `shotfleet.py:3122`; the README example says iOS-26-5) and that iPad 13" (M5) device types still exist: `xcrun simctl list devicetypes`.

## Passed when

36 of 36 assertions; no `open -a Simulator`; status bar and sizes right. If `simctl` or Maestro behaves differently, the simulator functions in `shotfleet.py` (`make_pool`, `Sim`, `run_setup`) are where to look; fix with a test.

## Record

`STATUS.md` row 9 (add Xcode build, macOS and iOS versions), the Xcode 27 row in `docs/compat.md` (replace "inference" with the result), `docs/handoff.md` item 12 (delete if passed).

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
