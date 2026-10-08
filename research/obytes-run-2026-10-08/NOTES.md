# Obytes starter showcase, 2026-10-08: final build from commit fd9b358, iPhone and Android

shotfleet 0.1.6 on obytes/react-native-template-obytes, built from the unmodified upstream commit fd9b358 ("v9.0.0 plus ten later commits"). Both platforms ran there. A first try on the tag v9.0.0 is kept as history (NOTES-tag-v9.0.0.md). This is a deliberately thin showcase: two languages, one translated screen. Numbers below come from the run.json and check.json files under fd9b358/ (and ios-*/ for the tag build). The page stays on a branch until Manu has seen it and the maintainers have had their say.

## How it went, in order
1. Tag build (v9.0.0, commit a8ded50, tag object f6309e9). iPhone: worked, 4 runs of which 3 succeeded (one dry attempt failed at the Theme sheet, one flow fix). Android: the Release APK never got past its splash screen on a fresh install in shotfleet's emulator, so there are no Android frames from the tag. Details below and in NOTES-tag-v9.0.0.md.
2. Upstream fixed the splash handling in PR #531 ("fix: hide splash screen from root layout", merged 2026-06-02). It is part of commit fd9b358ed11913d2a49fd9ffa6582fe03ba130e7 (`git describe`: v9.0.0-10-gfd9b358, package.json still says 9.0.0).
3. I rebuilt both platforms from that commit without editing anything and re-ran both. Android worked on the first try. The iPhone frames came out byte-identical to the tag build's.

## What ran (final build)
- App: obytes/react-native-template-obytes, an open-source Expo / React Native starter (Expo SDK 54, RN 0.81.5), MIT licence, copyright 2021 Obytes. Commit fd9b358, built unmodified on 2026-10-08. `git diff --stat v9.0.0 fd9b358` is 20 files (fd9b358/logs/diff-name-status.txt): 2 app-code files (src/app/_layout.tsx calls SplashScreen.hide() from the root layout; src/app/(app)/_layout.tsx loses the 1 s hideAsync timer), 4 app images (icon, adaptive-icon, splash-icon, favicon, recompressed), 14 CI, docs and cli files that are not in the app. Dependencies unchanged. See fd9b358/ARTIFACTS-fd9b358.txt for checksums and build commands.
- iPhone: Release simulator build (xcodebuild, arm64, JS bundle embedded, no Metro, no dev menu). The iOS executable is identical to the tag build's (same sha256); only the JS bundle and the four images differ. Bundle id com.obytes.development, display name ObytesApp, version 9.0.0.
- Android: Release APK, arm64-v8a, signed with the template's debug keystore, package com.obytes.development, version 9.0.0.
- What the template really is: it ships only en and ar, and only the Settings screen is translated (22 of 25 strings). The tab bar (Feed, Style, Settings), onboarding, login and the Style demo are hard-coded English and stay English in the Arabic run. The flow walks through onboarding and the local demo login uncaptured. The login makes no server call (LoginScreen.onSubmit stores a fixed fake token and pushes "/"). The typed values are demo values ("Alex", "alex@example.com", a digits-only password). After login the Feed tab does one background GET to the template's own mock API (dummyjson.com/posts); the Feed is never captured. The flow never picks a language inside the app and never taps Logout or any link.
- Tool: shotfleet 0.1.6 released binary for every run, Maestro 2.0.10.
- Devices: iPhone 17 Pro Max simulator, iOS 26.4 (runtime pinned), shotfleet's own pool simulator (named shotfleet-1 in the run), `simulators` is 1 in every run.json. Android: shotfleet's own AVD shotfleet_android (arm64, API 36, 1080x1920), `emulators` is 1 in every run.json. Neither run touched any other simulator or emulator (lists before and after are in fd9b358/logs).
- Config: `strings = "src/src/translations/*.json"` on both. shotfleet read the template's en.json and ar.json. "selectors not found in the app's strings" lists only the two onboarding texts (the app's own hard-coded English). Flows: fd9b358/flows/flow.ios.hd.yaml is byte-identical to the final flow of the tag job (flow.yaml in this folder). flow.android.hd.yaml is the Android flow written for the tag attempt, a copy of the iPhone flow with text waits and a text tap for the sheets (on Android the sheet options are reachable by text). No flow fix was needed on the final build (0 of 3 used).

## Runs on fd9b358 (numbers from run.json)
| Run | Folder | Locales | wall_seconds | seconds per locale | retries | screenshots | rc |
|---|---|---|---|---|---|---|---|
| iPhone dry | fd9b358/ios-hd-dry | en | 154 | 138 | 0 | 6/6 | 0 |
| iPhone run1 (counted) | fd9b358/ios-hd-run1 | en, ar | 143 | 65, 62 | 0 | 6+6 | 0 |
| iPhone run2 (repeat, ar first) | fd9b358/ios-hd-run2 | ar, en | 149 | 60, 76 | 0 | 6+6 | 0 |
| Android dry | fd9b358/android-hd-dry | en | 85 | 68 | 0 | 6/6 | 0 |
| Android run1 (counted) | fd9b358/android-hd-run1 | en, ar | 180 | 77, 64 | 0 | 6+6 | 0 |
| Android run2 (repeat, ar first) | fd9b358/android-hd-run2 | ar, en | 164 | 67, 63 | 0 | 6+6 | 0 |

iPhone run.json has `attempts: 1` per locale; Android run.json has no attempts field when nothing was retried (the logs have no retry line). The iPhone dry run was slower than on the tag (154 s against 71 s) because the Mac was busier. Process wall time including boot, cleanup and check (progress.log): iPhone 200, 281, 201 s; Android 180, 521, 201 s. Android run1's extra minutes were shotfleet's built-in check waiting for macOS text recognition to warm up ("another shotfleet is preparing macOS text recognition"); the capture itself was 180 s. `untranslated_selectors` in every locale: "Let's Get Started", "Obytes Starter" (the app's own English).

## check (run after the lock was released, no device)
`shotfleet check out-X --strings 'src/src/translations/*.json' --report check-X` on all six runs: 0 problems, notes [], unverified []. Files per run folder: check.json (this command), check-in-run.json (the one shotfleet writes inside the run), index.html.
- iPhone: evidence "hierarchy" for frames 01, 02, 04, 05 in both languages and "ocr" (macOS text recognition on the picture) for the two sheet frames 03 and 06, because the sheets are not in the iOS hierarchy. Same as on the tag build.
- Android: evidence "ocr" for every one of the 12 frames in run1 and in run2. Maestro 2.0.10 saves no per-step hierarchy on Android (the run prints that it needs 2.7.0), so text is read from the pixels, which is weaker, especially for Arabic. I looked at every Android frame myself.
- The check reads the screens; it does not prove that every tap hit the right button.

## Frames reviewed
Public-safe: yes for all (no real name or account, typed demo values never shown, no Feed, status bar set by shotfleet: 9:41, full signal, wifi, battery). "ObytesApp" is the plain App Name value in the About row. Obytes logo: in no frame (it only appears on the splash and the app icon, never captured; the first real frame of each flow is Settings).

### iPhone (looked at every frame, or byte-identical to one I looked at)
All frames of the fd9b358 runs are byte-identical (md5 and cmp) to the frames of the tag build (ios-run1/ios-run2), so the two iPhone images already chosen from the tag build are valid for fd9b358. Frames 02 and 05 are byte-identical to 01 and 04 in every run (the Settings list fits the 6.9" screen, nothing scrolls), so there are 4 distinct frames per language. Run2 is byte-identical to run1 and the dry en frames equal run1's. First eight hex digits of the md5: en 01/02 adf008c8, 03 c82438c5, 04/05 2241a410, 06 1fbc7e55; ar 01/02 3945b5f0, 03 15f2627d, 04/05 d7689516, 06 3a7adce0.

| Frame (run1) | Lang | Screen | Shows | "ObytesApp" | Logo | Wrong? |
|---|---|---|---|---|---|---|
| en/01_settings.png | en | Settings, light | General (Language, Theme "System"), About (App Name ObytesApp, Version 9.0.0), Support Us, Links, Logout, tab bar | yes | no | no. Language row has no value (app quirk: fresh install) |
| en/02_settings_more.png | en | = 01 | identical file | yes | no | duplicate, nothing scrolls |
| en/03_theme_sheet.png | en | Theme sheet over dimmed list | Dark, Light, System with emoji | yes (dimmed) | no | no |
| en/04_settings_dark.png | en | Settings, dark | Theme value "Dark", dark theme, tab bar | yes | no | no |
| en/05_settings_dark_more.png | en | = 04 | identical file | yes | no | duplicate |
| en/06_language_sheet.png | en | Language sheet, dark list dimmed | English, Arabic, no check mark | yes (dimmed) | no | no (no selection shown: app quirk) |
| ar/01_settings.png | ar | Settings, light, right-to-left | labels Arabic, right-aligned, chevrons on the left; Theme value "System" stays English; tab bar English and not mirrored | yes | no | no |
| ar/02_settings_more.png | ar | = 01 | identical file | yes | no | duplicate |
| ar/03_theme_sheet.png | ar | Theme sheet | Arabic dark / light options and "System" with emoji; option text left-aligned (the sheet is not RTL-aware) | yes (dimmed) | no | no |
| ar/04_settings_dark.png | ar | Settings, dark | Theme value in Arabic, dark | yes | no | no |
| ar/05_settings_dark_more.png | ar | = 04 | identical file | yes | no | duplicate |
| ar/06_language_sheet.png | ar | Language sheet | Arabic labels, left-aligned | yes (dimmed) | no | no |

### Android (all 30 raw frames looked at: 6 dry, 12 run1, 12 run2)
Dry and run1 frames viewed one by one; run2 viewed as a contact sheet per language plus a pixel diff against run1: all 12 run2 frames equal the run1 frame within 1 grey level in every pixel (0 pixels differ by more than 8). Byte-identical (md5): run1 en 04, 05, 06 = dry en 04, 05, 06. Everything else differs in PNG bytes but not visibly. Unlike on iPhone, 02 and 05 are real scrolled frames, so there are 6 distinct frames per language.

| Frame (fd9b358 android run1, raw/<lang>/) | Screen | What it shows | Anything wrong |
|---|---|---|---|
| en/01_settings.png | Settings, light, top | Settings title; General (Language, Theme "System" + gear emoji); About (App Name ObytesApp, Version 9.0.0); Support Us; Links (Privacy Policy, Terms of Service cut at the tab bar); tab bar Feed, Style, Settings | no. Language row has no value (app quirk) |
| en/02_settings_more.png | Settings, light, scrolled to Logout | About, Support Us, Links, Logout | the scrolled list runs under the transparent status bar: the Theme row is cut off and overlaps the clock and wifi/battery icons (the app is edge-to-edge). Cosmetic; frame not used |
| en/03_theme_sheet.png | Theme sheet over dimmed list | Dark, Light, System with emoji, left aligned | no |
| en/04_settings_dark.png | Settings, dark, top | same list in dark; Theme value "Dark" + moon | no |
| en/05_settings_dark_more.png | dark, scrolled | same as 02 in dark | same status-bar overlap; not used |
| en/06_language_sheet.png | Language sheet over dimmed dark list | English, Arabic; nothing picked | no |
| ar/01_settings.png | Settings, light, right-to-left | all labels Arabic; chevrons on the left; Theme value "System" stays English (the app's own string); tab bar order mirrored (Settings, Style, Feed) with English labels | no |
| ar/02_settings_more.png | scrolled | adds the GitHub, website and logout rows in Arabic | same status-bar overlap |
| ar/03_theme_sheet.png | Theme sheet | Arabic dark / light options, "System" with emoji, right-aligned (on Android the sheet follows RTL; on iPhone it was left-aligned) | no |
| ar/04_settings_dark.png | dark, top | Theme value in Arabic + moon | no |
| ar/05_settings_dark_more.png | dark, scrolled | | same status-bar overlap |
| ar/06_language_sheet.png | Language sheet | Arabic labels, right-aligned | no |

Android frames are 1080x1920, shorter than the iPhone's, so the list is cut at the Links section in 01 and 04. Arabic difference between the platforms: on Android the tab bar and the sheet options are mirrored; on iPhone the tab bar is not mirrored and the sheet options are left-aligned. "System" stays English in Arabic on both.

### Frames picked for the website
iPhone: en 04_settings_dark and ar 01_settings (2 of the 4 distinct per language; images from the tag build, valid because byte-identical). Android (from fd9b358 android run1): en 01_settings and ar 01_settings (light, top, the clearest proof of the translation; second choice 04_settings_dark). 4 of the 20 distinct frames (8 iPhone, 12 Android).

## What happened on the tag (history)
iPhone on v9.0.0 worked (see NOTES-tag-v9.0.0.md for runs, the one flow fix and the frame table).

Android on v9.0.0: the Release APK built from the tag never got past the system splash screen on a fresh install in shotfleet's emulator.
- Dry run (android-dry-failed/run.json): 81 s wall, 2 attempts (retried), 0/6 screenshots, rc 1. Failure line: `Assertion is false: id: login-button is visible`. The "on screen" list in that line still showed the onboarding texts. shotfleet deleted the failure screenshot with the work folder, so there is no picture of it.
- Observed on my own hand-booted emulator, with the same snapshot flags and settings as shotfleet: `dumpsys activity` showed the splash window displayed and `reportedDrawn=false` in 8 of 8 launches (animation scale 1.0 and 0, with and without `pm clear`, also 3 minutes after launch). `dumpsys input` showed the MainActivity input window as NOT_VISIBLE. A Maestro tap and an `adb input tap` on the button did nothing. `uiautomator dump` shows the onboarding screen laid out behind the splash, which is why text waits passed (logs/dbg-android/u1.xml).
- Cause, my reading of the code at the time: expo-splash-screen holds the first draw until `hide()`. The template called `preventAutoHideAsync()` in the root layout, and the only `hideAsync()` was a 1 s timer in the (app) layout, which the redirect to onboarding unmounts on a fresh install. This is consistent with what happened afterwards, not proven: upstream's fix (PR #531, hide the splash from the root layout) is in fd9b358, and the APK built from that commit gets past the splash in all three runs. I did not test a debug build, a real device or another emulator image, and I did not run the tag APK again.
- Things that did not unstick the tag APK: waiting 3 minutes, HOME and reopen, force-stop and restart, tap by coordinates, `am start`.
- Lock on the tag attempt: 18:07:57 to 18:21:40. At that point the plan was iPhone only; a rebuild with my own patch was ruled out because it would be a modified app. The later rebuild from fd9b358 has no change by me.

## Lock and load
- Tag build iPhone runs: lock 17:48:41 to 18:01:37 (12 min 56 s). Tag Android attempt: 18:07:57 to 18:21:40.
- fd9b358 Android runs: lock 20:14:37 to 20:34:10 (19 min 33 s), load during the runs 4 to 24. fd9b358 iPhone runs: lock 20:36:26 to 20:47:51 (11 min 25 s), load 14 to 95. Limit 60 min; no hard limit triggered. Details in progress.log.

## Findings for shotfleet
1. The Theme sheet options are not in the iOS hierarchy (react-native bottom sheet: only "close modal" and "Bottom Sheet" nodes). Text waits and taps fail there, so the sheet frames 03 and 06 are judged by OCR in `check`. Workaround on iPhone: fixed waits and a percent-position tap. On Android the options are reachable by text.
2. A stuck native splash passes every text wait, because the screen behind it is in the hierarchy. The failure line listed the texts behind the splash as "on screen", which sent me to the flow first. Idea: OCR the failure screenshot, or check `dumpsys activity` for `reportedDrawn=false`.
3. shotfleet deletes the failure screenshot after a failed retry (it removes the work folder). For a deterministic failure the picture would save a manual look.
4. The automatic retry cannot help a deterministic selector failure (157 s wall on iPhone, 81 s on Android).
5. `check --app <React Native apk>` with the 0.1.6 binary printed the hint that React Native keeps its translations inside compiled code, then reported "ar: the app has no ar translation" as a problem (rc 1) and skipped the ar listing. That was a false alarm caused by the missing strings (fd9b358/android-hd-run1/check-app-apk.json, fd9b358/logs/check-android-hd-run1-app.log). Fixed since: 0.1.8's check (commit 00d7346) exits 2 with the --strings hint for any framework APK passed with --app, React Native included; the coordinator had a worker rerun it on this obytes APK with the 0.1.8 code (I did not run it myself). Commit 1c7b085 (Unreleased, for 0.1.9) closes the other paths: the iOS .app, run.json reuse and folder pickup. The false error came from the 0.1.6 binary my runner chains used. `--strings` is what to use for React Native and Expo.
6. The first check after a long idle, or while another shotfleet warms the text recognition, can cost minutes of process wall (Android run1: 521 s process for 180 s of capture). Not a failure.
7. `strings` as a config-relative glob worked, and i18next JSON files are read fine.
8. Android edge-to-edge apps: a scrolled frame shows list content under the status bar (clock and wifi overlap). Not a shotfleet fault; a flow can avoid the scrolled frame.
9. Process notes (mine, not shotfleet): on the tag job the first runner chain took the device lock at 16:49:34 and released it unused at 17:09:34 because my monitor missed the lock event (`cut` buffered the pipe); I fixed the runner so it starts the dry run itself.

## Open items
- Courtesy note, posted by the coordinator: https://github.com/obytes/react-native-template-obytes/discussions/542 (no reply as far as I know). The page stays on this branch until Manu has seen it and the maintainers have had their say. No bug report is planned upstream.
- Manu's yes before anything goes live.
- Attribution block: project name, MIT licence, copyright 2021 Obytes, repo link https://github.com/obytes/react-native-template-obytes, version 9.0.0 plus ten later commits (fd9b358). "Screenshots of the open-source Obytes starter, captured by me with shotfleet from a release build I compiled myself. The project is not affiliated with shotfleet and doesn't endorse it. The images show the app's own interface." No logo.
- Not done: extras flow (flow.extras.draft.yaml, English only) not run, no iPad or tablet, no other language, Feed, Style and onboarding not captured, no debug build or real device.
