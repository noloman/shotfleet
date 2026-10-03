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

## Android emulators on Linux (untried)

`doctor` checks `/dev/kvm`, finds an SDK in `ANDROID_HOME`, `~/Android/Sdk` or `/usr/lib/android-sdk`, and picks the system image for your CPU
(`x86_64`, or `arm64-v8a` on ARM). Whether `run` completes 18 languages on an emulator under KVM is the experiment E1 in STATUS.md: it needs a
machine with KVM, so it has not been done.
