# shotfleet

Localized App Store and Google Play screenshots from **one English Maestro flow**: every language your app ships, captured in parallel, checked, and ready for fastlane.

```
$ shotfleet run shotfleet.toml
capturing 18 locales on 4 simulators...
ok   ar       4/4 screenshots
ok   de       4/4 screenshots
...
captured 18/18 locales in 534s on 4 simulators
checked 72 screenshots in 18 languages: 0 problem(s)
```

## Why

Localized screenshots often end up as **the English set copied into every language folder**. That happens because the UI script that drives the app taps English buttons ("Next", "Settings"), so it can't run in German or Japanese without a separate copy per language.

shotfleet reads the translations **compiled into your app** and rewrites the script for each language. "Next" becomes "Weiter", "次へ" or "İleri". Then it runs every language at once and checks the result.

## What it checks

After capture, every screenshot's text is compared against your app's own strings. On iOS, shotfleet reads the text straight from the app while each screenshot is on screen (exact, in every script); otherwise, and for screenshots made by other tools, it uses macOS's built-in text recognition:

- **Wrong language:** the German folder actually shows English or Japanese strings.
- **Copies:** the same image in two languages.
- **Missing:** a language that didn't produce every screenshot.
- **Translation collisions, before anything runs:** for example, `tr: 'Next' -> 'İleri' also means 'Advanced'`. A tap could hit the wrong button there, so you anchor that step with `below:`.

- **Store rules:** sizes each store accepts (every App Store display class, Play's 320–3840 px), at most 10 (App Store) or 8 (Play) per listing, no transparency, a 6.9" or 6.5" iPhone set, a 13" iPad set when the app runs on iPad. Notes (not failures) for Play's 2:1 rule and for listings that can't be recommended by Google Play (fewer than 4 screenshots at 1080px+ in exactly 9:16 or 16:9).
- **Languages your app doesn't have:** a store listing (say Traditional Chinese) whose screenshots can't be in that language because the app isn't translated into it.

### Check screenshots made by any tool

Already have screenshots from fastlane snapshot/screengrab, StoreScreens or by hand? Check them without capturing anything:

```bash
shotfleet check fastlane/ --app path/to/MyApp.app          # deliver: screenshots/<locale>/
shotfleet check fastlane/ --app path/to/app-release.apk    # supply: metadata/android/<locale>/images/phoneScreenshots/
```

Store codes are mapped back to your app's languages (`de-DE` to `de`, `no` to `nb`, `zh-CN` to `zh-Hans`). The report (`check.json` and `index.html`) goes to `./shotfleet-check` (change it with `--report`), and your fastlane folders are never touched. On CrossfitTracker's committed fastlane screenshots (252 iOS, 126 Android) it took about 25 seconds per platform. It found one real problem: the Traditional Chinese listings have Chinese captions over an English app. When we planted English screenshots in the German folder and deleted a Japanese one, both were reported.

It also finds real localization bugs. On CrossfitTracker it found an onboarding page whose Next button was unreachable on small phones in Japanese, Korean, Chinese and Arabic.

## Free and paid

`shotfleet check` is free for everyone, and `run` is free for up to 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once per developer, with a year of updates and a 14-day refund (see the site's licence page).

## Quickstart (once Maestro and a simulator build exist)

```bash
curl -fsSL https://shotfleet.com/install.sh | sh   # signed, notarized; Apple silicon
shotfleet activate <your key>                      # from your purchase email (`check` works without one)
shotfleet doctor                                   # checks Maestro, Java, Xcode, Android SDK
shotfleet init                                     # in your project folder: uses the newest Debug simulator build and Gradle debug APK it finds
shotfleet init path/to/MyApp.app path/to/app-debug.apk   # or name a simulator build (Debug-iphonesimulator) and/or an APK yourself
```

`shotfleet init` without arguments only reads folders, never builds. For iOS it takes the newest `Debug-iphonesimulator` app in Xcode's default DerivedData folder (`~/Library/Developer/Xcode/DerivedData`) whose `info.plist` points at an Xcode project in this folder (or one folder below it, or above it). For Android it takes the newest APK under `app/build/outputs/apk/debug` (or `<module>/build/outputs/apk/debug`, one folder below). It prints which build it chose and how old it is. If it finds nothing it exits with the exact `xcodebuild` and `./gradlew assembleDebug` commands to run, then run `shotfleet init` again. If you build somewhere else (a custom DerivedData location), pass the path as above.

1. Edit the generated `flow.yaml`: [Maestro](https://maestro.mobile.dev) steps in English. Navigate by the text users see and add a `takeScreenshot:` for each store image. No `appId` needed: shotfleet uses each build's own id, so one flow serves iOS and Android.
2. Try one language: `shotfleet run --locales en`.
3. Run them all: `shotfleet run` (finds `./shotfleet.toml`; both platforms if the file has both, `--platform ios` for one).
4. Review `out/index.html` (`out-ios/` and `out-android/` if the config has both platforms). It's a grid with a row per language and a column per screen, and problems are outlined in red.
5. Export to fastlane: `shotfleet export out --fastlane fastlane/` (`out-ios` or `out-android` if the config has both). That writes `deliver`'s `screenshots/<locale>/` or `supply`'s `metadata/android/<locale>/images/phoneScreenshots/`. Languages that failed a check are skipped, so a bad screenshot never reaches a listing.

## Uploading

shotfleet stops at fastlane's folders; fastlane uploads them. Screenshots only, nothing else touched:

```bash
# App Store: replaces the screenshots of every language folder in fastlane/screenshots
fastlane deliver --skip_binary_upload --skip_metadata --overwrite_screenshots --force

# Google Play: uploads metadata/android/<locale>/images/phoneScreenshots
fastlane supply --skip_upload_apk --skip_upload_aab --skip_upload_metadata --skip_upload_changelogs --skip_upload_images
```

Run `shotfleet check fastlane/` right before uploading: export already skips languages that failed, and the check
also catches folders you edited by hand.

## In CI

`run`, `check` and `export` take `--json`: the result goes to stdout as JSON (`exit`, `screenshots`, `problems` for `run` and `check`; `exit`, `exported`, `skipped` for `export`) and progress goes to stderr. Exit codes: `0` all good, `1` problems found, `2` setup error (the message says what to fix), `130` interrupted.

Checking needs only a Mac (it uses macOS text recognition), with no simulators, so it fits a pull-request job on GitHub's macOS runners. `check` is free and needs no licence. (This recipe hasn't been run on GitHub yet; the command itself is the one tested above.)

```yaml
# .github/workflows/screenshots.yml
on: pull_request
jobs:
  check-screenshots:
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - run: xcodebuild -scheme MyApp -sdk iphonesimulator -configuration Debug -derivedDataPath build build
      - run: curl -fsSL https://shotfleet.com/install.sh | sh   # Apple silicon runner
      - run: shotfleet check fastlane/ --app build/Build/Products/Debug-iphonesimulator/MyApp.app --json > check.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: screenshot-check
          path: |
            check.json
            shotfleet-check/
```

To use `run` or `export` in CI, set `SHOTFLEET_KEY` to your licence key (keep it in a secret). It's checked online on each run and uses none of your 3 activations; if the licence server can't be reached the job isn't failed. With an invalid key, `export` refuses and `run` captures only 2 languages.

## With AI agents

`shotfleet mcp` is an MCP server with `check`, `run` and `doctor` tools. Add it to Claude Code with
`claude mcp add shotfleet -- shotfleet mcp`, or to any MCP client as the command `shotfleet mcp`. There is also a
Claude Code skill in `skill/shotfleet/`.

## How it works

| | iOS | Android |
|---|---|---|
| Strings | `*.lproj/*.strings` inside the `.app` | `aapt2 dump resources` of the APK, keeping only languages the app itself ships (libraries add ~70 near-empty ones) |
| Language | launch arguments `-AppleLanguages (de)` | per-app locale `cmd locale set-app-locales` (Android 13+) |
| Devices | N simulators, iPhone 17 Pro Max (1320×2868, App Store 6.9") | N read-only emulators at 1080×1920 |
| Status bar | `simctl status_bar` override: 9:41, full battery | SystemUI demo mode: 9:41, full battery, no notifications |
| Parallelism | one sharded Maestro run | rounds of one language per emulator; Maestro's log says which flow ran where |

Every selector is rewritten to match **any** translation of that English label. If "Next" has two keys, German matches `(Nächste|Weiter)`. Selectors that use `id:` pass through untouched.

## Config

The whole config can be this (`shotfleet init` writes it):

```toml
[ios]
app = "path/to/MyApp.app"

[android]                 # optional: the same file and flow serve both platforms
apk = "path/to/app-debug.apk"
```

Everything else is read from the build or has a default; set it only to change it. A typo or a wrong type is refused
with a one-line message before anything runs.

```toml
[ios]
flow = "flow.yaml"        # default; shared by both platforms (an `appId:` header is set for you)
out = "out"               # default "out", or "out-ios" / "out-android" when the file has both platforms
parallel = 4              # simulators (emulators on Android); default 4
locales = ["de", "ja"]    # default: every language the app ships
base_locale = "de"        # the language your flow is written in (default en)
bundle_id = "com.example.myapp"   # default: read from the app (Android: package, read from the APK)
device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"   # default: 6.9" iPhone
runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"                    # default: newest installed
device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]   # several sizes from one flow: out/<device>/;
                          # `check out` and `export out` handle both, and the App Store takes both in one folder

[android]
devices = ["phone", "tablet"]   # phone 1080x1920 and tablet 1440x2560 (both 9:16, so Play can recommend the
                          # listing); out/<device>/, exported to phoneScreenshots / tenInchScreenshots
```

### Flutter, React Native, .NET MAUI, Unity and translation-platform exports

These frameworks don't keep their translations in a form shotfleet can read inside the built app, so point it at the
source files instead. Add `strings` to either section (globs, relative to the config):

```toml
strings = "lib/l10n/*.arb"                      # Flutter
strings = "src/locales/*/translation.json"      # React Native / Expo with i18next
strings = ["Resources/Strings/*.resx"]          # .NET MAUI
```

Supported: `.arb`, i18next/react-intl `.json` (nested keys, `_one`/`_other` plurals), `.xcstrings`, `.strings`,
`.stringsdict`, Android/Compose `strings.xml`, XLIFF (`.xlf`, `.xliff`), `.resx`, gettext `.po`, `.properties`, and
CSV with one column per language (Unity Localization, spreadsheets). ICU plurals (`{count, plural, one{…} other{…}}`)
and placeholders (`%d`, `%1$@`, `{name}`, `{{name}}`) are understood. The language comes from `@@locale`, the file name
(`app_de.arb`, `Resources.de.resx`) or the folder (`locales/de/`, `values-de/`). `check` takes the same files:
`shotfleet check fastlane/ --strings 'lib/l10n/*.arb'`.

## Extending shotfleet

Nothing here is on by default: a config without these tables behaves exactly as above. Go further when you want to.

**Hooks** run your own commands (`/bin/sh`, in the config's folder, output on stderr) around a run and an export:

```toml
[hooks]
before_run   = "make build-sim"                 # a string, or a list of commands run in order
after_run    = 'curl -sS -X POST -H "Content-type: application/json" "$SLACK_WEBHOOK_URL" --data "{\"text\":\"shotfleet $SHOTFLEET_PLATFORM: $SHOTFLEET_PROBLEMS problem(s)\"}"'
before_export = "git diff --quiet"              # a non-zero exit stops the export
after_export  = 'fastlane deliver --skip_binary_upload --skip_metadata --overwrite_screenshots --screenshots_path "$SHOTFLEET_FASTLANE/screenshots"'
# hook_timeout_s = 1800                         # default 600 per command
```

A failing `before_*` hook stops the command (exit 2); a failing `after_*` hook makes the exit code 1, so CI notices.
Variables: `SHOTFLEET_EVENT`, `_VERSION`, `_CONFIG`, `_PLATFORM`, `_OUT`, `_BUNDLE_ID`; `before_run` and `after_run` also get
`_LOCALES`; `after_run` gets `_EXIT`, `_PROBLEMS`, `_REPORT` (`<out>/check.json`); the export hooks get `_FASTLANE`, `_REPORT`
(and `_EXIT` after the export). `--no-hooks` skips them for a dry run.

**Overrides** replace what shotfleet would tap for one language, which is the fix for a collision warning (`'Next' ->
'İleri' also means 'Advanced'`) and for labels that aren't in your app's strings:

```toml
[overrides.tr]                         # the language as shotfleet names it: tr, pt-BR, zh-Hans...
"Next" = "İleri"                       # literal text
"Advanced" = "re:Gelişmiş.*"           # "re:" = a regular expression
"Search" = "Ara"
```

**Inputs** set the text a flow types, per language. Write `inputText: ${name}` in the flow and give the values in the config:

```toml
[inputs]                               # typed in every language that has no value of its own
name = "Alex"
[inputs.ja]                            # the language as shotfleet names it; pt covers pt-BR too
name = "田中"
```

The value goes into that language's flow as a Maestro `env:` entry. This works on iOS; Android runs type the
`[inputs]` defaults only, because Maestro hands any flow to any emulator. The values are tested as flow text, not yet
run on a device, so check the first screenshots in a script like Japanese or Arabic.

**Plugins**: `shotfleet foo` runs `shotfleet-foo` from your PATH (like `git` and `gh`), when `foo` isn't a built-in command.

**Anything else**: `run`, `check` and `export` take `--json` and use stable exit codes (0 ok, 1 problems, 2 setup error), so
they script like any other tool; `SHOTFLEET_OCR` / `--ocr-command` swaps the text reader; `strings = "glob"` swaps the
translation source.

## Tips

- **Dialogs that appear late** (disclaimers, consent screens): dismiss them in a loop until your first real screen is visible, not with a fixed wait:
  ```yaml
  - repeat:
      while:
        notVisible: "Welcome"
      times: 15
      commands:
        - tapOn: { text: "Accept", optional: true }
  ```
- **Longer languages push buttons off-screen:** add `scrollUntilVisible` before tapping them.
- **Permission prompts** ("Allow While Using App", "Don’t Allow") are drawn by iOS and Android in the device language, which stays English even while your app runs in German. Write those taps in English; shotfleet keeps the English text matchable. Better still, skip the prompts: on iOS start the flow with
  ```yaml
  - launchApp:
      permissions:
        all: allow
  ```
  (shotfleet adds its language arguments to your options). On Android shotfleet installs with every permission granted.
- **Fresh state:** each language starts from a clean install. On iOS that's `clearState`; on Android shotfleet clears the app data itself, because `clearState` would also erase the app language.

## Limits

- The installed program brings its own Python. Running from source needs Python 3.11+ (macOS's own `python3` is 3.9; `brew install python`).
- Strings are read from the build: `.strings`, `.stringsdict` and String Catalogs on iOS (including those in frameworks, Swift packages and a Watch app), `strings.xml` and `<plurals>` on Android, and Compose Multiplatform resources on both. Other frameworks read source files (see Config). Labels with numbers ("Round 2 of 12") are matched and translated with the same numbers, in every plural form.
- Flutter and React Native work from your translation files (tested on real translation files; not yet run on a real Flutter or React Native app).
- If you pass `init`, `run` or `check` a Flutter, React Native, .NET MAUI or Unity build, shotfleet tells you what to add: a `hint:` on stderr with the `strings =` line for your translation files, and a warning for a Flutter debug build (DEBUG banner) or a React Native Debug build (Metro dev server). It detects these builds from file names in the bundle, so it may miss some versions, and it never stops a run.
- Text recognition is macOS's. It reads 33 languages, including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. For scripts it can't read (Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts), `check` still catches screens in another language, copies and missing screens, and says which screens it couldn't read.
- If macOS text recognition stops answering (its `ANECompilerService` occasionally gets stuck until a restart), `check` switches to Tesseract automatically when it's installed (`brew install tesseract tesseract-lang`), and otherwise tells you to restart. iOS runs aren't affected: they read the app's own text.
- For full verification of those scripts, give `check` an OCR that reads them, e.g. Tesseract (`brew install tesseract tesseract-lang`, about 700 MB): `--ocr-command "tesseract {image} stdout -l {tesseract}"` (or set `SHOTFLEET_OCR`). It's used only for languages macOS can't read; `{lang}` is the language code if your tool wants that instead.
- `check` without `--app` relies on language detection, which can't judge short screens; pass `--app` for the full check.

- macOS on Apple silicon only (the installer refuses Intel Macs). Needs Xcode for iOS, the Android SDK for Android, Maestro 2.x and Java 17+ (Maestro needs it).
- Android needs API 33+ emulators for per-app languages. shotfleet finds the SDK in `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `~/Library/Android/sdk`, Homebrew's `android-commandlinetools`, or next to an `adb` on your PATH, and uses any installed arm64 `google_apis` or `google_apis_playstore` image of API 33 or newer (or the `system_image` from the config). `shotfleet doctor` prints the `sdkmanager` commands for whatever is missing.
- `launchApp` options must be written as a block (as above), not inline `{ ... }`.
- Text you type isn't translated by itself: it stays the same in every language unless you set `[inputs]` (iOS only, see above).
