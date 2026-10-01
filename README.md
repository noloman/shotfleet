# shotfleet

Localized App Store and Google Play screenshots from **one English Maestro flow**: every language your app ships, captured in parallel, checked, and ready for fastlane.

```
$ shotfleet run shotfleet.toml
capturing 18 locales on 4 simulators...
ok   ar       4/4 screenshots
ok   de       4/4 screenshots
...
captured 18/18 locales in 870s on 4 simulators
checked 72 screenshots: 0 problem(s)
```

## Why

Localized screenshots often end up as **the English set copied into every language folder**. That happens because the UI script that drives the app taps English buttons ("Next", "Settings"), so it can't run in German or Japanese without a separate copy per language.

shotfleet reads the translations **compiled into your app** and rewrites the script for each language. "Next" becomes "Weiter", "次へ" or "İleri". Then it runs every language at once and checks the result.

## What it checks

After capture, every screenshot is read with macOS's built-in text recognition and compared against your app's own strings:

- **Wrong language:** the German folder actually shows English or Japanese strings.
- **Copies:** the same image in two languages.
- **Missing:** a language that didn't produce every screenshot.
- **Translation collisions, before anything runs:** for example, `tr: 'Next' -> 'İleri' also means 'Advanced'`. A tap could hit the wrong button there, so you anchor that step with `below:`.

It also finds real localization bugs. On CrossfitTracker it found an onboarding page whose Next button was unreachable on small phones in Japanese, Korean, Chinese and Arabic.

## Quickstart (about 10 minutes)

```bash
ln -s "$PWD/shotfleet.py" /opt/homebrew/bin/shotfleet   # from this folder; Python 3.11+, no dependencies
shotfleet doctor                                   # checks Maestro, Xcode, Android SDK
shotfleet init path/to/MyApp.app   ios/            # simulator build (Debug-iphonesimulator)
shotfleet init path/to/app-debug.apk android/      # or an APK
```

1. Edit the generated `flow.yaml`. It's a normal [Maestro](https://maestro.mobile.dev) flow written in English. Navigate by the text users see and add a `takeScreenshot:` for each store image.
2. Try one language: `shotfleet run ios/shotfleet.toml --locales en`.
3. Run them all: `shotfleet run ios/shotfleet.toml`.
4. Review `out/index.html`. It's a grid with a row per language and a column per screen, and problems are outlined in red.
5. Export to fastlane: `shotfleet export ios/out --fastlane fastlane/`. That writes `deliver`'s `screenshots/<locale>/` or `supply`'s `metadata/android/<locale>/images/phoneScreenshots/`. Languages that failed a check are skipped, so a bad screenshot never reaches a listing.

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

[android]                 # in its own file
apk = "path/to/app-debug.apk"
package = "com.example.myapp"
flow = "flow.yaml"
parallel = 4            # emulators
out = "out"
```

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
- **Fresh state:** each language starts from a clean install. On iOS that's `clearState`; on Android shotfleet clears the app data itself, because `clearState` would also erase the app language.

## Limits

- Native apps only. Strings come from `.strings` (including String Catalogs, which Xcode compiles to `.strings`) on iOS and `strings.xml` on Android. Flutter, React Native and Compose Multiplatform resources on iOS aren't read yet.

- macOS only. Needs Xcode for iOS, the Android SDK for Android, and Maestro 2.x.
- Android needs API 33+ emulators for per-app languages.
- On iOS, `launchApp` with options isn't supported yet; use a bare `- launchApp`.
- Text you type into fields isn't translated, so demo data stays the same in every language.
