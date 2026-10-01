# shotfleet: from working prototype to a few $k/year

Goal: find out cheaply whether developers will pay ~$49 for shotfleet, and be ready to sell if they will.
Success = a few thousand dollars a year. Anything less means it stays a free tool for our own apps.

## Phase 1: make it work for someone who isn't us (Claude)
1. [x] Reliability: dismiss late dialogs (the disclaimer that broke Hindi) with a wait-until loop, on iOS and Android.
2. [x] `shotfleet doctor`: checks Maestro, Xcode/simctl, adb/emulator, aapt2 and swiftc, and says how to fix what's missing.
3. [x] `shotfleet init <app.app|app.apk>`: writes a starter config (bundle id/package, shipped locales) and a starter flow.
4. [x] `shotfleet export --fastlane <dir>`: copies screenshots into the folders fastlane `deliver`/`supply` upload from,
       mapping each locale to its App Store / Google Play code.
5. [x] README: a 10-minute quickstart, how selectors get translated, what the checks catch, limits.
6. [ ] (paused for macOS update) Verify end to end on CrossfitTracker: iOS 18/18, Android 18/18, export to a scratch folder.

## Phase 2: validation assets (Claude drafts, Manu publishes)
7. [x] Landing page draft (private preview): the problem, the CrossfitTracker demo grid, the bug it found,
       $49 one-time pricing, a waitlist / pre-order button.
8. [x] Launch post drafts for r/iOSProgramming, r/androiddev, Indie Hackers, the Maestro community and X.

## Phase 3: decide (Manu, about 2 weeks)
9. [ ] Manu: host the page, connect a waitlist/pre-order (e.g. Lemon Squeezy), post the drafts.
10. [ ] Go if 30+ signups or 5+ pre-orders; otherwise keep shotfleet as an internal tool.

## Phase 4: only if Go
11. [ ] License key check, Homebrew tap, release builds, support email, CI mode.

## Status (paused 2026-10-01 for a macOS update)
- Done: steps 1-5, landing page draft (`site/index.html`, not published yet), launch post drafts (`marketing/launch-posts.md`).
- Step 6 interrupted: with other sessions building, Maestro's automatic `simctl diagnose` on failed flows
  wedged CoreSimulator. Added a watchdog that kills those dumps and a memory-pressure guard; not yet verified.
- Resume: run `.explore/verify.sh` on a quiet Mac, regenerate `site/img/` thumbnails, publish the page preview.
