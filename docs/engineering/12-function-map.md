# 12. Function map of `shotfleet.py`

Scope: a navigable list of every top-level function and class in `shotfleet.py`, grouped by the sections described in [01](01-runtime-architecture.md#15-source-layout-sections-of-shotfleetpy), with line numbers at `main` `7e5176c` (0.1.7, 5,705 lines). The table below was **generated from the file** with Python's `ast` module on 2026-10-08 (line = the `def` or `class` line; the description is the first sentence of the docstring, or a short hand-written line where the function has none). Regenerate it instead of editing numbers by hand: line numbers drift with every commit, names do not.

Functions nested inside other functions (the closures in `ios_run_inner`, `android_run_inner`, `translate_flow`, `cmd_check`, `parse_js_translations`, `localize_flow`) are not listed; they are named in the chapter that explains their parent.

## Where to start reading

1. `main` (5065), `main_cmd` (5615), `main_dispatch` (5675): how a command is routed, where exit codes are made.
2. `cmd_run` (1856), `run_platform` (1900), `capture_platform` (1924), `ios_run_inner` (2010), then `android_run_inner` (2725).
3. `translate_flow` (949) and `localize_flow` (1158), with the tests in `tests/test_shotfleet.py` (class `TranslateFlow`).
4. `cmd_check` (3572) and `judge_screen` (3004).
5. `require_licence` (5560), `key_licence` (5504), `mac_licence` (5525).

## Main call chains

```text
main -> main_cmd -> main_dispatch
  run     -> apply_free_tier -> require_licence -> (key_licence | mac_licence) -> check_update_window
          -> cmd_run -> run_platform -> load_config -> run_hook(before_run)
                     -> capture_platform -> ios_run -> device_lock -> ios_run_inner
                                          -> android_run -> device_lock -> android_run_inner
                     -> run_hook(after_run)
  ios_run_inner     -> load_strings | config_strings -> shipped_locales -> translate_flow -> localize_flow
                    -> fit_parallel, capacity_warn -> make_pool -> healthy_installs
                    -> batch -> run_guarded(maestro) + capture_texts -> collect_shots -> junit_results
                    -> retry_choice -> (batch again) -> keep_earlier -> run.json -> cmd_check
  android_run_inner -> load_strings_apk | config_strings -> translate_flow -> fit_emulators -> android_pool
                    -> round_ -> android_flow -> run_guarded(maestro) -> flow_devices -> save_hierarchy_texts
                    -> retry_choice -> safe_round -> run.json -> cmd_check
  check   -> check_any -> check_build -> cmd_check -> find_screenshots -> usable_text | warm_up_ocr + read_text
          -> judge_screen -> store_rules -> coverage_matrix -> compare_folders -> write_gallery
  export  -> require_licence -> export_with_hooks -> cmd_export -> store_code
  activate -> cmd_activate -> gumroad_verify -> gumroad_fetch
  doctor  -> cmd_doctor -> (find_java, find_sdk, ios_runtimes, ocr --warmup) -> run_fix_plan -> fix_plan
  mcp     -> cmd_mcp -> mcp_call -> (cmd_doctor | check_any | apply_free_tier + cmd_run) -> mcp_summary
```

## Constants worth knowing

| Constant | Line | Meaning |
|---|---|---|
| `VERSION` | 28 | the version; read by `packaging/*.sh` and `tools/*.sh` with `sed` |
| `KEYS`, `REQUIRED`, `TABLES`, `HOOK_EVENTS`, `CAPTURE_KEYS` | 60-71 | the config schema |
| `APP_STORE`, `PLAY`, `PRIMARY`, `CANON`, `LANG_CANON` | 252-265 | store listing codes and locale spelling maps |
| `SELECTOR_KEYS`, `SYSTEM_BUTTONS` | 297, 939 | which flow keys carry text; dialog buttons that stay English |
| `SIM_TIMEOUT_S`, `SIM_BOOT_TIMEOUT_S`, `SIM_QUICK_TIMEOUT_S`, `SIM_LIST_TIMEOUT_S` | 1226-1231 | simctl timeouts |
| `STALL_S` | 1421 | default no-new-screenshot watchdog, 900 s |
| `CAPACITY_COST`, `CAPACITY_BASE_GB`, `CAPACITY_HEADROOM_GB`, `CAPACITY_SWAP_GB` | 1513-1516 | capacity planner figures (provisional) |
| `BUSY_SWAP_FRACTION`, `BUSY_LOAD_PER_CORE` | 1619-1620 | overload advisor thresholds (provisional) |
| `INFRA_ERRORS` | 1658 | error phrases that mean the device failed, so one retry can help |
| `DEMO_MODE`, `ANDROID_DEVICES`, `DEFAULT_IMAGE`, `SNAPSHOT` | 2431, 2526, 2353, 2478 | Android emulator setup |
| `HIER_MIN`, `HIER_LABEL` | 2615-2616 | Maestro version that saves per-step hierarchy; the marker label |
| `OCR_BUDGET_S`, `OCR_COMPILE_PATIENCE_S`, `OCR_STUCK_CPU_MIN`, `OCR_RETRY_S` | 3194, 3161, 3162, 3160 | text recognition waiting rules |
| `LATIN_UNLISTED`, `TWINS`, `CYRILLIC`, `TESSERACT`, `OSD_SCRIPT` | 2909, 2891, 2894, 3345, 3355 | language-judging tables |
| `APPLE_COLUMNS`, `PLAY_COLUMNS`, `APPLE_SIZES` | 3445-3446, 4805 | store classes for the coverage matrix and size rules |
| `MAESTRO_INTERFACE`, `MAESTRO_TESTED`, `MAESTRO_BAD`, `MAESTRO_PIN` | 3902, 3915, 3932, 3951 | what shotfleet needs from Maestro; the tested pair; the deny list (empty); the pinned download |
| `BAD_IOS_RUNTIMES` | 4764 | iOS runtimes `run` skips (27.0) |
| `COMMANDS` | 5041 | the nine commands |
| `MCP_TOOLS`, `MCP_VERSIONS`, `MCP_HEARTBEAT_S` | 5134, 5249, 5198 | MCP surface |
| `LICENCE_FILE`, `LICENCE_RECHECK_DAYS`, `LICENCE_OFFLINE_DAYS`, `GUMROAD_API`, `GUMROAD_PRODUCT_ID`, `MAX_MACS`, `FREE_LANGUAGES` | 5283-5290 | licence constants |

## How to regenerate the table

The listing below is mechanical. To refresh the line numbers after a change, run this from the repo root and paste the output over the table (functions without a docstring need a hand-written description, which is why a few rows differ from the docstring text):

```python
import ast, re
src = open("shotfleet.py").read()
for node in ast.parse(src).body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        doc = (ast.get_docstring(node) or "").replace("\n", " ")
        print(f"| {node.lineno} | `{node.name}` | {re.split(r'(?<=\.)\s', doc, maxsplit=1)[0][:115]} |")
```

Section boundaries (which section a line belongs to) are the line ranges in [01 section 1.5](01-runtime-architecture.md#15-source-layout-sections-of-shotfleetpy).

## Every function and class, by section

### Header, errors, path guards

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 30 | `Fail (class)` | A user-facing error: printed as one line, no traceback. |
| 37 | `bad_locale_text()` | Wording of the refusal for a bad language code |
| 40 | `check_locales()` | Refuse a locale that could not safely be a folder name: the command line, the MCP `locales` argument, the config. |
| 46 | `safe_strings()` | Drop the languages a translation file or a build names with something that isn't a language code, with a note. |
| 52 | `inside()` | root/parts, refused when it resolves outside root: the last guard before anything under the output folder is ... |

### Config validation and loading

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 73 | `check_tables()` | Refuse an unknown top-level table (a typo like [hook] would otherwise be ignored silently) and malformed ... |
| 99 | `check_capture()` | [capture] build/xctestrun/only_testing/screenshots/timeout: refuse typos, wrong types and missing settings before ... |
| 120 | `check_expect()` | [expect.<screenshot>] any/all/not = ["text", ...], with [expect.<screenshot>.<locale>] for one language: refuse ... |
| 137 | `read_doc()` | The parsed config file; a missing file or bad TOML is a Fail that says how to fix it. |
| 147 | `read_expect()` | The [expect.*] tables of a config, for `check --content` (no build, Maestro or licence needed). |
| 154 | `platforms_in()` | The platform sections ([ios], [android]) a config file has, in run order. |
| 161 | `check_section()` | Refuse an unknown key or a wrong type in [ios] / [android] (no files are read; load_config adds the checks that ... |
| 197 | `load_config()` | (platform, cfg, path resolver) for one section, with every mistake reported as a Fail that says how to fix it. |

### Locale tables and helpers

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 267 | `canon()` | Normalise a locale spelling (zh-CN to zh-Hans, iw to he) before any comparison |
| 272 | `store_code()` | The listing an app locale's screenshots belong to in `store` (APP_STORE or PLAY), or None if that store has no ... |
| 301 | `sh()` | subprocess.run with capture_output and text; the program's one shell-out helper |
| 304 | `aapt2()` | Newest aapt2 in the Android SDK; Fail with the fix if there is none. |

### Strings from the build (iOS bundle, Android resources, Compose)

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 314 | `plist_value()` | A top-level Info.plist value, or "" (PlistBuddy prints its errors on stdout). |
| 328 | `parse_strings_text()` | A .strings file (`"key" = "value";` with /* */ and // comments, \n \" \UXXXX escapes) as {key: value}. |
| 378 | `plist_to_json()` | A property list as plain data (dict/list/str), or None when unreadable. |
| 394 | `load_strings()` | {lproj: {key: value}} from every *.strings table in the app: its own *.lproj folders, plus those inside ... |
| 428 | `stringsdict_forms()` | {key#form: text} for every plural/device/width form in a .stringsdict, e.g. |
| 452 | `canon_lproj()` | Old lproj names (English.lproj) and underscores (en_GB.lproj) -> the code iOS uses for AppleLanguages. |
| 459 | `add_cvr()` | Compose Multiplatform resources: lines of 'string/key/base64(value)' in composeResources/<pkg>/values-<q>/*.cvr. |
| 475 | `android_locale()` | aapt2 config qualifier -> BCP-47 tag ('de', 'pt-rBR' -> 'pt-BR', 'b+zh+Hans' -> 'zh-Hans'); None if not a pure ... |

### Strings from source files, framework hints, shipped locales

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 486 | `locale_from_path()` | Language of a translation file from how ecosystems name them: app_de.arb, de.json, Resources.de.resx, ... |
| 507 | `icu_forms()` | {key: text} or, for ICU plural/select ('{n, plural, one{# item} other{# items}}'), one entry per form, with '#' ... |
| 526 | `icu_forms_all()` | (key, text) pairs of a flattened i18next-style table: key_one/key_other become key#one/key#other, ICU plurals one ... |
| 532 | `flatten()` | Nested JSON (i18next, Lokalise) -> {'a.b.c': text}. |
| 540 | `strip_js_comments()` | `src` without // and /* */ comments; string and template literals are left alone. |
| 558 | `parse_js_translations()` | ({key: text or nested dict}, skipped) for the object literal that holds a translation file's texts, read as data ... |
| 646 | `read_translation_file()` | {locale: {key: text}} from one source file, by format. |
| 758 | `config_strings()` | The config's `strings`: a folder of .lproj, or glob(s) of source files relative to the config. |
| 766 | `run_strings()` | What run.json keeps of the config's `strings`, as absolute paths: a later `shotfleet check <out>` reads the same ... |
| 773 | `load_strings_files()` | {locale: {key: text}} from translation source files matched by glob patterns (relative to cwd or absolute). |
| 787 | `unescape_android()` | Android resource escapes: \" \' \n \t \@ \? \uXXXX. |
| 794 | `load_strings_apk()` | {locale: {name: value}} from the string resources compiled into an APK (default config -> base). |
| 831 | `partly_translated()` | [(locale, percent)] for languages the app has some of its own strings in, but too few to count as shipped: ... |
| 844 | `note_partly_translated()` | Languages left out because too little is translated; and, for languages the developer asked for by name, a warning ... |
| 862 | `framework_hint()` | Print (to stderr, once, never blocking) what to add to shotfleet.toml when `build` is Flutter, React Native, MAUI ... |
| 885 | `shipped_locales()` | Locales the app itself is translated into. |

### Flow rewriting (translate_flow, localize_flow)

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 903 | `yaml_single_quote()` | Quote text for YAML with single quotes |
| 906 | `regex_literal()` | Escape Java-regex metacharacters (Maestro matches selectors as regexes) |
| 916 | `with_fallback()` | The strings the app shows in lp, the way iOS and Android resolve them: lp's own, then its parents' (zh-Hant-HK -> ... |
| 925 | `resolve_base()` | The table the flow's language lives in: `wanted` (default en), else its regional variant (en-GB only), else the ... |
| 944 | `override_pattern()` | The regex a user-set [overrides.<locale>] gives for this English text, or None. |
| 949 | `translate_flow()` | Rewrite English text selectors to the target language. |
| 1020 | `yaml_unquote()` | A YAML scalar's value: 'It''s' -> It's, "Say \"hi\"" -> Say "hi", plain stays. |
| 1029 | `split_comment()` | ('"Next"', ' # comment') -- a YAML comment starts at ' #' outside quotes. |
| 1038 | `redirect_screenshot()` | Rewrite one flow line if it names a screenshot, so files land in shots_dir. |
| 1052 | `print_untranslated()` | Print selectors not found in the app's strings |
| 1058 | `print_result()` | One line per language: ok/FAIL, screenshots, retried |
| 1063 | `count_screenshots()` | Count takeScreenshot steps in a flow (the expected number) |
| 1066 | `with_app_id()` | The flow with `appId:` set to this build's id, so one flow serves iOS and Android; a flow of bare steps gets a ... |
| 1074 | `inputs_for()` | Text to type for one language: the [inputs] defaults, then [inputs.<locale>] (exact, else the language part: pt ... |
| 1082 | `with_env()` | The flow header with `env:` values added (merged into an `env:` block the user already wrote), for `inputText: ... |
| 1092 | `flow_mapping_lines()` | The block-YAML lines for an inline `{ key: value, nested: { a: b }, list: [x, y] }` (launchApp options written on ... |
| 1153 | `apple_locale()` | The AppleLocale that goes with an app language: number and date formats follow the store locale (de -> de_DE, ... |
| 1158 | `localize_flow()` | Make a translated flow self-contained for one locale. |
| 1207 | `screenshot_ends()` | True when `out` just finished a takeScreenshot step (scalar or map form, any keys): the next step isn't deeper. |
| 1217 | `pause_after_screenshot()` | A pause while shotfleet reads the screen's text from the app (exact, any script; see capture_texts). |

### Simulators (iOS pool)

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 1233 | `simctl_sh()` | `xcrun simctl <args>` that cannot hang: a call that does not answer in time is a RuntimeError that says the Mac is ... |
| 1240 | `Sim (class)` | One iOS simulator: run() wraps xcrun simctl with per-command timeouts |
| 1253 | `healthy_installs()` | Install the app on the first k simulators of the pool that answer, shutting down any that don't (CoreSimulator ... |
| 1276 | `hung_marker()` | Path of the marker file for a simulator that stopped answering |
| 1279 | `mark_hung()` | Remember a pool simulator that stopped answering: the same ones hung again run after run (0.1.3 gates), so the ... |
| 1284 | `replace_hung()` | Delete a pool simulator that stopped answering last run, so make_pool creates a fresh one under its name. |
| 1297 | `run_setup()` | The user's per-device setup commands ([ios] simctl, [android] shell), once per booted device. |
| 1312 | `make_pool()` | Reuse or create n simulators named <prefix>-<i>, boot them, clean the status bar, run the config's [ios] simctl ... |

### Host safety: process control, text capture, watchdog, memory

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 1349 | `descendants()` | PIDs under root (inclusive), from one ps snapshot. |
| 1360 | `ios_screen_texts()` | Every label and value on screen, from the Maestro iOS driver's accessibility tree (exact Unicode). |
| 1375 | `capture_texts()` | While Maestro runs: when a screenshot appears in raw/<locale>/, read that screen's text from the driver of the ... |
| 1411 | `collect_shots()` | Move the screenshots (and screen texts) of the flow that took `<name>/<shot>` into dst, which is raw/<locale>. |
| 1423 | `run_guarded()` | subprocess.run, plus a watchdog that kills `simctl diagnose` started under this command. |
| 1470 | `newest_screenshot()` | The newest PNG's modification time under folder (any depth), 0 when there is none: what `run_guarded` watches. |
| 1475 | `memory_pressure()` | macOS's memory pressure level ("1" normal, "2" elevated, "4" critical), "" where it can't be read. |
| 1483 | `fit_parallel()` | Halve parallelism under memory pressure; refuse when critical. |
| 1494 | `mem_available_gb()` | Linux MemAvailable in GB, None where /proc/meminfo isn't there. |
| 1499 | `fit_emulators()` | On Linux, no more emulators than the machine can run: each wants about 2 cores and 3 GB. |

### Capacity planner

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 1518 | `Reading (class)` | What the Mac says before a run. |
| 1530 | `Plan (class)` | Result of plan_capacity: device count, level (ok, tight, short, critical), notes |
| 1535 | `capacity_need_gb()` | Memory a pool of n devices needs on top of what is in use: Maestro once, each device not yet booted, headroom. |
| 1539 | `plan_capacity()` | Pure: how many simulators/emulators to run at once, and why. |
| 1565 | `capacity_message()` | The warning for the buyer: what the Mac showed, what shotfleet suggests, what to close. |
| 1576 | `parse_vm_stat()` | Available GB from `vm_stat`: free + inactive + speculative pages; None when the text is not vm_stat's. |
| 1583 | `parse_swap_used_gb()` | GB in use from `sysctl -n vm.swapusage` ("total = 7168.00M  used = 6383.19M  free = ..."), None if unreadable. |
| 1588 | `parse_load1()` | First figure of `sysctl -n vm.loadavg` ("{ 828.41 423.28 236.45 }"), None if unreadable. |
| 1593 | `count_booted()` | (ours, other) booted simulators in `simctl list devices booted` output; ours are named <prefix>-<device>-<n>. |
| 1599 | `read_capacity()` | The impure part: ask the Mac. |

### Overload advisor, retries, failure explanations

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 1623 | `busy_reasons()` | Why this reading is dangerous for simulators ([] when it is not): swap almost full, macOS pressure critical, load ... |
| 1632 | `busy_message()` | The one-line warning, "" when the Mac is fine. |
| 1639 | `busy_warn()` | Print busy_message once per run (config `capacity = "off"` silences it). |
| 1647 | `capacity_warn()` | Warn-only (config `capacity`: "warn" default, "off" silent): print the planner's message when the Mac looks short ... |
| 1663 | `is_infra_error()` | True when a failed language's error looks like a device or infrastructure problem (INFRA_ERRORS), so one more try ... |
| 1668 | `retry_choice()` | (languages to retry, languages not retried) from {locale: result}: only failures with an infrastructure error are ... |
| 1674 | `say_not_retried()` | Tell the user which failed languages are not retried and why |
| 1679 | `retry_setup()` | `run --retry-failed`: (languages that failed in out/run.json, that report). |
| 1689 | `keep_earlier()` | After `run --retry-failed`: put the languages that passed last time back into the report as they were (in their ... |
| 1700 | `overload_note()` | Why failures on a loaded Mac are probably not the app's: slow simulators time Maestro's simctl calls out. |
| 1710 | `flow_parse_note()` | When Maestro could not read a flow, say so: the retry would fail the same way within seconds, and a memory hint ... |
| 1727 | `flow_steps()` | (lines, steps) of the maestro.log under `debug` that ran `flow`: steps = [(line index, description, status)] of ... |
| 1739 | `landscape_tap_hint()` | LANDSCAPE_HINT when the log shows Maestro's iOS landscape bug: the flow turned the screen to landscape, Maestro ... |
| 1759 | `failed_hierarchy()` | The screen hierarchy Maestro saved with the failed step of `flow` (commands json: metadata.error.hierarchyRoot), ... |
| 1770 | `screenshot_texts()` | Text lines macOS text recognition reads on one failure screenshot, for a flow with no saved hierarchy. |
| 1780 | `failure_details()` | Lines that say where a failed flow stopped: the failing step and its selector as Maestro's log names it, the ... |
| 1797 | `print_failure()` | Print failure_details indented under a FAIL line |

### run: orchestration, hooks, locks, ios_run_inner

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 1804 | `kill_stale_drivers()` | Kill Maestro iOS drivers attached to shotfleet's simulators. |
| 1814 | `junit_results()` | Parse Maestro's JUnit file into {flow name: ok, seconds, error} |
| 1823 | `device_type_id()` | 'iPad Pro 13-inch (M5)' or a full com.apple.CoreSimulator.SimDeviceType identifier -> the identifier. |
| 1836 | `default_device_type()` | iPhone 17 Pro Max, the 6.9" size class. |
| 1847 | `device_slug()` | com.apple...iPad-Pro-13-inch-M5-12GB -> ipad-pro-13-inch-m5-12gb (a folder and simulator-name prefix). |
| 1851 | `clear_single_run()` | A multi-device run writes out/<device>/; an old single-device run in out/ itself would hide it from device_runs. |
| 1856 | `cmd_run()` | Entry for `run`: loop over the config's platforms, return the worst exit code |
| 1869 | `config_commands()` | Every command a config makes `run` execute, by where it is written: [hooks] (shell), [capture] build (shell), ... |
| 1878 | `refuse_config_commands()` | The last guard: over MCP without hooks: true, no command from the config runs, even if mcp_call's check missed one. |
| 1883 | `run_hook()` | Run the user's commands for one event (strings run by /bin/sh in the config's folder, output to stderr). |
| 1900 | `run_platform()` | Load config, before_run hook, capture_platform, count problems, after_run hook |
| 1924 | `capture_platform()` | Choose the iOS or Android path; loop over device_types / devices; the [capture] build |
| 1950 | `ipad_set_missing()` | Across a multi-device run (parent/<device>/): an app that runs on iPad needs a 13" iPad set somewhere. |
| 1959 | `shutdown_sims()` | Shut down every simulator in OUR_SIMS |
| 1965 | `open_lock()` | A lock file in /tmp, where any user can make files: never opened through a symlink (O_NOFOLLOW), made 0o600, and ... |
| 1980 | `device_lock()` | One shotfleet run at a time per set of devices. |
| 2005 | `ios_run()` | device_lock around ios_run_inner, shutdown in finally |
| 2010 | `ios_run_inner()` | The whole iOS capture: strings, translate, boot, Maestro batch, retry, run.json, cmd_check |

### Bring your own capture (XCUITest)

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 2222 | `xcresult_pngs()` | Copy a result bundle's PNG attachments into dst as <XCTAttachment.name>.png; returns the file names written. |
| 2245 | `fastlane_cache()` | SnapshotHelper's folder for the length of a run: made if missing (SnapshotHelper never makes it, and a test passes ... |
| 2267 | `capture_build()` | The team's build-for-testing command, once per `run`, in the config's folder; its output goes to out/build.log. |
| 2281 | `find_xctestrun()` | The one .xctestrun the build made (shotfleet's own per-language copies don't count). |
| 2290 | `xctestrun_targets()` | The test targets of an .xctestrun: format 1 has them at the top level, format 2 in ... |
| 2295 | `xctestrun_app()` | The app under test: UITargetAppPath, else the first .app the tests depend on that isn't the test runner. |
| 2301 | `xctestrun_with_language()` | A copy of the .xctestrun whose UI tests launch the app in lproj (-AppleLanguages/-AppleLocale, as a Maestro run ... |
| 2311 | `set_sim_language()` | The simulator's own language, which every app launch gets however the test starts the app (no reboot needed). |
| 2316 | `newest_file()` | The newest file's modification time under folder, 0 when there is none. |
| 2324 | `capture_names()` | Every screen name any language of this run saved. |
| 2328 | `capture_result()` | A language's result: failed when xcodebuild failed, when it saved no screenshot, or when it lacks a screen another ... |
| 2336 | `fastlane_pngs()` | Move this simulator's SnapshotHelper screenshots (<simulator name>-<shot>.png, one folder for all simulators) into ... |

### Android: SDK, emulators, flows, android_run_inner

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 2348 | `host_abi()` | The emulator image architecture that runs at full speed here: arm64 on Apple silicon and ARM Linux, x86_64 ... |
| 2357 | `clean_path()` | An absolute path with ~ expanded and any `..` or `.` folded away. |
| 2362 | `find_sdk()` | The Android SDK, first match of: ANDROID_HOME, ANDROID_SDK_ROOT, ~/Library/Android/sdk, Homebrew's ... |
| 2380 | `cmdline_tool()` | sdkmanager or avdmanager: the SDK's cmdline-tools (latest, else any version), else on the PATH, else Homebrew's. |
| 2387 | `find_image()` | Package id of the best installed image of API 33+ for this machine's architecture (per-app languages need 33), or ... |
| 2397 | `sdkmanager_commands()` | The exact shell commands that install these SDK packages with the sdkmanager that exists (or Homebrew's, installed ... |
| 2415 | `commands_text()` | sdkmanager_commands() inside a sentence: a '# ...' line is an instruction (Linux: where Google's zip goes), and ... |
| 2421 | `adb_cmd()` | adb from the SDK we found, else whatever is on the PATH. |
| 2426 | `android_env()` | What Maestro needs to find the SDK we chose: ANDROID_HOME, and its adb on the PATH. |
| 2446 | `Emu (class)` | One Android emulator on a fixed port: adb() with timeout, booted() |
| 2464 | `stop_emulators()` | Stop every emulator shotfleet started. |
| 2480 | `start_emu()` | Headless emulator. |
| 2494 | `emulator_log_tail()` | The last lines of an emulator's own output, for a failure message ('' when there is none). |
| 2500 | `boot_failure_hint()` | The likely cause of an emulator that did not boot. |
| 2510 | `wait_booted()` | Wait until every emulator reports sys.boot_completed. |
| 2535 | `avd_home()` | Where shotfleet keeps its emulators: ANDROID_AVD_HOME, ANDROID_USER_HOME/avd, else ~/.android/avd. |
| 2542 | `require_api33()` | Per-app languages (`cmd locale set-app-locales`) exist from Android 13 (API 33). |
| 2551 | `android_pool()` | Boot n read-only copies of one AVD (created on first use as a 1080x1920 phone) into `pool`. |
| 2599 | `android_vars()` | (JS text, names) for the per-emulator typed values of one Android round, or ("", set()) when no [inputs.<locale>] ... |
| 2618 | `hierarchy_supported()` | True when this `maestro --version` string is >= HIER_MIN (None, unreadable, is not). |
| 2624 | `hierarchy_marker()` | The step that makes Maestro save the screen hierarchy: an optional assertTrue on `false` ends WARNED (the flow ... |
| 2630 | `android_flow()` | Per-run copy of a translated flow: own name, own screenshot folder, starts with a plain launchApp. |
| 2668 | `hierarchy_lines()` | The text of one Maestro screen-hierarchy tree, one string per line in screen order, without the status bar and ... |
| 2682 | `hierarchy_texts()` | {screenshot name: [text lines]} for the flow called `flow`, from Maestro's debug output: each marker step in ... |
| 2702 | `save_hierarchy_texts()` | Write <name>.texts.json (what iOS writes; `check` prefers it to OCR) next to each screenshot in dst that has a ... |
| 2711 | `flow_devices()` | {flow file stem: device serial} from Maestro's own log of how it sharded the run. |
| 2721 | `android_run()` | device_lock around android_run_inner |
| 2725 | `android_run_inner()` | The whole Android capture: strings, rounds of one language per emulator, retry, run.json, cmd_check |

### check: text recognition, language judging, screenshot discovery

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 2866 | `is_mac()` | sys.platform is darwin |
| 2869 | `vision_available()` | macOS text recognition (Vision) exists only on a Mac; elsewhere `check` reads screenshots with Tesseract. |
| 2873 | `install_hint()` | The brew or apt line that installs Tesseract |
| 2877 | `ocr_tool()` | Path of the OCR helper: bundled when frozen, else compiled from ocr.swift into .build/ocr |
| 2897 | `readable_languages()` | Base languages the text recognition in use reads. |
| 2911 | `can_read()` | True if the text reader's output is evidence for this base language (listed, or Latin script on a Mac). |
| 2916 | `vision_languages()` | Base languages macOS text recognition reads (ocr --langs), cached |
| 2925 | `norm()` | Text as OCR and string tables can both agree on: NFKC (NBSP, full-width), no bidi/zero-width marks, native digits ... |
| 2938 | `has_format()` | True for 'Day %d of 15'; false for plain text and for .stringsdict placeholders like '%1$#@jobs@' (their plural ... |
| 2943 | `format_regex()` | Regex source for what fmt looks like once filled in: numbers for %d, anything for %@ / {name}. |
| 2961 | `fill_format()` | fmt with its placeholders replaced by args ({'a1': '2', 'aname': 'Anna'}); None if an arg is missing. |
| 2973 | `norm_piece()` | norm() for a piece of a format string: same folding, but edge spaces kept ("Round " + "%d"). |
| 2979 | `Table (class)` | A locale's normalized strings, plus one regex for its format strings ("day %d of 15"). |
| 2983 | `string_tables()` | {locale: Table} for judge_screen. |
| 2998 | `read_nothing()` | True when a reader that may simply have failed found no text: Tesseract or --ocr-command (an Arabic Android screen ... |
| 3004 | `judge_screen()` | (locale the screen shows, problem or None) for one screenshot's OCR result. |
| 3063 | `system_dialog()` | The dialog's words alone are not enough: an app's own screen can say "Server isn't responding" or "Tracking has ... |
| 3070 | `system_banner()` | A system notification banner over the top of the screen. |
| 3076 | `caption_problem()` | Framed screenshots carry a marketing caption above the device. |
| 3092 | `play_folders()` | Which of Google Play's device folders a supply layout uses (phone, 7" and 10" tablets). |
| 3103 | `locale_tags()` | How a file name can spell its folder's locale: the folder name and its store codes (ru -> ru-RU on Play). |
| 3107 | `shot_key()` | The screen a file shows, the same in every language: its name without fastlane screengrab's millisecond timestamp ... |
| 3119 | `screen_keys()` | {"<label>/<name>": shot_key} for files given as "<label>/<name>", each judged with the rest of its folder. |
| 3125 | `find_screenshots()` | {folder label: [png, ...]} for the layouts people actually have: shotfleet's own output (raw/<locale>), fastlane ... |
| 3148 | `app_locale()` | The app language a store folder name stands for (de-DE -> de, no -> nb, zh-CN -> zh-Hans, iw-IL -> iw), or None. |
| 3165 | `ane_state()` | (is macOS's Neural Engine compiler service using the CPU right now, CPU minutes it has used in all). |
| 3176 | `ocr_not_answering()` | What happened when the text reader gave no answer, as far as ps shows it (no advice: OCR_WHAT_TO_DO follows it). |
| 3199 | `OcrBusy (class)` | macOS text recognition is still preparing (compiling) and the check's budget, or the read's patience, ran out. |
| 3202 | `ocr_left()` | Seconds left of the running check's text-recognition budget (no limit outside a check). |
| 3207 | `ocr_budget()` | The check-wide budget. |
| 3216 | `ocr_warmup_lock()` | One shotfleet per Mac warms up macOS text recognition at a time, so concurrent checks don't pile compiles onto ... |
| 3240 | `warm_up_ocr()` | One recognition on its own before the parallel ones, so macOS compiles its model once (minutes after a restart). |
| 3270 | `wait_for_ocr()` | p.communicate()'s (stdout, stderr), or None if p gives no answer in `timeout` s. |
| 3285 | `tesseract_env()` | Environment for Tesseract: OMP_THREAD_LIMIT defaults to 1 |
| 3289 | `tesseract_languages()` | Language data Tesseract has installed ({'eng', 'ell', ...}); empty if Tesseract isn't installed. |
| 3296 | `tesseract_code()` | Tesseract language name for an app locale |
| 3300 | `screen_text()` | The screen's text as the app reported it during the run (exact, any script), in OCR's result shape; or None. |
| 3309 | `usable_text()` | screen_text, but only when it proves something: fewer than 2 lines of any language's strings (mostly user content) ... |
| 3318 | `read_text()` | OCR one image. |
| 3357 | `tesseract_script()` | Tesseract's script detection, for listings whose script it reads badly when told the wrong one ({"osd_script": ... |
| 3367 | `external_ocr()` | Run the user's OCR command for a language macOS can't read; {image}, {lang} and {tesseract} are filled in. |
| 3391 | `ocr_can_read()` | True if macOS text recognition reads every letter of `text` (so not finding it on screen proves something). |
| 3399 | `content_rules()` | The any/all/not lists of one [expect.<screenshot>] table that apply to a screenshot of this language: its own ... |
| 3411 | `check_content()` | (problems, could-not-verify) for one screen's text against any/all/not lists, normalised like judge_screen does. |
| 3432 | `reports_json()` | The --json body: the one report as it is; with several, all lists merged plus `reports` (one entry each). |

### check: coverage matrix, release diff, cmd_check, gallery

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 3448 | `coverage_matrix()` | The per-language x device-class table for one store, or None when the store is unknown. |
| 3504 | `coverage_text()` | The matrix as plain aligned text, then the summary lines. |
| 3512 | `coverage_html()` | The coverage table as an HTML fragment for index.html |
| 3521 | `compare_folders()` | What changed per language and screen since `prev` (a shotfleet output folder or a fastlane folder): new, removed, ... |
| 3552 | `compare_lines()` | The diff as console lines (the first `limit`), plus how many were left out. |
| 3567 | `compare_html()` | The release diff as an HTML fragment |
| 3572 | `cmd_check()` | Check screenshots: each shows its own language's strings, none is a copy of another language, and no language is ... |
| 3818 | `write_gallery()` | out/index.html: one row per language, one column per screen; flagged screenshots outlined in red and marked "⚠ ... |

### doctor: Java, Maestro version and compatibility

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 3864 | `latest_release()` | Newest released version, or None (offline, or no releases yet). |
| 3872 | `java_major()` | Major version of a java executable, 0 if unreadable |
| 3878 | `find_java()` | (ok, JAVA_HOME to set or None) for Maestro, which needs Java 17+. |
| 3893 | `java_env()` | Environment additions that make Maestro find its Java ({} when the system's already works). |
| 3917 | `parse_maestro_version()` | The version in `maestro --version` output (a line like '2.0.10' or 'v2.0.10', maybe after JVM warnings), or None. |
| 3924 | `read_maestro_version()` | Installed Maestro's version, or None when it can't be read (garbage output, a timeout: it is a JVM app, slow on a ... |
| 3934 | `maestro_refusal()` | A message when `version` is on MAESTRO_BAD, else None. |
| 3939 | `maestro_warning()` | One line when this isn't a Maestro shotfleet was tested with; None when it is. |

### doctor --fix, cmd_doctor, init helpers

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 3957 | `tools_home()` | ~/.shotfleet or $SHOTFLEET_HOME |
| 3960 | `maestro_cmd()` | The Maestro to run: $SHOTFLEET_MAESTRO (a path), the one `doctor --fix` installed (a path), else "maestro" from ... |
| 3967 | `download()` | Fetch `url` to `dest` over HTTPS, printing progress, and refuse it unless it matches the checksum. |
| 3992 | `certifi_path()` | certifi's CA bundle path, None if not importable |
| 3998 | `tls_context()` | The CA bundle for downloads: the one the user's environment names (SSL_CERT_FILE and friends: corporate proxies ... |
| 4006 | `fetch_text()` | HTTPS GET a text with the TLS context |
| 4014 | `extract_zip_safely()` | Unzip into `target`, refusing members that would land outside it, and keep the unix permissions the zip stores ... |
| 4026 | `install_maestro()` | Maestro, the pinned version, into <tools home>/maestro. |
| 4039 | `adoptium_target()` | (os, arch) names Adoptium's API wants for this machine |
| 4046 | `install_jre()` | A Temurin 21 JRE into <tools home>/jre (found by find_java). |
| 4069 | `android_cmdline_archive()` | (url, sha1, size) of Google's 'cmdline-tools;latest' archive for this system, from the repository manifest. |
| 4082 | `fix_sdk_root()` | Where `doctor --fix` puts Android tools: the folder the user named in ANDROID_HOME / ANDROID_SDK_ROOT, else the ... |
| 4089 | `install_cmdline_tools()` | Google's Android command-line tools into <sdk>/cmdline-tools/latest (sdkmanager, avdmanager). |
| 4102 | `run_sdkmanager()` | Run sdkmanager (or the android shim) with given arguments |
| 4110 | `sdkmanager_invocation()` | The command line for sdkmanager arguments. |
| 4119 | `fix_plan()` | [(what it does, function)] for what is missing. |
| 4138 | `run_cmd()` | Run a command, Fail if it exits non-zero |
| 4141 | `run_fix_plan()` | Print the numbered plan, ask once (or take --yes), run the steps in order and stop at the first failure. |
| 4164 | `simctl_works()` | `xcrun simctl help` answers. |
| 4169 | `ios_runtimes()` | Names of the iOS Simulator runtimes Xcode has (['iOS 26.4']), [] when it has none, None when xcrun can't say. |
| 4177 | `xcode_hint()` | What to do when `xcrun simctl` does not answer on a Mac. |
| 4185 | `update_command()` | How this copy updates: Homebrew's cask lives under .../Caskroom/..., anything else came from install.sh or the ... |
| 4190 | `capture_mode()` | (uses [capture] for iOS, has an [android] section) for the config doctor looks at; (False, True) when there is ... |
| 4196 | `cmd_doctor()` | Check the tools shotfleet drives; print how to fix what's missing. |
| 4315 | `device_build()` | True for an iphoneos build (archives, device runs): it can't be installed on a simulator. |
| 4332 | `unpack_build()` | EAS (Expo), CI jobs and download pages hand over a simulator build as .tar.gz, .tgz or .zip: unpack it into `into` ... |
| 4362 | `build_hint()` | Why a path is not a simulator .app or .apk and what to pass |
| 4369 | `device_build_message()` | Wording for an iphoneos build |
| 4373 | `not_a_build()` | Why a file or folder that exists is not what [ios] app / [android] apk wants, and what to point at instead. |
| 4380 | `config_path()` | How the config should spell a path: relative when it's close (same project), else ~/... |
| 4388 | `outside_note()` | The one line init prints when the config has to name a build by its place on this Mac (outside the project folder). |
| 4394 | `age()` | '3 h ago' wording for a build's modification time |
| 4398 | `read_plist()` | Parse a plist, {} when unreadable |
| 4402 | `xcode_projects()` | Xcode workspaces and projects in cwd and up to two folders below (ios/App/App.xcodeproj; not Pods, node_modules, ... |
| 4408 | `scheme_for()` | Name of the shared scheme that launches an .app, read from the files on disk (never from xcodebuild, whose -list ... |
| 4417 | `derived_apps()` | Debug simulator builds in Xcode's DerivedData that belong to the project in cwd, newest first: [(mtime, .app, ... |
| 4439 | `simulator_app_time()` | When this simulator .app was last built, or None when it is not an installable app (a test runner, a device build). |
| 4447 | `gradle_apks()` | Gradle debug APKs in cwd's app/ (or any module folder one or two levels down, as in android/app of a React Native ... |
| 4455 | `is_watch_apk()` | True for a Wear OS APK |

### Project detection and init

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 4461 | `Project (class)` | What `shotfleet init` learns from a source folder: the framework, where its translation files are, where its ... |
| 4470 | `source_files()` | Files under cwd matching a glob such as '*.arb', not in hidden, build or dependency folders, at most `depth` ... |
| 4478 | `richest_folder_glob()` | '<folder>/*.ext' for the folder with the most translation files of that kind, or None. |
| 4487 | `first_glob()` | The first of these globs (relative to cwd) that matches files named like languages. |
| 4494 | `read_json_file()` | Parse a JSON file, {} when unreadable |
| 4498 | `flutter_arb_glob()` | l10n.yaml's arb-dir (flutter gen-l10n's setting), else the folder with the most .arb files. |
| 4515 | `kotlin_multiplatform()` | True when a Gradle build under cwd applies the Kotlin Multiplatform plugin: `kotlin("multiplatform")`, the ... |
| 4527 | `is_expo()` | An Expo app (its builds come from `expo run`), not a bare React Native app that merely depends on the `expo` ... |
| 4538 | `detect_project()` | The Project for the app whose source is in `cwd`, or None for a native Swift/Kotlin app and for anything ... |
| 4583 | `project_builds()` | (ios apps, apks) of this project's own build folders, newest first: [(mtime, path)]. |
| 4593 | `find_builds()` | The builds `shotfleet init` uses when none are given: the newest simulator .app for this folder's project and the ... |
| 4646 | `keep_note()` | What init says about a config that is already there: that it names the builds just given, or which it names ... |
| 4657 | `cmd_init()` | Write shotfleet.toml + flow.yaml for one or more builds: a simulator .app (iOS) and/or an .apk (Android). |
| 4721 | `ui_test_scheme()` | (shared scheme, UI test target) of a project's first scheme that tests a *UITests* bundle, read from the files on ... |
| 4731 | `cmd_init_capture()` | `init --capture`: a config whose [capture] runs the project's own XCUITest screenshot tests (no flow.yaml). |

### iOS runtimes, store rules, image checks, export

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 4766 | `runtime_version()` | A runtime's version as numbers: from simctl's "version" (26.4), else from its name ("iOS 26.4"); () when neither ... |
| 4771 | `bad_runtime_reason()` | Why this runtime is on the list of runtimes known to hang ("" when it is not). |
| 4776 | `pick_ios_runtime()` | (identifier, note) for the runtime `run` uses when the config names none: the newest one not on BAD_IOS_RUNTIMES; ... |
| 4789 | `latest_ios_runtime()` | Identifier of the iOS runtime run uses (skips BAD_IOS_RUNTIMES), printing a note when it skipped one |
| 4817 | `apple_class()` | The App Store display class of a pixel size, or None |
| 4823 | `png_alpha()` | None when a PNG has no alpha channel; "opaque" when it has one but every pixel's alpha is the maximum (XCUITest ... |
| 4852 | `image_info()` | ((width, height), alpha) for a PNG or JPEG, alpha as png_alpha says (None, "opaque" or "transparent"); JPEGs have ... |
| 4871 | `store_from_sizes()` | Which store a plain folder's screenshots are for, when neither the layout nor a build says: False (App Store) when ... |
| 4879 | `store_rules()` | (problems, notes) against the stores' published screenshot rules (research/store-specs.md). |
| 4939 | `blank_screenshot()` | True if a PNG shows nothing but one flat area between its status bar and its bottom edge: a frame the app has not ... |
| 4962 | `blank_note()` | The flow-failed text for a language whose screenshots include blank frames, or None. |
| 4969 | `png_size()` | (width, height) from a PNG header, or None if it isn't a PNG. |
| 4974 | `device_runs()` | Sub-folders of a multi-device run (out/<device>/run.json), or [] for a single run. |
| 4987 | `cmd_export()` | Copy verified screenshots into fastlane's upload folders (deliver for iOS, supply for Android). |

### Entry point: COMMANDS, skill, main

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 5043 | `cmd_skill()` | Copy the agent skills that ship with shotfleet into the folders AI coding agents load skills from: ... |
| 5065 | `main()` | argparse setup, the --json wrapper, plugin exec of shotfleet-<name> |

### MCP server

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 5178 | `mcp_summary()` | The default reply: counts, the first problem and note lines, and where the full check.json files are. |
| 5193 | `mcp_path()` | An MCP path argument as an absolute path: a string, never read as an option by the programs it is handed to. |
| 5200 | `mcp_call()` | One tool call -> (text, is_error). |
| 5251 | `cmd_mcp()` | Model Context Protocol server on stdin/stdout (JSON-RPC, one message per line). |

### Licence

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 5294 | `NoLicence (class)` | No valid licence: `export` stops; `run` falls back to the free tier. |
| 5297 | `cap_locales()` | Free-tier cut: first FREE_LANGUAGES languages, prints the free tier line |
| 5311 | `gumroad_api()` | SHOTFLEET_GUMROAD_API points the check at a test server. |
| 5317 | `baked_release_date()` | The day this build was made: packaging/build.sh writes it into a module (`_release`) that PyInstaller freezes into ... |
| 5330 | `sale_time()` | Gumroad's purchase.sale_timestamp ("2026-10-05T12:34:56Z") as unix time, or None when it is missing or unreadable. |
| 5335 | `is_time()` | True for a believable unix time (finite, 0 to 1e11) |
| 5338 | `updates_until()` | The last release day this purchase covers (the same date a year later; 29 February counts to 1 March), or None ... |
| 5347 | `check_update_window()` | A licence covers every version released within a year of the purchase. |
| 5363 | `ci_record_file()` | Path of ci-checked.json |
| 5366 | `write_json_atomic()` | Write a state file so a reader never sees half of it: a temp file in the same folder (private, 0600), then ... |
| 5378 | `key_hash()` | SHA-256 of a key (what ci-checked.json stores) |
| 5381 | `ci_seen()` | The last good online check of this key on this machine, {"checked", "sale"}, or None. |
| 5392 | `is_gumroad_key()` | Gumroad keys are four groups of 8 (ABCDEF12-34567890-...). |
| 5396 | `gumroad_fetch()` | -> (status, body bytes). |
| 5414 | `gumroad_verify()` | Gumroad's licence check -> (ok, uses, reason, sale): sale is the purchase time (unix) or None. |
| 5443 | `save_licence()` | Write licence.json; a folder that can't be written is a plain sentence, and this runs before anything is counted. |
| 5450 | `cmd_activate()` | Verify, window check, save-first-count-second, write licence.json |
| 5483 | `read_licence()` | The stored licence as a dict, or None when the file is missing or unreadable (a half-written file must never crash ... |
| 5491 | `cmd_deactivate()` | Delete licence.json (cannot give the activation back) |
| 5504 | `key_licence()` | SHOTFLEET_KEY (CI): checked online on every run, no activation used. |
| 5525 | `mac_licence()` | The licence activated on this Mac (licence.json): checked online at most weekly, works offline for 30 days after ... |
| 5560 | `require_licence()` | `run` and `export` need a licence in released builds; `check`, `doctor` and `init` are free. |
| 5573 | `upload_command()` | The fastlane command that uploads what `export` wrote, screenshots only (flags checked against docs.fastlane.tools ... |
| 5583 | `export_with_hooks()` | `export`, with the config's before_export / after_export hooks (found through run.json) around it. |
| 5602 | `apply_free_tier()` | `run` without a valid licence still runs, for two languages (the free tier shows the product). |

### Dispatch

| Line | Name | What it does (first sentence of its docstring) |
|---|---|---|
| 5612 | `on_sigterm()` | SIGTERM/SIGHUP become KeyboardInterrupt |
| 5615 | `main_cmd()` | Signal handlers, main_dispatch, shutdown_sims in finally |
| 5623 | `check_build()` | What `check` compares with when no --app or --strings is given: what `init` would use in cwd (find_builds, which ... |
| 5652 | `check_any()` | `check` on whatever folder it is: a run, a multi-device run, or Play listings (phone and tablet sets each on their ... |
| 5675 | `main_dispatch()` | Route a parsed command; licence gates; the one except that makes exit 2 and 130 |
