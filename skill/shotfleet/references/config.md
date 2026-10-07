# shotfleet.toml

`shotfleet init <build>` writes the config and `flow.yaml`; `shotfleet init` alone uses the newest Debug simulator build
(from Xcode's default DerivedData, matched to the project in the current folder) and the newest Gradle debug APK it finds
there, and says which. Only the build is required; everything else is read from
the build or defaulted. A typo or a wrong type is refused with a one-line message before anything runs
(`has an unknown setting 'x'; did you mean 'y'?`, `should be a whole number, not 'x'`). Paths are relative to the
config file; absolute and `~/` paths work. `init` writes a build inside the project folder as a relative path (commit the config) and prints a note when the build is outside it and the path is absolute or `~/`.

```toml
[ios]
app = "path/to/MyApp.app"          # required: a simulator build (Debug-iphonesimulator)

[android]                          # optional: the same file and flow serve both platforms
apk = "path/to/app-debug.apk"      # required in this section
```

`shotfleet run` runs both platforms when the file has both; `--platform ios` or `--platform android` picks one.
With both, output goes to `out-ios/` and `out-android/`; with one, to `out/`.

## Keys

Tables allowed: `[ios]`, `[android]`, `[hooks]`, `[overrides.<locale>]`, `[inputs]`, `[expect.<screenshot>]`, `[capture]`. Any other table is refused.

Keys valid in `[ios]` and `[android]`:

| Key | Type | Default | Meaning |
|---|---|---|---|
| `flow` | string | `flow.yaml` | the English Maestro flow, shared by both platforms |
| `out` | string | `out`, or `out-ios` / `out-android` | output folder (`raw/<locale>/`, `check.json`, `index.html`, `run.json`, logs) |
| `parallel` | whole number | 4 | simulators (emulators on Android) at once; `--parallel` overrides |
| `capacity` | string | `warn` | `warn` prints a warning when the Mac is short of memory or already swapping hard; `off` is silent. It never changes the run |
| `locales` | list | every language the app ships | languages to capture, as shotfleet names them (`de`, `pt-BR`, `zh-Hans`); `--locales` overrides |
| `base_locale` | string | `en` | the language the flow is written in |
| `strings` | string or list | read from the build | translation file globs (relative to the config) for Flutter, React Native, MAUI, Unity, exports |
| `stall_s` | whole number | 900 | seconds without a new screenshot before a run is stopped as hung (a stuck simulator or flow) and retried once |
| `timeout_s` | whole number | 600 | time limit in seconds for one round of flows (accepted by the config check; not described in the docs) |

`[ios]` only:

| Key | Default | Meaning |
|---|---|---|
| `app` (required) | none | simulator `.app` |
| `bundle_id` | read from the app | refused if it differs from the app's |
| `device_type` | iPhone 17 Pro Max (6.9"); an Xcode without it gets its newest `iPhone N Pro Max` | CoreSimulator device type id or name; one you set is never changed |
| `device_types` | none | several sizes from one flow, e.g. `["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]`; output goes to `out/<device>/` and `check`/`export` handle the folder; an app that runs on iPad needs the 13" iPad set |
| `runtime` | newest installed iOS | CoreSimulator runtime id. Installing an iOS 27 runtime changes what `run` uses; to stay on a runtime you have tested, pin it: `runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"` (`xcrun simctl list runtimes` shows the ids) |
| `simctl` | none | list of `xcrun simctl` commands run once per simulator after boot and the status bar; `$UDID` is the simulator's id, e.g. `["ui $UDID appearance dark"]`; applies to every language |

`[android]` only:

| Key | Default | Meaning |
|---|---|---|
| `apk` (required) | none | debug APK, API 33+ emulators |
| `package` | read from the APK | refused if it differs |
| `devices` | phone only | `["phone", "tablet"]`: phone 1080x1920 and tablet 1440x2560; output in `out/<device>/`, exported to `phoneScreenshots` and `tenInchScreenshots`; `"tablet-7"` adds a 7" tablet, 1080x1920 at 280 dpi, exported to `sevenInchScreenshots` |
| `shell` | none | list of commands run as `adb -s <serial> shell <command>` once per emulator right after boot (after demo mode), e.g. `["setprop debug.myapp.demo 1"]`; not run on a real emulator yet |
| `avd` | `shotfleet_android` | name of the phone emulator (accepted by the config check; not described in the docs) |
| `avd_tablet` | `shotfleet_android_tablet` | name of the tablet emulator when `devices` includes `"tablet"` (accepted by the config check; not described in the docs) |
| `avd_tablet-7` | `shotfleet_android_tablet7` | name of the 7" tablet emulator when `devices` includes `"tablet-7"` (same note) |
| `system_image` | newest installed arm64 `google_apis` or `google_apis_playstore` image of API 33+, else `system-images;android-36;google_apis;arm64-v8a` | image for the emulator shotfleet creates (same note) |

## Your own XCUITest screenshot tests (iOS, `[capture]`)

Instead of a Maestro flow, `run` can run the team's existing XCUITest screenshot tests (XCTAttachment or fastlane's
`SnapshotHelper`) on its simulators, one language per simulator. `[capture]` and `flow` are refused together; `app` is
optional (default: the app next to the `.xctestrun`). Maestro is not needed for this. New in 0.1.6; its device test passed on iOS 26.4 simulators.

```toml
[ios]
locales = ["de", "ja", "ar"]

[capture]
build = "xcodebuild build-for-testing -scheme MyApp -destination 'generic/platform=iOS Simulator' -derivedDataPath .shotfleet/build"
xctestrun = ".shotfleet/build/Build/Products/*.xctestrun"   # glob, exactly one match after the build
only_testing = ["MyAppUITests/ScreenshotTests"]             # optional, passed as -only-testing
screenshots = "auto"     # "attachments" (XCTAttachment), "fastlane" (SnapshotHelper) or "auto" (both)
timeout = 900            # seconds per language
```

- `build` runs once per `run`, with `/bin/sh` in the config's folder (output in `<out>/build.log`); `run --no-build` skips it.
- shotfleet sets each simulator's language itself (`simctl spawn <udid> defaults write -g AppleLanguages`/`AppleLocale`) and
  adds `-AppleLanguages (<lang>) -AppleLocale <locale>` to a copy of the `.xctestrun` next to the original. Don't pass `-testLanguage`.
- An XCTAttachment needs `lifetime = .keepAlways`, or a passing test keeps none. `SnapshotHelper` writes to
  `~/Library/Caches/tools.fastlane/screenshots`; shotfleet makes it if missing and moves fastlane's `language.txt`,
  `locale.txt` and `snapshot-launch_arguments.txt` aside during the run.
- A language that saved no screenshot, or lacks a screen another language saved, fails (exit 1), even when the test passed.
- Paid like any `run`: 2 languages without a licence. `check` stays free.

A language with under 50% of the app's own strings translated is skipped with a `note:`; list it in `locales` to
capture it anyway.

## Frameworks with translation files

```toml
strings = "lib/l10n/*.arb"                      # Flutter
strings = "src/locales/*/translation.json"      # React Native / Expo with i18next
strings = ["Resources/Strings/*.resx"]          # .NET MAUI
strings = "app/i18n/*.ts"                       # Ignite, i18n-js, vue-i18n: texts written as an object in code (read as data, never run)
```

Put it under `[ios]` and/or `[android]`. Formats: `.arb`, i18next/react-intl `.json`, `.xcstrings`, `.strings`,
`.stringsdict`, Android `strings.xml`, XLIFF (`.xlf`, `.xliff`), `.resx`, `.po`, `.properties`, CSV with one column per
language (Unity Localization). The language comes from `@@locale`, the file name (`app_de.arb`,
`Resources.de.resx`) or the folder (`locales/de/`, `values-de/`). `check` takes the same: `--strings '<glob>'`.
When `init`, `run` or `check` sees a Flutter, React Native, MAUI or Unity build, it prints `hint:` with the line to
add. It detects them by file names in the build, so it can miss versions.

## Hooks

Nothing runs unless the user wrote a `[hooks]` table. Commands run with `/bin/sh` in the config's folder, output on
stderr. A value is a string or a list of commands run in order. `--no-hooks` skips them.

```toml
[hooks]
before_run    = "make build-sim"
after_run     = 'curl -sS -X POST "$SLACK_WEBHOOK_URL" --data "{\"text\":\"shotfleet: $SHOTFLEET_PROBLEMS problem(s)\"}"'
before_export = "git diff --quiet"        # a non-zero exit stops the export
after_export  = 'fastlane deliver --skip_binary_upload --skip_metadata --overwrite_screenshots --screenshots_path "$SHOTFLEET_FASTLANE/screenshots"'
# hook_timeout_s = 1800                   # default 600 per command
```

- A failing `before_*` hook stops the command (exit 2); a failing `after_*` hook makes the exit code 1.
- Variables on every event: `SHOTFLEET_EVENT`, `SHOTFLEET_VERSION`, `SHOTFLEET_CONFIG`, `SHOTFLEET_PLATFORM`, `SHOTFLEET_OUT`. `before_run` and `after_run` also get `SHOTFLEET_BUNDLE_ID` and `SHOTFLEET_LOCALES` (empty unless restricted); `after_run` gets `SHOTFLEET_EXIT`, `SHOTFLEET_PROBLEMS`, `SHOTFLEET_REPORT` (`<out>/check.json`); the export hooks get `SHOTFLEET_FASTLANE`, `SHOTFLEET_REPORT`, and `SHOTFLEET_EXIT` after the export.
- Never add a hook that uploads to a store on the user's behalf without them asking for it. The `after_export` example above does; it is theirs to choose.

## Overrides

Replace what shotfleet taps for one language: the fix for a collision warning and for labels that are not in the app's
strings.

```toml
[overrides.tr]                  # the language as shotfleet names it: tr, pt-BR, zh-Hans...
"Next" = "İleri"                # literal text
"Advanced" = "re:Gelişmiş.*"    # "re:" = a regular expression
```

Values must be strings (`should map English texts to text in that language`).

## Inputs

Text a flow types, per language. The flow says `inputText: ${name}`:

```toml
[inputs]            # default for every language without its own value
name = "Alex"
[inputs.ja]         # language as shotfleet names it; `pt` covers pt-BR
name = "田中"
```

Values must be text and names letters, digits or `_`. iOS runs get the language's value as a Maestro `env:` entry in that
language's flow. On Android a name with a per-language value is read from `shotfleet_vars.js`, which picks the emulator's
row by `MAESTRO_DEVICE_UDID`; Maestro 2.11.0 sets it to the emulator's serial (German and Japanese values showed up as typed in screenshots, device run
2026-10-04: one emulator, one language after the other; two emulators at once and Arabic not run). Maestro 2.0.10 doesn't define it, so on
2.0.10 Android runs type the defaults only. Check the first screenshots in a script like Japanese or Arabic.

A failing `simctl` or `shell` command stops the run before capture (exit 2) and prints the command.

## Expected content

Prove the seeded content is on screen, per language. The table is named after the screenshot (`takeScreenshot: 01_home`):

```toml
[expect.01_home]
any = ["Senior iOS Engineer"]     # at least one on screen
[expect.01_home.de]               # one language only (`pt` covers pt-BR)
all = ["Steinmännchen"]           # every one on screen
[expect.03_log]
not = ["No workouts yet"]         # must not be on screen
```

Keys are `any`, `all`, `not`, each a non-empty list of texts; a typo is refused (`unknown setting 'anny'; did you mean 'any'?`).
`run` applies them itself; `shotfleet check <out> --content [shotfleet.toml]` applies them to existing screenshots (free,
no licence; put `--content` after the folder). Problems are `<locale>/<file>: expected "text" on screen` or `... must not be on
screen`, a table naming no screenshot is a problem, and a locale table matching no language is a note. Case, accents and spacing are ignored.
iOS compares the app's own text (exact in any script). Android is OCR: a text in a script macOS can't read is a note,
`could not verify`, never a pass or a fail. The `check` JSON keeps its keys (`exit`, `screenshots`, `problems`, `notes`).

## Plugins and other switches

- `shotfleet foo` runs `shotfleet-foo` from the PATH when `foo` is not a built-in command (like `git` and `gh`).
- `SHOTFLEET_OCR` or `--ocr-command` swaps the text reader for scripts macOS can't read: `"tesseract {image} stdout -l {tesseract}"` (`{lang}` is the language code).
- `SHOTFLEET_KEY` is the licence key for CI (see licence.md and ci.md).
- `shotfleet skill install` copies these skills into `~/.claude/skills` (Claude Code, Cursor) and `~/.agents/skills` (Codex, Gemini CLI, GitHub Copilot, Cursor). `--project` uses `./.claude/skills` and `./.agents/skills`; `--dir` one folder you choose.
- `shotfleet mcp` is an MCP server with `check`, `run` and `doctor`: `claude mcp add shotfleet -- shotfleet mcp`.
