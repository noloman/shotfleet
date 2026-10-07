# Beyond Maestro: does shotfleet need it, and what about XCUITest, Espresso and Paparazzi? (2026-10-06)

Owner's question: "does our project work only if you're using Maestro? if this is true, what if we use something like
Espresso or UI tests in iOS or even Paparazzi?" Scope addition: "investigate using shotfleet beyond Maestro and try to improve
it and overcome any limitations", answered in "Build plan" at the end.

Tags: **[M]** measured here today (command run, output quoted), **[R]** read in code or files on `origin/main` (f18965e),
**[W]** read on the web today (URL given), **INFERENCE** = my estimate, not proven. Nothing was built. No device, simulator or
device lock was used. `check` was run from source twice on scratch copies of real fastlane folders, both times with the 1-minute
`vm.loadavg` under 300 (189 and 218).

## Short answer

Only half of it needs Maestro. `shotfleet run` (capture) is Maestro only. `shotfleet check` (wrong language, copies, missing
screens, store sizes) works on any folder of PNGs, it is free, and it already works on fastlane snapshot (XCUITest) output: on a
real snapshot folder on this Mac it found a real bug, a German listing whose app UI is English [M]. On screengrab (Espresso)
output it gives false "missing" problems today, because screengrab puts a timestamp in every file name by default [M]. Paparazzi
output is one flat folder with the language inside the file name, so `check` can only take it one language at a time today [R].

So the honest site line today is "Already use fastlane snapshot? `check` works on those screenshots". After a half-day fix it can
add screengrab, and after a docs change, Paparazzi.

## 1. Facts about today

### 1.1 What depends on Maestro [R]

| Part | Maestro? | Where in `shotfleet.py` |
|---|---|---|
| `run`: runs the flow on every device | yes | `ios_run_inner`, `android_run_inner`, `run_guarded` (the `maestro test` call); version gate in `main_dispatch` (`maestro_refusal`) |
| Rewriting English text selectors per language | yes, Maestro YAML only | `translate_flow`, `localize_flow`, `SELECTOR_RE` |
| Android screen text from the hierarchy (exact, no OCR) | yes, Maestro 2.7+ | `android_flow(hierarchy=True)`, `hierarchy_texts`, `save_hierarchy_texts` |
| iOS screen text during the run | no Maestro API, but only inside `run` | `capture_texts`, `ios_screen_texts` |
| Simulator/emulator pool, locale per device, capacity planner, stall guard | no Maestro API, but only reachable through `run` | `make_pool`, `android_pool`, `run_setup`, `plan_capacity`, `device_lock` |
| `doctor` | checks and installs Maestro (plus Java, Xcode, SDK) | `cmd_doctor`, `fix_plan`, `install_maestro` |
| `init` | writes a Maestro `flow.yaml` | `cmd_init` |

### 1.2 What does not depend on Maestro [R]

- `check <folder>` on any folder (`find_screenshots`): shotfleet's `raw/<locale>/`, fastlane deliver `screenshots/<locale>/`, supply
  `metadata/android/<locale>/images/{phone,sevenInch,tenInch}Screenshots/`, plain `<locale>/`, or a flat folder with `--locale`.
  Free in released builds (`require_licence` docstring: "`check`, `doctor` and `init` are free").
- `export`: needs a `check.json`; uses `run.json` when present. For a non-shotfleet folder it takes only plain `<locale>/*.png` and
  writes the App Store layout (comment in `cmd_export`: "Play folders and JPEGs from other tools need a shotfleet run or a copy by
  hand"). Needs a licence.
- The MCP `check` tool and `--json`.

### 1.3 What `check` needs from screenshots [R]

1. **Layout**: one of the folder shapes above. The folder name is the language (`LOCALE_LABEL`); store codes map back to app
   languages (`app_locale`: `de-DE` to `de`).
2. **Text evidence**: a `<shot>.texts.json` sidecar if present (only `run` writes one, read by `screen_text`), otherwise OCR (macOS
   Vision, with Tesseract or `--ocr-command` as fallback). Compared with the app's strings from `--app` (.app or .apk), `--strings`
   globs, or `run.json`. Without any of them it falls back to language detection and says so (`check_any`).
3. **Store rules** from pixels only: size per App Store display class, Play's 320-3840 px, counts (10/8), alpha channel, a
   6.9"/6.5" set, a 13" iPad set (`store_rules`, `image_info`).
4. **Same file names in every language**: the "missing" rule is `have != names`, where `names` is the union of exact file names
   across languages (`cmd_check`, the block after `for h, hits in by_hash.items()`).

### 1.4 Can it check fastlane snapshot, screengrab and Paparazzi output today?

**fastlane snapshot (XCUITest): yes [M].** Real output from `~/Developer/subscrifi/iosApp/fastlane/screenshots` (Snapfile: 8
languages, `iPhone 15 Pro Max`; names like `iPhone 15 Pro Max-01Home.png`, 1290x2796 RGB). Copied en-US, de-DE and
`screenshots.html` to scratch and ran `python3 shotfleet.py check snap --report ...` (no `--app`):

```
checked 24 screenshots in 2 languages: 13 problem(s)
  - de-DE/iPhone 15 Pro Max-01Home.png: text looks like 'en', expected 'de'
  ... (11 de-DE screens in all)
  - de-DE: 12 iPhone 6.9" screenshots; the App Store takes at most 10
  - en-US: 12 iPhone 6.9" screenshots; the App Store takes at most 10
```

I opened `de-DE/iPhone 15 Pro Max-01Home.png`: the app UI is English ("Home", "Search...", "MONTHLY", "Filter & Sort"); only the
system tab label "Mehr" and the number format are German. A true positive: the simulator was German, the app's strings were not.
The 12-per-listing problem is true too. Device-prefixed names and `screenshots.html` were handled fine.

**fastlane screengrab (Espresso): runs, with false problems [M].** screengrab appends `_<System.currentTimeMillis()>` to every
name unless `use_timestamp_suffix(false)` is set [W: `FileWritingScreenshotCallback.getScreenshotFile`; `runner.rb` line 274 passes
`-e appendTimestamp`]. Real output from `~/Developer/subscrifi/androidApp` (`01Home_1773697012807.png` in de-DE,
`01Home_1773696985949.png` in en-US). Ran `check sg`:

```
checked 12 screenshots in 2 languages: 2 problem(s)
  - de-DE: missing 01Home_1773696985949.png, 02Categories_1773696986518.png, ...
  - en-US: missing 01Home_1773697012807.png, 02Categories_1773697013353.png, ...
```

Every language "misses" every other language's files, so a default screengrab user gets a red check on a correct set. (macOS OCR
was still compiling its model, so Tesseract read these screens; that is unrelated.)

**Paparazzi / Roborazzi: not directly [R, W].** Paparazzi writes every image flat into `src/test/snapshots/images/`, named
`<package>_<Class>_<method>[_<label>].png` [W: `Snapshot.toFileName`, `SnapshotVerifier.kt`]. `find_screenshots` wants `<locale>/`
folders; a flat folder works only with `--locale`, one language per call, which loses the cross-language checks (copies, missing).
INFERENCE, unverified: Paparazzi saves ARGB images, so PNG colour type 6, and `image_info` treats colour type 6 as "has
transparency" even when every pixel is opaque. Every Paparazzi image would then get a transparency problem. The same rule fires on
real files here: `~/Developer/HackerNewsKMP` fastlane PNGs are colour type 6 [M]. App Store Connect rejects images with an alpha
channel, so the rule is right, but its message should say how to flatten.

**Is it documented and tested?**
- Documented: README "Check screenshots you already have (fastlane, screengrab, by hand)" (README.md:34-46), docs.html:117-119,
  index.html:338 ("Check any screenshots, from fastlane or by hand"). alternatives.html's fastlane section does not mention `check`.
- Claim in `tests/claims.json`: "Check screenshots you already have: fastlane snapshot/screengrab, a plain folder per language, by
  hand". Proof listed: `CheckAnyFolder.test_finds_fastlane_ios_android_and_plain_folders`,
  `FastlaneBothStores.test_check_with_a_build_picks_its_half_of_a_fastlane_folder_for_both_stores`, and others.
- Gap: those tests use synthetic names (`1.png`), never snapshot's `Device-Name.png` or screengrab's `name_<13 digits>.png`. So the
  screengrab half of that claim is **false with default screengrab settings**. The WOD Tracker evidence (252 iOS / 126 Android)
  used stable names (`01_lift_list.png`), not screengrab's.
- Paparazzi, Roborazzi, Compose Preview tests, swift-snapshot-testing: not mentioned, not tested.

## 2. Options for other capture tools

### (a) Bring your own capture (BYOC)

shotfleet boots the pool, sets each device's language, runs the user's test command once per language in parallel, collects the
PNGs, checks, exports.

What it adds over fastlane, read in fastlane's source [W]:
- snapshot runs **languages one after another**; only devices run at the same time (`simulator_launcher.rb` line 46
  `launcher_config.languages.each_with_index`, and inside it `launch_simultaneously(devices, language, ...)`).
- screengrab loops locales one by one per device too (`runner.rb` line 252 `@config[:locales].each`).
- Known pain: snapshot "much slower (like 3x slower)", fastlane#15938 (already in research/market-2026.md).

So BYOC's value is shotfleet's pool: 20 languages on 4 simulators in rounds, built once, plus the check gate, in one command. The
same pitch `run` has, minus "no test code".

Proposed contract:

```toml
[capture]                 # instead of flow = "flow.yaml"
build   = "xcodebuild build-for-testing -scheme MyApp -destination 'generic/platform=iOS Simulator' -derivedDataPath build"   # once
command = "xcodebuild test-without-building -xctestrun build/Build/Products/MyApp.xctestrun -destination id=$SHOTFLEET_DEVICE -testLanguage $SHOTFLEET_LANGUAGE -testRegion $SHOTFLEET_REGION -resultBundlePath $SHOTFLEET_OUT/run.xcresult"
```

Env per language and device: `SHOTFLEET_LOCALE` (app locale, `pt-BR`), `SHOTFLEET_LANGUAGE` / `SHOTFLEET_REGION` (`pt` / `BR`),
`SHOTFLEET_DEVICE` (simulator UDID or emulator serial; also `ANDROID_SERIAL` on Android), `SHOTFLEET_OUT` (an empty folder for this
language; PNGs written here are the screenshots). Same names the hooks already use (`SHOTFLEET_OUT`, `SHOTFLEET_PLATFORM`).

Getting the screenshots without changing the user's tests:
- iOS: `xcodebuild` has `-testLanguage`, `-testRegion` and `-xctestrun` for `test-without-building` [M: `xcodebuild -help`, Xcode
  27.0]. Screenshots come out of the result bundle with `xcrun xcresulttool export attachments` [M: the subcommand exists on Xcode
  27]. That catches every `XCTAttachment` screenshot. INFERENCE: fastlane's `SnapshotHelper` writes PNGs to a cache folder; whether
  it also attaches them needs experiment E5.
- Android: shotfleet already sets emulator locales. The command is screengrab's own mechanism: `adb shell am instrument -w -e
  testLocale de_DE ...` or `./gradlew connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.testLocale=de_DE`
  (`LocaleTestRule` reads `testLocale`, `runner.rb` line 270), then `adb pull` of screengrab's device folder
  `.../files/screengrab/<locale>/images/screenshots` (`runner.rb` lines 143-163). INFERENCE: Gradle's install/uninstall per run makes
  parallel Gradle runs heavy; `am instrument` on prebuilt APKs is the lighter path.
- Any tool: whatever the command writes into `$SHOTFLEET_OUT`.

Value: medium-high for teams with UI tests and many languages (parallel languages and the gate). Effort: L, 4-6 agent days plus
device time; the round loop in `ios_run_inner` / `android_run_inner` is woven into the Maestro calls and has to be pulled apart.
Risk: medium-high: Xcode and Gradle drift becomes ours to support, and parallel `xcodebuild` processes are memory hungry (the
budget `plan_capacity` already handles). No selector rewriting: the user's tests must already work in every language.

### (b) First-class fastlane integration (check as the gate after snapshot/screengrab)

Most of the value exists: `check` runs on snapshot output and found a real bug [M]. Missing:
1. screengrab timestamps give false "missing" problems [M]. Fix: compare names with a trailing `_\d{13}` removed.
2. A ready lane in the docs: `snapshot` or `screengrab`, then `sh("shotfleet check ...")`, then `deliver`/`supply`. A non-zero
   exit stops the lane. README already covers CI and `--json`.
3. `export` is not needed by fastlane users: their tools already write into fastlane's folders. Say that instead of building
   `export` for supply folders.
4. `check fastlane/` without `--app` could find the build the way `init` does (`find_builds`, `derived_apps`, `gradle_apks`), so the
   full string comparison is on by default.
5. Tests with real names, so the claim is proven.

Value: the biggest reach (section 3), no direct revenue because `check` is free. It is the funnel: a free check that finds a real
bug in a fastlane set is the best ad for paid `run`. Effort: S, half a day to a day. Risk: low.

### (c) Paparazzi and other no-device renderers

Paparazzi (layoutlib on the JVM), Roborazzi (Robolectric), Compose Preview Screenshot Testing (`@Preview` plus a Gradle plugin),
swift-snapshot-testing (renders a view in a host app). Fast and cheap, no emulator. Language is set in test code: Paparazzi
`DeviceConfig.PIXEL_5.copy(locale = ...)`, Robolectric `@Config(qualifiers = "de")`, Compose `@Preview(locale = "de")`,
swift-snapshot-testing through the SwiftUI environment locale or the test scheme's language (INFERENCE from the libraries' docs,
not run).

Do the stores accept them?
- Apple 2.3.3: "Screenshots should show the app in use, and not merely the title art, login page, or splash screen."
  [W https://developer.apple.com/app-store/review/guidelines/]. Nothing asks for a real device or a status bar. Pixel sizes must
  match a display class, which a snapshot test can be set to (INFERENCE).
- Google: screenshots "must demonstrate the actual in-app or in-game experience", no device frames, and remove excess elements of
  the notification bar [W https://support.google.com/googleplay/android-developer/answer/9866151]. A render without a status bar
  is, if anything, closer to that.
- INFERENCE: acceptable to both stores as long as they show real app screens. The real differences: no or fake system bars,
  layoutlib fonts and text shaping can differ from a device (worst for CJK, Arabic, Indic), no real data, no system dialogs.

Could `check` validate them? Yes, once they are in `<locale>/` folders: OCR and store rules work on any PNG. Two gaps: the flat
layout and (INFERENCE) the alpha channel. Value: medium, mostly Android teams. Effort: S for docs (a copy loop into `<locale>/`
folders), S-M for a `--locale-from` option. Risk: low.

### (d) Selector rewriting for XCUITest/Espresso code

Not worth building:
- Test code is compiled. Rewriting `app.buttons["Next"]` per language means a source copy and a build per language, exactly the
  slowness people dislike in snapshot.
- Swift and Kotlin string literals are not marked as selectors the way Maestro's `tapOn:` values are. A rewriter would have to guess
  which literals to touch (logs, assertions, test data) and would break code.
- Teams that write UI tests mostly use accessibility identifiers or view ids (`app.buttons["onboarding.next"]`,
  `withId(R.id.next)`), which don't change per language. The problem mostly doesn't exist for them.
- When they do match text, their language already has the answer: look the string up in the app bundle (`NSLocalizedString(...,
  bundle:)`, `getString(R.string.next)`).

Selector rewriting stays Maestro's selling point: "no test code, one English flow".

## 3. Market

| Signal | Number | Tag |
|---|---|---|
| GitHub stars, fastlane/fastlane | 42,206 | [M] `gh api`, 2026-10-06 |
| GitHub stars, mobile-dev-inc/Maestro | 15,952 | [M] |
| GitHub stars, appium/appium / wix/Detox | 22,047 / 12,033 | [M] |
| GitHub stars, pointfreeco/swift-snapshot-testing | 4,362 | [M] |
| GitHub stars, cashapp/paparazzi / takahirom/roborazzi | 2,632 / 1,057 | [M] |
| fastlane gem downloads, all time / latest version (2.240.1) | 215,152,376 / 724,512 | [M] rubygems.org API |
| Homebrew installs of fastlane, last 365 days | 145,610 | [M] formulae.brew.sh API. Maestro isn't in Homebrew core (it installs by curl), so no comparable number |
| State of React Native 2025, E2E tools used (728 answering) | Maestro 45.7%, Detox 25.6%, Appium 17.9% | [W] https://results.2025.stateofreactnative.com/en-US/testing-and-monitoring/ (read through a summarizer; the 2024 URL returned the same figures, so the year is unconfirmed) |
| Native iOS/Android teams using XCUITest/Espresso | no public survey found | XCUITest and Espresso ship with Xcode and Android Studio, so they are the default |

INFERENCE:
- Among React Native and Expo teams, Maestro is now the most used E2E tool. Among native teams, XCUITest/Espresso dominate and
  Maestro is a growing minority.
- For store screenshots, fastlane snapshot/screengrab is the default path. fastlane's audience is about 2.6x Maestro's by stars and
  far larger by downloads (most fastlane downloads are CI upload jobs, not snapshot).
- Maestro-only `run` does limit sales, but less than it looks: the buyer of `run` is someone who does not want test code, and
  Maestro's "YAML, no code" is that buyer. The group shotfleet loses is teams with working UI tests and 10+ languages, who would
  pay for parallel languages plus the gate (option a). Today they can only use the free `check`.

## 4. Recommendation

1. **First: make `check` first-class for fastlane (b) and cover Paparazzi by docs (part of c).** About a day. Fixes a false claim
   (screengrab), makes the biggest audience free users of `check`, and every true positive like the subscrifi German set sells `run`.
2. **Second: BYOC for iOS (a), under the licence**, once fastlane users show up and ask for speed. iOS first because
   `-testLanguage` + `test-without-building` + `xcresulttool` need no change to the user's tests. 4-6 days plus device time.
3. **Third: Android BYOC**, after iOS BYOC proves people use it.
4. **Never: selector rewriting for test code (d).**

Site wording (informal, first person, no em dashes). The first line is true today; the rest only after item 1 ships.

- Today, home page near the free tier (index.html:338) and docs:
  "`run` needs Maestro. `check` doesn't. Already use fastlane snapshot? `check` works on those screenshots, and it's free."
- After item 1, home page:
  "Already use fastlane snapshot or screengrab? `check` works on those screenshots, and it's free. Point it at your fastlane folder and your app build."
- After item 1, alternatives.html, end of the fastlane section:
  "You don't have to pick one. If your fastlane UI tests already run in every language, keep them and run `shotfleet check` on the folder they write. It tells you which languages show the wrong strings, which are copies and which miss a screen. I ran it on a real fastlane snapshot set and it found a German listing whose app was still in English."
- After experiment E3, docs.html under "Check screenshots you already have":
  "Paparazzi, Roborazzi or Compose preview tests work too. Put each language's images in its own folder (`de/`, `ja/`) and run `check` on the parent folder. Those tools draw your screens without a device, so there's no real status bar. Both stores accept that as long as the screens show your app."

Don't say "any tool" (the claims audit removed that once already), and don't claim Paparazzi before a real Paparazzi folder passes.

## Build plan

### (1) First changes, concrete

**Item 1: `check` reads screengrab and snapshot names right (S, about 3 hours).**
- `shotfleet.py`: add `shot_key(name)` next to `find_screenshots`; it strips a trailing `_\d{13}` (screengrab's millisecond
  timestamp) before the extension. Use it in `cmd_check` where `names` and `have` are built (the "missing" rule) and in the
  `[expect.<shot>]` lookup (`png.stem in expect`), so `[expect.01Home]` matches `01Home_1773697012807.png`. Reports keep the real
  file names. No CLI change.
- Tests in `tests/test_shotfleet.py` (class `CheckAnyFolder`): `screenshots/de-DE/iPhone 15 Pro Max-01Home.png` with
  `screenshots.html` beside it; `metadata/android/{en-US,de-DE}/images/phoneScreenshots/01Home_<different 13 digits>.png` gives no
  "missing" problem; a screen that is really missing is still reported. Add both tests as proof to the existing claims.json entry.

**Item 2: fastlane as a documented path, with `--app` found by default (S, about 4 hours).**
- `shotfleet.py`: in `check_any`, with no `--app`/`--strings` and no `run.json`, call `find_builds(Path.cwd())` (what `init` uses,
  never builds) and print "using <build> for strings (pass --app to choose another)". If it finds both platforms, pick by layout as
  `cmd_check` already does. Keep today's language-detection note when nothing is found.
- Docs: README "Check screenshots you already have" gets a Fastfile lane (`snapshot`, `sh("shotfleet", "check", ...)`, `deliver`),
  a line that `export` is for shotfleet runs and fastlane users don't need it, and that screengrab's timestamps are fine. Same in
  docs.html; site sentences from section 4; alternatives.html fastlane paragraph.
- Tests: `tests/test_docs.py` / `test_claims_site.py` cover the new claims; a unit test that `check_any` picks a DerivedData app from
  a temp tree (reuse fixtures from `tests/test_setup_discovery.py`).

**Item 3: Paparazzi/Roborazzi folders (S now, S-M later).**
- Now: docs only (a copy loop into `<locale>/`), and the transparency problem line in `store_rules` gets a fix hint ("save it
  without an alpha channel, e.g. `sips -s format jpeg`").
- Only if asked: `check --locale-from REGEX` with a named group `locale` (e.g. `'_(?P<locale>[a-z]{2}(?:-[A-Z]{2})?)\.png$'`) in
  the flat branch of `find_screenshots`, plus a test with Paparazzi-style names.
- Before any claim: experiment E3 (one real Paparazzi PNG: colour type and names).

**Item 4, after 1-3 and only on demand: BYOC for iOS (L, 4-6 days).**
- Config: `[capture] build` and `command` (section 2a); `flow` optional when `[capture]` is set (`load_config`, `check_section`).
- `shotfleet.py`: split the round scheduler out of `ios_run_inner` (pool, per-language rounds, `run_guarded` with `stall_s`, retry,
  `collect_shots`) so the per-language step is a function: the Maestro step or a command step. New `xcresult_pngs(bundle, dst)` that
  calls `xcrun xcresulttool export attachments`. `doctor` stops requiring Maestro when the config has `[capture]`.
- Tests: env building, command templating, attachment collection from a canned export folder. Experiments E4 and E5 before release.
- Licence: same as `run`.

Correction to the candidates named in the scope: making fastlane output first-class for **export** isn't needed (fastlane already
writes those folders); first-class for `check` is the work. Paparazzi needs only docs until someone asks.

### (2) Other big limitations seen while reading

Already covered elsewhere (not repeated): Apple silicon only and Intel (workarounds-reach-distribution: "No", revisit at 3 asks);
older macOS (limits-platform-reach: build from python-build-standalone); Linux CI for `check` (limits-platforms 1a and
workarounds-reach-distribution item 3: a GitHub Action, `check` first); Android API 33 floor (limits-platforms 4: not worth it); OCR
scripts macOS can't read (workarounds-text-recognition; the Tesseract fallback is in code now); 7" tablets (limits-platforms 2b).

New from this read:
- **`check` has only OCR for screenshots it didn't take.** Fix: it already reads a `<shot>.texts.json` beside any PNG (`screen_text`);
  document the format so XCUITest/Espresso users can dump their screen's labels next to each screenshot. Exact text in every script
  for free; docs plus one test.
- **The alpha rule fires on any RGBA PNG, opaque or not.** Common from XCUITest attachments, Paparazzi and design tools. Keep it a
  problem (stores reject alpha channels) but say how to fix it in the same line.
- **Non-Maestro teams have nothing to pay for.** `check` (their whole value) is free; paid `run` is Maestro only. Fix: BYOC under the
  licence (item 4).
- **`export` can't take a supply folder or JPEGs made elsewhere** (comment in `cmd_export`). Fix: say so and don't build it; with
  BYOC, shotfleet writes `run.json` and the normal path works.
- **One config means one capture tool.** A team with Maestro on iOS and Espresso on Android needs two configs. Fix: `[capture]` per
  platform section once BYOC exists.
- **Free tier is 2 languages per run**, which can't show the copy/wrong-language catch at scale. Not changed here; `check` being free
  on existing fastlane sets is a stronger demo than a bigger free tier.

### (3) Device experiments, with time and hard limits

All under the device lock in `docs/device-queue.md`, one at a time, only when the 1-minute `vm.loadavg` is under 300, each with a
per-step kill limit and a progress check (the "hard limits on lock-holding jobs" rule). Only kill or delete what the experiment
started (simulators named `shotfleet*`, emulators it booted).

| # | Proves | Steps | Time | Hard limits |
|---|---|---|---|---|
| E1 | Item 1 on real output | no device: rerun `check` on scratch copies of subscrifi's screengrab and snapshot folders after the fix | 10 min | load < 300; scratch copies only, never the projects' folders |
| E2 | Item 2 build discovery | run `check` inside a project with a DerivedData app and a debug APK present | 15 min, no device | read only; nothing is built |
| E3 | Paparazzi colour type and names | throwaway Android module, one Paparazzi test in 2 locales, `./gradlew recordPaparazziDebug --no-daemon` (JVM only), then `check` | 45 min | no emulator; 20 min kill on the Gradle step; in scratch |
| E4 | BYOC iOS contract | fixture app with 2 XCUITest screenshots; `build-for-testing` once; `test-without-building -testLanguage de` and `ja` on 2 simulators at once; `xcresulttool export attachments`; `check` | 2 h | device lock; 2 simulators max; 15 min kill per `xcodebuild`; stall check every 2 min (new PNG or log line) |
| E5 | SnapshotHelper screenshots land in the xcresult | subscrifi's UI test, 1 language, 1 simulator, `-resultBundlePath` in scratch | 45 min | device lock; 1 simulator; 20 min kill; project files untouched |
| E6 | BYOC Android contract | fixture APK + test APK, `adb shell am instrument -e testLocale de_DE` on 1 then 2 emulators, `adb pull` of the screengrab folder | 2 h | device lock; second emulator only on 4+ cores; 15 min kill per instrument call |

Effort summary: items 1-3 about 1.5 agent days with E1-E3 (no device). Item 4 about 4-6 days plus E4-E5 (about 3 h of device time).
Android BYOC another 3-4 days plus E6.

## Sources

- fastlane snapshot language loop: https://github.com/fastlane/fastlane/blob/master/snapshot/lib/snapshot/simulator_launchers/simulator_launcher.rb
- screengrab runner and timestamp: https://github.com/fastlane/fastlane/blob/master/screengrab/lib/screengrab/runner.rb ,
  https://github.com/fastlane/fastlane/blob/master/screengrab/screengrab-lib/src/main/java/tools.fastlane.screengrab/FileWritingScreenshotCallback.java
- Paparazzi naming: https://github.com/cashapp/paparazzi/blob/master/paparazzi/src/main/java/app/cash/paparazzi/Snapshot.kt ,
  https://github.com/cashapp/paparazzi/blob/master/paparazzi/src/main/java/app/cash/paparazzi/SnapshotVerifier.kt
- Apple App Review Guidelines 2.3.3: https://developer.apple.com/app-store/review/guidelines/
- Google Play preview assets: https://support.google.com/googleplay/android-developer/answer/9866151
- State of React Native 2025, testing: https://results.2025.stateofreactnative.com/en-US/testing-and-monitoring/
- fastlane snapshot slowness: https://github.com/fastlane/fastlane/issues/15938
- Stars: `gh api repos/<owner>/<repo>`; downloads: https://rubygems.org/api/v1/gems/fastlane.json , https://formulae.brew.sh/api/formula/fastlane.json
