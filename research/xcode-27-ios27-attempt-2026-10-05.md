# Fixture e2e on an iOS 27 simulator: did not finish in 35 minutes (2026-10-05)

**Result: inconclusive. Not a pass, and not a proven failure.** The same `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios`
passed 36 of 36 on iOS 26.4.1 (2026-10-04, PR #37). On iOS 27.0 (24A434) it passed build, init and doctor and then `shotfleet run`
had not finished when the 35 minute hard limit killed it. The two runs were not made under the same conditions (below), so the
difference cannot be blamed on iOS 27 yet.

## What was run

- Mac: Xcode 27.0 (27A266a), macOS 27.0 (26A428), Maestro 2.0.10, runtime iOS 27.0 (24A434) `CD4542F7-3162-48A0-A78B-620797E51AEE` (Ready).
  The iOS 27 runtime was installed by someone else (not by this run); this run only used it and left it in place.
- Slot script: took the device lock at 10:56:33, ran the e2e (pid 855) from 10:56:37, killed it at 11:33:19 (35 min limit), deleted the
  four `shotfleet-*` simulators it had created (by UDID), left the runtime, released the lock at 11:34:42.
- `latest_ios_runtime()` returned `iOS-27-0` for that run (it picks the last available iOS runtime), so `init` and `run` used iOS 27.

## Conditions, against the iOS 26.4 pass

| | iOS 26.4 pass (2026-10-04 12:33) | iOS 27 attempt (2026-10-05 10:56) |
|---|---|---|
| load average 1/5/15 min at start | 125 / 129 / 117 | **735 / 768 / 710** |
| swap used | 7.3 of 8.2 GB | **21.6 of 22.5 GB** |
| at the end | load 175 / 599 / 587, swap 13.4 of 14.3 GB | load 36 / 109 / **968**, swap 22.4 of 23.6 GB |
| `doctor` | 5 s | **74 s** |
| `shotfleet run` | 988 s, passed | not finished after about 35 min |

The iOS 27 run started at about six times the load and three times the swap. At the end the 1 minute load had fallen to 36 but the
15 minute average was 968: the Mac was extremely loaded for most of the window. Other sessions reported the same condition stalling
simulators ("simulators stop answering") on this Mac.

## Established (from logs and samples)

- Build 7 s, init 1 s, doctor 74 s passed (`xc27-ios27-e2e.log`). The `shotfleet run` line is the last line of that log.
- The Maestro iOS driver was built and started: `xcodebuild` test runs of `maestro-driver-iosUITests-Runner` for two of the four
  simulators (`F1A55A7C…`, `05D63D96…`) are in the unified log at 11:05:31. The last log lines naming those two simulators are at
  11:05:37. About seven minutes after `run` began (about 10:58) is when the driver started: simulator creation, first boot and driver
  build all happen before that.
- Four `shotfleet-*` simulators existed on iOS 27 at cleanup: the two above and `E4DA7C59…`, `E8432EF0…` (no driver lines for these).
- **No `open -a Simulator`.** The once-a-second process sample (10:56:38 to 11:33:23, 1113 samples) contains no `open` process and no
  Simulator.app. `DeviceHub.app` (pid 26391) was running throughout, but it started at 09:24:41, before this run, so this run did not
  launch it. (The sampler's raw log has other sessions' commands that contain the word "open"; they are not Simulator launches.)
- The kill happened inside `shotfleet run`, not inside the Maestro flow of a finished device: no flow output exists (see gaps).

## Not known (do not read these as findings)

- Where exactly `shotfleet run` waited after 11:05:37: simulator boot, the driver's HTTP port, a Maestro command, or the screenshot step.
  The log has `xcodebuild` lines only until 11:05:37; Maestro talks to the driver over HTTP, so silence in that log does not prove a hang.
- Whether iOS 27 itself, Maestro 2.0.10's iOS driver on iOS 27, or only the load caused the stall. A guess: the load and swap alone
  can explain it (other sessions reported simulators that stopped answering on iOS 26.4 at load 140 to 490 and swap 15 to 16 GB), but the 74 s doctor and the missing run output do not exclude
  an iOS 27 problem.
- The IDEFoundation "Unexpectedly found another blueprint for the same blueprintIdentifier" errors at 11:05:31 and the "Error looking for
  performance baseline" line are in the log; whether they matter is unknown (they are Xcode messages; there is no iOS 26.4 extract of the same log to compare with).

## Gaps, why they exist

- No `shotfleet run` output, no Maestro logs or screenshots: the e2e deletes its work dir on exit and the kill counted as an exit;
  Maestro's own `~/.maestro/tests` had no directory for the window. Next time keep the work dir (`--keep`) or use `tools/ios27-repro.sh`,
  which writes everything to one output folder.
- No process sample beyond the Simulator/open watch.

## Next: one minimal repro (`tools/ios27-repro.sh`, not yet run)

One iOS 27 simulator, one language (de), `runtime` pinned to iOS 27 in the config, each step killed at its own limit
(build 90 s, init 60 s, doctor 180 s, run 600 s), 15 minutes in all, a progress sample every 15 s (simulator state, driver
processes, Maestro alive), all output in one folder. Run it on a quiet Mac (load below 60, swap not near full) while holding the device
lock, with Maestro 2.0.10 and, if there is time, 2.11.0 (`REPRO_MAESTRO_BIN_DIR`). Read the result:

- `PASS run exits 0` on a quiet Mac: the stall was load. Then run the full e2e on iOS 27 once, also on a quiet Mac.
- `FAIL run killed at its 600 s limit` on a quiet Mac: an iOS 27 problem. `progress.log` shows whether the simulator booted and
  whether the driver processes were alive; start with the driver's port and boot status.
