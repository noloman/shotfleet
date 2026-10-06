# Directory listings

Manu submits each one. Read each site's rules again the day you submit. The general text (50/150/300-character descriptions, tags, requirements) is in `marketing/kit/directories.md` "Master text"; below is what's new or different, per directory.

Updated short descriptions (the kit's ones predate 0.1.5):

- **150 characters:** `A Mac command-line tool that runs one English Maestro flow in every language your app has, on iOS and Android, and checks every screenshot.` (139)
- **300 characters:** `shotfleet runs one English Maestro flow in every language your app has, on iOS simulators and Android emulators at once, then checks each screenshot for the wrong language, blank screens and store sizes. check is free and also works on fastlane snapshot and screengrab output. Apple silicon Macs.` (296)

---

## 1. AlternativeTo

- **Submit:** https://alternativeto.net, sign in, "Suggest new application" (FAQ: https://alternativeto.net/faq).
- **Rules (from the 2026-10-02 research, read first-hand then):** don't use the listing to advertise; don't reward upvotes (discounts for votes can push the app down); the free queue is "usually at least a few months"; an optional $5 priority review takes 1 to 2 business days. Paying the $5 is your decision, not mine.
- **Name:** shotfleet
- **Platforms:** Mac
- **License:** Freemium (the free tier does the check fully and captures 2 languages)
- **Short description:** the 150-character text above.
- **Long description:** the 300-character text, plus: `No frames, captions or store upload: use it with fastlane, ButterKit or AppScreens for those. Needs Maestro and Java 17+ for capturing. Made by a solo developer.`
- **Alternative to:**
  - **fastlane** (snapshot and screengrab): yes, same job (capturing the screenshots in every language).
  - **ButterKit:** AlternativeTo has a ButterKit page (https://alternativeto.net/software/butterkit/about). Only partly the same job: ButterKit captures from the iOS Simulator and adds frames, captions and upload. shotfleet doesn't do frames or captions. Listing it as an alternative is fair only with the "works together" sentence below, otherwise people who want frames land on the wrong tool.
  - **AppScreens:** AlternativeTo has a page (https://alternativeto.net/software/appscreens/). Different job (mockups from screenshots you upload). Don't list shotfleet as its alternative; if a field lets you say "works with", use that.
- **Tags:** localization, app-store-screenshots, google-play, maestro, fastlane, command-line, developer-tools
- **Text for a ButterKit "alternative" comment, if the form has one:**
  > I made shotfleet. It does a narrower job than ButterKit: it captures the raw screenshots in every language from one Maestro flow, on iOS and Android, and checks they're really in that language. No frames or captions, so many people would use both.
- **Link:** `https://shotfleet.com/?utm_source=alternativeto`

## 2. SaaSHub

- **Submit:** https://www.saashub.com/services/submit (free).
- **Rules (read 2026-10-06):** rejected if it's a waitlist landing page, not launched yet, on a free subdomain, not in English, from an agency, or sent by email. They suggest adding categories and competitors, and verifying with an email on your own domain for faster review (use hello@shotfleet.com; you'd have to receive their mail through the forwarding).
- **Name:** shotfleet. **Website:** `https://shotfleet.com/?utm_source=saashub`
- **Tagline:** `Localized store screenshots from one English Maestro flow`
- **Description:** the 300-character text.
- **Categories:** Developer Tools; Localization; Mobile App Development (pick the closest they offer).
- **Competitors to list:** fastlane, ButterKit, AppScreens.
- **Pricing:** Freemium; one-time $49 ($29 for the first 100 buyers).

## 3. Awesome-ASO (GitHub PR)

- **Repo:** https://github.com/rafaecheve/Awesome-ASO (README, section "Tools").
- **Rules (CONTRIBUTING.md, read 2026-10-06):** format `[Name](link) - Description.`; keep name + description under 100 characters; list stays alphabetical; one PR per suggestion; commit message `Add Company Foo.io`; check for duplicates first. The Tools list already has paid screenshot tools (Screenies, Shotlingo, Storelift) and quotes each description.
- **Line to add:** right after `Screenproof`. Strictly alphabetical, shotfleet comes before Shotlingo and Shots; the live list has Shots before Shotlingo, so it isn't strict. Put it after Screenproof and copy that line's number (the numbering is uneven).

```
12. [shotfleet](https://shotfleet.com) - "Checks localized App Store and Play screenshots for the wrong language."
```

  Name + description: 80 characters.
- **Commit message:** `Add shotfleet.com`
- **PR title:** `Add shotfleet to Tools`
- **PR body:**
  > Adds shotfleet to Tools. It captures App Store and Google Play screenshots in every language from one Maestro flow, and its free check command flags screenshots in the wrong language, blank screens and store size problems. I made it. It's a paid Mac tool with a free tier; happy to change or drop the line if it doesn't fit.

## 4. awesome-maestro (GitHub PR)

- **Repo:** https://github.com/ludovicobesana/awesome-maestro, section "Tools and Integrations".
- **Rules (CONTRIBUTING.md, read 2026-10-06):** one change per PR, clear description, check issues first. Nothing about paid tools; the list already has commercial integrations (BrowserStack). Entry style: `- [Name](link) - One sentence.`
- `marketing/kit/maestro-community.md` suggested asking the Maestro team about paid tools first and starting with an article PR. That's still the polite order.
- **Line to add:**

```
- [shotfleet](https://shotfleet.com) - Runs one English Maestro flow in every language an app has, on iOS and Android, and checks each screenshot's language (paid, free check).
```

- **PR title:** `Add shotfleet to Tools and Integrations`
- **PR body:**
  > Adds shotfleet, a Mac tool built on Maestro. It rewrites a flow's text selectors from the app's own translations so one English flow runs in every language, then checks the screenshots. I made it; it's paid with a free check command. Not affiliated with Maestro.

## 5. Lists that don't fit (checked, don't submit)

- **awesome-ios** (https://github.com/vsouza/awesome-ios): CONTRIBUTING.md (read 2026-10-06) requires 100+ stars, more than one contributor, an OSI open-source licence, Swift Package Manager support and an iOS 14+ deployment target. Freemium is allowed, but shotfleet is closed source and not a Swift package, so the PR would be closed.
- **awesome-android-ui** (https://github.com/wasabeef/awesome-android-ui): a list of Android UI/UX libraries (Compose, layouts, buttons, dialogs). A Mac screenshot tool isn't a UI library. Don't submit.
- **awesome-fastlane** and similar: I didn't check these. If you find one with a "tools that work with fastlane" section, the Awesome-ASO line works there too, after reading its rules.

## Before submitting

- Gate 1 in README.md (0.1.5 live) for the screengrab wording.
- Keep a log: directory, date, status, visits by `utm_source` after two weeks. (GitHub list links have no utm tag, on purpose: list maintainers often reject tracking links.)
