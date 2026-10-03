# Capture a real Flutter, Expo and Compose app end to end

**Needs:** your Mac with Xcode and the Android SDK; Flutter needs about 1.5 GB.

## Context

The README says Flutter and React Native "work from your translation files (tested on real translation files; not yet run on a real Flutter or React Native app)". `shotfleet init` was verified, on Linux with Android builds only, to find the build and write the `strings` line for a Flutter 3.47.6 demo app and an Expo demo app; nothing has been captured on a device. Read `docs/handoff.md` item 3 and `research/frameworks.md` sections 1 to 4 and 12.

## Steps

Apps (shallow clone each; read their READMEs for prerequisites):
1. `wger-project/flutter` (37 languages in `lib/l10n/*.arb`; most screens need a server, so use register/login or onboarding screens). `flutter build ios --simulator --debug` and `flutter build apk --debug`. iOS simulators run debug builds only, so the DEBUG banner appears unless the app hides it.
2. `obytes/react-native-template-obytes` (Expo + i18next, `src/translations/{en,ar}.json`, `.maestro/` flows exist; en + ar is the free tier and includes right-to-left). Release builds: `npx expo run:ios --configuration Release --no-bundler` and `npx expo run:android --variant release --no-bundler`.
3. `JetBrains/kotlinconf-app` (Compose Multiplatform; strings are in the build, no `strings =`): `xcodebuild -workspace app/iosApp/KotlinConf.xcworkspace -scheme KotlinConfAppScheme -sdk iphonesimulator -configuration Debug build` and `./gradlew :app:androidApp:assembleDebug`.
For each app and platform: `shotfleet init` in the project folder with no arguments, a 3-step English flow with `takeScreenshot` after each step, `shotfleet run --locales de,ja` (en,ar for obytes), open `out/index.html`, then `shotfleet check`. Look at the screenshots: are they really in those languages?
Questions only a run answers: does the language reach the app (iOS `-AppleLanguages`, Android `cmd locale set-app-locales`)? does Maestro see the text (Flutter needs `Semantics` labels; React Native `testID` maps to `id:`; on iOS an `accessibilityLabel` replaces visible text, Maestro issue 1409)? untranslated selectors in the run output? Flutter DEBUG banner or React Native red box?

## Passed when

Per app and platform: 0 untranslated selectors, 0 problems from `check`, and a German or Arabic and a Japanese screenshot checked by eye.

## Record

A dated table of what passed and what did not in `research/frameworks.md`; `STATUS.md` row 10 and plan row C1. Change README, `site/public/docs.html`, `skill/` wording and claims C035 and C121 ONLY for what really passed, naming the app. If a framework needs a code change (for example the language not reaching a Flutter app), fix it with a test, or write it up in `docs/handoff.md` if large.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
