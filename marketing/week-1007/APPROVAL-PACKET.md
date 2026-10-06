# shotfleet marketing, week of Wed 7 to Tue 13 Oct 2026: approval packet

For Manu. Prepared 2026-10-06 (evening). **Nothing in here has been posted, submitted, emailed, paid for or changed.** No account
was created and no terms were accepted. Every item is a proposal: say yes or no per number (for example "yes 1.1, 1.3, 2.2; no 2.3").
Accounts, terms, payments and every send or submit are yours.

What is TRUE today, and what this packet relies on:

| Fact | Checked how |
|---|---|
| **0.1.5 is live**: `https://shotfleet.com/download/VERSION` = `0.1.5`; Homebrew cask `noloman/tap/shotfleet` = 0.1.5 | curl, 2026-10-06 |
| 0.1.6 (your own XCUITest tests on iOS, fastlane supply file names, failure details) is on `main` but **not live**, and its device test (`tools/fixture-byoc-e2e.sh`) hasn't run. Only "coming in 0.1.6" wording below | origin/main CHANGELOG |
| **Not live yet**: the AnywhereRoles showcase (the live home page still has the `SHOWCASE-PENDING` comment), the two guides (`/guides` is 404; they're merged on main in ba3844e but not deployed), the Docker image and GitHub Action for `check` (docs page has `DOCKER-PENDING`; `github.com/noloman/shotfleet-check-action` is 404) | curl of the live pages |
| Live and usable: free `check` on fastlane snapshot and screengrab output, Homebrew, `shotfleet mcp` (docs `#agents`), 9 clips on `/demo`, free licence for OSS maintainers and students, 108 of 120 (C107) | live site |
| Keysi has Show HN Tue 13 Oct and Product Hunt Wed 14 Oct, so **no shotfleet on HN, PH or Reddit this week**. Everything below is a long-lead listing, a private email, or a plain Maestro answer with no link | plan section 8 |

Where to start (my order, about 3 hours in total): 1.1 AlternativeTo (with the $5 you approved) → 1.3 Console.dev → 2.1 to 2.4 emails →
3.x one Maestro answer a day → the rest. Section 7 (Reddit ads) isn't for this week; it's ready for 26 Oct.

---

## 1. Directory listings

Same facts everywhere, a different first sentence on each site (they're compared against each other, and a copied text looks like spam).
Use one `utm_source` per site so `site/signups.sh --visits` can tell them apart.

Shared facts you may paste into any "pricing" or "requirements" field:

- **Pricing:** Freemium, one-time licence. `check`, `doctor` and `init` are free, and `run` is free for 2 languages. The licence (every language plus export to fastlane) is $29 for the first 100 buyers, then $49, once per developer, with a year of updates and a 14-day refund.
- **Requirements:** macOS 13 or later on an Apple silicon Mac. Xcode for iOS, the Android SDK with API 33+ emulators for Android, Maestro 2.x and Java 17+ for `run`. `check` needs neither Maestro nor Java.
- **Not included:** frames, captions, store upload.

### 1.1 AlternativeTo: as an alternative to fastlane (with the $5 priority review you approved)

- **Where:** https://alternativeto.net, top menu "Add an application" (from the FAQ: https://alternativeto.net/faq/). fastlane's page is https://alternativeto.net/software/fastlane/about/ (MIT, free; only 3 alternatives listed today: Flawless, Handler, Macless).
- **Account (yours):** sign up with Google, GitHub, Apple or email, and **verify the email** before the form lets you submit. Signing up accepts their terms, so that's your click.
- **The $5 (yours):** priority review is a **one-time $5 through Stripe**. Two places offer it: the screen right after you submit the form, or later from your user menu → **My submissions** → **"Get reviewed sooner"** while the app is still waiting. They review it in 1 to 2 business days (up to a week around holidays). It doesn't buy approval or ranking, and it's refundable only before the review happens (FAQ). You type the card into Stripe yourself; I never enter payment details.
- **Rules that matter:** English is required; no unreleased or invite-only apps; don't use the profile to advertise; never offer anything for upvotes (it can push the app down).
- **Fields** (the form is behind sign-in, so field names and limits are from the FAQ and the 2026-10-02 research; shorten if a limit is smaller):
  - Name: `shotfleet`
  - Website: `https://shotfleet.com/?utm_source=alternativeto`
  - Platforms: Mac
  - License: **Freemium**. My reasoning: the free tier does the full check and real captures (2 languages). AlternativeTo says Freemium only when the free version does the main job. If you'd rather not argue that, pick Commercial. Your call.
  - Alternative to: **fastlane** only. Not ButterKit or AppScreens (they make frames and captions; shotfleet doesn't).
  - Tags: `localization`, `app-store-screenshots`, `google-play`, `maestro`, `fastlane`, `command-line`, `developer-tools`
  - Short description (130 characters):
    > A fastlane snapshot alternative: one English Maestro flow captures iOS and Android in every language, then checks each screenshot.
  - Long description:
    > A fastlane snapshot alternative for people who'd rather write one Maestro flow than UI-test code for each platform. shotfleet reads the translations in your app build, rewrites the flow's taps for every language, and runs them on iOS simulators and Android emulators at the same time. Then it reads every screenshot back and flags the wrong language, blank screens and sizes the stores won't take.
    >
    > The check is free and also works on screenshots you already have, including fastlane snapshot and screengrab folders. Capturing is free for 2 languages; every language is a one-time licence.
    >
    > Apple silicon Macs only. Needs Maestro and Java 17+ for capturing. No frames, captions or store upload, so it sits next to fastlane, ButterKit or AppScreens rather than replacing them. Made by a solo developer.
- **Why:** fastlane's AlternativeTo page is where people go when snapshot doesn't switch languages, and it has almost no alternatives listed. The free queue is several thousand apps long, so the $5 moves the listing in front of launch week instead of after it.

### 1.2 SaaSHub

- **Where:** https://www.saashub.com/services/submit
- **Account (yours):** required. Register at https://www.saashub.com/register (email, username, password; no GitHub or Google login shown). Registering accepts their terms (/site/terms). Submitting is free. Their paid "Featured" placement is $99 a month: not suggested.
- **Rules:** rejected if it's a waitlist page, unreleased, on a free subdomain, not in English, from an agency, or sent by email. Submissions with competitors listed get reviewed sooner, and so do accounts verified with an email on your own domain (hello@shotfleet.com through the forwarding).
- **Fields:**
  - Name: `shotfleet`
  - Website: `https://shotfleet.com/?utm_source=saashub`
  - Tagline (87 characters): `Localized App Store and Google Play screenshots from one English Maestro flow, checked.`
  - Description:
    > Localized App Store and Google Play screenshots, made from one English Maestro flow and checked before you upload. shotfleet is a Mac command-line tool: it runs your flow in every language your app has, on iOS and Android at the same time, then reads each screenshot and flags the wrong language, blank screens and store size problems. The check is free and works on fastlane snapshot and screengrab output too. Apple silicon Macs only.
  - Categories: Developer Tools; Localization; Mobile App Development (or the closest they have)
  - Competitors: fastlane, ButterKit, AppScreens
  - Pricing: Freemium; one-time $49 ($29 for the first 100 buyers)
- **Why:** SaaSHub pages rank for "X alternatives" searches and get read by AI answers. It's free, and both of its hard requirements (a real domain, a released product) are true now.

### 1.3 Console.dev: submission email

- **Where:** email **hello@console.dev**, from your address. No form, no account, no fee. Criteria: https://console.dev/selection-criteria (developer tools, self-service, CLI, docs; for early tools, "the release must be pre 1.0", which 0.1.5 is). They don't do sponsored reviews, so don't offer anything.
- **Subject:** `shotfleet: localized store screenshots from one Maestro flow (free check, 0.1.5)`
- **Body:**
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
- **Before sending:** run `spctl -a -vv -t exec "$(which shotfleet)"` on your Mac and make sure it says "Notarized Developer ID". If it doesn't, delete "signed and notarized". Send once; no follow-up for 2 weeks.
- **Why:** Console's newsletter is read by exactly the people who install CLI tools, and the free check means they can try it without signing up, which is their main rule. It's also a long-lead slot, so sending it now lands it after launch week.

### 1.4 Indie App Catalog

- **Where:** the **Non-App-Store** form: https://indieappcatalog.com/non-appstore/submit . The App Store form (`/app/submit`) only takes a US App Store URL, so it doesn't fit.
- **Account (yours):** the Non-App-Store form says "Please log in to submit an app", so you need an account, which means accepting their terms. No fee is mentioned.
- **Fit (honest):** they list indie apps made by "real people". The Non-App-Store section has about 20 apps today, all Mac GUI apps (window and clipboard managers). A command-line tool is a stretch and may be declined. Low cost to try. Fields behind the login weren't readable, so fill them from this:
  - Name: `shotfleet`. Platform: macOS (Apple silicon). Price: Freemium, one-time licence ($29 for the first 100 buyers, then $49).
  - Link: `https://shotfleet.com/?utm_source=indieappcatalog`
  - Description:
    > I'm a solo developer, and I built shotfleet because my app's store screenshots in 18 languages were really the English ones in 18 folders. It's a Mac command-line tool: you write one Maestro flow in English, and it captures App Store and Google Play screenshots in every language your app has, then checks each one is really in that language. The check is free; capturing is free for 2 languages. Apple silicon Macs only.
- **Why:** an indie-maker audience and a backlink. Lowest priority of the six: skip it if you're short on time.

### 1.5 Official MCP Registry: `shotfleet mcp`

- **Where:** https://registry.modelcontextprotocol.io , published with the `mcp-publisher` command (quickstart: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx). Free, in preview (the registry says data resets can happen).
- **What you do:**
  1. `brew install mcp-publisher`
  2. Save the `server.json` below in an empty folder.
  3. `mcp-publisher login github` (a GitHub device-code login, as noloman). That gives you the `io.github.noloman/*` name. The alternative, `com.shotfleet/*`, needs a DNS TXT record on shotfleet.com or a file at `https://shotfleet.com/.well-known/mcp-registry-auth`. More work; not needed now.
  4. `mcp-publisher publish`
- **The catch (honest):** the registry's package types are npm, PyPI, NuGet, OCI (Docker) images and MCPB bundles from GitHub or GitLab releases. **A binary from shotfleet.com, `curl | sh` or a Homebrew cask can't be a package entry.** The schema only requires `name`, `description` (at most 100 characters) and `version`, and the reference docs show a "custom installation" example with only `websiteUrl`. But the quickstart says a package or remote is required. So it may refuse this file. If it does, stop there: the only way round it is building an `.mcpb` bundle on a GitHub release, which is a bigger decision than this week.
- **server.json** (description: 96 characters):
  ```json
  {
    "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
    "name": "io.github.noloman/shotfleet",
    "title": "shotfleet",
    "description": "Capture and check localized App Store and Google Play screenshots from one Maestro flow (macOS).",
    "version": "0.1.5",
    "websiteUrl": "https://shotfleet.com/docs#agents"
  }
  ```
  No `repository` field on purpose: `noloman/shotfleet-skills` is the plugin, not the server's source, and listing it as the source would mislead.
- **Why:** coding agents and MCP directories (Glama among them) read this registry. It's 15 minutes if it's accepted.

### 1.6 Glama

- **Where:** https://glama.ai/mcp/servers ("Add Server").
- **Honest verdict: skip for now.** Glama's server list is built around a GitHub repo with the server's source and a LICENSE, and it scores servers on a Docker build that answers introspection. A closed binary can't pass that, so the listing would show as uninstallable or low-scored, which looks worse than no listing. Its separate "Connectors" section seems to pull remote servers from the official registry (unconfirmed). If 1.5 is accepted, check in 2 weeks whether shotfleet shows up on Glama by itself.
- If you still want to try, the first sentence would be: `An MCP server that lets your coding agent check store screenshots for the wrong language and start captures, on your Mac.`

---

## 2. Outreach emails (send once, no follow-ups)

Same rules for all four: from your own address, once, no follow-up chain. If there's no answer in 2 weeks, that's the answer. No quote, name or logo
goes anywhere without their written yes to the exact words. The three design partners were picked because each one **publicly ships a
localized app on both stores and has written about or built localized store screenshots** (links cited). All three are React Native or Expo,
so the emails say plainly that I've only run one real Expo app.

### 2.1 Integreat (Digitalfabrik / Tür an Tür, non-profit, open source)

- **To:** `digitalfabrik@tuerantuer.de`, the public email on their GitHub organisation profile: https://github.com/digitalfabrik
- **Why them:** a React Native app on iOS and Android, 26 App Store languages, fastlane metadata in the repo. Their issue #2830 "Update store presence" (open since 2024-06-13) asks for store screenshots in different languages "with the screenshot in the matching languages": https://github.com/digitalfabrik/integreat-app/issues/2830 . As an open-source project they already qualify for the free licence the site offers.
- **Subject:** `Localized store screenshots for Integreat (issue #2830), free licence`
- **Body:**
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

### 2.2 Boardsesh (Marco de Jongh)

- **To:** `contact@boardsesh.com`, the public email on their GitHub organisation profile: https://github.com/boardsesh (the Play listing also shows support@boardsesh.com: https://play.google.com/store/apps/details?id=com.boardsesh.app)
- **Why them:** iOS and Android apps in English, French, German and Spanish. They built their own Maestro capture that runs once per device and locale and writes `app-stores/apple/screenshots/<locale>/<device>/`: https://github.com/boardsesh/boardsesh/blob/main/packages/mobile/.maestro/app-store.yaml . The comments say Maestro can't see plain text on their iOS 26 / React Native build, so they drive everything by deep links. That means shotfleet's text rewriting won't help them; the free **check** on the output they already make might.
- **Subject:** `Your Maestro app-store.yaml, and a free check for its output`
- **Body:**
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

### 2.3 iResucitó (Javier Castro, indie developer)

- **To:** `javier.alejandro.castro@gmail.com`, published by him on the app's site ("Contact me at …"): https://jacargentina.github.io/iResucito/ , and on his public GitHub profile.
- **Why him:** an indie app on the App Store and Google Play (6 App Store languages, 14 translation files in the repo) with a Maestro screenshot flow that switches the language inside the app: https://github.com/jacargentina/iResucito/blob/HEAD/packages/native/maestro/app-store-screenshots.yaml . Honest snag: an in-app language picker is the one setup I haven't tested, so the email says so.
- **Subject:** `Your Maestro screenshot flow in iResucitó`
- **Body** (in English; he's a Spanish speaker, so if you'd rather write it in Spanish, keep the same points):
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

Backups if one of the three looks wrong to you: My Bible Log (Android, 7 locales, per-locale Maestro capture,
https://github.com/mybiblelog/mybiblelog/blob/HEAD/mobile/.maestro/screenshots/capture.yaml ; developer email on its Play listing
`com.mybiblelog.app`). Not suggested: Bati (not in the stores yet).

### 2.4 Code With Andrea (Andrea Bizzotto): affiliate + free key

- **Where:** his contact form, https://codewithandrea.com/contact/ ("Send me a message"). The site shows no email address. The sponsorship page is gone (404), and he has no affiliate programme of his own, so this offers **yours**.
- **Before sending (yours):** decide the affiliate cut and turn on Gumroad Affiliates for the product (Gumroad allows 1 to 75%). I wrote 30% below; change the number if you want. Have one 100%-off code ready for him.
- **Why him:** his article "Automated screenshot generation with Maestro" (2025-03-17, https://codewithandrea.com/tips/automated-screenshot-generation-maestro/) teaches capturing store screenshots per device and language with Maestro and `takeScreenshot`, and it's a module in his paid Flutter in Production course. What it doesn't cover is how to switch the language per run, which is the part shotfleet does. His Flutter newsletter is large.
- **Message:**
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

## 3. Maestro community: 3 open questions with a drafted answer

Where: the GitHub issue or discussion itself, from your account. No shotfleet in any of the three this week (kit rule for weeks 1 and 2: help
first, no product name). I looked for a readable public Slack archive and found none. Only one open Maestro issue is a real locale bug (#2654); the
other two are a locale design discussion and a selector bug that bites multi-language lists. **Run each snippet on your Maestro version before
posting** and say which version you used.

### 3.1 Issue #2654: iOS permission helper only dismisses English alerts

- **Link:** https://github.com/mobile-dev-inc/Maestro/issues/2654 (open, verified today; opened 2025-08-20 on Maestro 1.41.0). With a Spanish simulator, the notification permission alert isn't dismissed and the test fails. The only replies are a bot link and "related". On main, Maestro's iOS driver still looks for the English alert text (`PermissionButtonFinder.swift`).
- **Answer:**
  > Still happens on current main as far as I can tell: the iOS driver looks for the English alert text, so a Spanish or German simulator never matches. Two workarounds until it's fixed:
  >
  > 1. Tap the button yourself with a regex that covers your languages, right after the step that triggers the alert. `optional: true` keeps English runs passing:
  >    ```yaml
  >    - tapOn:
  >        text: "(Allow|Permitir|Erlauben|Autoriser|Consenti)"
  >        optional: true
  >    ```
  >    Text selectors are regular expressions (https://docs.maestro.dev/maestro-flows/flow-control-and-logic/how-to-use-selectors). Check the exact button label for your iOS version in each language; Apple has changed wording before.
  > 2. If you don't need the device itself in Spanish, keep the simulator in English and only switch the app: `launchApp` with `arguments` (for example `AppleLanguages: "(es)"` and `AppleLocale: "es_ES"`). The alert then stays English and the built-in helper works.
  >
  > Note that `permissions: { all: allow }` doesn't get you out of this for notifications: per the docs, iOS doesn't grant those silently, so Maestro still has to tap the alert (https://docs.maestro.dev/maestro-flows/flow-control-and-logic/permissions).
  >
  > Tested on: MAESTRO VERSION, iOS VERSION simulator.
- **Why:** a real, unanswered bug that hits everyone running a non-English simulator. Before posting, test both routes; route 2's `AppleLanguages` form isn't in Maestro's docs.

### 3.2 Discussion #3018: "Centralizing Device Configurations for iOS 26 Rollout"

- **Link:** https://github.com/mobile-dev-inc/Maestro/discussions/3018 (open; started by Maestro staff 2026-02-26; 1 comment). It proposes `platform.ios/android.locale` in `config.yaml` and asks whether `--device-locale` should be a flag on `maestro test`.
- **Answer** (feedback from real use, which is what they asked for):
  > +1 to locale in config and as a flag on `maestro test`. Today the docs say you can only set it with `start-device` or `cloud`, so running one flow in 10 languages means restarting devices 10 times.
  >
  > Some things I ran into doing per-language runs, in case they help the design:
  >
  > - **Device locale vs app locale.** On iOS, launch arguments (`AppleLanguages`, `AppleLocale`) switch only the app, and that's often what screenshot runs want. But system alerts then stay in the device language, which is where #2654 bites. It would help if the config made clear which one you're setting, or allowed both.
  > - **Android per-app locale needs API 33+.** `adb shell cmd locale set-app-locales <package> --locales de-DE` works on Android 13+ images only, and `clearState` wipes it. If Maestro sets it, the order (clear, then set, then launch) matters.
  > - **Text selectors break per language.** Anything that sets the locale will surface this right away. A short docs note next to the new option, pointing to `id:` selectors and regex alternatives, would save a lot of "why does tapOn fail in German" questions.
  >
  > On the poll: a flag on `maestro test` (overriding config) feels most natural for CI matrices.
- **Why:** it's the Maestro team asking for exactly this input, so it's useful and visible to them. Before posting, re-check the Android line on an API 33+ emulator (the kit's article 2 TO VERIFY item 5).

### 3.3 Issue #1479: "tapOn with regular expression that starts with '+'"

- **Link:** https://github.com/mobile-dev-inc/Maestro/issues/1479 (open; opened 2023-09-22, Maestro 1.31.0, iOS 17 simulator). A regex tap on a phone prefix (`+33 .*`) taps the wrong row (Spain instead of France). No answer solves it.
- **Answer:**
  > Text selectors are regular expressions, so a leading `+` is a regex quantifier, not a literal plus. That's why `+33 .*` matches the wrong row. Escape it:
  > ```yaml
  > - tapOn: '\+33 .*'      # single quotes: the backslash stays as is
  > - tapOn: "\\+33 .*"     # double quotes: YAML needs the backslash doubled
  > ```
  > Same for `(`, `)`, `.`, `?` and `*` in labels, which shows up a lot with translated text (prices, "Next (2/3)" and so on). If the row has a stable id, `tapOn: { id: ... }` avoids the problem and also keeps working when the list is translated.
  >
  > Tested on: MAESTRO VERSION.
- **Why:** a short, correct fix for a 3-year-old open question, and the same trap hits regex taps over translated lists. Before posting, run both lines; if escaping doesn't fix it on your version, don't post.

Where shotfleet would truly fit later (not this week): if someone in these threads asks "is there a tool that runs one flow in every language?", use the disclosure line in `marketing/kit/maestro-community.md`, once, without a link.

---

## 4. Subreddit rules digest (read only; nothing is posted this week)

**I could not read the live sidebars.** Reddit blocks this machine: curl gets 403 on every `about/rules.json`, Claude in Chrome refuses reddit.com
("not allowed due to safety restrictions"), and so does the built-in browser. Below is a third-party snapshot (threadotter.com, "last checked July 2026")
plus the earlier research. **Before any Reddit post, open each sub's sidebar, rules and pinned posts yourself and screenshot the rule you rely on.**

| Sub | What a paid dev tool may do (secondary sources) | When | Draft status |
|---|---|---|---|
| r/androiddev | Promotion only with **mod permission** or inside designated threads (weekly/monthly showcase or app-feedback threads). Rule 5 as summarised earlier: a promotional post needs a thoughtful description and background, no copied marketing text. Send modmail first; skipping it is "the most common avoidable removal" | A showcase-thread comment early in a month, or a standalone technical post only after a mod says yes | `02-reddit.md` has the showcase comment and the modmail; matches this |
| r/iOSProgramming | **App Saturday only**: Saturdays, one app **once per year**, mods proposed about 20 sub karma in 6 months and a template (tech stack, challenges, AI disclosure). The July 2026 snapshot found no clear written rule: "NOT permission" | Sat 24 Oct at the earliest (plan), better after 0.1.6 is live so XCUITest can be said as available | Draft follows the template; add an AI-use line (agents drafted the text and helped build it) |
| r/FlutterDev | Promotion only with mod permission or in designated threads. Earlier summary: apps only if open source or an "insightful dive". Off-topic or ad-looking posts get removed | Not at launch. Later, a real dive (how Flutter strings work for screenshot tools) with the tool mentioned once | Draft says "probably skip": agree |
| r/SideProject | Self-promotion is the point. Title format `[Project name] - [Short description]`; say it's yours; screenshots or GIF; a live link with no email gate; don't repeat the same project often; no identical cross-posts | Any day in launch week; US morning | **No draft yet**: add one for launch week (story first, the grid and a clip) |
| r/macapps | Dev posts **once per developer per 30 days** (trusted devs: once per app); **10 r/macapps karma** to self-promote even in comments; otherwise the monthly megathread; modmail first; disclose; correct flair and template; headline `AppName — descriptor` | After Keysi. Note: if you post Keysi there on 13/14 Oct, shotfleet can't go there until about 13 Nov | **No draft yet**. A CLI is a fringe fit for that sub; low priority |

General: Reddit's old 1-in-10 guideline still matters to mods. If your account is mostly empty in these subs, spend the Keysi week answering
questions (no links) first.

---

## 5. Read-only checks

### 5.1 GA4 events (read in Chrome with your session, nothing changed)

Property `shotfleet` (557101981), Admin → Data display → Events, read 2026-10-06 evening:

- **Recent events (last 28 days, stream shotfleet.com):** `first_visit`, `page_view`, **`pricing_view`**, `scroll`, `session_start`.
- **`cta_click`: not seen yet.** Nobody who accepted the cookie banner has clicked a buy button.
- **Key events:** `close_convert_lead` and `qualify_lead` (Google's defaults, starred) and `purchase` (not starred), all "No stream data detected". **`pricing_view` is not a key event yet.**

**Your action (10 seconds, yours because it changes the property):** on that page, Recent events, click the star next to `pricing_view`. Do the same
for `cta_click` once it appears. I only clicked the two tabs to read them.

### 5.2 Did the waitlist email go out?

**No sign that it did.** Evidence (repo and coordinator state only; I didn't open your mailbox or the KV store):

- `STATUS.md` on main still lists "launch email" among the things to do (lines 34 and 91).
- `research/site-claims-audit-2026-10-06.md` row 28: "STATUS.md:29 and :85 still list the launch email as not sent, so the 30 days haven't started."
- `research/docs-audit-2026-10-05.md`: "I do not know whether the launch email went out."
- `coordinator-state.md` has no entry for sending it. Last known count: **0 signups** (STATUS.md R8, "not re-read today").
- The live privacy page still promises: "I will delete the waitlist within 30 days after I send the launch email, or sooner if you ask."

**What to do (your choice):** run `site/signups.sh` to see the count (it prints the addresses, so run it yourself). If it's 0, there's nothing to send
or purge. If there are people, send `marketing/launch-email.md` on announcement day (Mon 19 Oct), put "purge waitlist" in your calendar for 18 Nov, and
then run `site/signups.sh --purge-waitlist`.

---

## 6. What the launch drafts must change (list of edits, not rewrites)

Files on `origin/claude/launch-drafts` in `marketing/launch-drafts/`, plus kit files that feed them.

**True now, so update:**

1. `README.md` gate 1: **0.1.5 is live** (VERSION = 0.1.5 on 2026-10-06). Mark the gate passed. In "Facts used", change "cask at 0.1.4" to "cask at 0.1.5".
2. `README.md` gate 2 and every AnywhereRoles line: **still not live** (live home page has `SHOWCASE-PENDING`). It's on main and goes out with the 0.1.6 site. Until then, use C107 ("108 of 120 store screenshots of another of my apps flagged: translated captions over an app still in English") in:
   - `01-show-hn.md`, first comment, the "127 problems, 103 … recaptured … 0 problems" sentences;
   - `02-reddit.md`, r/iOSProgramming "The problem" paragraph ("103 problems");
   - `06-short-posts.md` thread 4/5. Skip standalone post E.
3. `01-show-hn.md`, "the only outside call is the licence check with Gumroad": **not true**. `doctor` also asks shotfleet.com for the latest version number (privacy page), and `doctor --fix` downloads from GitHub, Adoptium and Google. Change to: "Your app and screenshots never leave your Mac. It talks to Gumroad for the licence, and `doctor` asks shotfleet.com for the latest version number."
4. `01-show-hn.md`: add one line under Price: "Open-source maintainers and students can email me for a free licence." It's live, and it answers "closed and paid" (plan 5.2).
5. `01-show-hn.md` and `02-reddit.md`: once the guides are deployed (`/guides` is 404 today), link the matching guide in the first comment / at the end, with its own `utm_source`. Not before.
6. `10-faq-objections.md`, "Can it run in CI?": fine for macOS runners. **Don't add** Linux, Docker or the GitHub Action yet: 0.1.5's CHANGELOG lists them, but they aren't public (docs page has `DOCKER-PENDING`, the Action repo is 404, and anonymous pulls from ghcr are denied). The "Mac only?" answer ("If you're on Linux, I can't help you yet") stays true until then.
7. `research/marketing-plan-2026-10-06.md` section 1.4 says "`check` runs on Linux and in CI through the Docker image and GitHub Action in 0.1.5". Same problem as 6: don't paste that into any reply until the image and Action are public.
8. Kit files the drafts still point to, both stale on Flutter/React Native (one real Flutter app, wger, and one Expo app have run since): `marketing/kit/directories.md` section 5 (Console.dev email: use 1.3 above instead) and `marketing/kit/outreach.md` section 1 ("I have not run it on a real Flutter or React Native app yet").
9. `07-directories.md`: add Console.dev, Indie App Catalog (Non-App-Store form), MCP registry and Glama from section 1 here, and note that Indie App Catalog's App Store form doesn't fit.
10. `02-reddit.md`: add the live-read caveat from section 4 here, an r/SideProject draft, and an AI-use line in the App Saturday post (the template asks for it).

**When 0.1.6 is live** (VERSION = 0.1.6 and its device test passed; claims C231/C235 out of "untested"), and only then:

11. `01-show-hn.md`, "What it doesn't do": replace "It's built on Maestro. Support for your own XCUITest tests on iOS is coming in 0.1.6, not out yet." with "On iOS it can also run your existing XCUITest screenshot tests instead of a Maestro flow (new in 0.1.6). Android capture still needs Maestro." And "It needs Maestro and Java 17+" becomes "Capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests."
12. `10-faq-objections.md`, "Only Maestro?": same change. Add that the XCUITest path is paid like `run` (2 languages free) and iOS only.
13. `02-reddit.md` r/iOSProgramming "The paid part": replace the "coming in 0.1.6" sentence with the XCUITest line from 11. That makes App Saturday worth spending.
14. `03-product-hunt.md`, "What it isn't": same as 11.
15. Anything that says `check` works on "fastlane folders" in general: until 0.1.6, say **snapshot and screengrab** output. Play metadata folders from **fastlane supply** (`1_de-DE.png` names) give false "missing" lines in 0.1.5; 0.1.6 fixes that. After 0.1.6, "fastlane snapshot, screengrab and supply folders" is fine.

Unchanged and still true: prices, the 9/15-minute numbers with "on my M1 Pro, my app, Maestro 2.0.10", the unreachable Next button, the Turkish clash,
Homebrew, the 14-day refund, Apple silicon only.

---

## 7. Reddit ads test (approved by you via the coordinator: about $30 to $50, from Mon 26 Oct)

Not for this week; it's here so the copy is approved early. You create the ad account, add the payment method and press start. I don't touch any of it.

**Reddit's official ad policy and help pages could not be read** (redditinc.com is blocked for my tools; business.reddithelp.com only renders
with JavaScript). The policy and limits below are from third-party 2026 summaries. Read the official policy in Ads Manager before paying.

### 7.1 Policy points that matter (secondary, verify)

- Software and developer tools have no special restriction. The landing page must load, match what the ad says, and not redirect deceptively. Crypto and finance are restricted.
- **AI-generated creative must reportedly be disclosed** (2026). These texts were drafted by Claude. If Ads Manager has a disclosure toggle, turn it on.
- You may lock comments, but don't delete fair criticism. Better: leave comments on and answer them yourself as the maker.
- Limits: headline up to 300 characters (60 to 80 recommended), CTA text up to 30. Every headline below is at most 103.

### 7.2 Setup (all yours)

1. https://ads.reddit.com → create the advertiser account (accepts Reddit's advertising terms: your click).
2. Add the payment method (you type it; I never enter card details).
3. Campaign: objective **Traffic** (clicks), not conversions (no pixel). **Lifetime budget $40**, hard cap. Start Mon 26 Oct, end Mon 2 Nov.
4. One ad group (Reddit's minimum is reportedly $5 a day per ad group, so one group with 3 ads, rather than 3 starved groups): community targeting from 7.4, feed placement, all devices, manual CPC bid at the suggested floor. Don't use "maximise conversions" or auto-expand.
5. Three ads, 7.3. Image: `site/public/og.jpg`, or the WOD Tracker grid from the home page (your own app, so no third-party logos). CTA button: "Learn More".
6. No Reddit Pixel needed: the UTM tags plus the site's own counter and Gumroad are enough at this size.

### 7.3 Ad variants

The site's first-party counter splits only on `utm_source`, so all three use `utm_source=reddit-ads` (separate from the organic `reddit-<sub>` tags in the drafts). `utm_medium`, `utm_campaign` and `utm_content` show up in GA4 and in Gumroad's referrer data.

**A: the Maestro problem** (headline 103 characters)
- Headline: `Your Maestro flow only taps English buttons? Run it in every language your app has, on iOS and Android.`
- Body: `shotfleet runs one English Maestro flow in every language your app has, then checks each screenshot. Apple silicon Mac. 2 languages free.`
- Link: `https://shotfleet.com/?utm_source=reddit-ads&utm_medium=paid&utm_campaign=launch-test&utm_content=a-maestro`

**B: the question** (headline 100 characters)
- Headline: `Are your German App Store screenshots really in German? A free command reads each one and tells you.`
- Body: `shotfleet check compares each screenshot with your app's own strings: wrong language, blank screens, store sizes. Free, no account.`
- Link: `https://shotfleet.com/?utm_source=reddit-ads&utm_medium=paid&utm_campaign=launch-test&utm_content=b-check`

**C: fastlane users** (headline 85 characters)
- Headline: `fastlane snapshot stuck in English? Run a free check on the folder before you upload.`
- Body: `Point shotfleet check at your fastlane snapshot or screengrab folder. It flags screens still in English. Free, no Maestro needed.`
- Link: `https://shotfleet.com/alternatives?utm_source=reddit-ads&utm_medium=paid&utm_campaign=launch-test&utm_content=c-fastlane`
- If 0.1.6 is live by 26 Oct, you may swap C's body to: `Or let shotfleet run your existing XCUITest screenshot tests in every language, on several simulators at once. iOS, Apple silicon Mac.`

None of them mentions the price, a countdown, Flutter or React Native, frames, captions or upload, or any Maestro endorsement. B and C promise only the free part, which is true for everyone.

### 7.4 Targeting

- **Communities:** r/iOSProgramming, r/androiddev, r/swift, r/Kotlin, r/FlutterDev, r/reactnative, r/expo, r/SwiftUI (Ads Manager shows the reach; aim for 50k+ combined).
- **No interest or keyword targeting** on top (too broad for a Mac CLI).
- **Countries:** United States, United Kingdom, Canada, Australia, Ireland, Netherlands, Germany, the Nordic countries. A starting guess, not data.
- **Devices:** all. Don't restrict on a guess.

### 7.5 Budget split and schedule

- $40 lifetime = $5 a day for 8 days (Mon 26 Oct to Mon 2 Nov), all three ads in one group. Reddit shifts spend towards the better ad by itself; that's fine.
- Day 3 (Wed 28 Oct): pause any ad with 0 clicks or rejected. Don't raise bids to force delivery.
- If after $10 there are Reddit clicks but fewer than 3 `view` events for `reddit-ads` in `site/signups.sh --visits`, the link or tag is broken: pause and fix, don't top up.

### 7.6 What counts as worth continuing

Read on 28 Oct and 2 Nov: Reddit (impressions, clicks, spend), `site/signups.sh --visits` lines with `|reddit-ads|` (`view`, `pricing`, `cta`), GA4 (`cta_click` by campaign), Gumroad (sales and product views by referrer/UTM).

Gumroad's checkout page is on Gumroad, so the closest thing to "cost per checkout view" we can measure is **cost per buy-button click** (`cta` for `reddit-ads`), checked against Gumroad's product views for that day.

- **Continue** (one more $40, same rules) if any of these: at least 1 sale traced to `reddit-ads`; or **cost per buy-button click at or under $5** with at least 3 clicks. (One $29 sale nets about $24.46, so $5 per click pays back if about 1 in 5 clickers buys. That's a guess to replace with real numbers.) Pricing views per visit should also be at least the organic ratio from the week before.
- **Stop** if cost per click is over $3 and there's no buy-button click after $25, or if `pricing` per `view` is under half the organic ratio.
- **Write down after:** spend, impressions, clicks, CPC, views, pricing, cta, sales, refunds, and one line on what you'd change. That goes in MARKETING.md under measuring.

---

## Sources (all read 2026-10-06)

- Live site: https://shotfleet.com/ , /docs , /privacy , /whats-new , /download/VERSION ; /guides (404); Homebrew cask https://github.com/noloman/homebrew-tap
- Repo: origin/claude/marketing-plan (`research/marketing-plan-2026-10-06.md`, `marketing/kit/outreach.md`, `maestro-community.md`, `directories.md`, `reddit-ads.md`); origin/claude/launch-drafts (`marketing/launch-drafts/*`); origin/main (CHANGELOG.md, README.md, STATUS.md, LAUNCH.md, site/signups.sh); origin/claude/015-judge-speed (`research/site-claims-audit-2026-10-06.md`); `/Users/manu/Developer/shotfleet-rc-build/coordinator-state.md`
- Directories: https://alternativeto.net/faq/ , https://alternativeto.net/software/fastlane/about/ , https://www.saashub.com/services/submit , https://www.saashub.com/register , https://www.saashub.com/featured-products , https://console.dev/selection-criteria , https://indieappcatalog.com/app/submit , https://indieappcatalog.com/non-appstore/submit
- MCP: https://github.com/modelcontextprotocol/registry (docs: quickstart, authentication, package-types), https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json , https://glama.ai/mcp/servers , https://glama.ai/blog/2025-07-08-what-is-glamajson
- Outreach: https://github.com/digitalfabrik , https://github.com/digitalfabrik/integreat-app/issues/2830 , https://github.com/boardsesh , https://github.com/boardsesh/boardsesh/blob/main/packages/mobile/.maestro/app-store.yaml , https://play.google.com/store/apps/details?id=com.boardsesh.app , https://jacargentina.github.io/iResucito/ , https://github.com/jacargentina/iResucito , https://codewithandrea.com/contact/ , https://codewithandrea.com/tips/automated-screenshot-generation-maestro/
- Maestro: https://github.com/mobile-dev-inc/Maestro/issues/2654 , https://github.com/mobile-dev-inc/Maestro/discussions/3018 , https://github.com/mobile-dev-inc/Maestro/issues/1479 , https://docs.maestro.dev/maestro-flows/flow-control-and-logic/how-to-use-selectors , https://docs.maestro.dev/maestro-flows/flow-control-and-logic/permissions , https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales
- Reddit rules (secondary, July 2026 snapshot): https://www.threadotter.com/subreddit-rules/androiddev , /iOSProgramming , /FlutterDev , /macapps , /SideProject
- Reddit ads (secondary): https://www.auditsocials.com/blog/reddit-advertising-policy-compliance-guide-2026 , https://www.stackmatix.com/blog/reddit-ads-targeting-options-2026 , https://lettercounter.org/blog/reddit-ads-character-limits/ , https://ppc.land/reddit-ads-minimum-prices
- GA4: analytics.google.com property 557101981, Admin → Events (read only, your Chrome session)
