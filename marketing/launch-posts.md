# Launch post drafts

Post these yourself, after the landing page is live and the signup form is connected.
Replace LINK with the page URL. Check each community's self-promotion rules first;
r/iOSProgramming and r/androiddev only allow promotion in certain threads or days.

Lead with the story (the bug it found), not the product.

---

## r/iOSProgramming and r/androiddev

**Title:** My app's onboarding was broken in 4 languages and I only found out by automating store screenshots

I ship a workout app in 18 languages. My "localized" App Store screenshots were the English set copied into every language folder, because my Maestro screenshot flow taps English buttons and couldn't run in German or Japanese.

So I wrote a tool that rewrites the flow's English taps into each language using the strings compiled into the app ("Next" becomes Weiter, 次へ, İleri…), runs every language in parallel on simulators and emulators, and then reads each screenshot back to check it really shows that language.

On the first full Android run, Japanese, Korean, Chinese and Arabic all got stuck on the same onboarding page. Their text renders taller, the page didn't scroll, and the Next button was off the bottom of a common small phone. English fit, so nobody had noticed. It was a two-line fix.

Other things it caught:
- In Turkish, "Next" and "Advanced" are the same word (İleri), so a tap hit the wrong button.
- A "Continue" step meant for a popup that never appeared matched a different element in German.

Full run: 18 languages × 4 screens, both platforms, about 15 minutes per platform on an M1 Pro, exported straight into fastlane's folders.

I'm thinking of releasing it (one-time license). Would this be useful to you? How do you handle localized screenshots today? LINK

---

## Indie Hackers

**Title:** Validating a $49 dev tool before building the rest: localized store screenshots

I'm an indie mobile developer with a few apps on both stores. Localized screenshots were a chore I kept skipping. I'd copy English screenshots into every language, which wastes most of the conversion gain of localizing.

I built a CLI for my own apps. It takes one English UI flow, auto-translates it for every language the app ships, captures them all in parallel, and checks each image. It already found a real bug: users in 4 languages couldn't finish onboarding on small phones.

Before polishing it for sale, I'm testing demand with a landing page and an early-access list: LINK.

What I know about the market so far:
- fastlane (free) already captures screenshots, but it needs UI-test setup and runs one language at a time.
- Design tools (AppScreens etc.) charge $100–600/yr but don't capture from the app.
- No tool checks that the screenshots are actually right.

My bar is modest: a few thousand dollars a year. Does a $49 one-time license sound right for this?

---

## Maestro community (Slack / Discord)

Hi all. I built a small tool on top of Maestro that I'd love feedback on.

It takes one English flow and runs it in every language your app ships. It rewrites text selectors using the strings compiled into the .app/APK (so `tapOn: "Next"` becomes `(Nächste|Weiter)` for German), and shards the languages across simulators and emulators. On Android it sets the per-app locale for each emulator and maps flows to devices from Maestro's own shard log.

It's for store screenshots, but it doubles as a localization smoke test. It found an onboarding page whose Next button was unreachable in ja/ko/zh/ar.

Two Maestro things I ran into along the way, in case they're useful:
1. On Android, two separate `maestro test` processes on different devices share host port 7001 and can silently drive each other's device. Use one sharded run instead.
2. Sharded runs don't expose a shard index to flows, so I map flows to devices from the debug log.

Landing page with examples: LINK

---

## X / Bluesky (thread)

1/ My app's onboarding was broken for every Japanese, Korean, Chinese and Arabic user on small phones, and I only found out by automating my App Store screenshots. 🧵

2/ My screenshot flow tapped English buttons, so "localized" screenshots were English copies. I made a tool that translates the flow using the app's own strings: Next → Weiter, 次へ, İleri…

3/ It runs all 18 languages in parallel on simulators and emulators, then reads every screenshot back to check it actually shows that language and isn't a copy.

4/ First Android run: 4 languages stuck on the same page. Taller text, no scrolling, Next off-screen. English fit. A two-line fix.

5/ Bonus: in Turkish, "Next" and "Advanced" are the same word. It warns about clashes like that before running.

6/ I'm considering releasing it. Early access: LINK
