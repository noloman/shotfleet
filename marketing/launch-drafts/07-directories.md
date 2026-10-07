# Directory listings

Manu submits each one. Read each site's rules again the day you submit. The general text (50/150/300-character descriptions, tags, requirements) is in `marketing/kit/directories.md` "Master text"; below is what's new or different, per directory.

Updated short descriptions (the kit's ones predate 0.1.6):

- **150 characters:** `A Mac command-line tool that runs one English Maestro flow in every language your app has, on iOS and Android, and checks every screenshot.` (139)
- **300 characters:** `shotfleet runs one English Maestro flow in every language your app has, on iOS and Android at once, then checks each screenshot for the wrong language, blank screens and store sizes. check is free and also works on fastlane snapshot, screengrab and supply output. Apple silicon Macs.` (283)

---

## 1. AlternativeTo

- **Submit:** https://alternativeto.net, sign in, "Suggest new application" (FAQ: https://alternativeto.net/faq).
- **Rules (from the 2026-10-02 research, read first-hand then):** don't use the listing to advertise; don't reward upvotes (discounts for votes can push the app down); the free queue is "usually at least a few months"; an optional $5 priority review takes 1 to 2 business days. Paying the $5 is your decision, not mine.
- **Name:** shotfleet
- **Platforms:** Mac
- **License:** Freemium (the free tier does the check fully and captures 2 languages)
- **Short description:** the 150-character text above.
- **Long description:** the 300-character text, plus: `No frames, captions or store upload: use it with fastlane, ButterKit or AppScreens for those. Capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests (new in 0.1.6). Made by a solo developer.`
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

## 6. Console.dev (email)

- **Where:** email hello@console.dev from your address. No form, no account, no fee. Criteria: https://console.dev/selection-criteria (developer tools, self-service, CLI, docs; early tools must be pre 1.0, which 0.1.6 is). They don't do sponsored reviews, so offer nothing. This replaces the Console.dev email in `marketing/kit/directories.md` section 5, which predates 0.1.5.
- **Subject:** `shotfleet: localized store screenshots from one Maestro flow (free check, 0.1.6)`
- **Body:**
  > Hi,
  >
  > I'm Manu, a solo developer in the Netherlands, and shotfleet is the command-line tool I built after finding out my app's "localized" store screenshots were mostly English.
  >
  > You write one Maestro flow in English. shotfleet reads the translations compiled into your iOS or Android build, rewrites every text tap for each language, and runs the flow on several simulators and emulators at once. Then it reads every screenshot back and flags the wrong language, blank screens and sizes the stores won't take. On my M1 Pro, 18 languages x 4 screens took 9 minutes on iOS and 15 on Android (my app, Maestro 2.0.10).
  >
  > Why it might fit Console: `shotfleet check` is free with no account and works on screenshots from anything (fastlane snapshot, screengrab, supply, a folder per language). It has `--json` and plain exit codes for CI (0 ok, 1 problems, 2 setup error), and an MCP server (`shotfleet mcp`) that refuses a config's build and shell commands unless the call passes `hooks: true`. Docs: https://shotfleet.com/docs?utm_source=consoledev . Install is `brew install noloman/tap/shotfleet` or a one-line script; the build is signed and notarized. It's 0.1.6, so early.
  >
  > Limits, up front: Apple silicon Macs only. Capturing needs Maestro and Java 17+ and Android needs API 33+ emulators; on iOS it can also run your own XCUITest screenshot tests (new in 0.1.6, not run end to end yet). No frames, captions or upload. Flutter and React Native work from the translation files; I've run one real Flutter app and one Expo app, not more. Closed source. `doctor` asks shotfleet.com for the latest version number; your app and screenshots never leave your Mac.
  >
  > Price: the check is free and capturing is free for 2 languages. Every language is $29 for the first 100 buyers, then $49 once, with a year of updates and a 14-day refund.
  >
  > Site: https://shotfleet.com/?utm_source=consoledev
  >
  > Thanks for reading, and no worries if it's not a fit.
  > Manu
- **Before sending:** run `spctl -a -vv -t exec "$(which shotfleet)"`. If it doesn't say "Notarized Developer ID", delete "signed and notarized". Send once; no follow-up for 2 weeks.

## 7. Indie App Catalog (Non-App-Store form)

- **Where:** https://indieappcatalog.com/non-appstore/submit . Its App Store form (`/app/submit`) only takes a US App Store URL, so it doesn't fit shotfleet: use the Non-App-Store one.
- **Account (yours):** the form needs a login, which means accepting their terms. No fee is mentioned.
- **Fit, honestly:** the Non-App-Store section has about 20 apps, all Mac GUI apps. A command-line tool is a stretch and may be declined. Lowest priority; skip it if you're short on time.
- **Fields:** Name `shotfleet`. Platform macOS (Apple silicon). Price: Freemium, one-time licence ($29 for the first 100 buyers, then $49). Link `https://shotfleet.com/?utm_source=indieappcatalog`.
- **Description:**
  > I'm a solo developer, and I built shotfleet because my app's store screenshots in 18 languages were really the English ones in 18 folders. It's a Mac command-line tool: you write one Maestro flow in English, and it captures App Store and Google Play screenshots in every language your app has, then checks each one is really in that language. The check is free; capturing is free for 2 languages. Apple silicon Macs only.

## 8. Official MCP Registry

- **Where:** https://registry.modelcontextprotocol.io , published with `mcp-publisher` (`brew install mcp-publisher`, `mcp-publisher login github` as noloman, `mcp-publisher publish`). Free, in preview.
- **The catch:** its package types are npm, PyPI, NuGet, OCI images and MCPB bundles. A binary from shotfleet.com, a `curl | sh` or a Homebrew cask can't be a package entry, so it may refuse this file. If it does, stop: the only way round is an `.mcpb` bundle on a GitHub release, a bigger decision than a listing.
- **server.json** (description 96 characters; no `repository` field on purpose, `noloman/shotfleet-skills` is the plugin, not the server's source):
  ```json
  {
    "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
    "name": "io.github.noloman/shotfleet",
    "title": "shotfleet",
    "description": "Capture and check localized App Store and Google Play screenshots from one Maestro flow (macOS).",
    "version": "0.1.6",
    "websiteUrl": "https://shotfleet.com/docs#agents"
  }
  ```

## 9. Glama

- **Where:** https://glama.ai/mcp/servers ("Add Server").
- **Verdict: skip for now.** Glama lists servers from a GitHub repo with source and a LICENSE and scores them on a Docker build that answers introspection. A closed binary can't pass, so the listing would look worse than none. If section 8 is accepted, check in 2 weeks whether shotfleet shows up there by itself.
- If you still try, the first sentence: `An MCP server that lets your coding agent check store screenshots for the wrong language and start captures, on your Mac.`

---

## Before submitting

- Gate 1 in README.md (0.1.6 live) for the supply wording, and gate 3 (no Linux, Docker or Action in any text).
- Keep a log: directory, date, status, visits by `utm_source` after two weeks. (GitHub list links have no utm tag, on purpose: list maintainers often reject tracking links.)
