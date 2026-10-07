# 0.1.7 device check, 2026-10-07

From source at 97d897e (shotfleet.py still says VERSION 0.1.6 there), macOS 27.0.1, Xcode with simulator runtimes iOS 18.0, 18.6, 26.4 and 27.0, **no `runtime` in the config**, fixture app (tools/fixture-app), languages de and ja, under the device lock after a start check (load < 100, free memory >= 40 %, pressure <= 2, no swapping, 3 checks 60 s apart). Swap was ~92 % full the whole time, so the busy-Mac warning fired, as designed.

Part 1 (`part1-iphone/`, 17:50-17:55): iPhone only.
- `run` picked iOS 26.4 and said so: "using iOS 26.4: iOS 27.0 is installed, but its simulators freeze at boot ..." (04-run-A.log).
- `doctor` (03-doctor.log): exit 0, but the runtime line reads "ok iOS Simulator runtime iOS 27.0", the last runtime simctl lists, although `run` would use 26.4. Wording only; the warning appears when 27.0 is the only runtime.
- Deliberate failure: the flow tapped the German "Weiter" in both languages. de passed, ja failed with the step and the on-screen texts, and `run` said "not retrying ja: the flow or the app failed, not the device" (04-run-A.log, run.json: ja attempts 1).
- Flow fixed, then `run --retry-failed`: only ja was captured ("retrying the languages that failed in the last run: ja", 46 s), de was kept, `run.json` lists both, ja `attempts` 2 (05-*).
- `check`: the coverage table and the `coverage` key in check.json (06-check.log, 07-check.json); `check --compare` against the copy taken before the retry: "ja/02_settings.png: new, 3 screenshot(s) unchanged" (07-check-compare.log).
- `export` refused, because the fixture app runs on iPad and this run had no iPad set. That is the existing rule, and part 2 covers it.
- Not covered by a flag: checking the parent folder of a multi-device run shows the iPad column as "-" (not "missing") and prints the separate sentence "the app runs on iPad, so the App Store requires 13" iPad screenshots"; `check` then exits 1 with "0 problem(s)". Same as before 0.1.7.

Part 2 (`part2-iphone-ipad/`, 18:02-18:12): iPhone 17 Pro Max and iPad Pro 13-inch (M5), de and ja.
- Both passed on iOS 26.4. The iPhone pass was an automatic infrastructure retry: "retrying 2: de, ja", then both ok (the Mac was busy). The iPad pass used 1 device because memory pressure was elevated ("memory pressure is elevated: using 1 devices instead of 2").
- `check` exit 0, one coverage table per device folder, iPad column `ok (2)` in the iPad folder.
- `export --fastlane ... --print-upload` exit 0 and printed `fastlane deliver --screenshots_path .../fastlane/screenshots --skip_metadata --skip_binary_upload --overwrite_screenshots --force` (08-export-print-upload.log). It uploaded nothing.
- No shotfleet simulator was left booted (09-booted-after.txt).
