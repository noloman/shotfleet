# shotfleet on Maestro 2.11.0

**Current state (2026-10-04): 2.11.0 passes the fixture e2e and is in `MAESTRO_TESTED`; see the last section. The sections in between are the history: the first device run failed on `takeScreenshot` paths and was fixed.**

Date: 2026-10-03. Short version: nothing found so far that breaks shotfleet on Maestro 2.11.0, but the iOS end-to-end run did not happen, so 2.11.0 is not "tested" yet. Do not add it to `MAESTRO_TESTED` until that run passes.

## What was done

- Version: Maestro CLI 2.11.0 (released 2026-09-29, the latest 2.11.x; there is no 2.11.1).
- Downloaded `maestro.zip` (314,886,578 bytes) from the official GitHub release `cli-2.11.0` in mobile-dev-inc/maestro.
- Checksum: the release publishes `checksums_sha256.txt`. The SHA-256 of the download is 5384593c...e1283a, identical to that file and to the digest GitHub shows for the asset.
- Unpacked into `~/.maestro-tests/2.11.0/` (`bin/`, `lib/`). `~/.maestro` was not touched: `maestro --version` still prints 2.0.10 on the normal PATH, and `~/.maestro-tests/2.11.0/bin/maestro --version` prints 2.11.0.
- The new Maestro was only put first on PATH for single commands.

## Results per step

1. Download, verify, unpack, `--version`: pass.
2. Changelog read (2.1 to 2.11): see the table below. No breaking change found for the parts shotfleet uses.
3. Device-free checks with 2.11.0 first on PATH:
   - `python3 -m unittest discover -s tests -k Maestro`: 13 tests, OK (1 skipped).
   - `shotfleet.py doctor`: prints `ok   maestro 2.11.0 (tested: 2.0.10)` and then
     `note: Maestro 2.11.0 is not the version shotfleet was tested with (2.0.10); it may work`. Everything else is ok, "iOS: ready   Android: ready". Doctor does not block, which is the right behaviour.
4. iOS fixture e2e (`SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios`): NOT RUN. When I checked, `xcrun simctl list devices booted` showed another session's simulators (paid-review-iphone and four shotfleet-ipad-pro-13-inch-m5-12gb-N), and the coordinator then said another session is running `tools/fixture-e2e.sh` on iOS right now (Mac load about 750). The e2e for Maestro 2.11 is pending. No simulator was booted, shut down or deleted by this work. (`ps aux | grep qemu` showed 0 emulators, so Android was free, but the task asked for the iOS e2e only and no Android run was done.)

## What changed between 2.0.10 and 2.11.0 that touches shotfleet

| shotfleet uses | Change in Maestro | Evidence | Risk |
|---|---|---|---|
| `maestro --device A,B test ... --shard-split N --format JUNIT --output --debug-output` | All flags still exist in 2.11.0 (`maestro test --help`, `maestro --help`). `--flatten-debug-output` is new and optional. | help output | low |
| Parse of `Selected device X using port N with execution plan ExecutionPlan(flowsToRun=[...]` in `maestro.log` (`capture_texts`) | The log format string in `MaestroSessionManager` is byte-identical in the 2.0.10 and 2.11.0 CLI jars, and `ExecutionPlan(flowsToRun=` is still in maestro-orchestra. | strings from both jars | low, but only a real run proves the line is written to `maestro.log` |
| `rglob("maestro.log")` under `--debug-output` | 2.7.0 revamped the per-flow artifact bundle (flat, manifest, screenshot before every step, device logs). `/maestro.log` is still a path in the 2.11.0 CLI, and 2.7.0 notes "capture `maestro.log` even when the host disables logging additivity". Nested layout is still the default; flattening is opt-in. | changelog, jar strings | low (rglob is layout-proof) |
| Extra PNG per step in the debug output | 2.7.0. shotfleet reads screenshots from `raw/<locale>/`, not from the debug dir, but disk use and time per flow may rise. | changelog | low, measure in e2e |
| `MAESTRO_DRIVER_STARTUP_TIMEOUT=240000` | Variable still read by maestro-client and maestro-ios-driver in 2.11.0, same message text as 2.0.10. | jar strings | none |
| Sharded parallel iOS runs | 2.6.0 "Enable parallel iOS simulator execution with per-device session tracking". This is the real unknown: shotfleet's workaround for the old single-process limit (and `kill_stale_drivers`, port 7001 comment) was written for 2.0.10 behaviour. It may now be unnecessary or interact differently. | changelog | medium, only the e2e can settle it |
| Driver leftovers | 2.7.0 "clean up leftover driver files on simulators after runs", 2.6.0 XCTest logs added to debug output. | changelog | low |
| `launchApp`, `clearState` | 2.7.0 "surface errors from `launchApp`, `setPermissions`, `clearState` instead of swallowing them". A flow that quietly passed before may now fail loudly. 2.1.0 added `setPermissions` command; `launchApp` options unchanged. | changelog | low to medium |
| `inputText` with non-Latin text | Android Unicode input is first-party since 2.7.0 (limits-text.md section 2 already says "Android non-ASCII needs 2.7.0+"). | changelog | positive |
| `--device-os`, `--ios-version` | 2.4.0 deprecated `--ios-version`/`--android-api-level`. shotfleet does not pass them. | grep of shotfleet.py | none |
| `takeScreenshot` | 2.8.0 fixes `..` in paths and rejects a path that names a directory; 2.1.0 creates missing folders. | changelog | low |
| Analytics/update notices | `MAESTRO_CLI_NO_ANALYTICS=1` is still set by shotfleet; Maestro Studio was removed from the CLI in 2.6.0 (not used). | changelog | none |
| Physical iPhones | 2.11.0 stops listing them. shotfleet only uses simulators. | changelog | none |

Known risk list in `research/limits-text.md` section 1e (layout change, one PNG per step, parallel iOS in 2.6.0, "re-run the whole suite on the new version before shipping") is confirmed as the right list. Nothing new was found beyond the stricter `launchApp`/`clearState` error handling.

## Does the doctor or README need a change

No code change is needed.

- Doctor already treats a newer Maestro 2.x as installed, shows the version, and adds a one-line "not the version shotfleet was tested with; may work" note. That is accurate today, because 2.0.10 is the only version a real run used. Changing `MAESTRO_TESTED` now would claim something that has not been shown; `tests/test_doctor_versions.py` also pins it to `("2.0.10",)`.
- After the iOS e2e passes (and ideally the Android one), the small edit is: `MAESTRO_TESTED = ("2.0.10", "2.11.0")` in `shotfleet.py` (line 2066), update the assertion in `tests/test_doctor_versions.py` line 48, the README line 287 ("Maestro (tested with 2.0.10)") to "tested with 2.0.10 and 2.11.0", and the matching assertion in `tests/test_agent_skills.py` line 236.
- Related: `research/setup-friction.md` proposes a Homebrew formula that pins `cli-2.11.0/maestro.zip`. That pin should wait for the e2e result below. (Corrected 2026-10-03: the 2.11.0 zip, like 2.0.10's, has a single top folder `maestro/` holding `bin/` and `lib/`; `doctor --fix` handles that layout and the one without it.)

## Still to do

1. When no other session is using simulators: `PATH=$HOME/.maestro-tests/2.11.0/bin:$PATH SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` (about 17 minutes). Watch for: flows failing with an explicit `launchApp`/`clearState` error, the `Selected device ... using port` line missing from the debug `maestro.log` (then `capture_texts` finds no ports and `check` falls back to OCR), and run time per flow versus 2.0.10.
2. Same for `--platform-only android` if the Android side is to be claimed too.
3. Then make the edit above in one commit.

## Addendum 2026-10-03: a repeatable static check

`tools/maestro-compat.py <maestro folder>` now runs the device-free part of this analysis against any Maestro, from the list in
`shotfleet.MAESTRO_INTERFACE`. Results on real downloads, on Linux: **2.0.10: 28 passed, 0 failed; 2.11.0: 28 passed, 0 failed.** 2.11.1,
2.12.0 and 3.0.0 do not exist yet (release URLs return 404). One difference between the two that matters: **2.11.0 defines
`MAESTRO_DEVICE_UDID`**, 2.0.10 does not (see `docs/handoff.md` item 5). The device runs under "Still to do" above are unchanged and are
item 1 of `docs/handoff.md`, which also lists the exact edits to promote 2.11.0 to tested.

## Real device run, 2026-10-03 (evening): 2.11.0 FAILS, do not promote

Run on the Mac (Apple silicon, Xcode, iOS 26.4 simulators, Android emulator `shotfleet_android`) with the 2.11.0 download first on PATH
(`maestro --version` printed 2.11.0; SHA-256 5384593c...e1283a, 314,886,578 bytes; `~/.maestro` still 2.0.10). Repo at `main` 4d5d642.
`python3 tools/maestro-compat.py` on that download: 28 passed, 0 failed (as before). Both fixture e2e runs started from a quiet shotfleet
pool (no shotfleet simulators or `emulator-57xx` up; another session's idle `paid-review-iphone` and `emulator-5562` were left alone).

| Command | Result |
|---|---|
| `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` | exit 1 after 636 s, **FAIL: 25 of 36 assertions failed** (2.0.10: 36/36) |
| `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android` | exit 1 after 164 s, **FAIL: 19 of 29 assertions failed** (2.0.10: 29/29) |

Only the build, `init`, `doctor` and the few assertions that do not need screenshots passed. `shotfleet run` captured 0 of 4 locales on
every device (iPhone, iPad, Android phone), so `check`, `export` and everything that reads screenshots failed after it. Nothing else differed:
the assertion list of failures is the same set (screenshots missing, `check.json` missing, `after_run` hook `exit=1`, export folders empty).

### The one cause

Every flow fails at its first `takeScreenshot` step, 8 to 9 seconds in, with:

```
Invalid path "/private/var/folders/.../proj/out/iphone-17-pro-max/raw/de/01_welcome.png" for takeScreenshot: it resolves outside this run's
takeScreenshot output folder. If the path comes from a variable, check what it expands to.
```

Android is identical, with the path `.../proj-android/out/phone/.work/tmp/retry1/f0/01_welcome.png`. The text is in `maestro-orchestra.jar`
(next to `TAKE_SCREENSHOT_DIR`). 2.11.0's `maestro test --help` says `--test-output-dir` is "Directory for this run's artifacts: manifest.json,
commands.json, logs/, takeScreenshot/ and startRecording/ written directly into it". So since the 2.7.0/2.8.0 artifact rework, `takeScreenshot`
may only write inside `<test output dir>/takeScreenshot/`, and an absolute path elsewhere is rejected. shotfleet's generated per-locale flows
give `takeScreenshot` an absolute path under `raw/<locale>/` (iOS) or `.work/tmp/retryN/fK/` (Android), outside that folder. This is a
shotfleet/Maestro interface change, not load: the note shotfleet prints ("this Mac was short of memory...") is its generic hint and does not
apply (load was 4.8 at the start, and the failure is identical on all four shards and both platforms). My earlier research table rated the
2.8.0 `takeScreenshot` change "low"; that was wrong.

A possible way forward (not tried, no code was changed): give each Maestro run its own `--test-output-dir`, let the flows use bare names
(`takeScreenshot: 01_welcome`, which is what the user's `flow.yaml` has), and copy `<dir>/takeScreenshot/<name>.png` to
`raw/<locale>/<name>.png` after the run. That must keep working on 2.0.10, which has no `--test-output-dir`, so it needs a version gate or the
flag detected from `maestro test --help`. `MAESTRO_INTERFACE` and `tools/maestro-compat.py` should also learn to grep for the "resolves outside
this run's" string so the static check would have caught this.

### The other watch items from the risk table

- **`Selected device ... using port` line:** present in every debug `maestro.log` (e.g. `[shard 1] Selected device 1D26F129-... using port 63038
  with execution plan ExecutionPlan(flowsToRun=[...`). `capture_texts` would find its ports; no OCR fallback needed for this reason.
- **Sharded parallel iOS runs:** four shards on four simulators started in the same millisecond and each ran its flow independently (shard 1
  to 4, one device each). They behaved; the failures were all the `takeScreenshot` path, none a shard or port problem. Not a full proof,
  because no flow got past its first screenshot.
- **`launchApp` / `clearState` failing loudly (2.7.0):** not seen. Each flow got past `launchApp` and `waitForAnimationToEnd` and failed at
  `takeScreenshot`. `clearState` is not exercised before that point in this fixture.
- **Run time per flow vs 2.0.10:** not comparable; flows stop at 8 to 9 s. `doctor` took 64 s, `run` 568 s for iPhone plus iPad (all retries).
- **Android `[inputs.<locale>]` with `MAESTRO_DEVICE_UDID`:** not tested, because no Android flow reaches a screenshot. Still open.

### Consequences

`MAESTRO_TESTED` stays `("2.0.10",)`, nothing was promoted, no PR. `doctor` saying "may work" for 2.11.0 is now known to be wrong for any
shotfleet run: it does not work until the `takeScreenshot` handling above changes. Same for `doctor --fix` pinning (it still installs 2.0.10)
and the Homebrew formula idea in `research/setup-friction.md`: do not pin 2.11.0.
Evidence kept (not in the repo): `/private/tmp/claude-501/.../scratchpad/m211/{ios-evidence,android-evidence,e2e-ios.log,e2e-android.log}`.

## Fix and passing device runs, 2026-10-04 (night): 2.11.0 is tested

**What was changed.** Flows now name screenshots relative to Maestro's working directory (`takeScreenshot: de/01_welcome`; on Android `<tag>_f<j>/01_welcome`)
and Maestro runs with a per-attempt working directory. Probed on a throwaway iOS 26.4 simulator with the real downloads: 2.0.10 writes the file
under that directory (`<cwd>/de/01_welcome.png`); 2.11.0 writes it under `<--debug-output>/.maestro/tests/<run>/<flow>/takeScreenshot/de/01_welcome.png`
(or `<--test-output-dir>/<run>/<flow>/takeScreenshot/...`). `ArtifactCollector.confinedTo` in `maestro-orchestra.jar` checks
`artifactsDir.resolve(name).normalize().startsWith(artifactsDir)`, which is why an absolute path elsewhere fails and a relative one passes. `collect_shots()`
moves the files of either layout into `raw/<locale>/` after the run, and `capture_texts()` also watches 2.11.0's folder so the live screen-text capture works.
No version gate and no new flag, so the command line is unchanged.

**Results** (fixture e2e, same machine, the device lock held, `tools/fixture-e2e.sh --platform-only ios|android`):

| Maestro | Platform | Result | Time | Load / free memory / pressure at start |
|---|---|---|---|---|
| 2.11.0 | iOS | all 36 assertions passed | 344 s | 78 / 45% / level 2 |
| 2.11.0 | Android | all 29 assertions passed | 148 s | 765 / 52% / level 1 |
| 2.0.10 | iOS | first run: 11 of 22 failed, **not a Maestro result**: `simctl terminate did not answer within 300 s` (a simulator hung, load ~500) before Maestro started. Rerun: all 36 passed | 420 s (failed), 527 s (rerun) | 135 / 54% / 1 (failed); 51 / 50% / 2 (rerun) |
| 2.0.10 | Android | all 29 assertions passed | 99 s | 499 / 61% / 1 |

Unit tests: 5 new, the full suite passes. The Mac was shared with other sessions' builds and emulators (load 50 to 760), so the times are not a
2.0.10 versus 2.11.0 comparison; at memory-pressure level 2 shotfleet also halves its simulator count.

**The other watch items, now answered.** `Selected device ... using port` is written to `maestro.log` (seen in every debug log). Sharded parallel iOS
runs on 2.11.0 worked: 36/36 on the iOS fixture, which runs four languages sharded over the simulator pool. No `launchApp`/`clearState` failure.

**Not done.** CrossfitTracker/Remoti on 2.11.0 (`docs/handoff.md` item 6).

## Android `[inputs.<locale>]` on 2.11.0, 2026-10-04: works (one emulator)

Scratch copy of `tools/fixture-app-android` with a "Name" text field added (not in the repo), flow `tapOn: "Name"`, `inputText: ${name}`, `hideKeyboard`,
`takeScreenshot: 01_input`; config `[inputs] name = "Alex"`, `[inputs.de] name = "Jürgen Müller"`, `[inputs.ja] name = "田中太郎"`; `shotfleet run --locales de,ja`
on Maestro 2.11.0 (device lock held; load 94, free memory 47%, memory pressure level 2, 17 GB free disk). Result: exit 0, both languages captured,
`MAESTRO_DEVICE_UDID` = `emulator-5702` (the adb serial shotfleet's script keys on; Maestro's command log shows it), and the screenshots show
**"Jürgen Müller"** in the German UI and **"田中太郎"** in the Japanese one (Maestro 2.11 types non-Latin text on Android). No `no row for device` fallback.

**Limit.** Memory pressure was at level 2, so shotfleet used **one** emulator instead of two (`memory pressure is elevated: using 1 devices instead of 2`):
German and Japanese ran one after the other on the same emulator. That proves the variable's value and the typing; it does not exercise two emulators
at once (where Maestro hands the flow to either emulator and the per-round map picks the row by serial; that map is unit-tested and the same
log-based mapping is what the fixture e2e relies on for screenshots). Arabic typing was not tried. The user-facing wording says exactly this.
