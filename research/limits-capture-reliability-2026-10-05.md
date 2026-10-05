# Capture reliability: where a run can hang, flake, give wrong screenshots or leave a mess (2026-10-05)

Scope: `shotfleet run` from `shotfleet.py` on `main` 4755d1e (iOS `ios_run_inner`, Android `android_run_inner`, `run_guarded`, `make_pool`, `healthy_installs`,
`collect_shots`, `capture_texts`, cleanup in `main_cmd`). Method: code reading, plus device-free tests with stubs (fake `simctl` objects, fake adb emulators, a
fake Maestro, real child processes for the process-handling cases). **No simulator, emulator or Maestro was started**: the device lock was held by another
session ("WOD Tracker Play screenshots | retry tr,zh-TW"), and nothing here needed a device. Everything below marked "measured" was run in this session
on stubs; everything else is read from the code and says so.

## Top 3 findings (all three fixed on this branch, tests in `tests/test_capture_reliability.py`)

1. **A simulator that wedges while booting left the others booted.** `make_pool` boots all n simulators, then waits on `bootstatus` one by one (up to 900 s
   each). A simulator only joined `OUR_SIMS`, the list cleanup shuts down, after its own `bootstatus` and `status_bar`. A timeout on sim 2 of 4 therefore left
   sims 2 to 4 booted when shotfleet exited, on a Mac where booted simulators are what makes the next run slow. Fixed: each simulator is registered right
   after `create`. Test: three sims, the second wedges in `bootstatus`, all three are shut down.
2. **`run_guarded` could block for ever after it had killed Maestro.** It read Maestro's output through a pipe and `communicate()` waits for EOF, not for exit,
   so any process that inherited the pipe and was no longer a descendant (a daemonised helper, an adb server, a driver reparented to launchd) kept the call
   blocked after the kill, and the stall watchdog is gone by then. Measured: a stub whose helper holds the pipe for 8 s made `run_guarded` return after
   8.1 s; it returns in 0.1 s now. Fixed: output goes to a temp file and we `wait()` for the process. The watchdog thread also dies silently on a
   missing `pgrep` or an odd `ps` line (that would disable the stall check for the whole run); it now keeps going.
3. **Two shotfleet runs on one Mac steal each other's devices, and closing the terminal skips all cleanup.** Pool simulators are named
   `shotfleet-<device>-N` and emulators sit on 5702/5704, so a second run reinstalls the app under the first (the 2026-10-03 voided runs). Fixed:
   `device_lock` (an `flock` on `/tmp/shotfleet-ios-<prefix>.lock` and `/tmp/shotfleet-android-emulators.lock`, dropped by the OS when the process dies, so
   there is no stale lock; a second run exits 2 with "another shotfleet run is using these devices (pid, since)"; a lock file that cannot be made does not stop
   the run). SIGHUP (terminal closed, ssh dropped) now cleans up like SIGTERM and Ctrl-C; before, the process died with simulators and emulators running.

## Per-step table

"Today" is the code after this branch; "was" is `main` 4755d1e where it differs.

| Step | Failure mode | Today | Status |
|---|---|---|---|
| Start | Maestro not installed | `load_config` fails with the install command before anything boots | fine |
| Start | Two runs on the same devices | refused by `device_lock` (was: silent stealing) | fixed |
| Boot iOS | `bootstatus` never finishes (900 s limit per sim) | run stops with the simulator named and the `simctl shutdown` fix; was: other booted sims leaked | leak fixed; the whole run still stops (`healthy_installs` only covers install, not boot) |
| Boot iOS | `simctl create` fails, runtime missing | message names the type, runtime and where valid names are listed | fine |
| Boot iOS | a leftover pool sim of another device type | deleted and recreated, so sizes are right | fine |
| Boot Android | emulator exits early | `wait_booted` fails at once with the emulator log tail and a hint (disk, KVM, memory) | fine |
| Boot Android | port 5702 already used | `Fail` "already running, stop it" (racy against a second run; now also locked) | fine |
| Boot Android | boots but package service not up | `Emu.booted` also checks `service check package` | fine |
| Install iOS | install or terminate times out | `healthy_installs` shuts that sim down and carries on with the others; all dead: error | fine; the "restart the Mac" text is also what an invalid `.app` (wrong architecture, device build) produces, after 300 s per sim |
| Install Android | adb times out | was: bare `Command 'adb' timed out after 180 seconds`; now `adb install did not answer within 180 s: emulator-5702 is not responding` and the stop command | message fixed; one emulator still ends the run (no drop-and-carry-on as on iOS) |
| Language switch iOS | none needed: `AppleLanguages`/`AppleLocale` travel as launch arguments of each flow | cannot go wrong per simulator; an app with its own in-app language setting shows the wrong language and `check` says so | fine (check) |
| Language switch Android | `pm clear` then `cmd locale set-app-locales` per emulator before each round | needs API 33+; a failure ends the run with the adb error. A hung emulator: see below | partial |
| Maestro launch | slow driver start with 4 simulators | `MAESTRO_DRIVER_STARTUP_TIMEOUT=240000`; on 2.11.0 two of four drivers still timed out once at low load (2026-10-04, research/maestro-2-11.md) and the retry fixed it | known, cost is one retry; staggering is untried |
| Maestro run | whole process hangs, no output | stall watchdog kills the process tree after `stall_s` (900 s) without a new screenshot; overall `timeout_s` x batches + 300 s is the backstop | fine |
| Maestro run | one shard of four hangs, the other three finish | the watchdog only fires 900 s after the last screenshot of any shard, then everything is killed and the hung shard's languages are retried | costs up to 15 min; could be shorter per shard (remains) |
| Maestro run | 2.11 writes one PNG per step into the debug folder | the stall check treats those as progress, so it really means "no step for 900 s", which is stricter, not looser | fine |
| Maestro run | killed (stall, timeout, Ctrl-C, SIGTERM, SIGHUP) | descendants of Maestro killed from one `ps` snapshot, then orphaned XCTest drivers of our simulators (`kill_stale_drivers`); output no longer blocks the return | fixed (SIGHUP, pipe) |
| Maestro run | `simctl diagnose` after a failed flow wedges CoreSimulator | watchdog kills those started under Maestro | fine |
| Collect | screenshots in two layouts (2.0.x cwd, 2.11 artifact folder) | `collect_shots` moves both into `raw/<locale>/`; the screen texts go with them | fine (e2e on both) |
| Collect | flow passes but takes fewer screenshots, or a blank one | marked failed: "took N of M screenshots" or the blank note | fine |
| Collect | Maestro crashed and wrote no JUnit | the screenshots on disk decide | fine |
| Collect Android | which emulator ran which flow | read from Maestro's own log (`Selected device ... flowsToRun`); a flow with no log line is "never ran" | fine |
| Stale files | Android language that does not run keeps last run's `raw/<locale>` | was: stale screenshots stayed and `check`/`export` (which do not read the per-language `ok` in run.json) could take them as new; now cleared at the start like iOS | fixed |
| Stale files | iOS rerun that fails to boot has already deleted the previous good `raw/<locale>` | unchanged: `raw/<lp>` is cleared before any simulator boots, so a rerun of the same languages that dies at boot loses the last good set | remains (low; moving the clear after a successful boot is small but changes `--locales` semantics) |
| Retry | simulators gone for the retry (iOS) | was: `RuntimeError`, exit 2, no `run.json`, no check; now "not retrying", the first attempt's results are checked and written, exit 1 | fixed |
| Retry | only one retry | by design | fine |
| Android rounds | an emulator stops answering in round k | was: exception, exit 2, no `run.json`, no check, rounds 1..k-1 unreported; now rounds before k are kept, the rest are failed with "not captured: <why>" and exit 1, so `--locales` reruns just those | fixed |
| Cleanup iOS | Ctrl-C, SIGTERM, SIGHUP, normal end | `shutdown_sims` (60 s per sim, only simulators this process registered); a second Ctrl-C during it aborts the rest | fixed (SIGHUP); second Ctrl-C remains |
| Cleanup Android | `adb emu kill` hangs on a stuck emulator | was: the timeout escaped the `finally` and skipped the other emulators; now 30 s per emulator, then the Popen handle's process tree is killed | fixed |
| Cleanup | `kill -9` of shotfleet itself, power loss | simulators and emulators stay up; the flock goes with the process; the next run reuses the sims and says "already running" for emulators | cannot be fixed in the process; remains |
| Interrupt | partial results after Ctrl-C | `raw/` keeps what was captured; no `run.json` for an interrupted run | fine (`shotfleet check <out>` works on `raw/`) |
| Resume | no resume command | rerun `--locales de,ja` for what failed; the failure list is printed and in `run.json` | by design |
| Check | macOS text recognition (ANECompilerService, root) wedged | warm-up has a 600 s limit, each read 120 s x 2, then the message names the stuck service; Tesseract fallback exists. shotfleet never kills it | fine |
| Whole run | no overall wall-clock limit | each step has its own limit (simctl 300/900 s, adb 180 s, Maestro per batch, stall 900 s) but their sum for a bad Mac is hours | remains; a `run_timeout_s` is the obvious knob |

## Fixed on this branch

- `make_pool`: simulators registered for cleanup at once (`shotfleet.py`, test `PoolBoot`).
- `run_guarded`: output through a file, no pipe hang; watchdog survives tool errors (`RunGuarded`).
- `device_lock`: one run per device set; used by `ios_run` and `android_run` (`OneRunPerDeviceSet`).
- SIGHUP handled like SIGTERM (`Cleanup`).
- `stop_emulators`: bounded `adb emu kill`, then the Popen handle's tree (`Cleanup`); `Emu.adb` times out with a named emulator and the fix.
- iOS retry survives "no simulator answers"; Android rounds survive a lost emulator, with partial results and exit 1 (`PartialResults`, `RetryOnSlowSimulator`).
- Android clears `raw/<locale>` for the languages it is about to run.

## What remains

1. Boot-time drop of one dead simulator (as `healthy_installs` does for install): `make_pool` boots all, waits on all, so one wedged boot ends the run.
2. Android has no equivalent of `healthy_installs` (drop a dead emulator and go on with the rest); today a lost emulator ends the capturing, with the partial results kept.
3. Per-shard stall detection, so a hung shard is cut after a few minutes, not 15 after the last screenshot of the others.
4. An overall run limit (`run_timeout_s`) and a message for "every simulator failed to install" that separates a bad `.app` from a wedged CoreSimulator.
5. iOS `raw/<locale>` is cleared before boot (a failed boot loses the last good set).
6. Staggered driver start for 4 simulators on Maestro 2.11.0 (only worth doing if the measurement below shows it matters).
7. A second Ctrl-C while simulators shut down leaves the rest booted.

## What needs real devices to measure

- Whether `bootstatus` of the 2nd simulator can really wedge while the 1st is fine (the leak fix is proven on stubs; how often it happens is not known).
- Whether an orphan holds Maestro's stdout in practice (the pipe fix is proven with a stub helper; no real Maestro or adb server was observed doing it).
- Per-shard hang frequency on 4 simulators, and 2.0.10 versus 2.11.0 driver-start timeouts at 4 simulators (research/maestro-2-11.md says not measured for 2.0.10).
- `adb emu kill` on a hung emulator, and whether the emulator launcher's Popen tree includes the qemu process on macOS and Linux (if qemu is reparented, the kill misses it).
- Whether `pm clear` keeps the runtime permissions that `adb install -g` granted (unknown; the e2e passes, so it does not show on the fixture).
- `flock` on `/tmp` under the packaged, hardened-runtime binary (the code falls back to no lock when `/tmp` is not writable, so it fails open).
- Android API below 33 for `cmd locale set-app-locales`.

Nothing in the release path was touched: no 0.1.1 build, no CHANGELOG edit (another session owns the 0.1.1 heading), no push.
