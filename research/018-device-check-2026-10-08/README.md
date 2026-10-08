# 0.1.8 candidate device check, 2026-10-08

shotfleet from source, branch claude/018-candidate at 00d7346 (VERSION still says 0.1.7), macOS 27.0.1, iOS runtimes 18.0, 18.6, 26.4, 27.0, `runtime` pinned to iOS 26.4 in the config. Maestro 2.0.10. Fixture app (tools/fixture-app, tools/fixture-app-android; the Android one rebuilt with an extra `values-zh-rCN` so it ships zh-CN). Device lock held 12:37-12:50 after the start rule (3 checks 60 s apart: load 7-8, free memory 44 %, pressure 2, swapouts +0, no foreign xcodebuild test). The Mac got busy during the run (load 190-400 from an ANECompilerService text-model compile; swap 90-97 % full, so the busy-Mac warning fired).

The first start of the run steps (12:37) failed in 15 s per step: my configs had `locales` and `parallel` at the top of shotfleet.toml, which is not allowed (they go inside `[ios]` / `[android]`). Configs fixed, steps rerun under the same lock (progress.log shows both). The Maestro 2.11.0 step (40-*.log) did not run: my script's `env PATH=...` was not quoted. Not repeated, because another session has the same A/B queued.

| Item | Result | Where |
|---|---|---|
| A1 string-form `scrollUntilVisible` in a non-English run | PASS. `element: "Next"` became `'Weiter'`, `'下一步'` in the translated flows; de and ja passed on iPhone (2/2 screenshots each), zh-CN and de on Android | flows/, 10-*, 30-* |
| A2 `waitForAnimationToEnd` before each screenshot | PASS on iOS and Android with Maestro 2.0.10: every flow has the 1000 ms step before `takeScreenshot`, all flows passed. Extra time: iPhone de/ja warm flow 11 s with and without it; gap between the two screenshots 4-5 s with, 3-4 s without (one second at most, noisy under load) | flows/, results/ios-a, ios-b |
| A3 `zh-Hans` on an Android build that ships zh-CN | PASS. "note: zh-Hans is zh-CN in this app, so shotfleet uses zh-CN", zh-CN 2/2 screenshots (the stock fixture APK has no zh; this APK was rebuilt with zh-CN) | 30-* |
| B6 `check --app` on the wger Flutter builds | PASS after one fix on the candidate (commit 00d7346): Runner.app and the APK, without `--strings`: exit 2 "This is a Flutter build: pass --strings 'lib/l10n/*.arb'"; with `--strings`: 12 and 18 screenshots checked, 0 problems. Before the fix the APK without `--strings` exited 1 with 3 false "no translation" problems and 0 screenshots checked | b6-wger/ |
| B7 iPhone + iPad parent folder | PASS. With the iPad set: exit 0, iPad column ok (2). Without it (iPad folder removed from a copy): iPad column `missing`, 2 problem lines, exit 1. A one-device `out/` folder: same, 2 problems, exit 1 | b7 logs, 10-* |
| B8 `[expect]` with `key` | PASS. Correct screen: exit 0, 4 screens checked. Wrong screen (key "Settings" on the welcome screenshot): exit 1, `expected "Einstellungen" on screen` (de) and `"設定"` (ja) | b8 logs |
| C9 `doctor` names the runtime | PASS. Without a runtime in the config: "ok iOS Simulator runtime iOS 26.4" plus the note why 27.0 is skipped. With the pin: "sets runtime = ..., so `run` uses iOS 26.4" | 03-doctor, c9 |
| C10 Android note on Maestro 2.0.10 | PASS. The note appears at the start of the run and again before the check result, with the Maestro 2.11.0 suggestion | 30-* |

Other things seen:
- iPhone + iPad run (10-*): rc 0, de/ja 2/2 on both, 4 screenshots checked per device, 0 problems. The iPad pool simulator "stopped answering last run" and was replaced ("same name, new id"), the new message of item 8.
- iPhone-only run (20-*) exits 1 because the app runs on iPad and the run has no iPad set (the existing rule, not a failure of the run).
- Android zh-CN + de (30-*): rc 0, 2/2 each, 57 s capture, check 0 problems; only the Google Play 9:16 note.
- Simulators: the iPad simulator that shotfleet replaced during my hold was deleted by my cleanup; nothing of mine is booted (logs/sims.final.txt, adb.final.txt). Sim 18DBDD79 (Manu's iPhone 15 Pro) was not touched.
