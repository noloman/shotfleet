# shotfleet email drafts

For Manu. Written 2026-10-06. **Drafts only.** Nothing was sent, no Gmail draft was made, no contact form was filled, nobody was signed
in anywhere. You approve each email by number, then send it yourself, from your own address, once.

| # | Recipient | Purpose | Send date / trigger | Status |
|---|---|---|---|---|
| 1 | Integreat team, digitalfabrik@tuerantuer.de | Design partner (free OSS licence) | Wed 7 to Sun 11 Oct | ready |
| 2 | Boardsesh, contact@boardsesh.com | Design partner (free check, key for feedback) | Wed 7 to Sun 11 Oct | ready |
| 3 | Javier Castro (iResucitó), javier.alejandro.castro@gmail.com | Design partner | Wed 7 to Sun 11 Oct | ready |
| 4 | Andrea Bizzotto, codewithandrea.com/contact form | Partner: free key + Gumroad affiliate cut | Wed 7 to Sun 11 Oct, after Gumroad Affiliates is on | ready (needs affiliates on) |
| 5 | Console.dev, hello@console.dev | Directory/newsletter submission | Wed 7 to Sun 11 Oct | ready |
| 6 | Every buyer (Gumroad purchase Workflow email) | Post-purchase: install, activate, reply if stuck | Set up this week; Gumroad sends it on each sale | ready |
| 7 | shotfleet waitlist (BCC, only addresses on the list) | The one launch email the privacy page promises | Mon 19 Oct, only if the list isn't empty and it was never sent | ready (check list first) |
| 8 | iOS Dev Weekly (+ SwiftLee), suggest.iosdevweekly.com form | Newsletter pitch: fastlane snapshot guide | Wed 21 Oct (Thu 22 if Show HN is on the 21st), after `/guides` is deployed | ready (after guides live) |
| 9 | Android Weekly, androidweekly.net submit section | Newsletter pitch: one Maestro flow guide | Same day as 8 | ready (after guides live) |
| 10 | Kotlin Weekly, mailinglist@kotlinweekly.net | Newsletter pitch: the unreachable Next button | Wed 4 Nov or later, after article 3 is published | ready (after article 3 live) |
| 11 | KMP Weekly, kmpweekly.com/submit or hello@kmpweekly.com | Newsletter pitch: Google Play screenshots in every language | After article 5 is published and its steps were run | after article 5 |
| 12 | Indie Dev Monday (Josh Holtz), newsletter@indiedevmonday.com | Indie dev journey suggestion | Mon 26 Oct or later | ready |
| 13 | Rudrank Riyam (asc CLI), rudrankriyam@gmail.com | Partner: asc upload + shotfleet check recipe | After you've run the recipe end to end; week of 26 Oct or later | ready (needs the recipe run) |
| 14 | Flutter Developer Weekly, mark@flutterdeveloperweekly.com | Newsletter pitch: Flutter/RN guide | Week of 2 Nov, after guide 3 is published | after guide 3 |
| 15 | Flutter Tap | Newsletter pitch: Flutter/RN guide | Week of 2 Nov, after guide 3 | needs address (route is a tweet) |
| 16 | Code With Andrea newsletter | Flutter/RN guide | Week of 2 Nov, only if Andrea answered 4 | only if he replied to 4 |
| 17 | Phiture ASO Monthly (ASO newsletter) | "What check found" article | Week of 16 Nov, after that article is out | needs address |
| 18 | A design partner who said yes | Send the key and install steps | When 1, 2, 3 or 4 replies yes | ready (trigger) |
| 19 | A design partner who sent a write-up | Ask for written OK on an exact quote | Only if they wrote something you want to quote | ready (trigger) |
| 20 | Anyone asking for the OSS/student licence | Reply with the 100%-off code | When a request comes to hello@shotfleet.com | ready (trigger) |
| 21 | hn@ycombinator.com | Ask once why the Show HN was flagged | Only if the Show HN shows [dead] or vanishes | ready (trigger) |
| 22 | Existing buyers (Gumroad "Emails" to customers) | 0.1.6 is out: XCUITest on iOS, supply folders | After 0.1.6 is live, only if there are buyers | after 0.1.6 |
| 23 | Users of your other apps | Product news | **Don't send**: no list with consent exists | blocked (no consent) |

Emails that need 0.1.6 are 22 and the swaps marked **[after 0.1.6]** inside 8 and 9. "0.1.6 is live" means
`https://shotfleet.com/download/VERSION` says `0.1.6` and the device test (`tools/fixture-byoc-e2e.sh`) passed.

---

## How I checked, and the rules for all of them

**True today (2026-10-06):** 0.1.5 is live (`/download/VERSION` = 0.1.5). 0.1.6 is on `main`, not live: your own XCUITest tests on iOS,
fastlane supply file names, failure details, plus the AnywhereRoles showcase and the guides go out with its site. `/guides` is still 404
live (the two guides are merged on main as `/guides/fastlane-snapshot-screenshots-all-english` and
`/guides/maestro-one-flow-every-language`). The Docker image and GitHub Action for `check` aren't public yet, so no email mentions Linux.
Licence (live `/terms`): $29 for the first 100 buyers, then $49, once per developer; a year of updates; 14-day refund; the key has 3
activations for your own Macs, and you reset the count by email if someone runs out. Free: `check`, `doctor`, `init`, and `run` for 2
languages. OSS maintainers and students get a 100%-off code by emailing hello@shotfleet.com. Flutter and React Native: one real Flutter app
(wger) and one real Expo app (the obytes template), per the live home page. Apple silicon Macs only, a CLI only, no frames, captions or upload.

**Calendar:** Keysi has Show HN Tue 13 Oct and Product Hunt Wed 14 Oct, so nothing public for shotfleet on 12 to 14 Oct. The private emails
1 to 5 go out before that week. Announcement week is Mon 19 to Sun 25 Oct, Show HN Tue 20 or Wed 21 Oct.

**Copied as they were:** 1, 2, 3, 4 and 5 are section 2 and 1.3 of `marketing/week-1007/APPROVAL-PACKET.md`, word for word. I re-checked
the facts in them today and found nothing wrong (Integreat #2830 is still open; the Code With Andrea contact page, Console.dev's criteria and
the iOS Dev Weekly form all load).

**Reused and corrected:** 7 is `marketing/launch-email.md`; 8 and 9 merge `marketing/launch-drafts/05-newsletter-pitches.md` with
`marketing/kit/newsletters.md`; 10 and 11 are from `kit/newsletters.md`; 12 and 13 from `kit/outreach.md` sections 3 and 4; 18 and 19 from
`kit/outreach.md` section 1; 21 from `kit/launch-day.md`; 23 is `launch-drafts/09-email-other-app-users.md`. Each one says what I changed.

**Rules for every email:** send once, no follow-up chain; silence is an answer. One ask per email. Never offer money or a licence for
coverage (design partners get a licence for honest feedback, with nothing promised about its tone). No quote, name or logo anywhere without
a written yes to the exact words. Mention the price at most once. Run `tools/check-claims.sh` before announcement-week emails. Log each send
(date, recipient, `utm_source`) in one note so nothing goes twice.

---

## 1. Integreat: design partner

- **To:** `digitalfabrik@tuerantuer.de`, the public email on their GitHub organisation: https://github.com/digitalfabrik
- **Send:** Wed 7 to Sun 11 Oct.
- **True detail:** issue #2830 "Update store presence" (open since 2024-06-13) asks for store screenshots in each language with the app in
  that language: https://github.com/digitalfabrik/integreat-app/issues/2830 . React Native app, 26 App Store languages, fastlane metadata in
  the repo. As an open-source project they already qualify for the free licence.
- **Condition:** none.
- **Subject:** `Localized store screenshots for Integreat (issue #2830), free licence`

> Hi Integreat team,
>
> I saw issue #2830 in integreat-app, about new store screenshots in every language with the app itself in that language. That's exactly what I build tools for, so I'm writing once.
>
> I make shotfleet, a Mac command-line tool. You write one Maestro flow in English; it runs it in every language your app has, on iOS simulators and Android emulators, and then checks that each screenshot is really in that language. For React Native it works from your translation files. Honest caveat: I've run it on one real Expo app so far, not on a bare React Native app like yours, so you'd be an early test, not a safe bet.
>
> Open-source projects get a free licence, so it's yours if you want it, no strings. If you try it, I'd like to hear honestly what worked and what didn't. I won't quote you or name the app anywhere without your written yes.
>
> The check part is free anyway and works on screenshots you already have: https://shotfleet.com/?utm_source=integreat
>
> Thanks for the work you do,
> Manu (Manuel Lorenzo)

---

## 2. Boardsesh: design partner

- **To:** `contact@boardsesh.com`, the public email on their GitHub organisation: https://github.com/boardsesh (the Play listing also shows
  support@boardsesh.com: https://play.google.com/store/apps/details?id=com.boardsesh.app)
- **Send:** Wed 7 to Sun 11 Oct.
- **True detail:** their own Maestro capture runs once per device and locale into `app-stores/apple/screenshots/<locale>/<device>/`, driven
  by deep links because Maestro can't see the text on their iOS 26 / React Native build:
  https://github.com/boardsesh/boardsesh/blob/main/packages/mobile/.maestro/app-store.yaml . So the free check is the useful part for them.
- **Condition:** none.
- **Subject:** `Your Maestro app-store.yaml, and a free check for its output`

> Hi Marco,
>
> I read the comments in Boardsesh's `.maestro/app-store.yaml`. Driving the whole capture through deep links because Maestro can't see the text on iOS 26 / Fabric is a clever workaround, and I recognised the pain.
>
> I make shotfleet, a Mac tool for localized store screenshots. Most of it is about rewriting text taps per language, which your setup doesn't need. The part that might be useful is the check: it reads each screenshot and flags one that isn't in its folder's language, blank screens, copies and sizes the stores won't take. It's free with no account. I haven't tried your `<locale>/<device>/` folder layout, so it may need a small step first.
>
> If you try it and send me what broke, I'll give you a full licence for free, no strings, and I won't quote you or name Boardsesh anywhere without your written yes.
>
> https://shotfleet.com/?utm_source=boardsesh
>
> Cheers,
> Manu

---

## 3. iResucitó (Javier Castro): design partner

- **To:** `javier.alejandro.castro@gmail.com`, published by him on the app's site ("Contact me at …"):
  https://jacargentina.github.io/iResucito/ , and on his public GitHub profile.
- **Send:** Wed 7 to Sun 11 Oct.
- **True detail:** his Maestro flow picks the language in the app's own settings with `${LOCALE_LABEL}`:
  https://github.com/jacargentina/iResucito/blob/HEAD/packages/native/maestro/app-store-screenshots.yaml . An in-app language picker is the
  one setup shotfleet hasn't been tested on, and the email says so.
- **Condition:** none. He's a Spanish speaker: if you'd rather write it in Spanish, keep the same points.
- **Subject:** `Your Maestro screenshot flow in iResucitó`

> Hi Javier,
>
> I found iResucitó's `app-store-screenshots.yaml` while looking at how people make localized store screenshots with Maestro. Picking the language in the app's own settings with `${LOCALE_LABEL}` is a neat way round Maestro not setting the locale.
>
> I make shotfleet, a Mac tool for the same job: one English Maestro flow, run in every language on iOS and Android, then every screenshot checked against the app's own strings. To be straight with you, an app with its own language picker is the one case I haven't tested, and I've run one real Expo app, not more. So I'm not sure the capture part fits you. The check part is free and works on the screenshots your flow already makes.
>
> If you want to try it on iResucitó, I'll give you a full licence for free, no strings. All I'd ask is an honest note on what worked and what didn't. I won't quote you or name the app without your written yes.
>
> https://shotfleet.com/?utm_source=iresucito
>
> Saludos,
> Manu

Backup if one of 1 to 3 looks wrong to you (from the packet): My Bible Log (Android, 7 locales, per-locale Maestro capture,
https://github.com/mybiblelog/mybiblelog/blob/HEAD/mobile/.maestro/screenshots/capture.yaml ; developer email on its Play listing
`com.mybiblelog.app`). Not drafted; ask and I'll write it.

---

## 4. Code With Andrea (Andrea Bizzotto): free key + affiliate cut

- **To:** the contact form at https://codewithandrea.com/contact/ ("Send me a message"). The site shows no email address. Paste the text
  into the form yourself.
- **Send:** Wed 7 to Sun 11 Oct.
- **True detail:** his tip "Automated screenshot generation with Maestro" (2025-03-17,
  https://codewithandrea.com/tips/automated-screenshot-generation-maestro/) captures store screenshots per device and language with Maestro,
  and leaves switching the language per run to the reader.
- **Condition:** turn on Gumroad Affiliates for the product first and pick the cut (30% below; change it if you want). Have one 100%-off
  code ready.
- **Subject (if the form has one):** `Your Maestro screenshots tip, and a tool for the language step`

> Hi Andrea,
>
> Your Maestro screenshots tip is one of the few clear write-ups on the topic, and it's what I point people to. I built a Mac tool for the step it leaves to the reader: getting the same flow to run in every language. shotfleet reads the app's translations (ARB for Flutter), rewrites the flow's text taps per language and runs the languages in parallel on iOS and Android, then checks that every screenshot is really in its language.
>
> Honest status for Flutter: I've run one real Flutter app end to end (wger, iOS and Android, German and Japanese), not more. Its Japanese is only partly translated, and the check said so.
>
> Two offers, no strings on either: a free licence, so you can see whether it's any good, and a 30% Gumroad affiliate cut if you ever think it's worth mentioning to your readers. If it isn't a fit, no reply needed.
>
> https://shotfleet.com/?utm_source=codewithandrea
>
> Thanks for all the Flutter content,
> Manu (Manuel Lorenzo)

---

## 5. Console.dev: submission

- **To:** `hello@console.dev`. No form, no fee. Criteria: https://console.dev/selection-criteria (developer tools, self-service; early
  tools must be pre-1.0, which 0.1.5 is). They don't do sponsored reviews, so nothing is offered.
- **Send:** Wed 7 to Sun 11 Oct.
- **True detail:** written to their criteria: free with no account, CLI, docs, `--json`, exit codes.
- **Condition:** run `spctl -a -vv -t exec "$(which shotfleet)"` first. If it doesn't say "Notarized Developer ID", delete "signed and
  notarized".
- **Subject:** `shotfleet: localized store screenshots from one Maestro flow (free check, 0.1.5)`

> Hi,
>
> I'm Manu, a solo developer in the Netherlands, and shotfleet is the command-line tool I built after finding out my app's "localized" store screenshots were mostly English.
>
> You write one Maestro flow in English. shotfleet reads the translations compiled into your iOS or Android build, rewrites every text tap for each language, and runs the flow on several simulators and emulators at once. Then it reads every screenshot back and flags the wrong language, blank screens and sizes the stores won't take. On my M1 Pro, 18 languages x 4 screens took 9 minutes on iOS and 15 on Android (my app, Maestro 2.0.10).
>
> Why it might fit Console: `shotfleet check` is free with no account and works on screenshots from anything (fastlane snapshot, screengrab, a folder per language). It has `--json` and plain exit codes for CI (0 ok, 1 problems, 2 setup error), an MCP server (`shotfleet mcp`), and docs at https://shotfleet.com/docs?utm_source=consoledev . Install is `brew install noloman/tap/shotfleet` or a one-line script; the build is signed and notarized. It's 0.1.5, so early.
>
> Limits, up front: Apple silicon Macs only. Capturing needs Maestro and Java 17+, and Android needs API 33+ emulators. No frames, captions or upload. Flutter and React Native work from the translation files; I've run one real Flutter app and one Expo app, not more. Closed source.
>
> Price: the check is free and capturing is free for 2 languages. Every language is $29 for the first 100 buyers, then $49 once, with a 14-day refund.
>
> Site: https://shotfleet.com/?utm_source=consoledev
>
> Thanks for reading, and no worries if it's not a fit.
> Manu

---

## 6. Gumroad purchase Workflow email (every buyer)

- **To:** each buyer, sent by Gumroad (Workflows → "Purchase" trigger, product shotfleet). You set it up in Gumroad yourself; it's an account
  change.
- **Send:** set it up this week (plan section 4.1, "Trust fixes"), so the first buyer gets it.
- **True detail:** it's the buyer's own purchase. Gumroad's receipt already carries the licence key; this only adds the steps.
- **Condition:** check whether Gumroad's receipt already shows the key. If not, add Gumroad's licence key placeholder where it says
  `<your key>`.
- **Subject:** `Your shotfleet licence: 3 steps to your first run`

> Hi,
>
> Thanks for buying shotfleet. I'm Manu, I made it, and this email comes from me.
>
> 1. Install: `curl -fsSL https://shotfleet.com/install.sh | sh` (or `brew install noloman/tap/shotfleet`)
> 2. Activate: `shotfleet activate <your key>` (the key is on your Gumroad receipt)
> 3. Run `shotfleet doctor --fix` in your app's folder, then `shotfleet init`. It writes a starter flow and tells you what's missing.
>
> The docs: https://shotfleet.com/docs
>
> The key works on 3 of your own Macs, and CI doesn't count. If you run out after a reinstall, email me and I'll reset it.
>
> If anything gets stuck, just reply to this email with what you ran and what it said. I read every one. And if it's not for you, email me within 14 days and you'll get your money back, no questions.
>
> Manu

---

## 7. Waitlist: the one launch email

- **To:** the shotfleet waitlist only, in BCC, from your own account. Run `site/signups.sh` yourself to see the count (it prints addresses,
  so not on a shared screen). Don't add anyone.
- **Send:** Mon 19 Oct, 09:30 (plan 4.1 and 4.2, kit `launch-day.md`).
- **True detail:** these people asked for exactly this email; the privacy page promises one email when shotfleet is out.
- **Condition:** only if the list isn't empty **and** the email was never sent (no sign it was: STATUS.md still lists it as to do). After
  sending, put "purge waitlist" in your calendar for 30 days later (Wed 18 Nov) and then run `site/signups.sh --purge-waitlist`. If the list
  is empty, skip this and there's nothing to purge.
- **Changed from `marketing/launch-email.md`:** added the free tier, Apple silicon and Homebrew; the refund line now matches the live terms
  (email within 14 days); dropped "in parallel" jargon; kept the subject.
- **Subject:** `shotfleet is out ($29 for the first 100 buyers)`

> Hi,
>
> You joined the shotfleet list, so here's the news: it's out. The first 100 buyers pay $29 instead of $49, whoever buys first.
>
> shotfleet takes one English Maestro flow and captures your App Store and Google Play screenshots in every language your app has, then checks each one against your app's own strings before it reaches the stores.
>
> What it caught on my own apps while I built it:
> - an onboarding page whose Next button couldn't be reached in Japanese, Korean, Chinese and Arabic,
> - store listings with translated captions over an app that was still in English.
>
> It runs on Apple silicon Macs. `shotfleet check` is free, and so is capturing 2 languages, so you can see what it does before paying:
>
> `curl -fsSL https://shotfleet.com/install.sh | sh` (or `brew install noloman/tap/shotfleet`)
>
> Buy: https://shotfleet.com/#price
> If it's not for you, email me within 14 days and I'll refund you, no questions asked.
>
> This is the only email you'll get from this list. I'll delete the list within 30 days.
>
> Manu

---

## 8. iOS Dev Weekly (and SwiftLee Weekly)

- **Route:** first try the iOS Dev Directory (https://iosdevdirectory.com, "Add a Site"; needs an RSS feed on the site). If the site is
  listed, don't use the form: the curator already reads it by RSS. Otherwise the form at https://suggest.iosdevweekly.com (fields: name,
  email, link, who published it, blog post yes/no, Swift library yes/no, reason). SwiftLee's writers page
  (https://swiftlee-weekly.com/for-writers/) sends suggestions to this same form, so one submission covers both.
- **Send:** Wed 21 Oct (Thu 22 if Show HN is on the 21st). Once.
- **True detail:** article link, not the landing page (their curators pick articles).
- **Condition:** `/guides/fastlane-snapshot-screenshots-all-english` must load on shotfleet.com (404 today) and its TO VERIFY list be
  ticked.
- **Changed from `05-newsletter-pitches.md`:** the link is now the guide (the kit rule), with the URL as it is on main (`/guides/...`, not
  the old slug in `kit/newsletters.md`); the "103" AnywhereRoles number is out until the showcase is live, and 108 of 120 is used.
- **Form fields:** Name: Manu Lorenzo. Link: `https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english?utm_source=iosdevweekly`.
  Publisher: I wrote it. Blog post: yes. Swift library: no.
- **Reason for inclusion:**

> Why fastlane snapshot screenshots come out in English in every language folder, from the fastlane docs and the old issue threads, and a free way to check each image against the app's own strings before upload. On my own apps that check flagged 108 of 120 store screenshots: translated captions over an app still in English. Disclosure: I make the tool the guide mentions at the end; the guide works without it.

**[after 0.1.6]** If 0.1.6 is live by then, add one sentence before the disclosure: "The tool can now also run your existing XCUITest
screenshot tests in every language."

---

## 9. Android Weekly

- **Route:** the "What do you want to submit?" section on https://androidweekly.net ("Suggest a link for an upcoming Android Weekly Issue.
  Links in each issue will be chosen by us."). Open it for the exact fields.
- **Send:** same day as 8. Once.
- **True detail:** article 2 is the Android angle (per-app locales on API 33+, `clearState` resetting the language).
- **Condition:** `/guides/maestro-one-flow-every-language` must load (404 today).
- **Changed from `05-newsletter-pitches.md`:** guide link instead of the home page; text from `kit/newsletters.md`, shortened.
- **Title:** `Run one Maestro flow in every language: per-app locales, iOS launch arguments, and the traps`
- **Link:** `https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=androidweekly`
- **Note:**

> How to run one Maestro flow in several languages: Android per-app locales (Android 13+, set with adb) and iOS launch arguments, plus the traps that make every run quietly English, like a default in the flow header that beats the command line, and clearState resetting the app language on Android. I wrote it. I also make a paid tool in this area; it's mentioned once at the end and the guide stands without it.

**[after 0.1.6]** No change needed: XCUITest is iOS only.

---

## 10. Kotlin Weekly

- **To:** `mailinglist@kotlinweekly.net`, subject exactly as below (their site: "please do also drop us an email",
  https://kotlinweekly.net). 22,907 readers per the site.
- **Send:** Wed 4 Nov or later: at least two weeks after Android Weekly (their readers overlap), and only once article 3 is live.
- **True detail:** a real Compose fix (`verticalScroll(rememberScrollState())` on two columns).
- **Condition:** article 3 ("the button nobody could reach") is published on shotfleet.com (it isn't on main yet) and its TO VERIFY items
  2, 4, 5 and 6 are ticked. Fix the URL below to its real `/guides/...` path.
- **Changed from `kit/newsletters.md`:** shorter; the URL follows the `/guides/` pattern.
- **Subject:** `Link for submission - Kotlin Weekly`

> Hi,
>
> A short story with a real Compose fix: in Japanese, Korean, Chinese and Arabic, the Next button of my Android onboarding sat below the bottom of a small phone, because the page didn't scroll and the translated text runs taller. The fix is a `verticalScroll(rememberScrollState())` on two columns. The article shows the diff, the broken screen, and how to test for it in your own app.
>
> https://shotfleet.com/guides/the-button-nobody-could-reach?utm_source=kotlinweekly
>
> I wrote it. I also make a paid tool that found the problem while running my app in every language; the article says plainly the tool didn't spot the button itself, and mentions it only at the end.
>
> Thanks,
> Manu

---

## 11. KMP Weekly

- **Route:** the form at https://kmpweekly.com/submit ("Found something interesting about Kotlin Multiplatform? Share it with us!"), or
  `hello@kmpweekly.com` (shown on that page). Use the form if it works.
- **Send:** only after article 5 (Google Play screenshots in every language, with emulators) exists and its steps were run.
- **True detail:** Compose Multiplatform resources are read on both platforms (README); there's a real-app note on a Compose
  Multiplatform app (Kuokka), but say only what you re-check.
- **Condition:** article 5 published. Don't claim a KMP app run unless you have it.
- **Subject (if email):** `Link suggestion: Google Play and App Store screenshots in every language`

> Hi,
>
> An article for KMP readers: how to make Google Play (and App Store) screenshots in every language an app has, with emulators and fastlane, including Compose Multiplatform apps whose strings live in Compose resources.
>
> https://shotfleet.com/guides/google-play-screenshots-every-language-emulators?utm_source=kmpweekly
>
> I wrote it. I also make the tool the last section mentions; it's optional.
>
> Thanks,
> Manu

---

## 12. Indie Dev Monday (Josh Holtz)

- **To:** `newsletter@indiedevmonday.com`, the nomination address on https://indiedevmonday.com/faq ("How can I nominate myself…").
- **Send:** Mon 26 Oct or later (after announcement week, so you have real numbers to tell).
- **True detail:** since 2026 it "follows developers over time" instead of one spotlight (https://indiedevmonday.com/about). Josh is the
  lead maintainer of fastlane (https://joshholtz.com), so the email doesn't knock fastlane and doesn't explain it to him.
- **Condition:** none. Name the workout app the way its store listing does. The "50 sales in 60 days" line is your own STRATEGY.md gate: delete that sentence if you'd rather not share it.
- **Changed from `kit/outreach.md` section 3:** rewritten for the new "journeys" format; dropped the link to article 3, which isn't live;
  added the Josh/fastlane detail.
- **Subject:** `Indie Dev Monday: a solo dev who just started selling a dev tool`

> Hi Josh,
>
> I saw Indie Dev Monday now follows people over time, so here's one journey that has just started.
>
> I'm Manu, a solo developer in the Netherlands. I ship a workout app on iOS and Android in 18 languages, a Mac app (Keysi), and since 5 October a paid command-line tool, shotfleet. It came from finding out my "localized" store screenshots were the English set in 18 folders. You know the fastlane snapshot side of that problem far better than I do; my tool runs one Maestro flow in every language and then checks each screenshot.
>
> Where I am: launched, first strangers only now finding it, and a plain rule for myself: 50 sales in 60 days or it stays a free tool. I'm happy to share the real numbers either way, good or bad.
>
> If that fits a journey, I'd be glad to answer questions. If not, thanks for the newsletter.
>
> Manu
> https://shotfleet.com/?utm_source=indiedevmonday

---

## 13. Rudrank Riyam (asc CLI): a recipe, not a pitch

- **To:** `rudrankriyam@gmail.com`, the public email on his GitHub profile (https://github.com/rudrankriyam; bio "ASC CLI"). The
  alternative is a post in the repo's Discussions (https://github.com/rorkai/App-Store-Connect-CLI/discussions). Pick one, not both.
- **Send:** week of 26 Oct or later.
- **True detail:** asc's README has `asc screenshots upload --path "./screenshots/en-US"` per locale and a capture matrix
  (https://github.com/rorkai/App-Store-Connect-CLI, 7,680 stars today). `shotfleet export` writes `screenshots/<locale>/` folders.
- **Condition:** you've run the upload end to end on a real app with shotfleet's export folder, and paste the real command and asc version
  where marked. If you can't run it, don't send.
- **Changed from `kit/outreach.md` section 4:** repo owner corrected (rorkai, not rudrankriyam); email form instead of a Discussions post,
  as the plan's partner row says; shorter.
- **Subject:** `asc screenshots upload + a language check before it`

> Hi Rudrank,
>
> I make shotfleet, a closed-source Mac tool that captures localized store screenshots from one Maestro flow and checks each one is really in its language. Disclosure done; here's the useful part.
>
> I uploaded shotfleet's export folder with asc, one locale at a time. What I ran: PASTE THE REAL COMMAND, OUTPUT AND `asc --version`. What I didn't test: FILL IN.
>
> The check is free and works on any folder per language, so it could sit right before `asc screenshots upload` for anyone, whether asc or something else captured the images. If a short recipe like that would help your docs, I'm happy to write it as a PR in your format. If it's out of scope, no problem.
>
> Manu
> https://shotfleet.com/?utm_source=asccli

---

## 14. Flutter Developer Weekly

- **To:** `mark@flutterdeveloperweekly.com` (the "Contact Mark" address on https://flutterdeveloperweekly.com, curated by Mark Winters).
  The page footer says © 2020: check that a recent issue exists before sending.
- **Send:** week of 2 Nov, after guide 3 (Flutter/React Native) is published.
- **True detail:** the guide covers ARB files, which the built Flutter app doesn't keep readable.
- **Condition:** guide 3 live; the Flutter claim stays "one real app" (wger).
- **Changed from the "Fresh Flutter" draft in `05-newsletter-pitches.md`:** that newsletter doesn't exist, so this goes to one I found; it
  links the guide, not the home page. Fix the URL to the guide's real path.
- **Subject:** `Link suggestion: localized App Store and Play screenshots for Flutter apps`

> Hi Mark,
>
> A guide for Flutter readers: how to get App Store and Google Play screenshots in every language a Flutter app has, why the strings have to come from the ARB files, and how to check the result.
>
> https://shotfleet.com/guides/flutter-localized-store-screenshots?utm_source=flutterdevweekly
>
> I wrote it. I also make the tool it mentions at the end; to be clear, I've run it on one real Flutter app (wger), not more.
>
> Thanks,
> Manu

---

## 15. Flutter Tap

- **Route:** **needs address.** https://fluttertap.com is a Buttondown newsletter; the only route it gives is "Have something amazing to
  share? Tweet us at @fluttertap!". No email or form. The sender address (news@newsletter.fluttertap.com) is not a submission route; don't
  use it.
- **Send:** week of 2 Nov, after guide 3, if you post on X.
- **Text for the tweet (one link, once):**

> @fluttertap a guide on getting App Store and Google Play screenshots in every language of a Flutter app, from the ARB files, and checking them: https://shotfleet.com/guides/flutter-localized-store-screenshots?utm_source=fluttertap (I wrote it; it mentions my tool at the end)

---

## 16. Code With Andrea newsletter

- **Route:** none separate. His newsletter is his own; the only contact is the form already used in 4.
- **Send:** week of 2 Nov, **only if Andrea answered email 4**. Then reply in that thread; no new message to the form (no follow-up chains).
- **Reply text:**

> Hi Andrea, a short follow-up since you replied: I've now written a Flutter guide on localized store screenshots, from ARB files to the check: https://shotfleet.com/guides/flutter-localized-store-screenshots?utm_source=codewithandrea . If it's useful for your newsletter, it's yours to link; if not, no worries.
> Manu

---

## 17. Phiture ASO Monthly (ASO newsletter)

- **Route:** **needs address.** https://phiture.com/aso-monthly-newsletter/ says their "ASO Research Team collects, summarizes, and analyzes
  the most important updates" each month (first Wednesday). It shows no submission address. Find a route (a contact page or an author on
  the issue) before sending; I didn't find one.
- **Send:** week of 16 Nov, after the plan's week-5 article "What check found in N real store listings" is published (only with owners'
  permission, or your own apps).
- **True detail:** it's a research digest, so pitch data, not the tool.
- **Condition:** the article exists, and every app named in it is yours or the owner said yes in writing.
- **Subject:** `Data for ASO Monthly: how often "localized" screenshots are English underneath`

> Hi,
>
> In case it's useful for ASO Monthly: I checked N store listings that claim several languages, and in N of them the captions were translated but the app under the caption was still in English. The method and the numbers are here: https://shotfleet.com/guides/WHAT-CHECK-FOUND?utm_source=asomonthly
>
> I make the tool I used for it, so take that into account; the numbers stand on their own.
>
> Manu

---

## 18. Design partner said yes: key and steps

- **To:** the person who replied yes to 1, 2, 3 or 4.
- **Send:** when they reply.
- **Condition:** make a single-use 100%-off code in Gumroad first (not FOUNDER29).
- **From `kit/outreach.md` section 1 ("After yes").**
- **Subject:** reply in the same thread.

> Great, thanks. Here's your free code: CODE. Use it on https://shotfleet.com/#price and Gumroad sends the key.
>
> Then: `curl -fsSL https://shotfleet.com/install.sh | sh`, `shotfleet activate <key>`, and `shotfleet doctor --fix` in the app's folder.
>
> If anything breaks, reply with what you ran and what it said, and I'll help. Bad news is just as useful to me as good.
>
> Manu

Log the minutes each partner's first run costs you (plan: over 30 minutes per sale means fix onboarding first).

---

## 19. Asking to quote a partner

- **To:** a partner who sent a write-up or note you'd like to use.
- **Send:** only if there's something you want to quote. Nothing goes public before their written yes to the exact words. Keep the reply.
- **Subject:** reply in the same thread.

> Thanks for writing that up. Could I quote this on shotfleet.com, on PAGE, with your name as NAME AND ROLE?
>
> "EXACT WORDS"
>
> Only if you're happy with it. A no is completely fine, and you can change the words.
>
> Manu

---

## 20. Free licence for open-source maintainers and students

- **To:** whoever asked at hello@shotfleet.com (live site offer).
- **Send:** when the request comes. Check the repo or student proof first.
- **Condition:** one single-use code per request. Note it in your private list (plan 5.2).

> Hi NAME,
>
> Here's your free code for shotfleet: CODE. Use it on https://shotfleet.com/#price and Gumroad sends the key. It's the same licence everyone gets.
>
> If it helps, a public note on how it went would mean a lot, but you don't owe me anything. And if something doesn't work, reply and tell me.
>
> Manu

---

## 21. Show HN flagged

- **To:** `hn@ycombinator.com` (kit `launch-day.md`).
- **Send:** only if the Show HN shows [dead], or doesn't appear on /shownew. Once. Don't repost, don't ask anyone to vouch.

**Subject:** `Show HN: shotfleet flagged?`

> Hi,
>
> I posted a Show HN today, "TITLE" (LINK). It seems to be flagged or dead. Did I break a rule? If so I'd like to know which, so I don't do it again. Happy to accept whatever you decide.
>
> Thanks,
> Manu (HN: YOUR USERNAME)

---

## 22. [after 0.1.6] 0.1.6 is out (existing buyers)

- **To:** your shotfleet buyers, through Gumroad (Emails → to customers of shotfleet). They're customers of this product and this is an
  update to it.
- **Send:** **send after 0.1.6 is live** (VERSION = 0.1.6 and `tools/fixture-byoc-e2e.sh` passed). Only if there are buyers. Never in a
  Keysi week.
- **Condition:** re-read the 0.1.6 CHANGELOG on the day and drop any line that changed.
- **Subject:** `shotfleet 0.1.6: your XCUITest tests, and fastlane supply folders`

> Hi,
>
> shotfleet 0.1.6 is out. What's new for you:
>
> - On iOS, `run` can use your existing XCUITest screenshot tests instead of a Maestro flow. It sets each simulator's language itself and runs several at once. Android still needs Maestro.
> - `check` now understands fastlane supply's file names (`1_de-DE.png`), so no more false "missing" lines on Play folders.
> - A failed language now says which step it stopped on and what was on the screen.
>
> Update with `brew upgrade --cask noloman/tap/shotfleet`, or run the install line again. Your key keeps working.
>
> Questions or problems: just reply.
>
> Manu

---

## 23. Users of your other apps: don't send

- **Status: blocked.** I found no list of your app users who opted in to product news.
- **What I checked:** the repo has no mailing list for WOD Tracker, Stressi, Cairn, Keysi or AnywhereRoles. App Store and Google Play don't
  give you users' emails. Keysi's own privacy page (`Keysi/site/privacy.html`) says an email you type in is used to answer you "and nothing
  else" and "never added to a mailing list", so Keysi support emails can't be used. The shotfleet waitlist can only get email 7. In the
  Netherlands (GDPR and the Telecommunicatiewet) marketing email needs prior consent; the existing-customer exception covers your own similar
  products, and a workout or keyboard app isn't similar to a developer tool. Not legal advice.
- **How to check for yourself:** look for any signup that said in words "news about my apps" (a newsletter tool such as Buttondown,
  Mailchimp or ConvertKit, or a form on one of your app sites). If there is one, and it records when and how each person agreed, you may
  send this once with an unsubscribe link. If not, don't.
- **Subject:** `Something different from me this time: a developer tool`

> Hi,
>
> You're getting this because you signed up for news about my apps. This one is different: it's a tool for people who make apps, so if that's not you, skip it.
>
> It's called shotfleet. It makes App Store and Google Play screenshots in every language your app has, from one flow you write once in English, and checks that every screenshot is really in the right language. I built it because my own store screenshots were wrong in a way I hadn't noticed: the captions were translated, but the app under them was still in English.
>
> The check is free and works on screenshots you already have: https://shotfleet.com/?utm_source=app-newsletter
>
> It runs on Apple silicon Macs. The full version is $29 for the first 100 buyers, then $49, once.
>
> If you know someone who makes apps in a few languages, feel free to forward this.
>
> Manu
>
> [Unsubscribe link, and your postal address if your mail service needs it]

---

## Sources (read 2026-10-06)

- Plan: `research/marketing-plan-2026-10-06.md` (origin/claude/marketing-plan). Packet: `marketing/week-1007/APPROVAL-PACKET.md`
  (origin/claude/marketing-week-1007). Drafts: `marketing/launch-drafts/05-newsletter-pitches.md`, `09-email-other-app-users.md`,
  `marketing/launch-email.md` (origin/claude/launch-drafts). Kit: `marketing/kit/outreach.md`, `newsletters.md`, `launch-day.md`,
  `directories.md`. Truth: origin/main `CHANGELOG.md`, `site/public/guides/`; live https://shotfleet.com/ , /terms , /download/VERSION
  (0.1.5), /guides (404).
- Recipients: https://github.com/digitalfabrik , https://github.com/digitalfabrik/integreat-app/issues/2830 , https://github.com/boardsesh ,
  https://jacargentina.github.io/iResucito/ , https://codewithandrea.com/contact/ ,
  https://codewithandrea.com/tips/automated-screenshot-generation-maestro/ , https://console.dev/selection-criteria ,
  https://suggest.iosdevweekly.com , https://iosdevdirectory.com , https://swiftlee-weekly.com/for-writers/ , https://androidweekly.net ,
  https://kotlinweekly.net , https://kmpweekly.com/submit , https://indiedevmonday.com/faq , https://indiedevmonday.com/about ,
  https://joshholtz.com , https://github.com/rudrankriyam (GitHub API), https://github.com/rorkai/App-Store-Connect-CLI ,
  https://flutterdeveloperweekly.com , https://fluttertap.com , https://phiture.com/aso-monthly-newsletter/
