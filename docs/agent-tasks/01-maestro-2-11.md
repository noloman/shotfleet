# Run Maestro 2.11.0 on the fixture apps, then promote it

**Needs:** your Mac (Apple silicon, Xcode, Android SDK), about 40 minutes.

## Context

Maestro 2.11.0 is the newest release. It passes the device-free screen `tools/maestro-compat.py` (28 of 28, same as 2.0.10) but has never run on a device, so `MAESTRO_TESTED` in `shotfleet.py` is still `("2.0.10",)` and `doctor` says 2.11.0 "may work". Read `docs/handoff.md` item 1 and `docs/compat.md`.

## Steps

1. Download 2.11.0 into a scratch folder: `https://github.com/mobile-dev-inc/maestro/releases/download/cli-2.11.0/maestro.zip` (about 315 MB); its SHA-256 must be `5384593cb4e7a106489e75a821d157dd43f4e438df6bc308b72e82c685e1283a`. Unzip (top folder `maestro/`), put `<that>/maestro/bin` first on PATH for the commands below only, check `maestro --version` prints 2.11.0, and run `python3 tools/maestro-compat.py <that>/maestro` (expect 28 passed).
2. `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` (about 17 minutes; 36 assertions on 2.0.10), then `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only android` (29 on 2.0.10). Keep the logs.
3. Watch for the risks in `research/maestro-2-11.md`: flows failing loudly on `launchApp`/`clearState` (2.7.0 stopped swallowing those errors); the line `Selected device ... using port` missing from `maestro.log` (then `check` falls back to OCR for iOS text); sharded parallel iOS runs behaving differently (2.6.0 changed them); run time per flow against 2.0.10.
4. On the Android run also test `[inputs.<locale>]`: 2.11.0 defines `MAESTRO_DEVICE_UDID` (2.0.10 does not). A flow with `inputText: ${name}` and different `[inputs.de]` and `[inputs.ja]` values on two emulators; the German screenshot must show the German value. Confirm what value Maestro puts in the variable (shotfleet expects the adb serial such as `emulator-5554`).

## Passed when

All fixture assertions pass on 2.11.0 on both platforms (and the CrossfitTracker numbers in `README.md` are not worse by more than 20 percent in time).

## Record

If everything passes, ONE commit promotes 2.11.0 exactly as `docs/handoff.md` item 1 lists: `MAESTRO_TESTED = ("2.0.10", "2.11.0")`; `MAESTRO_PIN` to version 2.11.0, size 314886578, the URL above and the SHA-256 above; the wording `tested with 2.0.10` in `README.md`, `site/public/docs.html`, `skill/shotfleet/SKILL.md`, `skill/shotfleet/references/troubleshooting.md`; `tests/claims.json` rows quoting it; `tests/test_agent_skills.py` (the quoted README string); `tests/test_doctor_versions.py` (the assertion, and the cases using 2.11.0 as "a newer version": use 2.99.0). Only if step 4 also passed, drop the "Maestro 2.0.10 doesn't define it" wording (`README.md` Inputs, `site/public/docs.html`, `skill/shotfleet/references/config.md`, the note printed by `shotfleet.py`, the caveat in `tests/test_limits_c2_c3.py`). If anything fails: change no code; record under a dated heading in `research/maestro-2-11.md`.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
