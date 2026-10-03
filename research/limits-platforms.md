# Overcoming shotfleet's platform limits (research, 2026-10-02)

Scope: README "Limits" items (1) macOS only, (2) Android phone only, (3) API 33+ only, (4) Apple Watch / Mac / tvOS / visionOS / custom product pages.
Code read: main checkout `/Users/manu/Developer/shotfleet` at 304cd1a (read-only; line numbers below are from there, this worktree's `shotfleet.py` is older and has no Android tablet code). Nothing was booted; no simulator, emulator or Maestro flow was run.

Evidence tags: **[V]** verified in a primary source fetched today (URL given). **[M]** measured or read on this Mac today. **[I]** inferred or from secondary sources (blogs, search snippets); treat as a hypothesis to test.

## 0. Read this first

1. **Android tablets are already built and verified in main** (commits 62e5ec1, 03605fc, 2026-10-02): `devices = ["phone", "tablet"]`, phone 1080x1920 and tablet 1440x2560 @320 dpi from one flow, exported to `phoneScreenshots` / `tenInchScreenshots` (`ANDROID_DEVICES`, shotfleet.py L982-985). It does **not** cover `sevenInchScreenshots`, Wear OS or TV. The only open tablet work is the 7" slot (section 2). Do not start a second tablet implementation.
2. **Premise correction for (2): Google's page does not say "4 each for 7" and 10"".** It says [V] (https://support.google.com/googleplay/android-developer/answer/9866151): "For Chromebook and tablets, you can add a minimum of 4 screenshots", 1,080-7,680 px, 16:9 landscape or 9:16 portrait. The promotion rule is "at least four screenshots with minimum 1080px resolution" for apps, and "a minimum of two screenshots across different device types" is needed to publish. Whether the Console counts 7" and 10" separately is **not stated on the page**; I could not check the Console UI.
3. **Premise correction for (3): the "API 33+" limit is about the emulator image, not about your users' devices.** The screenshot is taken on one emulator you choose. An app with `minSdk 21` still runs on an API 36 emulator. So the limit excludes almost nobody (section 3).
4. **Biggest real gap is (1), but only the Android half of it** (and CI). iOS needs a Mac, full stop.

## 1. Verdict table

| # | Limit | Verdict | Effort | Build order |
|---|---|---|---|---|
| 1a | Android-only runs on Linux (and `check` on Linux via Tesseract) | **Feasible now** for run; **needs experiment** for check quality | M (3-4 days incl. CI validation) | 2 |
| 1b | Android on Windows native | Not worth it (WSL/Linux instead) | L | - |
| 1c | iOS off a Mac | Impossible (Xcode/CoreSimulator) | - | - |
| 2a | Android 10" tablet | **Done in main** | - | - |
| 2b | Android 7" tablet (`sevenInchScreenshots`) | **Feasible now** (config + folder) | S (half a day) | 1 |
| 2c | Wear OS | Needs experiment | M | 4 |
| 2d | Android TV | Needs experiment; breaks the "one flow" model | M | 5 |
| 3 | API < 33 emulators | Not worth it | M | - |
| 4a | Apple Watch capture | Not worth it (Maestro cannot drive watchOS) | L | - |
| 4b | Mac, tvOS, visionOS capture | Not worth it | L each | - |
| 4c | Watch/Mac/TV/Vision `check` + `export` of screenshots made elsewhere | Feasible now (linter already knows the sizes) | S | 3 |
| 4d | Custom product pages | Export-side variant sets feasible; upload is `asc`'s job | M | 6 |

## 2. (1) macOS only

### 2.1 What truly needs a Mac

| Part | Needs macOS? | Evidence |
|---|---|---|
| iOS simulators, `xcrun simctl`, building the `.app` | **Yes, hard** | Xcode / CoreSimulator. No workaround. |
| Maestro itself | No. macOS, Linux, Windows | [V] https://docs.maestro.dev/get-started/quickstart.md (answer to "which OSes"): macOS, Windows, Linux; WSL "only if strictly necessary". Needs Java 17+ [V] https://github.com/mobile-dev-inc/maestro |
| Android emulator + adb + aapt2 | No. Linux x86_64 needs KVM; Windows needs WHPX/Hyper-V | Google ships x86_64 images for API 33-37, Wear and TV: `sdkmanager --list` today shows `system-images;android-36;google_apis;x86_64`, `android-36;android-wear-signed;x86_64`, `android-36;android-tv;x86_64`, `android-35;google_apis_tablet;x86_64` [M] |
| The OCR helper (`ocr.swift`: Vision text recognition + NaturalLanguage language detection) | **Yes** (Swift, Vision, NaturalLanguage) | Replacement exists: Tesseract fallback is already coded (`TESSERACT_COMMAND`, `external_ocr`, `SHOTFLEET_OCR`) |
| The released binary (PyInstaller, arm64, signed/notarized, Homebrew `depends_on :macos`) | Built for macOS | `packaging/build.sh`, `packaging/shotfleet.rb` |
| The Python itself (`shotfleet.py`) | No: stdlib-only single file, Python 3.11+ | imports at L17-21 are all stdlib [M] |

### 2.2 Every macOS-specific call in `shotfleet.py` (main @304cd1a)

grep for `xcrun|PlistBuddy|swiftc|plutil|sips|/Applications|Library/|sysctl|ps|pgrep`. There is **no `sips`, no `/Applications`, no `osascript`, no `open`**. PNG sizes are read from the header (`png_size`, L1718 area), not with `sips`.

| Line(s) | Call | iOS only? | What it takes for the Android-on-Linux path |
|---|---|---|---|
| 59, 143, 1427, 1617 | `/usr/libexec/PlistBuddy` | iOS only | Nothing (guard: `[ios]` on non-darwin -> `Fail("iOS needs a Mac")`). Later optional: `plistlib` (stdlib, reads binary and XML plists) replaces it |
| 155, 161, 313 | `plutil -convert json` | iOS only | Same as above (only if you want iOS `check --app` on Linux; plain-text `.strings` would need a small parser [I]) |
| 660-676, 797, 1634, 1981 | `xcrun simctl ...` | iOS only | Nothing. L1981 loops over an empty `OUR_SIMS` on Android, so it never calls xcrun |
| 694 | `ps -Ao pid=,ppid=` (`descendants`, used by `run_guarded` on **both** platforms) | no | Works unchanged on procps (Debian/Ubuntu/Fedora) [I]; not on BusyBox/Alpine |
| 746-747 | `pgrep -f "simctl diagnose"`, `kill -9` | no, but harmless | Unchanged (matches nothing on Linux) |
| 763 | `sysctl -n kern.memorystatus_vm_pressure_level` (`fit_parallel`, called by `android_run`) | no | On Linux it prints nothing, so there is **no memory guard**. Replace with `/proc/meminfo` `MemAvailable` (halve parallelism below ~1.5 GB per emulator [I]) |
| 945 | `SDK = $ANDROID_HOME or ~/Library/Android/sdk` | no | Linux default `~/Android/Sdk`; also honor `ANDROID_SDK_ROOT` |
| 996 | default image `system-images;android-36;google_apis;arm64-v8a` | no | Pick by `platform.machine()`: `x86_64` on Linux x64 (image exists [M]). AVD creation otherwise unchanged |
| 1010-1012 area (`start_emu`) | `emulator -no-window -no-audio -no-boot-anim -snapshot` | no | Add `-gpu swiftshader_indirect` when no GPU (headless CI) [I]; check `/dev/kvm` in `doctor` |
| 1143-1150 | `ocr_tool()`: `swiftc` build or bundled `ocr` | **yes, and called unconditionally in `cmd_check` (L1432)** | On non-darwin: skip Vision, force `use_vision=False` and use Tesseract (L1442 path exists) |
| 1161, 1554 | `readable_languages()`, doctor warm-up call the Swift helper | yes | Gate by platform; on Linux treat "readable" as "Tesseract has the language data" |
| 1352-1353 | `ps ... ANECompilerService` | yes (macOS) | Gate |
| 1542-1543 | doctor requires `swiftc`, `xcrun` | yes | Gate by platform; add KVM and Tesseract checks |
| 1875 (and `licence.py` `STATE`) | licence file under `~/Library/Application Support` | yes | XDG: `~/.config/shotfleet`. `SHOTFLEET_KEY` in CI already validates without using an activation slot (L1948) |
| 1947 | licence enforced only when `sys.frozen` | - | A Linux **zipapp or source install is never "frozen", so it would run unlicensed**. Either ship a PyInstaller Linux binary, or accept the "honour system" the licence docstring already accepts |

Not macOS-specific but Linux-relevant: `os.uname()` in `licence.py` (POSIX only, fine on Linux, breaks on Windows); Windows would also need replacing `kill`, `ps`, `pgrep`, the `maestro` shim and the SIGTERM handler.

### 2.3 Minimal plan: Android run + check on Linux (verdict: feasible now, effort M)

1. Platform guard in `load_config`/`cmd_run`: `[ios]` off darwin -> one-line Fail. (S)
2. Paths and defaults: SDK location, `x86_64` image by host arch, licence path. (S)
3. `cmd_check`: if not darwin, never call `ocr_tool()`; route to Tesseract, tell the user which screens lost language detection. (S)
4. `fit_parallel` via `/proc/meminfo`; `doctor` Linux branch (KVM, tesseract, Java 17). (S)
5. Emulator flags for headless GPU-less hosts; run once on a GitHub `ubuntu-latest` job to find what breaks. (S-M, this is the real unknown)
6. Packaging: `linux-x86_64` PyInstaller build in a CI matrix (build on the oldest Ubuntu you support for glibc compatibility [I]); Homebrew formula `on_linux` or a plain `curl | tar` install. (S-M)
7. Re-measure with `tools/langmatrix.py` on Tesseract output for the 18-language CrossfitTracker Android set: **this is the experiment that decides whether `check` on Linux is trustworthy.** (S-M)

Quality of the Tesseract path, one data point [M]: I ran `tesseract -l eng+<lang>` (Tesseract installed locally with 162 languages) on the repo's four 360x640 JPEG Android shots (`site/public/img/android_{de,hi,ja,zh-CN}.jpg`). German, Hindi, Japanese and Simplified Chinese UI text came out readable, but CJK lines come back with spaces between words ("プロ フィ ー ル", "进度 ... 动作 库"). Whether `judge_screen`'s matcher normalizes that is **untested** (and 360x640 JPEGs are far worse than real 1080x1920 PNGs). Language detection (`lang`/`langs`) is None with Tesseract, so `check` without `--app` loses its detector on Linux; with `--app app.apk` it compares lines to the APK strings, which is the mode that matters. A pure-Python detector (fastText lid / lingua) is an option if needed (M, adds a dependency) [I].

Windows (verdict: not worth it, L): native Windows needs the process-control rewrite above plus WHPX; Maestro itself says to use WSL only if necessary [V]; emulator inside WSL2 needs nested KVM [I]. Tell Windows users to use a Linux CI job or a Mac.

### 2.4 GitHub Actions: costs, runners, virtualization

Verified at https://docs.github.com/en/billing/reference/actions-runner-pricing (fetched today) unless tagged:

| Runner | $/min | Notes |
|---|---|---|
| Linux 2-core x64 | 0.006 | `ubuntu-latest`: 2 vCPU/8 GB private repos, **4 vCPU/16 GB public repos** [V runner reference] |
| Linux 2-core arm64 | 0.005 | **No KVM on GitHub's arm64 Linux runners** [I, secondary: hannesa2/action-android-arm64 and search results] |
| Linux 4/8/16-core x64 (larger) | 0.012 / 0.022 / 0.042 | larger runners are not eligible for included minutes on private repos [V about-larger-runners] |
| Windows 2-core | 0.010 | |
| macOS 3 or 4-core (M1 or Intel) | 0.062 | `macos-14/15/26`, label `xcode-27` exist; arm64 M1 = **3 CPU, 7 GB** [V] |
| macOS 5-core M2 Pro (`macos-*-xlarge`) | 0.102 | 14 GB [V] |
| macOS 12-core Intel (`macos-*-large`) | 0.077 | 30 GB [V] |

- GitHub's own docs: "Nested-virtualization is not supported due to the limitation of Apple's Virtualization Framework" for arm64 macOS runners [V https://docs.github.com/en/actions/reference/runners/github-hosted-runners and .../larger-runners]. So **an accelerated Android emulator cannot run on hosted Apple-silicon macOS runners** (inference from that statement + the emulator needing Hypervisor.framework [I]). Hosted Intel macOS runners (`macos-15-intel`, `macos-26-intel`) exist [V] and `reactivecircus/android-emulator-runner` uses Hypervisor.framework there [V README], but Intel is the legacy line; do not build on it.
- Linux x64 KVM: "Actions users of our 2-vCPU GitHub-hosted Linux runners will be able to make use of hardware acceleration for Android testing" via a udev rule [V https://github.blog/changelog/2024-04-02-github-actions-hardware-accelerated-android-virtualization-now-available/]. The README of android-emulator-runner calls Ubuntu "2-3 times faster than the macOS ones" [V].
- Free tier: standard runners are free in public repos [V billing concepts page]; Free plan 2,000 min/month, Pro/Team 3,000 [V]. The "macOS minutes count 10x against included minutes" claim appears in secondary sources only; GitHub's billing page I fetched lists dollar rates and no multipliers, so I could not verify it. Plan on dollars, not included minutes.
- Cost per run [I, from README's iOS benchmark of 18 locales in 534 s on 4 simulators plus build/boot overhead]: iOS on `macos-26-xlarge` roughly 15 min x $0.102 = ~$1.5. Android on Linux roughly 12-25 min x $0.006-0.022 = ~$0.1-0.5 (4 emulators need the 8-core larger runner; `ubuntu-latest` private has 2 vCPU, so `parallel = 1`). Android emulator RAM per instance is a guess [I]; measure in experiment E1.
- Licensing in CI: `SHOTFLEET_KEY` validates without consuming an activation slot (L1948) [M]: good for ephemeral runners.

### 2.5 Recommended CI recipe per platform

- **iOS (macOS only):** one job on `macos-26` (use `-xlarge` if you want 4 simulators; the 3-core/7 GB M1 is small for 4 simulators plus Maestro drivers [I]); `xcodebuild ... -sdk iphonesimulator`; `shotfleet run --parallel 2`; upload `out/` and `check.json`. The README's existing `check`-only recipe (macos-15) is still the cheapest macOS job: `check` needs no simulators.
- **Android (Linux, KVM):** `ubuntu-latest` (public repo: 4 vCPU) or a larger runner; enable KVM with the udev snippet from android-emulator-runner [V]; install Java 17, Maestro, SDK images `x86_64`; `shotfleet run android.toml --parallel 2`; upload artifacts. Needs Linux support from section 2.3.
- **Both:** two parallel jobs (macOS iOS, Linux Android) uploading `out-ios` and `out-android`; a final cheap Linux job runs `shotfleet check` on both folders (Tesseract) and `export`. This also keeps macOS minutes (6-10x the price of Linux) to the iOS capture only.
- **Self-hosted Mac mini:** the only way to do both platforms on one machine with accelerated arm64 emulators (what shotfleet does locally today) [I].

## 3. (2) Android beyond phones

### 3.1 What Google says (verified today)

From https://support.google.com/googleplay/android-developer/answer/9866151 [V]: up to 8 screenshots per device type; JPEG or 24-bit PNG, min 320, max 3840 px (general); **tablets and Chromebooks: min 4, 1,080-7,680 px, 9:16 or 16:9**; **Wear OS: at least 1, 1:1, min 384x384, app UI only**; **Android TV: "at least one Android TV screenshot" to publish a TV app** (no size on the page); Android XR: 4-8, 8:5; Automotive: 2 portrait 800x1280 + 2 landscape 1024x768.

fastlane supply folder names [V https://docs.fastlane.tools/actions/supply/]: `phoneScreenshots/`, `sevenInchScreenshots/`, `tenInchScreenshots/`, `tvScreenshots/`, `wearScreenshots/`, under `fastlane/metadata/android/<locale>/images/`.

### 3.2 7" and 10" tablets from the same flow (verdict: 10" done; 7" feasible now, S)

Existing mechanism, already proven [M, from main's git log]: `hw.lcd.width/height/density` override on a `pixel_tablet` AVD (profile's native size is 2560x1600 @320 per my local `Pixel_Tablet.avd/config.ini` [M]); portrait 9:16 so Play can recommend the listing. 1440x2560 @320 dpi = 720x1280 dp, which lands in the `sw720dp` (10") layout bucket.

7" proposal (sizes from device specs/arithmetic [I]; the "does the layout switch to the 7" bucket" part is an experiment):
- `"tablet7": {"avd": "shotfleet_android_tablet7", "profile": "7in WSVGA (Tablet)" (or `Nexus 7 2013`), "size": (1080, 1920, 280), "folder": "sevenInchScreenshots"}`.
- Why not the real Nexus 7 2013 (1200x1920 @320): that is 10:16, not 9:16, so it would not qualify for Play's 9:16/16:9 recommendation rule [V]. Nexus 7 (2012) is 800x1280 @213 (my local `Nexus_7_2012.avd` [M]), under 1080 px, so it fails the 1080px rule.
- Why 280 dpi: 1080 px / (280/160) = 617 dp wide, i.e. `sw600dp` (7") and below `sw720dp` (10"). Any dpi up to 288 keeps sw >= 600.
- Avoid landscape-locked tablet layouts: if an app forces landscape on tablets the portrait override may render rotated/letterboxed [I]. This is experiment E3.
- Cheap alternative: export the 10" set into both folders. Zero emulator time, but the 7" slot then shows images from a different layout bucket; whether Play validates that is unknown [I]. Offer it as a flag, default off.
- Export: add `sevenInchScreenshots` to the `folder` map; the store linter should count per folder (4+ at 1080px+ for promotion, 8 max) rather than lumping tablets together because Google's page does not say which. Keep warnings as notes, not failures.

Risks: tablet emulators are heavy (a 1440x2560 AVD costs about 1.8x the pixels of the phone one [I]); main's commit 62e5ec1 noted the Maestro driver "never installs" on a fresh tablet emulator before 03605fc fixed it, so expect first-run slowness (`MAESTRO_DRIVER_STARTUP_TIMEOUT` default is 15 s on Android [I: search snippet of docs.maestro.dev/advanced/configuring-maestro-driver-timeout, page not fetched], main already sets 240 s).

### 3.3 Wear OS (needs experiment, M)

- Store rule [V]: 1:1, min 384x384, no frames/extra text. fastlane folder `wearScreenshots` [V].
- Emulator: Wear images exist locally (`android-wear-signed`, Wear OS 6, and a `Wear_OS_XL_Round` AVD [M]) and as x86_64 for Linux [M]. API 33 Wear = Wear OS 4 [M sdkmanager listing: "Wear OS 4"].
- Unknowns: Maestro docs do not confirm Wear OS support ("I cannot find information in the docs confirming Wear OS support", answer from docs.maestro.dev [V]); round displays: `adb screencap` likely returns a square with the round mask not applied [I]; `cmd locale set-app-locales` on Wear [I, framework command, probably works on API 33+]; one flow serving phone and watch is unlikely because the screens differ (a Wear app is a different APK with its own flow). Needs an experiment on one real Wear app before committing.

### 3.4 Android TV (needs experiment, M, low priority)

- Maestro `pressKey` supports `Remote Dpad Up/Down/Left/Right/Center` [V, docs.maestro.dev answer]. TV flows navigate by focus, not by tapping text, so the "one English flow for every device" promise does not carry over: it would be a separate TV flow with the same language rewrite. Spec: at least one TV screenshot, no size on the page [V]. TV images exist for API 33-36 incl. x86_64 [M].
- Demand is likely tiny for the indie audience in STRATEGY.md [I].

## 4. (3) Older Android than API 33

Why 33: `LocaleManager`/per-app language and `adb shell cmd locale set-app-locales` arrived in Android 13 (API 33) [V https://developer.android.com/guide/topics/resources/app-languages]. AndroidX `AppCompatDelegate.setApplicationLocales()` backports it only **inside the app's own code** (AppCompat 1.6+, plus a manifest service for API <= 32) [V same page], which shotfleet cannot trigger from outside.

Options for an API <= 32 emulator (all [I], from community sources, none tested here):

| Option | How | Cost / catch |
|---|---|---|
| System locale via root | `adb root`, `setprop persist.sys.locale de-DE`, `setprop ctl.restart zygote` (older recipes use `persist.sys.language` + `persist.sys.country`, removed on newer images) | Needs a root-capable image (`google_apis`, not `google_apis_playstore`). Zygote restart kills the app and SystemUI (~10-30 s guess; shotfleet already re-asserts demo mode per round). A cold boot per language costs ~22 s vs 4-5 s snapshot boot (numbers from the code comment at `start_emu`) |
| `emulator -prop persist.sys.locale=...` at launch | Per-language cold boot, `-no-snapshot` | Loses the snapshot speedup, which is what makes parallel rounds cheap |
| `settings put system system_locales ...` / `content insert` | Writes the setting, but the configuration is applied only on restart/broadcast | Unreliable [I]; do not build on it |
| `am broadcast -a com.android.intent.action.SET_LOCALE` | Needs the old "Custom Locale" app in the image | Absent from current images [I] |

How many people does it exclude? Using Google's version distribution as relayed by Android Headlines for December 2025 [secondary; https://www.androidheadlines.com/2026/01/android-version-distribution-numbers-2025-2026-market-share.html]: Android 13 = 13.9%, Android 12 = 11.4%, 11 = 13.7%, 10 = 7.8%, 9 = 4.5%, older ~4.7%; so devices at API <= 32 are about 42%, API 33 is 13.9%, and API >= 34 is the rest (telemetrydeck shows SDK 36 at 46.6% in September 2026, a biased developer sample [V telemetrydeck.com/survey/android/Android/sdkVersions/]). **That number is irrelevant for shotfleet**: it measures users' phones, while shotfleet needs one modern emulator. The people actually excluded are developers whose app cannot run on an API 33+ emulator image at all (apps that crash on newer Android, or 32-bit-only native libraries on an arm64 image [I]), and I have seen no such app in research/real-apps.md.

**Recommendation: do not build it.** Add one README sentence: "needs an API 33+ *emulator*; your app's minSdk can be lower". Revisit if three buyers ask. One side benefit worth remembering: a system-wide locale (root route) would also localize system permission dialogs, which per-app locales do not (roadmap item 2.1) [I].

## 5. (4) Apple platforms beyond iPhone/iPad

Source for specs [V]: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications (fetched today; 1-10 screenshots, JPEG/PNG, no alpha).

| Class | Apple spec [V] | Required? [V] | Can a Maestro flow drive it? | Verdict |
|---|---|---|---|---|
| iPad 13" | 2064x2752 or 2048x2732 | if app runs on iPad | Yes, done (`device_types`) [M, ROADMAP] | Done |
| Apple Watch | 422x514, 410x502, 416x496, 396x484, 368x448, 312x390 depending on model | "Required for Apple Watch apps"; "same screenshot size ... across all localizations" | **No.** Maestro's docs list only Android (emulators, devices) and iOS (simulators) [V docs.maestro.dev/get-started/supported-platform]; Watch simulators exist (this Mac has watchOS 26.5 and 27.0 runtimes and Series 12/Ultra 4 device types [M]) | Not worth it as flow-driven capture. L, would need XCUITest/own driver |
| Mac | 16:10: 1280x800, 1440x900, 2560x1600, 2880x1800 | "Required for Mac apps" | No: Maestro has no macOS-desktop driver [I: not in docs] | Not worth it |
| Apple TV | 1920x1080, 3840x2160 | "Required for Apple TV apps" | No: tvOS support is an open P3 epic, issue #1515 since Oct 2023 [V https://github.com/mobile-dev-inc/maestro/issues/1515] | Not worth it |
| Vision Pro | 3840x2160 | "Required for Apple Vision Pro" | No (no visionOS driver) [I] | Not worth it |

Cheap, real value: `check` and `export` for these classes when screenshots come from other tools. The linter already encodes Watch, Mac and TV sizes (shotfleet.py L1649-1650 [M]); add the Watch rule "one size across all locales" (Apple states it [V]), Vision Pro sizes, and fastlane's folder handling (deliver reads them from `screenshots/<locale>/`; fastlane's table has the same Watch/Mac/TV/Vision sizes, see `research/store-specs.md` section 3 [V]). Effort S. This is a funnel feature for `check`, not a capture feature.

**Custom product pages (CPP).** Apple [V https://developer.apple.com/app-store/custom-product-pages and .../configure-multiple-product-page-versions/]: up to 70 additional versions per app (the cap was 35 until October 2025 per a secondary source, adapty/respectaso), customizable screenshots, app previews, promotional text; localizable; each needs review; available iOS 15+; the app must be Ready for Distribution in at least one region. The App Store Connect API has `appCustomProductPageLocalizations` -> `appScreenshotSets` [I, from search results listing the endpoint]. For a flow-driven tool this is a **variant-set problem**, not a capture problem: capture more screens once, then group them per page (`[[variants]] name="fitness" shots=["home","stats"]`), and export per-variant folders. Upload stays with `asc`/fastlane (STRATEGY.md says "not building store upload"). Verdict: feasible, M, unproven demand (ROADMAP 2.7 says the same); AppScreens sells it [I]. Build only after the CI/Linux work.

## 6. Experiments to run before building (none needs a simulator on this Mac)

| ID | Question | How | Cost |
|---|---|---|---|
| E1 | Does the Android path run on `ubuntu-latest` with KVM, x86_64 API 36, Maestro 2.x, 1 and 2 parallel emulators? Boot time, RAM, wall time for 18 locales | A GitHub Actions workflow on a throwaway public repo (free minutes) after steps 1-5 of 2.3 | S |
| E2 | Does `judge_screen` give the same verdicts on Tesseract output as on Vision for the 18-language Android set (incl. CJK spacing)? | Run `check` with `SHOTFLEET_OCR`/Tesseract on CrossfitTracker's committed Android screenshots (126 files, README) and diff `check.json` vs the Vision run; plant the same defects the README mentions | S |
| E3 | Does 1080x1920 @280 give `sw600dp` and a real 7" layout; does the driver install; do landscape-locked apps break? | One emulator run, one app, on a quiet Mac (needs the Mac, so schedule it when the other sessions are done) | S |
| E4 | Does Play Console accept the same set in both tablet slots / require 4 in each? | Ask Manu to look at Play Console's tablet upload page (not reachable from here) | S |
| E5 | Maestro on a Wear OS AVD: driver install, `tapOn` by text, `takeScreenshot` | One real Wear app | S-M |

## 7. Ranked recommendation (small paid CLI)

1. **7" tablet slot (S, half a day).** Everything else for tablets exists; this completes the Play tablet story and the store linter. Coordinate with the other session: only add `tablet7` to `ANDROID_DEVICES` and the folder map. Needs E3 and E4 first, or ship it as opt-in.
2. **Android run + check on Linux (M).** The largest untapped audience: Android developers are mostly not on Macs, and Linux CI is 6-10x cheaper than macOS minutes. It turns the planned "CI mode / team licence" (STRATEGY.md section 2, ~$149) into something Android teams can use without a Mac, while iOS stays Mac-only. Decide after E1+E2; if Tesseract-based check is weak, ship "run on Linux, check on a Mac or with `--app` string matching" first.
3. **`check`/`export` for Watch, Mac, TV, Vision screenshots from other tools (S).** Cheap funnel for the free command; the size tables already exist.
4. **Wear OS capture (M)**, only after E5 and only if a buyer asks.
5. **Android TV (M)**: separate flow model; skip until asked.
6. **CPP variant sets (M)**: unproven demand; export-side only.
7. **Do not build:** API < 33 (document the "emulator, not app" distinction instead), Windows-native, Apple Watch/Mac/tvOS/visionOS capture, iOS off a Mac.

## 8. Sources

- Google Play screenshots: https://support.google.com/googleplay/android-developer/answer/9866151
- fastlane supply: https://docs.fastlane.tools/actions/supply/
- Apple screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
- Apple custom product pages: https://developer.apple.com/app-store/custom-product-pages , https://developer.apple.com/help/app-store-connect/create-custom-product-pages/configure-multiple-product-page-versions/
- GitHub Actions pricing and runners: https://docs.github.com/en/billing/reference/actions-runner-pricing , https://docs.github.com/en/actions/reference/runners/github-hosted-runners , https://docs.github.com/en/actions/reference/runners/larger-runners , https://github.blog/changelog/2024-04-02-github-actions-hardware-accelerated-android-virtualization-now-available/
- Android emulator action: https://github.com/ReactiveCircus/android-emulator-runner
- Maestro: https://github.com/mobile-dev-inc/maestro , https://docs.maestro.dev/get-started/supported-platform , https://github.com/mobile-dev-inc/maestro/issues/1515
- Per-app languages: https://developer.android.com/guide/topics/resources/app-languages
- Android distribution (secondary): https://www.androidheadlines.com/2026/01/android-version-distribution-numbers-2025-2026-market-share.html , https://telemetrydeck.com/survey/android/Android/sdkVersions/
- Local: `sdkmanager --list`, `avdmanager list device`, `xcrun simctl list` (read-only), `~/.android/avd/*/config.ini`, Tesseract run on `site/public/img/android_*.jpg`.
