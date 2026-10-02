# Launch posts (refreshed)

**Before posting:** Check each community's self-promotion rules. r/iOSProgramming and r/androiddev restrict promotional posts to certain threads or days. Lead with the real story, not the product.

---

## r/iOSProgramming + r/androiddev (one post, alternating platforms)

**Title:** My app's onboarding was broken in 4 languages on small phones, and I only found out by automating store screenshots

I ship a workout app in 18 languages. My Maestro screenshot flow taps English buttons, so my first "localized" screenshots were just the English set copied into every language folder, because the flow couldn't run in German or Japanese.

I built a tool that rewrites the flow's English taps into each language using the strings compiled into the app (so "Next" becomes "Weiter", "次へ", "İleri"…), runs every language in parallel on simulators and emulators, and reads each screenshot back to check it actually shows that language.

On the first full Android run, Japanese, Korean, Chinese and Arabic all got stuck on the same onboarding page. Their text renders taller, the page didn't scroll, and the Next button was off the bottom of a common small phone. English fit, so nobody had noticed. A small fix in my app.

Other things it caught:
- In Turkish, "Next" and "Advanced" are the same word (İleri), so a tap would hit the wrong button.
- A "Continue" button meant for a popup that never appeared matched a different element in German.

Full run: 18 languages × 4 screens, about 9 minutes on iOS and 15 on Android, exported straight into fastlane's folders. Both platforms from one flow.

I'm thinking of releasing it. Would this be useful to you? How do you handle localized screenshots today?

**Link:** https://shotfleet.manulorenzop.workers.dev

---

## Indie Hackers

**Title:** Validating before building more: localized store screenshots for $49 once

I'm an indie developer. Localized screenshots were something I kept skipping. My "localized" listings just had the English set copied into each language.

I built a CLI for my own apps. It takes one English UI flow, rewrites it for every language the app ships (using the app's own translations), captures them all in parallel, and checks each image. It found a real bug: on small phones, users in 4 languages couldn't get through onboarding.

Before polishing it for sale, I'm testing demand with a landing page and an early-access list at https://shotfleet.manulorenzop.workers.dev.

What I know about the market:
- fastlane (free) already captures screenshots, but it needs UI-test setup in your project and runs your languages one after another.
- Design tools like AppScreens cost $99–180/yr but don't capture from the app itself.
- I couldn't find any tool that verifies the screenshots are actually in the right language.

My pricing: $49 one-time ($29 for the first 100 buyers). Free tier: capture 2 languages and check any screenshots.

Does this sound useful? Particularly interested in hearing from anyone shipping 10+ languages.

---

## Maestro Slack/Discord community

Hi all. I built a small tool on top of Maestro that I'd love feedback on.

It takes one English flow and runs it in every language your app ships. It rewrites text selectors using the strings compiled into the .app/APK (so `tapOn: "Next"` becomes `(Nächste|Weiter)` for German), and shards the languages across simulators and emulators in parallel.

It's designed for store screenshots, but it doubles as a localization smoke test. On my own app it found an onboarding page where the Next button was unreachable in Japanese, Korean, Chinese and Arabic on small phones.

Two Maestro things I ran into:
1. On Android, two separate `maestro test` processes on different devices share host port 7001 and can silently drive each other's device. Use one sharded run instead.
2. Sharded runs don't expose a shard index to flows, so I map flows to devices from the debug log.

Landing page: https://shotfleet.manulorenzop.workers.dev

---

## X (3 separate posts, can be a thread)

### Post 1
On small phones, my app's onboarding was broken for Japanese, Korean, Chinese and Arabic users, and I only found out by automating my App Store screenshots.

My screenshot flow tapped English buttons, so "localized" screenshots were just copies. I made a tool that translates the flow using the app's own strings: Next → Weiter, 次へ, İleri…

### Post 2
It runs all 18 languages in parallel on simulators and emulators, then reads every screenshot back to check it actually shows that language and isn't a copy.

First Android run: 4 languages stuck on the same page. Taller text, no scrolling, Next off-screen. English fit. A small fix in my app.

### Post 3
Bonus: in Turkish, "Next" and "Advanced" are the same word. The tool warns about clashes like that before running. Considering releasing it as a one-time tool. Early access at https://shotfleet.manulorenzop.workers.dev

---

## Show HN

**Title:** Show HN: One English Maestro flow, every language your app ships, checked

Landing page: https://shotfleet.manulorenzop.workers.dev

**First comment (post yourself):**

Hi all. I ship a workout app in 18 languages. My Maestro screenshot flow taps English buttons, so I couldn't run it in other languages without per-language copies. I built shotfleet to fix that. It rewrites the flow's English text into each language using the app's own compiled strings, runs every language in parallel on simulators and emulators, and verifies each screenshot.

On the first full Android run, the onboarding page was unreachable in Japanese, Korean, Chinese and Arabic on small phones (taller text, no scrolling, button off the bottom). English fit, so the bug wasn't obvious. It was a small fix in my app.

**What it does:** One English flow → every language the app ships → both platforms at once → each image checked (wrong language, copies, missing, store size rules, iPad rule) → exported to fastlane's folders.

**How it works:** Reads the translations compiled into your .app/APK, rewrites selectors (`tapOn: "Next"` becomes the regex for all German translations of "Next"), shards languages across simulators and emulators.

**Proven on:** CrossfitTracker iOS/Android (18 languages, 9 min / 15 min), Kuokka Compose (iPhone + 13" iPad). Checked fastlane screenshots from any tool (fastlane snapshot/screengrab, etc).

**Not yet:** Flutter/React Native apps (via source files, untested on a real app).

**Friction:** macOS only. Needs Xcode, Android SDK, and a Maestro flow written.

**Pricing:** $49 one-time (a year of updates, keeps working afterwards). $29 for the first 100 buyers. Free tier: check any screenshots + capture 2 languages in `run`.

Would love feedback. How do you handle localized screenshots today?

---

## Notes for all posts

- The $29 founder price is for the first 100 buyers, whoever buys first (not a list perk); mention it once, not repeatedly.
- Lead with the real bug story, not the product features.
- Avoid hype: say "one real bug found" not "catches all localization bugs."
- Be specific about times and numbers (18 languages, 9 min / 15 min, 4 simulators, small phones).
- For r/iOSProgramming and r/androiddev: link the same landing page in both posts, add `?utm_source=reddit` to track which subreddit drives signups.
- Add `?utm_source=` tags to links in each post (reddit, ih, x, hn, maestro, etc.) so the landing page tracks which channel each signup came from.
- Do NOT claim: a real Flutter/React Native run, live permission-alert taps, frames, captions, upload to stores. iPad and Android tablet sets are real (verified 2026-10-02: Remoti on an iPad 13", CrossfitTracker on an Android tablet), so they can be claimed.
