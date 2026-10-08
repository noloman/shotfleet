# Obytes starter run record, 2026-10-08

shotfleet 0.1.6 on obytes/react-native-template-obytes v9.0.0 (MIT), a Release simulator build compiled by hand: iPhone only (4 runs, 3 of them successful, 12 + 12 + 6 screenshots). The Android Release build never got past its splash screen on the emulator, so there are no Android frames. Start with NOTES.md.

- NOTES.md: what ran, numbers from run.json, check results, the one flow fix, frames reviewed, the Android blocker with its evidence level, "Findings for shotfleet", open items, the attribution block.
- flow.yaml (final iPhone flow), flow.used-by-run1.yaml (same file), flow.attempt1-failed.yaml (the one that failed at the Theme sheet), flow.draft.yaml, flow.extras.draft.yaml (never run), shotfleet.toml, shotfleet.draft.toml: iPhone flows and config. flow.android.yaml, shotfleet.android.toml: the Android ones (the flow never got past its first assertion).
- ios-dry, ios-run1, ios-run2: run.json, check.json (written by `shotfleet check --report`), check-in-run.json (the check.json shotfleet writes inside the run folder), maestro1.log.
- ios-dry-failed-1: the first dry attempt (2 of 6 frames, retried once): run.json, Maestro logs, junit.
- android-dry-failed: run.json, Maestro logs and junit of the Android dry run (0 of 6 frames, retried once).
- logs/: console logs of every run and check, simulator / AVD / adb lists before and after, my hand-booted emulator logs, chain output. logs/dbg-android: my three small diagnostic flows and the view tree dump behind the splash.
- scripts/: the chain scripts that held the device lock and started the runs.
- ARTIFACTS.txt (what was built, checksums), CLONE.txt (which commit), progress.log (timeline).
- No frames (PNG), no .app, no .apk, no template .env.
