# shotfleet

Localized App Store and Google Play screenshots from **one English Maestro flow**: every language your app ships, captured in parallel, checked, and ready for fastlane.

```
$ shotfleet run shotfleet.toml
capturing 18 locales on 4 simulators...
ok   ar       4/4 screenshots
ok   de       4/4 screenshots
...
captured 18/18 locales in 534s on 4 simulators
checked 72 screenshots: 0 problem(s)
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

## Quickstart (about 10 minutes)

```bash
curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh   # signed, notarized; Apple silicon
shotfleet activate <your key>                      # from your purchase email (`check` works without one)
shotfleet doctor                                   # checks Maestro, Xcode, Android SDK
shotfleet init path/to/MyApp.app   ios/            # simulator build (Debug-iphonesimulator)
shotfleet init path/to/app-debug.apk android/      # or an APK
```

1. Edit the generated `flow.yaml`. It's a normal [Maestro](https://maestro.mobile.dev) flow written in English. Navigate by the text users see and add a `takeScreenshot:` for each store image.
2. Try one language: `shotfleet run ios/shotfleet.toml --locales en`.
3. Run them all: `shotfleet run ios/shotfleet.toml`.
4. Review `out/index.html`. It's a grid with a row per language and a column per screen, and problems are outlined in red.
5. Export to fastlane: `shotfleet export ios/out --fastlane fastlane/`. That writes `deliver`'s `screenshots/<locale>/` or `supply`'s `metadata/android/<locale>/images/phoneScreenshots/`. Languages that failed a check are skipped, so a bad screenshot never reaches a listing.

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

`run` and `check` take `--json`: the report goes to stdout as JSON (`exit`, `screenshots`, `problems`) and progress goes to stderr. Exit codes: `0` all good, `1` problems found, `2` setup error (the message says what to fix), `130` interrupted.

Checking needs only a Mac (it uses macOS text recognition), with no simulators, so it fits a pull-request job on GitHub's macOS runners. (This recipe hasn't been run on GitHub yet; the command itself is the one tested above.)

```yaml
# .github/workflows/screenshots.yml
on: pull_request
jobs:
  check-screenshots:
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - run: xcodebuild -scheme MyApp -sdk iphonesimulator -configuration Debug -derivedDataPath build build
      - run: python3 shotfleet.py check fastlane/ --app build/Build/Products/Debug-iphonesimulator/MyApp.app --json > check.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: screenshot-check
          path: |
            check.json
            shotfleet-check/
```

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

```toml
[ios]
app = "path/to/MyApp.app"
bundle_id = "com.example.myapp"
flow = "flow.yaml"
device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"
runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"
parallel = 4            # simulators
out = "out"
# locales = ["de", "ja"]   # default: every language the app ships
# base_locale = "de"        # the language your flow is written in (default en)
# device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]   # several sizes from one flow: out/<device>/;
#                            # `check out` and `export out` handle both, and the App Store takes both in one folder

[android]                 # in its own file
apk = "path/to/app-debug.apk"
package = "com.example.myapp"
flow = "flow.yaml"
parallel = 4            # emulators
out = "out"
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
- Flutter and React Native support (via source files) is tested with sample files, not yet on a real Flutter/RN app.
- Text recognition is macOS's. It reads 33 languages, including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. For scripts it can't read (Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts), `check` still catches screens in another language, copies and missing screens, and says which screens it couldn't read.
- For full verification of those scripts, give `check` an OCR that reads them, e.g. Tesseract (`brew install tesseract tesseract-lang`, about 700 MB): `--ocr-command "tesseract {image} stdout -l {tesseract}"` (or set `SHOTFLEET_OCR`). It's used only for languages macOS can't read; `{lang}` is the language code if your tool wants that instead.
- `check` without `--app` relies on language detection, which can't judge short screens; pass `--app` for the full check.

- macOS only. Needs Xcode for iOS, the Android SDK for Android, and Maestro 2.x.
- Android needs API 33+ emulators for per-app languages.
- `launchApp` options must be written as a block (as above), not inline `{ ... }`.
- Text you type into fields isn't translated, so demo data stays the same in every language.
