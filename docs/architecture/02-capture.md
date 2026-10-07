# 2. The capture pipeline

Back to the [index](../ARCHITECTURE.md). Anchors are `shotfleet.py:LINE` at `origin/main` `285e099`.

Capture is everything from "the config names a build" to "PNG files in `out/raw/<locale>/`". `run` then calls `check`
([03-check.md](03-check.md)).

## 2.1 Where the translations come from

shotfleet never asks the developer for a translation table. It reads the translations the app already ships, so the rewritten selectors always
match the binary under test. The result everywhere is a dict `{locale: {key: text}}` (`strings`).

### iOS builds (`load_strings`, `:394`)

- Walks every `*.lproj` under the `.app` (its own, plus those inside frameworks, Swift package bundles and an embedded Watch app). `Base.lproj` is
  skipped: it is layout storage, not a language.
- `*.strings` are read by `plist_to_json` (`:378`): `plutil -convert json` when `plutil` exists (it also reads binary and old-style plists), otherwise
  `plistlib` plus a hand-written `.strings` parser (`parse_strings_text`, `:328`) so Linux works without Apple tools.
- `*.stringsdict` plural, device and width rules become `key#form` entries (`stringsdict_forms`, `:428`), so "1 item" and "2 items" are both known.
- Keys from a nested bundle are prefixed `<bundle path>/<table>:<key>` so two frameworks cannot collide.
- Compose Multiplatform resources (`*.cvr`: `string|key|base64(value)` lines) are added as `cmp:<key>` entries (`add_cvr`, `:459`).
- String Catalogs (`.xcstrings`) are compiled by Xcode into `.strings`/`.stringsdict` inside the `.app`, so `load_strings` needs nothing special. Catalog entries
  keyed by their English text have no English table at all; the loop at `:416-425` fills the development language from the keys, skipping plural
  forms English does not have.
- `CFBundleDevelopmentRegion` decides which table is "the base language" if there is no `en`.

### Android builds (`load_strings_apk`, `:794`)

`aapt2 dump resources app.apk` is parsed line by line: `string`, `plurals` (`name#one`, `name#other`) and `array` (`name[0]`) resources, with
multi-line values and Android escapes (`unescape_android`). A config qualifier becomes a locale through `android_locale` (`:475`): `pt-rBR` to
`pt-BR`, `b+zh+Hans` to `zh-Hans`; `night`, `land`, `v31` and pseudolocales are dropped. Compose Multiplatform keeps strings in APK assets (`.cvr`
files read from the zip). `aapt2` is found under the SDK's `build-tools` (`aapt2()`, `:304`).

Libraries (AndroidX, Material, Play Services) bring their own strings in about 80 locales, so raw coverage is meaningless for a small app.
`shipped_locales` (`:885`) first separates the app's own keys (a key found in fewer than 90 percent of the maximum number of locales any key
reaches; when no key reaches 20 locales, or when that rule would leave under 10 percent of the keys, every key counts as the app's) and then keeps
locales that cover at least half of those. `partly_translated`
(`:831`) names the ones left out for being 10 to 49 percent translated, and warns when the user asks for such a language by name.

### Source translation files (`strings = "glob"`)

Frameworks that compile translations into code cannot be read from the build. `read_translation_file` (`:646`) dispatches on extension:

| Extension | Used by | Notes |
|---|---|---|
| `.arb` | Flutter | `@@locale`, metadata keys skipped, ICU plurals split into forms |
| `.json` | i18next, react-intl, Lokalise | nested keys flattened to `a.b.c`; `key_one`/`key_other` plurals become `key#one`/`key#other` |
| `.ts` `.js` `.mjs` `.cjs` | Ignite, i18n-js, vue-i18n | `parse_js_translations` (`:558`) reads the object literal as data and **never runs it**; anything that is code (calls, variables, spreads) is skipped and counted in a stderr note |
| `.xcstrings` | String Catalog source | every language in one file |
| `.strings` `.stringsdict` | iOS sources | |
| `.xml` | Android `strings.xml`, Compose | |
| `.xlf` `.xliff` | XLIFF 1.2 and 2.0 exports | source and target languages in one file |
| `.resx` | .NET MAUI | |
| `.po` | gettext | plural forms all kept; msgid is the source text |
| `.properties` | Java ResourceBundle | |
| `.csv` | Unity Localization, spreadsheets | one column per language |

The language of a file comes from `@@locale`, the file name (`app_de.arb`, `Resources.de.resx`) or a folder (`locales/de/`, `values-de/`):
`locale_from_path` (`:486`) holds those rules. `load_strings_files` (`:773`) merges files; a key that two files define differently keeps both, the
later one namespaced `<file stem>:<key>`.

`FRAMEWORKS` (`:853`) lists file-name markers for Flutter, React Native, Unity and MAUI. `framework_hint` (`:862`) prints a one-time `hint:` on
stderr with the exact `strings = ...` line, and warns about builds that will spoil screenshots (Flutter debug banner, a React Native Debug build that
loads from Metro). `init` goes further: `detect_project` (`:4272`) reads `pubspec.yaml`, `package.json`, `*.csproj`, Gradle settings and
`l10n.yaml`, finds the translation glob and the build, and writes both into the config.

Why read source files instead of the built app for those frameworks: the translations are inside Dart or JavaScript bundles, which shotfleet cannot
parse reliably (`research/frameworks.md`). What the user lists is read as data, never executed.

## 2.2 Rewriting a flow for one language

A flow is YAML that shotfleet treats as **text**, line by line, not as a parsed document. That is deliberate: Maestro's YAML has many forms
(scalar, inline map, block map) and a round trip through a YAML library would change formatting and comments. The cost is that
`translate_flow` and `localize_flow` carry a set of regex rules; the tests (`TranslateFlow`, `LocalizeFlow`, `AndroidFlow` in `tests/test_shotfleet.py`)
are the specification.

### `translate_flow(flow, base, target, overrides)` (`:949`)

Input: the English flow, the base-language table (`en`), the target-language table (or a list of them), optional `[overrides.<locale>]`.
Output: `(flow, untranslated_selectors, collisions)`.

- It rewrites only values of **selector keys**: `SELECTOR_KEYS` (`:297`): `tapOn`, `doubleTapOn`, `longPressOn`, `assertVisible`, `assertNotVisible`,
  `scrollUntilVisible`, `text`, `copyTextFrom`, `visible`, `notVisible` and the relative anchors `below`, `above`, `leftOf`, `rightOf`, `childOf`,
  `containsChild`. `id:` selectors and `inputText` values are untouched (typed text is not translated; use `[inputs]`).
- For an English text it finds every key whose base value equals it (`by_text`), collects each key's value in the target language, and emits a Java
  regex that matches any of them: `(Nächste|Weiter)`. Maestro matches text selectors as full regexes, so metacharacters are escaped
  (`regex_literal`).
- **Format strings.** `Round 2 of 12` is matched against base values with placeholders (`%d`, `%1$@`, `{name}`, `{{name}}`, ICU), through `format_regex`
  (`:2829`), and filled into every target plural form with the same numbers (`fill_format`). No per-language plural rules are needed because every
  form is an allowed alternative.
- **Wildcards.** `".*Register"` or `"Self-hosted.*"` (Flutter merges a row's title and detail into one label) are translated for the part they name
  and the wildcard is kept.
- **System dialogs.** `SYSTEM_BUTTONS` (`:939`) lists permission-prompt buttons ("Allow While Using App", "Don't Allow", ...). Those dialogs are drawn
  by iOS or Android in the **device** language, which stays English while the app runs in German. So a tap on such a text keeps its English
  spelling as one of the alternatives.
- **Collisions.** If the target word for key A also means another short label on the same screen (`tr`: Next and Advanced are both `İleri`), it
  records a warning, because a tap could hit the wrong element. `run` prints it before any device boots; the user anchors the step with `below:` or
  adds an override.
- **Overrides.** `override_pattern` (`:944`) makes `[overrides.<locale>]` win over the app's strings; a `re:` prefix passes a regular expression.
- Selectors it cannot find anywhere are returned as `untranslated_selectors`, left as written, and printed ("selectors not found in the app's
  strings"). They may still work in English.

`with_fallback(strings, lp)` (`:916`) builds the table the app actually shows for `lp` the way the OS does: `zh-Hant-HK`, then `zh-Hant`, then `zh`.

### `localize_flow` (iOS, `:1158`)

Why it exists: Maestro can only run several simulators from one process with `--shard-split`, and that hands **any flow to any device**. So the
language cannot live on the simulator; it must travel with the flow. `localize_flow` makes each translated flow self-contained:

- `name: <locale>` in the header so Maestro's JUnit report and logs name the language.
- A `launchApp` with `clearState: true` and `arguments: AppleLanguages: "(de)"`, `AppleLocale: "de_DE"` is prepended (`apple_locale`, `:1153`). The
  user's own first `launchApp` options (permissions, `appId`) are merged in; later `launchApp` steps get the same language arguments without
  `clearState`. One-line `launchApp: { ... }` options are expanded (`flow_mapping_lines`, `:1092`).
- Every `takeScreenshot` is redirected to a per-locale path (`redirect_screenshot`, `:1038`) so files land in a folder named after the language.
- After every `takeScreenshot` a pause is inserted (`pause_after_screenshot`, `:1217`): an optional `extendedWaitUntil` on the text
  `__shotfleet_reading_screen__` with a 1,500 ms timeout. It always times out; its purpose is to hold the flow still while the background thread reads
  the screen's text from the app.
- `[inputs]` values go in as a Maestro `env:` block (`with_env`).
- `with_app_id` (`:1066`) sets `appId:` to the build's own id, so one flow serves iOS and Android.

### `android_flow` (`:2527`)

Per round and per emulator it writes `<tag>_f<j>.yaml`: own name, own screenshot folder, starts with a plain `launchApp`. **No `clearState`**: on Android
that would wipe the per-app language shotfleet just set, so shotfleet clears app data itself (`pm clear`) before each round. Because Maestro assigns
flows to emulators in an order shotfleet does not control, per-emulator typed values (`[inputs.<locale>]`) go through `shotfleet_vars.js`
(`android_vars`, `:2496`), a `runScript` that picks its row by `MAESTRO_DEVICE_UDID` (Maestro 2.11.0 sets it, 2.0.10 does not; then the `[inputs]`
defaults are typed). With Maestro 2.7.0 or newer a marker step (`assertTrue: ${false}`, `optional: true`, labelled `shotfleet:hier:<shot>`) follows every
`takeScreenshot`: an optional failing step ends WARNED, the flow carries on, and Maestro 2.7+ saves the screen hierarchy with a warned step. That
is how Android gets exact app text without pixels. `hierarchy_supported` (`:2515`) gates it on `HIER_MIN = (2, 7, 0)`. The reasoning, including why
`maestro hierarchy` is not used (it tears down the port forwards of a sharded run), is in `research/limits-text.md` section 1.

## 2.3 iOS devices

**Pool.** `make_pool(n, device_type, runtime, prefix, simctl)` (`:1304`) reuses or creates `n` simulators named `shotfleet-<device-slug>-<i>` (for
example `shotfleet-iphone-17-pro-max-1`). Rules that matter:

- A pool simulator with the right name but another device type (config changed) is **deleted and recreated**, or screenshots would come out the wrong size.
- Only simulators matching `<prefix>-<digits>` are ever deleted. Others on the machine are never touched (`OUR_SIMS`, `:1717`).
- A simulator that stopped answering in a previous run has a marker file `~/.shotfleet/hung-simulators/<UDID>`; the next `make_pool` deletes it and
  creates a fresh one (`replace_hung`, `:1276`). In the 0.1.3 release tests the same two simulators hung three runs in a row.
- After boot: `status_bar override` (9:41, full battery, wifi), and a `defaults write` that tells the simulator the "Ready for Apple Intelligence" banner
  was already shown. The second is an inference from the key's name (comment at `:1331-1335`) and suppresses only that banner.
- Then the user's `[ios] simctl` commands (`run_setup`, `:1289`), once per simulator, `$UDID` substituted. A failing command stops the run (exit 2).

**Device type default.** `default_device_type` (`:1750`) is the iPhone 17 Pro Max (1320x2868, the App Store 6.9" class); with an older Xcode that lacks
it, the newest `iPhone N Pro Max` is used. A configured `device_type` is never changed. `device_type_id` accepts a display name or a full identifier.
`runtime` defaults to the **last** installed iOS runtime (`latest_ios_runtime`, `:4496`). Installing a newer runtime therefore silently changes what
`run` uses: pin `runtime` in the config for a tested setup.

**Multi-device sets.** `device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]` runs the whole pipeline once per type into `out/<slug>/`
(`capture_platform`, `:1831`), then `ipad_set_missing` (`:1857`) refuses an iPad-capable app that has no 13" iPad set.

**Install.** `install()` uninstalls then installs the app on every simulator at once (`healthy_installs`, `:1245`), because one wedged simulator
used to cost its full timeout in turn (five wedged simulators cost 1,500 s in the 0.1.2 gate). It does **not** `simctl terminate`: uninstalling stops
a running app and the terminate call was the one that hung. The uninstall is the first call per simulator and has a 60 s limit (`SIM_QUICK_TIMEOUT_S`),
so it doubles as a "does this simulator answer" probe. Dead simulators are shut down, marked hung and dropped; the run continues with the rest and fails
only when none answers, with the exact `xcrun simctl shutdown <UDID>` commands for shotfleet's own simulators.

**Run.** One Maestro process: `maestro --device <udid,udid,...> test <flows dir> --shard-split <k> --format JUNIT --output junit<N>.xml --debug-output <dir>`
under `run_guarded`, with `MAESTRO_DRIVER_STARTUP_TIMEOUT=240000` (several XCTest drivers starting at once are slow) and
`MAESTRO_CLI_NO_ANALYTICS=1`. Results are read from the JUnit XML (`junit_results`); if Maestro crashed before writing it, the screenshots on disk
are the ground truth. A language is only `ok` if Maestro said so **and** it produced exactly as many screenshots as the flow has `takeScreenshot`
steps **and** none is blank (`blank_note`).

**Text from the app.** While Maestro runs, `capture_texts` (`:1367`) polls the debug folder for new PNGs and Maestro's own `maestro.log` for lines
like `Selected device <udid> using port 7001 with execution plan ExecutionPlan(flowsToRun=[...])` (the same log line `tools/maestro-compat.py` insists
a new Maestro still has). That tells it which port's XCUITest driver is running which language's flow, so `ios_screen_texts` (`:1352`) can POST to
`http://127.0.0.1:<port>/viewHierarchy` and save every label, title, value and placeholder as `<shot>.texts.json`. The 1,500 ms pause
after each screenshot is for this. Per-port reads run in a thread pool so one slow driver does not hold the others.

**Cleanup.** `kill_stale_drivers` (`:1719`) kills leftover `xcodebuild test-without-building` Maestro drivers attached to shotfleet's simulators (a stale
driver keeps port 7001 bound to its own device, so the next run silently drives the wrong one). `ios_run` shuts every pool simulator down in a
`finally` (`shutdown_sims`, `:1866`, which also clears the status-bar override); `main_cmd` does it again.

## 2.4 Android devices

**SDK discovery** (`find_sdk`, `:2259`): `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `~/Library/Android/sdk`, `~/Android/Sdk`, Debian's `/usr/lib/android-sdk`,
Homebrew's `android-commandlinetools`, or the folder above an `adb` on the PATH, taking the first with at least one SDK part inside. `find_image`
(`:2284`) picks the newest installed `google_apis*` image of API 33+ for this machine's architecture (`host_abi`: arm64-v8a on Apple silicon, x86_64
elsewhere). `doctor` prints the exact `sdkmanager` commands when something is missing and `doctor --fix` runs them.

**Why API 33.** Per-app languages (`cmd locale set-app-locales`) exist from Android 13. An older emulator would boot for minutes and then fail at
the first language, so `require_api33` (`:2439`) refuses up front (the app's own minSdk can stay low).

**Emulators** (`android_pool`, `:2448`):

- AVDs named `shotfleet_android` (phone: 1080x1920 at 420 dpi), `shotfleet_android_tablet` (1440x2560) and `shotfleet_android_tablet7` (1080x1920 at 280
  dpi), created on first use with `avdmanager`, then `config.ini` is patched for the size (`ANDROID_DEVICES`, `:2423`). The sizes are exactly 9:16
  at 1080 px or more so Google Play can recommend the listing (`research/store-specs.md`). The AVD folder is passed explicitly
  (`avd_home()`), because on a Linux box with `XDG_CONFIG_HOME` set (GitHub's runners) tools would otherwise use `~/.config/.android`.
- One time per AVD, a writable emulator boots on port 5700, waits 20 s and saves a snapshot named `shotfleet`. Every later run starts `n` **read-only**
  copies from that snapshot on ports 5702, 5704, ... (boot in 4 to 5 s instead of about 22 s cold, measured) so runs never modify the AVD. If any
  `emulator-57xx` is already running the run refuses.
- `wait_booted` (`:2407`) needs `sys.boot_completed == 1` **and** `service check package` to answer (on a busy machine the first can be true while
  `adb install` still fails with "Can't find service: package"); an emulator that exits early fails the run at once with its own last log lines and a
  likely cause (`boot_failure_hint`: no KVM, full disk, memory).
- `DEMO_MODE` (`:2328`) is applied to every emulator after boot and again before each round: ANR and crash dialogs hidden, animations off, heads-up
  notifications off, and SystemUI demo mode (clock 9:41, full battery, wifi, no notifications).
- The APK is installed with `adb install -r -g` (all permissions granted).

**Rounds** (`android_run_inner`, `:2622`; `round_`): with `n` emulators and `L` languages there are `ceil(L/n)` rounds. In a round each emulator gets
one language: `pm clear <pkg>` (fresh onboarding, and it resets the app language, so set it after), then
`cmd locale set-app-locales <pkg> --locales <lp>`. All of that round's flows go to one Maestro process with `--shard-split`. Maestro assigns flows to
emulators in an order shotfleet does not control, so `flow_devices` (`:2608`) reads the same `Selected device ... flowsToRun=[...]` log line to learn
which flow ran where, and each emulator's language is known from the setup step. The code comment gives the one-process-with-`--shard-split` reason
for iOS (see `localize_flow`); Android uses the same mechanism, and the round structure exists because shotfleet cannot choose which flow lands on which emulator.

`safe_round` wraps each round: if an emulator stops answering `adb`, capturing ends, what earlier rounds took is kept, checked and written to
`run.json`, and the remaining languages are reported as failed (rerun them with `--locales`). Emulators are stopped in a `finally`
(`stop_emulators`, `:2361`): ask politely with `adb emu kill`, wait 20 s, then kill the process tree (the `Popen` handle is shotfleet's own).

## 2.5 Parallelism and capacity

`want = min(--parallel or config parallel or 4, number of languages)`. Then:

- `fit_parallel` (`:1475`) reads `kern.memorystatus_vm_pressure_level`: level 4 (critical) refuses the run; level 2 (elevated) halves the count.
- `fit_emulators` (`:1491`) on Linux caps at `cores // 2` and `free GB // 3` (each emulator wants about 2 cores and 3 GB; measured on a 2-core,
  7 GB runner where two emulators put "Process system isn't responding" over every screenshot; `docs/linux.md`).
- `capacity_warn` (`:1607`) is the **warn-only** capacity planner (config `capacity = "warn"`, the default): `plan_capacity` (`:1530`, pure) takes
  the fewest of cores, free memory, half under elevated pressure and one while swapping, and `run` prints a message naming what the Mac showed.
  It never changes the pool and never refuses. The constants (`CAPACITY_COST`, `CAPACITY_SWAP_GB = 10`) are provisional and the file says which
  figure came from which run (`research/workarounds-maestro-resources-2026-10-05.md`). `capacity = "adjust"` is refused as not available.
- `overload_note` explains failures that look like a loaded Mac, but only when a failed flow's error is `Unknown error` or `Unable to clear state`,
  never for an ordinary assertion failure; `flow_parse_note` says so instead when Maestro reported "Parsing Failed".

Why it matters: four simulators on a loaded Mac took many times longer than on a quiet one, and retries added load. Two gate runs were lost to
memory (`docs/handoff.md` section 17). The release gate now starts only at memory pressure level 1.

## 2.6 Setting the language

| Platform | How | Why this way |
|---|---|---|
| iOS Maestro run | launch arguments `-AppleLanguages (de)` and `-AppleLocale de_DE` in each flow's `launchApp` | one Maestro process serves all simulators, so the language must travel with the flow |
| iOS `[capture]` | `defaults write -g AppleLanguages` / `AppleLocale` **on the simulator** (`set_sim_language`, `:2208`), plus the same two arguments injected into the `.xctestrun` | `xcodebuild -testLanguage` is ignored with `-xctestrun` (measured in `research/byoc-ios-experiment-2026-10-06.md`), so shotfleet sets the language itself |
| Android | `cmd locale set-app-locales <pkg> --locales <lp>` after `pm clear` | per-app language, Android 13+; the system language stays English, so the OS's own dialogs stay English |

`apple_locale` (`:1153`) derives `AppleLocale` from the store code so number and date formats follow the store locale (`de` to `de_DE`,
`zh-Hans` to `zh_CN`).

## 2.7 Bring your own capture (BYOC, iOS)

Config: a `[capture]` table in place of `flow` (validated by `check_capture`, `:99`). Requires `[ios]`; Android still needs a Maestro flow.

1. **Build once.** `capture_build` (`:2164`) runs the team's `build` string with `/bin/sh -c` in the config's folder under `run_guarded` (over MCP only with `hooks: true`: `refuse_config_commands` is its first line) (limit
   `CAPTURE_BUILD_TIMEOUT_S = 3600`), output to `out/build.log`. `run --no-build` skips it.
2. **Find the test run file.** `find_xctestrun` (`:2178`) globs `xctestrun`; exactly one match is required (shotfleet's own per-language copies,
   named `*.shotfleet-<lp>.xctestrun`, are ignored). The app under test is read from the file (`xctestrun_app`) unless `[ios] app` is set.
3. **One language per simulator, as soon as free.** `capture_batch` starts one worker thread per simulator; each takes the next language from a
   shared list. `capture_step` (`ios_run_inner`, nested) sets the simulator language, uninstalls the app, clears stale SnapshotHelper files, writes
   `xctestrun_with_language` (`:2198`: a copy **beside the original**, because the paths inside are relative to its folder and a moved copy fails with
   exit 70) and runs `xcodebuild test-without-building -xctestrun ... -destination id=<udid> -resultBundlePath ... -only-testing:...` under
   `run_guarded`.
4. **Collect screenshots** from two sources, depending on `screenshots = "attachments" | "fastlane" | "auto"`:
   - `xcresult_pngs` (`:2119`): `xcresulttool export attachments`, file names recovered from `manifest.json`
     (`<name>_<n>_<UUID>.png` becomes `<name>.png`); duplicate names are both kept with a warning. An `XCTAttachment` needs `lifetime = .keepAlways` or
     Xcode discards it when the test passes.
   - `fastlane_pngs` (`:2233`): fastlane's `SnapshotHelper` writes `<simulator name>-<shot>.png` into `~/Library/Caches/tools.fastlane/screenshots`,
     **one folder shared by every simulator**, and only if that folder exists. `fastlane_cache` (`:2142`) is a context manager that creates it,
     moves aside `language.txt`, `locale.txt` and `snapshot-launch_arguments.txt` (they would force one language on every simulator) and puts them
     back afterwards, also after Ctrl-C or a crash; a leftover `.shotfleet-aside` folder from a SIGKILLed run is restored first.
5. **Judge.** `capture_result` (`:2225`): failed when xcodebuild failed, when the test passed but saved nothing (`NO_SHOTS_HINT`: "which proves
   nothing"), or when the language lacks a screen another language saved. Then blank-frame check. After the retry, results are recomputed against every
   screen any language saved.

Progress for the stall watchdog is "a file changed in the result bundle or a new SnapshotHelper file appeared" (`newest_file`, `newest_screenshot`).
Same pool, same retry, same `check` and `export` as a Maestro run; paid like `run`. Status: **the device test (`tools/fixture-byoc-e2e.sh`) has not
passed on a device for the finished feature**, which is why `site/BYOC_DEVICE_PROVEN` does not exist and public lines carry the caveat
("not run end to end on a device yet", enforced by `tests/test_site.py` `ByocPending`). Experiments E4 and E5 (research note above) showed it works by
hand on the fixture app and on a real project.

## 2.8 Retries, timeouts, watchdogs

| What | Value | Where |
|---|---|---|
| One retry of failed languages | after the first pass, on the devices that still answer | `ios_run_inner` (`:2076`), Android `safe_round` / retry loop |
| `simctl` default call | 300 s; `bootstatus` 900 s; `uninstall` and `terminate` 60 s | `SIM_TIMEOUT_S`, `SIM_BOOT_TIMEOUT_S`, `SIM_QUICK_TIMEOUT_S` (`:1226-1230`) |
| `adb` call | 180 s default | `Emu.adb` (`:2345`) |
| Emulator boot | 600 s | `wait_booted` |
| Maestro batch (iOS) | `timeout_s` (600) times `ceil(languages / devices)` plus 300 s | `ios_run_inner` (`:2000`) |
| Maestro round (Android) | `timeout_s` plus 300 s | `android_run_inner` (`:2686`) |
| Stall watchdog | no new PNG for `stall_s` (default 900) kills Maestro and its drivers | `run_guarded` (`:1415`), `STALL_S` (`:1413`) |
| `[capture]` per language | `timeout` (900) | `CAPTURE_TIMEOUT_S` |
| `[capture]` build | 3,600 s | `CAPTURE_BUILD_TIMEOUT_S` |
| Hooks | `hook_timeout_s` (600) per command | `run_hook` |

`run_guarded` (`:1415`) is the one place that runs long children. It writes output to a temp file, runs a watchdog thread that (a) kills any
`simctl diagnose` started under the command (Maestro dumps diagnostics after every failed flow; several at once wedge CoreSimulator, and shotfleet
keeps Maestro's own screenshots and logs so they are not needed), and (b) kills the whole process tree when the progress value (newest screenshot
mtime) has not changed for `stall_s`. On timeout, Ctrl-C or SIGTERM it kills every descendant (`descendants`, one `ps` snapshot) so Maestro and
its drivers never keep running. It raises `TimeoutExpired` with `.stalled = True` for the stall case so messages can differ. The overall timeout
scales with the number of languages, so on its own it would let a hung simulator keep a 19-language run alive for hours (seen: 6 h with no screenshot);
the stall watchdog is the fix.

## 2.9 Device locks and sharing a machine

Two layers, both about the same fact: pool simulators share names and emulators sit on fixed ports, so two runs on one Mac reinstall the app
under each other and produce wrong or missing screenshots (seen 2026-10-03).

1. **In the program: `device_lock(key)`** (`:1887`). An `fcntl.flock` on `/tmp/shotfleet-<key>.lock` (`ios-<sim_prefix>` per device type,
   `android-emulators`), non-blocking. If held, `Fail("another shotfleet run is using these devices (<key>, pid N, since HH:MM)...")`, exit 2. The OS
   drops an flock when the holder dies, so there is no stale lock to clean up. The file is opened by `open_lock` (`:1872`): `O_NOFOLLOW`, mode `0o600`, and only used when it is a regular file of this user (a symlink or another user's file in the shared `/tmp` makes the run go on without the lock, with a note; security finding S4). Any other lock error (no `fcntl`, unwritable `/tmp`) also lets the run go
   on without the lock. `USE_DEVICE_LOCK = False` in tests. Text-recognition warm-up has its own lock (`OCR_LOCK`) because one Mac has one
   `ANECompilerService`.
2. **Between agent sessions on the shared development Mac: `docs/device-queue.md`.** A convention, not code: take
   `mkdir /tmp/shotfleet-devices.lock` (with a `holder` file) before booting any simulator or emulator, one device job at a time, a hard time limit on every
   script and waiter, never kill or delete what you have not proven is yours, start only at memory pressure level 1, do not change the machine-wide
   default runtime while others queue. The files live in `/tmp` and die with a reboot; waiters die with their sessions and must be re-armed.

## 2.10 What a failed language tells you

After the retry, for each failed language `failure_details` (`:1695`) prints: the failing step and selector from Maestro's log (`flow_steps` finds the
log that ran this flow; sharded runs tag lines `[shard N]`), the path of the failure screenshot, up to 12 texts that were on that screen (from the
hierarchy Maestro saved with the failure, else one OCR of the screenshot, skipped while macOS is compiling), and the iOS landscape hint if it applies
(`landscape_tap_hint`, `:1654`: Maestro still taps at portrait coordinates after `setOrientation: LANDSCAPE_*`, seen 344 points off on a real iPad
run). `[capture]` runs have no Maestro log; they keep xcodebuild's log per language instead.
