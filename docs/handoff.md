# What is left, and how to do it

Written 2026-10-03 at the end of a session that could not run anything on a device. Each item says **what it needs** (the reason it was not
done), **the steps**, **how you know it passed**, and **where to record it**. Evidence goes into `STATUS.md` (the row named) and, if a promise
changes, into `tests/claims.json` and the README in the same commit. The rule of this repo stands: nothing is called "tested" without a run.

**Each open item that a local agent can do now has its own prompt in [docs/agent-tasks/](agent-tasks/README.md)** (start a session on your Mac and say: read the file and do it).

Order: 1 and 2 first (they unblock the Maestro and Linux claims), then 3 and 5, then the rest.

| # | Item | Needs | Why not done here |
|---|---|---|---|
| 1 | Maestro 2.11.0 on iOS and Android, then promote it | your Mac, ~40 min, a quiet machine | no simulator |
| 2 | E1: the Android fixture on Linux with KVM | a Linux box with `/dev/kvm` and 4+ cores | passed with ONE emulator on a 2-core GitHub runner (PR #33); two emulators and the 18-language timing still open |
| 3 | A real Flutter, Expo and React Native app captured end to end | Mac (iOS) and/or KVM Linux (Android) | no device |
| 5 | Android `[inputs]` on Maestro 2.11.0 | an emulator | no emulator |
| 8 | Python 3.14 final | the final release | the suite passes on 3.14.0rc2; the final release is not out |
| 9 | A real activation with a real key (the proxy half is done) | a live Gumroad product and a test key | not live yet |
| 10 | Unity | a Unity install and devices | not planned |
| 11 | Decisions that are not engineering | you | see the end |
| 12 | Xcode 27 with an iOS 27 runtime (iOS 26.4 part done), monthly spec check, demand tests | a Mac; the site after launch | research dated 2026-10-03 |

---

## 1. Maestro 2.11.0 (and promoting it)

**State: done 2026-10-04.** The first device run on 2.11.0 failed (it rejects absolute `takeScreenshot` paths, `research/maestro-2-11.md`); shotfleet now
names screenshots relative to Maestro's working directory and moves them into `raw/<locale>/` afterwards (`collect_shots`). The fixture e2e then
passed on 2.11.0 (iOS 36/36, Android 29/29) and on 2.0.10 (36/36, 29/29). `MAESTRO_TESTED` is `("2.0.10", "2.11.0")` and `doctor --fix` installs
2.11.0. CrossfitTracker on 2.11.0 was run on 2026-10-04 (all three targets 19/19, 0 problems; `research/maestro-2-11.md`). Still open from this item: per-flow timings on a quiet Mac (the runs were on a loaded one), why 9 iOS languages needed a retry at 4 simulators (the last bullet of this file), and the
Android `[inputs]` check (item 5). The steps below are what was run, for repeating it on a future version.

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

**State (2026-10-03):** passed with one emulator (`SHOTFLEET_E2E_PARALLEL=1`) on a 2-core GitHub runner with KVM, 466 s run phase (PR #33, `docs/linux.md`). The default two emulators failed on 2 cores in every run (Android's "Process system isn't responding"); **what is left** is the same script with the default two emulators on a machine with 4 or more cores (real hardware, a larger runner, or a nested-virtualization cloud VM), and the 18-language real-app timing below (build CrossFit Tracker's Android debug app from current `origin/main` for it: older debug builds send Firebase events to the production property). The checklist is in
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

## 5. Android `[inputs]` on Maestro 2.11.0

**State: done 2026-10-04, with one limit.** 2.11.0 defines `MAESTRO_DEVICE_UDID` (2.0.10 does not) and it is the adb serial (`emulator-5702`); the German
and Japanese screenshots show their own typed values. The run used ONE emulator (memory pressure made shotfleet halve 2 to 1), so de and ja ran one after
the other; two emulators at once and Arabic are not run. The wording was updated as described below, saying exactly that.

**Steps:** the fixture (`tools/fixture-app-android`), a flow with `inputText: ${name}` and `[inputs.de]`, `[inputs.ja]` with different values,
`shotfleet run --locales de,ja` on 2 emulators with 2.11.0 first on the PATH. **Passed when** the German screenshot shows the German value and
the Japanese one the Japanese value (the run prints `no row for device '...'` if the value is not a serial shotfleet knows). **If it passes:**
remove the "Maestro 2.0.10 doesn't define it" wording in `README.md` (Inputs), `site/public/docs.html`, `skill/shotfleet/references/config.md`
and the note printed by `shotfleet.py` (search for `doesn't define it`), and drop the version caveat from `tests/test_limits_c2_c3.py`.

## 8. Python 3.14

Run on 3.14.0rc2 (2026-10-03, `uv python install 3.14`): all 595 tests pass with `-W error::DeprecationWarning`. Left: add `"3.14"` to the `linux`
matrix in `.github/workflows/ci.yml` once `actions/setup-python` offers a final 3.14, and re-run on the final release. The tar-extraction change
3.14 makes is already handled (`TAR_SAFE` in `shotfleet.py`).

## 9. Licence calls behind a proxy

Done for the TLS part (2026-10-03), in this sandbox, which sits behind a real HTTPS-re-signing proxy: `gumroad_verify` aimed at a harmless public URL
fails with `CERTIFICATE_VERIFY_FAILED (self-signed certificate)` without `SSL_CERT_FILE` and reaches the server with it. Left: a real activation
with a real test key once Gumroad is live (`STATUS.md` gate 5): `HTTPS_PROXY=... SSL_CERT_FILE=<proxy CA> shotfleet activate <key>`. The
Gumroad product id is not set in the source tree, so no real licence server could be called from here.

## 10. Other frameworks

- **Unity / games:** not realistic (no text in the accessibility tree). Not planned.

## 11. Decisions that are not engineering

- **A Linux release:** `packaging/build-linux.sh` builds a working 20 MB folder. Missing: where to host it, a Linux branch in `site/public/install.sh`
  (it refuses non-Macs on purpose today), a Linux step in `packaging/release.sh`, and a checksum/`VERSION` convention for a second platform.
  Decide, then it is about a day.
- **A GitHub Action for `check`:** needs the Linux release above (or the macOS one) to download.
- **Everything in `STATUS.md` "What Manu must do"** (payment provider, tax question, test purchase, go-live, outside testers, posting) is
  unchanged by this session.

## 12. New from the strategy research (2026-10-03, see research/profit-plan-2026-10-03.md)

- **Xcode 27 final replaced Simulator.app with Device Hub** (`docs/compat.md`: shotfleet never opens Simulator.app and Maestro only does so when it starts a simulator itself, which shotfleet never asks it to). **Run 2026-10-04 on Xcode 27.0 (27A266a), macOS 27.0 with the iOS 26.4 runtime: 36 of 36 assertions, no `open -a Simulator`, status bar and 1320x2868 right** (`STATUS.md` row 9). **Still open: the same run with an iOS 27 simulator runtime** (none is installed on this Mac). `xcodebuild -downloadPlatform iOS` offers "iOS 27.0 Simulator (24A434) (arm64)", **8.05 GB**; on 2026-10-05 it ran at about 0.9 MB/s (hours), so start it early with `-exportPath <dir>` (downloads the image without installing it; the import step was not tried). Installing it makes `latest_ios_runtime()` pick iOS 27 for every later `shotfleet init`, so on a shared Mac install it last or pin `runtime` in the configs, and delete it again afterwards if the others should stay on 26.4. If `simctl` behaves
  differently on iOS 27, `shotfleet.py`'s simulator functions are where to look.
- **Apple's screenshot specifications change often** (8 Jul, 19 Aug, 9 Sep). The sizes are now watched by `tools/apple-specs-watch.py` (run it monthly with `tools/watch-upstream.sh`): it
  compares every size on Apple's page with `APPLE_SIZES` and was run on the real page on 2026-10-03 (45 distinct sizes, table matches; it also found four old-device landscape sizes
  that were missing, now added). The prose rules (count, alpha, which set is required) are not machine-read: read the page once a month. iPhone Duo sizes are known; Apple opens
  uploads for it "later this year", so `export` for Duo is untested. `tools/watch-upstream.sh` runs this and the Maestro check together. The two GitHub workflows for them are manual-only; nothing is scheduled.
- **Team / CI demand test and the layout check** are decided by the experiments in section 7 of the strategy note, after launch; do not build them before.

## Known small things, not blocking

- `tools/pretend-mac.py <test module>` runs a test module as if on an Apple-silicon Mac (platform and CPU only). It reproduced both macOS-only failures of the
  `doctor --fix` tests before CI did; use it on new tests, but it does not replace a Mac.
- Older test modules leak a few sockets (`ResourceWarning`); harmless, not from the new tests.
- A quiet-Mac re-measure of the README timings (iOS about 9 min, Android about 15, 4 devices) is still open: the 2026-10-04 regression passed on correctness but ran on a swapping Mac with 2 devices (`STATUS.md` row 10). Do it once with nothing else running, `parallel = 4`, and only then change the README or claim C007.
- **iOS driver start at 4 simulators on Maestro 2.11.0:** the CrossfitTracker run of 2026-10-04 passed 19/19 but 9 of 19 languages (18 in an earlier run) needed shotfleet's retry because two of four parallel simulators did not get their XCTest driver ready within 240 s (`research/maestro-2-11.md`, last section). Open: run the same on Maestro 2.0.10 with `parallel = 4` to see whether this is new; if it is, try a longer `MAESTRO_DRIVER_STARTUP_TIMEOUT` or staggered driver starts.

## 13. State at the end of 2026-10-05 (device-queue coordinator wrap-up)

- **shotfleet 0.1.0 is LIVE** (go-live ran 2026-10-05 08:02-08:11: `5fa4f7c` Gumroad product ID, `5bbec86` Site: sale open). Evidence: `research/go-live-gate.md`: G3 65/65 on the signed build of main 081853b (iPhone, iPad, Android; real licence), G10 production smoke 36 checks / 0 failed, live archive's checksum, signature and quarantined run verified. Not run: a real `install.sh` from the live URL into this Mac's real PATH (it can link into /opt/homebrew/bin; use a temp HOME), G8 (real apps with the release binary) and a refunded real key (needs a real sale).
- **Merged today after a full local gate (798 tests, 59 worker checks, exit 0):** #40 (small experiments), #32 (launch-article verification; `site/draft` is not deployed).
- **Open PRs that change `shotfleet.py` (next release, 0.1.1), do not merge blind:** #29 (first real Flutter/Expo/Compose runs, has conflicts), then #31 (stacked on #29; its blank-frame retry, Flutter release APK, Arabic secure field and wger in 19 languages were never verified on a device), #44 (Android screen text from the UI hierarchy, Maestro 2.7+; device run pending), #37 (Xcode 27.0 on the iOS 26.4 runtime, 36/36; conflict in STATUS.md, its session merges it). Each needs: rebase on main, `tools/check-claims.sh` exit 0, the device run named in its PR, then a release rebuild and the fixture e2e gate (G3) on the exact build before publishing.
- **Maestro:** 2.0.10 and 2.11.0 both pass the fixture e2e (iOS 36/36, Android 29/29; 2.11.0 with the relative-screenshot-names fix, PR #35 merged earlier). A two-emulator Android `[inputs]` check on 2.11.0 and the iOS 27 runtime (8.05 GB, ~0.5 MB/s: needs a fast connection or an overnight download; do not import it while other jobs run, it changes `latest_ios_runtime()`) are the open device items.
- **Running device jobs on this Mac (shared by many agent sessions):** use the lock protocol in `docs/device-queue.md`. Every run script or waiter needs a hard time limit (an unbounded waiter held the lock for 8 h overnight); check ownership of a process or folder before killing or deleting it (a work dir deleted by mistake voided a release gate run); `simctl` wedges under load (CoreSimulatorService restart is a user decision: it stops every booted simulator).
- **Disk:** swung between 11 and 50 GB on 2026-10-04/05; AVD images (35 GB in ~/.android), CoreSimulator (43 GB), Gradle caches (33 GB) and session scratch in /private/tmp (56 GB) are the big items. shotfleet's own simulator cache (shotfleet-*) is recreated on demand.

