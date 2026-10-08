# 1. Code layout, conventions, config and output folders

Back to the [index](../ARCHITECTURE.md).

## Repository map

| Path | What it is |
|---|---|
| `shotfleet.py` | The whole program: 5,707 lines, about 400 KB (at `cf43aa6`), standard library only. |
| `ocr.swift` | 56-line Swift helper that wraps macOS Vision text recognition and NaturalLanguage detection. Built to `.build/ocr` from source, or shipped prebuilt in the release. |
| `skill/` | Three agent skills (`shotfleet`, `shotfleet-ci`, `shotfleet-review`) with `references/`. Shipped inside the release (`--add-data skill:skill`) and copied by `shotfleet skill install`. |
| `packaging/` | Build, sign, notarize, package, publish, go-live scripts, pinned build inputs (`requirements-build.txt`). See [07](07-packaging-and-release.md). |
| `tools/` | Developer tools: fixture apps and end-to-end scripts, release-candidate, verify-release, watchers for upstream Maestro and Apple's size page, guides generator, `check-claims.sh`. |
| `site/` | The website (`public/`, static), the Cloudflare Worker (`worker.js`) and its tests, wrangler configs. See [08](08-website.md). |
| `tests/` | 51 test modules plus `claims.json` (the claims register) and `fixtures/`. See [09](09-testing.md). |
| `docs/`, `research/`, `marketing/` | Docs for buyers and agents, dated research notes, launch material. `research/` is the "why". |
| `examples/crossfittracker/` | A real app's config and flows (iOS and Android) used as the worked example. |
| `Dockerfile` | The Linux `check` image (compiled program plus Tesseract). |
| `.githooks/pre-commit` | Runs `tools/check-claims.sh`. Enable once per clone: `git config core.hooksPath .githooks`. |
| `.github/workflows/*.yml` | All `workflow_dispatch` only. Nothing runs on push. See [09](09-testing.md). |

Top-level files worth knowing: `README.md` (buyer docs, tested), `CHANGELOG.md` (the release gate reads its top heading), `STATUS.md` and
`docs/handoff.md` (project state, stale in places), `TESTING.md`, `DISTRIBUTION.md`, `LAUNCH.md`, `PLAN.md`, `ROADMAP.md`, `STRATEGY.md`.

## Why `shotfleet.py` is one file

There is no written decision record for this. What the repo does show is a set of things that are easy because everything is one module, and
that would each need changing if it were split:

- **Tests import it as a module** (`import shotfleet as sf`) and patch module-level names (`mock.patch.object(sf, "GUMROAD_API", ...)`,
  `sf.USE_DEVICE_LOCK = False`, `sf.LICENCE_FILE`). Almost all 49 test modules depend on that.
- **Release scripts edit and read it with `sed` and regexes.** `packaging/go-live.sh:85` and `tools/release-candidate.sh:96` rewrite the
  `GUMROAD_PRODUCT_ID = ...` line; `packaging/build.sh`, `pkg.sh` and `publish.sh` read `VERSION = "..."`. The release-candidate script builds a
  temp **copy** of the file with a test product id so the licence gate is on without touching the repo.
- **PyInstaller freezes one entry script.** `getattr(sys, "frozen", False)` is the switch between "a developer's source checkout" (no licence
  gate, helper built on demand) and "a released build" (licence gate, helper bundled at `sys._MEIPASS`).
- **Everything is imported at the top** on purpose: a Homebrew Python upgrade in the middle of a run deletes the old library
  folder, and lazy imports would then fail (seen 2026-10-01).
- The project's style (the `ponytail:` comments) prefers the smallest thing that works with a named ceiling over structure for its own sake.

The cost is real: 5,700 lines in one namespace, long functions (`ios_run_inner` is about 190 lines with nested closures, `cmd_check` about 230), and
module-level mutable state (see "Global state" below). If you split it, keep `import shotfleet` working and keep every name the tests patch.

## How `shotfleet.py` is organised

Order in the file, with the section banners (`# ---------- name ----------`) and what lives there. The sections are in this order; for line numbers use [the generated function map](../engineering/12-function-map.md), which lists every function by section and says which commit it was made at.

| Section | Key contents |
|---|---|
| Header | usage docstring (lists only 5 of the 9 commands, see the appendix), Python 3.11 guard, imports, `VERSION`, `Fail`, config schema constants `KEYS`, `REQUIRED`, `TABLES`, `HOOK_EVENTS`, `CAPTURE_KEYS` |
| Config validation and loading | `check_tables`, `check_capture`, `check_expect`, `read_doc`, `platforms_in`, `check_section`, `load_config` |
| Locale tables | `APP_STORE`, `PLAY` (store listing codes), `PRIMARY`, `CANON`, `canon`, `store_code`, `SELECTOR_KEYS`, `sh`, `aapt2` |
| `strings` | `parse_strings_text` (a `.strings` parser so Linux needs no `plutil`), `plist_to_json`, `load_strings`, `stringsdict_forms`, `add_cvr` (Compose Multiplatform) |
| `strings from source files` | `locale_from_path`, `icu_forms`, `parse_js_translations` (reads `.ts`/`.js` translation objects as data, never runs them), `read_translation_file`, `load_strings_apk`, `partly_translated`, `FRAMEWORKS`, `framework_hint`, `shipped_locales` |
| Flow rewriting | `with_fallback`, `resolve_base`, `SYSTEM_BUTTONS`, `translate_flow`, `redirect_screenshot`, `with_app_id`, `inputs_for`, `flow_mapping_lines`, `localize_flow`, `pause_after_screenshot` |
| `simulators` | timeouts, `Sim`, `healthy_installs`, `mark_hung` / `replace_hung`, `run_setup`, `make_pool` |
| `host safety` | `descendants`, `ios_screen_texts`, `capture_texts`, `collect_shots`, `run_guarded`, `fit_parallel`, `fit_emulators` |
| `capacity planner` | `Reading`, `Plan`, `plan_capacity` (pure), `read_capacity` (impure), `capacity_warn`, `overload_note`, `flow_parse_note` |
| Failure details | `flow_steps`, `landscape_tap_hint`, `failed_hierarchy`, `failure_details` |
| `run` | `kill_stale_drivers`, `device_type_id`, `default_device_type`, `cmd_run`, `run_hook`, `run_platform`, `capture_platform`, `device_lock`, `ios_run`, `ios_run_inner` |
| `bring your own capture` | `xcresult_pngs`, `fastlane_cache`, `capture_build`, `find_xctestrun`, `xctestrun_with_language`, `set_sim_language`, `capture_result`, `fastlane_pngs` |
| `android` | SDK discovery `find_sdk`, `find_image`, `sdkmanager_commands`, `DEMO_MODE`, `Emu`, `start_emu`, `wait_booted`, `ANDROID_DEVICES`, `android_pool`, `android_vars`, `android_flow`, `hierarchy_texts`, `android_run` / `android_run_inner` |
| `check` | OCR plumbing (`ocr_tool`, `ane_state`, `warm_up_ocr`, `read_text`, Tesseract helpers), text normalisation `norm`, format strings (`SPEC`, `format_regex`), `string_tables`, `judge_screen`, system dialog and banner detection, `find_screenshots`, `cmd_check`, `write_gallery` |
| `doctor / init / export` and `doctor --fix` | `latest_release`, `find_java`, Maestro pin and interface (`MAESTRO_INTERFACE`, `MAESTRO_TESTED`, `MAESTRO_PIN`), `download`, `install_maestro`, `install_jre`, `fix_plan`, `cmd_doctor`, `unpack_build`, `FLOW_TEMPLATE` |
| `project detection` and init | `Project`, `detect_project`, `find_builds`, `cmd_init`, `cmd_init_capture` |
| Store rules and export | `APPLE_SIZES`, `png_alpha`, `image_info`, `store_rules`, `blank_screenshot`, `device_runs`, `cmd_export` |
| Entry | `COMMANDS`, `cmd_skill`, `main` |
| MCP | `MCP_TOOLS`, `mcp_summary`, `mcp_call`, `cmd_mcp` |
| `licence`, dispatch | licence constants, `gumroad_api`, `baked_release_date`, `check_update_window`, `write_json_atomic`, `gumroad_fetch`, `gumroad_verify`, `cmd_activate`, `key_licence`, `mac_licence`, `require_licence`, `apply_free_tier`, `main_cmd`, `check_build`, `check_any`, `main_dispatch` |

The file is organised by feature, not by layer. There is no class hierarchy: the only classes are tiny (`Fail`, `Sim`, `Emu`, `Table`, `Reading`,
`Plan`, `Project`, `OcrBusy`, `NoLicence`).

### Conventions

- **Functions, module constants, `ponytail:` comments.** A constant in caps near the code that uses it. A `ponytail:` comment records a
  deliberate shortcut and its ceiling ("one OCR per 4 at a time", "first plural block only"). Respect them; lift the ceiling only with a measurement.
- **Pure core, impure edge.** The capacity planner shows the pattern: `plan_capacity` is pure and unit-tested with numbers; `read_capacity`
  asks the Mac. `translate_flow`, `judge_screen`, `store_rules` and the parsers are pure functions of their inputs. New logic should follow it, because
  tests run with no devices.
- **User-facing errors are `Fail`.** `raise Fail("one sentence that says how to fix it")` ends in `shotfleet: <message>` on stderr and exit 2
  (`main_dispatch`). `RuntimeError`, `ValueError`, `OSError` and `subprocess.TimeoutExpired` get the same treatment, so low-level helpers
  raise `RuntimeError` with a worded message. Every message names the fix: a command to run, a config key to set. The tests check wording.
- **Never a traceback for a known failure.** `tests/test_shotfleet.py` has tests that assert "Traceback" is absent. A bare `Exception` in the MCP
  server is caught per call (`mcp_call`) so one bad call cannot kill the server.
- **Subprocesses are argv lists, never `shell=True` on untrusted input.** The one `/bin/sh -c` is the user's own `[hooks]` and `[capture] build`
  strings (see [11](11-security-and-privacy.md)).
- **Output goes to a file, not a pipe, when a child can outlive its parent.** `run_guarded` sends Maestro's output to a temp file because a
  daemonised helper that inherited the pipe would block `communicate()` after the kill.
- **Timeouts everywhere a device or the OS can hang.** Every `simctl` call has a timeout (`Sim.run`); every `adb` call has one (`Emu.adb`,
  `Emu.adb`); Maestro runs under a stall watchdog (`run_guarded`); text recognition under a budget. See [02](02-capture.md).
- **Locale spellings are normalised through `canon()`**: `zh-CN` is `zh-Hans`, `iw` is `he`, `nb` stays `nb`. Always compare after `canon`.
- **Text is compared after `norm()`**: NFKD without accents, casefolded, bidi marks removed, native digits to ASCII, single spaces.
- **Wording rules.** No em dashes in any public text or in these docs (tests enforce it for the site, the skills and the docs page); no emoji.
  Plain English, first person where the author speaks.

### Exit codes

Defined by behaviour, not by constants:

| Code | Meaning | Where it comes from |
|---|---|---|
| 0 | Everything worked and nothing is wrong | return value of the `cmd_*` function |
| 1 | The work ran and found problems: check problems, a failed language in `run`, a failing `after_*` hook, `--strict` with unverified screens, `doctor --fix` step failed, `export` skipped a bad language | `cmd_check` returns `1 if problems or (strict and not_verified) else 0`; `ios_run_inner` returns `max(cmd_check(...), 1 if failed else 0)`; `cmd_export` returns `0 if not bad else 1` |
| 2 | Setup error: bad config, missing tool, no licence for `export`, a `before_*` hook failed, device lock held | any `Fail`/`RuntimeError`/`ValueError`/`OSError`/`TimeoutExpired` reaching `main_dispatch`; `doctor` returns 2 when neither platform is ready |
| 130 | Interrupted (Ctrl-C) | `KeyboardInterrupt` handler; SIGTERM and SIGHUP are turned into `KeyboardInterrupt` by `main_cmd` so CI cancellation cleans up |
| 124 | Only inside the hook runner: a hook timed out. It becomes exit 2 (`before_*`) or 1 (`after_*`) | `run_hook` |

`--json` wraps this: `main()` redirects stdout to stderr while the command runs, then prints one JSON object
`{"exit": code, ...report}` on stdout. Progress text therefore never pollutes the JSON.

### Logging

There is no logging framework. Everything is `print`:

- Progress and results go to **stdout** (`captured 18/18 locales in 534s`, `ok   de  4/4 screenshots`).
- Hints, notes and warnings that must not break `--json` go to **stderr** (`note:`, `hint:`, `warning:` prefixes). `framework_hint` is deduplicated through
  the `HINTED` set so a run over many devices says each hint once.
- Maestro's and xcodebuild's own output is written to files in the output folder (`maestro1.log`, `maestro_r1.log`, `build.log`, per-language
  `.work/capture/attemptN/<lp>.log`). `run` prints the path when something failed.
- Emulator output goes to `$TMPDIR/shotfleet-emulator-logs/emulator-<port>.log` (`EMU_LOG_DIR`) and its tail is printed when an emulator
  dies before booting.
- Over MCP all of this is captured into a `StringIO` and returned (`mcp_call`).

### Global state

Module-level mutable state exists and tests reset it. Know it before adding more:

| Name | Purpose |
|---|---|
| `OUR_SIMS` | UDIDs of simulators shotfleet booted, so cleanup and `kill_stale_drivers` never touch anyone else's |
| `NO_HOOKS`, `NO_BUILD`, `CONFIG_COMMANDS` | set from `--no-hooks` / `--no-build` or by MCP; `CONFIG_COMMANDS` is False during an MCP `run` without `hooks: true` (see [06](06-mcp-and-skills.md)) |
| `USE_DEVICE_LOCK` | tests that run a fake `run` set it False so two test suites never refuse each other |
| `LOCALE_CAP` | the free-tier cap, set by `apply_free_tier`, which resets it to None first (the MCP server calls it on every `run`) |
| `RELEASE_DATE` | the build day from the frozen `_release` module, or None from source; read once at import |
| `REPORTS`, `LAST_REPORT` | every `check.json` this call wrote, for `--json` and MCP summaries |
| `OCR_DEADLINE` | the running check's text-recognition budget |
| `HINTED`, `EXPORT_RESULT` | dedupe hints; what `export --json` prints |
| `functools.cache` on `vision_languages`, `tesseract_languages`, `locale_tags`, `java_env`; `lru_cache` on `norm` | safe to clear in tests (`java_env.cache_clear()` is called after installing a JRE) |

MCP runs several commands in one long-lived process, so `mcp_call` resets `LAST_REPORT` and `REPORTS` at the start of each call and restores
`NO_HOOKS` in a `finally`.

## The config file: `shotfleet.toml`

Parsed with `tomllib` (`read_doc`). The schema is enforced in code, so the code is the reference; the README "Config" section is the
buyer-facing copy.

Top-level tables (`TABLES`): `ios`, `android`, `hooks`, `overrides`, `inputs`, `expect`, `capture`. An unknown table is refused with a
"did you mean" suggestion (`difflib.get_close_matches`), because a typo like `[hook]` would otherwise be ignored for a multi-minute run.

`[ios]` and `[android]` keys (`KEYS`), type-checked by `check_section`:

| Key | Type | Platform | Meaning |
|---|---|---|---|
| `flow` | str | both | Maestro flow, default `flow.yaml`. Forbidden together with `[capture]`. |
| `out` | str | both | Output folder; default `out`, or `out-ios` / `out-android` when the file has both platforms |
| `parallel` | int >= 1 | both | Devices at once, default 4 |
| `locales` | list of str | both | Restrict languages; an empty list is refused (it would silently capture everything) |
| `base_locale` | str | both | Language the flow is written in, default `en` |
| `strings` | str or list | both | Glob(s) of translation files, or one folder of `.lproj`, instead of reading the build |
| `timeout_s`, `stall_s` | int >= 1 | both | Per-batch timeout (default 600) and no-new-screenshot watchdog (default 900, `STALL_S`) |
| `capacity` | `"warn"` or `"off"` | both | The memory warning. `"adjust"` is refused as not available yet |
| `app`, `bundle_id`, `device_type`, `device_types`, `runtime`, `simctl` | str / list | iOS | Simulator `.app`, override of the id read from `Info.plist`, device type(s), runtime id, per-simulator `xcrun simctl` commands |
| `apk`, `package`, `avd`, `avd_tablet`, `avd_tablet-7`, `system_image`, `devices`, `shell` | str / list | Android | APK, package override, emulator names, system image, `["phone", "tablet", "tablet-7"]`, per-emulator `adb shell` commands |

Internal keys that `load_config` adds and the rest of the code reads: `_config` (path), `_hooks`, `_overrides`, `_inputs`, `_expect`, `_capture`,
and at run time `sim_prefix`, `multi_device`, `device` (`capture_platform`).

Other tables:

```toml
[hooks]                              # strings or lists of strings, run by /bin/sh in the config's folder
before_run = "make build-sim"        # events: before_run, after_run, before_export, after_export
hook_timeout_s = 1800                # default 600 per command

[overrides.tr]                       # per language: English text -> text to tap; "re:" prefix = regular expression
"Next" = "İleri"

[inputs]                             # values for `inputText: ${name}`
name = "Alex"
[inputs.ja]
name = "田中"

[expect.01_home]                     # a screenshot's name; keys any / all / not, optional [expect.<shot>.<locale>]
any = ["Senior iOS Engineer"]

[capture]                            # iOS only, instead of flow: your own XCUITest tests
build = "xcodebuild build-for-testing -scheme MyApp -destination 'generic/platform=iOS Simulator' -derivedDataPath .shotfleet/build"
xctestrun = ".shotfleet/build/Build/Products/*.xctestrun"
only_testing = ["MyAppUITests/ScreenshotTests"]
screenshots = "auto"                 # attachments | fastlane | auto
timeout = 900
```

Hook behaviour (`run_hook`): each command is `["/bin/sh", "-c", cmd]` with `cwd` = the config's folder, stdout redirected to stderr so
`--json` keeps stdout clean, a per-command timeout, and these variables: `SHOTFLEET_EVENT`, `_VERSION`, `_CONFIG` on every event; `before_run` and
`after_run` also get `_PLATFORM`, `_OUT`, `_BUNDLE_ID`, `_LOCALES`; `after_run` adds `_EXIT`, `_PROBLEMS`, `_REPORT`; export hooks get `_FASTLANE`,
`_REPORT`, `_PLATFORM`, `_OUT` (and `_EXIT` after). A failing `before_*` hook raises `Fail` (exit 2); a failing `after_*` hook prints a line and
makes the exit code 1. `--no-hooks` and MCP without `hooks: true` skip them all.

Validation order inside `load_config` matters for the error you get: tables, then section keys and types, then "`[capture]` needs `[ios]`", then
"flow and capture are exclusive", then the build itself (`Info.plist` readable, not a device build, `bundle_id` matches; APK readable, `package`
matches), then "Maestro installed" (skipped for `[capture]`).

## Output folders and files

A run writes everything under `out/` (or `out-ios/`, `out-android/`, or `out/<device>/` for several device types):

```
out/
  run.json            what the run did (see below); `check` reads it to find the build and the translation files
  check.json          the check report
  index.html          the grid: a row per language, a column per screen, problems outlined and marked in words
  raw/<locale>/<shot>.png        the screenshots, one folder per language
  raw/<locale>/<shot>.texts.json the app's own screen text for that screenshot (a JSON list of lines), when it was read
  maestro1.log, maestro2.log     iOS: Maestro output of attempt 1 and the retry
  maestro_r1.log, maestro_retry1.log   Android: one per round / retry round
  junit1.xml ...      Maestro's JUnit reports (iOS junit<attempt>.xml, Android junit_<tag>.xml)
  build.log           [capture] only: the output of the build command
  .work/              flows, Maestro debug output, staging; wiped per run (flows, debug, shots, tmp), safe to delete
```

Multi-device runs (`device_types = [...]` on iOS, `devices = [...]` on Android) write `out/<device-slug>/` each (for example
`out/iphone-17-pro-max/` and `out/ipad-pro-13-inch-m5-12gb/`), and `clear_single_run` removes an older single-device `run.json` first
because `device_runs()` decides "single or multi" by whether `out/run.json` exists. `check` and `export` accept the parent folder and loop
over the sub-folders.

`run.json` (written at the end of `ios_run_inner`, and `android_run_inner`):

```json
{
 "locales": {"de": {"untranslated_selectors": [], "ok": true, "error": null, "screenshots": 4, "attempts": 1}},
 "config": "/abs/path/shotfleet.toml",
 "strings": ["/abs/glob"], "base_locale": "en",          // only when `strings` was used
 "wall_seconds": 534, "simulators": 4, "app": "/abs/My.app"   // Android: "emulators", "apk", "platform": "android", "device", "hierarchy_markers"
}
```

Per-language results also carry `retried` (Android), `device` (the emulator that ran it) and `hierarchy_texts` (how many screenshots got app text).
`check` re-derives the right strings from `run.json` (`cmd_check`): `strings` globs if present, else the `app` or `apk` path.

`check.json` (`cmd_check`):

```json
{"screenshots": [{"file": "de/01_home.png", "src": "raw/de/01_home.png", "sha": "<12 hex>", "lang": "de", "chars": 812, "evidence": "hierarchy|ocr"}],
 "problems": ["de/01_home.png: shows en strings (7 lines) more than de (1)"],
 "notes": ["..."],
 "unverified": ["de/03_x.png"]}
```

`problems` fail the check; `notes` never do; `unverified` lists screens nobody could read (see [03](03-check.md)). `evidence` is `"hierarchy"` when
the text came from the app (`.texts.json`) and `"ocr"` otherwise, even though the name says hierarchy for iOS too.

State outside the output folder:

| Path | Written by | Purpose |
|---|---|---|
| `~/Library/Application Support/shotfleet/licence.json` | `activate` | The licence (plain text, unsigned). Linux has the same relative path under `~/Library/...` because the constant is not platform-aware. |
| `~/.shotfleet/` (or `$SHOTFLEET_HOME`) | `doctor --fix` | Maestro, a JRE, downloads, `hung-simulators/<UDID>` markers |
| `~/Library/Application Support/shotfleet/app` | `install.sh` | The installed program folder; a link to it goes on the PATH |
| `/tmp/shotfleet-<key>.lock`, `/tmp/shotfleet-ocr-warmup.lock` | `device_lock`, `ocr_warmup_lock` | flock files; the OS drops the lock when the process dies |
| `~/Library/Caches/tools.fastlane/screenshots` | fastlane's SnapshotHelper; shotfleet creates it temporarily for `[capture]` | See [02](02-capture.md) |
| `~/.android/avd` (or `$ANDROID_AVD_HOME`) | `android_pool` | The `shotfleet_android*` emulators and their `shotfleet` snapshot |
| `$TMPDIR/shotfleet-emulator-logs/` | `start_emu` | Emulator output |
