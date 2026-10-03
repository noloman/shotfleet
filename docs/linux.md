# shotfleet on Linux

What works, what is untried, and what cannot work. Status 2026-10-03, from source (`python3 shotfleet.py ...`, Python 3.11+).
`packaging/build-linux.sh` builds a 20 MB folder (PyInstaller, unsigned, 13 s on x86_64); that folder ran `check` and `doctor` on the test machine. There is no Linux installer or published release build yet (`install.sh` still refuses non-Macs).

| | Linux | Evidence |
|---|---|---|
| `check` on screenshots (any tool) | works, with Tesseract | run on rendered German and English screenshots on Linux; a planted English screenshot in the German folder was found; unit tests in `tests/test_portable.py` |
| Strings from an APK (`--app app.apk`, `init app.apk`) | works, needs `aapt2` | a real resources-only APK in `tests/fixtures/` (`tests/test_android_apk.py`) |
| Strings from translation files (`strings = "..."`: ARB, JSON, `.po`, `.resx`, `.ts`...) | works | `tests/test_projects.py`, `tests/test_js_translations.py` |
| `.strings`, `.stringsdict`, `Info.plist` | read in Python (no `plutil`, no `PlistBuddy`) | `tests/test_portable.py` |
| `shotfleet init` in a Flutter / React Native / ... project folder | works | synthetic project folders |
| `run` on Android emulators | coded, **never run**: SDK folders, the x86_64 image, KVM check | command lines unit-tested only; no KVM in the test machine |
| `run` on iOS | cannot work: iOS simulators exist only on a Mac with Xcode | |
| `check --app MyApp.app` | reads the app's `.strings` (works); text from the app during a run needs a Mac | |

## Real framework builds (2026-10-03, Linux x86_64, no emulator)

| Project | Build | What `shotfleet init` (no arguments) did |
|---|---|---|
| Flutter 3.47.6, `flutter create` + `gen_l10n`, en/de/ja | `flutter build apk --debug` (82 s) | found `build/app/outputs/flutter-apk/app-debug.apk`, wrote `strings = "lib/l10n/*.arb"`, read package `com.shotfleet.demo_l10n`, 3 languages |
| Expo (blank-typescript) + i18next + expo-localization, en/de/ja | `expo prebuild`, `./gradlew assembleRelease` (6.5 min) | found `android/app/build/outputs/apk/release/app-release.apk`, wrote `strings = "src/locales/*/translation.json"`, 3 languages |

In both APKs the app's own text is **not** in the Android resources (85 and 86 library languages, no "Willkommen"), so without the
`strings` line `init` would have reported about 85 languages. Flutter 3.47 writes the generated localizations next to the ARB files
(`lib/l10n/*.dart`), not into `flutter_gen`. These are small demo apps made for this check, not third-party apps, and nothing was run on a
device: the language mechanism (`cmd locale set-app-locales`, launch arguments) and Maestro's view of Flutter and React Native screens remain unproven.

Project detection was also run on three real third-party repositories (shallow clones, nothing built):

| Repository | Detected | Notes |
|---|---|---|
| wger-project/flutter | Flutter, `lib/l10n/*.arb` | 40 ARB files, 37 languages read; the other 3 (`gl`, `km`, `ur`) are empty files in the repo. 13 languages are under half translated, so `shipped_locales` skips them and says so |
| obytes/react-native-template-obytes | Expo, `src/translations/*.json` | en and ar |
| JetBrains/kotlinconf-app | Kotlin Multiplatform | first missed (version-catalog alias `kotlinMultiplatform`, modules two folders down); fixed, with a test |

## Set up

```bash
sudo apt install tesseract-ocr tesseract-ocr-all openjdk-21-jre-headless aapt   # Tesseract reads the screenshots; aapt2 reads the APK
python3 shotfleet.py doctor        # says what is missing, with the exact sdkmanager commands
python3 shotfleet.py check fastlane/ --app app-release.apk
```

- Install the Tesseract data for the languages you ship (`tesseract-ocr-all` has them all). A language without data is reported as
  "could not verify", never as a pass. `shotfleet doctor` prints how many languages Tesseract has.
- `check` gives each Tesseract process one thread (`OMP_THREAD_LIMIT=1`), because four processes each starting a thread per core spin
  against each other. Set `OMP_THREAD_LIMIT` yourself to change that.
- Without macOS text recognition there is no language detection for screens with fewer than two of your strings, and no marketing-caption
  check for framed screenshots. Pass `--app` (or `--strings`) for the full check.

## Experiment E1: the Android fixture on a Linux machine with KVM

This is the one missing proof for Linux. `tools/fixture-e2e.sh --platform-only android` builds the fixture app with the SDK tools,
runs `init`, `doctor`, `run` (de, ja, ar, tr on two emulators), `check` and `export`, then plants a copied and a missing screenshot and
asserts they are found. Everything before the emulator was run on the test machine without KVM; the emulator steps were not.
About 10 minutes plus the first image download.

1. **Machine:** x86_64 or ARM Linux with `/dev/kvm` usable by your user (`ls -l /dev/kvm`; `sudo usermod -aG kvm $USER` and log in again),
   6 GB of free memory, 10 GB of disk. Not a cloud VM without nested virtualization.
2. **Packages:** `sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-jpn tesseract-ocr-ara tesseract-ocr-tur openjdk-21-jre-headless openjdk-21-jdk-headless unzip`
   (the JDK for `javac` and `keytool`, which build the fixture).
3. **Android SDK:** unzip Google's "Command line tools only" into `~/Android/Sdk/cmdline-tools/latest`, then
   `yes | sdkmanager --licenses` and `sdkmanager platform-tools emulator "build-tools;36.0.0" "platforms;android-36" "system-images;android-36;google_apis;x86_64"`
   (`python3 shotfleet.py doctor` prints the exact commands for what is missing; `export ANDROID_HOME=~/Android/Sdk`).
4. **Maestro 2.0.10:** the tested version (`curl -Ls "https://get.maestro.mobile.dev" | bash`, then `maestro --version`).
5. **Run:** `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android --keep`
6. **Pass:** the last line is `PASS: all N assertions passed`. The script prints the machine (CPU, cores, memory, KVM) at the top and the
   seconds each phase took.
7. **Write down** in `STATUS.md` (E1 row): the machine line, the `android: shotfleet run` phase time (the Mac reference is 18 languages in 15 min 24 s on
   CrossfitTracker, from PLAN.md; the e2e runs only 4), and any `FAIL` lines with their logs in the kept work dir.
8. **If it fails** the usual suspects, in order: `doctor` not saying `Android: ready` (a missing SDK part); the emulator not booting in
   600 s (KVM not really in use: `emulator -accel-check`); a `could not verify` note on ja or ar (Tesseract data missing); `cmd locale
   set-app-locales` refused (the image is older than API 33).

## Android emulators on Linux (untried)

`doctor` checks `/dev/kvm`, finds an SDK in `ANDROID_HOME`, `~/Android/Sdk` or `/usr/lib/android-sdk`, and picks the system image for your CPU
(`x86_64`, or `arm64-v8a` on ARM). Whether `run` completes 18 languages on an emulator under KVM is the experiment E1 in STATUS.md: it needs a
machine with KVM, so it has not been done.
