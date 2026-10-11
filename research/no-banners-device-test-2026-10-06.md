# No-banners device test (0.1.5 fix), 2026-10-06

The fix being tested is on main (876be29, 6030d8e). iOS: right after boot, `simctl spawn <udid> defaults write com.apple.generativeexperiences.corefollowup DateOfLastAppleIntelligenceReadinessCFU -date <now UTC>`. Android: `settings put global heads_up_notifications_enabled 0` added to DEMO_MODE.

Device lock: held 13:32 to 13:54 (22 min, hard limit 35). Quiet check at 13:32: free memory 65 %, load 218. Load reached about 800 to 860 during the test (other projects' Gradle and xcodebuild). Screenshots and DB copies are in `shotfleet-rc-build/banner-test/`.

## Result: both inconclusive. Neither control showed a banner.

### iOS: inconclusive
- I created two fresh "iPhone 17 Pro Max" simulators on iOS 26.4 (23E254a), sf-banner-on and sf-banner-off, and booted both. Both had finished booting at 13:33:38.
- On sf-banner-on I ran shotfleet's exact `defaults write` at 13:33:38. Reading it back gave `DateOfLastAppleIntelligenceReadinessCFU = "2026-10-06 11:33:38 +0000"`. On sf-banner-off the domain did not exist.
- 8 minutes later (13:41:40) `simctl io screenshot` of sf-banner-on hung for more than 6 min under load 800. I killed my own call. A second try at 13:49 with a 60 s limit also got no picture. So there is no screenshot of sf-banner-on.
- The sf-banner-off screenshot finally landed at 13:48, about 15 min after boot (`ios-banner-off-8min.png`). It shows no banner, and the home screen was still half drawn (blank app icons).
- CoreFollowUp `items.db`, read on copies taken at 13:48: 0 rows in `items` and 0 in `notifications` on both simulators. Neither file had been written since 13:32.
- The control (sf-banner-off) never got the "Ready for Apple Intelligence" item, so this run proves nothing about the fix. The heavy load probably slowed the simulators past the roughly 5.5 min mark where the banner showed before. To do: run again on a quiet Mac (load under 100) and wait longer (15 min) for the control.

### Android: inconclusive
- I booted shotfleet_android (API 36 / Android 16) with `-read-only -no-snapshot-save` on port 5790, so the AVD stays unchanged.
- First pass was invalid. adb in a `while read` loop swallowed stdin, so only the first DEMO_MODE line ran. I re-ran all 12 lines with `</dev/null` and read back `heads_up_notifications_enabled` = 0.
- Shot 1 (heads-up off): `cmd notification post -S bigtext -t T sftest body`. No banner (`android-1-headsup-off.png`).
- Control (heads-up on, set back to 1): posted again. No banner (`android-2-headsup-on-control.png`). Reason: `cmd notification post` uses the shell's `shell_cmd` channel, which has mImportance=3 (DEFAULT). Android shows a heads-up banner only for importance 4 (HIGH), so this command can never make one. This control can't work on any device.
- Other controls I tried, all with heads-up on:
  - An SMS via `adb emu sms send`. It was stored, but Messages posted no notification (`android-3`).
  - An incoming call via `adb emu gsm call`. Telecom reached RINGING, but there was no banner, both in demo mode (`android-4`) and after leaving demo mode (`android-5`, only status-bar icons).
- Note: under this load each adb command took 10 to 20 s, so shots came 1 to 2 s after the post command returned, not after the post itself.
- To do: as the control, use an app that posts on an IMPORTANCE_HIGH channel (for example a tiny test APK, or the fixture app with a high-importance channel), on a quiet Mac.

## Cleanup
- Both simulators were shut down and deleted.
- The emulator was stopped (pid 15218, mine). No AVD was created.
- The user's "iPhone 15 Pro" was not touched.
