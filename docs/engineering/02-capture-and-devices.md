# 2. Capture and devices

Scope: everything `run` does between "read the app's strings" and "PNG files in `out/raw/<locale>/`": reading translations, rewriting the flow per language, injecting the language into the app (iOS launch arguments, Android per-app locales), booting simulators and emulators, running Maestro under watchdogs, reading each screen's text while the screenshot is on screen, the capacity planner and overload advisor, retries, locks, and the bring-your-own-capture (XCUITest) path. Anchors are `shotfleet.py:LINE` at `7e5176c` (0.1.7). Overview first: [01 runtime architecture](01-runtime-architecture.md). What happens to the PNGs afterwards: [03](03-check-ocr-export.md).

## 2.1 Where the strings come from

The core idea of the product: the translations are compiled into the app build, so shotfleet reads them from the build and rewrites the English flow into each language. The result of every reader is `{locale: {key: text}}`.

| Source | Reader | Notes |
|---|---|---|
| iOS `.app` | `load_strings` `:394` | every `*.lproj/*.strings`, `.stringsdict` (plural forms as `key#form`), and String Catalog output inside the bundle, also inside frameworks, Swift package bundles and an embedded Watch app (keys there get their bundle path as prefix); `Base.lproj` is skipped; Compose Multiplatform `*.cvr` resources (`add_cvr` `:459`). `.strings` files are parsed in Python (`parse_strings_text` `:328`) so Linux needs no `plutil`. A catalog keyed by English text gets a synthetic base table (`:417-425`). |
| Android `.apk` | `load_strings_apk` `:794` | `aapt2 dump resources` (strings, plurals, arrays; non-locale qualifiers like `night`, `land`, `v31` are skipped by `android_locale` `:475`) plus `.cvr` assets for Compose Multiplatform |
| Source files (Flutter, React Native, MAUI, Unity, translation exports) | `read_translation_file` `:646`, driven by `config_strings` `:758` / `load_strings_files` `:773` | `.arb`, `.json` (i18next/react-intl; `key_one`/`key_other` become `key#one`), `.ts/.tsx/.js/.mjs/.cjs` translation objects (read as **data** by `parse_js_translations` `:558`, never executed; code entries are skipped and counted), `.xcstrings`, `.strings`, `.stringsdict`, `.xml` (Android and Compose), `.xlf/.xliff`, `.resx`, `.po`, `.properties`, `.csv` |

The language of a source file comes from its path (`locale_from_path` `:486`: `app_de.arb`, `Resources.de.resx`, `locales/de/translation.json`, `values-de/strings.xml`, `de.lproj/...`) or from the file itself (`@@locale` in `.arb`, a `.po` header). Every locale code is checked against `SAFE_LOCALE` before it can become a folder name (`safe_strings` `:46`).

**Which languages does the app ship?** `shipped_locales` (`:885`). Library resources (AndroidX, Material, Play Services) bring their own strings translated into about 80 locales, so raw coverage would call an English-only app "translated" into 86 languages. The function first separates the app's own strings (keys translated into fewer locales than the libraries' near-universal set; with fewer than 20 locales every key counts as the app's own) and then keeps a language when it has at least half (`min_coverage = 0.5`) of those. `partly_translated` (`:831`) names languages with 10% to 50% coverage so the developer who is mid-translation is told why they were skipped; `locales = [...]` in the config overrides the choice.

`framework_hint` (`:862`) recognises Flutter, React Native, .NET MAUI and Unity builds by file-name markers (`FRAMEWORKS` `:853`) and prints, once, what to add to the config (`strings = "..."`), plus warnings about Flutter debug banners and React Native debug builds with no JS bundle. It never blocks.

## 2.2 Rewriting the flow: `translate_flow`

`translate_flow(flow, base, target, overrides)` (`:949`) is a pure function: the flow text, the base-language table, the target table(s) and the user's `[overrides.<locale>]`. It returns `(translated flow, selectors it could not translate, collisions)`.

What it rewrites: lines whose key is in `SELECTOR_KEYS` (`:297`: `tapOn`, `doubleTapOn`, `longPressOn`, `assertVisible`, `assertNotVisible`, `scrollUntilVisible`, `text`, `copyTextFrom`, `visible`, `notVisible`, and the relative anchors `below`, `above`, `leftOf`, `rightOf`, `childOf`, `containsChild`), in scalar form and in inline-map form (`{ text: "Accept", optional: true }`). Anything else (`inputText`, `launchApp`, ids, points) is left alone. For each selector value:

1. A user override wins (`override_pattern` `:944`; a `re:` prefix is taken as a regex).
2. A wrapped wildcard such as `.*Register` or `Self-hosted.*` (Flutter merges a row's texts into one label) has its inner text translated and the wildcard kept.
3. The English text is looked up among the base table's **values**; each key found gives that key's target translation. One English label can map to several keys, so the result is a regex alternation `(Weiter|Nächste)`, regex-escaped (`regex_literal` `:906`, since Maestro matches selectors as full Java regexes).
4. System dialogs: `SYSTEM_BUTTONS` (`:939`: "Allow", "Don't Allow", "While using the app", ...) are drawn in the device language, which stays English (measured on iOS 27), so the English text is kept as an alternative to any translation.
5. Format strings (`Round %d of %d`, `{name}`): `format_regex`/`fill_format` (`:2943`, `:2961`) match a selector like `Round 2 of 12` against the base format and fill every target plural form with the same numbers.
6. Not found anywhere: the selector is left as is and reported as untranslated.
7. **Collisions**: when two different English labels translate to the same word in one language (Turkish `Next` and `Advanced` both `Ileri`), a tap could hit the wrong element; `collisions` reports it before anything runs, and the README tells the author to anchor that step with `below:`.

`with_fallback` (`:916`) builds the table the app actually shows for a locale the way iOS and Android resolve it: the locale's own strings, then its parents' (`zh-Hant-HK` to `zh-Hant` to `zh`, `pt-BR` to `pt`). `resolve_base` (`:925`) picks the table the flow's language lives in (`en`, else a regional `en-GB`, else a clear error naming the app's development language).

## 2.3 Putting the language into the app

Maestro can run several devices from one process only with `--shard-split`, which hands any flow to any device. So the language cannot live on the device for that path; it has to travel with the flow, or the device must be told after the flow was assigned. The two platforms solve it differently.

### iOS: launch arguments in the flow (`localize_flow`, `:1158`)

Each language gets its own flow file `.work/flows/<lp>.yaml`:

- header: `name: <lp>`, the `appId` of this build (`with_app_id` `:1066`, so one flow serves iOS and Android), and an `env:` block with the language's `[inputs]` values (`inputs_for` `:1074`: defaults, then `[inputs.<lp>]`, exact locale else language part);
- the **first** `launchApp` becomes shotfleet's fresh-state launch: `clearState: true` plus `arguments: AppleLanguages: "(<lp>)"` and `AppleLocale: "<xx_XX>"` (`apple_locale` `:1153` maps the language to the store locale so number and date formats follow it: `de` to `de_DE`, `zh-Hans` to `zh_CN`). The user's own options (permissions, `appId`, extra arguments) are merged, including a one-line `{ ... }` form (`flow_mapping_lines` `:1092`). A flow with no `launchApp` still gets one at the top;
- later `launchApp` steps get the language arguments again, without `clearState`;
- every `takeScreenshot` is redirected to a path relative to Maestro's working directory (`redirect_screenshot` `:1038`, scalar and map forms) and followed by a 1.5 second optional `extendedWaitUntil` on a text that never appears (`pause_after_screenshot` `:1217`), which gives the text reader time to read the screen while it is still showing.

Maestro 2.0.x writes a relative screenshot path under its working directory; Maestro 2.11 refuses a path outside its artifact folder and writes it under `<debug>/.maestro/tests/<run>/<flow>/takeScreenshot/<name>/` instead. `collect_shots` (`:1411`) looks in both places and moves the files into `raw/<locale>/`.

### Android: per-app locale on the emulator, a union flow for the round (`android_run_inner`, `:2725`)

Languages are captured in **rounds** of one language per emulator (`n` emulators, `ceil(languages / n)` rounds). For each round (`round_`, `:2773`):

1. per emulator: `adb shell pm clear <pkg>` (fresh onboarding; it also resets the app language, so the locale is set after), then `adb shell cmd locale set-app-locales <pkg> --locales <lp>` (Android 13 / API 33 or newer, enforced by `require_api33` `:2542`), and the SystemUI demo mode is re-asserted (`DEMO_MODE` `:2431`: fixed clock 9:41, full battery and signal, no notifications, animations and error dialogs off);
2. **one translated flow for the whole round**: `translate_flow` is given the list of the round's languages, so each selector matches the text in **any** of them (`[with_fallback(strings, lp) for lp in lps]`), because Maestro will give any flow to any emulator in an order shotfleet does not control;
3. `android_flow` (`:2630`) writes one copy per emulator (`<tag>_f0.yaml`, ...) with its own name and screenshot folder, starts with a plain `launchApp` (no `clearState`: it would wipe the per-app language just set), and optionally a `runScript` step that supplies per-emulator `[inputs.<locale>]` values keyed by `MAESTRO_DEVICE_UDID` (`android_vars` `:2599`; Maestro 2.0.10 has no such variable, so on 2.0.10 Android types the `[inputs]` defaults);
4. after the Maestro run, `flow_devices` (`:2711`) reads Maestro's log ("Selected device X using port N with execution plan ExecutionPlan(flowsToRun=[...])") to learn which flow ran on which emulator, and therefore which language that screenshot folder holds.

### Reading the screen's own text

This is what makes `check` exact in every script (see [03](03-check-ocr-export.md)):

- **iOS** (`capture_texts` `:1375`, `ios_screen_texts` `:1360`): a thread polls Maestro's `maestro.log` files for the port each flow's driver listens on, and whenever a new PNG appears it POSTs to `http://127.0.0.1:<port>/viewHierarchy` on that driver and saves every `label`, `title`, `value` and `placeholderValue` as `<shot>.texts.json` next to the PNG. On any error it does nothing, and `check` falls back to OCR for that screenshot.
- **Android** (`hierarchy_marker` `:2624`, `hierarchy_texts` `:2682`, `save_hierarchy_texts` `:2702`): never `maestro hierarchy` (it cannot reach the drivers of a sharded run and tore down their port forwards, measured 2026-10-01). Instead, after every `takeScreenshot`, `android_flow` inserts an optional `assertTrue` on `${false}` labelled `shotfleet:hier:<name>`. It ends WARNED, the flow carries on, and Maestro 2.7.0 or newer saves the screen hierarchy for a warned step. shotfleet pairs each marker in `commands.json` with the screenshot before it and writes `<shot>.texts.json`. Below 2.7.0 (`HIER_MIN`, `:2615`) Android screens are read by OCR only.

## 2.4 Devices

### iOS simulators (`make_pool`, `:1312`)

- Names: `shotfleet-<i>` for a single device type, `shotfleet-<device-slug>-<i>` when `device_types` lists several (`device_slug` `:1847`). A simulator with a pool name but another device type is deleted and recreated (screenshots would have the wrong size).
- Each simulator is booted, `bootstatus -b` waited for, and given a clean status bar (`9:41`, wifi, full battery); `simctl spawn defaults write` marks the iOS 26 "Ready for Apple Intelligence" banner as already shown (an inference from the key's name, comment at `:1341`, not verified on a device); then the config's `[ios] simctl` commands run (`run_setup` `:1297`, refused over MCP without `hooks: true`).
- `OUR_SIMS` records the UDIDs at once, so even a failed boot is shut down later and nobody else's simulators are touched. `kill_stale_drivers` (`:1804`) kills Maestro iOS drivers (`xcodebuild test-without-building` with "maestro" in the arguments) attached to shotfleet's UDIDs: a leftover driver keeps port 7001 for its simulator and the next run would silently drive the wrong device.
- **Runtime choice**: with no `runtime` in the config, `latest_ios_runtime` (`:4789`) calls `pick_ios_runtime` (`:4776`), which takes the newest runtime not listed in `BAD_IOS_RUNTIMES` (`:4764`, currently `{"27.0": "its simulators freeze at boot (seen in our own device test runs)"}`). If iOS 27.0 is the only one, it is used with a warning (and `doctor` warns too). A runtime named in the config is always used. Default device: `default_device_type` (`:1836`), iPhone 17 Pro Max (the 6.9 inch size class), falling back to the newest "iPhone N Pro Max".
- **Wedged simulators**: CoreSimulator can stop answering on a loaded Mac. Every `simctl` call has a timeout (`SIM_TIMEOUT_S` 300, boot 900, `uninstall`/`terminate` `SIM_QUICK_TIMEOUT_S` 60, list/create/delete `SIM_LIST_TIMEOUT_S` 120, `:1226-1231`), and `healthy_installs` (`:1253`) installs the app on the simulators **in parallel**, drops any that do not answer (shuts it down, `mark_hung` writes `~/.shotfleet/hung-simulators/<UDID>`), and carries on with the rest; if none answers it raises with the fix. The next `make_pool` sees the marker and replaces that simulator with a new one (`replace_hung` `:1284`).

### Android emulators (`android_pool`, `:2551`)

- Pool: `n` read-only copies of one AVD (`ANDROID_DEVICES` `:2526`: `phone` = `shotfleet_android`, 1080x1920 at 420 dpi, folder `phoneScreenshots`; `tablet` = 1440x2560 at 320 dpi, `tenInchScreenshots`; `tablet-7` = 1080x1920 at 280 dpi, `sevenInchScreenshots`). Sizes are chosen so Google Play can recommend the listing (exactly 9:16 at 1080 px or more, `research/store-specs.md`).
- The AVD is created on first use with `avdmanager` from the best installed system image of API 33 or newer for this machine's ABI (`find_image` `:2387`; `arm64-v8a` on Apple silicon and ARM Linux, `x86_64` elsewhere, `host_abi` `:2348`; `google_apis` preferred over `google_apis_playstore`; default `system-images;android-36;google_apis;<abi>`).
- One-time snapshot: the first time, one writable emulator boots on port 5700, waits 20 s and saves a snapshot named `shotfleet`; later copies boot **from that snapshot, read-only** (4 to 5 s instead of about 22 s cold, measured, `ROADMAP.md`). Emulators run headless (`-no-window -no-audio -no-boot-anim`) on ports 5702, 5704, ... (`Emu`, `:2446`; `start_emu` `:2480`); an emulator already on that port is refused rather than reused.
- Boot success means `sys.boot_completed` is 1 **and** `service check package` says found (`Emu.booted` `:2456`; seen on a busy 2-core machine where the first was true while `adb install` said "Can't find service: package").
- Demo mode is applied after boot, and the config's `[android] shell` commands run on each emulator (`run_setup`).
- Cleanup: `stop_emulators` (`:2464`) asks each emulator to `emu kill` with a short timeout, waits up to `EMU_STOP_WAIT_S = 20`, then kills the process tree; the caller does this in a `finally`.
- Linux: `fit_emulators` (`:1499`) limits the pool to `cores // 2` and `free GB // 3` (about 2 cores and 3 GB per emulator). That figure is one data point (a 2-core runner passed with one emulator and failed with two), noted as `ponytail:` in the code; see [08](08-testing.md) and `docs/linux.md`. `boot_failure_hint` (`:2500`) explains the three known causes: the 12 GB userdata partition on small disks, no `/dev/kvm`, not enough memory or cores.

## 2.5 Running Maestro safely: `run_guarded` (`:1423`)

Every Maestro (and `xcodebuild`, and the `[capture]` build) runs under `run_guarded(cmd, timeout, env, cwd, progress, stall_s)`:

- Output goes to a temp **file**, not a pipe (a daemonised helper that inherited the pipe would block `communicate()` after a kill).
- A watchdog thread wakes every few seconds, kills any `simctl diagnose` started under this command (Maestro runs one after every failed flow; several at once wedge CoreSimulator, and shotfleet keeps Maestro's own logs), and, if a `progress()` callable is given, kills the whole process tree when its value (the newest screenshot's mtime, `newest_screenshot` `:1470`) has not changed for `stall_s` (default 900 s). The overall `timeout` scales with the number of languages, so without the stall check a hung simulator would keep a 19-language run alive for hours (seen: 6 h with no screenshot).
- A timeout, Ctrl-C or SIGTERM kills the descendants (`descendants` `:1349`, one `ps` snapshot) and re-raises; a stall sets `.stalled` on the `TimeoutExpired` so callers can word the message.

## 2.6 The capacity planner and the overload advisor

Both are **warnings only**. Neither changes the pool or refuses a run (`capacity = "adjust"` is refused in the config as "not available yet"). They exist because a loaded Mac makes flows time out and the retries add load.

- **Hard rule that is not a warning**: `fit_parallel` (`:1483`) halves the number of devices under elevated macOS memory pressure (`kern.memorystatus_vm_pressure_level` = "2") and refuses the run under critical pressure ("4"). On Linux `fit_emulators` applies.
- **Planner** (`:1511-1615`): `read_capacity` (impure) asks the Mac for available memory (`vm_stat`: free + inactive + speculative), total memory, swap in use and total, 1-minute load, cores, pressure level and how many pool simulators are already booted; any reading that fails stays `None` and its rule is skipped. `plan_capacity(want, platform, reading)` (pure) returns the fewest of: cores / per-device cores, free memory / per-device GB, half under elevated pressure, one while swapping (>= 10 GB swap in use with too little memory for the pool). Constants: iOS costs 2.0 GB and 1 core per simulator, Android 3.0 GB and 2 cores per emulator, plus 1.5 GB for Maestro and 2.0 GB headroom (`CAPACITY_COST`, `CAPACITY_BASE_GB`, `CAPACITY_HEADROOM_GB`, `CAPACITY_SWAP_GB`, `:1513-1516`; labelled provisional in the comments: the swap figure is read from two 2026-10-05 gate runs, the per-device costs are estimates). `capacity_message` words the advice ("Close Xcode, Android Studio and other simulators, run ./gradlew --stop ...").
- **Overload advisor** (0.1.7, `:1617-1645`): `busy_reasons` flags swap at least 90% full, critical pressure, or load at least 10 per core (`BUSY_SWAP_FRACTION`, `BUSY_LOAD_PER_CORE`; provisional, from a 2026-10-07 run at load 500 to 800 where every `simctl uninstall` timed out). `busy_warn` prints one plain warning per run (`BUSY_STATE`), suggests `--parallel` half as many, and is called again before a retry and between Android rounds. `capacity_warn` (`:1647`) prints the advisor's warning if it fires, otherwise the planner's, never both. `capacity = "off"` silences both.

## 2.7 Failures, retries and `--retry-failed`

**What is retried by itself (0.1.7).** After the first attempt, `retry_choice` (`:1668`) splits failed languages into those whose error looks like the device or Maestro breaking and those that do not. `is_infra_error` (`:1663`) matches the lowercase error against `INFRA_ERRORS` (`:1658`): "unknown error", "unable to clear state" (Maestro's words when a slow simulator times its simctl calls out), "no result", "flow never ran", "no progress for", "did not answer", "not responding", "stopped answering", "offline", "emulator did not boot", "emulators did not boot", "can't find service", "not found: emulator". Only those are retried, once. A language that failed on a missing element, a wrong screenshot count or a blank screen would fail the same way again, so it is **not** retried, and `say_not_retried` (`:1674`) tells the user which ones and that `run <config> --retry-failed` reruns just them after a fix. Add a phrase to `INFRA_ERRORS` when a new device failure shows up.

The retry is careful: it warns again if the Mac got busier (`busy_warn`), clears the failed languages' `raw/` folders, and runs `healthy_installs` again first (Maestro's `clearState` uninstalls and reinstalls the app, and a slow simulator that timed out half-way leaves the app gone, so every flow of a blind retry would fail within seconds). If no simulator answers any more, it keeps what attempt 1 captured, checks it, and reports the rest as failed (exit 1). On Android the same logic lives in `safe_round` (`:2821`): an emulator that stops answering adb ends capturing, not the report; the remaining languages are reported as `not captured: ...`.

**`run --retry-failed`.** `retry_setup` (`:1679`) reads `out/run.json` (refusing a missing/unreadable file or one written by another config), returns the languages with `ok: false`, and `keep_earlier` (`:1689`) puts the passed languages back into the new report in their old order and adds the earlier tries to the retried languages' `attempts`. If nothing failed, `run_platform` prints "nothing to retry" and exits 0 before building or booting anything. It cannot be combined with `--locales`.

**Failure explanations** (`failure_details` `:1780`): the failing step and selector from Maestro's log (`flow_steps` `:1727`), the failure screenshot path, up to 12 texts that were on that screen (from the hierarchy Maestro saved with the failure, else one OCR read of the screenshot, skipped while macOS text recognition is busy, `screenshot_texts` `:1770`), and a one-line explanation of the Maestro iOS landscape tap bug when the log shows exactly that (`landscape_tap_hint` `:1739`). `flow_parse_note` (`:1710`) says "Parsing Failed" is a YAML problem, not a memory problem; `overload_note` (`:1700`) prints the "this Mac was short of memory" note only when a failure's error is `Unknown error` or `Unable to clear state`.

**Known gap (documentation versus code).** The README, the docs page and the skill's troubleshooting table still say that `run` captures a **blank** language "again once". In 0.1.7 a blank screenshot is not an infrastructure error, so it is reported and not retried (verified: `is_infra_error` on the real `blank_note` text returns False). The comments at `shotfleet.py:4579` and `:4962-4965` carry the same stale sentence. See the corrections list in the [README](README.md).

## 2.8 Locks

Two different locks exist; do not confuse them.

1. **Inside the program** (`device_lock`, `:1980`): one shotfleet run at a time per set of devices. `flock` on `/tmp/shotfleet-<key>.lock`, where `<key>` is `ios-<simulator prefix>` (`ios-shotfleet`, or `ios-shotfleet-<device-slug>` per device type) or `android-emulators`. The lock file is opened with `O_NOFOLLOW`, mode 0600, and used only if it is a regular file owned by this user (`open_lock` `:1965`); otherwise the run goes on without it with a note. The OS drops an `flock` when the process dies, so no lock is ever stale. A second run gets `another shotfleet run is using these devices (<key>, pid N, since HH:MM)`; exit 2. A second lock, `/tmp/shotfleet-ocr-warmup.lock`, serialises the warm-up of macOS text recognition (see [03](03-check-ocr-export.md)).
2. **Between humans and agent sessions** (not code): `docs/device-queue.md`. Many agent sessions share one Mac; two device jobs at once made simulators hang and voided runs. The convention is `mkdir /tmp/shotfleet-devices.lock` with a holder line, a queue file `/tmp/shotfleet-device-queue.md`, a hard time limit on every waiter, and never killing what you did not create. These files live in `/tmp` and vanish on reboot. Anything that boots a simulator or emulator (including `tools/fixture-e2e.sh`, `shotfleet run`, `maestro`) takes it first. See [08](08-testing.md) and [10](10-contributing.md).

## 2.9 Bring your own capture (iOS `[capture]`)

For teams that already have XCUITest screenshot tests (`XCTAttachment` or fastlane `SnapshotHelper`). `run` then uses the same simulator pool but runs `xcodebuild test-without-building` instead of Maestro. Notes in `research/byoc-ios-experiment-2026-10-06.md`; the device test (`tools/fixture-byoc-e2e.sh`) passed on 2026-10-07 on iOS 26.4 (flag file `site/BYOC_DEVICE_PROVEN`, see [07](07-website-and-backend.md)).

1. `capture_build` (`:2267`) runs the team's `build` command once (`/bin/sh -c`, in the config's folder, 1 hour limit, output in `out/build.log`), unless `--no-build`. It is refused over MCP without `hooks: true`.
2. `find_xctestrun` (`:2281`) requires exactly one match for the `xctestrun` glob. The app under test is read from the `.xctestrun` (`xctestrun_app` `:2295`, `UITargetAppPath` or the first non-runner `.app`) unless `[ios] app` names it.
3. Per language, on whichever simulator is free (`capture_batch`, one `xcodebuild` per simulator at a time): `set_sim_language` writes `AppleLanguages` and `AppleLocale` into the simulator (`xcodebuild`'s `-testLanguage` is **ignored** with `-xctestrun`, measured), the app is uninstalled for a fresh state, `xctestrun_with_language` (`:2301`) writes a per-language copy beside the original (paths inside are relative to its folder) with `-AppleLanguages`/`-AppleLocale` added to the UI target's command-line arguments, and `xcodebuild test-without-building -xctestrun ... -destination id=<udid> -resultBundlePath ...` runs under `run_guarded`.
4. Screenshots come from two places: the result bundle's PNG attachments (`xcresult_pngs` `:2222`, via `xcrun xcresulttool export attachments`; two attachments with one name both kept as `name.png` and `name-2.png` with a warning) and fastlane's SnapshotHelper cache folder `~/Library/Caches/tools.fastlane/screenshots` (`fastlane_pngs` `:2336`, files named `<simulator name>-<shot>.png`). `fastlane_cache` (`:2245`) makes that folder if it is missing (SnapshotHelper never does, and a test then passes with no screenshots), moves fastlane's `language.txt`, `locale.txt` and `snapshot-launch_arguments.txt` aside for the run (they would force one language on every simulator), and always puts them back, also after a SIGKILL'd run (it restores leftovers on the next start).
5. A passing test proves nothing: `capture_result` (`:2328`) fails a language that saved no screenshot (`NO_SHOTS_HINT`), that lacks a screen another language has, or that has a blank frame.
6. The rest (retry, `check`, `export`) is shared with the Maestro path. `doctor` does not ask for Maestro or Java for an iOS-only `[capture]` config.

## 2.10 Hooks and config commands

`[hooks]` (shell, around `run` and `export`), `[capture] build` (shell), `[ios] simctl` (host `xcrun simctl`) and `[android] shell` (device `adb shell`) are the config's four ways to run a command. `config_commands` (`:1869`) lists them; `refuse_config_commands` (`:1878`) is the last guard that stops them from running over MCP unless `hooks: true` was passed. A config from a cloned repo can hold any command, which is why the gate exists. See [04](04-setup-mcp-skills.md).

## 2.11 Added after 0.1.7 (branch `claude/018-capture-check`; line anchors above are from 0.1.7, search by name)

- `SELECTOR_KEYS` now has `element` (scrollUntilVisible's plain-text form); `INLINE_RE` skips a value that opens a nested `{`, so `{ element: { text: ... } }` is translated once, through `text`.
- `settle_before` / `SETTLE_MS`: `localize_flow` and `android_flow` take `settle_ms` (default 0, so old callers and tests see no change); `ios_run_inner` and `android_run_inner` pass `cfg.get("settle_ms", SETTLE_MS)`. Config key `settle_ms`, 0 to 10000.
- `match_locales`: maps the languages the user asked for onto the codes the build ships (canon equality, case, a language alone to its only regional variant and back; never across a Chinese script or a different region); both run paths call it before `cap_locales`.
- `no_result` / `INFRA_ERRORS`: a flow Maestro never reported on gets "driver did not start in time" when its log says so (still a device failure, so retried once).
- `no_hierarchy_note`: the Android OCR fallback text, printed at the start and again before the check.
- `replace_hung` keeps the name (`make_pool` creates `shotfleet-<i>` again); the message says so.
