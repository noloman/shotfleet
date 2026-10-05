# Paste-in block for AGENTS.md, CLAUDE.md or .cursorrules

Copy everything between the lines into the project's agent instructions file (`AGENTS.md` for Codex and others,
`CLAUDE.md` for Claude Code, `.cursorrules` or `.cursor/rules/shotfleet.mdc` for Cursor, `GEMINI.md` for Gemini CLI).

---

## shotfleet (localized store screenshots)

shotfleet captures App Store and Google Play screenshots in every language the app ships from one English Maestro
flow, and checks every screenshot against the app's own strings. It also checks screenshots you already have (fastlane, screengrab, by hand).
Needs an Apple silicon Mac, Maestro 2.x and Java 17+; Xcode for iOS, the Android SDK for Android.

Commands:

- `shotfleet doctor`: checks Maestro, Java, Xcode and the Android SDK and says how to fix what is missing.
- `shotfleet init <MyApp.app> <app-debug.apk> --dir <dir>`: writes `shotfleet.toml` and `flow.yaml` (either build, or both).
- `shotfleet run <dir>/shotfleet.toml --locales en`: captures one language first; without `--locales`, all of them. Boots simulators and takes minutes: ask first.
- `shotfleet check <fastlane-dir> --app <MyApp.app | app.apk> --json --report <report-dir>`: verifies screenshots, free, no simulators. Use `--strings '<glob>'` instead of `--app` for Flutter or React Native translation files.
- `shotfleet export <out> --fastlane <fastlane-dir>`: copies the languages that passed into fastlane's folders (needs a licence). Only when asked.
- `shotfleet activate <key>`: the user runs this themselves with the key from their Gumroad receipt email.

Exit codes for `run`, `check`, `export`: 0 all good, 1 problems found, 2 setup error (stderr says what to fix), 130
interrupted. `--json` prints JSON to stdout (`exit`, `screenshots`, `problems`, `notes`; `export`: `exit`, `exported`,
`skipped`) and progress to stderr. The HTML grid is `<report-dir>/index.html`.

Rules:

1. Never say screenshots are correct without running `shotfleet check` and reading its `problems`.
2. Write one English flow (`flow.yaml`): tap by the text users see, `takeScreenshot: 01_name` per store image. Never one flow per language. Typed text (`inputText`) is not translated.
3. Never edit, move or delete files in the fastlane folder, and never upload to App Store Connect or Google Play. Only `shotfleet export`, when the user asks, writes there.
4. Never put the licence key in the repo, a config file, a log or chat. Do not read `~/Library/Application Support/shotfleet/licence.json`.
5. iOS needs a Debug simulator build (not an `.ipa` or archive); Android needs a debug APK and API 33+ emulators.
6. Do not claim Flutter or React Native work beyond reading their translation files (`strings = "<glob>"`); it was run end to end only on wger (Flutter) and the obytes template (Expo), on iOS and Android, 2026-10-03; say "not yet run" for any other app or bare React Native.
7. Problems: count issues, not lines; say which languages to recapture and whether the cause is in the app (untranslated string, button off-screen in a long language) or in the flow.
8. Details: the shotfleet skill (`skill/shotfleet/`) and its `references/` folder, or the README.

---
