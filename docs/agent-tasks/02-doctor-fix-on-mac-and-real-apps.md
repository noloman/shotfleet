# Try doctor --fix on this Mac, then the real-app regression

**Needs:** your Mac, network, about 1 hour.

## Context

`shotfleet doctor --fix` was run for real on Linux only. On macOS three things are unverified: the Temurin JRE tarball layout (`install_jre` renames the extracted folder to `~/.shotfleet/jre`; `find_java` then looks in `~/.shotfleet/jre/Contents/Home`), the `brew install --cask android-commandlinetools` branch when Homebrew exists, and Google's `mac_arm64` command-line tools archive when it does not. Read `docs/handoff.md` items 4 and 6.

## Steps

Part A (needs network, about 20 minutes): `export SHOTFLEET_HOME=$(mktemp -d) ANDROID_HOME=$(mktemp -d)` and a PATH without Maestro and Java (for example `PATH=/usr/bin:/bin:/usr/sbin:/sbin`). Run `python3 shotfleet.py doctor`, then `python3 shotfleet.py doctor --fix --yes`, then `doctor` again. Record which plan steps were shown, whether each ran, and whether `doctor` then reports Maestro 2.0.10 and Java ok. Try both Android branches: once with Homebrew on the PATH and once with `brew` hidden (a PATH without /opt/homebrew/bin). If the JRE step fails because the folder layout differs, fix `install_jre` / `find_java` and add a test; look at the real extracted folder, do not guess.
Part B: the real-app regression of `STATUS.md` plan A2, on Maestro 2.0.10: CrossfitTracker iOS (18 languages), Android phone and tablet, Remoti iPhone + iPad. Use the project's docs for how each app is built (README, PLAN.md, `examples/crossfittracker/`).

## Passed when

Part A: `doctor` reports Maestro and Java ok after `--fix`, on both Android branches. Part B: 0 problems from `check` and timings in the README's range (iOS 18 languages about 9 minutes, Android about 15).

## Record

`STATUS.md` rows D1 and 10, claim C126 in `tests/claims.json` (stays `partial` unless both Part A branches passed), `docs/handoff.md` (delete what is done, keep what is not); timings into `README.md` only where they changed.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
