# shotfleet: from working prototype to a few $k/year

Goal: find out cheaply whether developers will pay $79 ($49 founder price) for shotfleet, and be ready to sell if they will.
Success = a few thousand dollars a year. Anything less means it stays a free tool for our own apps.

## Phase 1: make it work for someone who isn't us (Claude)
1. [x] Reliability: dismiss late dialogs (the disclaimer that broke Hindi) with a wait-until loop, on iOS and Android.
2. [x] `shotfleet doctor`: checks Maestro, Xcode/simctl, adb/emulator, aapt2 and swiftc, and says how to fix what's missing.
3. [x] `shotfleet init <app.app|app.apk>`: writes a starter config (bundle id/package, shipped locales) and a starter flow.
4. [x] `shotfleet export --fastlane <dir>`: copies screenshots into the folders fastlane `deliver`/`supply` upload from,
       mapping each locale to its App Store / Google Play code.
5. [x] README: a 10-minute quickstart, how selectors get translated, what the checks catch, limits.
6. [x] Verify end to end on CrossfitTracker: iOS 18/18, Android 18/18, export to a scratch folder.

## Phase 1b: product quality bar (before anything is sold)
- [x] Test suite: 37 tests, standard library only (`python3 -m unittest discover -s tests`), mutation-checked.
- [x] Every expected mistake gives a one-line cause and fix, no tracebacks (config, paths, bundle id, tools, locales).
- [x] Code review: 10 findings fixed (stale results could mislabel languages; cleanup killed other projects' Maestro drivers; ...).
- [~] Proven on apps other than CrossfitTracker: Remoti iOS strings (String Catalogs) load correctly; full runs pending
      (need the Mac free of the emulator benchmark).
- [ ] Docs match behavior exactly; `--help` per command.

## Phase 2: validation assets (Claude drafts, Manu publishes)
7. [x] Landing page draft (private preview): the problem, the CrossfitTracker demo grid, the bug it found,
       $49 one-time pricing, a waitlist / pre-order button.
8. [x] Launch post drafts for r/iOSProgramming, r/androiddev, Indie Hackers, the Maestro community and X.

## Strategy
See STRATEGY.md: positioning against fastlane, StoreScreens/asc, Maestro and design tools; product moves; 6-week launch plan.
The decision rule there (50 founder sales in 60 days) supersedes the signup count below once the sale opens.

## Phase 3: decide (Manu, about 2 weeks)
9. [~] Live at https://shotfleet.manulorenzop.workers.dev (Cloudflare Worker + KV waitlist; `site/signups.sh` lists signups).
       Posting the drafts needs Manu's OK per post.
10. [ ] Go if 30+ signups or 5+ pre-orders; otherwise keep shotfleet as an internal tool.

## Phase 4: only if Go
11. [ ] License key check, Homebrew tap, release builds, support email, CI mode.

## Status (2026-10-01)
- Phases 1-2 done. Verified on CrossfitTracker: iOS 18/18 in 8m54s, Android 18/18 in 15m24s, all on the
  first attempt, 0 check problems; both exported into fastlane deliver/supply folders.
- Landing page draft: https://claude.ai/artifact/XzrP9PFaTXr8Lc8EcXu4aJ (private). Source in `site/`.
- Next is Phase 3, Manu's: host the page, connect signups, post `marketing/launch-posts.md`.
