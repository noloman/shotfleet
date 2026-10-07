# WOD Tracker showcase runs, iPhone and Android, 2026-10-07

Two jobs of the same day, merged into one record: the iPhone half (runs on the simulator, 18:12 to 19:16) and the Android half (runs on the emulator, 19:20 to 20:34). The text below was written by the two run sessions; the "Findings for shotfleet" section is the list for the shotfleet roadmap. The frames themselves (PNGs) are not in this folder: the 12 that are on the site are the WebP files `site/public/img/showcase/wod_*.webp` (converted with `cwebp -q 80 -resize 360 0`); the source paths are in the table "Frames on the site" below.

- App: WOD Tracker (store name; Manu's own CrossFit-style workout timer and log app), version 1.6.7, commit 0cdad156 of the owner's repo. iOS build 58 (`me.manulorenzo.crossfittracker`); Android versionName 1.6.7-debug, versionCode 77 (`me.manulorenzo.crossfittracker.android.debug`). In store review since 2026-10-07 11:40 CEST, NOT released: the store version at the time of the runs was 1.6.4. Debug builds (a simulator build and a debug APK), not store binaries.
- iOS build: a Debug simulator build (arm64 simulator slice, Xcode 27.0, iphonesimulator27.0 SDK, MinimumOSVersion 18.0), built 2026-10-07 17:56-18:03 from a fresh `git archive 0cdad156` copy (nothing was written in the owner's repo). Display name "WOD Tracker", the bundle folder is called `Crossfit Tracker.app`, executable sha256 1ee74be646a8395fbf395d6520f16215504cedf549535bb88a0f5943d46845ff.
- Android build: debug APK `androidApp-debug.apk`, sha256 7d6199c210bc287b6523e1efdaa150d1f94fcf34e45ace3a6fa37e929c119b52, built 2026-10-07 17:46-17:53 from a fresh `git archive 0cdad156` copy. The launcher label is "CrossFit Tracker (Debug)" (never visible in a frame).
- iOS: the RevenueCat keys are EMPTY in this build (`Secrets.swift` holds the CI placeholders: `revenueCatAPIKey`, `cancelFeedbackURL`, `cancelFeedbackAppKey` are empty strings). RevenueCat is unconfigured, so the iPhone frames show no paywall, no trial card, no offerings. That is simpler for a showcase; do not read the absence of a paywall as a product fact. No data was seeded on iOS (the demo seed is behind a shake gesture, `#if DEBUG`, which Maestro cannot do), so every iPhone frame is an empty-state, built-in screen: Train, the Benchmarks library, a timer setup sheet, the WOD clock.
- Android: seeded DEMO data through the app's debug deep link, no account. The flow opens `crossfittracker://debug`, taps "PRO" (a debug tier override) and "Wipe & Seed" (a year of generated demo lifts and WODs, notes written in the app language, toast "Seeded 1 year of debug data"). No sign-in, no Health Connect, no real device data. The seed is random per run, so kg, volumes and dates differ between runs and languages; a frame is not one person's history. PRO is a debug override: say "debug build with demo data", not "a paid tier".
- Tool: shotfleet 0.1.6 (the released binary, `shotfleet --version` printed `shotfleet 0.1.6`), Maestro 2.0.10. No "free tier:" line was printed in any run log. The page that shows these frames goes live with 0.1.7; the frames were captured with 0.1.6.
- iPhone device: 1 iPhone 17 Pro Max simulator, iOS 26.4 (runtime pinned in `shotfleet.toml`, never 27.0), `parallel = 1`, shotfleet's own pool simulator `shotfleet-iphone-17-pro-max-1`; the simulator list at the start and the end is identical (logs/sims.before.txt, logs/sims.final.txt), so nothing was created or deleted, and only the owner's `iPhone 15 Pro` (not mine) stayed booted as found.
- Android device: ONE private emulator, shotfleet's own AVD `shotfleet_android` (1080x1920, 420 dpi, Android 16 / API 36 google_apis arm64, 4 cores, 3 GB RAM), serial emulator-5702, `parallel = 1`. The AVD list before and after is identical (kuokka_smoke, shotfleet_android, shotfleet_android_tablet); no emulator running before the lock and none after (logs/adb.before.txt, adb.final.txt, qemu.before.txt, qemu.final.txt).
- Load and memory at the start. iPhone: three quiet checks 60 s apart (rc 0 each): 18:12:37 free memory 49 % / load 118 / disk 76 GiB free; 18:13:37 free 53 % / load 53 / 75 GiB; 18:14:38 free 55 % / load 23 / 76 GiB. Lock taken 18:14:38, released 19:16:06 (61 min of the 75-minute limit); at release load 19, free 56 %, 73 GiB free; load stayed between 6 and 84 during the hold (progress.log has every sample). Android: a manual check at 19:20 (free 62 % / load 6), then three passes 60 s apart: 19:21:16 free 62 % / load 4 / 73 GiB free, 19:22:16 free 63 % / load 3 / 73 GiB, 19:23:17 free 62 % / load 2 / 73 GiB. Lock taken 19:23:17, released 20:34:15 (71 min of the 90-minute limit); at release load 3, free 63 %, 72 GiB free; load stayed between 2 and 31 (progress-android.log).
- Languages: the showcase subset hi, tr, zh-Hans, pl, nl, pt on iPhone (exact `.lproj` names of the build; the app ships ar da de en es fr hi it ja ko nb nl pl pt ru sv tr zh-Hans zh-Hant). On Android the APK ships `ar da de en es fr hi it ja ko nb nl pl pt ru sv tr zh-CN zh-TW`, so the codes used are hi, tr, zh-CN, pl, nl, pt (`pt` is the app's one Portuguese resource set; the text is Brazilian Portuguese).
- Flows (one English flow per platform, shotfleet translated the taps). iPhone: `flow.yaml` (final, used by run2 and run3) and `flow.used-by-run1.yaml` (run1; the only difference is how the Benchmarks row is reached): onboarding (disclaimer, 3 x Next, experience level, "I'll explore on my own"), then 4 screens: 01_train, 02_benchmarks, 03_timer_setup, 04_clock. Android: `flow.android.yaml` (final) = the owner's `scripts/aso/shotfleet/android.yaml` at 0cdad156 (used for the Play screenshots on 2026-10-05) with the shot names changed, one shot added (04_train) and one fix (the Turkish `below:` anchor, see Findings); `flow.android.used-by-dry-zhsmoke-run1first.yaml` is the first version (used by android-dry, android-zhsmoke and the failed first try of run1). Android: onboarding (disclaimer, 3 x Next, "I'll explore on my own"), Profile > Kilograms (not shot), debug deep link, PRO, Wipe & Seed, then 01_log, 02_progress, 03_analytics, 04_train, 05_benchmarks, 06_clock (12 Min EMOM, round 2/12).

## Runs that count

iPhone: all rc=0, 4/4 screenshots per language, 1 attempt each, 1 simulator. Android: all rc=0, 6/6 screenshots per language, no retry, 1 emulator. Numbers are from each `run.json` (`wall_seconds` is shotfleet's own wall clock including simulator or emulator boot; per-language seconds are the Maestro time; the Android `run.json` has no attempts field, a retry would show in the console log and as `"retried": true` on the failed locale).

| Run | Platform | Languages | wall_seconds | per language (seconds) | screenshots | retries | `shotfleet check` |
|---|---|---|---|---|---|---|---|
| iphone-dry | iPhone | en | 205 | en 190 | 4 | 0 (attempts 1) | 0 problems, 0 notes, 0 unverified |
| iphone-run1 | iPhone | hi, tr | 366 | hi 169, tr 184 | 8 | 0 (attempts 1, 1) | 0 problems, 0 notes, 0 unverified |
| iphone-run2 | iPhone | zh-Hans, pl | 400 | zh-Hans 174, pl 214 | 8 | 0 (attempts 1, 1) | 0 problems, 0 notes, 0 unverified |
| iphone-run3 | iPhone | nl, pt | 384 | nl 192, pt 179 | 8 | 0 (attempts 1, 1) | 0 problems, 0 notes, 0 unverified |
| android-dry | Android | en | 175 | en 159 | 6 | 0 | 0 problems, 0 notes, 0 unverified |
| android-dry-final | Android | en | 187 | en 169 | 6 | 0 | 0 problems, 0 notes, 0 unverified |
| android-zhsmoke | Android | zh-CN | 194 | zh-CN 175 | 6 | 0 | 0 problems, 0 notes, 0 unverified |
| android-run1 | Android | hi, tr, zh-CN | 553 | hi 175, tr 164, zh-CN 167 | 18 | 0 | 0 problems, 0 notes, 0 unverified |
| android-run2 | Android | pl, nl, pt | 528 | pl 163, nl 160, pt 162 | 18 | 0 | 0 problems, 0 notes, 0 unverified |

The runs that count on the site: iphone-run1, iphone-run2, iphone-run3 (24 screenshots, 6 languages x 4 screens) and android-run1, android-run2 (36 screenshots, 6 languages x 6 screens), 60 in all. The iPhone English dry run and the Android dry, dry-final and zh-CN smoke runs are extra runs and are not counted. `android-run2-sleep-interrupted-2020` is a try of run2 that the Mac's sleep froze (see below); it is not counted either.

`shotfleet check <out>` ran after each run with the lock released (the 0.1.6 binary, normal environment, no Tesseract; `--app` the .app or the APK). iPhone: all 28 frames were verified from the view hierarchy (evidence "hierarchy", none by text recognition). Android: Maestro 2.0.10 saves no view hierarchy (`hierarchy_markers` false in run.json), so `check` read the Android frames by text recognition (macOS Vision): evidence "ocr" for all 54 checked frames of the five runs. That is weaker evidence than the iPhone check's hierarchy. Files: `<run>/run.json`, `check.json` (the report), `check-in-run.json` (the check shotfleet ran inside the run), `logs/check-*.log`. `untranslated_selectors`: only `2/12` (the clock-label pattern of the flow, a number pattern with nothing to translate) in every run. The wall clock per run seen by my scripts (including shutdown): iPhone 241 s (dry), 420 s, 441 s, 441 s; Android dry 260 s, zh-CN smoke 260 s, run1 622 s, run2 561 s, dry-final 220 s.

Console warnings (both platforms) about words that share a translation with another string: iPhone hi `Benchmarks` and `Skip`, tr `Next`, zh-Hans `Benchmarks` and `Workouts`; Android tr `Log` -> `Kaydet` also means Save, tr `Next` -> `İleri` also means Advanced, pl `I Understand` / `Log` / `Select a lift`, zh-CN `Train` -> `训练` also means Work/Workouts. For the Android ones the frames were looked at: the right screens were reached.

## What went wrong before the runs that count (the flows, not the counted frames; logs in `logs/failed-attempts/` and `logs/failed-attempts-android/`)

iPhone:

1. Dry run 1 (en, rc=1, 271 s): the draft waited for the "Benchmarks" row, which is below the fold on Train. Fix: wait for the "Start here" card, scroll to the row.
2. Dry run 2 (en, rc=1, 3/4 frames, 225 s): "12 Min EMOM" (Quick start list) is also below the fold. Fix: scroll to it. Dry run 3 (`logs/run-dry-final-en.log`): 4/4.
3. Run 1 first try (hi, tr, rc=1, 0/2, 352 s): `scrollUntilVisible` with the plain `element: "Benchmarks"` string is NOT translated by shotfleet 0.1.6 (only the `element: {text: ...}` form is); it stayed English. Fix: the object form.
4. Run 1 attempt A (hi, tr, rc=0, 8/8, 360 s): hi `02_benchmarks` was NOT the Benchmarks screen. After the scroll the Hindi row sat behind the floating tab bar and the tap hit the Train tab. A green run with one wrong frame, found only by looking at the frame (`check` said 0 problems for it, because the frame is a valid Train screen). Fix: one extra scroll (this is `flow.used-by-run1.yaml`); run1 was run again and is the run that counts. The frames of attempt A are discarded and are not on the site.
5. Run 2 first try (zh-Hans, pl, rc=1, zh-Hans 1/4, pl 4/4, 357 s): in Chinese "Benchmarks" and the card pill "Benchmark" are the same word (基准), so `scrollUntilVisible` was satisfied by the pill and the later tap found nothing. Fix (final `flow.yaml`): four fixed drags to the end of the list, then a plain tap on the row (at the end of the list the pill has scrolled away). Run 2 and run 3 ran with this flow, run 1 with the previous one (it passed and its frames are right).
6. Process note: after run 1's first failure and after attempt A, I stopped my own chain script (SIGKILL, lock kept, still mine) and the just-started next run's process group to edit the flow while holding the lock, then continued with a second script that adopted the lock; two runs were killed about a minute after they started, at 18:37 and 18:46, and left no output worth keeping (`scripts/chain-iphone2.sh`, `progress.log`). The hold stayed under the 75-minute limit. No simulator was left booted. Run 1 of the iPhone therefore used the earlier flow (`flow.used-by-run1.yaml`).

Frames of the discarded iPhone attempts (3 English frames of dry run 2, 2 of run 1's first try, 5 of run 2's first try, 8 of attempt A) were all looked at: Train or Benchmarks screens, nothing private; not used.

Android:

1. zh-Hans smoke try (rc=2, 21 s, no emulator booted): 0.1.6 refuses `zh-Hans` on Android ("none of those languages are in the app ... write them as listed"); used zh-CN.
2. Run1 first try (hi, tr, zh-CN, rc=1, 474 s): hi 6/6 and zh-CN 6/6, tr 0/6 after one retry. In Turkish the onboarding page "Experience level" has an option "İleri" (Advanced) and a button "İleri" (Next), and the third `tapOn "Next"` hit the Advanced option, so "Pick your first step" never showed. Fix: pin the button with `below: "3+ years of consistent training"` (the same fix the iPhone flow has). Run1 was run again with the fixed flow: 3/3. The hi and zh-CN frames of the failed try were looked at (fine, not used). (The screenshot of the wrong tap, 70 KB, is not copied into this record.)
3. Run2 first try (pl, nl, pt, rc=0, 18/18, but 1619 s wall because of the Mac's 17-minute sleep): repeated, see Findings (g). The interrupted try kept its 18 frames (looked at, fine); they are not used.

No other Android flow change was needed: no scroll-to-text problem (the flow already used the `element: {text: ...}` form), no wrong frame found, no first-launch dialog in any frame.

## Findings for shotfleet

(a) `scrollUntilVisible` with `element: "text"` (the plain string form) is not translated in 0.1.6; only `element: {text: ...}` is. An iPhone run (run 1, first try, hi and tr, 0 of 2 locales) died on it: the string stayed English. Worth a README line, or translating the string form too.

(b) A green run can hold a WRONG frame. The iPhone attempt A exited 0 with 8/8 screenshots, but the Hindi `02_benchmarks` frame showed Train (the Benchmarks row sat behind the tab bar and the tap hit the Train tab), and `check` said 0 problems: it reads pictures, and a Train screen in Hindi is a valid screen; it cannot know which screen the flow meant to reach. That attempt's frames are discarded and are NOT on the site. The only defence was looking at every frame. A flow assertion after each tap (`assertVisible` on text that only the target screen has) would catch it; shotfleet could suggest one.

(c) In Chinese a card pill "基准" had the same text as the Benchmarks row, so a text-scroll stopped early and the tap found nothing. Where texts collide, use fixed drags or ids (the final iPhone flow uses four fixed drags, then a plain tap).

(d) Turkish "İleri" is both "Advanced" and "Next" (Android onboarding): the wrong option was tapped and the tr run failed 0/6. A `below:` anchor fixed it. shotfleet printed the warning for this on iPhone ("'Next' -> 'İleri' also means 'Advanced'") and on Android.

(e) 0.1.6 rejects `zh-Hans` on Android; the code the APK ships is `zh-CN` (refused in 21 s, no emulator booted; logs/failed-attempts-android/run-android-zhsmoke-zh-Hans-rejected.log). Maybe map zh-Hans to zh-CN as `check` already does for store codes.

(f) Maestro 2.0.10 saves no screen hierarchy on Android (`hierarchy_markers` false), so `check` judged the Android frames by text recognition, which is weaker evidence than the iPhone check, which used the view hierarchy. Page text about the Android check must say so.

(g) The Mac slept (Maintenance Sleep, 19:57:01 to 20:14:16, 17 minutes, from `pmset -g log`) during an Android try, freezing the emulator and the run in progress (run2, first try; its wall clock of 1619 s is wrong). Fix used: `caffeinate -i -w <chain pid>` (ends with the chain, changes no setting). shotfleet could hold a caffeinate assertion while a run is in progress.

(h) Process notes (mine, not shotfleet's): the runner killed its own chain script twice while holding the device lock (to edit the flow), and the iPhone run1 therefore used the earlier flow (`flow.used-by-run1.yaml`) while run2 and run3 used the final one; the lock stayed mine and under the limit. On the Android side the lock was taken after the iPhone job had released it, and one old queue line without a DONE of its own was treated as stale because its agent had written DONE lines earlier that day.

## Frames reviewed

Every frame of the runs that count was looked at (28 iPhone frames including the English dry run; 54 Android frames including the dry and smoke runs). Findings: all frames show the right screen in the right language (English for the dry runs); no blank frame; nothing cut off in a way that matters (the Snap a WOD row at the bottom of Android Train and the last list items are cut by the tab bar, as in the app; on the iPhone timer sheet the chip rows scroll sideways and the last chip is cut by the screen edge, normal UI); no account, name, e-mail, Health or location data; no real date; no debug banner or "CrossFit Tracker (Debug)" label on Android; no RevenueCat paywall on iPhone; no Heroes names in view (only Girl workouts at the top of the list); no "CrossFit" word on screen in the iPhone frames (the app calls itself WOD Tracker; the Train frames do not show the app name at all). Status bar: 09:41 and full battery (the clean status bar); the pl, nl and pt frames of Android run2 have no Wi-Fi icon (the interrupted try, same flow, has it). Dates in the Android Log are seed-relative, not a real history. English leftovers are app content, not a failed translation: format names (AMRAP, For Time, EMOM, Tabata), the Benchmarks library's names and movements (Amanda, Muscle-Up, Snatch - 135 lbs...), exercise names (Back Squat, Clean), "Girl", "WOD", and the pt clock label "Round". In Hindi and Turkish the iPhone Benchmarks frames are the weakest for a "translated" claim (the titles are localised, the list below them is English). Profile, Settings, AI Coach and Health were never opened for a frame.

"WEB PICK" = the 12 picked for the website (one per language and platform; the 6 iPhone and the 6 Android picks); "second choice" = the alternative if a pick is rejected. The paths are under `/Users/manu/Developer/shotfleet-rc-build/showcase-wod/` (the frames are not in this folder).

### iPhone (28 frames: 4 English dry run, 24 that count)

| path (under /Users/manu/Developer/shotfleet-rc-build/showcase-wod/) | language | screen | what it shows | public-safe | use |
|---|---|---|---|---|---|
| out-iphone-dry/raw/en/01_train.png | en | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) |  |
| out-iphone-dry/raw/en/02_benchmarks.png | en | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time |  |
| out-iphone-dry/raw/en/03_timer_setup.png | en | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-dry/raw/en/04_clock.png | en | clock | WOD clock, 12 Min EMOM, round 2/12 | yes |  |
| out-iphone-run1/raw/hi/01_train.png | hi | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) |  |
| out-iphone-run1/raw/hi/02_benchmarks.png | hi | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time | second choice |
| out-iphone-run1/raw/hi/03_timer_setup.png | hi | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-run1/raw/hi/04_clock.png | hi | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | WEB PICK |
| out-iphone-run1/raw/tr/01_train.png | tr | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) |  |
| out-iphone-run1/raw/tr/02_benchmarks.png | tr | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time | WEB PICK |
| out-iphone-run1/raw/tr/03_timer_setup.png | tr | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-run1/raw/tr/04_clock.png | tr | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | second choice |
| out-iphone-run2/raw/zh-Hans/01_train.png | zh-Hans | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) |  |
| out-iphone-run2/raw/zh-Hans/02_benchmarks.png | zh-Hans | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time |  |
| out-iphone-run2/raw/zh-Hans/03_timer_setup.png | zh-Hans | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge | second choice |
| out-iphone-run2/raw/zh-Hans/04_clock.png | zh-Hans | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | WEB PICK |
| out-iphone-run2/raw/pl/01_train.png | pl | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) |  |
| out-iphone-run2/raw/pl/02_benchmarks.png | pl | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time | WEB PICK |
| out-iphone-run2/raw/pl/03_timer_setup.png | pl | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-run2/raw/pl/04_clock.png | pl | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | second choice |
| out-iphone-run3/raw/nl/01_train.png | nl | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) | second choice |
| out-iphone-run3/raw/nl/02_benchmarks.png | nl | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time |  |
| out-iphone-run3/raw/nl/03_timer_setup.png | nl | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-run3/raw/nl/04_clock.png | nl | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | WEB PICK |
| out-iphone-run3/raw/pt/01_train.png | pt | train | Train tab, top: Start here card, The Chief card, AMRAP/For Time/EMOM/Tabata tiles | yes (empty state) | WEB PICK |
| out-iphone-run3/raw/pt/02_benchmarks.png | pt | benchmarks | Benchmarks library, top of the Girl list (Amanda, Angie, Annie) | yes (public WOD names; no Heroes names in view); English leftovers: Girl, movements, For Time |  |
| out-iphone-run3/raw/pt/03_timer_setup.png | pt | timer_setup | AMRAP timer setup sheet (15:00, get ready 10 s) | yes; English: For Time/EMOM chip names, last chip cut off at the right edge |  |
| out-iphone-run3/raw/pt/04_clock.png | pt | clock | WOD clock, 12 Min EMOM, round 2/12 | yes | second choice |

### Android (54 frames: 18 English dry runs, 6 zh-CN smoke, 36 that count)

| path | language | screen | what it shows | public-safe | use |
|---|---|---|---|---|---|
| out-android-dry/raw/en/01_log.png | en | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar.  | yes (seeded demo data, no account) |  |
| out-android-dry/raw/en/02_progress.png | en | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-dry/raw/en/03_analytics.png | en | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) |  |
| out-android-dry/raw/en/04_train.png | en | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-dry/raw/en/05_benchmarks.png | en | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-dry/raw/en/06_clock.png | en | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) |  |
| out-android-dry-final/raw/en/01_log.png | en | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar.  | yes (seeded demo data, no account) |  |
| out-android-dry-final/raw/en/02_progress.png | en | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-dry-final/raw/en/03_analytics.png | en | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) |  |
| out-android-dry-final/raw/en/04_train.png | en | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-dry-final/raw/en/05_benchmarks.png | en | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-dry-final/raw/en/06_clock.png | en | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) |  |
| out-android-zhsmoke/raw/zh-CN/01_log.png | zh-CN | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar.  | yes (seeded demo data, no account) |  |
| out-android-zhsmoke/raw/zh-CN/02_progress.png | zh-CN | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-zhsmoke/raw/zh-CN/03_analytics.png | zh-CN | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) |  |
| out-android-zhsmoke/raw/zh-CN/04_train.png | zh-CN | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-zhsmoke/raw/zh-CN/05_benchmarks.png | zh-CN | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-zhsmoke/raw/zh-CN/06_clock.png | zh-CN | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/hi/01_log.png | hi | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar. Hindi labels, seeded notes in Hindi. | yes (seeded demo data, no account) | WEB PICK |
| out-android-run1/raw/hi/02_progress.png | hi | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/hi/03_analytics.png | hi | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/hi/04_train.png | hi | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-run1/raw/hi/05_benchmarks.png | hi | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/hi/06_clock.png | hi | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) | second choice |
| out-android-run1/raw/tr/01_log.png | tr | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar. FAB reads "Kaydet" (the app's Turkish string for Log). | yes (seeded demo data, no account) | second choice |
| out-android-run1/raw/tr/02_progress.png | tr | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/tr/03_analytics.png | tr | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) | WEB PICK |
| out-android-run1/raw/tr/04_train.png | tr | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-run1/raw/tr/05_benchmarks.png | tr | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/tr/06_clock.png | tr | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/zh-CN/01_log.png | zh-CN | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/zh-CN/02_progress.png | zh-CN | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/zh-CN/03_analytics.png | zh-CN | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations).  | yes (seeded demo data, no account) | second choice |
| out-android-run1/raw/zh-CN/04_train.png | zh-CN | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar.  | yes (no data at all) |  |
| out-android-run1/raw/zh-CN/05_benchmarks.png | zh-CN | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English.  | yes (seeded demo data, no account) |  |
| out-android-run1/raw/zh-CN/06_clock.png | zh-CN | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase.  | yes (seeded demo data, no account) | WEB PICK |
| out-android-run2/raw/pl/01_log.png | pl | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pl/02_progress.png | pl | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | WEB PICK |
| out-android-run2/raw/pl/03_analytics.png | pl | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations). Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pl/04_train.png | pl | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (no data at all) |  |
| out-android-run2/raw/pl/05_benchmarks.png | pl | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pl/06_clock.png | pl | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | second choice |
| out-android-run2/raw/nl/01_log.png | nl | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/nl/02_progress.png | nl | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | second choice |
| out-android-run2/raw/nl/03_analytics.png | nl | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations). Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | WEB PICK |
| out-android-run2/raw/nl/04_train.png | nl | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (no data at all) |  |
| out-android-run2/raw/nl/05_benchmarks.png | nl | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/nl/06_clock.png | nl | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pt/01_log.png | pt | log | Log tab, All filter: "52 week streak" chip, two weekday groups of demo lift entries (sets, volume, notes in the app language), the Log button, bottom tab bar. PR badges and highlighted PR sets (seeded). Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | WEB PICK |
| out-android-run2/raw/pt/02_progress.png | pt | progress | Progress > Lifts for Back Squat: four stat cards (estimated 1RM, volume, sets, average weight in kg) and the Progress Over Time chart. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) | second choice |
| out-android-run2/raw/pt/03_analytics.png | pt | analytics | Progress > Analytics scrolled to the Plateau Analysis card ("2 lifts showing plateau", Back Squat / Clean with recommendations). Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pt/04_train.png | pt | train | Train tab, top: six timer tiles (AMRAP, For Time, EMOM, Tabata, Intervals, Countdown); the Snap a WOD row is cut off by the tab bar. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (no data at all) |  |
| out-android-run2/raw/pt/05_benchmarks.png | pt | benchmarks | Train > Benchmarks library, top of the Girl list (Amanda, Angie), Start Timer row; Girl/For Time/movements are app content in English. Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |
| out-android-run2/raw/pt/06_clock.png | pt | clock | Full-screen WOD clock, 12 Min EMOM, round 2/12, green work phase. "Round" is English in the app's own Portuguese string (app content). Status bar shows no Wi-Fi icon (battery only) in this run. | yes (seeded demo data, no account) |  |

Verdict (iPhone): 28 of 28 frames are public-safe and in the right language; 0 blank, 0 cut off, 0 wrong-language, 0 private. Verdict (Android): 54 of 54 frames of the five runs are public-safe and in the right language; 0 blank, 0 wrong screen, 0 private. Left out of the picks: iPhone `01_train` in hi/tr/zh-Hans/pl/nl (the home page already shows WOD Tracker's Train screen from the 2026-10-01 run in other languages), `03_timer_setup` (last chip cut off, least interesting), the English dry-run frames; Android `04_train` (no data, the iPhone job covers Train) and `05_benchmarks` (English list, same as the iPhone frames).

## Frames on the site (12 of the 60 captured, picked after looking at all of them)

Converted with `cwebp -q 80 -resize 360 0` into `site/public/img/showcase/` (no captions, frames or edits). Sources under `/Users/manu/Developer/shotfleet-rc-build/showcase-wod/`:

| site file | source frame | run |
|---|---|---|
| wod_iphone_hi_clock.webp | out-iphone-run1/raw/hi/04_clock.png | iphone-run1 |
| wod_iphone_tr_benchmarks.webp | out-iphone-run1/raw/tr/02_benchmarks.png | iphone-run1 |
| wod_iphone_zh-hans_clock.webp | out-iphone-run2/raw/zh-Hans/04_clock.png | iphone-run2 |
| wod_iphone_pl_benchmarks.webp | out-iphone-run2/raw/pl/02_benchmarks.png | iphone-run2 |
| wod_iphone_nl_clock.webp | out-iphone-run3/raw/nl/04_clock.png | iphone-run3 |
| wod_iphone_pt_train.webp | out-iphone-run3/raw/pt/01_train.png | iphone-run3 |
| wod_android_hi_log.webp | out-android-run1/raw/hi/01_log.png | android-run1 |
| wod_android_tr_analytics.webp | out-android-run1/raw/tr/03_analytics.png | android-run1 |
| wod_android_zh-cn_clock.webp | out-android-run1/raw/zh-CN/06_clock.png | android-run1 |
| wod_android_pl_progress.webp | out-android-run2/raw/pl/02_progress.png | android-run2 |
| wod_android_nl_analytics.webp | out-android-run2/raw/nl/03_analytics.png | android-run2 |
| wod_android_pt_log.webp | out-android-run2/raw/pt/01_log.png | android-run2 |

No frame of `out-iphone-run1-attemptA-hi-frame02-wrong` or of any other discarded attempt is used.

## Not run

iPad, tablet AVD (`shotfleet_android_tablet` never booted), Wear, Watch, the other 13 languages, Programs/Profile/Log/Progress/AI Coach/Health screens on iPhone (never tapped, on purpose), Settings/AI Coach/Health on Android, the camera/Snap a WOD sheet, seeded data on iPhone. Nothing was changed in the owner's repo or the stores by these runs.

## Files (layout of this folder)

See README.md. `flow*.yaml` and `shotfleet*.toml` are the flows and configs (final and the versions earlier runs used); `iphone-*/` and `android-*/` hold `run.json`, `check.json` (the report) and `check-in-run.json` of each run; `logs/` has the run and check logs, the simulator, AVD and adb lists before and after, the last quiet check and `failed-attempts/` and `failed-attempts-android/` with the logs of the failed attempts; `scripts/` the chain and check scripts; `progress.log` and `progress-android.log` the timeline of each job. The PNG frames, the .app and the APK are not part of the record (two PNGs from `logs/failed-attempts*` were left out to keep it small).
