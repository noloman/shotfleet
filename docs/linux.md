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
   6 GB of free memory, 10 GB of disk. Not a cloud VM without nested virtualization: the emulator
   refuses x86_64 images when the CPU exposes no `vmx`/`svm`, and refuses an arm64 image on an x86_64 host ("System image must match the host
   architecture"), so there is no software fallback. (Checked 2026-10-03 on a VM without virtualization, emulator 37.2.)
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

### E1 result, 2026-10-03: GitHub-hosted runner (2 vCPU, 7 GB, KVM usable), five attempts

The owner allowed GitHub Actions once for this (`.github/workflows/e1-android-kvm.yml`, manual only). What happened, in order, and what each attempt fixed:

| Attempt | Outcome | Cause and fix |
|---|---|---|
| 1 | `doctor --fix` failed | Google's Android CLI (the new `sdkmanager`) refuses an SDK folder whose path contains `..` ("Illegal entry path escaping destination directory"); the runner's workspace path has one. `find_sdk` and `fix_sdk_root` now return clean paths |
| 2 | fixture build failed | the workflow's own extra `sdkmanager` call still had the dotted path (workflow fixed) |
| 3 | `shotfleet run` waited 600 s: "emulators did not boot in time" | **the emulator had died at once** and its output went to `DEVNULL`, so nothing explained it. Emulator output is now kept, shotfleet fails immediately when the process exits, and a timeout shows the log tail and the likely cause |
| 4 | the emulator log said `FATAL: Not enough space to create userdata partition. Available: 7322 MB, need 12288 MB` | the hosted runner starts with about 7 GB free; the emulator wants 12 GB. The failure message now names this fix. The workflow clears the preinstalled Android SDK, .NET and similar first |
| 5 | emulators booted; the fixture **failed on the first tap** | see below |

**What attempt 5 proved on Linux with KVM:** `/dev/kvm` is usable on a hosted runner (`emulator -accel-check`: "KVM (version 12) is installed and usable"); `doctor --fix` installs Maestro, Google's tools, platform-tools, emulator, build-tools and the x86_64 API 36 image and `doctor` then says `Android: ready`; the fixture app builds; `init` and `doctor` pass; the snapshot emulator boots, saves its snapshot, and both read-only copies load it in about 15 s each; the per-app language reaches the app (`check` read the four screenshots it got, in de, ja, ar and tr, and found 0 problems). 9 of 13 assertions passed.

**What failed:** in all four languages the flow took screenshot 1, then Maestro could not find the localized "Next" button (`Element not found: Text matching regex: (Weiter|次へ)`, `(İleri|التالي)`). `captured 0/4 locales in 534 s`; the whole run phase took 829 s. The same fixture passed 29 of 29 on the Mac.

**Not established:** whether this is the runner (two software-rendered emulators, Maestro and the JVMs on 2 vCPUs, where a screen can be too slow to show the button within Maestro's wait) or a real Linux difference. The workflow did not keep the screenshots or Maestro's debug output, so the screen at the failure was not seen. It now does (`out/` is uploaded). To separate the two: run the same fixture on a machine with 4+ cores, or with `parallel = 1`, and look at the screenshot Maestro took before the failing step.

**Run 6 (one emulator, `parallel = 1`, 2026-10-03):** same failure. One emulator booted from the snapshot, every language captured `01_welcome.png`, then Maestro reported `Element not found: Text matching regex: Weiter` (ja `次へ`, ar `التالي`, tr `İleri`) after 587 s of capture; `check` read the four welcome screens with 0 problems, so the app was in the right language. So the theory "two emulators starve a 2-vCPU runner" is **not** what breaks it (one emulator fails the same way); a slow software-rendered screen on 2 vCPUs, or a Linux difference in how Maestro finds the button, are both still open. The screenshot Maestro took at the failing step and `maestro_r*.log` are in the run's artifact (`e1-android-kvm`, ID 11279947777, 14 days) but this environment cannot download artifacts: Manu can, from the run page of run 37138279362. **Do not run E1 again** until those are read.

Do not claim Linux `run` support from this. What is solid: setup, `doctor --fix`, building, booting and the per-app language on Linux/KVM; what is not: a complete run.

### E1 on a GitHub-hosted runner, 2026-10-03, second series: passed with ONE emulator on 2 cores

Run on `ubuntu-latest` (private repo, so the small runner): `Linux 6.17.0-1022-azure x86_64; 2 cores; 7 GB; KVM usable`, cpu `AMD EPYC 7763` (some runs `EPYC 9V45`).
KVM was usable after the usual udev rule; `doctor --fix` fetched the image; the fixture built, `init` and `doctor` passed (`Android: ready`).

| Attempt | Emulators | `android: shotfleet run` | Result |
|---|---|---|---|
| 1 | 2 | 5 s | emulator never found (the `XDG_CONFIG_HOME` bug below) |
| 2, 3 | 2 (default) | 1209 s, 754 s | 4 of 13 assertions failed: "Process system isn't responding" over every first screenshot; once also `Maestro Android driver did not start up in time` |
| 4 | 1 (`SHOTFLEET_E2E_PARALLEL=1`) | 580 s | same dialog, 4 of 13 failed |
| 5 | 1, ANR dialogs hidden and animations off at boot, `MAESTRO_DRIVER_STARTUP_TIMEOUT=180000` | **466 s** | **`PASS: all 13 assertions passed`**, total 8 min 13 s |
| 6 | 2, same quieter settings | 248 s | `adb install` said `Can't find service: package` (a race, fixed: an emulator counts as booted only when that service answers) |
| 7 | 2, same, with the fix | 687 s | 4 of 13 failed: the system dialog is back on every first screenshot (`hide_error_dialogs` does not hide it); `check` now reported all four as problems |

What the pass proves: on Linux with KVM the emulator boots from a freshly downloaded x86_64 API 36 image, the app's language switches per locale (de, ja, ar, tr; the Arabic screen is right to left),
Maestro taps the localized button, `check` finds a planted copy and a planted missing screenshot, `export --fastlane` writes the listings. I looked at the screenshots: real, correct language, no dialog.
What it does not prove: the default two-emulator run, which does not work on 2 cores (four failed runs with the dialog or the race, the last with every fix in place; two emulators plus Maestro need more than 2 cores), runs on a machine with more cores,
an 18-language run of a real app (none here; a 2-core runner's time would not be comparable to the Mac's 15 min 24 s), arm64 Linux. One screenshot (de, second screen) shows 8:36 and a window icon instead of the 9:41 demo clock: demo mode was dropped on that screen under load.

Two real Linux problems came out of it, both fixed:
- GitHub's runners set `XDG_CONFIG_HOME`, so `avdmanager` created the emulator in `~/.config/.android/avd` while shotfleet looked only in `~/.android/avd`; shotfleet now names the folder (`ANDROID_AVD_HOME`) to `avdmanager` and the emulator (`tests/test_setup_discovery.py`). Its error text also no longer shows only progress bars.
- A slow machine put Android's "Process system isn't responding" dialog over the screenshots and `check` said 0 problems. Emulators now hide such dialogs and turn animations off at boot, and `check` reports a system dialog on a screenshot as a problem (`tests/test_shotfleet.py`, `G1CheckDetectors`).

`run` now picks the emulator count itself on Linux (`fit_emulators`: at most cores / 2 and free GB / 3, printed when it lowers your `parallel`), so a 2-core machine runs one emulator without `SHOTFLEET_E2E_PARALLEL=1`. The rule is one measurement, not a fit; the two-emulator case on 4 or more cores is still to be run.

This answers the "Not established" above. The second series kept the screenshots: every first screenshot had Android's "Process system isn't responding" dialog over the app (the German button "Weiter" is visible underneath, so the language switch worked), which blocked Maestro's tap. The cause is the 2-core machine, not a Linux difference; one emulator alone was not enough (run 4 above failed the same way as run 6 of the first series), the dialog had to be quieted too. So: Linux `run` is proven for the fixture with one emulator on 2 cores; not with two, and not for a real app.

## Android emulators on Linux (untried)

`doctor` checks `/dev/kvm`, finds an SDK in `ANDROID_HOME`, `~/Android/Sdk` or `/usr/lib/android-sdk`, and picks the system image for your CPU
(`x86_64`, or `arm64-v8a` on ARM). Whether `run` completes 18 languages on an emulator under KVM is the experiment E1 in STATUS.md: it needs a
machine with KVM, so it has not been done.
