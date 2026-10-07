# Troubleshooting shotfleet

Find the message with `grep -n "<fragment>"` here. Errors that stop a command print `shotfleet: <message>` on stderr
and exit 2. The first column holds the fixed part of the message (names and numbers vary); each fragment is a
message the program prints. Run `shotfleet doctor` first for anything about tools.

## Tools (doctor and every run)

`shotfleet doctor` prints `ok` or `MISSING <tool> (<platform>)  -> <fix>` per tool, then `iOS: ready|not ready  Android: ready|not ready`.

| Tool | Needed for | Fix |
|---|---|---|
| maestro (tested with 2.0.10 and 2.11.0) | run | `curl -Ls https://get.maestro.mobile.dev \| bash`. Maestro 1.x is refused by doctor. Another 2.x prints a one-line note in `doctor` and at the start of `run` (it may work). `shotfleet doctor --fix` installs 2.11.0. |
| java 17+ | Maestro | `brew install openjdk@21`. shotfleet finds Homebrew's Java itself (it is keg-only, so `java` is not on PATH); do not edit the user's shell profile. |
| xcrun simctl | iOS | install Xcode and an iOS Simulator runtime |
| iOS Simulator runtime | iOS | `xcodebuild -downloadPlatform iOS` (or Xcode > Settings > Components); `doctor` shows the newest one it found |
| adb, emulator, avdmanager, aapt2, system image | Android | run the `sdkmanager` commands that `doctor` prints under `Android: to install what is missing` (it uses the sdkmanager that exists, or installs Homebrew's `android-commandlinetools` first). The SDK is found in `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `~/Library/Android/sdk`, Homebrew's `android-commandlinetools`, or beside an `adb` on the PATH; `doctor` prints `Android SDK:` with the one it chose. Any installed arm64 `google_apis` or `google_apis_playstore` image of API 33 or newer counts; an existing `shotfleet_android` emulator needs none. |
| text recognition | check | first use after a restart compiles macOS's model: about 30 s on a quiet Mac, 127 s measured on a loaded one, up to a few minutes. `doctor` prints `...  text recognition` first and the time after. Wait; do not kill it. |

## Setup errors (exit 2)

| Fragment | Cause | Fix |
|---|---|---|
| `no config at` | wrong path or no `shotfleet.toml` | `shotfleet init` (or `shotfleet init <build>`); `run` looks for `./shotfleet.toml` |
| `no Debug simulator build or Gradle debug APK found for` | `shotfleet init` with no build found none for this folder (it only reads folders: Xcode's default DerivedData for a project here, and `app/build/outputs/apk/debug`); the message lists the exact build commands | run the printed `xcodebuild` / `./gradlew assembleDebug` command, then `init` again; or pass the build path (needed when DerivedData is in a custom location) |
| `isn't valid TOML` | syntax error in the config | fix the line the message names |
| `needs an [ios] or an [android] section` | empty config | add `[ios]` with `app` or `[android]` with `apk` |
| `has an unknown table` | typo such as `[hook]`; known: ios, android, hooks, overrides, inputs, expect | use the table it suggests |
| `command failed, stopping before the run` | an `[ios] simctl` or `[android] shell` command exited non-zero; the message shows the command and its error | run that `xcrun simctl ...` / `adb shell ...` yourself on a booted device and fix it; `$UDID` is only replaced in `simctl` |
| `matches no screenshot` | an `[expect.<name>]` table names a screenshot that isn't in the folder (typo, or the flow doesn't take it) | use the name from `takeScreenshot:` (the message suggests the nearest) |
| `could not verify` | a note: `[expect]` text in a script macOS can't read, on a screen read by OCR | not a failure; give `--ocr-command` an OCR that reads it (Tesseract), or trust the iOS run, which uses the app's own text |
| `has an unknown setting` | typo in a key; the message suggests the nearest or lists all | see config.md |
| `should be a` | wrong type, e.g. `parallel = "4"` | use a whole number, string, list |
| `should be 1 or more` | `parallel = 0`, `timeout_s = 0` or `stall_s = 0` in the config | use a positive whole number |
| `is empty. Remove the line` | `locales = []` in the config | delete the line (every language the app ships) or list some |
| `should be a list of strings` | `locales`, `device_types`, `devices` or `strings` holds something other than text | `locales = ["de", "ja"]` |
| `is missing:` | `app` (iOS) or `apk` (Android) not set | set it |
| `unknown event` | bad `[hooks]` key; events are before_run, after_run, before_export, after_export | rename |
| `should be a command (a string) or a list of commands` | hook value is not text | use a string or a list of strings |
| `should map English texts to text in that language` | `[overrides.<lang>]` values are not strings | `"Next" = "Weiter"` |
| `flow file not found` | `flow` points nowhere | `shotfleet init` writes `flow.yaml` |
| `no simulator app at` | `app` is not an `.app` folder with `Info.plist` | build for the simulator, point at the `.app` |
| `is a device build` | an iphoneos build, `.ipa` or archive | `xcodebuild -scheme <Scheme> -sdk iphonesimulator -configuration Debug build`; use `Build/Products/Debug-iphonesimulator/<App>.app` |
| `an .ipa is a device build` | `.ipa` passed to init/check | pass the simulator `.app` |
| `an .aab can't be installed directly` | `.aab` passed | `./gradlew assembleDebug`, pass the `.apk` |
| `pass the simulator .app, not an archive` | `.xcarchive` passed | same as above |
| `unzip it first` | a `.zip` passed to `check --app` (`init` unpacks a `.zip`, `.tar.gz`, `.tgz` or `.tar` itself, e.g. an EAS build) | pass the `.app` or `.apk` inside |
| `unpack it first` | a `.gz` file passed to `check --app` | `tar -xzf` it, pass the `.app` inside |
| `pass a simulator .app or an .apk` | other file type | pass one of those |
| `is a folder, not an .app; did you mean` | a folder holding the `.app` was passed | pass the `.app` it names |
| `isn't a simulator app:` / `isn't an APK:` | the config's `app` or `apk` names a file or folder of the wrong kind (an `.ipa`, `.aab`, archive, the other platform's build) | follow the hint after the colon |
| `xcrun isn't available` | no Xcode (iOS runs need a Mac with Xcode) | install Xcode, or run Android only (`--platform android`) |
| `no iOS Simulator runtime is installed` | Xcode has no iOS runtime | `xcodebuild -downloadPlatform iOS` |
| `could not create simulator` | Xcode does not know the default device type or the runtime (an older Xcode has no iPhone 17 Pro Max); the message carries Xcode's reason | set `device_type` or `runtime` in the config; `xcrun simctl list devicetypes` lists the valid names |
| `builds given; a config holds one app per platform` | two `.app` or two `.apk` to `init` | run `init` once per app |
| `bundle_id is` | config `bundle_id` differs from the app's | delete the key (it is read from the app) |
| `can't read the bundle id` | broken `Info.plist` | set `bundle_id` |
| `no APK at` | wrong `apk` path | fix the path |
| `package is` | config `package` differs from the APK | delete the key |
| `can't read the package name` | aapt2 could not read the APK | set `package`, or rebuild the APK |
| `doesn't look like a valid APK` | not an APK | rebuild |
| `Maestro isn't installed` | no `maestro` on PATH | `curl -Ls https://get.maestro.mobile.dev \| bash` |
| `aapt2 not found under` | SDK Build-Tools missing | `shotfleet doctor` prints the `sdkmanager "build-tools;36.0.0"` command, or set `ANDROID_HOME` |
| `avdmanager not found under` | SDK command-line tools missing | run the `sdkmanager ... cmdline-tools;latest` command in the message |
| `don't know how to read` | `strings` file type unsupported | supported: .arb .json .xcstrings .strings .stringsdict .xml .xlf .xliff .resx .po .properties .csv |
| `no translation files match` | `strings` glob matches nothing (globs are relative to the config) | fix the glob |
| `Set base_locale in the config` | the app has no `en` strings (the message names its development language) | `base_locale = "<code>"`, the language the flow is written in |
| `none of those languages are in the app` | `--locales` or `locales` names languages the app does not ship; the message lists what it ships | use those codes |
| `macOS reports critical memory pressure` | Mac out of memory | close apps and simulators, rerun; free memory first (see "Free memory before a run" on the docs page, https://shotfleet.com/docs#limits) |
| a run behaves differently after an iOS 27 runtime was installed | `runtime` defaults to the newest installed one, so `run` now uses iOS 27 | pin a tested one: `runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"` (`xcrun simctl list runtimes` shows the ids). iOS 27 ran with one simulator and one language (0 problems, 2026-10-05); four simulators at once has not been tried on it |
| `no simulator type called` | bad `device_type`/`device_types` name | `xcrun simctl list devicetypes` |
| `unknown Android device` | `devices` entry other than phone, tablet, tablet-7 | use `phone`, `tablet` or `tablet-7` |
| `which needs API 33 (Android 13) or newer` ("... is Android API 31; ...") | the `system_image` in the config, or the existing emulator, is older than API 33 (per-app languages need Android 13) | install an API 33+ image (the message prints the command) and set `system_image` (or `avd`); the app's minSdk can stay low |
| `couldn't create the emulator` | system image not installed (shotfleet uses the config's `system_image`, else the newest installed arm64 `google_apis`/`google_apis_playstore` image of API 33+, else `system-images;android-36;google_apis;arm64-v8a`) | run the `sdkmanager` command after `Install the image with:` in the message, or set `system_image` |
| `is already running. Stop it` | a leftover emulator on shotfleet's port | `adb -s emulator-<port> emu kill` |
| `emulators did not boot in time` | slow boot (600 s limit), or on Linux no usable `/dev/kvm`; the message ends with the emulator's last log lines (kept in `<tmp>/shotfleet-emulator-logs/`) and the likely cause. `the emulator exited with code N before it booted` means it crashed: read those lines | close other apps and rerun; on Linux check `ls -l /dev/kvm` |
| `hook before_run failed` | the user's hook returned non-zero | fix the hook, or `--no-hooks` to skip |
| `hook before_export failed` | same, before export | same |
| `write launchApp arguments as a block, not inline` | `arguments:` given as a plain value, not a mapping | a block of `name: value` lines, or an inline `{ name: value }` |
| `flow needs an 'appId:' header` | malformed flow header | start the flow with `- launchApp` or `appId:` then `---` |
| `--locales is empty` | `--locales ,` | drop the flag for all languages |
| `--parallel must be 1 or more` | `--parallel 0` | use 1 or more |

## check errors (exit 2)

| Fragment | Cause | Fix |
|---|---|---|
| `no folder at` | wrong path | fix it |
| `no screenshots found in` | layout not recognised | use `screenshots/<locale>/*.png`, `metadata/android/<locale>/images/phoneScreenshots/*.png` or `<locale>/*.png`; a flat folder of one language's PNGs needs `--locale <code>` (`shotfleet check shots/ --locale en`) |
| `has both iOS and Android screenshots` | a folder with both stores and no `--app` | pass `--app` with the build of the store to check |
| `screenshots but --app is` | an iOS folder with an `.apk` or the reverse | pass the matching build |
| `contains no translations shotfleet can read` | the build has no `.lproj`, String Catalog or resources (typical for Flutter, React Native, Unity, MAUI) | use `--strings '<glob>'` |
| `the app this run used is gone` | a shotfleet output folder whose `.app` or `.apk` moved | pass `--app` |
| `--ocr-command failed on` | the custom OCR command failed; if it says language data: `brew install tesseract-lang` | fix the command |

## Export and licence errors

| Fragment | Cause | Fix |
|---|---|---|
| `no shotfleet run in` | `export` pointed at a folder without `run.json` | pass the `run` output folder (`out`, `out-ios`, `out-android`) |
| `hasn't been checked` | no `check.json` in it | `shotfleet check <out>` |
| `need a licence` | `export`, or `run` past 2 languages, without a licence | the user runs `shotfleet activate <key>`; see licence.md |
| `that key didn't activate` | wrong, disabled (`the key was disabled`), refunded or charged-back key | the user checks the key in the Gumroad receipt email |
| `activations. Email hello@shotfleet.com` | the key has used all 5 activations (3 Macs plus 2 spare for reinstalls); `deactivate` does not give one back | the user emails hello@shotfleet.com to have the count reset |
| `SHOTFLEET_KEY couldn't be checked` | Gumroad unreachable and the key never passed a check on this machine in the last 30 days | run again once the network reaches Gumroad |
| `your licence covers every shotfleet version released until` | this version came out more than a year after the purchase | keep using a version from within the year, or email hello@shotfleet.com about a renewal |
| `SHOTFLEET_KEY isn't a valid licence` | bad key in CI | fix the secret |
| `this licence is no longer valid` | refunded, charged back or disabled (the reason is in the parentheses) | the user contacts support |
| `couldn't reach the licence server for 30 days` | offline too long | connect once |

## Warnings and notes (not errors)

| Fragment | Meaning | Fix |
|---|---|---|
| `screenshot(s) not verified, because` | the per-screen note is `not verified (macOS text recognition was busy)`: macOS was still compiling its text model in `ANECompilerService` (first time, can take minutes on a loaded Mac and about 40 minutes on a quiet one) past `check`'s 8-minute budget, and no Tesseract is installed. `check` finished anyway: the app's own texts, store sizes and missing screens were checked (identical unread screens are a note, not a copy problem); these screenshots are listed in `unverified` and exit 0 (1 with `--strict`) | run `check` again later, close heavy apps, or `brew install tesseract` (used automatically); no restart needed |
| `another shotfleet is preparing macOS text recognition; waiting` | another shotfleet on this Mac is warming up text recognition; they take turns, and the wait counts against the 8 minutes | nothing |
| `selectors not found in the app's strings` | the flow taps a label that is not in the app's strings, left as-is, may fail outside English | write the label exactly as the English string, use `id:`, or add `[overrides.<lang>]` |
| `also means` | `warning <lang>: 'Next' -> 'İleri' also means 'Advanced'`: a tap could hit the wrong element | anchor with `below:`/`above:`, or override |
| `translated in the app, so it is skipped` | `note: <lang> is only N% translated`; below 50% of the app's own strings it is not captured | add the code to `locales` to capture it anyway |
| `of the app's own strings are translated` | `warning <lang>: only N% ...`: you asked for a language the app only half translates, so the missing strings show the base language | translate it, or drop it from `locales`; check reports the screenshots that came out in the base language |
| `blank screenshot(s)` | a screenshot with only a status bar: Flutter debug builds and Compose paint after the text is readable; `run` captures the language again once, and prints this if it is still blank | before `takeScreenshot` add `extendedWaitUntil: {visible: "<text on the screen>", timeout: 60000}` |
| `blank: nothing is drawn on it yet` | the same, found by `check` on a folder | the same wait |
| a login flow works in English but the password field stays empty in Arabic (iOS) | iOS drops Latin letters typed into a secure field while the app runs in Arabic; digits are typed | use a numeric demo password (`123456`) |
| Maestro: `Element not found: Text matching regex` on a Flutter row | Flutter joins a row's title and detail into one label (`Title\nDetail`) | tap it as `"Title.*"` |
| `free tier: capturing` | no licence: 2 languages captured | see licence.md |
| `memory pressure is elevated` | shotfleet halved the simulators | close apps |
| `this Mac was short of memory` | printed only when a failed flow's error is `Unknown error` or `Unable to clear state` on a loaded Mac: usually a slow simulator, not the app | close other simulators, `shotfleet run --locales <failed codes>` |
| `failed step:` | under a `FAIL <lang>` line: the step Maestro stopped on, with its selector, as Maestro's log names it | compare the selector with what `on screen:` shows |
| `failure screenshot:` | under a `FAIL <lang>` line: the screenshot Maestro took when the step failed | open it |
| `on screen:` | under a `FAIL <lang>` line: up to 12 texts on the failure screen, from the screen hierarchy Maestro saved (else read once from the screenshot; left out while macOS text recognition is busy) | the selector should match one of them; if the screen is a different one, an earlier step went somewhere else |
| `Maestro taps at portrait coordinates in iOS landscape` | iOS flow with `setOrientation: LANDSCAPE*`: Maestro's log shows a portrait-sized frame and the tap went to the element's portrait position, so it missed on the landscape screen (a Maestro issue, seen on iPad) | capture iPad in portrait, or open the screen with a launch argument or deep link instead of tapping there |
| `maestro made no new screenshot for` | no screenshot for `stall_s` (default 900 s): a simulator or flow hung; shotfleet stopped Maestro and the languages go to the retry | usually load: close other simulators; raise `stall_s` only if a flow really takes longer between screenshots |
| `maestro timed out` | one round exceeded `timeout_s` (default 600) | raise `timeout_s`, shorten the flow, or fewer `parallel` |
| `flow passed but took` | fewer screenshots than `takeScreenshot` steps (an optional step skipped?) | check the flow, the maestro log in the output folder |
| `no result (see maestro log)` | Maestro crashed or produced no report | read `<out>/maestro1.log` |
| `flow never ran (see maestro log)` | Android: Maestro did not start that language | read `<out>/maestro_r1.log` |
| `no screenshots were captured, so there's nothing to check` | every flow failed | read the maestro logs; run one language |
| `keeps its translations inside compiled code` | `hint:` a Flutter, React Native, MAUI or Unity build | add the `strings = "<glob>"` line it prints |
| `Flutter debug build` | `hint:` the DEBUG banner will show | `debugShowCheckedModeBanner: false`; Android: `flutter build apk --release` |
| `has no JavaScript bundle` | `hint:` React Native Debug build needs Metro | build Release |
| `no --app given: using` | check found the app build (or translation files) in the current folder the way `init` does | nothing; pass `--app` to choose another build |
| `checking by language detection only` | weaker check: no `--app`, and no build found in the current folder | pass `--app` or `--strings`, or run check from the project folder |
| `macOS can't read the script of` | those screens only got the weaker checks | optional Tesseract via `--ocr-command` |
| `no text found (blank or still loading?)` | problem line: the screenshot is blank, or captured before the screen loaded | add `waitForAnimationToEnd` or an assert before `takeScreenshot` |
| `has no listing in that language` | export skipped a language the store has no listing for | nothing to do |
| `failed checks (see` | export skipped a language that failed | fix and recapture that language |
| `so it gets the` | export copies `en` to an existing `en-GB` listing and similar | informational |
| `add "iPad Pro 13-inch (M5)" to device_types` | the app runs on iPad and no 13" set exists: `run` and `check` print it and exit 1, `export` refuses (exit 2) | add that device type and run again |
| `hook after_run failed` | an after hook returned non-zero: exit becomes 1 | fix the hook |

## Hardware and limits

- Simulators: default 4 at once (`parallel`). Under elevated memory pressure shotfleet halves it; under critical it stops. On a smaller Mac use `--parallel 2`.
- Many simulators plus Android emulators at once is heavy: run one platform at a time with `--platform ios` or `--platform android`.
- iOS simulators only run Debug builds. Android needs API 33+ emulators (per-app languages).
- One iOS language run: simulators are named `shotfleet-<n>` and reused; shotfleet only touches its own.
- Real-run sizing (18 languages x 4 screens, one Mac): about 9 minutes on iOS and 15 on Android.
