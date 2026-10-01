---
name: shotfleet
description: Capture and check localized App Store / Google Play screenshots with shotfleet. Use when the user wants store screenshots in several languages, wants to verify existing fastlane screenshots are in the right language, or asks whether screenshots are missing, duplicated or untranslated.
---

# shotfleet

shotfleet runs one English Maestro flow in every language an iOS or Android app ships, and checks each
screenshot against the app's own strings using macOS text recognition. Requires macOS, Python 3.11+, Maestro.

## Checking existing screenshots (no simulators needed)

```bash
shotfleet check <fastlane-dir> --app <MyApp.app | app.apk> --json > check.json
```

- `<fastlane-dir>` holds `screenshots/<locale>/` (deliver) or `metadata/android/<locale>/images/phoneScreenshots/` (supply), or plain `<locale>/` folders.
- `--app` is a simulator build (`Debug-iphonesimulator/*.app`) or an APK. Without it, only language detection is used.
- Exit codes: 0 clean, 1 problems, 2 setup error (stderr says what to fix).
- Read `problems` in the JSON. Each one is `<locale>/<file>: <what>`. Report them to the user as-is and open `shotfleet-check/index.html` for the visual grid.
- Never edit or delete files in the fastlane folder; the report goes to `./shotfleet-check`.

## Capturing

```bash
shotfleet doctor                       # fix anything it reports first
shotfleet init <app> <dir>             # writes <dir>/shotfleet.toml and <dir>/flow.yaml
shotfleet run <dir>/shotfleet.toml --locales en   # one language first
shotfleet run <dir>/shotfleet.toml --json         # all languages
shotfleet export <dir>/out --fastlane fastlane/   # only languages that passed
```

Writing the flow: navigate by the English text users see (`tapOn: "Next"`), add `takeScreenshot: 01_name`
per store image. shotfleet translates the selectors. If it warns about a collision
(`tr: 'Next' -> 'İleri' also means 'Advanced'`), anchor that step with `below:`/`above:`. Dismiss dialogs
that appear late with `repeat: while: notVisible:`. Don't write one flow per language.

## Don't

- Don't claim screenshots are correct without running `check` and reading its problems.
- Don't upload to the stores; that is the user's call.
