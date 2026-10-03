# shotfleet on Maestro 2.11.0

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
- Related: `research/setup-friction.md` proposes a Homebrew formula that pins `cli-2.11.0/maestro.zip`. That pin should wait for the e2e result below. The zip unpacks to `bin/` and `lib/` directly (no `maestro/` wrapper folder), which matches the formula's `Dir["*"]` install.

## Still to do

1. When no other session is using simulators: `PATH=$HOME/.maestro-tests/2.11.0/bin:$PATH SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` (about 17 minutes). Watch for: flows failing with an explicit `launchApp`/`clearState` error, the `Selected device ... using port` line missing from the debug `maestro.log` (then `capture_texts` finds no ports and `check` falls back to OCR), and run time per flow versus 2.0.10.
2. Same for `--platform-only android` if the Android side is to be claimed too.
3. Then make the edit above in one commit.
