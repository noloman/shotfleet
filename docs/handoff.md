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
| 3 | A real Flutter, Expo and React Native app captured end to end | **done 2026-10-03 on a Mac** (wger, obytes, kotlinconf-app; `research/frameworks.md` section 15); bare React Native and Linux/KVM runs still open | |
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

**A public app for that comparison now exists:** wger (commit `cf12708`, `flutter build apk --debug`, 19 languages, flow `research/real-apps-2026-10-03/wger-android/flow.yaml`). Mac, 2026-10-04: 19/19 captured, `wall_seconds` 822 on 1 emulator (memory pressure cut 2 to 1), with another session's emulator loading the Mac for the first ~13 minutes, so it is an upper bound, not a clean timing; a clean Mac rerun is queued (device queue line 8). The flow needs the `Title.*` selector translation from PR #29 (not in `main` before it). `research/frameworks.md` section 16.

## 3. Real Flutter, Expo and Compose apps, end to end

**Done 2026-10-03 on a Mac** (iOS and Android; evidence in `research/frameworks.md` section 15 and `research/real-apps-2026-10-03/`): wger (Flutter), the obytes template (Expo, Release) and JetBrains' kotlinconf-app (Compose Multiplatform) were built, `init`ed with no arguments, run in two languages each and checked; README, `site/public/docs.html`, `skill/` and claims C035 and C121 name those apps and nothing more. Language reached all three on both platforms; `-AppleLanguages` and `set-app-locales` need no change.

**Still open from this item**
- Bare React Native (Rocket.Chat or Ignite from section 12), and a Flutter or Expo app that is not one of these two.
- The same on a KVM Linux box (Android only) for the timing.
- **Blank screenshots: done (2026-10-04).** `check` flags a flat frame and `run` captures that language again once, then reports it. On a device (KotlinConf iOS, no wait) the second capture was blank again, so the flow must wait for text; see `research/frameworks.md` section 16.
- **Still to run on a device** (the 2026-10-04/05 follow-up window produced nothing: `research/frameworks.md` section 17; it needs a quiet Mac, and each job a hard time limit): Rocket.Chat with a real flow (the starter flow only caught the splash); wger iOS in all 19 languages (the first try hung on a stuck simulator); a clean wger Android 19-language timing for the Linux comparison (E1; the 2026-10-04 run of 822 s on 1 emulator ran under another session's load); a clean KotlinConf iOS pair with a longer wait (the 2026-10-03 evidence image `kotlinconf-ios/en-01_privacy.png` is blank).
- **`run` keeps stale language folders:** a partial rerun keeps the other languages on purpose; `check` now says which language folders are not from this run (a note, not a problem), so a stale `ja` is no longer mistaken for part of a 19-language run.
- **Flutter debug builds show the DEBUG banner on iOS and, with a debug APK, on Android;** `init` already warns. A `release` APK on Android is untried with shotfleet.
- **Marketing and draft pages may still say "not yet run on a real Flutter or React Native app"** (`site/draft/`, `marketing/kit/`, `research/`): left alone on purpose, they are conservative. Update them when the posts are rewritten. `site/public/alternatives.html` was wrong in the other direction and was fixed in the 2026-10-05 docs refresh (audit A1): it now says one real Flutter app (wger) and one real Expo app (the obytes template).
- Xcode 27 and these three builds: see the "did not pass" table; none of it is shotfleet's, but a `doctor` or README note could save a buyer an afternoon (`expo run:ios` cannot open the Simulator; `IPHONEOS_DEPLOYMENT_TARGET=15.1`; `ARCHS=arm64` for KMP).

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

- **Xcode 27 final replaced Simulator.app with Device Hub** (`docs/compat.md`: shotfleet never opens Simulator.app and Maestro only does so when it starts a simulator itself, which shotfleet never asks it to). **Run 2026-10-04 on Xcode 27.0 (27A266a), macOS 27.0 with the iOS 26.4 runtime: 36 of 36 assertions, no `open -a Simulator`, status bar and 1320x2868 right** (`STATUS.md` row 9). **iOS 27, 2026-10-05: works on one simulator, one language; the 4-simulator e2e is untested.** An iOS 27.0 (24A434) runtime was installed on this Mac by another session (the image is 8.05 GB; `xcodebuild -downloadPlatform iOS` also installs it, even with `-exportPath`). The full e2e on it passed build, init and doctor, then `shotfleet run` had not finished at the 35 min limit, at load 735 and swap 21.6 of 22.5 GB (the iOS 26.4 pass ran at load about 120). `tools/ios27-repro.sh` (one simulator, one language, per-step kill limits) then passed on a quiet Mac: `shotfleet run` captured 1/1 locales in 78 s with 0 problems, and the unified log shows no `open` process for that window (checked afterwards). So the stall did not reproduce and is consistent with load, but it is not proven. **Still open:** the full e2e (4 simulators, iPhone and iPad) on iOS 27 on a quiet Mac, optional. Details in `research/xcode-27-ios27-attempt-2026-10-05.md`. The default runtime (`latest_ios_runtime()`) is the newest installed, so anyone with iOS 27 installed gets it in `init`: pin `runtime` in configs on a shared Mac. If `simctl` or the driver behaves differently on iOS 27, `shotfleet.py`'s simulator functions are where to look.
- **Apple's screenshot specifications change often** (8 Jul, 19 Aug, 9 Sep). The sizes are now watched by `tools/apple-specs-watch.py` (run it monthly with `tools/watch-upstream.sh`): it
  compares every size on Apple's page with `APPLE_SIZES` and was run on the real page on 2026-10-03 (45 distinct sizes, table matches; it also found four old-device landscape sizes
  that were missing, now added). The prose rules (count, alpha, which set is required) are not machine-read: read the page once a month. iPhone Duo sizes are known; Apple opens
  uploads for it "later this year", so `export` for Duo is untested. `tools/watch-upstream.sh` runs this and the Maestro check together. The two GitHub workflows for them are manual-only; nothing is scheduled.
- **Team / CI demand test and the layout check** are decided by the experiments in section 7 of the strategy note, after launch; do not build them before.

## Known small things, not blocking

- `tools/pretend-mac.py <test module>` runs a test module as if on an Apple-silicon Mac (platform and CPU only). It reproduced both macOS-only failures of the
  `doctor --fix` tests before CI did; use it on new tests, but it does not replace a Mac.
- Older test modules leak a few sockets (`ResourceWarning`); harmless, not from the new tests.
- **iOS driver start at 4 simulators on Maestro 2.11.0:** the CrossfitTracker run of 2026-10-04 passed 19/19 but 9 of 19 languages (18 in an earlier run) needed shotfleet's retry because two of four parallel simulators did not get their XCTest driver ready within 240 s (`research/maestro-2-11.md`, last section). Answered 2026-10-05: the same run on Maestro 2.0.10 with `parallel = 4` (iOS 26.4) passed 19/19 on the first attempt with no retry (404 s), so this is specific to 2.11.0; if 2.11.0 is ever promoted, try a longer `MAESTRO_DRIVER_STARTUP_TIMEOUT` or staggered driver starts first.

## 13. State at the end of 2026-10-05 (device-queue coordinator wrap-up)

History: this section was written while 0.1.0 was live. Section 14 is the state after 0.1.1 and section 15 the state after 0.1.2 (the latest).

- **shotfleet 0.1.0 is LIVE** (go-live ran 2026-10-05 08:02-08:11: `5fa4f7c` Gumroad product ID, `5bbec86` Site: sale open). Evidence: `research/go-live-gate.md`: G3 65/65 on the signed build of main 081853b (iPhone, iPad, Android; real licence), G10 production smoke 36 checks / 0 failed, live archive's checksum, signature and quarantined run verified. Not run: a real `install.sh` from the live URL into this Mac's real PATH (it can link into /opt/homebrew/bin; use a temp HOME), G8 (real apps with the release binary) and a refunded real key (needs a real sale).
- **Merged today after a full local gate (798 tests, 59 worker checks, exit 0):** #40 (small experiments), #32 (launch-article verification; `site/draft` is not deployed).
- **Open PRs that change `shotfleet.py` (next release, 0.1.1), do not merge blind:** #29 (first real Flutter/Expo/Compose runs, has conflicts), then #31 (stacked on #29; its blank-frame retry, Flutter release APK, Arabic secure field and wger in 19 languages were never verified on a device), #44 (Android screen text from the UI hierarchy, Maestro 2.7+; device run pending), #37 (Xcode 27.0 on the iOS 26.4 runtime, 36/36; conflict in STATUS.md, its session merges it). Each needs: rebase on main, `tools/check-claims.sh` exit 0, the device run named in its PR, then a release rebuild and the fixture e2e gate (G3) on the exact build before publishing.
- **Android screen text from the UI hierarchy (PR #44):** on Maestro 2.7.0+ `run` reads each Android screenshot's text from Maestro's per-step hierarchy instead of OCR (`research/limits-text.md` 1g); fixture e2e on 2.11.0 passed 30/30 with hierarchy evidence on 8/8 screenshots. Not yet run: two emulators at once.
- **Maestro:** 2.0.10 and 2.11.0 both pass the fixture e2e (iOS 36/36, Android 29/29; 2.11.0 with the relative-screenshot-names fix, PR #35 merged earlier). A two-emulator Android `[inputs]` check on 2.11.0 and the iOS 27 runtime (8.05 GB, ~0.5 MB/s: needs a fast connection or an overnight download; do not import it while other jobs run, it changes `latest_ios_runtime()`) are the open device items.
- **Running device jobs on this Mac (shared by many agent sessions):** use the lock protocol in `docs/device-queue.md`. Every run script or waiter needs a hard time limit (an unbounded waiter held the lock for 8 h overnight); check ownership of a process or folder before killing or deleting it (a work dir deleted by mistake voided a release gate run); `simctl` wedges under load (CoreSimulatorService restart is a user decision: it stops every booted simulator).
- **Disk:** swung between 11 and 50 GB on 2026-10-04/05; AVD images (35 GB in ~/.android), CoreSimulator (43 GB), Gradle caches (33 GB) and session scratch in /private/tmp (56 GB) are the big items. shotfleet's own simulator cache (shotfleet-*) is recreated on demand.
- **Next release:** the plan for 0.1.2 (scope, estimates, risks, device slots, order) is in `research/0.1.2-plan.md`.

## 14. State after 0.1.1 (2026-10-05, evening)

History: 0.1.1 was live from 13:27 to 16:07 on 2026-10-05; section 15 is the current state.

- **shotfleet 0.1.1 is LIVE since 13:27** (Cloudflare version 65c62221, rollback target 609fa866): tarball 10,705,287 B sha256 6f6b5bfc..., installer package 10,723,486 B, built from commit e2e1998 (main 2ccda21) with a standalone Python 3.14.2, minimum macOS 13. Device gate 65 of 65 in 54 min 57 s (iOS pinned to 26.4), production smoke 36 checks, 0 failed. Evidence: `research/release-0.1.1-evidence-2026-10-05.md`.
- **Hosted-runner result:** the live 0.1.1 was installed on GitHub's Apple-silicon macOS 14.8.9 and 15.7.9 runners: `install.sh`, `shotfleet --version`, `doctor` (to the end) and `check` on two sample screenshots all worked (`research/limits-platform-reach-2026-10-05.md`). Not shown: simulator runs there, macOS 13, macOS 26.0 to 26.2, a clean Mac. The range on the pages stays "13 or later; tested on macOS 27".
- **Catalan finding:** the same Catalan screenshot was skipped on macOS 14.8.9 ("macOS can't read the script of ca") and judged "looks like 'en'" on 15.7.9: older macOS reads fewer languages than the 33 of macOS 27 (`research/limits-catalan-check-macos-2026-10-05.md`). README and docs now say so.
- **Gradle-daemon lesson:** idle Gradle daemons from several projects held about 21 GB; four simulators then thrashed (the 0.1.1 gate took 55 minutes instead of about 25 until seven daemons were stopped). Run `./gradlew --stop` once per Gradle version before a device job (`docs/owner-note-0.1.1.md`).
- **Docs refresh:** the audit `research/docs-audit-2026-10-05.md` (branch `claude/docs-audit`) was applied on `claude/docs-refresh`; `research/README.md` lists what was applied and what was not.
- **Next:** `research/0.1.2-plan.md`. A refund or a disabled key: `docs/refund-runbook.md`.

## 15. State after 0.1.2 (2026-10-05, evening; the latest)

- **shotfleet 0.1.2 is LIVE since 16:07** (published 16:05:53 to 16:07:13). Cloudflare version d5ef4236-b146-4ce8-8ffb-5b18c6eb9ba5; the rollback target is b64119e0-3b6c-4355-827b-51c31bdb7157. Site deploys that day, in order: 609fa866, 65c62221 (0.1.1), ec2f56f5 (docs refresh), b64119e0 (fail-open docs), d5ef4236 (0.1.2). Tarball `shotfleet-0.1.2-macos-arm64.tar.gz` 10,709,291 B sha256 00673ba0dd268476e676dfe286cd31708530571222bb8d8300129c2e5941d422; installer package 10,728,218 B sha256 1b229f2c5540820515adbc78ff46d34ca6af9909966ba9b689b0c2be6106c60d. Built from main adbe90d (VERSION 0.1.2); main at publish time was 0a24e8d, which differs from adbe90d only under `research/`. Standalone Python 3.14.2. Notarization Accepted (zip a7cb0248-f170-409e-9567-1b83126955a8, pkg 8de6fe64-e63b-4733-a84c-8cc8ff0c616e), package stapled. Declared minimum macOS: two files 11.0, the `ocr` helper 13.0, identical to 0.1.1 (`tools/macho-minos.py`). What it contains: `CHANGELOG.md`, section 0.1.2.
- **How it was published: the first real production run of `packaging/publish.sh`.** It had been rehearsed before on the staging worker `shotfleet-staging` (`/Users/manu/Developer/shotfleet-rc-build/staging-rehearsal/`, the pipeline notes in `research/limits-release-engineering-2026-10-05.md`). The run: manifest and SHA-256 check of the two tested files, clean tree at origin/main with `VERSION`, `shotfleet.py`, the top CHANGELOG heading and the docs "Last checked" line agreeing, record of the live Cloudflare version id, stage the files, archive the shipped bytes, `wrangler deploy`, verify the served bytes (VERSION, tarball and pkg hashes, `install.sh` 200), `tools/golive/smoke.sh` (36 checks, 0 failed), a live install into a temp HOME (`shotfleet 0.1.2`). Log: `/Users/manu/Developer/shotfleet-rc-build/0.1.2/publish.log`. This was also the first build with the pinned inputs (`packaging/requirements-build.txt`, `pip --require-hashes`): no problem.
- **Rollback:** record `/Users/manu/Developer/shotfleet-rc-build/release-archive/state/rollback-0.1.2-20261005-160553.txt` (holds b64119e0). Command: `cd site && npx --yes wrangler@latest rollback b64119e0-3b6c-4355-827b-51c31bdb7157 -y` (the publish script runs it by itself on a failed verification; it was not needed). The shipped bytes, with the previously live files, are in `/Users/manu/Developer/shotfleet-rc-build/release-archive/archive/0.1.2`. A rollback of the Worker does not change what Gumroad or buyers' installed copies hold.
- **Gate evidence (nothing here is "tested" beyond what is listed):** `tools/verify-release.sh`: PASS 12 checks on the built files, PASS on the live downloads (8 checks tarball, 4 checks pkg). Non-device proofs on the build, all PASS: quarantined `--version`, spctl and stapler, codesign (hardened runtime, team 2357A78TMR), `env -i` start, TLS in the frozen build (a made-up key reached Gumroad and was refused, nothing written), `check` on 72 real screenshots with 0 problems (frozen 338 s, from source 318 s), `install.sh` in a throwaway HOME (a wrong checksum is refused). Details: `/Users/manu/Developer/shotfleet-rc-build/0.1.2/proofs.out` and `progress.log`.
- **Device gate on the signed build: PASS, all 65 assertions** (66 PASS lines; 0 FAIL; started 15:27:29, finished 16:04:31, 37 minutes; iOS runtime pinned to 26.4; iPhone, iPad and the Android fixture). Notable: the iPhone phase captured 4 of 4 languages in 59 s; in the iPad phase 3 of 4 simulators "stopped answering" (`simctl terminate` over 300 s) at load 700 and above, and shotfleet recovered by itself and finished 4 of 4 languages in 100 s on one simulator with 0 problems (the capture-reliability changes working). End of the gate: load 12, free memory 66 %, swap 6.0 GB. Log: `/Users/manu/Developer/shotfleet-rc-build/0.1.2/g3-012.log`.
- **Not tested on 0.1.2:** macOS 13 and 26.0 to 26.2, a clean Mac, hosted macOS 14 and 15 (those hosted runs were on 0.1.1, section 14), the 4-simulator e2e on iOS 27, a refunded real key. The public line stays "Built for macOS 13 or later on Apple silicon (tested on macOS 27)."
- **Gumroad:** the Sales page showed NO sales at all (read-only check, 2026-10-05 15:48), so no 0.1.0 or 0.1.1 buyer exists and the update email is not needed yet. Put "to update, run the install line again" on the receipt or in a Gumroad purchase Workflow. The Gumroad description carries "Built for macOS 13 or later on Apple silicon (tested on macOS 27)."
- **Correction to earlier notes: macOS text recognition was NOT permanently wedged, and NO REBOOT is needed.** A root `ANECompilerService` showed bursts of cold compiles (23 minutes of CPU in 50 minutes, 0.0 % when idle). A cold compile of the OCR helper takes 35 to 122 s at load 550 to 890, while shotfleet waits about 60 to 90 s, so `check` says it isn't answering. `usesCPUOnly` and the compute-device APIs do not avoid the compile (`research/workarounds-text-recognition-2026-10-05.md`). So the launch-article items 01/2 and 01/5 are not blocked by a reboot: they need a quiet Mac. Wording elsewhere that still says "restart the Mac" (README Limits, the skill's troubleshooting table, article 01, ROADMAP.md) is owned by other changes and is not edited by this section.
- **Agent habits:** the resume hook `cleanup-orphan-agents.sh` was removed from the owner's Claude settings (it killed working agents). What stays: run long steps detached, keep a RESUME.md, push WIP often.
- **Open for 0.1.3** (none started; the coordinator's plan): PR #44 (Android screen text from the UI hierarchy; not shipped in 0.1.2); the text-recognition patch (wait on the ANE compile up to 6 minutes and print the exact message); the capacity planner in warn-only mode, a Maestro deny list and a cheap Maestro watcher (`research/workarounds-maestro-resources-2026-10-05.md`); `selftest.sh` into `tools/`; the `docs/linux.md` fix; versioned download URLs, with a GitHub Action and a Homebrew tap draft, if the owner agrees (`research/workarounds-reach-distribution-2026-10-05.md`); a Maestro measurement at 4 iOS simulators (2.0.10 took 404 s, 2.11.0 took 826 s with retries); the older-macOS proof (Tart VMs for macOS 13.6, 26.0 and 26.2, or a volunteer's Mac running research/proposed-selftest/selftest.sh from the branch claude/workarounds-older-macos; `research/workarounds-older-macos-2026-10-05.md`). The order and the owner decisions: `research/strategy-roadmap-2026-10-05.md`.
- **Still the owner's:** KvK and tax, one real paid sale by a second person to prove a refunded key is refused, launch posts, the items in `docs/owner-note-0.1.1.md`. `STATUS.md` "What is left to do" lists them.
