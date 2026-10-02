# shotfleet.toml

`shotfleet init <build>` writes the config and `flow.yaml`; `shotfleet init` alone uses the newest Debug simulator build
(from Xcode's default DerivedData, matched to the project in the current folder) and the newest Gradle debug APK it finds
there, and says which. Only the build is required; everything else is read from
the build or defaulted. A typo or a wrong type is refused with a one-line message before anything runs
(`has an unknown setting 'x'; did you mean 'y'?`, `should be a whole number, not 'x'`). Paths are relative to the
config file; absolute and `~/` paths work.

```toml
[ios]
app = "path/to/MyApp.app"          # required: a simulator build (Debug-iphonesimulator)

[android]                          # optional: the same file and flow serve both platforms
apk = "path/to/app-debug.apk"      # required in this section
```

`shotfleet run` runs both platforms when the file has both; `--platform ios` or `--platform android` picks one.
With both, output goes to `out-ios/` and `out-android/`; with one, to `out/`.

## Keys

Tables allowed: `[ios]`, `[android]`, `[hooks]`, `[overrides.<locale>]`, `[inputs]`. Any other table is refused.

Keys valid in `[ios]` and `[android]`:

| Key | Type | Default | Meaning |
|---|---|---|---|
| `flow` | string | `flow.yaml` | the English Maestro flow, shared by both platforms |
| `out` | string | `out`, or `out-ios` / `out-android` | output folder (`raw/<locale>/`, `check.json`, `index.html`, `run.json`, logs) |
| `parallel` | whole number | 4 | simulators (emulators on Android) at once; `--parallel` overrides |
| `locales` | list | every language the app ships | languages to capture, as shotfleet names them (`de`, `pt-BR`, `zh-Hans`); `--locales` overrides |
| `base_locale` | string | `en` | the language the flow is written in |
| `strings` | string or list | read from the build | translation file globs (relative to the config) for Flutter, React Native, MAUI, Unity, exports |
| `timeout_s` | whole number | 600 | time limit in seconds for one round of flows (accepted by the config check; not described in the README) |

`[ios]` only:

| Key | Default | Meaning |
|---|---|---|
| `app` (required) | none | simulator `.app` |
| `bundle_id` | read from the app | refused if it differs from the app's |
| `device_type` | iPhone 17 Pro Max (6.9") | CoreSimulator device type id or name |
| `device_types` | none | several sizes from one flow, e.g. `["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]`; output goes to `out/<device>/` and `check`/`export` handle the folder; an app that runs on iPad needs the 13" iPad set |
| `runtime` | newest installed iOS | CoreSimulator runtime id |

`[android]` only:

| Key | Default | Meaning |
|---|---|---|
| `apk` (required) | none | debug APK, API 33+ emulators |
| `package` | read from the APK | refused if it differs |
| `devices` | phone only | `["phone", "tablet"]`: phone 1080x1920 and tablet 1440x2560; output in `out/<device>/`, exported to `phoneScreenshots` and `tenInchScreenshots` |
| `avd` | `shotfleet_android` | name of the phone emulator (accepted by the config check; not described in the README) |
| `avd_tablet` | `shotfleet_android_tablet` | name of the tablet emulator when `devices` includes `"tablet"` (accepted by the config check; not described in the README) |
| `system_image` | newest installed arm64 `google_apis` or `google_apis_playstore` image of API 33+, else `system-images;android-36;google_apis;arm64-v8a` | image for the emulator shotfleet creates (same note) |

A language with under 50% of the app's own strings translated is skipped with a `note:`; list it in `locales` to
capture it anyway.

## Frameworks with translation files

```toml
strings = "lib/l10n/*.arb"                      # Flutter
strings = "src/locales/*/translation.json"      # React Native / Expo with i18next
strings = ["Resources/Strings/*.resx"]          # .NET MAUI
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
- Variables: `SHOTFLEET_EVENT`, `SHOTFLEET_VERSION`, `SHOTFLEET_CONFIG`, `SHOTFLEET_PLATFORM`, `SHOTFLEET_OUT`, `SHOTFLEET_BUNDLE_ID`. `before_run` and `after_run` also get `SHOTFLEET_LOCALES`; `after_run` gets `SHOTFLEET_EXIT`, `SHOTFLEET_PROBLEMS`, `SHOTFLEET_REPORT` (`<out>/check.json`); the export hooks get `SHOTFLEET_FASTLANE`, `SHOTFLEET_REPORT`, and `SHOTFLEET_EXIT` after the export.
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
language's flow; Android runs type the defaults only. Unit-tested as flow text, not yet run on a device: check the first
screenshots in a script like Japanese or Arabic.

## Plugins and other switches

- `shotfleet foo` runs `shotfleet-foo` from the PATH when `foo` is not a built-in command (like `git` and `gh`).
- `SHOTFLEET_OCR` or `--ocr-command` swaps the text reader for scripts macOS can't read: `"tesseract {image} stdout -l {tesseract}"` (`{lang}` is the language code).
- `SHOTFLEET_KEY` is the licence key for CI (see licence.md and ci.md).
- `shotfleet skill install` copies these skills into `~/.claude/skills` (`--project` for `./.claude/skills`, `--dir` for another agent).
- `shotfleet mcp` is an MCP server with `check`, `run` and `doctor`: `claude mcp add shotfleet -- shotfleet mcp`.
