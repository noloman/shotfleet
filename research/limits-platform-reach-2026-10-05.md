# Platform reach: which machines shotfleet cannot serve, why, and what is cheap (2026-10-05)

Question: which machines, OS versions, architectures and device types does shotfleet (0.1.0 live, 0.1.1 in the gate) not serve today, and which limits can be overcome cheaply?
Device-free. No simulator, emulator or Maestro flow was run; the device lock (`/tmp/shotfleet-devices.lock`) was held by "Remoti release session" and was never taken. Nothing was killed or deleted that this work did not create (scratch files only, in the session scratchpad).
Branch `claude/limits-platform-reach`. **No change to `shotfleet.py`, `packaging/`, `site/` or `tests/claims.json`** (coordinator's rule while 0.1.1 is gated). The code I tried is kept as a patch plus tests under `research/proposed-platform-reach/` (not applied, not shipped) and one new tool, `tools/macho-minos.py`, with its test.

Evidence tags: **[M]** measured here today; **[R]** read in the repo (file named); **[I]** inferred or from memory of third-party facts, treat as a hypothesis.

## Top 3 findings

1. **The shipped Apple-silicon folder needs the macOS it was built on, and nothing says so.** The 0.1.0 build folder (`/Users/manu/Developer/shotfleet/dist/shotfleet`, same `packaging/build.sh` and Homebrew Python 3.14.8 as the release) has 52 of its 56 Mach-O files at minimum macOS **27.0** (Python.framework, libssl, libcrypto, the `ocr` helper); the PyInstaller bootloader is 11.0 [M, `tools/macho-minos.py`]. Cause: Homebrew's Python is built for the host OS (macOS 27.0, SDK 27.0), and `swiftc` without `-target` also targets the host. No README, site or terms line names a minimum macOS [R, grep]. A static look at its imports (section "Static survey") adds two concrete risks: `Python.framework` imports `mkfifoat`/`mknodat` strongly (macOS 13.0 and newer only), and `pyexpat` needs the OS's libexpat 2.7.2 or newer (`shotfleet.py` imports `plistlib` at line 20, so a missing symbol stops start-up). Whether macOS 13 to 26 starts it is still **unknown**: it needs a real older Mac or a VM or runner. The fix is cheap and measured: building from a python-build-standalone interpreter (`uv python`, already on this Mac) and `swiftc -target arm64-apple-macos13.0` gives a folder whose Mach-O files need macOS 11.0 (bootloader, libpython) and 13.0 (`ocr`), 21 MB, and `--version` runs [M]. See "What is cheap".
2. **Intel Macs are not served, and the reason is only the build, not the toolchain.** The frozen binary is arm64 only, `install.sh` refuses `uname -m` other than `arm64`, and terms and site say "no Intel build yet" [R]. Everything shotfleet drives is Intel-ready: Maestro's iOS simulator driver is x86_64+arm64 in both 2.0.10 and 2.11.0, Google ships `emulator-darwin_x64` 37.x and `commandlinetools-mac_x86_64` (manifest fetched 2026-10-05), and shotfleet's own `host_abi` and `android_cmdline_archive` already pick `x86_64` / `x64` [M, R]. What is missing: an x86_64 (or universal2) PyInstaller build, and any run on Xcode 26 (Intel Macs cannot run macOS 27 [I], so Xcode 27 is out; every iOS run so far was Xcode 27.0, see below). Recommendation: do not build it now (section 5).
3. **Linux means x86_64 with KVM, and the docs overstate it.** `docs/linux.md` says "x86_64 or ARM Linux with `/dev/kvm`", and `host_abi()` returns `arm64-v8a` on aarch64 Linux. Google's manifest has **no Linux arm64 emulator** (`emulator` has `linux/x64` only; `cmdline-tools` has no arch tag) [M], so an ARM Linux box cannot get a working emulator from `doctor --fix`. For x86_64: E1 passed with ONE emulator on a 2-core runner (8 min 13 s, fixture, 13/13); two emulators fail on 2 cores; two emulators on 4 or more cores, a real 18-language app on Linux, and anything shipped as a Linux build are not done [R, `docs/linux.md`]. Linux is a source install only (no installer, licence enforced only when frozen, `docs/linux.md`, DISTRIBUTION).

## Platform table

| Platform | Verdict | Evidence |
|---|---|---|
| Apple silicon Mac, macOS 27.0, Xcode 27.0, iOS 26.4 simulators | **works** | fixture iOS 36/36, Android 29/29, CrossfitTracker 19/19, 2026-10-04 (`STATUS.md` rows 9, 10; `docs/compat.md`) |
| Same, with an iOS 27 simulator runtime | **unknown** | no run on iOS 27; a runtime is installed on this Mac now (`doctor` printed "iOS 27.0" today, not by this work), which also changes `latest_ios_runtime()` for every config without `runtime` (`docs/device-queue.md` rule 6) |
| Apple silicon, macOS 13 to 26 (running the 0.1.0 folder) | **unknown, at risk** | every Mach-O file but the bootloader is built for 27.0 [M]; no run on an older macOS |
| Apple silicon, macOS 12 and older | **does not work** (0.1.0: cannot load Python, `mkfifoat` is macOS 13.0) | static survey [M]; the rebuilt folder targets 13.0 for `ocr`, target 12 not tried |
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

## How to build 0.1.1+ for older macOS (for the release session; nothing here has been run on an older macOS)

Goal: a folder whose Mach-O files need macOS 13 or less, not 27.0. What I did, in the order to repeat it. The scratch builds went to the session scratchpad only; nothing was signed, notarized or published.

**1. Python.** Python 3.14.2 from python-build-standalone (Astral's builds, which `uv` installs), **already on this Mac, nothing downloaded**:
`/Users/manu/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/bin/python3.14` (57 MB installed; its `BUILD` file says release tag 20260127; `sysconfig` `MACOSX_DEPLOYMENT_TARGET` is 11.0; OpenSSL 3.5.5 statically inside; pyexpat built in with its own expat 2.6.3). Find it with `uv python find 3.14 --managed-python` (works offline; uv 0.9.28). I do not have the original archive's filename, size or checksum: uv fetched it earlier from the python-build-standalone GitHub release and checked it itself. **A surprise: it is older than Homebrew's** (3.14.2 against 3.14.8). If a newer 3.14.x is wanted, `uv python install 3.14` downloads one (file, size and checksum to be shown to the owner first; I did not run it). Do not use Homebrew's Python: it is the cause of the macOS 27.0 minimum, and its `pyexpat` needs the OS's expat 2.7.2 or newer (see the static survey below).

**2. Commands** (the same two edits are in `research/proposed-platform-reach/shotfleet-and-build.diff`, to `packaging/build.sh`):
- the OCR helper line becomes `swiftc -O -target "$ARCH-apple-macos13.0" ocr.swift -o build/ocr` (`ARCH=$(uname -m)` is already set above it; `-target` goes right after `-O`). Measured: minos 13.0; the arm64 and the x86_64 builds both compile, and the arm64 one printed Vision's language list. The Swift runtime symbols it imports change with the target (static survey), so the flag matters for running on macOS 13, not only for the number.
- the venv line becomes `"${PYTHON:-python3}" -m venv build/venv`, and the build is started as `PYTHON=$(uv python find 3.14 --managed-python) packaging/build.sh` (with `DEVELOPER_ID`, `NOTARY_PROFILE`, `INSTALLER_ID` as for any release). `build/` is wiped at the top of the script, so the venv is always new.
- PyInstaller 6.22.3 (what `pip install --upgrade pyinstaller certifi` gave the last build; hooks-contrib 2026.8). I did not run pip: I used the packages already in `/Users/manu/Developer/shotfleet/build/venv/lib/python3.14/site-packages` through a `.pth` file in a venv made from the Python above, and the command line of `build.sh` minus signing: `--onedir --name shotfleet --add-binary <ocr>:. --add-data skill:skill`.
- **No `MACOSX_DEPLOYMENT_TARGET` is needed or used**: PyInstaller compiles nothing (its prebuilt bootloader is minos 11.0), the interpreter's own value is 11.0, and `swiftc` takes `-target`.
- `build.sh`'s signing loop needs no change: it signs whatever Mach-O files the folder holds (3 or 4 here instead of 56); the `*.framework` loop then finds nothing, which is fine.

**3. Checks afterwards.**
1. `python3 tools/macho-minos.py dist/shotfleet --max 13` must exit 0. Measured on my scratch folder: 2 files at 11.0 (bootloader, libpython), 1 at 13.0 (`ocr`), "needs macOS 13.0 or newer". Run it on the **extracted release tarball** too, because that is what ships.
2. `dist/shotfleet/shotfleet --version` printed `shotfleet 0.1.1` (scratch, unsigned, 21 MB against 20 MB for the Homebrew folder).
3. `shotfleet doctor`: the Android and iOS lines were ready. Text recognition could not be judged: macOS's recognition model compile failed with its known `e5rt` error under this Mac's load (the gate notes mention it), so the bundled `ocr` of the new folder is **not proven to read text**. Run `check` on a fixture screenshot on a quiet Mac.
4. `build.sh`'s own quarantined `--version` run (after notarization), and `spctl` and `stapler` on the package, as for every release. Untested: signing and notarizing a folder whose only dylib is a 17 MB `libpython3.14.dylib` with the hardened-runtime entitlements; standalone Python has not been through the notary here.
5. Licence and TLS from the frozen program: the standalone Python links OpenSSL 3.5.5 statically and `build.sh` adds certifi as before. My scratch build had no certifi, so the licence HTTPS call (`tools/release-candidate.sh`, gate G6) must be re-run on this build.
6. The only proof of "runs on macOS 13 to 26" is a run there (see the VM and runner section).

**What broke or surprised me.** (a) Homebrew's folder has 56 Mach-O files, the standalone one 4: its stdlib extension modules (pyexpat, _ssl, _hashlib, zlib) are inside libpython, so there is less to sign and no OS-library dependency for them. (b) Homebrew's Python, not PyInstaller, set the macOS 27 minimum. (c) My first scratch `doctor` said "can't start" because I had named the helper `ocr-arm64`; `build.sh` names it `ocr`, so this does not apply to the script. (d) This agent's shell hook refuses compound commands, so everything here ran as plain commands or small Python scripts; irrelevant to the build.

## Static survey: what the 0.1.0 folder needs that older macOS lacks

Method: on `/Users/manu/Developer/shotfleet/dist/shotfleet` (56 Mach-O files: the bootloader, `Python.framework`, 5 bundled dylibs, `ocr`, 48 stdlib `.so`): `otool -L` for linked libraries, `nm -u -m` for imported symbols (strong or weak), and the headers of Xcode 27's SDK (`__API_AVAILABLE` or `__OSX_AVAILABLE` per declaration) for the macOS that introduced each libSystem symbol. Scripts: `research/proposed-platform-reach/static-survey-*.py.txt`. No new build.

| What | Finding | Breaks on | Confidence |
|---|---|---|---|
| Weak imports | 0.1.0 has no weak (availability-guarded) import of a libSystem symbol except `inet_aton`: with minos 27 the `@available` guards compile away. The standalone build imports `_mkfifoat`, `_mknodat`, `_inet_aton` and `__availability_version_check` weak, i.e. guarded | n/a | measured |
| libSystem (488 symbols imported across the files) | all 10.15 or older except `preadv`, `pwritev` (macOS 11.0) and **`mkfifoat`, `mknodat` (macOS 13.0)**, imported strong by `Python.framework` | macOS 12 and older: `dyld: Symbol not found: _mkfifoat` when loading Python | high for the symbols and the 13.0 (SDK header); medium for "dyld refuses at launch" (the usual behaviour for a strong import) |
| `pyexpat.so` against `/usr/lib/libexpat.1.dylib` | imports `XML_SetAllocTrackerActivationThreshold` and `XML_SetAllocTrackerMaximumAmplification`; the SDK's `expat.h` says "Added in Expat 2.7.2"; this Mac's libexpat is 2.7.4. `shotfleet.py` line 20 imports `plistlib` and line 22 `xml.etree`, both of which import `pyexpat`, so **start-up fails** wherever the OS's libexpat is older than 2.7.2 | any macOS whose libexpat is older than 2.7.2. I could not look up which macOS releases ship which expat, so whether macOS 26.x is covered is unknown | symbols and "2.7.2" measured; the versions per macOS unknown |
| `ocr` helper | compiled at target 27: imports the newer Swift runtime entry points `_swift_getTypeByMangledNameInContext2` and `...InMetadataState2` and some ContiguousArray specialisations, and links `libswift_Builtin_float.dylib`; the same source at target 13 imports the older `...InContext` entry points and `libswiftDarwin` instead (diff of `nm -u`) | macOS 13 and 14, possibly later (an OS Swift runtime older than the compiler's); `check` loses the Vision reader | high that the symbols differ; medium on which OS first has the new ones |
| Linked system libraries | `libSystem`, `libobjc`, `libz`, `libbz2`, `libexpat`, `libffi`, `SystemConfiguration`, `CoreFoundation`; for `ocr` also Foundation, CoreGraphics, CoreText, Vision, NaturalLanguage and `/usr/lib/swift/libswift*.dylib` shims. All exist on macOS 11 and 13 as far as I know (`libswift_Builtin_float` probably not) | | medium: names only |
| Bundled `@rpath` libraries | libssl, libcrypto, libmpdec, liblzma, libzstd: independent of the OS; the OS symbols they use are libSystem ones, covered above | | medium |
| Framework symbols (Foundation 18, CoreGraphics 9, CoreText 5, Vision 5, ...) | not checked one by one (Objective-C classes and Swift overlay symbols are not in `/usr/include`) | | low |

So the 0.1.0 folder cannot start on macOS 12 or older (libSystem), may not start on macOS 13 to 26 (expat, and `ocr`), and has only been seen to run on macOS 27.0. The standalone build removes the first two by construction (weak guards, built-in expat 2.6.3) and `-target 13.0` removes the third. This is static reasoning, not a run. Not covered: Objective-C and Swift behaviour at run time (for example Vision revisions on macOS 13), dyld policy differences between releases, Python modules I did not see imported.

## Testing older macOS without an older Mac (nothing run or triggered, no downloads; web sources read 2026-10-05)

**macOS VMs on this Apple-silicon Mac (an M1 Pro).**
- Apple's Virtualization framework runs a guest that is the same as or older than the host. The oldest guest depends on the chip: M1, M2 and M3 hosts can run macOS 12.0.1 and newer; an M4 host only 13.4 and newer; **macOS 11 cannot be virtualized on any Apple-silicon chip** ([eclecticlight.co, 2024-11-14](https://eclecticlight.co/2024/11/14/m4-macs-cant-virtualise-older-macos/); secondary and from 2024). So macOS 13, 14, 15 and 26 guests are possible here, 11 is not.
- Tools: **Tart** (Cirrus Labs; Fair Source licence, royalty-free on personal workstations, a paid licence above 100 CPU cores in server installations: [tart.run/licensing](https://tart.run/licensing/)) has prebuilt images for Monterey, Ventura, Sonoma, Sequoia and Tahoe in vanilla, base and xcode variants (`tart clone ghcr.io/cirruslabs/macos-<name>-base:latest`; default 2 CPUs and 4 GB RAM; [tart.run/quick-start](https://tart.run/quick-start/)); a base image is about 25 GB (search result, not verified). UTM and Parallels use the same framework and the same limits.
- Licence: Apple's macOS licence allows 2 additional macOS instances on one Apple computer for development and testing, and the kernel enforces 2 running VMs ([khronokernel, 2023-08](https://khronokernel.com/macos/2023/08/08/AS-VM.html)). Enough for one old and one new guest.
- Cost here: free software; 25 to 50 GB of disk per guest (`STATUS.md` row 16 puts this Mac's free disk at 17 to 33 GB) and 4 GB of RAM or more per guest while the host already swaps (21 GB swap, load 840, reported today). **Not feasible on this Mac now**; feasible on a quiet Mac with 60 GB or more free.
- Xcode and the iOS Simulator are reported to work inside a macOS guest (secondary sources, not verified by me). The Android emulator needs hardware virtualization inside the guest, which Apple offers only on M3 or M4 hosts with a macOS 15 guest, according to [Tart's FAQ](https://tart.run/faq/) (a passing remark there); on this M1 Pro an Android run in a guest does not work.

**GitHub-hosted macOS runners, manual only (`workflow_dispatch`, as `ci.yml` already is).** From [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) and [pricing page](https://docs.github.com/en/billing/reference/actions-runner-pricing), fetched 2026-10-05:

| Label | macOS | CPU | vCPU / RAM | $ per minute |
|---|---|---|---|---|
| `macos-14` | 14 | arm64 (M1) | 3 / 7 GB | 0.062 |
| `macos-15` | 15 | arm64 (M1) | 3 / 7 GB | 0.062 |
| `macos-26`, `macos-latest` | 26 | arm64 (M1) | 3 / 7 GB | 0.062 |
| `macos-15-intel`, `macos-26-intel` | 15, 26 | Intel x64 | 4 / 14 GB | 0.062 |
| `macos-13` and older | not listed | | | |
| larger: 12-core Intel, 5-core M2 Pro | | | 30 GB, 14 GB | 0.077, 0.102 |

There is **no macOS 13, 12 or 11 hosted runner**: the oldest is macOS 14. The rates are those listed for standard macOS runners (private repos; the E1 runs used a private repo). I did not confirm on that page whether standard runners are free for a public repo, nor the included-minutes multiplier for macOS. Estimate: 5 to 8 minutes per OS (install, `--version`, `doctor`, `check` on a few fixture screenshots) is about $0.31 to $0.50 per OS, so macOS 14, 15 and 26 arm64 plus 26 Intel is under $2 (my arithmetic, not GitHub's). An Intel runner shows whether the arm64 folder is refused cleanly; it cannot test an Intel build. The owner's rule is "run checks locally, not GH Actions", so each run needs their yes. GitHub states nested virtualization is not supported on its arm64 macOS runners, so no Android emulator there.

**What such a test can prove:** the notarized tarball unpacks and `shotfleet --version` starts (the dyld, libexpat and Swift-runtime questions of the survey), `doctor` runs, `check` reads fixture PNGs through the bundled `ocr` and the Python readers, and `install.sh` works from the live URL; a VM adds Gatekeeper behaviour for a browser download. **What it cannot:** Android emulator runs, real devices, the Xcode 27 plus iOS 27 combination (guests and runners carry other Xcodes), and timing (3 vCPUs or a guest is slower than this Mac). iOS simulator runs are possible in principle in both, since the simulator needs no nested hypervisor, but need the fixture build and an Xcode on that image; they are not part of the cheap test.

**Recommendation for testing:** first run `tools/macho-minos.py` and the survey scripts on the real release tarball (free, a minute); then one manual runner job each on `macos-14` and `macos-15` (about $1) that installs the 0.1.1 tarball and runs `--version`, `doctor` and `check` on the fixture's committed screenshots; a VM only if a macOS 13 result is needed and a Mac with the disk is available.

## Hosted-runner test of the LIVE 0.1.1 on macOS 14 and 15 (measured 2026-10-05)

Workflow `.github/workflows/macos-compat.yml` (manual only), two dispatches. Run 1 (https://github.com/noloman/shotfleet/actions/runs/37303612329) failed only because the script accepted `doctor` exit 0 or 1 and `doctor` exits 2 when the Mac is not ready; its `check` step was skipped. Run 2 (https://github.com/noloman/shotfleet/actions/runs/37304115758, after PR #65) succeeded. Cost: 4 jobs of 15 to 30 s, about 4 billed macOS minutes, roughly $0.25 for both runs. Each job installed the live `install.sh` into a temporary HOME on an Apple-silicon GitHub runner.

| | macOS 14.8.9 (macos-14) | macOS 15.7.9 (macos-15) |
|---|---|---|
| install.sh (download, checksum, install) | ok, "installed shotfleet 0.1.1" | ok, same |
| `shotfleet --version` | `shotfleet 0.1.1` | `shotfleet 0.1.1` |
| `shotfleet doctor` | exit 2 (not ready: no Maestro, no Android system image; java, swiftc, simctl, adb, emulator, avdmanager, aapt2 ok), "text recognition ready in 1 s", iOS runtime 18.2 found, about 9 s | exit 2, same findings, "text recognition ready in 1 s", iOS runtime 26.2 found, 20 s |
| `shotfleet check` on 2 sample PNGs (ca, de) | exit 1: 2 problems, both "315x560 isn't an App Store screenshot size" (the sample PNGs are downscaled copies); "macOS can't read the script of ca", so ca was only checked for another language | exit 1: 3 problems: the same two size problems plus "ca/02_advanced.png: text looks like 'en', expected 'ca'" |
| job wall time | 16 s | 29 s |

**What this proves:** the live 0.1.1 installs from the live site, starts, runs `doctor` to the end, compiles and runs the bundled `ocr` helper (text recognition ready in 1 s) and runs `check` to a report, on macOS 14.8.9 and 15.7.9 on Apple silicon, with no dyld, expat or symbol error. Together with the 0.1.0 measurements (52 of 56 files need macOS 27.0) this shows the standalone-Python rebuild removed the start-up wall on 14 and 15.

**What it does not prove:** macOS 13 (no hosted runner), macOS 26.0 to 26.2 (none either, so the Expat question on 26.x for 0.1.0 stays unmeasured; 0.1.1 bundles Expat), simulators and emulators (the runner has no running simulator; Maestro is absent), Gatekeeper (curl sets no quarantine flag), the licence call from the packaged program, a real buyer's Mac, a clean user account with no Homebrew (the runner has Homebrew and Java, and install.sh used /opt/homebrew/bin).

**New finding, from the OS difference:** the same Catalan screenshot is judged differently. On macOS 14 the text reader cannot read Catalan, and `check` says so and skips the language test; on macOS 15 it reads the screenshot and calls it English. That wger screen may really contain English text (not checked against the app), so this may be a true detection or a false one; either way a buyer on macOS 15 can see a language problem for a screen that macOS 14 does not judge. The sample size problem is an artefact of using downscaled sample files, not a product problem.
