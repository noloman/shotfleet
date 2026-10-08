# Obytes starter run record, 2026-10-08

shotfleet 0.1.6 on obytes/react-native-template-obytes (MIT), Release builds compiled by hand. The final build is the unmodified upstream commit fd9b358 ("v9.0.0 plus ten later commits", includes the upstream splash fix, PR #531): iPhone and Android, 3 runs each, all successful (12 + 12 + 6 screenshots per platform). A first try on the tag v9.0.0 worked on iPhone (same frames) and did not get past the splash screen on Android. Start with NOTES.md.

- NOTES.md: the story of the final build: what ran, numbers from run.json, check results and evidence kinds, frames reviewed on both platforms, the tag attempt as history (with the Android blocker and its evidence level), findings for shotfleet, open items, the attribution block.
- NOTES-tag-v9.0.0.md: the first notes, from the tag build (iPhone details, the one flow fix, the Android blocker).
- fd9b358/: the final build. ios-hd-{dry,run1,run2} and android-hd-{dry,run1,run2} each hold run.json, check.json (`shotfleet check --report`), check-in-run.json (the check shotfleet writes inside the run), index.html, Maestro logs and junit. android-hd-run1/check-app-apk.json is the `check --app` try on the React Native APK. flows/ has the flows and configs used, scripts/ the chain scripts that held the device lock, logs/ the console logs, simulator / AVD / adb lists, build logs (not the 12 MB Xcode log), the 20-file diff to the tag (diff-name-status.txt, diff-stat.txt). ARTIFACTS-fd9b358.txt: what was built, checksums.
- flow.yaml, flow.used-by-run1.yaml, flow.attempt1-failed.yaml, flow.draft.yaml, flow.extras.draft.yaml (never run), shotfleet.toml, shotfleet.draft.toml: iPhone flows and config of the tag job. flow.android.yaml, shotfleet.android.toml: the Android ones of the tag attempt (the flow never got past its first assertion).
- ios-dry, ios-run1, ios-run2, ios-dry-failed-1: the tag-build iPhone runs. android-dry-failed: the tag-build Android dry run (0 of 6 frames, retried once).
- logs/, scripts/: logs and chain scripts of the tag job. logs/dbg-android: my three small diagnostic flows and the view tree dump behind the splash.
- ARTIFACTS.txt (tag build, checksums), CLONE.txt (which commit was cloned), progress.log (timeline of everything, both builds).
- No frames (PNG), no .app, no .apk, no template .env.
