# Bring your own capture on iOS: experiments E4 and E5 (2026-10-06)

Question (from research/beyond-maestro-2026-10-06.md, option (a) and Build plan item 4): can shotfleet run a team's existing
XCUITest screenshot tests on several iOS simulators at once, one language per simulator, without changing their test code, and
then collect and check the screenshots?

Tags: **[M]** measured here today, **INFERENCE** = my estimate, not proven. Xcode 27.0 (27A266a), iOS 26.4 runtime, iPhone 17
Pro Max simulators, macOS 27 on the shared Mac. `check` was run from source at origin/main aca9dd6. No change to `shotfleet.py`.
Evidence lives in `~/Developer/shotfleet-rc-build/byoc-ios/` (fixture, logs, result bundles, collected PNGs, check reports,
RESUME.md with the timeline).

## Answer: GO, with two corrections to the contract in the beyond-maestro note

Yes [M]. On a fixture app, 2 simulators ran the same prebuilt test bundle at the same time, one in German and one in Japanese,
and the screenshots came back in the right language and passed `check`. On a real project (subscrifi) the unchanged fastlane
`SnapshotHelper` test ran on a shotfleet-style simulator and its 12 screenshots were collected and checked; `check` found a real
bug in them.

The two corrections:

1. **`-testLanguage` / `-testRegion` do not work with `test-without-building -xctestrun`** [M]. The run passes and the
   screenshots are English. Setting `TestLanguage`/`TestRegion` in the `.xctestrun` file does nothing either [M]. What works:
   setting the simulator's own language with `simctl spawn <udid> defaults write -g AppleLanguages/AppleLocale` (no reboot needed)
   [M]. So shotfleet sets the language itself, the way it already owns the pool; the user's command must not be trusted to do it.
2. **fastlane's `SnapshotHelper` never attaches screenshots to the result bundle** [M]. It writes PNGs to the Mac user's
   `~/Library/Caches/tools.fastlane/screenshots/<simulator name>-<shot>.png`, one folder shared by every simulator, and only if
   that folder already exists. So shotfleet needs two collectors: result-bundle attachments and the fastlane cache folder.

## E4: the contract on a fixture

### Fixture [M]

`byoc-ios/e4/fixture`: shotfleet's own `tools/fixture-app/App.swift` (en/de/ja strings copied from `tools/fixture-app/Resources`),
with one change, `.accessibilityIdentifier("primary")` on the button, plus an XCUITest target generated with xcodegen
(`project.yml`). The test is what a team would write, with no shotfleet code:

```swift
func testScreenshots() {
    let app = XCUIApplication(); app.launch()
    snap("01Welcome"); app.buttons["primary"].tap(); snap("02Settings")
}
private func snap(_ name: String) {
    let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot()); a.name = name; a.lifetime = .keepAlways; add(a)
}
```

### Commands that worked [M]

```sh
# once, no device (20 s, load 27)
xcodebuild build-for-testing -project Fixture.xcodeproj -scheme FleetFixture \
  -destination 'generic/platform=iOS Simulator' -derivedDataPath build
#   -> build/Build/Products/FleetFixture_iphonesimulator27.0-arm64-x86_64.xctestrun

# per simulator (names unique to the run; never reuse someone else's)
xcrun simctl create byoc-e4-de com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max com.apple.CoreSimulator.SimRuntime.iOS-26-4
xcrun simctl boot $UDID && xcrun simctl bootstatus $UDID
xcrun simctl spawn $UDID defaults write -g AppleLanguages -array de      # the language, before each test run; no reboot
xcrun simctl spawn $UDID defaults write -g AppleLocale -string de_DE

# per language, all simulators at once (each its own result bundle)
xcodebuild test-without-building -xctestrun "$XCTESTRUN" -destination "id=$UDID" -resultBundlePath runs/de.xcresult

# collect
xcrun xcresulttool export attachments --path runs/de.xcresult --output-path att-de --filter '*.png'
```

`export attachments` writes `<UUID>.png` files plus `manifest.json`; the screenshot's name is in
`attachments[].suggestedHumanReadableName` as `<XCTAttachment.name>_<index>_<UUID>.png` (`01Welcome_0_17023C40-....png`), and
`deviceName`/`deviceId` say which simulator took it. Stripping `_<n>_<UUID>` gives `01Welcome.png`. The collector used here
(`byoc-ios/e4/collect.py`, 20 lines) writes `<locale>/<name>.png`. The PNGs are 1320x2868, no alpha channel, so the alpha
concern from the beyond-maestro note does not apply to XCUITest attachments.

### What did not set the language [M]

| Way | Result |
|---|---|
| `test-without-building -xctestrun X -testLanguage de -testRegion DE` | exit 0, screenshots English |
| a copy of the `.xctestrun` with `TestLanguage = de`, `TestRegion = DE` | exit 0, English |
| `test-without-building -project ... -scheme ... -derivedDataPath build -testLanguage de` | **German** (works in scheme mode only) |
| a copy of the `.xctestrun` with `UITargetAppCommandLineArguments = [-AppleLanguages, (ja), -AppleLocale, ja_JP]` | **Japanese** |
| simulator global prefs (`defaults write -g` through `simctl spawn`), no reboot | **German / Japanese** |

New simulators inherit the Mac's languages (`en-NL`, `nl-NL` here), so without any of the working ways an app with no Dutch
falls back to English and the run still passes. The global prefs are the one way that does not depend on how the team's test
launches the app (`UITargetAppCommandLineArguments` only reaches the scheme's target app; INFERENCE: a test that launches with
`XCUIApplication(bundleIdentifier:)`, as subscrifi's does, would not get it).

### `check` on the collected folders [M]

`python3 shotfleet.py check <folder> --app build/.../FleetFixture.app` (macOS text recognition was still compiling under load, so
Tesseract read the screens):

- Parallel run, global prefs: `checked 4 screenshots in 2 languages: 2 problem(s)`; every screen confirmed `de`/`ja` by OCR; the 2
  problems are the true "the app runs on iPad, so the App Store requires 13" iPad screenshots" (xcodegen's default device family).
- Sequential run on one simulator: same result.
- The first run (`-testLanguage`, English screens): `shows en strings ... more than de/ja` on 3 screens and `identical image in 2
  languages` twice. So `check` catches exactly the silent failure of correction 1.

### Timings [M]

Load was high the whole time from other projects (1-minute load 150 at start, 490-900 during the runs; free memory 61 %), so the
numbers are noisy. The test itself runs 4-6 s; each `xcodebuild` call adds about 5 s.

| Step | Time |
|---|---|
| `build-for-testing` (once) | 20 s |
| create + boot 2 simulators | 62 s |
| first run, 2 simulators in parallel, cold (installs the app) | 45 s |
| warm, 2 languages: parallel on 2 simulators vs one after the other on 1 simulator (3 rounds) | 15 / 11 / 16 s vs 19 / 17 / 25 s |

Parallel is about 1.5x faster for 2 languages on this tiny test, mostly fixed `xcodebuild` cost. INFERENCE for a real suite:
subscrifi's test takes about 120 s per language, so 8 languages are about 16 min one after the other and about 4-5 min on 4
simulators in 2 rounds, which is the pitch against fastlane snapshot's language-after-language loop.

## E5: a real project's existing test (subscrifi)

Worked on a scratch copy only (`byoc-ios/e5/subscrifi`, rsync without build folders); the subscrifi repo was not modified (only
`xcodebuild -list` was run in it; file times checked afterwards).

### What it took to build [M]

1. RevenueCat 5.67.0 (pinned in `Package.resolved`) does not compile with Xcode 27 (`invalid redeclaration of synthesized
   memberwise 'init(stringRepresentation:)'`). In the copy I deleted `Package.resolved`, which resolved 5.92.0.
2. `generic/platform=iOS Simulator` builds x86_64 too, and the Kotlin Multiplatform `shared.framework` is arm64 only: link error.
   Fix: `ARCHS=arm64`.
3. The Snapfile's scheme `iosApp` is a personal scheme with no test target: `There are no test bundles available to test` (exit
   70). The shared scheme `iosApp-shared` has `SubscribiUITests`.
4. Moving the `.xctestrun` out of `Build/Products` breaks it (`__TESTROOT__` is relative to the file): exit 70.

Working build (first full build with Gradle about 5 min, the final incremental one 90 s):

```sh
xcodebuild build-for-testing -project Subscribi.xcodeproj -scheme iosApp-shared \
  -destination 'generic/platform=iOS Simulator' -derivedDataPath ../../dd CODE_SIGNING_ALLOWED=NO ARCHS=arm64
```

### Where SnapshotHelper's screenshots go [M]

- Result bundle: `export attachments` gives an empty manifest. `SnapshotHelper.snapshot()` only writes a file; it never calls
  `XCTAttachment`.
- The file goes to `$SIMULATOR_HOST_HOME/Library/Caches/tools.fastlane/screenshots/<SIMULATOR_DEVICE_NAME>-<name>.png`. The
  simulator sets `SIMULATOR_HOST_HOME` to the Mac user's home. Overriding it failed both ways I tried:
  `TEST_RUNNER_SIMULATOR_HOST_HOME=...` and `TestingEnvironmentVariables.SIMULATOR_HOST_HOME` in the `.xctestrun` copy.
- If that folder doesn't exist (fastlane creates it), every `snapshot()` logs `Problem writing screenshot` and **the test still
  passes**. My first 2 runs passed with 0 files.
- With the folder created first: 12 files, `byoc-e5-de-01Home.png` ... `byoc-e5-de-12PriceHistory.png`, 1320x2868, no alpha.
  I moved them out and removed the folder I had created (it did not exist before).
- `SnapshotHelper` also reads `language.txt`, `locale.txt` and `snapshot-launch_arguments.txt` from that folder and adds
  `-AppleLanguages` from them. They were absent, so it logged "Couldn't detect/set language" and the simulator's global language
  applied. A leftover `language.txt` from an earlier fastlane run would force that language on every simulator.

Run (simulator language set to de by global prefs): `xcodebuild test-without-building -xctestrun
iosApp-shared_iosApp-shared_iphonesimulator27.0-arm64.xctestrun -destination id=$UDID -resultBundlePath runs/de3.xcresult`, exit 0
in 121 s (the test 114 s).

### `check` on it, and a real bug [M]

Collected as `de-DE/<name>.png` (simulator-name prefix stripped), `check --app dd/.../Subscribi.app`: `checked 12 screenshots in 1
languages: 14 problem(s)`. Every screen `shows en strings (N lines) more than de (0)`, plus 12 > 10 per listing and the iPad
rule. The screenshot shows English app text with German system parts ("Mehr" tab, `107,88 $`), the same thing the beyond-maestro
note found in the fastlane-made set. Cause, read in the copy: `iosApp/Helpers/LocalizationHelper.swift` picks the strings bundle
from `UserDefaults "selectedLanguage" ?? "en"`. So a fresh install on a German phone shows English until the user picks a language
in Settings. A true positive, and a bug for the subscrifi owner (not fixed here, read only).

## Snags, in one list

1. `-testLanguage`/`-testRegion` and the `.xctestrun` `TestLanguage` key are ignored by `test-without-building -xctestrun` on
   Xcode 27.0; the run passes in the Mac's language. Set the simulator's global language instead.
2. New simulators get the Mac's language list (`en-NL`, `nl-NL`).
3. `defaults write -g` through `simctl spawn` takes effect on the next app launch; no reboot (shotfleet can switch language between
   rounds on the same simulator).
4. Attachment files come out as `<UUID>.png`; names are in `manifest.json` (`suggestedHumanReadableName`, `_<n>_<UUID>` suffix).
5. Only attachments with `lifetime = .keepAlways` are exported for passing tests (the `.xctestrun` has `SystemAttachmentLifetime =
   deleteOnSuccess`, so XCTest's automatic screenshots are dropped). A team that uses `XCTAttachment` without `.keepAlways` gets
   nothing on success. INFERENCE from the default; not run without `.keepAlways`.
6. `SnapshotHelper` writes only to the Mac user's fastlane cache folder, shared by all simulators, must pre-exist, can't be
   redirected, and fails silently. Its file names start with the simulator name, so unique simulator names per slot keep parallel
   runs apart.
7. A leftover `language.txt` in that folder overrides the language for every simulator.
8. Real projects drift with Xcode: a pinned package that no longer compiles, x86_64 in the generic simulator destination vs an
   arm64-only KMP framework, a personal scheme without tests. The build command has to stay the team's own.
9. The `.xctestrun` must stay next to its products.
10. A passing test is no proof of screenshots (snags 1 and 6): shotfleet must count what it collected per language and fail on a
    missing screen. `check` already flags wrong language and copies.

## Design for the shotfleet feature

### Config

```toml
[capture]                 # instead of flow = "flow.yaml"; one of the two
build = "xcodebuild build-for-testing -scheme MyApp-shared -destination 'generic/platform=iOS Simulator' -derivedDataPath .shotfleet/build ARCHS=arm64"
xctestrun = ".shotfleet/build/Build/Products/*.xctestrun"   # glob, exactly one match after the build
only_testing = ["MyAppUITests/ScreenshotTests"]             # optional, passed as -only-testing
screenshots = "auto"      # "attachments" | "fastlane" | "auto" (both)
timeout = 900             # per language, seconds; the existing stall guard still applies
```

`device_type`, `runtime`, `locales`, `out`, `parallel`, `[setup]` hooks stay as they are. `bundle_id` and `app` are not needed for
capture; `app` stays optional for `check`'s string comparison (default: the `.app` next to the `.xctestrun`, found from its
`UITargetAppPath`). Validation in `load_config`/`check_section`: `[capture]` and `flow` are mutually exclusive, `build` and
`xctestrun` are required, `screenshots` is one of the three values.

No free-form test `command` in the first version: shotfleet runs `xcodebuild test-without-building` itself, because the language
(snag 1) and the collection (snag 6) only work when shotfleet controls the run. Add a `command` escape hatch later if someone needs
a wrapper.

### CLI

No new command. `shotfleet run` sees `[capture]` and runs the build once (skipped with `--no-build`), then the usual pool and
rounds. `--only`, `--parallel`, `check` after the run and `export` are unchanged, because shotfleet writes `raw/<locale>/` and
`run.json` as it does today. `shotfleet init --capture` writes a `[capture]` block from the schemes it finds (`xcodebuild -list`,
prefer a shared scheme with a UI test target), and `doctor` stops requiring Maestro when the config has `[capture]`.

### How the language is passed

Per round, for each simulator and its language, before the test run:

```sh
xcrun simctl spawn $UDID defaults write -g AppleLanguages -array <lproj>      # e.g. pt-BR
xcrun simctl spawn $UDID defaults write -g AppleLocale -string <locale>       # e.g. pt_BR
```

Plus a per-run copy of the `.xctestrun` beside the original (it must stay in `Build/Products`) with
`UITargetAppCommandLineArguments += [-AppleLanguages, (<lproj>), -AppleLocale, <locale>]`. This is the same pair `run` already gives
Maestro (`shotfleet.py` line ~1099), and it covers an app that ignores the global prefs. `-testLanguage` is not used.

### Where screenshots are collected from

After each language's run, into `out/raw/<locale>/`:

- **attachments**: `xcresulttool export attachments --path <bundle> --output-path <tmp> --filter '*.png'`, names from
  `manifest.json` with `_<n>_<UUID>` stripped. On a name clash (one test case attaches the same name twice) keep both, numbered,
  and warn.
- **fastlane**: before the run, create `~/Library/Caches/tools.fastlane/screenshots` if missing and move `language.txt`,
  `locale.txt` and `snapshot-launch_arguments.txt` aside (restore them at the end, also on Ctrl-C). After the run, take
  `<simulator name>-*.png` for that simulator only and strip the prefix. Remove the folder at the end only if shotfleet created it.
  The device lock already keeps a second run from sharing the folder.
- Then count: a language with 0 screenshots, or fewer names than the union across languages, fails the run (snag 10) with the
  hint "the test passed but saved no screenshots: XCTAttachment needs lifetime = .keepAlways; SnapshotHelper needs ...".

### Licence

Paid, same as `run`: `require_licence()` before the first device boots, and the same free tier (2 languages per run without a
licence). `check` stays free. This is the first paid product for teams that don't use Maestro (beyond-maestro note, "Non-Maestro
teams have nothing to pay for").

### Code shape

Split the round loop out of `ios_run_inner` so the per-language step is a function: today's Maestro step, or the new capture
step (`capture_step(sim, locale, cfg) -> list[Path]`: write prefs, write the `.xctestrun` copy, `run_guarded(xcodebuild ...)`,
collect). New small helpers: `xcresult_pngs(bundle, dst)`, `fastlane_cache_pngs(sim_name, dst)`, `xctestrun_with_language(src,
lproj, locale)`. Simulator names must stay unique per slot (they are: `shotfleet-<device>-N`).

### Tests to write

Unit, no device (`tests/test_shotfleet.py`):
- config: `[capture]` without `flow` loads; both, or neither, is an error; bad `screenshots` value is an error.
- `xcresult_pngs` on a canned export folder (a `manifest.json` from this experiment plus 2 tiny PNGs): names stripped to
  `01Welcome.png`, files copied, a duplicate name kept with a warning (`subprocess` faked).
- `fastlane_cache_pngs`: takes only this simulator's prefix, strips it, ignores other simulators' files.
- the fastlane folder guard: `language.txt` moved aside and restored, also when the step raises; a folder that existed is not
  removed.
- `xctestrun_with_language`: the copy sits beside the original, has the arguments, works for format 1 and format 2 files (both seen
  here).
- the prefs commands per locale (`pt-BR` -> `AppleLanguages (pt-BR)`, `AppleLocale pt_BR`).
- the "0 screenshots" and "missing name" failures with their hints.
- licence: a `[capture]` run with 3 languages and no licence is refused like a Maestro run; 2 are allowed.
- `doctor` with `[capture]` does not ask for Maestro.
- claims: a `tests/claims.json` entry only after the e2e below passes.

End to end, opt-in, on devices (`tools/fixture-byoc-e2e.sh`, under the device lock): add the XCUITest target to
`tools/fixture-app` (a `project.yml` like `byoc-ios/e4/fixture`), run `shotfleet run` with `[capture]` in de/ja/ar/tr on 2
simulators, expect `check` to pass, then run once with a fake `xctestrun` copy that forces English and expect `check` to report the
wrong language. One more variant with a `SnapshotHelper`-style test to cover the fastlane collector.

### Effort

About 3-4 agent days plus 1-2 h device time for the e2e, a little under the 4-6 days estimated, because the experiment settled
the unknowns (language, collection, names). Android BYOC (E6) is separate.

## Device use

Lock held 18:36-18:59 (23 min, hard limits 60 + 45 min not reached); quiet check passed at the start (free 61 %, load 153, disk 77
GB free). Simulators used: `byoc-e4-de`, `byoc-e4-ja`, `byoc-e5-de`, all shut down and deleted; no other device touched.
