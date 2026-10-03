# Compatibility with the tools shotfleet drives

Checked 2026-10-03. "Checked" says how: **real run** means shotfleet ran it end to end on a device, **static** means a program looked at the
tool without running an app, **suite** means the unit tests. Anything not in the table was not checked; `docs/handoff.md` lists what is
left and how to do it.

## Maestro

| Version | What was done | Result |
|---|---|---|
| 2.0.10 | every real run to date (CrossfitTracker 18/18 on iOS and Android, the iOS fixture e2e 36/36, the Android fixture 29/29), plus `tools/maestro-compat.py` | 28/28 static checks. **Tested** (`MAESTRO_TESTED`). |
| 2.11.0 (the newest: 2.11.1, 2.12.0 and 3.0.0 do not exist as of 2026-10-03) | `tools/maestro-compat.py`, run on the real download (SHA-256 5384593c...e1283a, matches the release's own checksum file) on Linux; the changelog read from 2.1 to 2.11 in `research/maestro-2-11.md` | 28/28 static checks. **No device run**, so not in `MAESTRO_TESTED`: doctor says "may work". |

`tools/maestro-compat.py [folder]` checks any Maestro against `shotfleet.MAESTRO_INTERFACE`, the one list of what shotfleet relies on:
`--version` parses; `maestro --device` and `maestro test --shard-split --format --output --debug-output` exist and `--format` offers JUNIT; the
jars still hold the log line shotfleet parses to learn which emulator ran which flow (`Selected device ... using port ... with execution plan
ExecutionPlan(flowsToRun=`), `maestro.log`, the two environment variables shotfleet sets, and the thirteen flow keys it writes. A unit test
fails if that list stops matching what `shotfleet.py` passes. Run it first whenever a new Maestro appears:

```bash
python3 tools/maestro-compat.py ~/.shotfleet/maestro      # or any unpacked Maestro folder; exit 1 if something required is gone
```

What it cannot tell: whether the sharded parallel runs behave (Maestro 2.6.0 changed parallel iOS handling), whether `launchApp`/`clearState`
errors that 2.7.0 stopped swallowing now fail a flow that used to pass, or how long a run takes. Those need the device run.

**A finding worth acting on:** 2.11.0 defines `MAESTRO_DEVICE_UDID` (in `maestro/orchestra/util/Env.class`); 2.0.10 does not. shotfleet's
Android `[inputs.<locale>]` support already keys on that variable and was written for exactly this, so per-language typed text on Android may
work on 2.11.0. Not run on a device; the value Maestro puts in it (the adb serial, which is what shotfleet's script expects) is unconfirmed.

## Other tools

| Tool | Versions | How | Result |
|---|---|---|---|
| Python | 3.11, 3.12, 3.13 | suite (658 tests on 2026-10-03, 41 skipped as Mac-only) with deprecation warnings as errors, run on each of 3.11, 3.12 and 3.13 after the docs audit; CI runs 3.11 and 3.13 on Linux, 3.12 on macOS | pass |
| Python | 3.10 | run | refuses with "shotfleet needs Python 3.11 or newer" |
| Python | 3.14.0rc2 | suite (595 tests) with deprecation warnings as errors | pass; the final 3.14 release is not out, so not in CI yet |
| Java | Temurin 21.0.12.1 (from `doctor --fix`), openjdk 21.0.11 | ran Maestro 2.0.10 and 2.11.0 and Google's sdkmanager | works |
| Android SDK | command-line tools 23.0, platform-tools 37.0.1, emulator 37.2.12, build-tools 36.0.0, API 36 `google_apis` x86_64 | installed by `doctor --fix` on Linux; `doctor` saw all of it | install and detection work; **the emulator was never started** (no hardware virtualization) |
| Flutter | 3.47.6 stable | built a 3-language app with `gen_l10n`; `init` found the APK and ARB files; wger's real ARB files read | works up to the build; no device run. 3.47 writes generated localizations next to the ARB files, not into `flutter_gen`. |
| Expo / React Native | `create-expo-app` as of 2026-10-03 (SDK number not recorded) | built a release APK with i18next + expo-localization; `init` found it | works up to the build; no device run |
| Kotlin Multiplatform | JetBrains/kotlinconf-app (clone only) | detection | works after a fix |
| Licence calls through an HTTPS-re-signing proxy | this sandbox's | real handshake, aimed at a harmless URL, no key | fails without `SSL_CERT_FILE`, works with it |
| Google Android command-line tools | 23.0 (`sdkmanager` prints "deprecated, Android CLI will be used instead"), Android CLI 1.0.16500706 | `doctor --fix` on a bare Linux machine and on a GitHub runner; `android --no-metrics sdk install` checked against the real tool | works after two fixes (dotted SDK path; usage reporting). **Risk:** `sdkmanager` is a deprecated shim; if Google removes it, `doctor --fix` and the printed `sdkmanager` commands in `doctor` need to move to `android sdk install` |
| Apple App Store screenshot sizes | Apple's specification page, read 2026-10-03 | `tools/apple-specs-watch.py` on the real page: 45 distinct sizes; table matches after adding iPhone Duo and four old-device landscape sizes | match; re-run monthly with `tools/watch-upstream.sh` |
| Xcode 27 final (Device Hub replaces Simulator.app) | read in code, no run | shotfleet itself only calls `xcrun simctl` (list, create, delete, boot, bootstatus, status_bar, install, shutdown, help, plus the user's own `[ios] simctl` commands) and never `open -a Simulator`. Maestro 2.0.10 and 2.11.0 both contain `open -a .../Simulator.app --args -CurrentDeviceUDID` in `LocalSimulatorUtils.launchSimulator`, reachable only from `DeviceService.startDevice` (`maestro start-device` and the interactive device picker); shotfleet boots its own simulators and gives Maestro their ids, so that path should not run | **inference, not proved**; other tools broke on exactly this call (expo/expo#46671, callstackincubator/rock#731, anthropics/claude-code#95085). Needs the fixture e2e on a Mac with Xcode 27 |
| Tesseract | 5.3.4 | `check` on rendered screenshots on Linux (de, ja, en data) | works |
| Xcode, iOS Simulator runtimes, macOS | not checked in this environment | | see `docs/handoff.md` |

## When a new version of a tool appears

1. **Maestro:** `tools/watch-upstream.sh` (about monthly, and before a release) fetches the newest stable release and screens it, together with Apple's size table. By hand:
   `python3 tools/latest-maestro.py`, or `python3 tools/maestro-compat.py <folder>` for a copy you already have. All green means "worth a real run", not "supported".
2. **Python:** add it to the `linux` matrix in `.github/workflows/ci.yml` as soon as `actions/setup-python` has it.
3. **Android SDK / Java / Flutter / Expo:** `shotfleet doctor --fix` in a fresh `SHOTFLEET_HOME` and `ANDROID_HOME` fetches the current Android
   tools; `init` in a freshly built sample project shows whether the build still lands where `detect_project` looks.
4. **Promoting a Maestro version** to "tested" is a code change in several places, listed in `docs/handoff.md` under item 1.
