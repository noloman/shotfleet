# Final launch text pack (shotfleet 0.1.0, live since 2026-10-05)

Owner: Manu posts, from his own accounts. Claude wrote the text and posted, sent and submitted nothing. Every sentence was checked against the repo on 2026-10-05 (main c4affd4); what changed from the old drafts is in FINAL-pack-changes.md. Where a fact is only "evidence" in tests/claims.json, the text says what was measured and where, not more.

The old kit files (show-hn.md, social.md, directories.md, maestro-community.md, launch-day.md and the rest) stay for the schedule and the rules. Paste from this file, not from them.

## Before you paste anything (10 minutes)

1. Open https://shotfleet.com: the price section must still say $29 for the first 100 buyers, then $49. The page has no counter. Gumroad shows how many times FOUNDER29 was used. If it passed 100, delete every "$29" sentence below and say the price is $49.
2. Run `maestro --version` and `shotfleet --version` on your Mac. The text says "tested with 2.0.10 and 2.11.0" (docs/compat.md). The 9 and 15 minute numbers were measured on 2.0.10. If you released 0.1.1, the install line gets it; none of the text below depends on 0.1.1.
3. Chinese is the only language of the unreachable-Next-button story with an image in the repo (`site/public/img/bug_zh.jpg`). The text says "several languages" and points at the Chinese one. The site says four (Japanese, Korean, Chinese, Arabic). If you can confirm all four from your app repo (commit 687ffccd), say four.
4. Do not link the guide pages (`/the-button-nobody-could-reach`, `/maestro-one-flow-every-language`, `/fastlane-snapshot-screenshots-all-english`). They are drafts in `site/draft/guides/` and return 404. This pack links only the home page and `/docs`, `/alternatives`, `/terms`, `/privacy`.
5. Read each place's current rules the same day (Show HN guidelines, r/macapps sidebar, Indie Hackers, the Maestro Slack). Our tools have not read Reddit's or Slack's.
6. Every link to our own site carries `?utm_source=<channel>`; the tags used below are `hn`, `indiehackers`, `mastodon`, `bluesky`, `x`, `macapps`, `maestro`, `waitlist` and one per directory.

---

## 1. Show HN

**Title** (recommended, 77 characters):

```
Show HN: shotfleet, store screenshots in every language from one Maestro flow
```

Alternative (73): `Show HN: One English Maestro flow, every language your app ships, checked`

**URL:** `https://shotfleet.com/?utm_source=hn`

Leave the text box empty. Do not ask anyone to vote or comment. Post the comment below yourself right after submitting.

**First comment**

> Hi HN, I'm Manu, a solo developer in the Netherlands. I make a workout app, WOD Tracker, that ships in many languages (18 in the run below). My Maestro screenshot flow tapped English buttons, so it could not run in German or Japanese without a copy of the flow per language, and my "localized" store screenshots ended up as the English set copied into every language folder.
>
> shotfleet is what I built for that. You write one English Maestro flow. It reads the translations compiled into your .app or APK, rewrites every text tap for each language ("Next" becomes "Weiter", "次へ", "İleri"), runs the languages in parallel on iOS simulators and Android emulators, and then compares each screenshot with your app's own strings: wrong language, copies, missing screens, App Store and Play size rules. `export` writes fastlane's folders; fastlane does the upload.
>
> One thing the first full Android run showed me: it got stuck on one onboarding page in several languages (the Chinese one is on the site). The text was taller, the page did not scroll, and Next was below the bottom of a small phone, so the flow could not tap it. English fit, so I had never seen it. The fix in my app was small: I made two pages scroll. To be exact, it was `run` that got stuck; `check` would not flag a missing button.
>
> Numbers, so you can judge them: in my first full run, 18 languages x 4 screens = 72 screenshots took 9 minutes on iOS and 15 minutes on Android, on one M1 Pro Mac, 4 simulators or emulators in parallel, Maestro 2.0.10, one app. Yours will differ.
>
> Limits, up front:
> - Apple silicon Mac only. The installer refuses Intel Macs.
> - Needs Maestro (tested with 2.0.10 and 2.11.0), Java 17+, Xcode for iOS (a Debug simulator build) and the Android SDK for Android (API 33+ emulators, for per-app languages).
> - You write the flow (`shotfleet init` writes a starter). No frames, no captions, no store upload.
> - Closed source.
> - Flutter and React Native work from your translation files instead of the built app. I ran one Flutter app (wger) and one Expo app (the obytes template) on iOS and Android, two languages and three screens each. A bare React Native app built but I did not get a real flow through it. Please treat this as early.
> - It reads text, it does not judge layout. For scripts that macOS text recognition cannot read, it does fewer checks unless Tesseract is installed.
>
> Price: `shotfleet check` is free (no account, no licence) and works on fastlane snapshot and screengrab folders and on a plain folder per language. `run` is free for 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49, once per developer, with a year of updates and a 14-day refund. Checkout is on Gumroad.
>
> Install: `curl -fsSL https://shotfleet.com/install.sh | sh` (it verifies a checksum; the script is short, read it first). Signed with my Developer ID and notarized. I would like to hear how you check localized screenshots today, and what would stop you from trying this.

**Short answers to the 8 most likely questions**

1. Closed source and `curl | sh`: why trust it?

> Fair. The script is short, so read it before you pipe it. It refuses anything that is not macOS on Apple silicon, downloads one tarball and its SHA-256, installs nothing if the sum does not match, and puts the program under `~/Library/Application Support/shotfleet` with a link on your PATH. The program is signed with my Developer ID and notarized: Apple's notary service accepted it, and the installer package on the site passes `spctl` as Notarized Developer ID. A copy installed by `curl` has no quarantine flag, so Gatekeeper is not consulted on that path. `shotfleet check` needs no key and no account, so you can try that part first. It is closed source, and I know that rules it out for some of you.

2. Why not fastlane snapshot, or Maestro's locale flag?

> If your UI tests already run in every language and you are happy with them, keep them: fastlane snapshot is open source and built for that, and `shotfleet check` works on its output. I wanted one plain-English Maestro flow for iOS and Android with no test code in the app, and a check of every image afterwards, because my recurring failure was a good-looking image in the wrong language. For Maestro itself: when I last read its docs, the documented way to set a locale was `--device-locale` on `maestro start-device`, which is per device. What shotfleet adds is rewriting the text taps for each language from your app's strings, a parallel run, a fresh state per language, and the check. It is built on Maestro. I am not affiliated with the Maestro project.

3. What leaves my machine?

> Your app and your screenshots are never uploaded; the program runs on your Mac. Going by the code and its tests, the only network calls are: a licence check with Gumroad when you activate and about weekly after (the key, the product ID and whether to count an activation; no Mac name), a version lookup on shotfleet.com when you run `doctor`, and local traffic to Maestro on 127.0.0.1. My tests run `check` and `export` with the network cut off. I have not done a packet capture, so if you care, run it behind Little Snitch and tell me what you see.

4. What do I need installed? Intel? CI?

> An Apple silicon Mac (no Intel build, and I have no date for one), Xcode for iOS, the Android SDK for Android with API 33+ emulators (per-app languages arrived in Android 13), Maestro and Java 17+, which Maestro needs. `shotfleet doctor` checks all of this and says how to fix what is missing. Maestro: tested with 2.0.10 and 2.11.0; other 2.x versions may work and `doctor` tells you when yours is another one. In CI you need a macOS runner. `run`, `check` and `export` take `--json`, and the exit codes are 0 all good, 1 problems found, 2 setup error. The GitHub Actions recipe for `check` in the README has not been run on GitHub yet; the command in it is the one I tested locally.

5. Flutter and React Native?

> They work from your translation files (ARB, i18next JSON, .po and others), because those frameworks do not keep readable strings in the build. On a Mac I ran one Flutter app (wger) and one Expo app (the obytes template), iOS and Android, two languages and three screens each, and a Compose Multiplatform app (JetBrains' KotlinConf app) in German and English. A bare React Native app (Rocket.Chat) built but I did not get a real flow through it. So: early, and I would like to hear what happens on yours.

6. Why paid, and what exactly do I get?

> Capturing alone is something fastlane and Maestro already do. What I charge for is the every-language run and the export, because that is where my own time went. Free: `check`, and `run` for 2 languages, so you can see real results on your own app first. A licence is $29 for the first 100 buyers, then $49, once per developer. It unlocks every language, both platforms, the iPad and Android tablet sets, and `export`. It includes a year of updates; after that your version keeps working as long as macOS, Xcode and Maestro let it. A key has 3 activations. Refund: 14 days, email hello@shotfleet.com and I refund it through Gumroad. Prices are before VAT where it applies; Gumroad is the merchant of record. I have no demand data at any price yet, so this launch is partly how I find out.

7. How does the check work, and what can it not do?

> During an iOS run it reads the text on screen through Maestro's driver while each screenshot is up. For screenshots from other tools, or on Android, it reads the image with the text recognition built into macOS (33 languages on my Mac, it depends on the macOS version) and compares what it finds with your app's own strings. It reports wrong-language screens, copies, missing screens and store size rules, and it says which screens it could not read. It does not judge layout. It does not translate text you type into fields unless you set `[inputs]`. It drives simulators and emulators. It does not catch every localization bug: the unreachable button above stopped the run, and `check` would not have flagged it. If your app keeps its own saved language choice that overrides the system one, I have not tested that case.

8. Is 9 and 15 minutes reproducible?

> No, treat it as a rough scale. It is one app, 18 languages x 4 screens, my first full run, on an M1 Pro with 32 GB, 4 in parallel, Maestro 2.0.10. I re-ran the same app later on 2.11.0 on a busy Mac with 19 languages; those times are not comparable, and 9 of the 19 iOS languages needed shotfleet's own retry because two of the four simulators were slow to start their driver. The numbers change with the Mac, its load, the app's start-up time and Maestro and Xcode updates.

**Source of each fact:** timings, app, hardware: tests/claims.json C005, C007, C105 and research/first-run.md; later 2.11.0 run: docs/compat.md and research/maestro-2-11.md; Maestro versions, Java, API 33, Apple silicon, Intel refusal: README.md Limits, docs/compat.md, site/public/install.sh; free tier and licence: README.md "Free and paid", site/public/terms.html, shotfleet.py `FREE_LANGUAGES`; notarization: research/go-live-gate.md G4, G5 and the post-launch section; installer behaviour: site/public/install.sh, G7; network calls: C004 and C085; check method: README.md "What it checks", C027; Flutter, Expo, Compose, Rocket.Chat: research/frameworks.md sections 15 and 16; fastlane snapshot "open source": C038; Maestro docs on locale: marketing/kit/maestro-community.md (docs read 2026-10-02); bug story: README.md, site/public/index.html, C012 to C014; CI recipe not run: README.md "In CI".

---

## 2. Indie Hackers story post

**Title:** I made a tool for my own localized store screenshots, and it is on sale now

**Link:** `https://shotfleet.com/?utm_source=indiehackers`

> I ship a workout app, WOD Tracker, in many languages, and my "localized" App Store and Google Play screenshots were the English set copied into each language folder. My UI script tapped English buttons ("Next", "Settings"), so it could not run in German or Japanese without a copy per language.
>
> So I built shotfleet for myself. It is a Mac command line tool. You write one Maestro flow in English. It reads the translations compiled into your app, rewrites each tap for every language, runs the languages in parallel on simulators and emulators, and then checks each screenshot against the app's own strings: wrong language, the same image twice, a missing screen, store size rules. Then it exports fastlane's folders. fastlane does the upload.
>
> On my first full run, 18 languages x 4 screens took 9 minutes on iOS and 15 on Android, on one M1 Pro Mac. That is one app on one Mac, so take it as a rough scale. The same Android run also got stuck on an onboarding page in several languages: the text was taller, the page did not scroll and Next was below the screen of a small phone. English fit, so I had never seen it. I made two pages scroll.
>
> What it is not: no frames, no captions, no store upload. Apple silicon Macs only. It needs Maestro, Java 17+, Xcode for iOS and the Android SDK for Android. Flutter and React Native work from translation files, but I have run only one Flutter app and one Expo app, in two languages each, so that part is early.
>
> The business side: `shotfleet check` is free, and `run` is free for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49, once per developer, with a year of updates and a 14-day refund. It went on sale on 5 October 2026, so I have no sales numbers to share and no demand data yet. I built it for myself first and I am finding out whether other people need it.
>
> I would like to hear from anyone who ships 10 or more languages: how do you make and check your store screenshots today?

**Source of each fact:** README.md ("Why", "What it checks", "Free and paid", "Limits"), site/public/index.html, tests/claims.json C005, C007, C012 to C014, C035; research/go-live-gate.md (sale live 2026-10-05); research/frameworks.md sections 15 and 16.

---

## 3. Launch thread: Mastodon, Bluesky, X (6 posts each)

Post as a thread from each account, from your own accounts, in the order shown. The sale is live. If the Show HN is up the same day, post the Show HN first and answer its comments before the threads. State the price once, in post 6. Add alt text to every image that describes it, not the post. Asset hints: post 1 the review grid or a terminal capture of the real `run` summary, post 2 `site/public/img/bug_zh.jpg` (alt text: "Chinese onboarding page on a small Android phone with four goal cards and a Skip link, but no Next button"), post 3 a ribbon image from the real `train_*` screenshots, post 6 none.

Never post a screenshot with a red outline unless the problem in it was planted, and say so.

### Mastodon (iosdev.space), limit 500

1.
> shotfleet is out: one English Maestro flow, run in every language your app ships, on iOS and Android, with every screenshot checked. It is a Mac command line tool I made for my own app. A thread on what it does and what it does not do. https://shotfleet.com/?utm_source=mastodon #iOSDev #indiedev

2.
> Why I made it: my screenshot flow tapped English buttons, so my "localized" screenshots were the English set copied into every language folder. Then my first full Android run got stuck on one onboarding page. In several languages the text was taller, and Next was below the bottom of a small phone. English fit, so I had never seen it.

3.
> How it works: it reads the translations compiled into your build and rewrites each tap, so "Next" becomes Weiter, 次へ or İleri. It runs the languages in parallel on simulators and emulators and compares each image with the app's own strings. 18 languages x 4 screens took 9 minutes on iOS and 15 on Android in my first run, on one Mac.

4.
> It warns before a run when two labels clash in one language (in Turkish strings I tested, "Next" and "Advanced" were both İleri). After a run it reports wrong-language images, copies, missing screens and store size rules. It does not make frames or captions and does not upload; fastlane uploads. #Maestro

5.
> Limits: Apple silicon Mac only. Needs Maestro (tested with 2.0.10 and 2.11.0), Java 17+, Xcode for iOS, the Android SDK with API 33+ emulators. Flutter and React Native work from translation files; I have run one Flutter app and one Expo app, two languages each, so that part is early.

6.
> Free: `shotfleet check` on fastlane screenshots or a folder per language, and `run` for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49 once per developer, 14-day refund. Install and details: https://shotfleet.com/?utm_source=mastodon

### Bluesky, limit 300

1.
> shotfleet is out. One English Maestro flow, every language your app ships, iOS and Android, and every screenshot checked. I made this Mac command line tool for my own app. A short thread on what it does and does not do. https://shotfleet.com/?utm_source=bluesky

2.
> Why: my screenshot flow tapped English buttons, so my "localized" screenshots were the English set copied into every folder. Then my first full Android run got stuck on one onboarding page: in several languages the text was taller and Next sat below the bottom of a small phone.

3.
> It reads the translations compiled into your build and rewrites each tap: "Next" becomes Weiter, 次へ or İleri. Languages run in parallel on simulators and emulators, then each image is compared with the app's strings. First run: 18 languages x 4 screens, 9 min on iOS, 15 on Android.

4.
> Before a run it warns when two labels clash in a language (in Turkish strings I tested, "Next" and "Advanced" were both İleri). After a run it reports wrong-language images, copies, missing screens and store size rules. No frames, no captions, no upload.

5.
> Limits: Apple silicon Mac only. Needs Maestro (tested with 2.0.10 and 2.11.0), Java 17+, Xcode for iOS and the Android SDK with API 33+ emulators. Flutter and React Native work from translation files; I ran one Flutter app and one Expo app, so that is early.

6.
> Free: `shotfleet check` on fastlane screenshots or a folder per language, and `run` for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49 once per developer, 14-day refund. https://shotfleet.com/?utm_source=bluesky

### X, limit 280

1.
> shotfleet is out: one English Maestro flow, every language your app ships, iOS and Android, every screenshot checked. A Mac command line tool I made for my own app. Thread on what it does and does not do. https://shotfleet.com/?utm_source=x

2.
> Why: my screenshot flow tapped English buttons, so "localized" screenshots were the English set copied into each folder. My first full Android run then got stuck on an onboarding page: in several languages Next was below the screen of a small phone.

3.
> It reads the translations compiled into your build and rewrites each tap: Next becomes Weiter, 次へ or İleri. Languages run in parallel on simulators and emulators, then each image is compared with the app's strings. First run: 18 languages x 4 screens, 9 min iOS, 15 Android.

4.
> It warns before a run if two labels clash in one language (Turkish "Next" and "Advanced", in strings I tested). It reports wrong-language images, copies, missing screens, store size rules. No frames, captions or upload.

5.
> Limits: Apple silicon Mac only. Needs Maestro (tested with 2.0.10 and 2.11.0), Java 17+, Xcode for iOS, Android SDK with API 33+ emulators. Flutter and React Native work from translation files; I ran one Flutter and one Expo app, so early.

6.
> Free: shotfleet check on fastlane screenshots or a folder per language, and run for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49 once per developer, 14-day refund. https://shotfleet.com/?utm_source=x

**Source of each fact:** README.md ("Why", "How it works", "What it checks", "Free and paid", "Limits"); site/public/index.html (flow row with the Turkish warning, the unreachable Next story); tests/claims.json C015, C017 (Turkish clash), C031, C037, C042, C048; timings C007 and C105 (first run, softened to "first run, one Mac"); frameworks research/frameworks.md sections 15 and 16; Maestro versions docs/compat.md.

---

## 4. r/macapps (short post)

**Before you post:** read the subreddit's current rules and sidebar the same day. Our tools have not read them. Self-promotion may not be allowed, may need a flair or a disclosure format, or may be limited to a weekly thread, and a command line tool for developers may be off topic there. If the rules do not clearly allow it, skip this item. Do not post it in other subreddits as a copy.

**Title:** I made a command line tool that makes App Store and Google Play screenshots in every language (Apple silicon, developer tool)

**Link:** `https://shotfleet.com/?utm_source=macapps`

> I am the developer. shotfleet is a Mac command line tool for people who ship an iOS or Android app in several languages. You write one English Maestro flow, it runs it in every language the app ships on simulators and emulators, and it checks each screenshot against the app's own strings (wrong language, copies, missing screens, store sizes). It exports to fastlane's folders; it does not make frames or captions and does not upload.
>
> Apple silicon only. Needs Maestro, Java 17+ and Xcode (iOS) or the Android SDK (Android). Free: `check` on existing screenshots, and `run` for 2 languages. A licence for every language and export is $29 for the first 100 buyers, then $49, once per developer, with a 14-day refund.
>
> I would like feedback from developers: what would stop you from trying it?

**Source of each fact:** README.md ("Why", "What it checks", "Free and paid", "Limits"); site/public/terms.html; site/public/install.sh (Apple silicon only).

---

## 5. Directory blurbs

Reuse these in every directory form. Re-read each directory's rules the same day (marketing/kit/directories.md lists them and the tag per directory). Link: `https://shotfleet.com/?utm_source=<directory>` with exactly one tag per directory. Disclose that you made it wherever there is a comment field. Do not ask for upvotes.

**Name:** shotfleet

**Tagline (53 characters):** One English Maestro flow, every app language, checked

**Pricing line:** Freemium, one-time licence ($29 for the first 100 buyers, then $49)

**Category:** Developer Tools (second choice: Localization). **Platform:** macOS, Apple silicon only.

**60-word description:**

> shotfleet is a Mac command line tool. From a single English Maestro flow it captures App Store and Google Play screenshots in every language your app ships, in parallel on simulators and emulators. It then checks each image for wrong language, copies, missing screens and store size rules. Checking is free, and so are 2 languages. Apple silicon Macs only.

**140-word description:**

> shotfleet is a command line tool for macOS (Apple silicon) that makes localized App Store and Google Play screenshots from one English Maestro flow. It reads the translations compiled into your iOS or Android build, rewrites each text tap for every language ("Next" becomes "Weiter" or "次へ"), and runs the languages in parallel on iOS simulators and Android emulators. It then compares each screenshot with your app's own strings and reports wrong-language images, copies, missing screens and store size rules. Languages that pass export to fastlane's folders; fastlane uploads. It makes no frames or captions. It needs Maestro, Java 17+, Xcode for iOS and the Android SDK for Android. `shotfleet check` is free, and `run` is free for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49 once, with a 14-day refund.

**Source of each fact:** README.md ("Why", "What it checks", "Free and paid", "Limits", "Uploading"); site/public/index.html (title, meta description, requirements line); site/public/llms.txt; tests/claims.json C002, C015, C032, C037, C042, C048.

---

## 6. Maestro community post

**Where:** the Maestro Slack, `#maestro-questions` or the channel the rules point to (join at https://slack.maestro.dev/). **Before you post:** read the workspace and channel rules (not read by our tools). If self-posts are not allowed, answer questions only and mention shotfleet only when asked, in one sentence, with the disclosure that you built it and that it is paid after 2 languages. The first thing to ask, once, is whether a closed, paid tool built on Maestro is welcome in the channel and on the community projects page:

> Hi, a small question before I post anything. I have a Mac command line tool built around Maestro that is closed source, free for a small tier and paid beyond that (it runs one flow in many languages). Is it welcome to mention it here, or are the channel and the community projects page for free and open projects only?

If the answer is yes, post this. Do not use a link tag other than `maestro`.

> Hi all. I built a Mac tool on top of Maestro and would like feedback from people who run flows in several languages. I made it, it is closed source, and it is paid after 2 languages, so weigh it that way. I am not affiliated with the Maestro project.
>
> You write one English flow. shotfleet reads the translations compiled into the .app or APK, rewrites each text selector for each language (`tapOn: "Next"` becomes `(Nächste|Weiter)` for German when the app has two German strings for "Next"), and runs the languages in parallel on iOS simulators and Android emulators. It sets the language by launch arguments on iOS and by per-app locale on Android 13+ (API 33), and starts each language from a fresh state. Then it checks each screenshot against the app's own strings.
>
> It is tested with Maestro 2.0.10 and 2.11.0. Two things I ran into that may help you:
> 1. 2.11.0 only lets `takeScreenshot` write inside its own artifact folder; absolute paths outside it were rejected, so my first 2.11.0 run captured nothing. Flows now name screenshots relative to Maestro's working directory.
> 2. 2.11.0 defines `MAESTRO_DEVICE_UDID`, 2.0.10 does not. I use it to type different text per language on Android (it worked on 2.11.0 in one emulator, German then Japanese).
>
> Limits: Apple silicon Mac only, no frames or captions or upload. Details: https://shotfleet.com/?utm_source=maestro . What would you want from a tool like this, and what would break it on your flows?

**Source of each fact:** README.md ("How it works", "Config", "Limits"); docs/compat.md (2.0.10 and 2.11.0 tested, the `takeScreenshot` finding, `MAESTRO_DEVICE_UDID`); CHANGELOG.md 0.1.1 (the two Maestro 2.11.0 entries); research/maestro-2-11.md; tests/claims.json C015, C016 (selector rewrite), C114 (inputs, partial: the text says what was run).

---

## 7. Waitlist email

**Send once, from your own account, to the addresses on the list only (BCC).** Do not add anyone. The list is deleted within 30 days of sending, as the privacy page says; delete it from Cloudflare after that and keep your word.

**Subject:** shotfleet is out

> Hi,
>
> You joined the shotfleet list, so this is the one email I said I would send: shotfleet is on sale now.
>
> It is a Mac command line tool. You write one English Maestro flow, and it captures your App Store and Google Play screenshots in every language your app ships, in parallel on simulators and emulators. Then it checks each screenshot against your app's own strings: wrong language, copies, missing screens and store size rules. It exports to fastlane's folders; it does not make frames or captions and does not upload to the stores.
>
> What it showed me on my own app: my first full Android run got stuck on one onboarding page in several languages, because the text was taller and Next was below the bottom of a small phone. And `shotfleet check` flagged store listings of another of my apps that had translated captions over a still-English app.
>
> The first 100 buyers pay $29 instead of $49, once, per developer. The price is applied at checkout, and Gumroad does the checkout. A licence includes every language, export, a year of updates and a 14-day refund. It needs an Apple silicon Mac, Maestro, Java 17+, Xcode for iOS and the Android SDK for Android.
>
> Buy: https://shotfleet.com/?utm_source=waitlist#price
> Install: curl -fsSL https://shotfleet.com/install.sh | sh
> Then: shotfleet activate <your key>
>
> `shotfleet check` is free if you only want to see what it finds in screenshots you already have, and `run` is free for 2 languages. If it does not work for your app, email me within 14 days and I will refund you. Your address is deleted within 30 days of this email, or sooner if you ask: https://shotfleet.com/privacy
>
> Manu

**Source of each fact:** site/public/index.html (price section, free tier, requirements); site/public/terms.html (licence, refund, Gumroad, 3 activations); site/public/privacy.html (30-day deletion, one email); README.md ("What it checks", "Free and paid", quickstart); tests/claims.json C042, C056, C100, C107 (caption finding, softened to "flagged ... on another of my apps"); install line: site/public/install.sh.

---

## Do not say

- "Catches all localization bugs", "finds every bug". It found nothing in the unreachable-button case: `run` got stuck; `check` cannot see a missing button.
- "Works with any tool's screenshots". Tested: fastlane snapshot and screengrab output, and a plain folder per language. Say that.
- Anything about fastlane being slow, not parallel or one language at a time. Do not quote speed comparisons: no head-to-head was run. Do not quote competitor prices or features (AppScreens, ButterKit, simshot) unless you re-check them the same day.
- "I could not find any other tool that checks the language of screenshots", or "the only tool". It is an absence claim nobody can prove. Ask instead how people check today.
- "Works with Flutter" or "React Native" without the caveat: one Flutter app and one Expo app, two languages and three screens each; a bare React Native app (Rocket.Chat) only built.
- "Nothing in your app changes". It needs a Debug simulator build (iOS) and API 33+ emulators (Android), and an app with its own saved in-app language choice has not been tested.
- "Frames", "captions", "uploads to the stores", "works with ButterKit and AppScreens" (never tried), "Intel build coming", "runs on Linux", "runs on real devices".
- "Maestro recommends", "official", "partner", "endorsed". Say you are not affiliated.
- Maestro facts that were never checked on 2.0.10 or 2.11.0: that two Android `maestro test` runs share port 7001, that sharded runs expose no shard index, that a header `env:` default beats `-e`. They are not in this pack.
- That the $29 price is a perk of being on the waitlist, or a "N of 100 left" counter. The page has no counter; whoever buys first among the first 100 buyers pays $29.
- "One licence per Mac" or "up to 3 Macs". Say "3 activations per key" and "once per developer".
- "No questions asked" without the condition in the terms, and "VAT included" (prices are before VAT where it applies).
- "Quickstart in 10 minutes" (nobody timed a cold install). "9 minutes" or "15 minutes" without "first run, one app, one Mac". "Reads the text exactly in every script" (iOS reading from the app is not asserted by any run; macOS text recognition has a language list).
- "Two-line fix" or "8 lines": say "a small fix, I made two pages scroll".
- "The first run found it" without saying it was `run` that got stuck, not `check`.
- "Notarized, no Gatekeeper prompt" as a blanket claim. Say what was checked: Apple's notary accepted the program and the package, the package passes `spctl`, and a `curl` install has no quarantine flag.
- That `doctor --fix` was tried on a Mac (it has not been).
- Polar, Lemon Squeezy, Homebrew, "universal binary". Sales are Gumroad only and the build is arm64 only.
- Hype, superlatives, emoji, exclamation marks, em dashes.
