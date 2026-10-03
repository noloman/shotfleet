# Run the Android fixture on Linux with KVM (experiment E1)

**Needs:** a Linux machine (x86_64 or arm64) with a usable `/dev/kvm`. If the machine has none, stop at step 0 and say so: the emulator refuses x86_64 images without `vmx`/`svm` and an arm64 image on an x86_64 host.

## Context

`check`, the Android readers, `doctor`, `doctor --fix` and `packaging/build-linux.sh` work on Linux (PR #8, #11, `docs/linux.md`). The emulator was never started: the development sandbox had no hardware virtualization. This is experiment E1 of `docs/linux.md` and `docs/handoff.md` item 2.

## What is already known (2026-10-03, one hosted-runner attempt; read `docs/linux.md`, section "E1 result", once the E1 PR is merged)

On a GitHub-hosted 2-vCPU runner everything up to the first flow step worked and 9 of 13 assertions passed; then Maestro could not find the localized "Next" button in any of the four languages. Open question: slow 2-vCPU runner or a real Linux difference. On your machine, compare: if it passes with 4+ cores it was the runner; if it fails the same way, look at the screenshot Maestro took before the failing step (`<work dir>/proj-android/out/.work/debug/`) and at `maestro.log`.

## Steps

0. `ls -l /dev/kvm` and `egrep -c '(vmx|svm)' /proc/cpuinfo` (must be non-zero on x86_64).
1. `python3 shotfleet.py doctor --fix --yes` (fetches Maestro, Java, the Android tools and an x86_64 system image; a large download).
2. `sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-jpn tesseract-ocr-ara tesseract-ocr-tur`.
3. `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android --keep`.
4. Then an 18-language `shotfleet run` of a real Android app on that machine, for the timing to compare with 15 min 24 s on the Mac.

## Passed when

The last line of step 3 is `PASS: all N assertions passed`.

## Record

`STATUS.md` row E1: the `machine:` and `cpu:` lines the script prints, the seconds of the `android: shotfleet run` phase, any FAIL lines. Add the measured timing to `docs/linux.md`. Do not claim Linux support in README or the site from this alone.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
