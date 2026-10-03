# What is left, and how to do it

Written 2026-10-03 at the end of a session that could not run anything on a device. Each item says **what it needs** (the reason it was not
done), **the steps**, **how you know it passed**, and **where to record it**. Evidence goes into `STATUS.md` (the row named) and, if a promise
changes, into `tests/claims.json` and the README in the same commit. The rule of this repo stands: nothing is called "tested" without a run.

**Each open item that a local agent can do now has its own prompt in [docs/agent-tasks/](agent-tasks/README.md)** (start a session on your Mac and say: read the file and do it).

Order: 1 and 2 first (they unblock the Maestro and Linux claims), then 3 to 5, then the rest.

| # | Item | Needs | Why not done here |
|---|---|---|---|
| 1 | Maestro 2.11.0 on iOS and Android, then promote it | your Mac, ~40 min, a quiet machine | no simulator |
| 2 | E1: the Android fixture on Linux with KVM | a Linux box with `/dev/kvm` | no hardware virtualization here |
| 3 | A real Flutter, Expo and React Native app captured end to end | Mac (iOS) and/or KVM Linux (Android) | no device |
| 4 | `doctor --fix` on a Mac | your Mac, a clean user | untried on macOS |
| 5 | Android `[inputs]` on Maestro 2.11.0 | an emulator | no emulator |
| 6 | Real-app regression (CrossfitTracker, Remoti) | your Mac and the apps | not on this machine |
| 7 | Android on-screen text from the UI tree (B2) | one emulator, Maestro 2.11 | no emulator |
| 8 | Python 3.14 final | the final release | the suite passes on 3.14.0rc2; the final release is not out |
| 9 | A real activation with a real key (the proxy half is done) | a live Gumroad product and a test key | not live yet |
| 10 | Capacitor, MAUI, Unity | per-framework toolchains and devices | not attempted |
| 11 | Decisions that are not engineering | you | see the end |
| 12 | Xcode 27 check, monthly spec check, demand tests | a Mac; the site after launch | research dated 2026-10-03 |

---

## 1. Maestro 2.11.0 (and promoting it)

**State:** 2.11.0 is the newest Maestro and passes all 28 static checks (`docs/compat.md`). No run on a device. `MAESTRO_TESTED` is still
`("2.0.10",)`, so doctor says "may work". `doctor --fix` still installs 2.0.10.

**Steps, on your Mac, no other session using simulators:**

```bash
# a copy of 2.11.0 that does not touch ~/.maestro
mkdir -p ~/.maestro-tests && cd ~/.maestro-tests
curl -sSL -o m.zip https://github.com/mobile-dev-inc/maestro/releases/download/cli-2.11.0/maestro.zip
shasum -a 256 m.zip        # 5384593cb4e7a106489e75a821d157dd43f4e438df6bc308b72e82c685e1283a
unzip -q m.zip -d 2.11.0 && ~/.maestro-tests/2.11.0/maestro/bin/maestro --version      # 2.11.0
cd <repo>
python3 tools/maestro-compat.py ~/.maestro-tests/2.11.0/maestro                         # 28 passed, 0 failed
export PATH=$HOME/.maestro-tests/2.11.0/maestro/bin:$PATH
SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios                                # ~17 min, expect 36/36
SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android                            # expect 29/29
```

**Watch for** (from `research/maestro-2-11.md`): a flow now failing loudly on `launchApp`/`clearState` (2.7.0 stopped swallowing those errors);
the line `Selected device ... using port` missing from `maestro.log` (then `check` falls back to OCR for iOS text); the sharded parallel iOS runs
behaving differently (2.6.0 changed them; shotfleet's `kill_stale_drivers` and the port-7001 comment were written for 2.0.10); run time per
flow versus 2.0.10. Then the same on CrossfitTracker (item 6).

**If it passes, promote it in one commit** (these places quote the version and must change together or tests fail):

- `shotfleet.py`: `MAESTRO_TESTED = ("2.0.10", "2.11.0")`; `MAESTRO_PIN` to `version "2.11.0"`, `size 314886578`,
  url `.../cli-2.11.0/maestro.zip`, `sha256 5384593cb4e7a106489e75a821d157dd43f4e438df6bc308b72e82c685e1283a`.
- README (`Maestro (tested with 2.0.10)` and the `doctor --fix` paragraph), `site/public/docs.html` (the `doctor --fix` line),
  `skill/shotfleet/SKILL.md` and `skill/shotfleet/references/troubleshooting.md` (`tested with 2.0.10`), `tests/claims.json` rows quoting them.
- Tests: `tests/test_agent_skills.py` (the quoted README string), `tests/test_doctor_versions.py` (the `MAESTRO_TESTED` assertion, and the
  cases that use 2.11.0 as "a newer version": use 2.99.0 instead).
- Run `tools/check-claims.sh`; it names anything missed.

**If it fails:** `docs/compat.md` says which part of the interface to look at; keep `MAESTRO_TESTED` as is and record the failure in
`research/maestro-2-11.md`.

## 2. E1: the Android fixture on Linux

**State:** everything up to the emulator was run (build, `init`, `doctor`, the Linux `check` path); the emulator was not. The checklist is in
`docs/linux.md` ("Experiment E1"). Short form, on a Linux machine with `/dev/kvm`:

```bash
python3 shotfleet.py doctor --fix --yes            # fetches Maestro, Java, the Android tools and an x86_64 system image (a large download)
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-jpn tesseract-ocr-ara tesseract-ocr-tur
SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android --keep
```

**Passed when** the last line is `PASS: all N assertions passed`. **Record** in `STATUS.md` row E1: the `machine:` and `cpu:` lines the script
prints, the seconds of the `android: shotfleet run` phase, any `FAIL` lines. A VM without nested virtualization cannot do this at all: the
emulator refuses x86_64 images without `vmx`/`svm` and refuses an arm64 image on an x86_64 host.

Then the real one: `shotfleet run` of 18 languages on a real app on that machine, for the timing to compare with 15 min 24 s on the Mac.

## 3. Real Flutter, Expo and React Native apps, end to end

**State:** `init` finds the build and writes the `strings` line (proved on a Flutter 3.47.6 and an Expo demo app built on Linux, and on real
repos wger and obytes by detection only). Nothing has been captured on a device. Questions only a run answers:

- Does the language reach the app? iOS: `-AppleLanguages` launch arguments. Android: `cmd locale set-app-locales`. Flutter and React Native read
  the process locale, so it should; Expo apps with a persisted language (AsyncStorage) may ignore it.
- Does Maestro see the text? Flutter needs `Semantics` labels (icons need `semanticLabel`); React Native `testID` maps to `id:`; on iOS an
  `accessibilityLabel` replaces the visible text in the tree (Maestro issue 1409).
- The Flutter DEBUG banner (iOS simulators run debug builds only) and the React Native Release requirement.

**Steps (Mac for iOS, any KVM Linux or Mac for Android).** Use the three repos already checked: wger-project/flutter
(`flutter build ios --simulator --debug`, `flutter build apk --debug`), obytes/react-native-template-obytes (`npx expo run:ios --configuration
Release --no-bundler`, `npx expo run:android --variant release --no-bundler`), JetBrains/kotlinconf-app (`xcodebuild -workspace
app/iosApp/KotlinConf.xcworkspace -scheme KotlinConfAppScheme ...`, `./gradlew :app:androidApp:assembleDebug`). In each: `shotfleet init`,
write a 3-step English flow, `shotfleet run --locales de,ja`, open `out/index.html`.

**Passed when** the German and Japanese screenshots show German and Japanese, 0 untranslated selectors in the run output, 0 problems from
`check`. **Record** in `STATUS.md` row C1 and, only for what passed, in the README ("Flutter and React Native work from your translation files"
currently says "not yet run on a real Flutter or React Native app"; claims C035, C121).

## 4. `doctor --fix` on a Mac

**State:** the Linux path was run for real (Maestro, Google's tools, platform-tools, emulator, image; the Java download separately). On macOS:
the Temurin JRE tarball unpacks to `jdk-21.x.y+z-jre/Contents/Home/...`; `install_jre` renames that folder to `~/.shotfleet/jre`, and
`find_java` looks at `~/.shotfleet/jre/Contents/Home`. Unverified. So is the `brew install --cask android-commandlinetools` branch, and the
Google archive pick for `mac_arm64`.

**Steps:** a clean macOS user (or `SHOTFLEET_HOME=$(mktemp -d)` plus `ANDROID_HOME=$(mktemp -d)` and a `PATH` without Java and Maestro):

```bash
python3 shotfleet.py doctor --fix --yes && python3 shotfleet.py doctor
```

**Passed when** `doctor` reports Maestro and Java as ok afterwards. **Record** in claim C126 and `STATUS.md` row D1. This is also the real
test of `STATUS.md` gate 7 (clean-Mac cold install) once the installer exists.

## 5. Android `[inputs]` on Maestro 2.11.0

**State:** 2.11.0 defines `MAESTRO_DEVICE_UDID` (2.0.10 does not), and shotfleet's script already uses it (`android_vars`). Unconfirmed: what
value Maestro gives it. shotfleet expects the adb serial (`emulator-5700`...).

**Steps:** the fixture (`tools/fixture-app-android`), a flow with `inputText: ${name}` and `[inputs.de]`, `[inputs.ja]` with different values,
`shotfleet run --locales de,ja` on 2 emulators with 2.11.0 first on the PATH. **Passed when** the German screenshot shows the German value and
the Japanese one the Japanese value (the run prints `no row for device '...'` if the value is not a serial shotfleet knows). **If it passes:**
remove the "Maestro 2.0.10 doesn't define it" wording in `README.md` (Inputs), `site/public/docs.html`, `skill/shotfleet/references/config.md`
and the note printed by `shotfleet.py` (search for `doesn't define it`), and drop the version caveat from `tests/test_limits_c2_c3.py`.

## 6. Real-app regression

`STATUS.md` plan A2: CrossfitTracker iOS (18 languages), Android phone and tablet, Remoti iPhone + iPad, on Maestro 2.0.10, after the config
rewrite, `[inputs]`, the iOS retry and `init` discovery commits, and now after this session's changes (the `plutil`/`PlistBuddy` replacements
only run when those tools are absent, so macOS behaviour should be unchanged, but a real run is the proof). Needs a quiet Mac and 30+ GB free.
**Passed when** 0 problems and the timings are in the README.

## 7. Android on-screen text from the UI tree (B2)

`research/limits-text.md` 1b: a 10-minute marker experiment on one emulator with Maestro 2.11: can the UI hierarchy be read during a sharded
run without hanging it (2.0.10's `maestro hierarchy` broke sharded runs)? One text file per screenshot, or "not possible" written down. Today
Android screenshots are checked with OCR only.

## 8. Python 3.14

Run on 3.14.0rc2 (2026-10-03, `uv python install 3.14`): all 595 tests pass with `-W error::DeprecationWarning`. Left: add `"3.14"` to the `linux`
matrix in `.github/workflows/ci.yml` once `actions/setup-python` offers a final 3.14, and re-run on the final release. The tar-extraction change
3.14 makes is already handled (`TAR_SAFE` in `shotfleet.py`).

## 9. Licence calls behind a proxy

Done for the TLS part (2026-10-03), in this sandbox, which sits behind a real HTTPS-re-signing proxy: `polar_post` aimed at a harmless public URL
fails with `CERTIFICATE_VERIFY_FAILED (self-signed certificate)` without `SSL_CERT_FILE` and reaches the server with it. Left: a real activation
with a real test key once Gumroad is live (`STATUS.md` gate 5): `HTTPS_PROXY=... SSL_CERT_FILE=<proxy CA> shotfleet activate <key>`. Neither the
Polar organisation id nor the Gumroad product id is set in the source tree, so no real licence server could be called from here.

## 10. Other frameworks

- **Capacitor / Ionic:** unverified whether the iOS WKWebView language follows the launch argument (an Apple forum report says
  `navigator.language` ignores it since iOS 17.4). A throwaway app with two buttons settles it in 20 minutes on a Mac.
- **.NET MAUI:** `dotnet workload install maui`, then the LocalizationDemo sample from dotnet/maui-samples (`research/frameworks.md` section 12).
- **Unity / games:** not realistic (no text in the accessibility tree). Not planned.

## 11. Decisions that are not engineering

- **A Linux release:** `packaging/build-linux.sh` builds a working 20 MB folder. Missing: where to host it, a Linux branch in `site/public/install.sh`
  (it refuses non-Macs on purpose today), a Linux step in `packaging/release.sh`, and a checksum/`VERSION` convention for a second platform.
  Decide, then it is about a day.
- **A GitHub Action for `check`:** needs the Linux release above (or the macOS one) to download.
- **Everything in `STATUS.md` "What Manu must do"** (payment provider, tax question, test purchase, go-live, outside testers, posting) is
  unchanged by this session.

## 12. New from the strategy research (2026-10-03, see research/profit-plan-2026-10-03.md)

- **Xcode 27 final replaced Simulator.app with Device Hub** (static analysis in `docs/compat.md`: shotfleet never opens Simulator.app and Maestro only does so when it starts a simulator itself, which shotfleet never asks it to; unproved). Before selling, run `tools/fixture-e2e.sh --platform-only ios` on a Mac with Xcode 27 final and an iOS 27 simulator
  runtime, and record the Xcode build and iOS version in `STATUS.md` row 9 (no record says which Xcode the real runs used). Passed when 36 of 36 assertions hold; if `simctl` behaves
  differently, `shotfleet.py`'s simulator functions are where to look.
- **Apple's screenshot specifications change often** (8 Jul, 19 Aug, 9 Sep). The sizes are now watched by `tools/apple-specs-watch.py` (run it monthly with `tools/watch-upstream.sh`): it
  compares every size on Apple's page with `APPLE_SIZES` and was run on the real page on 2026-10-03 (45 distinct sizes, table matches; it also found four old-device landscape sizes
  that were missing, now added). The prose rules (count, alpha, which set is required) are not machine-read: read the page once a month. iPhone Duo sizes are known; Apple opens
  uploads for it "later this year", so `export` for Duo is untested. `tools/watch-upstream.sh` runs this and the Maestro check together. The two GitHub workflows for them are manual-only; nothing is scheduled.
- **Team / CI demand test and the layout check** are decided by the experiments in section 7 of the strategy note, after launch; do not build them before.

## Known small things, not blocking

- `tools/pretend-mac.py <test module>` runs a test module as if on an Apple-silicon Mac (platform and CPU only). It reproduced both macOS-only failures of the
  `doctor --fix` tests before CI did; use it on new tests, but it does not replace a Mac.
- Older test modules leak a few sockets (`ResourceWarning`); harmless, not from the new tests.
