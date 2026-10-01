# shotfleet first-run findings (buyer's view)

Method: README, `--help`, CLI messages and landing copy only; shotfleet.py source not read. Version 0.1.0 (re-run after the coordinator's bug fixes). `~` = home.

**Not tested (no-run constraint):** `run` and `export` after a real run. That means: [ios]+[android] in one config, missing flow file, typo in `--locales`, non-English base-language app, and the actual message for a device build at run time. These are the highest-risk gaps; test them when the Mac is free.

**My own slip, disclosed:** while exploring I twice launched `shotfleet run` by accident (an archive config with `--locales en`, then one with `--locales ""`). Both booted simulators (shotfleet-1..4). I killed the processes and shut every shotfleet simulator down; only the pre-existing "iPhone 16 Pro" remains booted. No emulators or Maestro runs were completed. This may have briefly slowed the benchmark.

## Ranked findings (likelihood x severity)

### 1. System Python 3.9 crashes with a raw traceback (high x high)
Fresh Macs ship `/usr/bin/python3` 3.9. Homebrew Python was first on my PATH, so the README symlink worked, but a buyer without Homebrew Python gets:
```
$ /usr/bin/python3 shotfleet.py --help
Traceback (most recent call last):
  File ".../shotfleet.py", line 14, in <module>
    import ... tomllib
ModuleNotFoundError: No module named 'tomllib'
```
Same for `doctor`. The README says "Python 3.11+" only in a code comment. `doctor` cannot help since it never runs.
Fix: add a version check before the imports: "shotfleet needs Python 3.11 or newer (you have 3.9). Install it with `brew install python` and run again." State the requirement in prose above the install block.

### 2. Install section does not say how to get the tool, and hardcodes Apple-silicon Homebrew (high x medium)
README: `ln -s "$PWD/shotfleet.py" /opt/homebrew/bin/shotfleet   # from this folder`. There is no download or clone step ("this folder" is undefined) and `/opt/homebrew` does not exist on Intel Macs (`/usr/local/bin`). The landing page sells "early access" but says nothing about how the file arrives.
Fix: "1. Download shotfleet (link/email). 2. `chmod +x shotfleet.py && ln -s "$PWD/shotfleet.py" ~/.local/bin/shotfleet`" and note the PATH requirement. Also give `python3 shotfleet.py ...` as the no-install form.

### 3. A device build (.xcarchive) is accepted by `init` with no warning (high x high)
```
$ shotfleet init ~/Developer/HackerNewsKMP/iosApp/Kuokka.xcarchive/Products/Applications/Kuokka.app arch
wrote arch/shotfleet.toml
wrote arch/flow.yaml
me.manulorenzo.kuokka: 48 languages (ar, az, ...)
next: edit arch/flow.yaml, then: shotfleet run arch/shotfleet.toml --locales en
```
The app's Info.plist says `DTPlatformName = iphoneos`, so it cannot install on a simulator. `init` calls it fine, and the buyer finds out only after `run` boots simulators (the `run` failure text I could not capture). The error for a missing path says "no simulator app", so the check exists in some form, just not for this case.
Fix: at `init` and `run`, detect device builds and say: "This .app was built for a real iPhone (iphoneos), not the simulator. Build with `xcodebuild -sdk iphonesimulator` or choose the iPhone simulator in Xcode and use the Debug-iphonesimulator folder."

### 4. `check` without `--app` floods the report with doubtful problems (medium x high)
```
$ shotfleet check $FL
no --app given: checking by language detection only (pass --app ...)
checked 264 screenshots in 22 languages: 60 problem(s)
  - ar-SA/02_benchmarks.png: text looks like 'pl', expected 'ar'
  - de-DE/08_watch_modes.png: text looks like 'nb', expected 'de'
  - en-US/01_timer.png: text looks like 'nb', expected 'en'
```
The same folder with `--app` reports 1 problem out of 252. A buyer's first `check` is most likely the one from the README without `--app` knowledge, and "English looks like Norwegian" reads as a broken tool. Note also 264 vs 252 screenshots between the two modes, unexplained.
Fix: label this mode "rough guess, expect false alarms", show it as "possible problems", or require `--app` for fastlane folders. Say why counts differ.

### 5. `.ipa`/`.aab`/`.zip` errors do not say what to do (high x medium)
```
$ shotfleet init fake/App.ipa x      -> pass a simulator .app or an .apk
$ shotfleet init fake/app.aab x      -> pass a simulator .app or an .apk
$ shotfleet check $FL --app fake/App.ipa -> shotfleet: no simulator app at fake/App.ipa
```
The file exists, yet `check` says "no simulator app at" (reads like a missing path), and the two commands word it differently. Nothing explains how to get the right file.
Fix by extension: `.ipa` "An .ipa is a device build. Use the .app from your simulator build (Debug-iphonesimulator)." `.aab` "An .aab is the Play upload format. Build an APK: `./gradlew assembleRelease` (or `bundletool build-apks`)." `.zip` "Unzip it first." A folder: "This is a folder, not an .app; did you mean <path>/X.app?"

### 6. Generated config pins `iOS-27-0` and absolute paths; README says `iOS-26-5` (medium x medium)
`init` wrote `runtime = "com.apple.CoreSimulator.SimRuntime.iOS-27-0"` and `app = "/Users/manu/Library/Developer/..."`. The README sample shows iOS-26-5. A buyer on an older Xcode may not have that runtime; absolute paths break when the config is committed or moved. Nothing explains the keys, and there is no list of installed runtimes.
Fix: write comments in the toml ("runtime: run `xcrun simctl list runtimes` for yours"), use paths relative to the config, and have `doctor` list the matching runtime and say if it is missing.

### 7. Generated flow tells you to write English but not how to find your screens (medium x medium)
The flow is a launch plus `01_home` and one commented-out `tapOn: "Settings"`. Good start, but missing: that screenshots must be named per store slot, that `01_home` is a valid name, that text must match the English string in your app exactly (case), and a pointer to `scrollUntilVisible`/the Tips section. The `next:` line says "then: run ... --locales en" but does not say that the simulator will open and take minutes.
Fix: add 3 comment lines in the flow ("Copy the button text exactly as in your app's English strings", "See README > Tips for late dialogs and long languages") and print "`run` boots simulators; try `--locales en` first (about 1-2 minutes)".

### 8. `check` with the wrong platform's app gives 39 problems and no warning (medium x medium)
`shotfleet check <iOS fastlane> --app <Android APK>` -> "checked 144 screenshots in 22 languages: 39 problem(s)" (all "the app has no X translation"). 144 vs 252 screenshots also shows it silently skipped some folders. A user mixing up folders gets a confident wrong report.
Fix: if the folder layout (`screenshots/` vs `metadata/android/`) does not match the app type, say "this looks like an iOS folder but you passed an APK".

### 9. `check` language-count and wording surprises (medium x low)
```
checked 252 screenshots in 22 languages: 1 problem(s)
  - zh-Hant: the app has no zh-Hant translation, so this listing shows another language
```
The app has 18 languages and the folder 22 store codes; which map to which is never shown (`en-GB`, `es-MX`, `ar-SA`...). "shows another language" does not say which, or whether to delete the listing or translate the app. `report:` path is relative to where you run it, and image links in `index.html` are relative paths into the fastlane folder, so moving the report breaks them.
Fix: "zh-Hant: your app has no Traditional Chinese, so these screenshots cannot be in that language. Remove the zh-Hant listing or add the translation." Print the code mapping (`de-DE -> de`) in a verbose line and copy images into the report, or use absolute paths.

### 10. Empty and typo cases: terse, and an empty `--locales` runs everything (medium x low)
```
$ shotfleet check empty --app "$IOS"   -> no screenshots found in empty   [exit 1]
$ shotfleet check /nope                -> shotfleet: no folder at /nope   [exit 2]
$ shotfleet export ../ios/out --fastlane x -> no shotfleet run in ../ios/out. Run 'shotfleet run <config>' first
$ shotfleet run ... --locales ""        -> (silently treated as all languages and started booting 4 simulators)
$ shotfleet run ... --parallel 0        -> error: --parallel must be 1 or more   (good)
```
"no screenshots found" exits 1 (same as "problems found") with no hint about the expected layout. Empty `--locales` should be an error, not "all".
Fix: "no screenshots found in empty. Expected `<folder>/<locale>/*.png` (fastlane deliver) or `metadata/android/<locale>/images/phoneScreenshots/`." Exit 2. Reject empty `--locales`.

## Landing page vs README vs behaviour
- Landing: "18 languages took 9 minutes on iOS and 15 on Android". README sample: "captured 18/18 locales in 870s on 4 simulators" (14.5 min on iOS). Conflicting iOS timing; not verified here.
- README says the whole thing takes "about 10 minutes" to get going, but first `run` boots simulators and takes minutes; neither mentions disk/RAM for 4 simulators or 4 emulators.
- README JSON promises `exit`, `screenshots`, `problems`: confirmed present now (check.json file on disk has only `screenshots` and `problems`; `exit` appears only on `--json` stdout; minor).
- README says `check` took "about 25 seconds per platform"; mine took roughly 30s on iOS. OK.
- Landing says "No changes to the app" and "native apps only for now". README Limits mention Flutter/RN/Compose Multiplatform "on iOS"; my Compose Multiplatform APK (HackerNewsKMP) was read fine on Android (11 languages), so the limits wording is unclear about KMP on Android.
- Landing "$79 once... $49 for the first 100 people" is a waitlist ("I'll email you once"), while the README reads like a shippable tool: a visitor cannot tell whether a download exists yet.
- `doctor` prints `ok maestro (both)` with no version, though the README requires Maestro 2.x; also does not check Python or Java versions.
- `--version` prints `shotfleet 0.1.0` fine; the unknown-subcommand and missing-command errors are standard argparse and clear.
