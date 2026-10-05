# Platform reach: which machines shotfleet cannot serve, why, and what is cheap (2026-10-05)

Question: which machines, OS versions, architectures and device types does shotfleet (0.1.0 live, 0.1.1 in the gate) not serve today, and which limits can be overcome cheaply?
Device-free. No simulator, emulator or Maestro flow was run; the device lock (`/tmp/shotfleet-devices.lock`) was held by "Remoti release session" and was never taken. Nothing was killed or deleted that this work did not create (scratch files only, in the session scratchpad).
Branch `claude/limits-platform-reach`. **No change to `shotfleet.py`, `packaging/`, `site/` or `tests/claims.json`** (coordinator's rule while 0.1.1 is gated). The code I tried is kept as a patch plus tests under `research/proposed-platform-reach/` (not applied, not shipped) and one new tool, `tools/macho-minos.py`, with its test.

Evidence tags: **[M]** measured here today; **[R]** read in the repo (file named); **[I]** inferred or from memory of third-party facts, treat as a hypothesis.

## Top 3 findings

1. **The shipped Apple-silicon folder needs the macOS it was built on, and nothing says so.** The 0.1.0 build folder (`/Users/manu/Developer/shotfleet/dist/shotfleet`, same `packaging/build.sh` and Homebrew Python 3.14.8 as the release) has 52 of its 56 Mach-O files at minimum macOS **27.0** (Python.framework, libssl, libcrypto, the `ocr` helper); the PyInstaller bootloader is 11.0 [M, `tools/macho-minos.py`]. Cause: Homebrew's Python is built for the host OS (macOS 27.0, SDK 27.0), and `swiftc` without `-target` also targets the host. No README, site or terms line names a minimum macOS [R, grep]. Whether macOS 15 or 26 refuses to start it, or starts and later crashes on a missing symbol, is **unknown**: it needs a real older Mac. The fix is cheap and measured: building from a python-build-standalone interpreter (`uv python`, already on this Mac) and `swiftc -target arm64-apple-macos13.0` gives a folder whose Mach-O files need macOS 11.0 (bootloader, libpython) and 13.0 (`ocr`), 21 MB, and `--version` runs [M]. See "What is cheap".
2. **Intel Macs are not served, and the reason is only the build, not the toolchain.** The frozen binary is arm64 only, `install.sh` refuses `uname -m` other than `arm64`, and terms and site say "no Intel build yet" [R]. Everything shotfleet drives is Intel-ready: Maestro's iOS simulator driver is x86_64+arm64 in both 2.0.10 and 2.11.0, Google ships `emulator-darwin_x64` 37.x and `commandlinetools-mac_x86_64` (manifest fetched 2026-10-05), and shotfleet's own `host_abi` and `android_cmdline_archive` already pick `x86_64` / `x64` [M, R]. What is missing: an x86_64 (or universal2) PyInstaller build, and any run on Xcode 26 (Intel Macs cannot run macOS 27 [I], so Xcode 27 is out; every iOS run so far was Xcode 27.0, see below). Recommendation: do not build it now (section 5).
3. **Linux means x86_64 with KVM, and the docs overstate it.** `docs/linux.md` says "x86_64 or ARM Linux with `/dev/kvm`", and `host_abi()` returns `arm64-v8a` on aarch64 Linux. Google's manifest has **no Linux arm64 emulator** (`emulator` has `linux/x64` only; `cmdline-tools` has no arch tag) [M], so an ARM Linux box cannot get a working emulator from `doctor --fix`. For x86_64: E1 passed with ONE emulator on a 2-core runner (8 min 13 s, fixture, 13/13); two emulators fail on 2 cores; two emulators on 4 or more cores, a real 18-language app on Linux, and anything shipped as a Linux build are not done [R, `docs/linux.md`]. Linux is a source install only (no installer, licence enforced only when frozen, `docs/linux.md`, DISTRIBUTION).

## Platform table

| Platform | Verdict | Evidence |
|---|---|---|
| Apple silicon Mac, macOS 27.0, Xcode 27.0, iOS 26.4 simulators | **works** | fixture iOS 36/36, Android 29/29, CrossfitTracker 19/19, 2026-10-04 (`STATUS.md` rows 9, 10; `docs/compat.md`) |
| Same, with an iOS 27 simulator runtime | **unknown** | no run on iOS 27; a runtime is installed on this Mac now (`doctor` printed "iOS 27.0" today, not by this work), which also changes `latest_ios_runtime()` for every config without `runtime` (`docs/device-queue.md` rule 6) |
| Apple silicon, macOS 13 to 26 (running the 0.1.0 folder) | **unknown, at risk** | every Mach-O file but the bootloader is built for 27.0 [M]; no run on an older macOS |
| Apple silicon, macOS below 13 | **does not work** (as built from the fix) | the `ocr` helper compiled at target 13.0 (Vision text models); target 12 not tried; shotfleet's check needs Vision [R `ocr.swift`] |
| Xcode 26.x | **unknown** | no recorded run: `iPhone 17 Pro Max` exists from Xcode 26.0 [I]; `iPad Pro 13-inch (M5)` (named in the iPad hint) probably from 26.1 [I]. The 10-01 README runs did not record the Xcode version |
| Xcode 16 and older | **does not work by default** | default `device_type` is `iPhone-17-Pro-Max`; `make_pool` fails and says to set `device_type` [R shotfleet.py `make_pool`]. Works if the user names an existing type [I]. Proposed fix in the patch |
| Intel Mac | **does not work** | arm64-only binary; installer refuses; terms say so [R]. Toolchain ready: Maestro driver fat [M], Google x64 emulator and tools [M]. Source install (`python3 shotfleet.py`) would run on Intel [I] but is unlicensed, never tested |
| Apple silicon Mac in a Rosetta terminal | **wrongly refused** | `install.sh` tests `uname -m`, which says `x86_64` under Rosetta; `sysctl -n hw.optional.arm64` would say 1 [I]. The file is under `site/` (not touched) |
| Linux x86_64 with KVM, Android only | **works for the fixture with 1 emulator** | E1: `PASS: all 13 assertions`, 8 min 13 s, 2 cores, 7 GB (`docs/linux.md`) |
| Linux x86_64, 2 emulators | **2 cores: does not work; 4+ cores: unknown** | four failed runs with the "Process system isn't responding" dialog; `fit_emulators` caps at cores/2 and free GB/3 (one measurement, `docs/linux.md`) |
| Linux arm64 | **does not work** | no Google emulator for linux arm64 [M manifest]; `host_abi` still says `arm64-v8a` [R] |
| Linux, iOS | **impossible** | needs Xcode and CoreSimulator |
| Linux `check` | **works with Tesseract** | no language detection without `--app` (`docs/linux.md`) |
| Windows | **does not work** | not attempted (`limits-platforms.md` 1b) |
| Android API 33+ emulator image | **works** | API 36 `google_apis` arm64 and x86_64 [R] |
| Android API below 33 | **does not work, and fails late** | `cmd locale set-app-locales` needs API 33; `find_image` filters to 33+, but a config `system_image` or an existing AVD of API 31 is accepted, boots, then fails at the first language [R]. The app's minSdk is irrelevant (it runs on the newer emulator). Proposed guard in the patch |
| Android phone (1080x1920), 10" tablet (1440x2560) | **works** | CrossfitTracker phone and tablet 19/19 on 2.0.10 and 2.11.0 |
| Android 7" tablet (`tablet-7`) | **coded, device run unknown** | in `ANDROID_DEVICES` [R]; no run recorded (`limits-platforms.md` E3 open) |
| Android foldable | **not supported** | no AVD profile or device entry [R]; Play has no separate foldable slot that I could verify [I] |
| Wear OS | **not supported** | `PLAY_FOLDERS` has phone, 7", 10" only, no `wearScreenshots`; Maestro on Wear unconfirmed (`limits-platforms.md` 3.3, E5 open) |
| Android TV | **not supported** | no `tvScreenshots`; focus navigation needs another flow model (`limits-platforms.md` 3.4) |
| iPhone 6.9" (default) and other iPhone types | **works** (named type) | `device_type` any `simctl` name; only the 17 Pro Max was run on real apps |
| iPad Pro 13" | **works** | fixture, Remoti, CrossfitTracker |
| Other iPads (11", mini, 10.9") | **unknown** | named via `device_types`; `apple_class` knows 11", 10.5", 9.7" sizes; no run |
| Apple Watch, Mac, Apple TV, Vision | **capture impossible; `check` sizes known** | Maestro has no driver for them (`limits-platforms.md` section 5) |
| Maestro 2.0.10 | **works** | all earlier runs; 28/28 static checks |
| Maestro 2.11.0 | **works, one open watch item** | fixture 36/36 and 29/29; CrossfitTracker 19/19 x3; at 4 simulators 2 of 4 iOS drivers missed the 240 s start in attempt 1 and shotfleet's retry fixed 9 of 19 languages; 2.0.10 at 4 simulators with a cold run was not measured (`research/maestro-2-11.md`) |
| Maestro 2.11.1, 2.12.x, 3.x | **unknown** | did not exist on 2026-10-03; not re-checked today (`tools/latest-maestro.py` makes a network call; not run) |
| Maestro on Intel (iOS) | **driver ready** | both versions' `driver-iPhoneSimulator` runner is x86_64+arm64, iOS-sim minimum 13 and 14 [M] |
| Python source install | **3.11 to 3.14 works, 3.10 refuses** | `docs/compat.md` |

## What is cheap to fix (device-free)

| Fix | Cost | State |
|---|---|---|
| **Lower the macOS the build needs.** In `packaging/build.sh`: `swiftc -O -target "$ARCH-apple-macos13.0"` and `"${PYTHON:-python3}" -m venv build/venv`, then build with `PYTHON=$(uv python find 3.14 --managed-python)`. Measured: Mach-O minimum 11.0 and 13.0 instead of 27.0; also a universal `ocr` helper compiles (`lipo` of an arm64 and an x86_64 build, both target 13.0) | 2 lines; the proof still needs a run on an older macOS | **patch only** (`research/proposed-platform-reach/shotfleet-and-build.diff`). Not verified: PyInstaller's hardened-runtime signing and notarization of the standalone libpython (not run, 0.1.1 is being gated); the certifi bundle and TLS of the licence call in that build; the OCR helper inside the scratch build (on this loaded Mac, macOS text recognition threw its known `e5rt` error, so it is not a verdict on the build) |
| **Say which macOS builds were built for** after every build | one script | `tools/macho-minos.py dist/shotfleet [--max 14]`, committed with a test. Run it on the extracted release tarball before publishing: it would have caught the 27.0 |
| **Default iPhone type falls back to the newest `iPhone N Pro Max`** this Xcode has | 10 lines, 4 tests | patch only. Reaches Xcode 16-era Macs once the macOS minimum is fixed; untested on such an Xcode |
| **Refuse an emulator image below API 33 before booting it** (config `system_image` or an existing AVD's `image.sysdir.1`) with the reason and the install command | 15 lines, 3 tests | patch only. Saves a 1 to 5 minute boot and a cryptic adb error |
| **Docs: Linux is x86_64 only; no ARM Linux emulator** (and make `host_abi` fail early on aarch64 Linux) | a sentence, 3 lines | not done (`docs/linux.md` and `shotfleet.py` are frozen/needs the owner) |
| **`install.sh`: accept Apple silicon under Rosetta** (`sysctl -n hw.optional.arm64`) | 1 line | not done (`site/`) |
| `init` hints on Intel: `iossimulator-arm64` (MAUI) and `ARCHS=arm64` (Kotlin Multiplatform) are hard-coded | 2 lines | skipped: only matters if Intel is ever built |

The patch passes its own 7 tests and the neighbouring suites (`test_setup_discovery`, `test_first_run`, `test_portable`, `test_claims_unit`, `test_shotfleet`: exit 0) when applied to `shotfleet.py`; I reverted it afterwards. To use it: `git apply research/proposed-platform-reach/shotfleet-and-build.diff` and copy `test_platform_reach_proposed.py.txt` to `tests/`. It was not run through `tools/check-claims.sh` (see the end of this note).

## What needs hardware or real devices

- **An older Apple-silicon Mac (macOS 13, 14, 15 or 26), or a clean VM of one:** does the 0.1.0 folder start, does `check` read, does a fixture run pass; then does the rebuilt folder. This is the single most valuable test in this note. Install the release there with `install.sh` and run `shotfleet doctor`; then `tools/fixture-e2e.sh`.
- **An Intel Mac with Xcode 26:** the only way to learn whether iOS runs, x86_64 simulators and Maestro's x86_64 driver work end to end. Rosetta is not installed on this Mac (`arch -x86_64 /usr/bin/true`: "Bad CPU type"), so an x86_64 build cannot even be started here.
- **Xcode 26.x and Xcode 16 Macs:** iPhone 17 Pro Max and iPad M5 type names, and the fallback in the patch.
- **iOS 27 simulator runtime run** (already on `docs/handoff.md`).
- **A Linux machine with 4+ cores and KVM:** two emulators; then an 18-language real app; an ARM Linux machine only to confirm that no emulator exists for it.
- **Real or emulated Wear OS, TV, foldable, 7" tablet:** E3 and E5 in `limits-platforms.md`.
- A 4-simulator iOS run on 2.0.10 to separate the 2.11.0 driver-start timeouts from load.

## Recommendation: what to build

1. **Now (cost: an hour, then one test on an old Mac): make the macOS minimum a measured number.** After the 0.1.1 gate, apply the build.sh part of the patch, run `tools/macho-minos.py` on the release folder, and test the folder on one older macOS. Until that test exists, the honest wording is "tested on macOS 27 with Xcode 27", and nothing should claim a lower minimum. If the older Mac does not start the 0.1.0 folder, the live product silently excludes every Mac below 27 and buyers will see a dyld error; that is also the best argument for a one-line "needs macOS X" in the README and on the sale page (the owner's call, `site/`).
2. **Do not build Intel.** Cost: a second Python and PyInstaller build on an x86_64 Mac (or Rosetta, or a universal2 Python from python.org plus the fat `ocr`, both downloads), a second notarization and `.pkg`, `install.sh` and site and smoke changes, and no way to test it on this hardware; and Intel Macs top out at macOS 26 and Xcode 26, a combination shotfleet has never been run on. Revisit when three buyers ask. In the meantime keep "Apple silicon only" and fix the Rosetta check.
3. **Do not build Linux release packaging yet.** Keep `docs/linux.md` honest (x86_64 only; one emulator proven), run the two-emulator case once on a 4-core machine, then decide. The Linux CI-team use case (`limits-platforms.md` section 2.5) depends on that run.
4. **Apply the two small guards (`device_type` fallback, API 33 refusal) in a later release**; they are cheap and need no hardware to be correct, but they change `shotfleet.py`, so after the gate.
5. Skip Wear OS, TV, foldables, Windows, API below 33 capture (system-locale root route), Apple Watch, Mac, tvOS, visionOS capture, as in `limits-platforms.md`; nothing here changes that.

## How the numbers were obtained

- Mach-O minimum macOS and architectures: `otool -l`, `lipo -archs`, via `tools/macho-minos.py` on `/Users/manu/Developer/shotfleet/dist/shotfleet` (the main checkout's build output, read only; its tarball is `shotfleet-0.1.0-macos-arm64.tar.gz`, 8.7 MB, while STATUS gives 9.7 MB for the published one, so it may be an earlier build of the same script; the published tarball was not downloaded, so run the tool on it to be certain). Homebrew `python@3.14` 3.14.8: minos 27.0, SDK 27.0; uv's python-build-standalone 3.14.2 (`~/.local/share/uv/python`): libpython minos 11.0.
- The scratch build: PyInstaller 6.22.3 (taken from the main checkout's existing `build/venv` site-packages through a `.pth` file, no pip install, no download) run from a venv of the uv Python, into the scratchpad only; `shotfleet --version` printed 0.1.1. `doctor` on it found Android ready and the iOS pieces, and was killed once (exit 137, not by this work) and then showed macOS's `e5rt` error in text recognition on this loaded Mac (known, `STATUS.md` "Known issue seen at the gate").
- `ocr.swift` compiled with `-target arm64-apple-macos13.0` and `-target x86_64-apple-macos13.0` and `lipo -create`: all three outputs report minos 13.0; the arm64 one printed Vision's language list.
- Maestro iOS driver architectures: unzipped `driver-iPhoneSimulator/.../maestro-driver-iosUITests-Runner.zip` from `~/.maestro/lib/maestro-ios-driver.jar` (2.0.10) and `~/.maestro-tests/2.11.0/lib/maestro-ios-driver.jar`: x86_64 arm64 in every file.
- Google's repository manifest: `https://dl.google.com/android/repository/repository2-3.xml`, 419,185 bytes, **the only download of this work** (read into the scratchpad, not in the repo): `cmdline-tools;latest` 23.0 has linux (no arch), `macosx x64` and `macosx aarch64`; `emulator` 37.3.2 (canary) and 37.2.12 have `linux x64`, `macosx x64`, `macosx aarch64`; `platform-tools` 37.0.1 and `build-tools;36.0.0` have no arch tag. System-image manifests were not fetched (earlier note `limits-platforms.md` lists x86_64 images for API 33 to 37).
- Intel Macs cannot run macOS 27 and macOS 26 is their last release: from memory of Apple's WWDC 2025 statement [I]; not re-checked today.
