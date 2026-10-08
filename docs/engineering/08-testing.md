# 8. Testing and verification

Scope: how shotfleet is tested and what each kind of test proves: the unit suite in `tests/`, the doc and site guardrails, the two fixture apps and the device scripts that drive them (`tools/fixture-e2e.sh`, `tools/fixture-byoc-e2e.sh`), the helper tools in `tools/`, the Maestro compatibility matrix and why 2.0.10 and 2.11.0 are the tested pair, the protocol for sharing one Mac's simulators between agent sessions, Android emulators on Linux (KVM), the iOS 27.0 simulator hang, CI policy, and the known-flaky and slow cases. Written on 2026-10-08 against the repository at version 0.1.7 (commit `7e5176c`; the live site runs 0.1.6). Every statement was checked against the files; where a statement could not be checked it says "not verified" and names the file that is the only source. Claims register mechanics and the release gate are in [06-packaging-and-release.md](06-packaging-and-release.md); the website in [07-website-and-backend.md](07-website-and-backend.md); the code under test in [01-runtime-architecture.md](01-runtime-architecture.md), [02-capture-and-devices.md](02-capture-and-devices.md) and [03-check-ocr-export.md](03-check-ocr-export.md). Support-side use of these tools is in [09-operations-and-support.md](09-operations-and-support.md), how to change code and tests together in [10-contributing.md](10-contributing.md), why things are the way they are in [11-history-and-decisions.md](11-history-and-decisions.md). Index: [README.md](README.md).

## 8.1 The layers at a glance

| Layer | What it proves | Needs | Cost | Where |
|---|---|---|---|---|
| Unit | the program's functions and CLI against fakes for simulators, emulators, Maestro, Xcode, Gradle, the network and text recognition | Python 3.11+ (`shotfleet.py:15` refuses older); Mac-only tests skip elsewhere | seconds to about a minute for the whole suite (8.3) | `tests/test_*.py` (51 modules) |
| Doc and site guardrails | the site, README, docs page, skills, `llms.txt` and a few docs say what the program really does | Python; Node for the worker tests; Playwright + Chromium optional | part of the same run | 8.6 |
| Worker tests | the Cloudflare Worker (`/api/*`) with an in-memory KV and limiter | Node (CI uses 22; the dev Mac has 26.10.0) | well under a second per check | `site/worker.test.mjs` |
| Device-free script tests | the shell scripts (`fixture-e2e.sh`, `selftest.sh`, `publish.sh` and others) against fake `xcrun`, `adb`, `wrangler`, `notarytool` | Python, `sh`; some Mac-only | in the unit run | `tests/test_fixture_e2e.py`, `test_selftest.py`, `test_release_scripts.py`, `test_golive.py`, `test_release_candidate.py` |
| Static Maestro screen | a Maestro install still has every flag, log line, variable and flow key shotfleet uses | a Maestro folder and Java | seconds | `tools/maestro-compat.py` (8.11, 8.12) |
| Fixture end to end | the real program on real simulators and emulators against the two fixture apps | a quiet Mac with Xcode (and the Android SDK for Android), the device queue (8.13) | 6 to 17 minutes per platform (8.9) | `tools/fixture-e2e.sh`, `tools/fixture-byoc-e2e.sh` |
| Release proofs on the built bytes | signature, notarization, `env -i` start, TLS, licence against a fake Gumroad, `install.sh` | a build and a Mac | minutes | `tools/release-candidate.sh`, `tools/verify-release.sh`, `tools/selftest.sh` (06) |
| Real apps | a third-party app end to end (CrossfitTracker, wger, the obytes template, kotlinconf-app) | the apps and a quiet Mac | 10 to 30 minutes each | not automated; recorded in `research/` and `docs/compat.md` |

Rule of the repository (`docs/handoff.md:5`, `shotfleet.py:3915`): nothing is called "tested" without a run that passed. The unit suite cannot promote anything to "tested"; only a device run can.

## 8.2 Cheat sheet

All commands are run from the repository root. "Safe" means: no simulator, emulator or Maestro process is started and nothing outside a temp folder is written.

| I want to | Command | Safe on the shared Mac? |
|---|---|---|
| run everything the gate runs | `sh tools/check-claims.sh > /Users/manu/Developer/shotfleet-rc-build/<name>.out 2>&1; echo rc=$?` (push only when `rc=0`; never `... \| tail -1; git push`) | Yes, but it adds load (it runs half the cores' worth of processes at once); see 8.17 |
| run one module | `python3 -m unittest tests.test_docs` | Yes |
| run one class or one test | `python3 -m unittest tests.test_shotfleet.Licence` / `...Licence.test_name -v` | Yes |
| run tests by name pattern | `python3 -m unittest discover -s tests -k Maestro` | Yes (used in `research/maestro-2-11.md`) |
| run a module as if on an Apple-silicon Mac | `python3 tools/pretend-mac.py test_doctor_fix` (module name without `tests.`) | Yes |
| run the module the way Linux CI does | `python3 -W error::DeprecationWarning -m unittest discover -s tests` (`.github/workflows/ci.yml:29`) | Yes |
| run the worker tests | `node site/worker.test.mjs` (exit 0 only if every `ok` line passed) | Yes |
| run the browser tests | `node tests/browser_site.cjs` (exit 77 = Playwright or Chromium missing) | Yes (local server only) |
| screen a Maestro install | `python3 tools/maestro-compat.py <folder with bin/ and lib/>` | Yes (runs `maestro --version` and `--help`, reads jars) |
| screen the newest upstream Maestro and Apple's size table | `sh tools/watch-upstream.sh` | Network, downloads about 315 MB unless that version already passed |
| enable the pre-commit check once per clone | `git config core.hooksPath .githooks` (the hook just runs `tools/check-claims.sh`) | Yes |
| syntax-check a shell script | `sh -n tools/fixture-e2e.sh` | Yes |

Do not run these on the shared Mac without the device queue (8.13) and a quiet-Mac check; every one of them boots simulators or emulators or builds heavily:

| Command | Why |
|---|---|
| `SHOTFLEET_E2E=1 tools/fixture-e2e.sh ...` | boots up to 4 simulators per device type and, with `--android`, 2 emulators (script header, lines 8-10) |
| `SHOTFLEET_E2E=1 tools/fixture-byoc-e2e.sh` | boots 2 simulators and builds an Xcode project |
| `IOS27_REPRO=1 tools/ios27-repro.sh` | boots one iOS 27 simulator |
| `shotfleet run ...`, `maestro ...`, `emulator ...` by hand | they are device jobs (`docs/device-queue.md:7-8`) |
| `SHOTFLEET_RC=1 tools/release-candidate.sh` | PyInstaller build of hundreds of MB, several minutes, needs pip's network (script header). No device, but heavy. |
| `tools/selftest.sh --download`, `tools/golive/smoke.sh <url>`, `tools/status.sh` | network (the live site / GitHub) |
| GitHub Actions workflows | cost money; never trigger them to "see if CI passes" (8.16) |

The guards are real: the device scripts refuse without `SHOTFLEET_E2E=1` (`tools/fixture-e2e.sh:34-38`, `tools/fixture-byoc-e2e.sh:29-33`), `IOS27_REPRO=1` (`tools/ios27-repro.sh:13`), `SHOTFLEET_RC=1` (`tools/release-candidate.sh`). The opt-in stops accidents; it does not replace the queue.

## 8.3 `tools/check-claims.sh`: what the gate runs

Description only; it was not run to write this chapter.

1. Creates a temp folder, `cd`s to the repo root (`tools/check-claims.sh:6-7`).
2. Lists `tests/test_*.py` largest file first (`ls -S`, line 11) and runs each module as its own process with `xargs -P <jobs>` (`python3 -m unittest discover -s tests -p <module>.py`). `jobs` is `CHECK_JOBS` or half the online cores (line 8), because most of the time is spent waiting for subprocesses, not on CPU. One process per module also keeps modules that patch module-level state (8.4) from affecting each other.
3. Sums the `Ran N tests` lines and the `OK`/`FAILED (...)` summaries of all modules with awk.
4. Runs `node site/worker.test.mjs` last (line 26) and counts its `ok ` and `FAIL ` lines. If Node is missing the script fails; it does not skip.
5. Prints one line and exits 0, or prints every module's full output and exits 1:
   `check-claims: ok (python: Ran <N> tests in <S>s OK (skipped=<K>); worker: <M> checks ok)`.

Who runs it: `.githooks/pre-commit` (after `git config core.hooksPath .githooks`), `packaging/release.sh:11` (refuses to build if it fails), `packaging/go-live.sh:128`, a human, and `.github/workflows/ci.yml` (manual only).

Numbers, with their dates (they grow with the suite):

| Fact | Value | Source |
|---|---|---|
| test modules | 51 | `ls tests/test_*.py`, 2026-10-08 |
| `def test_` occurrences | 1,230 | `grep -c`, 2026-10-08 |
| test cases the loader finds | 1,247 (loaded, not run; 17 more than the `def test_` count because `UpdateWindow` in `tests/test_shotfleet.py` subclasses `GumroadLicence` and so runs its 17 tests again: 29 collected against 12 defined) | `unittest.TestLoader().discover('tests')`, 2026-10-08, Python 3.14.8 |
| whole-gate time | 52 to 69 s on 2026-10-07, 10-core Mac busy with other jobs (load over 70) | `TESTING.md:3` |
| earlier figures | 91 s for 1,184 tests plus 59 worker checks at `285e099` on 2026-10-06 (load about 500) | `docs/architecture/13-mismatches.md:11` |
| worker checks | 59 at `285e099` (2026-10-06); the file has 37 `check(` call sites today, some in loops, so today's count is not verified | `docs/architecture/13-mismatches.md:11`, `site/worker.test.mjs` |
| a slice I ran on 2026-10-08 | `tests.test_latest_maestro tests.test_maestro_compat tests.test_doctor_versions`: 36 tests in 5.1 s, OK, 1 skipped | this chapter's author |
| the full suite today | not run for this chapter; whether it is green at `7e5176c` is not verified here | |

## 8.4 How the unit tests are built

- **Import style.** Tests `import shotfleet as sf` and patch names on `sf`. Most modules do `sys.path.insert(0, repo_root)` and some also `tests/`, so `python3 -m unittest tests.test_x` (from the root) and `discover -s tests` both work. There is no `tests/__init__.py`.
- **Cross-module imports.** Several modules import helpers or whole test classes from others: `test_capture_reliability` imports `FleetCase` from `test_claims_unit`; `test_free_tier_message` imports `FleetCase`, `Reply`, `gumroad_answer`; `test_json_multi_report` and `test_upload_gate_017` import `G1_*` helpers from `test_shotfleet`; `test_latest_maestro` imports `Server` from `test_doctor_fix` and `fake_maestro` from `test_maestro_compat`; `test_docs` and `test_claims_site` import `Page`, `BANNED`, `PAGES` from `test_site`. Consequences: importing a module runs its top level (including its `USE_DEVICE_LOCK` line, next bullet). Imported helper classes such as `FleetCase` have no tests of their own, so nothing is collected twice that way; the only inflation of the case count is the `UpdateWindow(GumroadLicence)` subclass (8.3).
- **Global state set at import.** `test_shotfleet`, `test_claims_unit`, `test_first_run`, `test_byoc_ios`, `test_release_candidate` and `test_reliability_017` set `sf.USE_DEVICE_LOCK = False` at import (`tests/test_shotfleet.py:12`, `test_claims_unit.py:16`, ...), so fake runs never take the real `/tmp/shotfleet-<key>.lock` (`shotfleet.py:1977-1993`) and two suites at once cannot refuse each other. The tests of the lock itself turn it back on for their class with `mock.patch.object(sf, "USE_DEVICE_LOCK", True)` (`test_capture_reliability.py:47`, `test_security.py:138`) and use unique per-process keys (`test-<pid>`, `secrevtest-<pid>`) and delete their lock files, so they cannot collide with a real run. `test_reliability_017.py:10` is the 0.1.7 fix for a real run holding the iOS lock making these tests fail (release commit `7e5176c`).
- **Own copy of the program.** `test_ocr_wait.py:10-12` loads `shotfleet.py` as a second module object and points `OCR_LOCK` at a temp file, so a real shotfleet on the same Mac never waits on the tests.
- **Skips are by design.** Reasons found in the code: `aapt2` missing (`test_android_apk.py:20`); Node missing (`test_claims_site.py:235,371`, `test_limits_c2_c3.py:167,173`); Playwright or Chromium missing (`tests/browser_site.cjs` exits 77, the Python test skips); not macOS (`needs_mac` in `test_shotfleet.py:14` used on 26 tests, `test_golive.py` on 5, `test_reliability_017.py:12` on the class `IosRetries`, `test_selftest.py`, `test_fixture_e2e.py:306`, `test_release_candidate.py:181`); `javac`, `keytool`, SDK build-tools or `android.jar` missing (`test_fixture_e2e.py:17`); Tesseract without English and Japanese data (`test_claims_unit.py:510`); a real `maestro` on this machine (`test_doctor_versions.py:102`); macOS text recognition not answering within 90 s (`test_cli_claims.py:349-352`); the site already live, so waitlist-only checks skip (`LIVE` in `test_site.py:22`, `test_golive.py:16`, `test_site_audit.py:17`, `test_claims.py:19`). A skip is not a pass for what it covers: run the matching device or Mac step when you change that area.
- **Real macOS text recognition.** One test runs it for real: `RealVisionSmoke` (`test_cli_claims.py:344-357`, builds the Swift OCR helper with `swiftc`, draws "EEE", reads it). Every other test stubs it with `fake_vision()` (`test_cli_claims.py:31`). `research/speed-2026-10-05.md:85` lists a few other calls to the real helper as of that date (some tests in `test_shotfleet.py`, `test_agent_skills.py`, `test_android_apk.py`, `test_json_multi_report.py`, `test_release_candidate.py`); whether they still do is not verified. A cold model compile on a loaded Mac takes minutes (see 8.17).
- **Pure functions get number-in, verdict-out tests**: the capacity planner (`test_capacity_planner.py`), `judge_screen`, `store_rules`, `translate_flow`, `pick_ios_runtime`.
- **A user-visible message is part of the contract.** Tests assert on fixed words of messages; a traceback for a known failure is a bug and a test asserts it is absent.

## 8.5 Every test module

"Defs" is the number of `def test_` in the file (static count, 2026-10-08). "Needs" lists what is required beyond Python; "none" means the docstring says no device, no network and no Mac, and the file has no skip decorators (not run on Linux for this chapter). Network means only `127.0.0.1` servers; no test is meant to reach the internet.

| Module | Defs | What it guards | Needs / weight |
|---|---|---|---|
| `test_agent_skills.py` | 24 | the three agent skills in `skill/`, `docs/AGENTS-snippet.md` and `site/public/llms.txt` against the program: every documented command parses with the real argparse parser, JSON keys, troubleshooting messages, config keys, env vars, exit codes, prices and links (doc guardrail, 8.6) | none; uses `fake_vision` |
| `test_android_apk.py` | 8 | Android strings read from a real APK (`tests/fixtures/strings-fixture.apk`), arrays in source files | `aapt2` for the APK class (skips otherwise) |
| `test_android_hierarchy.py` | 12 | Android screen text from Maestro's per-step hierarchy files (canned in `tests/fixtures/android-hierarchy`) | none |
| `test_api33_refusal.py` | 3 | an Android system image below API 33 is refused before the emulator boots | none |
| `test_apple_specs_watch.py` | 10 | `tools/apple-specs-watch.py` against a local server standing in for Apple's page | local HTTP server |
| `test_byoc_ios.py` | 48 | bring your own capture, iOS `[capture]`: config, attachment and fastlane collectors, `.xctestrun` copy, per-simulator language, run, doctor, init; every `xcrun` call is faked. `DeviceTestScript` tests `tools/fixture-byoc-e2e.sh` text | none |
| `test_capacity_planner.py` | 24 | the pure capacity planner and its message, the readers, the wiring; also the `MAESTRO_BAD` refusal (`:140-148`) | none |
| `test_capture_reliability.py` | 8 | `run_guarded` hangs, pool boot cleanup, one run per device set (real `device_lock`, unique keys), cleanup, partial results | none (spawns `sleep`) |
| `test_check_quality.py` | 10 | `check` says "could not read", not "blank", when a reader finds nothing; hang mid-check; system dialogs and banners | none |
| `test_claims.py` | 7 | the claims register `tests/claims.json` (273 rows): schema, quoted words still present, no known-false claim, "proven" names a test that exists (doc guardrail) | none |
| `test_claims_site.py` | 39 | proofs of the site-layer claims; runs `site/worker.test.mjs` once and looks up each named check; runs `tests/browser_site.cjs` (doc guardrail) | Node; Playwright + Chromium optional |
| `test_claims_unit.py` | 44 | unit-layer proofs: tier reaches both platforms, free tier on a frozen build, Gumroad reply shapes, hook env and exit codes, caption over an English UI, `init` per framework; defines `FleetCase` (8.7) | none; one Tesseract test |
| `test_clean_env_start.py` | 2 | the program starts with an empty `HOME` and a bare `PATH` (a `NameError` at import once crashed `--version` for buyers without an Android SDK) | subprocess only |
| `test_cli_claims.py` | 19 | what the site and README say the program prints and accepts; `JsonReports`, `CheckPromises`, `NothingIsUploaded`; `RealVisionSmoke` (doc guardrail) | `RealVisionSmoke`: Mac + `swiftc`, skips if recognition silent for 90 s |
| `test_consent.py` | 10 | Google Analytics consent, checked statically: nothing from Google loads and no cookie is set before "Accept analytics"; CSP, privacy page and footer agree with `ga.js` (site guardrail) | none |
| `test_device_type_fallback.py` | 6 | the default iPhone type falls back to the newest `iPhone N Pro Max`; an explicit `device_type` is never changed | none |
| `test_docs.py` | 28 | `site/public/docs.html` (anchors, "Last checked against version" equals `VERSION`, commands parse, config keys exist, hook variables) and `tools/build-guides.py` (doc guardrail) | none |
| `test_doctor_fix.py` | 42 | `doctor --fix`: downloads Maestro, Java and Android tools against a local HTTP server; checksum refusal, zip-slip refusal, SDK paths, emulator boot failures | local HTTP server |
| `test_doctor_versions.py` | 15 | `doctor` and `run` say which Maestro was tested and warn outside it; `MAESTRO_TESTED` is pinned here (`:57`); a slow text-recognition warm-up is a note, not a problem | fake `maestro` on PATH |
| `test_failure_messages.py` | 15 | what `run` says when a flow fails: step, screenshot, on-screen texts, iOS landscape tap hint (`tests/fixtures/maestro-failure/ipad-landscape.log`) | none |
| `test_first_run.py` | 30 | the first hour of a new user: wrong builds, locale names, missing `sysctl`, no runtime, config kept by `init`, OCR wait | none |
| `test_fixture_e2e.py` | 36 | `tools/fixture-e2e.sh` without devices: syntax, refusal, its assertion helper on synthetic output (one planted defect at a time), the whole script against fake `xcrun`, `adb`, `df`, `memory_pressure`, `sysctl`, `codesign` and a fake `shotfleet`; Linux refusals; the parallel knob | Mac for the whole-script class; Android parts need JDK + SDK build-tools (builds the real fixture APK, boots nothing) |
| `test_flat_check.py` | 5 | `check` on a flat folder of PNGs needs `--locale` | none |
| `test_free_tier_message.py` | 7 | wording of the free-tier cap message; stubbed licence server | none |
| `test_golive.py` | 23 | `packaging/go-live.sh --dry-run`, `tools/golive/smoke.sh`, `storefront.sh`, `install.sh` against a local fake server | Mac (5 `needs_mac`), `shasum`; local HTTP server |
| `test_handoff_docs.py` | 3 | every backticked path in `docs/handoff.md`, `compat.md`, `linux.md`, `agent-tasks/*.md` exists; the version-promotion checklist names strings that are really there (doc guardrail) | none |
| `test_js_translations.py` | 12 | translations written as a JS object (Ignite, i18n-js, vue-i18n) are read as data, never executed | none |
| `test_json_multi_report.py` | 2 | `--json` on a check over several reports prints one document | none |
| `test_latest_maestro.py` | 12 | `tools/latest-maestro.py`: picks the newest stable release, checksum, "seen" file, verdict; local server for GitHub | local HTTP server |
| `test_limits_c2_c3.py` | 15 | Android 7" tablet slot; check/export of Watch, Mac, Apple TV, Vision Pro sets made elsewhere; Android typed values per emulator | Node for 2 tests |
| `test_limits_first_run.py` | 15 | first-run friction found 2026-10-05: installer wording, Xcode not selected, iOS-only buyer, activate help, init before Maestro | none |
| `test_maestro_compat.py` | 9 | `tools/maestro-compat.py` against a fake Maestro (shell script + small jar) | none (no Java, no real Maestro) |
| `test_ocr_wait.py` | 29 | patient text-recognition warm-up, messages, the Latin-script rule, the check-wide budget, the per-Mac warm-up lock with two real processes | none; real subprocesses; sleeps of seconds |
| `test_pinned_build_inputs.py` | 6 | the release build installs only `packaging/requirements-build.txt` with hashes; no unpinned install is left; `build.sh` refuses a wrong Python | none |
| `test_platform_reach.py` | 3 | `tools/macho-minos.py` parsing of canned `otool -l` text | none |
| `test_portable.py` | 21 | readers that must work without macOS tools (`.strings`, `.stringsdict`, `Info.plist` without `plutil`/`PlistBuddy`), check without Mac OCR | none |
| `test_projects.py` | 39 | `init` recognises Flutter, React Native, Expo, MAUI, Capacitor, Kotlin Multiplatform folders and writes `strings` | none (synthetic folders) |
| `test_relative_app_path.py` | 4 | `init <app>` writes a relative path when the app is inside the project | none |
| `test_release_candidate.py` | 21 | `tools/release-candidate.sh` without building: syntax, refusal, safety rules in its text, and that its fake Gumroad answers the way `gumroad_verify` reads it | Mac for one PlistBuddy test |
| `test_release_consistency.py` | 3 | `shotfleet.py` `VERSION`, top `CHANGELOG.md` heading and `docs.html` "Last checked against version" agree; `tools/macho-minos.py --max` works (doc guardrail) | none |
| `test_release_scripts.py` | 39 | `packaging/publish.sh`, `preflight.sh`, `notary-check.sh` and `tools/verify-release.sh` against fake artifacts, a fake `wrangler`/`notarytool` and a local server; subprocess timeout 120 s (`:35`) | `sh`, `shasum`; local HTTP server; seconds to tens of seconds |
| `test_reliability_017.py` | 29 | 0.1.7: runtime guard (`BAD_IOS_RUNTIMES`), bounded `simctl` calls, overload advisor, infra-only retries, `--retry-failed` | none; class `IosRetries` needs a Mac |
| `test_screenshot_mode_doc.py` | 4 | `docs/screenshot-mode.md` examples survive `localize_flow`, no em dash, honest about what is not built (doc guardrail) | none |
| `test_security.py` | 16 | the 2026-10-07 security review as tests: MCP `run` runs no config command unless asked, MCP `check` runs no program, locales are never paths, lock files in `/tmp` (symlink, mode, FIFO) | none |
| `test_selftest.py` | 4 | `tools/selftest.sh`: syntax, `--help`, and a run against a fake release folder; checks `/tmp/shotfleet-selftest.*` is left as found | Mac for 2 tests |
| `test_setup_discovery.py` | 38 | `init` without arguments finds builds; Android SDK, image and `sdkmanager` discovery in `doctor` (fake home, fake SDK) | none |
| `test_shotfleet.py` | 310 | the core: 65 classes (flow translation, locales, Maestro output, `judge_screen`, export, store rules, MCP, licence incl. `GumroadLicence`, `LicenceHardening`, `UpdateWindow`, multi-device, free tier, config, hooks, the `G1*` detector and exit-code proofs, ...) | `needs_mac` on 26 tests; a local Gumroad HTTP server in `GumroadLicence` |
| `test_simctl_timeout.py` | 7 | a simulator that stops answering ends the run with a message naming it; installs run at once | none |
| `test_site.py` | 42 | the public site: structure, one price, banned phrases, go-live transform, privacy, What's new date, `DockerPending`, `ByocPending`, security.txt, HSTS, UTF-8 headers (doc guardrail) | none |
| `test_site_audit.py` | 55 | static site audit: contrast from CSS tokens, tap targets, tables, landmarks, JSON-LD, metadata lengths, robots, sitemap, CSP (doc guardrail) | none |
| `test_upload_gate_017.py` | 17 | 0.1.7: store coverage matrix, `check --compare`, `export --print-upload` | none |
| **Total** | **1,230** | | |

Files that are not modules:

| File | Role |
|---|---|
| `tests/claims.json` | the register of 273 public promises (status counts on 2026-10-08: proven 120, evidence 103, fixed 22, partial 20, removed 3, policy 3, unverifiable 2). Mechanics are in [06](06-packaging-and-release.md). |
| `tests/browser_site.cjs` | Chromium via Playwright against `site/public` served locally with every `/api/*` call stubbed; run by `test_claims_site.BrowserBehaviour`; exit 77 means skipped |
| `tests/fixtures/strings-fixture.apk` | 5 KB resources-only APK with strings in en, de, ja, ar, tr (names, a `<plurals>` and a `<string-array>`), made with `aapt2` from `tools/fixture-app-android` (`test_android_apk.py` docstring) |
| `tests/fixtures/android-hierarchy/` | `ar-welcome.json`, `ja-welcome.json`, `de-settings-real.json`: Maestro 2.11.0 hierarchy files (the shape it wrote in the "experiment A" run named in `test_android_hierarchy.py`) |
| `tests/fixtures/maestro-failure/ipad-landscape.log` | excerpt of a real iPad `maestro.log`, app id replaced |
| `site/worker.test.mjs` | the worker's own tests, plain Node with an in-memory KV and limiter; prints `ok`/`FAIL` lines |

## 8.6 Doc and site guardrails: tests that fail when text drifts

These tests are the reason a change to a sentence on the site, README, docs page, skill or a few docs files makes the gate go red. That is intended: the sentence and the proof must change together. The workflow is in [10-contributing.md](10-contributing.md); the claims mechanics in [06](06-packaging-and-release.md).

| Test | Guards | Typical failure |
|---|---|---|
| `test_claims.py` | each row of `tests/claims.json`: the file exists, the quoted words (`where_text`) are still in it, a `proven` row names a test that exists | you reworded a promise: update the row |
| `test_claims_site.py`, `test_claims_unit.py` | the proofs the register names for site-layer and unit-layer claims | |
| `test_cli_claims.py` | what README and site say the program prints and accepts (terminal samples, documented commands, JSON reports, check promises, versions, "nothing is uploaded") | you changed output wording the README quotes |
| `test_docs.py` | `site/public/docs.html`: one h1, anchors and table of contents, title/description lengths, sitemap and `llms.txt` once, every `shotfleet` command parses with the real parser, every config key exists and every TOML example is accepted, hook variables match, no upload or price promise, no em dash or banned phrase, and the line "Last checked against version X on DATE" (`:90`) | version bumped in `shotfleet.py` but not in `docs.html` |
| `test_release_consistency.py` | `VERSION` (`shotfleet.py:28`), the top dated `CHANGELOG.md` heading and the docs "Last checked" line are the same version | partial version bump |
| `test_agent_skills.py` | `skill/*`, `docs/AGENTS-snippet.md`, `site/public/llms.txt`: commands, JSON keys, troubleshooting messages, config keys and tables, env vars, exit codes, free tier, prices, links, requirements equal README (including the string `Maestro (tested with 2.0.10 and 2.11.0)` at `:292`) | a message in the program changed |
| `test_handoff_docs.py` | backticked paths in `docs/handoff.md`, `docs/compat.md`, `docs/linux.md`, `docs/agent-tasks/*`; the promotion checklist quotes; the pinned 2.11.0 checksum in `docs/handoff.md` and `research/maestro-2-11.md` | you renamed or deleted a file those docs name |
| `test_screenshot_mode_doc.py` | `docs/screenshot-mode.md` | |
| `test_site.py`, `test_site_audit.py`, `test_consent.py` | the public site | |
| `test_release_scripts.py`, `test_golive.py`, `test_pinned_build_inputs.py` | the release and go-live scripts and the pinned build inputs | |

Flag files that change what the site tests demand:

| File | Meaning | Test |
|---|---|---|
| `site/BYOC_DEVICE_PROVEN` (exists, 0 bytes) | bring-your-own-capture passed its device test (2026-10-07) | `test_site.ByocPending` (`:363-390`): while the file is absent, every line offering "your own XCUITest" tests must contain "its device test hasn't passed yet"; while present, no line may say so |
| `site/DOCKER_PUBLISHED` (absent) | the `ghcr.io/noloman/shotfleet-check` image is published | `test_site.DockerPending` (`:338`): while absent, no public file may mention the image outside `DOCKER-PENDING` comment markers |
| `<!-- WAITLIST -->` in `site/public/index.html` (absent: the site is live) | the sale page is live | `LIVE` in `test_site.py:22`, `test_golive.py:16`, `test_site_audit.py:17`, `test_claims.py:19` skips waitlist-only checks |

No test scans `docs/engineering/` or `docs/architecture/`: the paths and numbers in these chapters are not machine-checked.

## 8.7 Test doubles and patch targets

| Double | Where | Stands in for |
|---|---|---|
| `FleetCase` | `tests/test_claims_unit.py:33-111` | a whole fleet run: a project with an iOS app and an Android app in four languages, and patches for `LICENCE_FILE`, `sys.frozen` (True turns the licence gate on), `LOCALE_CAP`, `NO_HOOKS`, `maestro_cmd`, `read_maestro_version` (returns "2.0.10"), `java_env`, `fit_parallel`, `kill_stale_drivers`, `shutdown_sims`, `OUR_SIMS`, `latest_ios_runtime`, `make_pool`, `android_pool`, `run_guarded` (a fake Maestro that writes JUnit and `maestro.log`), `cmd_check`, `aapt2`, `sh`. `main()` also replaces `sf.urllib.request.urlopen` with a function that fails, so any licence call is an error. |
| `sf.USE_DEVICE_LOCK = False` | many modules (8.4) | the per-set `flock` of `device_lock` |
| `sf.LICENCE_FILE` | referenced in 5 modules, 73 occurrences (`shotfleet.py:5283`) | `~/Library/Application Support/shotfleet/licence.json` |
| `sf.GUMROAD_API` | `test_shotfleet.py:1401` and 2 other modules (7 occurrences) (`shotfleet.py:5287`) | `https://api.gumroad.com/v2/licenses`, replaced by a local `BaseHTTPRequestHandler` (`H`, `test_shotfleet.py:1379`) |
| `sf.RELEASE_DATE` | referenced in 6 modules (`shotfleet.py:5328`) | the baked build date that decides the one-year update window (`UpdateWindow`) |
| `sf.sh` / `sf.run_guarded` | referenced in 14 and 5 modules | every host command; fakes return canned `CompletedProcess` objects |
| `sf.make_pool`, `sf.android_pool` | referenced in 8 and 6 modules | simulator and emulator pools; `FakeSim`, `FakeEmu` classes in `test_shotfleet.py:2947,2963,3476` and `test_capture_reliability.py:29` |
| `sf.read_text` / `fake_vision()` | patched in 7 modules / `test_cli_claims.py:31` | macOS Vision text recognition; `fake_vision` reads each image's `.txt` sidecar |
| fake Gumroad | `tools/release-candidate.sh` (`FakeGumroad`, can simulate outage, refund, uses), `tests/test_release_candidate.py:78`, `test_claims_unit.py` (`Reply`, `gumroad_answer`, `http_error`) | `api.gumroad.com/v2/licenses/verify`; built from Gumroad's documentation, so its behaviour is an assumption until a real paid sale and refund (`STATUS.md` gate 5) |
| fake `wrangler`, `notarytool`, local `ThreadingHTTPServer` | `tests/test_release_scripts.py`, `test_golive.py` | Cloudflare, Apple, the live site |
| fake Maestro folder | `tests/test_maestro_compat.py:15` `fake_maestro(version, flags, strings)` | a Maestro install (shell script + small jar) |
| local servers for releases and specs | `test_latest_maestro.py` (`SHOTFLEET_MAESTRO_RELEASES`), `test_apple_specs_watch.py` (`SHOTFLEET_APPLE_SPECS_URL`), `test_doctor_fix.py` `Server` | GitHub, Apple, Adoptium, Google |
| fake `xcrun`, `adb`, `df`, `memory_pressure`, `sysctl`, `codesign`, `shotfleet` | `tests/test_fixture_e2e.py:245-300` (`FAKE_SF`, `FAKE_ADB`, `FAKE_XCRUN`) | all that the fixture script touches |
| fake OCR helper scripts | `tests/test_ocr_wait.py:15` `fake_helper(body)`; `ps` mocked | the Swift helper and `ANECompilerService` |
| stubbed `/api/*` in Chromium | `tests/browser_site.cjs` | the worker, to test `forms.js` and `analytics.js` |
| in-memory KV and limiter | `site/worker.test.mjs:2-5` | Cloudflare KV and the rate limiter |

## 8.8 The fixture apps

**iOS: `tools/fixture-app/`.** `App.swift` is a SwiftUI app with two screens in one view: "Welcome" with a subtitle ("Your screenshots, in every language.") and a "Next" button, and "Settings" with "Choose how the app looks and sounds." and a "Done" button. Strings are in `Resources/{en,de,ja,ar,tr}.lproj/Localizable.strings` with the English text as key; German reads Willkommen / Einstellungen / Weiter / Fertig. `build.sh <outdir>` compiles it with `swiftc` for `arm64-apple-ios17.0-simulator` (no Xcode project), writes the `Info.plist` (bundle id `dev.shotfleet.fixture`, iPhone and iPad, portrait on iPhone, all orientations on iPad) and ad-hoc signs it: `FleetFixture.app`. The one flow both platforms run (`tools/fixture-e2e.sh:117-128`) is: `launchApp`, wait, `takeScreenshot: 01_welcome`, `tapOn: "Next"`, wait, `takeScreenshot: 02_settings`. So every language yields 2 screenshots per device.

**iOS XCUITest target (for bring your own capture).** `project.yml` describes the same app as an Xcode project with a UI test target; `FleetFixture.xcodeproj` is generated with `xcodegen` and committed, so the machine running the test does not need it. This variant is iPhone only (`TARGETED_DEVICE_FAMILY: "1"`, so `check` does not ask for an iPad set). `UITests/ScreenshotTests.swift` has three test classes: `ScreenshotTests` (XCTAttachment with `.keepAlways`, read from the result bundle), `SnapshotStyleTests` (writes PNGs the way fastlane's SnapshotHelper does, into `~/Library/Caches/tools.fastlane/screenshots`, only if that folder exists), and `NoKeepTests` (an attachment without `.keepAlways`: the test passes but saves nothing, and the run must fail).

**Android: `tools/fixture-app-android/`.** `MainActivity.java` is the same two screens in plain Android Views (no AndroidX, no Gradle); same words in `res/values{,-de,-ja,-ar,-tr}/strings.xml` (Arabic is right to left); package `com.shotfleet.fixture`, minSdk 33 (so the per-app language API works). `build.sh <outdir>` uses only the SDK's own tools (`aapt2`, `d8`, `zipalign`, `apksigner` from the newest build-tools, the newest platform `android.jar`) plus the JDK's `javac` and `keytool`, signs with a throwaway key, and writes `FleetFixture.apk`. No downloads. It runs on the AVD `shotfleet_android` (the phone slot, `shotfleet.py:2527`).

**What the German assertion reads:** the iOS and Android raw `de/01_welcome.png` must show "Weiter" and `de/02_settings.png` "Fertig" (`WORDS`, `tools/fixture-e2e.sh:266`), taken from the app's own `.texts.json` capture when the run saved one, else from macOS text recognition.

## 8.9 `tools/fixture-e2e.sh`

Header: `tools/fixture-e2e.sh:1-18`. About 410 lines; the last part is the Python assertion helper (lines 256-410, between `: <<'__PY__'` and `__PY__`), which `tests/test_fixture_e2e.py` loads and tests against synthetic trees.

**Invocation.** `SHOTFLEET_E2E=1 tools/fixture-e2e.sh [--android] [--platform-only ios|android] [--skip-android] [--keep]`. `SHOTFLEET_E2E_ANDROID=1` is the same as `--android`. `SHOTFLEET_BIN=<binary>` tests a built release instead of `shotfleet.py` (a built binary needs a licence for the export step: activate it or set `SHOTFLEET_KEY`). `SHOTFLEET_E2E_PARALLEL=1|2` (default 2) sets the Android config's `parallel` (line 218); `SHOTFLEET_E2E_ADB` overrides the `adb` path. No flag means iOS only. On Linux only `--platform-only android` runs (lines 40-43).

**Pre-flight** (nothing is created or booted before it passes): 5 GB free in `$TMPDIR` (line 48); on macOS, memory pressure not critical (level 4 or under 10% free); on Linux, 6 GB available memory, a readable and writable `/dev/kvm`, Tesseract with `deu`, `jpn`, `ara`, `tur` data (lines 55-63); no shotfleet simulator already booted and no emulator on ports 5700-5799 (lines 146-151). It does not take the agent lock of 8.13; shotfleet's own `flock` (8.13) is the only lock it holds.

**Phases and what they assert.**

| Phase | Assertions |
|---|---|
| build | the fixture builds (exit 0) and has an `Info.plist` |
| `init` | exit 0; wrote `shotfleet.toml` and `flow.yaml` |
| `doctor` | exit 0 and prints `iOS: ready` (or `Android: ready`) |
| `run` | exit 0 on iPhone 17 Pro Max and iPad Pro 13-inch (M5), languages de, ja, ar, tr (4 simulators per device type unless memory pressure halves them) |
| `check`, `export --fastlane` | each exits 0 |
| tree assertions | per device: 2 screenshots in every language; every PNG exists, is a real image of at least 5,000 bytes and 300 px; no two languages share an identical image; German text shows the expected words; `check.json` has 0 problems; `run.json` has every language ok; Android with hierarchy markers: every screenshot's text came from the UI hierarchy. Export: one folder per listing locale with all screenshots (one set per device). The four `[hooks]` events fired with exit 0 |
| planted failures | on copies of the output: a German picture copied over Japanese, and one screenshot deleted; `check` must exit 1 for each and its output must name the language (`shows de` / `identical image`, `missing`). This proves the detectors work |

**Counts** (derived from the script and matching recorded runs): iOS 36 assertions; Android 29, or 30 when the run recorded hierarchy markers (`shotfleet.py:2615` `HIER_MIN = (2, 7, 0)`, the extra assertion at `tools/fixture-e2e.sh:341`); iOS plus Android 65 (or 66). Recorded: 36/36 and 29/29 on 2.0.10 and 2.11.0 (2026-10-04, `docs/compat.md:11-12`), Android 30/30 on 2.11.0 (2026-10-07, `research/maestro-2-11-0.1.6-2026-10-07/NOTES.md`).

**Runtime.** The header says "about 10 minutes for iOS, a few more for Android" (line 10). Recorded wall times differ with load and with how many devices memory pressure allows: iOS 344 s (2.11.0, 2026-10-04), 527 s (2.0.10, rerun the same day), 16 min 42 s (2.0.10 on Xcode 27, 2026-10-05, `docs/compat.md:47`), 518 s on 2026-10-07 with one simulator at a time; Android 99 to 148 s (2026-10-04), 108 s (2026-10-07); a full iOS + Android gate is 37 to 55 minutes on a quiet Mac (`docs/architecture/07-packaging-and-release.md:85`). There is no hard time limit inside this script (the BYOC script has one, 8.10); the queue protocol requires the caller to impose one (8.13).

**What "passed" means.** The last line is `PASS: all N assertions passed` and the exit status is 0 (`finish`, lines 109-115). Exit 1 means at least one assertion failed (the work dir is kept); exit 2 means a refusal (missing opt-in, pre-flight, a booted pool).

**Cleanup.** The trap shuts down only simulators named like shotfleet's pools (`shotfleet-iphone-*`, `shotfleet-ipad-*`, `POOLS` at `:270`) once a run started, and only `emulator-57xx` if it started emulators; pre-flight proved none was there before. A second shotfleet run started at the same moment could be hit (comment at lines 72-73).

## 8.10 `tools/fixture-byoc-e2e.sh` and `BYOC_DEVICE_PROVEN`

The device test for bring your own capture (iOS `[capture]`, see [02](02-capture-and-devices.md)). `SHOTFLEET_E2E=1 tools/fixture-byoc-e2e.sh [--keep]`. It builds `tools/fixture-app/FleetFixture.xcodeproj` for testing once, then runs `shotfleet run` with a `[capture]` config on 2 simulators in parallel, languages de and ja:

1. `ScreenshotTests` with `screenshots = "attachments"` (full run including the build);
2. `SnapshotStyleTests` with `screenshots = "fastlane"` and `--no-build`; the fastlane cache folder must be as it was found afterwards;
3. `NoKeepTests`: the test passes but saved nothing, so the run must exit 1 and say `saved no screenshots`.

20 assertions in all (3 exit codes, 2 x 7 per-case checks, 3 more); a passing run prints `PASS: all 20 assertions passed`. Guards: `SHOTFLEET_E2E=1`, macOS with `xcodebuild`, 5 GB free, memory pressure not critical, 1-minute load under 300 (line 44), no `shotfleet-N` simulator booted. Hard limit: the whole script is killed after `SHOTFLEET_E2E_LIMIT_S` (default 1800 s, lines 51-53), each language's test after 300 s (`[capture] timeout`) and 240 s without progress (`stall_s`). Header estimate: about 5 minutes. Recorded: 12 min 46 s at load 7 rising to 354, 2026-10-07, 20/20, iOS 26.4 pinned, signed 0.1.6 binary (`research/byoc-device-test-2026-10-07/README.md`). Earlier attempts failed on the machine, not the feature: 2026-10-06 at heavy load (simulator uninstall hung, 14 of 20 assertions, `research/byoc-device-test-2026-10-06/`), and 2026-10-07 12:28 killed by the hard limit because iOS 27.0 simulators froze at boot (8.15).

`site/BYOC_DEVICE_PROVEN` (empty file) records that this test passed. Its presence flips the site test from "every line offering your own XCUITest tests must carry the caveat 'its device test hasn't passed yet'" to "no line may carry any such caveat" (`tests/test_site.py:363-390`). If the file is deleted, the gate demands the caveat back on at least 10 lines of README and public pages.

## 8.11 Other tools in `tools/`

| Tool | What it does | Runs where / cost |
|---|---|---|
| `check-claims.sh` | the gate (8.3) | local; the only thing the pre-commit hook runs |
| `selftest.sh` | "does the release start on THIS Mac?": installs a tarball, folder or `--download` into a throwaway `HOME` with an empty environment, runs `--version`, `doctor` (never `--fix`, 150 s limit) and `check` on two screenshots it draws itself with JXA, prints one PASS/FAIL block to paste back. Options `--quarantine`, `--licence-probe` (one made-up key to Gumroad), `--hide-tools` (`sandbox-exec` hides Homebrew, Java, Android, Maestro folders), `--keep`. Exit 0 PASS, 1 FAIL, 2 usage | macOS only; used for the macOS 26.2 VM run (`research/vm-older-macos-results-2026-10-05.md`). Tested by `tests/test_selftest.py` against a fake release folder. **There is no `shotfleet selftest` subcommand**: `grep selftest shotfleet.py` finds nothing. The earlier copy in `research/proposed-selftest/selftest.sh` differs from `tools/selftest.sh` only in its header comment |
| `fixture-e2e.sh`, `fixture-byoc-e2e.sh` | 8.9, 8.10 | devices |
| `maestro-compat.py` | the offline Maestro vetting (8.12) | any machine with a Maestro folder |
| `latest-maestro.py` | finds the newest stable `cli-X.Y.Z` release of `mobile-dev-inc/maestro` (skips drafts and pre-releases), downloads its `maestro.zip` (315 MB) checking the release's `checksums_sha256.txt`, runs `maestro-compat` on it, prints the verdict (tested / newer than anything tested / older). Exit 0 nothing required missing, 1 something gone, 2 could not fetch. Skips the download when the newest tag equals the last passing one, kept in `tools/.latest-maestro-seen` (git-ignored; `SHOTFLEET_MAESTRO_SEEN`, `SHOTFLEET_MAESTRO_RELEASES`, `GITHUB_TOKEN` honoured) | network |
| `watch-upstream.sh` | runs `latest-maestro.py` then `apple-specs-watch.py`; exit 0 only if both pass, 1 = something to update, 2 = a watcher could not read its source. The local replacement for scheduled Actions; run about monthly and before a release | network |
| `apple-specs-watch.py` | compares every "W x H pixels" size on Apple's screenshot specification page with `APPLE_SIZES` in `shotfleet.py`; exit 1 on drift, 2 if the page no longer parses (fewer than 40 sizes) | network |
| `langmatrix.py` | measures the language check on every language AndroidX is translated into (about 85): renders a phone screen of real UI strings per language, then asks `judge_screen` whether the right screen passes, the English screen filed as that language is flagged, and a close language's screen (uk/ru, nb/da, pt-PT/pt-BR, ...) is flagged. `python3 tools/langmatrix.py <app.apk> [out_dir] [--tesseract]`; writes `matrix.json`. Needs `.build/render` (source `tools/render.swift`); no script in the repo builds that binary (how it is built is not verified) and the checkout has only `.build/ocr`. The 85-language reading measurement is mentioned in `research/e2-tesseract-parity.md:25` and `research/limits-platforms.md:77`; where the full result table lives is not verified | Mac |
| `pretend-mac.py` | runs one test module with `sys.platform = "darwin"` and `machine() = "arm64"` after import; no Xcode, Vision or plutil appear. It found two Mac-only assumptions in the `doctor --fix` tests that a macOS CI job also found | any |
| `ios27-repro.sh` | the one-simulator, one-language repro of the iOS 27 hang (8.15); every step killed at its own limit, 15 minutes in all | Mac, device queue |
| `macho-minos.py` | lists every Mach-O file's minimum macOS (and architectures) in a built folder; `--max 13` exits 1 if something needs newer. Homebrew's Python made the 0.1.0 folder need macOS 27.0 | needs `otool`, `lipo`, `file` |
| `verify-release.sh`, `release-candidate.sh`, `golive/smoke.sh`, `golive/storefront.sh` | release proofs (06) | |
| `status.sh` | prints the numbers `STATUS.md` quotes (runs the unit and worker tests unless `--quick`, reads the live site with `curl`); not a gate | network |
| `build-guides.py`, `bump-homebrew.sh`, `sync-public-skills.sh` | content and release helpers (06, 07) | |

## 8.12 The Maestro compatibility matrix

**What shotfleet relies on.** `MAESTRO_INTERFACE` (`shotfleet.py:3902-3913`) is the one list: the flags `maestro --device` and `maestro test --shard-split --format --output --debug-output`, the `--format` value `JUNIT`, five log strings (`Selected device`, `using port`, `with execution plan`, `ExecutionPlan(flowsToRun=`, `maestro.log`), two environment variables it sets (`MAESTRO_DRIVER_STARTUP_TIMEOUT`, `MAESTRO_CLI_NO_ANALYTICS`), thirteen flow keys it writes, and one nice-to-have, `MAESTRO_DEVICE_UDID`.

**The constants.**

| Constant | Value | Effect |
|---|---|---|
| `MAESTRO_TESTED` (`:3915`) | `("2.0.10", "2.11.0")` | versions a real fixture e2e passed on, iOS and Android. `doctor` prints `maestro X (tested: ...)`; any other version gets one note ("not the version shotfleet was tested with ...; it may work"), never an error (`maestro_warning`, `:3939`, used at `:4239` and `:5692`) |
| `MAESTRO_PIN` (`:3951`) | 2.11.0, 314,886,578 bytes, SHA-256 `5384593c...e1283a` | what `doctor --fix` downloads |
| `MAESTRO_BAD` (`:3932`) | `{}` | versions proven bad; `run` stops before booting devices (`maestro_refusal`, used at `:5691`). Empty today. Add one only with a reproduced failure and the evidence in `research/` (comment at `:3930-3931`) |
| `HIER_MIN` (`:2615`) | `(2, 7, 0)` | first Maestro whose per-step artifacts include the screen hierarchy; below it Android text comes from OCR |

**What `tools/maestro-compat.py` checks** (28 checks): `--version` parses (1) and is 2 or newer (1); the 5 required flags exist in `--help`; `--format` offers `JUNIT` (1); 20 strings are still in the `*maestro*`/`*server*` jars (5 log, 2 env, 13 flow keys). `MAESTRO_DEVICE_UDID` is reported as INFO. Exit 0 nothing required missing, 1 something gone, 2 usage. Recorded: 28/28 on 2.0.10 and on 2.11.0. It is a screen, not a test: green means "worth a real run", never "supported".

What it cannot tell: whether sharded parallel runs behave (Maestro 2.6.0 changed parallel iOS handling), whether errors that 2.7.0 stopped swallowing (`launchApp`, `clearState`) now fail a flow, how long a run takes, and, the proof in point, it did not and would not have caught the 2.11.0 `takeScreenshot` change (the interface has no entry for it). The unit test `tests/test_maestro_compat.py:85-89` checks one direction only: every flag and env var named in `MAESTRO_INTERFACE` is still in `shotfleet.py`; a new flag that `shotfleet.py` starts using but nobody adds to the list is not detected.

**Why 2.0.10 and 2.11.0.** No document states a policy beyond "extend only after a real run" (`shotfleet.py:3915`). The facts:

- **2.0.10** is the version every real run used until 2026-10-03 (CrossfitTracker 18/18 on iOS and Android, the iOS fixture 36/36, the Android fixture 29/29; `docs/compat.md:11`) and the one installed in `~/.maestro` on the development Mac (`research/maestro-2-11-0.1.6-2026-10-07/NOTES.md`). It is the baseline.
- **2.11.0** (released 2026-09-29) is the newest upstream release: `docs/compat.md:12` records that 2.11.1, 2.12.0 and 3.0.0 did not exist on 2026-10-03, and the 2026-10-07 notes still call it the newest. It is what `doctor --fix` installs, and it brings two things shotfleet uses: Android screen text from the UI hierarchy (2.7.0 and later) and `MAESTRO_DEVICE_UDID` (set to the adb serial) for Android `[inputs.<locale>]` (`docs/compat.md:27-30`).
- **The history behind "tested".** On 2026-10-03 the fixture e2e on 2.11.0 failed (iOS 25 of 36, Android 19 of 29): since the 2.7/2.8 artifact rework `takeScreenshot` may only write inside the run's artifact folder, and shotfleet gave it absolute paths (`research/maestro-2-11.md`, "The one cause"). shotfleet now names screenshots relative to Maestro's working directory and moves them afterwards (`collect_shots`); on 2026-10-04 2.11.0 passed 36/36 and 29/29, and 2.0.10 still did. Both were re-run on 2026-10-07 with the 0.1.6 code (8.12 table below), because the 0.1.4 to 0.1.6 changes had only run on 2.0.10.

**Behaviour differences that are recorded** (all are in `research/maestro-2-11.md` and `docs/compat.md`; none is a bug in shotfleet):

| Topic | 2.0.10 | 2.11.0 |
|---|---|---|
| absolute `takeScreenshot` path | accepted | rejected; relative name under the run's folder |
| per-step screen hierarchy | not saved | saved; Android `check` reads text from it (`evidence = "hierarchy"`) |
| `MAESTRO_DEVICE_UDID` | not defined | defined; adb serial |
| iOS driver start at 4 simulators (CrossfitTracker, 19 languages) | 19/19, no retry, 404 s capture on a quiet Mac, 2026-10-05 (`docs/compat.md:57`) | 19/19 but 9 of 19 languages needed shotfleet's retry ("iOS driver not ready in time"), 826 s, 2026-10-04 (`docs/handoff.md:151`). Not a clean comparison: load differed. Specific to 2.11.0 per that note; a longer `MAESTRO_DRIVER_STARTUP_TIMEOUT` or staggered starts were not tried |
| `launchApp` / `clearState` errors | swallowed | surfaced (2.7.0) |

**Evidence runs (device):**

| Date | Maestro | What | Result | Where |
|---|---|---|---|---|
| 2026-10-03 | 2.11.0 | fixture e2e | FAIL iOS 25/36, Android 19/29 (absolute paths) | `research/maestro-2-11.md` |
| 2026-10-04 | 2.11.0 | fixture e2e after the fix | iOS 36/36 (344 s), Android 29/29 (148 s) | same |
| 2026-10-04 | 2.0.10 | same | Android 29/29; iOS first run 11 of 22 failed on a hung simulator (not Maestro), rerun 36/36 | same |
| 2026-10-04 | 2.11.0 | CrossfitTracker 19 languages | iOS, Android phone, Android tablet 19/19 each, 0 problems | same |
| 2026-10-04 | 2.11.0 | Android `[inputs.de]`, `[inputs.ja]` | works on one emulator; two at once not run | same |
| 2026-10-07 | 2.11.0 | 0.1.6 fixture e2e | Android 30/30 in 108 s; iOS attempt 1 17/36 (all four iPad simulators stopped answering at `simctl uninstall`, 18 to 21 GB of swap, the same hang as the 0.1.6 gate on 2.0.10 that morning); iOS rerun 36/36 in 518 s with one simulator at a time | `research/maestro-2-11-0.1.6-2026-10-07/NOTES.md`, `logs/` |

Not covered by the 2026-10-07 run (its own list): real apps on 0.1.4 to 0.1.6 code, 4 simulators in parallel, clean timings, Android on 2 emulators at once.

**Procedure to add a new Maestro version.** Everything below is what was done for 2.11.0 (`docs/handoff.md:25-62`), corrected against the current files.

1. Screen it offline. `sh tools/watch-upstream.sh`, or `python3 tools/latest-maestro.py`, or `python3 tools/maestro-compat.py <folder>` for a copy you have. Expect 28 passed. A FAIL says which part of `MAESTRO_INTERFACE` is gone: decide whether shotfleet or the list changes.
2. Put the download in its own folder, not over `~/.maestro` (the 2.11.0 runs used `~/.maestro-tests/<version>/`), verify its SHA-256 against the release's `checksums_sha256.txt`, and put its `bin` first on `PATH` for single commands only. Check `maestro --version`.
3. Take the device lock and do the quiet check (8.13). Run `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` and `--platform-only android`. Expect 36 and 29 (30 with hierarchy). Since 0.1.7 `run` skips the iOS 27.0 runtime by default, so the iOS 26.4 pin that earlier gates added with a temporary config line is needed only on a pre-0.1.7 build or when 27.0 is the only runtime.
4. Watch for, from the 2.11.0 research: errors from `launchApp`/`clearState`; the `Selected device ... using port` line missing from `maestro.log` (then `capture_texts` falls back to OCR on iOS); sharded parallel iOS runs; `takeScreenshot` path rules; driver start timeouts at 4 simulators; `MAESTRO_DEVICE_UDID` still the adb serial (check with an Android `[inputs]` flow); hierarchy artifacts still written.
5. Optionally run a real app (done for 2.11.0 with CrossfitTracker).
6. If it passes, promote in ONE commit. The places that quote the pair, found by search on 2026-10-08 (the list in `docs/handoff.md:53-61` is shorter than this): `shotfleet.py` `MAESTRO_TESTED` (and `MAESTRO_PIN`: version, size, URL, SHA-256, only if `doctor --fix` should install the new one); `README.md` (`Maestro (tested with 2.0.10 and 2.11.0)` at line 455, the `doctor --fix` paragraph at line 142); `site/public/docs.html` (lines 180, 182 and the run-time sentence at 461); `skill/shotfleet/SKILL.md:11`; `skill/shotfleet/references/troubleshooting.md:13`; tests `test_agent_skills.py:292`, `test_doctor_versions.py:57-121` (the assertion and the "newer version" cases, which use 2.99.0), `test_handoff_docs.py:23-25` (hard-coded quote strings), `test_claims_site.py:75-76`; claims rows that quote the version in `where_text` (C033, C146, C153, C266 on 2026-10-08; search `tests/claims.json` for the old string) and rows that mention it in proof text; docs `docs/compat.md`, `docs/linux.md:69`, `docs/weekend-support.md:39`, `docs/handoff.md`. Run the gate; it names what was missed.
7. Record the evidence in a dated `research/<name>-<date>/` folder and a new row in `docs/compat.md`.
8. If it fails: change no claim and no constant; write what failed (command, log lines) in `research/`. Add the version to `MAESTRO_BAD` only if the failure is reproduced and you want `run` to refuse it (the mechanism is tested at `tests/test_capacity_planner.py:140-148`). An untested version only warns.

## 8.13 The device queue and the two locks

Two different locks exist; do not confuse them (the code one is also described in [02-capture-and-devices.md](02-capture-and-devices.md#28-locks)).

**1. In the program (automatic).** `device_lock(key)` (`shotfleet.py:1980`) takes an `flock` on `/tmp/shotfleet-<key>.lock`: `ios-<sim_prefix>` around an iOS device set (`:2007`) and `android-emulators` around the Android pool (`:2722`, emulators sit on fixed ports 5702, 5704, ...). The OS drops it when the process dies. A second run on the same devices fails with "another shotfleet run is using these devices". Reason: pool simulators are named `shotfleet-<device>-N`, so two runs of one device type reinstall the app under each other and steal each other's simulators (seen 2026-10-03). A lock file that cannot be made does not stop the run.

**2. Between agent sessions (a convention, `docs/device-queue.md`).** Many Claude sessions share one Mac. Two device jobs at once (load 600 to 1000, free memory near zero) made simulators hang and voided runs. The rules:

1. One device job at a time. Before booting any simulator or emulator (including `fixture-e2e.sh`, `shotfleet run`, `maestro`): `mkdir /tmp/shotfleet-devices.lock && echo "<session> | <what> | <started HH:MM> | est. <N> min" > /tmp/shotfleet-devices.lock/holder`. If `mkdir` fails, someone holds it: do non-device work and add a line to `/tmp/shotfleet-device-queue.md`.
2. Release with `rm -rf /tmp/shotfleet-devices.lock` once your own simulators and emulators are shut down.
3. Every run script and every waiter has a hard time limit (kill only your own PIDs). A waiter without one held the lock for 8 hours (`docs/handoff.md:162`).
4. Never kill or delete what you have not proven is yours (process cwd, parent chain, or a log naming the folder). A stale lock (older than 2 h, no live process) is reported to the queue owner, not broken.
5. Quiet check before starting: free memory at least 20 percent, load under 300, no emulator on ports 57xx. Jobs that share no device names or ports (an iOS job beside an Android-only one) may overlap with the owner's OK.
6. Do not change the machine-wide default while others are queued: importing an iOS runtime changes `latest_ios_runtime()` for every run.

The files live in `/tmp` and do not survive a restart; waiters die with their sessions, so re-arm them. On 2026-10-08 `/tmp/shotfleet-devices.lock` did not exist (nobody held it); `/tmp/shotfleet-device-queue.md` existed (last modified 2026-10-07 20:34) and was not read for this chapter.

**Stricter start rules that grew later and are not in `device-queue.md`:** the coordinator's rule for the 2026-10-07 reruns was not actively swapping (`vm_stat` swapouts under 2,000 pages per 60 s, three windows in a row), load under 100, free memory at least 40 percent, memory pressure at most 2, lock free, no `xcodebuild` of another job, disk at least 15 GB (`research/maestro-2-11-0.1.6-2026-10-07/NOTES.md`); and from the 0.1.3 and 0.1.4 gates: start at memory pressure level 1 (not by free percentage alone), no busy Gradle or Kotlin daemon (idle ones held 21 GB; run `./gradlew --stop` per Gradle version), every emulator under the lock, and a pool simulator that hung is replaced, not reused (`docs/handoff.md:207-211`). `tools/fixture-byoc-e2e.sh:44` hard-codes load under 300 and `tools/fixture-e2e.sh:49-54` refuses only at pressure level 4. Which numbers are "the" rule is not settled in any file.

**Running the unit suite beside a device job** is not addressed by the protocol. The suite is light on CPU but starts many processes; it is inference, not a rule, that you should not start `check-claims.sh` while a gate run is in progress unless the change cannot wait.

## 8.14 Linux and Android emulators on KVM

Status per `docs/linux.md` (verified against the current files; that document has stale parts, listed in 8.19).

| Machine | Can run the Android emulator? | Evidence |
|---|---|---|
| Apple silicon Mac (the development Mac) | Yes, arm64 image; every Android gate to date | `docs/compat.md:49`, `shotfleet.py:2349` |
| Linux x86_64 with a usable `/dev/kvm` (physical or nested virtualization) | Yes | `docs/linux.md:91`, `docs/handoff.md:68` |
| GitHub-hosted `ubuntu-latest` (private repo: 2 vCPU, 7 GB, about 7 GB free disk; KVM usable after a udev rule) | One emulator, yes: the fixture passed 13/13 assertions in 8 min 13 s with one emulator, ANR dialogs hidden and animations off. Two emulators: failed in every attempt ("Process system isn't responding" over the first screenshot, or `adb install` racing the boot) | `docs/linux.md:101-126` |
| Linux without `vmx`/`svm` (a VM without nested virtualization) | No: the emulator refuses x86_64 images, and refuses an arm64 image on an x86_64 host; no software fallback | `docs/linux.md:60-63` (checked 2026-10-03, emulator 37.2) |
| ARM Linux | No Google emulator image; `doctor` would ask for `arm64-v8a` | `docs/linux.md:60,130` |
| Intel Mac | Not supported (the installer refuses Intel Macs) | `README.md:455` |
| macOS hosted runners (`macos-14`, `macos-15`) | Not used for emulators or simulators; only install, `doctor`, `check` of the live 0.1.1 | `docs/compat.md:50`, `.github/workflows/macos-compat.yml` |

**One emulator versus two on a small machine.** What is proven: one emulator on 2 cores passes the Android fixture. What is not: two emulators on 4 or more cores, an 18-language real-app run on Linux (the Mac reference is 15 min 24 s for 18 languages), arm64 Linux. The code encodes the one data point: `fit_emulators` (`shotfleet.py:1499`) on Linux uses at most `cores // 2` and `free GB // 3` emulators and prints when it lowers `parallel`; its comment calls the 2 cores and 3 GB per emulator "that one data point ... not a fit". On a Mac, `fit_parallel` (`:1483`) halves the device count at memory pressure level 2 and refuses at level 4. `tools/fixture-e2e.sh` defaults its Android config to `parallel = 2`; `SHOTFLEET_E2E_PARALLEL=1` is for 2-core machines (`tools/fixture-e2e.sh:214-218`).

**Other facts that bite:** the emulator wants about 12 GB free for its data partition (a hosted runner has about 7, so the E1 workflow deletes the preinstalled Android SDK and .NET first; `boot_failure_hint`, `shotfleet.py:2500-2509`); GitHub runners set `XDG_CONFIG_HOME`, so shotfleet names `ANDROID_AVD_HOME` explicitly for `avdmanager` and the emulator (`:2488,2536-2540`); Google's Android CLI rejects an SDK path containing `..`; an emulator counts as booted only when `adb`'s package service answers; Android below API 33 is refused before booting (`tests/test_api33_refusal.py`); on Linux `doctor` checks `/dev/kvm` (`:4220`).

**Running E1 (the Linux fixture) again.** `docs/linux.md:53-77` and `docs/agent-tasks/05-e1-android-on-linux-kvm.md`: a Linux x86_64 machine with usable `/dev/kvm`, 6 GB free memory, 10 GB disk, Tesseract with deu, jpn, ara, tur data, a JDK, then `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android --keep` and record the `machine:` and `cpu:` lines (the script prints them, lines 141-144), the seconds of the `android: shotfleet run` phase and any FAIL lines in `STATUS.md`. The open items are two emulators on 4+ cores and the 18-language timing. Do not trigger `.github/workflows/e1-android-kvm.yml` to do it: it is manual-only, costs runner minutes, and the owner allowed it once (workflow header).

The "13 assertions" in the E1 results versus 29/30 on the Mac: the E1 runs were on the script as of 2026-10-03 (`git log` shows later commits adding the hierarchy assertion, `fd2807a`, 2026-10-04); I could not reconstruct how 13 was counted. Not verified.

## 8.15 The iOS 27.0 simulator hang

- **The list.** `BAD_IOS_RUNTIMES = {"27.0": "its simulators freeze at boot (seen in our own device test runs)"}` (`shotfleet.py:4764`). `pick_ios_runtime` (`:4776`) chooses, when the config has no `runtime`, the newest runtime not on the list and prints one line saying which and why; if 27.0 is the only runtime it uses it with a warning. A runtime set in the config is always used. `doctor` warns when 27.0 is all there is (`:4233-4234`). Matching is on the exact version tuple, so 27.0 only, not 27.0.1 or 27.1 (whether those hang is not verified).
- **Tests.** `tests/test_reliability_017.py:20-73` (`RuntimeGuard`, including `BAD_IOS_RUNTIMES.keys() == {"27.0"}` at `:43`); to change the list, change that assertion too.
- **Evidence.** 2026-10-05: the 4-simulator fixture e2e on iOS 27.0 (24A434) did not finish in 35 minutes at load 735 and swap 21.6 of 22.5 GB; inconclusive because the load alone could explain it (`research/xcode-27-ios27-attempt-2026-10-05.md`). The same day `tools/ios27-repro.sh` (one simulator, one language) passed: 1/1 locales in 78 s (`docs/compat.md:47`). 2026-10-07: a BYOC attempt at 12:28 was killed by its hard limit because iOS 27.0 simulators froze at boot, and pinning iOS 26.4 fixed it (`research/byoc-device-test-2026-10-07/README.md`). The 0.1.7 device check (`research/017-device-check-2026-10-07/README.md`) ran on a Mac with runtimes iOS 18.0, 18.6, 26.4 and 27.0 and no `runtime` in the config; `run` picked 26.4 and said so. So the evidence that 27.0 "freezes at boot" is: several of our own runs plus the 2026-10-07 BYOC attempt; the reproduction is not isolated from machine load (not verified).
- **Untested.** The 4-simulator iOS 27 run (`docs/compat.md:47`); other iOS 27.x; Xcode 26.x (`docs/compat.md:53`).
- **Known wording gap** noted in the 0.1.7 check: `doctor` prints the last runtime simctl lists ("iOS 27.0") even though `run` would pick 26.4; wording only. Whether this was fixed afterwards is not verified (`research/017-device-check-2026-10-07/README.md`).
- **To re-test or remove the entry**, run `IOS27_REPRO=1 tools/ios27-repro.sh [outdir]` under the queue on a quiet Mac with an iOS 27 runtime that `simctl list runtimes` shows Ready; `REPRO_MAESTRO_BIN_DIR=<maestro>/bin` puts another Maestro first. It boots one simulator named `shotfleet-iphone-17-pro-max-1` on `com.apple.CoreSimulator.SimRuntime.iOS-27-0` (it sets `runtime` itself, so the skip list does not apply), deletes it again by UDID if it did not exist before, never touches a runtime, kills every step at its limit (build 90 s, init 60 s, doctor 180 s, run 600 s), and samples progress every 15 s into `progress.log`. PASS is a `PASS` line: exit 0, or exit 1 whose only cause is the fixture's iPad 13-inch device-type warning. Remove the entry only after a 4-simulator fixture e2e on 27.0 passes on a quiet Mac.

## 8.16 CI policy

Every workflow in `.github/workflows/` is `workflow_dispatch` only: `ci.yml` ("claims": `tools/check-claims.sh` on `macos-latest` with Python 3.12 and Node 22, plus a Linux job on Python 3.11 and 3.13 with Tesseract and `aapt2`, warnings as errors), `apple-specs.yml`, `maestro-latest.yml`, `macos-compat.yml`, `e1-android-kvm.yml`. Nothing runs on push, pull request or schedule. The reason is written in the files: "the owner pays for runner minutes, and the local gate tools/check-claims.sh is the real gate" (`ci.yml:2`), "this repo's rule is local checks, no scheduled Actions" (`apple-specs.yml`, `maestro-latest.yml`, `e1-android-kvm.yml` headers), "one run costs money (macOS minutes), so dispatch it once, on purpose" (`macos-compat.yml:1`). `TESTING.md:3` says the same.

Consequences: the local run is the gate (the pre-commit hook, `packaging/release.sh:11`); commits carry `[skip ci]` by convention; `tools/watch-upstream.sh` replaces the two scheduled watchers; never dispatch a workflow to check a change; the Linux Python matrix is only exercised when someone dispatches `ci.yml` (the last result is not recorded in the repo, so whether the suite passes on 3.11 and 3.13 Linux today is not verified). Python 3.14 is not in the CI matrix ("add 3.14 when setup-python has a final release", `ci.yml:23`); the development Mac runs 3.14.8 and the three modules I ran passed on it.

## 8.17 Known flaky tests, slow first runs and load effects

There is no recorded list of flaky unit tests (`grep -ri flak` over `tests/`, `TESTING.md`, `STATUS.md`, `docs/` finds none); the suite is meant to be deterministic. What the history shows:

| Case | What happened | Fix or advice | Source |
|---|---|---|---|
| Warm-up lock test (`test_ocr_wait.WarmUpLock.test_two_warm_ups_take_turns`) | flaky at load about 390: the second process could start before the first held the lock | commit `8d80e45` (2026-10-06): the second process starts only once the first has logged `start`. Any test racing two processes needs an explicit handshake | `git show -s 8d80e45`, `tests/test_ocr_wait.py:253` |
| Mac-only assumptions in `doctor --fix` tests | two tests assumed the machine they were written on and failed on a macOS runner | `tools/pretend-mac.py` reproduces the class | `tools/pretend-mac.py:5-6`, `docs/handoff.md:148` |
| Sockets leaked by older modules | `ResourceWarning`, harmless | none | `docs/handoff.md:150` (not re-verified) |
| Heavy tests under load | a release-script dry run has a 120 s subprocess timeout (`tests/test_release_scripts.py:35`); three tests that called real Vision took 140 to 214 s each before 2026-10-05 | `fake_vision()` (`8a6a070`); on a single timeout error under load, rerun before debugging | `research/speed-2026-10-05.md:71-83`. A prior chapter recorded one such timeout (161 s then 197 s whole-gate); I found no file with those numbers, not verified |
| Parallel processes fighting over locks | two suites at once refusing each other | `USE_DEVICE_LOCK = False` in fake-run modules; `check-claims.sh` runs one module per process | 8.4 |

**Device-run flakiness is the real flakiness.** It is not a unit-test problem and shaped the product (stall watchdog, hung-simulator replacement, capacity warning, `--retry-failed`):

- simulators that stop answering under load (`simctl uninstall` or `terminate` timing out; 15 to 21 GB of swap, load 500 to 900); the 0.1.3 gate failed twice like this (`docs/handoff.md:201-206`), the 0.1.6 gate and the first 2026-10-07 Maestro rerun failed on the iPad half;
- "iOS driver not ready in time" on Maestro 2.11.0 at 4 simulators (8.12);
- an emulator booted outside the device lock breaking an Android gate (0.1.3, run 3);
- memory starvation voiding a gate even at 34 percent free (it was swapping);
- idle Gradle or Kotlin daemons holding about 21 GB, making a gate take 55 minutes instead of about 25 (`docs/handoff.md:173`);
- macOS text recognition: the first `check` after boot or a model update compiles the OCR model in the root `ANECompilerService`, 35 to 122 s at load 550 to 890 and over 10 minutes after a macOS model update (747 s in a 0.1.4 proof). The service is not wedged and a reboot is not needed (`docs/handoff.md:188,222`; `research/workarounds-text-recognition-2026-10-05.md`). Unit tests are protected by `fake_vision`; `RealVisionSmoke` skips if recognition is silent for 90 s.
- first emulator image download and first simulator boot: minutes, not part of any timing figure above unless stated.

When a device test fails: read the Maestro log and the load, swap and memory-pressure figures before blaming the code; rerun only after the Mac is quiet. The gate policy for a failed full run was "combined evidence" from two runs of the same signed build (iOS in one, Android in another), written down in `docs/handoff.md` so nobody reads it as one 65/65 run.

## 8.18 Adding tests

- Put the test next to its neighbours: function-level tests in `tests/test_shotfleet.py`; a feature with several tests in its own module named for the feature. If it needs the fake fleet, subclass `FleetCase` (8.7).
- No network, no real device, no `sleep` for ordering. Use the doubles in 8.7. If two processes must meet, add an explicit handshake.
- A user-visible message is part of the contract: assert on its fixed words.
- Anything that parses or prints a flow, a path, a locale or a size: include a non-English case and a regional case (`pt-BR`, `zh-Hant-HK`).
- A fake run module needs `sf.USE_DEVICE_LOCK = False` (or a class that sets it back on, with a unique lock key and cleanup).
- Changing a sentence on the site, README, docs page or skills makes the guardrails fail until they agree (8.6): that is the intended workflow ([10](10-contributing.md)).
- Changing a documented path breaks `test_handoff_docs.py`.
- A new Mac-only test uses `needs_mac` or an equivalent `skipUnless`; check it with `tools/pretend-mac.py` and, if it matters, on a real Mac.

## 8.19 Differences from docs/architecture/09-testing.md and other existing docs

`docs/architecture/09-testing.md` was written at 0.1.6 (`285e099`) and is a lead, not truth. Verified against the current files:

**In `docs/architecture/09-testing.md`**

| Line | Claimed | Current files |
|---|---|---|
| 13 | 49 modules, 1,173 `def test_` at `285e099` | 51 modules, 1,230 `def test_`, 1,247 loaded cases at `7e5176c` (new: `test_reliability_017.py`, `test_upload_gate_017.py`) |
| 28 | "`TESTING.md` says about 15 seconds" | `TESTING.md:3` already says 52 to 69 s (2026-10-07); the parenthetical is stale |
| 44 | `test_shotfleet.py` 3,514 lines | 3,527 lines, 310 `def test_`, 66 classes |
| 52 | `test_byoc_ios.py` 547 lines | 549 |
| 74 | 36 assertions for iOS, 29 for Android | Android is 30 when the run recorded hierarchy markers (Maestro 2.7.0 and later); 30/30 recorded 2026-10-07 |
| 84-85 | one release-script timeout at load 370, whole check 161 s, rerun 197 s | no file in the repository contains those numbers: not verified |
| 52 | each `test_security.py` test "fails on `c18473f`" | not checkable here (needs that commit's tree) |
| (absent) | | the 0.1.7 modules; `tools/ios27-repro.sh`; `BAD_IOS_RUNTIMES`; `tools/fixture-byoc-e2e.sh` assertion count (20) and hard limit; the in-program device lock versus the agent lock; the flag files |
| 13-14, 16 | OK as claims: layers, `check-claims.sh` mechanics, the pre-commit hook, `pretend-mac.py`, 36/29 counts for 2.0.10 | confirmed |

**In other docs**

| File | Claimed | Current files |
|---|---|---|
| `docs/architecture/13-mismatches.md:10` | `MAESTRO_TESTED` at `:3654`, `MAESTRO_PIN` at `:3690` | now `shotfleet.py:3915` and `:3951` |
| `docs/architecture/13-mismatches.md:11` and `tools/status.sh:3` ("the tests take about 30 s") | full check about 15 s / 30 s | 52 to 69 s on 2026-10-07 (`TESTING.md:3`), 91 s on 2026-10-06 |
| `tools/fixture-app/README.md` | "Android is skipped: there is no Android fixture yet" | `tools/fixture-app-android/` exists and `tools/fixture-e2e.sh --android` runs it (29 or 30 assertions). Its "about 10 minutes" is also an optimistic figure (8.9) |
| `docs/linux.md:14` | `run` on Android emulators "coded, never run ... no KVM in the test machine" | it ran: one emulator passed the fixture on a 2-core hosted runner (`docs/linux.md:101-126`, `docs/handoff.md:68`) |
| `docs/linux.md:55-58` | "Everything before the emulator was run ... the emulator steps were not" | the emulator steps ran on 2026-10-03 (the runner); the section header "Experiment E1" is the checklist, not the state |
| `docs/linux.md:97` | "Do not run E1 again until those are read" | superseded by the second series (`:101-126`), which kept the screenshots and found the cause (the ANR dialog on a 2-core machine) |
| `docs/linux.md:128-132` | "Android emulators on Linux (untried)", "has not been done" | contradicts `:101-126` and `fit_emulators` (`shotfleet.py:1499`) |
| `docs/linux.md:5` | the `ghcr.io/noloman/shotfleet-check` image is described as existing (with a 2026-10-06 verdict from it) | `site/DOCKER_PUBLISHED` does not exist and `tests/test_site.py:338` treats the image as unpublished; whether the image was pushed is not verified (`packaging/docker-check.sh`) |
| `docs/agent-tasks/README.md` (row 05 and "E1 state") | E1 "did not pass"; "sandbox has no hardware virtualization" | it passed with one emulator (above) |
| `docs/agent-tasks/05-e1-android-on-linux-kvm.md` ("Context") | "The emulator was never started" | the "What is already known" paragraph of the same file contradicts it; the paragraph is right |
| `docs/agent-tasks/01-maestro-2-11.md` ("Context") | `MAESTRO_TESTED` "is still `("2.0.10",)`" | done 2026-10-04; it is `("2.0.10", "2.11.0")` (the agent-tasks README row says DONE) |
| `docs/compat.md:38` | Python 3.14.0rc2 tested, "the final 3.14 release is not out" | 3.14.8 runs on the development Mac; three test modules passed on it (2026-10-08) |
| `docs/compat.md:47` | iOS 27 works on one simulator; no mention that `run` now skips 27.0 by default or of the 2026-10-07 boot freezes | `shotfleet.py:4764`, `research/byoc-device-test-2026-10-07/README.md`; there is no 0.1.7 row at all |
| `docs/compat.md:14-18` | "A unit test fails if that list stops matching what `shotfleet.py` passes" | one direction only (`tests/test_maestro_compat.py:85-89`, 8.12) |
| `docs/handoff.md:53-61` | the promotion checklist | incomplete: also `docs/compat.md`, `docs/linux.md:69`, `docs/weekend-support.md:39`, `tests/test_claims_site.py:75-76`, `tests/test_handoff_docs.py:23-25` and four claims rows (8.12) |
| `docs/device-queue.md:14` | quiet check: free memory 20 percent, load under 300 | later start rules are stricter (8.13); the file also does not mention the in-program `flock` or that `fixture-e2e.sh` does not take the agent lock |
| `.github/workflows/e1-android-kvm.yml` header | "five runs" | `docs/linux.md` records six in the first series plus seven in the second |

## 8.20 Not verified

- That the full gate is green at `7e5176c`: I did not run `tools/check-claims.sh` or the whole suite (instructed not to). Only the static counts, a loader count (1,247 cases) and 36 tests in three modules (OK, 1 skipped) are measured.
- Today's number of worker checks (37 `check(` call sites; 59 recorded at `285e099`), and whether Node 22 versus 26.10.0 matters.
- Which unit tests still call the real macOS text recognition besides `RealVisionSmoke` (`research/speed-2026-10-05.md` is dated).
- Whether each "needs: none" module passes on Linux; the Linux CI job was not dispatched and no result is recorded.
- Whether a Maestro newer than 2.11.0 exists today (no network was used; last record 2026-10-07).
- Whether iOS 27.0.x or later 27.x simulators also freeze; the 4-simulator iOS 27 run; Xcode 26.x; macOS 13 and 26.0 to 26.1.
- The two-emulator case on 4 or more cores; an 18-language Linux run.
- How E1's "13 assertions" relates to the current 29/30 (8.14).
- How `.build/render` (needed by `tools/langmatrix.py`) is built.
- Whether the `doctor` wording gap noted in the 0.1.7 device check was fixed.
- The old release-script timeout figures (161 s, 197 s) and the claim that each `test_security.py` test fails on `c18473f`.
- Whether `ghcr.io/noloman/shotfleet-check` has been pushed.
- Anything about `/tmp/shotfleet-device-queue.md`: it exists but I did not read it.
