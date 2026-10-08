# Obytes starter showcase run, 2026-10-08

shotfleet 0.1.6 on obytes/react-native-template-obytes v9.0.0. iPhone only. This is a deliberately thin showcase: two languages, one translated screen. Numbers below come from the run.json and check.json files in this folder.

## What ran
- App: obytes/react-native-template-obytes, an open-source Expo / React Native starter (Expo SDK 54, RN 0.81.5), MIT licence, copyright 2021 Obytes, tag v9.0.0 = commit a8ded50 (tag object f6309e9). I compiled a Release simulator build on 2026-10-08 (xcodebuild, arm64, JS bundle embedded, no Metro, no dev menu). Bundle id com.obytes.development, display name ObytesApp, version 9.0.0. The template's own tracked `.env` (placeholders, API_URL=https://dummyjson.com/) was used and is not copied here. See ARTIFACTS.txt and CLONE.txt.
- What the template really is: it ships only en and ar, and only the Settings screen is translated (22 of 25 strings). The tab bar (Feed, Style, Settings), onboarding, login and the Style demo are hard-coded English and stay English in the Arabic run. The flow walks through onboarding and the local demo login uncaptured. The login makes no server call (LoginScreen.onSubmit stores a fixed fake token and pushes "/"). The typed values are demo values ("Alex", "alex@example.com", a digits-only password). After login the Feed tab does one background GET to the template's own mock API (dummyjson.com/posts); the Feed is never captured.
- Tool: shotfleet 0.1.6 released binary (`--version` printed `shotfleet 0.1.6`), Maestro 2.0.10.
- Device: 1 simulator, iPhone 17 Pro Max, iOS 26.4 (runtime pinned in shotfleet.toml), `simulators` is 1 in every run.json, shotfleet's own pool simulator. The owner's other simulators were not touched (logs/sims.before.txt vs sims.final.txt identical).
- Config: shotfleet.toml with `strings = "src/src/translations/*.json"`. shotfleet read the template's en.json and ar.json. "selectors not found in the app's strings" lists only the two onboarding texts (the app's own hard-coded English).
- The flow never picks a language inside the app (that restarts the app and stores the choice) and never taps Logout or any link.

## Runs (numbers from run.json)
| Run | Folder | Locales | wall_seconds | seconds per locale | attempts | screenshots | rc |
|---|---|---|---|---|---|---|---|
| dry attempt 1 (failed) | ios-dry-failed-1 | en | 157 | 52 | 2 (retried) | 2/6 | 1 |
| dry (final flow) | ios-dry | en | 71 | 59 | 1 | 6/6 | 0 |
| run1 (counted) | ios-run1 | en, ar | 129 | 58, 58 | 1, 1 | 6+6 | 0 |
| run2 (repeat, ar first) | ios-run2 | ar, en | 149 | 58, 79 | 1, 1 | 6+6 | 0 |

Process wall time including boot and cleanup (logs/last.result): 201 s, 140 s, 161 s, 180 s. No retries in the final runs. 0 retries in the counting runs (run1, run2). Every run printed `captured N/N locales`, then shotfleet's own check: 0 problems.

## The one flow fix (of at most 3)
Dry attempt 1 failed at the Theme sheet. The sheet is on screen, but the iOS accessibility hierarchy contains only "close modal" and "Bottom Sheet", not its options (Dark / Light / System, English / Arabic). `extendedWaitUntil visible "Dark.*"` timed out and a text tap could not work. The failed flow is kept (flow.attempt1-failed.yaml). Fix: replace the text waits with waitForAnimationToEnd plus a 3 s busy-wait, and tap Dark by position (`point: "50%,74%"`, first option row; full-width rows, same in both languages). The Language sheet is only looked at. That worked in all locale captures (dark applied in en and ar). The flow used by run1 and run2 is the same file as the final dry (flow.yaml = flow.used-by-run1.yaml).

## check (run after the lock was released, no device)
`shotfleet check out-ios-X --strings 'src/src/translations/*.json' --report check-ios-X`: dry 6 screenshots, 0 problems; run1 12 screenshots in 2 languages, 0 problems, notes [], unverified []; run2 12 screenshots, 0 problems. Evidence kind: hierarchy for frames 01, 02, 04, 05 in both languages; ocr (macOS text recognition on the picture) for 03 and 06, the two sheet frames, because the sheets are not in the hierarchy. I looked at the sheet frames myself as well. The check reads the screens; it does not prove that every tap hit the right button.

## Frames reviewed (every frame, by looking or by byte-identity to one I looked at)
Public-safe: yes for all (no real name or account, typed demo values never shown, no Feed, status bar set by shotfleet: 09:41, full signal / wifi / battery). "ObytesApp" is the plain App Name value in the About row. Obytes logo: in no frame (it only appears on the splash and the app icon, never captured; the first frame of each flow is Settings).

Frames 02 and 05 are byte-identical to 01 and 04 in every run (the whole Settings list fits the 6.9" screen, nothing scrolls), so there are 4 distinct frames per language, 8 distinct frames in the counting run. All 12 frames of run2 are byte-identical to run1; all en frames of run1 are byte-identical to the dry. First six hex digits of the md5: en 01 adf008c8, 03 c82438c5, 04 2241a410, 06 1fbc7e55; ar 01 3945b5f0, 03 15f2627d, 04 d7689516, 06 3a7adce0.

| Frame (run1; dry and run2 identical) | Lang | Screen | Shows | "ObytesApp" | Logo | Wrong? |
|---|---|---|---|---|---|---|
| ios-run1/raw/en/01_settings.png | en | Settings, light | General (Language, Theme "System"), About (App Name ObytesApp, Version 9.0.0), Support Us, Links, Logout, tab bar | yes | no | no. Language row has no value (app quirk: fresh install, no stored choice) |
| en/02_settings_more.png | en | = 01 | identical file | yes | no | duplicate, nothing scrolls |
| en/03_theme_sheet.png | en | Theme sheet over dimmed list | Dark, Light, System with emoji | yes (dimmed) | no | no |
| en/04_settings_dark.png | en | Settings, dark | Theme value "Dark", dark theme, tab bar | yes | no | no |
| en/05_settings_dark_more.png | en | = 04 | identical file | yes | no | duplicate |
| en/06_language_sheet.png | en | Language sheet, dark list dimmed | English, Arabic, no check mark | yes (dimmed) | no | no (no selection shown: app quirk) |
| ar/01_settings.png | ar | Settings, light, right-to-left | labels Arabic, right-aligned, chevrons on the left; Theme value "System" stays English; tab bar English (Feed, Style, Settings) and not mirrored | yes | no | no |
| ar/02_settings_more.png | ar | = 01 | identical file | yes | no | duplicate |
| ar/03_theme_sheet.png | ar | Theme sheet | Arabic dark / light options and "System" with emoji; option text left-aligned (the sheet is not RTL-aware) | yes (dimmed) | no | no, see findings |
| ar/04_settings_dark.png | ar | Settings, dark | Theme value in Arabic, dark | yes | no | no |
| ar/05_settings_dark_more.png | ar | = 04 | identical file | yes | no | duplicate |
| ar/06_language_sheet.png | ar | Language sheet | Arabic labels, left-aligned | yes (dimmed) | no | no |
Also looked at: ios-dry-failed-1 frames 01 and 02 (= good 01) and the failure screenshot (Theme sheet fine on screen).

Frames picked for the website: en 04_settings_dark and ar 01_settings (2 of the 8 distinct ones). Second choices: en 03, ar 04.

## Android: no frames
I also built the Android Release APK of the same tag and tried it in shotfleet's emulator (arm64, API 36). It never got past its splash screen on a fresh install. Result: 0 counted frames, 0 of 3 planned runs done, no check.
- Dry run (android-dry-failed/run.json): 81 s wall, 2 attempts (retried), 0/6 screenshots, rc 1. Failure line: `Assertion is false: id: login-button is visible` at the step after the onboarding wait. The "on screen" list in that line still showed the onboarding texts. shotfleet deleted the failure screenshot with the work folder, so no picture exists.
- What I observed (evidence level: observation on my own emulator, hand-booted with the same snapshot flags and settings as shotfleet): `dumpsys activity` showed the system splash window displayed and `reportedDrawn=false` in 8 of 8 launches (animation scale 1.0 and 0, with and without `pm clear`, also 3 minutes after launch). `dumpsys input` showed the MainActivity input window as NOT_VISIBLE. A Maestro tap and an `adb input tap` on the button did nothing. `uiautomator dump` shows the onboarding screen laid out behind the splash, which is why text waits passed (logs/dbg-android/u1.xml). Screenshots of the splash exist in the source folder and are not copied here.
- What I did not do: test a debug build, a real device, or any other emulator image.
- Inference (code reading, not tested, not proof): expo-splash-screen holds the first draw until `hide()`. The template calls `preventAutoHideAsync()` in `src/app/_layout.tsx`, and the only `hideAsync()` is in a `useEffect` in `src/app/(app)/_layout.tsx` that starts a 1 s timer. On a fresh install that same layout redirects to `/onboarding`, which unmounts it and clears the timer. If that is right, the splash is never hidden. It may also be my setup. The cause is not established. The iPhone Release build is not affected.
- Things that did not unstick it: waiting 3 minutes, HOME and reopen, force-stop and restart, tap by coordinates, `am start`. A deep link was not tried to a conclusion.
- Lock: taken 18:07:57, released 18:21:40 (13 min 43 s). adb devices, qemu list and AVD list identical before and after.
- Decision (coordinator, option A): publish iPhone only. A rebuild with a patch would be a modified app, so it was not done.

## Lock and load (iPhone runs)
Lock taken 17:48:41 after three quiet checks, released 18:01:37 (held 12 min 56 s, limit 60). Load at release 52, free memory 60%.

## Findings for shotfleet
1. The Theme sheet options are not in the iOS hierarchy (react-native bottom sheet: only "close modal" and "Bottom Sheet" nodes). Text waits and text taps fail there, so frames 03 and 06 are judged by OCR in `check` (evidence "ocr"). Workaround: fixed waits and a percent-position tap. The failure line "on screen: ObytesApp | close modal | Bottom Sheet" helped; a hint like "the screenshot shows more text than the hierarchy: bottom sheet?" would save a dry run.
2. A stuck native splash passes every text wait, because the screen behind it is in the hierarchy. On Android 12+ the Maestro hierarchy contains the views behind the starting window, so `visible` succeeds and a tap goes to nothing. shotfleet's failure line lists the texts behind the splash as "on screen" (from the hierarchy, not from pixels, as far as I can tell), which sent me looking at the flow first. Idea: OCR the failure screenshot, or check `dumpsys activity` for `reportedDrawn=false`, and say "the app's first frame has not been drawn".
3. shotfleet deletes the failure screenshot after a failed retry (it removes the work folder). For a deterministic failure like the Android one, the picture would have saved a manual look. Keeping the last failure screenshot in the failed run folder would help.
4. The automatic retry cannot help a deterministic selector failure (157 s wall on iPhone, 81 s on Android).
5. `strings` as a config-relative glob worked, and i18next JSON files are read fine.
6. Process note (mine, not shotfleet): the first runner chain took the device lock at 16:49:34 and released it unused at 17:09:34 (idle limit, no command was sent), 20 minutes of lock time wasted, because my monitor missed the lock event (`cut` buffered the pipe). I fixed the runner so it starts the dry run itself, and a TERM trap that runs cleanup must also exit.

## Open items
- Courtesy note posted by the coordinator: https://github.com/obytes/react-native-template-obytes/discussions/542 (not read by me; no reply at last check). The page only goes live if the maintainers do not object, and only after Manu's yes.
- Attribution block (PLAN.md section 1): project name, MIT licence, copyright 2021 Obytes, repo link https://github.com/obytes/react-native-template-obytes, version 9.0.0. "Screenshots of the open-source Obytes starter, captured by me with shotfleet from a Release build I compiled myself. The project is not affiliated with shotfleet and doesn't endorse it. The images show the app's own interface." No logo.
- Not done: extras flow (flow.extras.draft.yaml, English only) not run, no iPad, no other language, Feed / Style / onboarding not captured, no Android frames.
