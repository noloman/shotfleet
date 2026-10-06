# 9. Testing

Back to the [index](../ARCHITECTURE.md).

**The gate is local.** Every workflow in `.github/workflows/` is `workflow_dispatch` only (`ci.yml`, `apple-specs.yml`, `maestro-latest.yml`, `macos-compat.yml`,
`e1-android-kvm.yml`). Nothing runs on push or pull request, because the owner pays for runner minutes. Never trigger a workflow to "see if CI passes"; the local run is the
check, and commits say `[skip ci]`. `tools/watch-upstream.sh` runs the two scheduled-style watchers on your own machine instead.

## 9.1 Layers

| Layer | What | Needs | Where |
|---|---|---|---|
| Unit | the program's functions and CLI, with fakes for simulators, emulators, Maestro, Xcode, Gradle, the network | Python 3.11+; nothing else (Mac-only tests skip elsewhere) | `tests/test_*.py` (51 modules, 1,127 `def test_` at `c18473f`) |
| Site and claims | pages, docs, skills, the claims register, release scripts against fakes | Python, Node 22 for the worker tests, optionally Playwright with Chromium | `test_site*.py`, `test_docs.py`, `test_claims*.py`, `test_agent_skills.py`, `test_release_scripts.py`, `site/worker.test.mjs`, `tests/browser_site.cjs` |
| Fixture end-to-end | the real program on real simulators and emulators against `tools/fixture-app` and `tools/fixture-app-android` | a quiet Mac, Xcode, the Android SDK, `SHOTFLEET_E2E=1`, the device lock | `tools/fixture-e2e.sh`, `tools/fixture-byoc-e2e.sh` |
| Release proofs | the frozen, signed build: quarantined run, `env -i` start, TLS, licence against a fake Gumroad, `install.sh` | a build and a Mac | `tools/release-candidate.sh`, `tools/verify-release.sh`, `tools/selftest.sh` |
| Real apps | CrossfitTracker, Remoti, wger, an Expo template, kotlinconf-app | the apps and a quiet Mac | recorded in `research/` and `STATUS.md`, not automated |

## 9.2 Running everything locally

```sh
sh tools/check-claims.sh > /Users/manu/Developer/shotfleet-rc-build/some-check.out 2>&1; echo rc=$?
```

What it does (`tools/check-claims.sh`): runs each `tests/test_*.py` module as **its own process** (`python3 -m unittest discover -s tests -p <module>.py`), largest file first, `xargs -P` at half the
cores (`CHECK_JOBS=n` to choose), because most test time is waiting on subprocesses, not CPU; then `node site/worker.test.mjs`; prints **one line** (`check-claims: ok (python: Ran
1121 tests in 101s OK (skipped=21) ; worker: 59 checks ok)`) and the full output only on failure. Exit 0 or 1. Measured on 2026-10-06 at `c18473f` on a 10-core Mac under a load average of about 370 from other
sessions: 101 s. (`TESTING.md` says about 15 seconds; that was an earlier, smaller suite on a quiet machine.)

Rules for the people running it:

- **Redirect to a file and read the exit code of the check itself.** Do not write `sh tools/check-claims.sh | tail -1; git push`: a pipe's status is the last command's, so a red run can look green and
  get pushed. The convention is `...> file 2>&1; echo rc=$?` and push only when that `rc` is 0.
- Use a durable folder (for example `shotfleet-rc-build/`), not `/tmp`, for outputs you may need after a reboot.
- To enable it as a pre-commit check once per clone: `git config core.hooksPath .githooks`.
- One module: `python3 -m unittest tests.test_shotfleet`; one class or test by name as usual. To run a module as if on an Apple-silicon Mac: `python3 tools/pretend-mac.py test_doctor_fix` (flips
  `sys.platform` and the CPU only; no Xcode, Vision or plutil; a screen for tests that assume the machine they were written on, not a substitute for a Mac).
- Skips (21 on the reference run) are by design: `aapt2` not installed, Tesseract missing a language, Playwright or Chromium missing (`browser_site.cjs` exits 77), Mac-only tests off a Mac
  (`RealVisionSmoke`, `test_fixture_e2e` script tests), Node missing. A skip is not a pass for what it covers: run the matching device or Mac step when you change that area.
- Device and release scripts refuse without an opt-in (`SHOTFLEET_E2E=1`, `SHOTFLEET_RC=1`) and, on the shared development Mac, need the device lock ([02](02-capture.md#29-device-locks-and-sharing-a-machine)).

## 9.3 What the unit tests look like

- `tests/test_shotfleet.py` (3,183 lines) is the main suite, in many small classes (`TranslateFlow`, `LocalizeFlow`, `AndroidFlow`, `Locales`, `JudgeScreen`, `Export`, `StoreRules`,
  `Mcp`, `Licence`, `GumroadLicence`, `CheckAnyFolder`, `MultiDevice`, ...). The `G1...` classes are the "gate 1" detector and exit-code proofs.
- Tests import the program as a module (`import shotfleet as sf`) and patch module names. Typical patches: `sf.LICENCE_FILE` to a temp file, `sf.GUMROAD_API` to a local server,
  `sf.USE_DEVICE_LOCK = False`, `sys.frozen` to True to turn the licence gate on, `sf.sh` or `sf.run_guarded` to a fake that returns canned `CompletedProcess` objects, `sf.make_pool` and
  `sf.android_pool` to fakes that return fake devices, `sf.read_text` to a fake OCR (`fake_vision()` in `tests/test_cli_claims.py`).
- **Pure functions get number-in, verdict-out tests**: the capacity planner (`test_capacity_planner.py`), `judge_screen`, `store_rules`, `translate_flow`.
- **Fixtures** live in `tests/fixtures/`: `strings-fixture.apk` (a 5 KB APK with strings in several locales, so the `aapt2` reader is tested for real where `aapt2` exists), Maestro failure log excerpts
  (`maestro-failure/ipad-landscape.log`, a real iPad log with the app id replaced), Android hierarchy samples.
- Specialised modules: `test_byoc_ios.py` (547 lines: `[capture]` with a fake `xcodebuild`, result-bundle manifests, the fastlane cache dance), `test_ocr_wait.py` (warm-up, lock, budget, with
  scripts standing in for the Swift helper), `test_doctor_fix.py` (downloads against a local HTTP server, checksum refusal, zip-slip refusal), `test_release_scripts.py`
  (`publish.sh`, `verify-release.sh`, `preflight.sh`, `notary-check.sh` against a fake `wrangler`, a fake `notarytool` and a local web server), `test_golive.py` (`go-live.sh --dry-run`,
  `smoke.sh`), `test_portable.py` (readers that must work with Apple tools hidden).

### Test doubles

| Double | Where | Stands in for |
|---|---|---|
| Fake Gumroad HTTP server | `tests/test_shotfleet.py` (`GumroadLicence`, `H` handler), `tools/release-candidate.sh` (`FakeGumroad`, controllable: outage, refund, uses), `tests/test_release_candidate.py` | `api.gumroad.com/v2/licenses/verify`; built from Gumroad's documentation and source, so its behaviour is an assumption until a real paid sale and refund (see [05](05-licensing.md)) |
| Fake `wrangler`, fake `notarytool`, local `ThreadingHTTPServer` | `tests/test_release_scripts.py`, `tests/test_golive.py` | Cloudflare and Apple, for the release scripts |
| Fake Maestro folder | `tests/test_maestro_compat.py` (`fake_maestro(version, flags, strings)`) | a Maestro install for `tools/maestro-compat.py` |
| Local releases and specs servers | `tests/test_latest_maestro.py`, `tests/test_apple_specs_watch.py` (`SHOTFLEET_MAESTRO_RELEASES`, `SHOTFLEET_APPLE_SPECS_URL`) | GitHub and Apple's page |
| Fake devices | `FakeSim`, `FakeEmu` classes in `test_shotfleet.py`, `test_capture_reliability.py`, `test_claims_unit.py` | simulators and emulators |
| Stubbed `/api/*` in Chromium | `tests/browser_site.cjs` | the worker, to test `forms.js` and `analytics.js` |
| In-memory KV and limiter | `site/worker.test.mjs` | Cloudflare KV and the rate limiter |

## 9.4 Fixture end-to-end

`tools/fixture-e2e.sh` (about 410 lines; the assertion helper is the Python at the end of the file, which `tests/test_fixture_e2e.py` loads and tests against fakes). Phases: pre-flight (5 GB free,
memory pressure not critical, Linux: KVM and Tesseract data), build the fixture app, `init`, `doctor`, `run` on iPhone and iPad for `de`, `ja`, `ar`, `tr`, `check`, `export`, then
**plant a copied screenshot and delete one** and assert `check` reports both, then the Android half the same way on the phone emulator. It prints `PASS ...` or `FAIL ...` per assertion and
`PASS: all N assertions passed` (36 for iOS, 29 for Android) or exits 1. It runs from `shotfleet.py` or, with `SHOTFLEET_BIN=<binary>`, against a built release, which is how the release gate uses it.
Its cleanup shuts down only simulators named like shotfleet's pools and, if it started emulators, only `emulator-57xx`.

## 9.5 Flaky-test and flaky-run history

There is no recorded list of flaky unit tests; the suite is expected to be deterministic. What the history shows:

- **Warm-up lock test** (`tests/test_ocr_wait.py`): was flaky at load around 390 because the second process could start before the first held the lock; commit `8d80e45` (2026-10-06)
  starts the second process only once the first holds the lock. Lesson: any test that races two processes needs an explicit handshake, because this Mac is often at load 300 to 900.
- **Mac-only failures found late:** two `doctor --fix` tests assumed the machine they were written on and failed on the macOS CI job. `tools/pretend-mac.py` was written to reproduce that class of failure.
- **Release-script tests under heavy load:** `test_release_scripts.DryRun.test_real_tree_version_extractors_work_on_the_real_files` runs `publish.sh --dry-run` with a 120 s subprocess timeout and errored once
  while this Mac was at load about 370 and the full check took 161 s; the rerun passed (197 s). A single timeout error under load: rerun before debugging.
- **Older modules leak a few sockets** (`ResourceWarning`); harmless, not from newer tests (`docs/handoff.md`).
- **Parallel test processes must not fight over devices or locks:** a fake `run` sets `USE_DEVICE_LOCK = False` so two suites at once never refuse each other; `check-claims.sh` runs one module per process.
- **Device-run flakes (not unit tests) are the real flakiness**: simulators that stop answering under load, `iOS driver not ready in time` on Maestro 2.11.0 at 4 simulators (9 of 19 languages needed the
  retry; the same run on 2.0.10 needed none), unlocked emulators breaking a gate, memory starvation at 15 GB of swap. These shaped the product (stall watchdog, hung-simulator replacement, capacity
  warning) and the gate rules in [07](07-packaging-and-release.md#74-the-release-gate-test-the-exact-files). If a device test fails, read the Maestro log and the load figures before blaming the code.

## 9.6 Adding tests

- Put a test where its neighbours are (function-level in `test_shotfleet.py`, a feature with several tests in its own module named for the feature).
- A user-visible message is part of the contract: assert on its fixed words. A traceback for a known failure is a bug; assert it is absent.
- Anything that parses or prints a flow, a path, a locale or a size: include a non-English and a regional case (`pt-BR`, `zh-Hant-HK`).
- If your change touches a sentence on the site, README, docs page or skills, the claims and skills tests will fail until those agree; that is the intended workflow ([10](10-making-changes.md)).
- No network, no real devices, no `sleep` for ordering. Use the fakes above.
