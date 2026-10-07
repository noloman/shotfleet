---
name: shotfleet
description: Install, set up, run, check and troubleshoot shotfleet, a macOS command-line tool that captures localized App Store and Google Play screenshots from one English Maestro flow and verifies them. Use when the user mentions shotfleet, shotfleet.toml or flow.yaml for many languages, store screenshots in several languages, fastlane screenshots that may be in the wrong language, copied, missing or untranslated screenshots, "check my screenshots", or when a shotfleet doctor, init, run, check or export command fails or prints a problem. Covers iOS and Android; Flutter and React Native work from translation files.
---

# shotfleet

shotfleet rewrites one English Maestro flow into every language an app ships, runs all languages in parallel on
simulators or emulators, and checks every screenshot against the app's own strings (text recognition on macOS,
or the app's own text for iOS runs). It also checks screenshots you already have (fastlane snapshot, screengrab, a plain folder per language), with no simulator.
Needs an Apple silicon Mac, Maestro (tested with 2.0.10 and 2.11.0) and Java 17+; iOS needs Xcode, Android needs the Android SDK. Built for macOS 13 or later on Apple silicon. My full runs, with simulators and emulators, were all on macOS 27. On macOS 14 and 15 I ran the installer, doctor and check for version 0.1.1, and on macOS 26.2 in a virtual machine for 0.1.2. Other macOS versions are not tested yet.

Start with `shotfleet --version`. If it is missing, the installer from https://shotfleet.com/docs is
`curl -fsSL https://shotfleet.com/install.sh | sh`: ask the user before running a remote script.

Update: run the install line again. It replaces the program and keeps your licence (the key is stored outside the program folder). `shotfleet doctor` tells you when a newer version is out. A year of updates is included: every version released within a year of your purchase.

## Which path?

1. **The user has screenshots (fastlane or any folder) and wants to know if they are right** -> [Check](#check). No simulators, no licence.
2. **The user wants to capture screenshots in many languages** -> [Capture](#capture): `doctor`, `init`, write the flow, `run` one language, then all.
3. **The app is Flutter, React Native, .NET MAUI or Unity** -> same paths, plus `strings = "<glob>"` in the config or `--strings '<glob>'` on `check`, pointing at the translation files. Details in [references/config.md](references/config.md). Run `shotfleet init` in the project folder first: it recognises these projects, finds the build where the framework puts it, writes the `strings` line itself and prints the framework's own build command when there is no build yet (EAS `.tar.gz` builds are unpacked).
4. **The user wants it in CI** -> use the `shotfleet-ci` skill, or [references/ci.md](references/ci.md).
5. **There is a check report to explain** -> use the `shotfleet-review` skill.
6. **A command printed an error or a hint** -> [references/troubleshooting.md](references/troubleshooting.md) (grep the message).
7. **Licence, activation, free tier** -> [references/licence.md](references/licence.md).

## Check

```bash
shotfleet check <fastlane-dir> --app <MyApp.app | app.apk> --json --report <report-dir> > check.json
```

- `<fastlane-dir>` is the fastlane folder or its `screenshots/` folder (deliver: `screenshots/<locale>/`), or `metadata/android/<locale>/images/phoneScreenshots/` (supply), or plain `<locale>/` folders (with no `--app` and no build found, the image sizes pick the store; a mix of App Store and other sizes is judged against both stores and says so in a note). A flat folder of one language's PNGs (no `<locale>/` level) needs `--locale <code>`, e.g. `shotfleet check shots/ --locale en`; shotfleet never guesses the language. A folder with both stores is checked one store per run: `--app` (an `.app` or an `.apk`) picks which.
- `--app` is a simulator build (`Debug-iphonesimulator/*.app`, never an `.ipa` or archive) or a debug `.apk`. Without it only language detection runs and short screens can't be judged.
- Translation files instead of a build: `--strings 'lib/l10n/*.arb'` (repeatable).
- Put `--report` outside the fastlane folder (default is `./shotfleet-check` in the current directory). shotfleet never edits the checked folder.
- `--content [shotfleet.toml]` (after the folder) also requires the `[expect.<screenshot>]` texts from the config to be on screen (`any`, `all`, `not`, per language); free, no licence, and `run` does it by itself. Missing texts are `problems`; texts OCR can't read are `notes` ("could not verify"). See [references/config.md](references/config.md).
- First text recognition after a restart can take 30 s to minutes and prints nothing. It is not a hang: wait.
- Scripts macOS can't read (Greek, Hebrew, most Indic): `check` says which screens it only checked weakly; for full checks add `--ocr-command "tesseract {image} stdout -l {tesseract}"` (needs `brew install tesseract tesseract-lang`).

## Capture

```bash
shotfleet doctor                                   # fix every MISSING line first
shotfleet doctor --fix                             # or let it download Maestro, Java and the Android tools (asks once; never sudo)
shotfleet init <MyApp.app> <app-debug.apk> --dir <dir>   # either build or both; writes shotfleet.toml and flow.yaml
shotfleet run <dir>/shotfleet.toml --locales en    # ONE language first: boots simulators, takes minutes
shotfleet run <dir>/shotfleet.toml --json          # all languages
shotfleet export <dir>/out --fastlane <fastlane-dir>   # only languages that passed; needs a licence
```

1. The build must be a **Debug simulator build** for iOS (`xcodebuild -scheme <Scheme> -sdk iphonesimulator -configuration Debug build`) or an APK (`./gradlew assembleDebug`, API 33+ emulators).
2. Edit `flow.yaml` (English Maestro steps, one `takeScreenshot:` per store image): see [references/flow-writing.md](references/flow-writing.md).
3. `run` prints `warning <lang>: ... also means ...` for translation collisions and `selectors not found in the app's strings` for labels it could not translate. Fix those before the full run (anchor with `below:`/`above:`, or `[overrides.<lang>]`).
4. `export` writes into the user's fastlane folder (it replaces same-size PNGs in the listing folders). Run it only when asked, after `check` is clean.
5. Free tier: `run` captures 2 languages without a licence and `export` refuses. Never ask the user to paste the key into chat. `activate` comes after the first run, when the user wants every language ([references/licence.md](references/licence.md)).
6. Xcode must be the selected one (`xcode-select -p` shows which); the Android block of `doctor` can be ignored by iOS-only apps; the first `doctor` can take a minute while macOS prepares text recognition.

## Exit codes (run, check, export, doctor)

| Code | Meaning | What to do |
|---|---|---|
| 0 | all good | report what was checked |
| 1 | problems found (or a language failed, or an `after_*` hook failed) | read `problems`, see the `shotfleet-review` skill |
| 2 | setup error: stderr says `shotfleet: <what to fix>` | fix it, see troubleshooting.md |
| 130 | interrupted | rerun |

`doctor` exits 2 when neither iOS nor Android is ready and 0 when at least one is; `doctor --fix` exits 1 when a step it ran failed, and 0 after all its steps worked.

## Reading `--json`

`stdout` is only JSON; progress goes to stderr. Read `exit` first.

- `check` and `run`: `{"exit", "screenshots": [{"file": "<locale>/<name>.png", "src", "sha", "lang", "chars", "evidence"}], "problems": ["<locale>/<file>: <what>", ...], "notes": [...], "unverified": ["<locale>/<file>", ...], "coverage": {"store", "columns", "locales", "summary"}}`. `problems` fail the check; `notes` are worth knowing and do not. `unverified` lists screenshots nobody read because macOS text recognition was busy (it can prepare for about 40 minutes) and no Tesseract was installed: tell the user to run `check` again later or `brew install tesseract`; no restart is needed. They exit 0 unless `check --strict` (then 1). `lang` is the language the screen shows (null when macOS can't read that script). `evidence` is `"hierarchy"` when the screen's text came from the app's own UI tree (saved next to the screenshot as `<name>.texts.json`), `"ocr"` when it was read from pixels. `src` is relative to the report folder. `coverage` (App Store or Google Play, known stores only) is a table of language by device class with cells `ok`, `missing`, `too many`, `wrong size` or `optional`, and `summary` says in plain words what is short; it is information, it changes no exit code. `check --compare <earlier folder>` adds a `compare` object (new, removed and changed screens per language), also report only.
- `export`: `{"exit", "exported": ["<listing folder>", ...], "skipped": ["<locale>", ...]}`. A skipped language failed a check.
- With `exit` 2 the JSON has only `exit`.
- With several reports (several `device_types`, both platforms, a folder of device runs, Play phone and tablet sets) `screenshots`, `problems` and `notes` hold all of them, plus `reports`: `[{"report": "<path of check.json>", "problems": [...]}]`. With one report there is no `reports` key.
- Count issues, not lines: one wrong-language locale usually yields a wrong-language line, a copy line and a missing line.

## Tell the user

- What you ran, the exit code, the number of problems, and the path of `index.html` (open it for the grid: a row per language, a column per screen, problems outlined in red).
- For each problem group: which locale to recapture and whether the cause is in the app (untranslated string, button off-screen in a long language) or in the flow.
- What was not covered: `unverified` screenshots, scripts macOS can't read, `check` without `--app`, Android screens on Maestro older than 2.7.0 (read by text recognition only).

## Do not

- Do not say screenshots are correct without running `check` and reading `problems`.
- Do not upload to App Store Connect or Google Play; fastlane does that and the user decides.
- Do not edit, move or delete files in the fastlane folder; only `export`, when asked, writes there.
- Do not put the licence key in a repo, a config file, a command you echo, or chat. Never print `licence.json`.
- Do not claim Flutter or React Native work beyond reading their translation files (run end to end only on wger, a Flutter app, and the obytes template, an Expo app, on iOS and Android, 2026-10-03; say "not yet run" for any other app or bare React Native).
- Do not translate typed text: `inputText` is not rewritten, so demo data stays the same in every language.
- Do not write one flow per language; write one English flow.
- Do not start many simulators yourself or run `run` without asking: it uses the Mac heavily for minutes.

## More

[references/troubleshooting.md](references/troubleshooting.md), [references/flow-writing.md](references/flow-writing.md),
[references/config.md](references/config.md), [references/ci.md](references/ci.md), [references/licence.md](references/licence.md).
The tool also ships an MCP server (`shotfleet mcp`) with `check`, `run` and `doctor`; its `check` writes the report into `./shotfleet-check` in the server's working directory (never into the folder it
checks) unless you pass its `report` argument. Its replies are a short summary with the path to `check.json`; pass `full: true` for the whole report. Over MCP, no command written in the config runs unless you pass `hooks: true`: `run` skips `[hooks]` and refuses a config with a `[capture]` build, `[ios] simctl` or `[android] shell`; `check` takes no `ocr_command` (that is the CLI's `--ocr-command`).
