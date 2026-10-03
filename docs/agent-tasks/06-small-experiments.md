# Run three small experiments: Android UI-tree text, Capacitor language, MAUI sample

**Needs:** your Mac with an emulator and simulators; about 2 hours in total.

## Context

Three open questions that need a device, each small. Read `docs/handoff.md` items 7 and 10, `research/limits-text.md` section 1 and `research/frameworks.md` sections 7 and 12.

## Steps

A. Android on-screen text from the UI tree (the 10-minute marker experiment): on one emulator with Maestro 2.11.0 can the UI hierarchy be read during a sharded run without hanging it (2.0.10's `maestro hierarchy` broke sharded runs)? Follow `research/limits-text.md` section 1b. Result: one text file per screenshot, or "not possible" written down.
B. Capacitor/Ionic on iOS: a throwaway app with two buttons whose labels come from `navigator.language` and from a string table; launch it on a simulator with `-AppleLanguages (de)` and see whether the WKWebView language follows (an Apple forum report says `navigator.language` ignores it since iOS 17.4). 20 minutes.
C. .NET MAUI: `dotnet workload install maui` (large), then the LocalizationDemo sample from `dotnet/maui-samples`; `shotfleet init` and a 2-language run (`research/frameworks.md` section 12). Skip C if the install exceeds 5 GB and say so.

## Passed when

A: a clear yes or no with the evidence. B: whether the language reaches the webview, yes or no. C: 0 untranslated selectors on a 2-language run, or the exact failure.

## Record

`research/limits-text.md` and `research/frameworks.md` (dated sections), `docs/handoff.md` (delete what is answered). Change README or site wording only for what passed.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
