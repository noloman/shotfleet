# Directory submissions: ready-to-paste text

Owner: Manu submits, one at a time, after reading each site's current rules. Nothing here has been submitted. Written 2026-10-02.
URL check on 2026-10-02 (HTTP status from a script, so a 403 means the site blocks scripts, not that it is down): see the "URL check" column. Rules come from research/marketing-research.md section 2 (V = read first-hand there).

## Master text (reuse, do not rewrite per site)

Product name: shotfleet
Tagline (53 characters): One English Maestro flow, every app language, checked

50 characters: Localized store screenshots from one Maestro flow.

150 characters: A Mac command line tool that runs one English Maestro flow in every language your app ships, on iOS and Android, and checks every screenshot it makes.

300 characters: shotfleet takes one English Maestro flow and runs it in every language your app ships, in parallel on iOS simulators and Android emulators. It rewrites taps from the app's own translations, then checks each screenshot: wrong language, copies, missing screens, store sizes. Free: check, 2 languages.

Pricing line: Freemium, one-time licence
Pricing detail (use only where a field allows it): `shotfleet check` is free, and `run` is free for 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once per developer, a year of updates, 14-day refund.

Category (pick the closest the site offers): Developer Tools. Second choice: Localization, or Automation.
Tags: maestro, localization, app store screenshots, google play screenshots, fastlane, ios, android, cli, macos, testing

Requirements (state them wherever there is a text field): macOS on an Apple silicon Mac (the installer refuses Intel Macs). Xcode for iOS, the Android SDK with API 33+ emulators for Android, Maestro 2.x, Java 17+. A Maestro flow you write (it gets most of the way from `shotfleet init`). Not included: frames, captions, store upload (fastlane uploads).

Links: homepage https://DOMAIN/ ; article https://DOMAIN/the-button-nobody-could-reach . Add `?utm_source=DIRECTORY` (for example `alternativeto`, `devhunt`, `uneed`, `peerlist`, `indiehackers`, `indieappcatalog`) so the funnel counter can split visits.

Logo and screenshots: use the review grid (red outline version) and the terminal capture from marketing/kit/social.md, plus `site/public/og.jpg`. Do not upload anything that shows another company's logo.

Rules that apply to all: do not ask anyone for upvotes or comments, do not use discounts to buy votes, do not give friends a script. Disclose that you made it, in your own words, wherever there is a comment field.

---

## Summary table

| Directory | Where to submit | URL check | Ready when | Cost and lead time |
|---|---|---|---|---|
| AlternativeTo | https://alternativeto.net (account, then "Suggest new application"; FAQ https://alternativeto.net/faq) | 403 to scripts; page exists per research (V) | Site live on the real domain; the free tier installs; Manu has a verified email account | Free, "usually at least a few months" in the backlog (V); optional $5 one-time priority review in 1 to 2 business days (V) |
| DevHunt | https://devhunt.org (GitHub login, then submit a tool; the `/submit` path returned 404, so use the button on the home page) | home 200, `/submit` 404 | Site live on the domain; free tier installs; a demo or repo link exists (the site's demo video counts) | Free; weekly launches; banner ads cost $149 per week (V), not needed |
| Uneed | https://www.uneed.best/submit-a-tool | 200 | Site live on the domain, in English; launch assets ready | Free waiting line with an automatic date; $29.99 to pick the date (S). A free launch needs a score of 10 to stay published and 20 to keep the dofollow link (S) |
| Peerlist Launchpad | https://peerlist.io (Launchpad, from a verified profile) | `/launchpad` 403 to scripts | Verified Peerlist profile; site live; launch week chosen (the window opens Mondays and runs the week, S) | Free, one launch per week (S) |
| Console.dev | Email hello@console.dev (criteria https://console.dev/selection-criteria) | 200 | Free tier installs on a clean Mac; docs page exists; real domain | Free; no sponsored reviews; editorial review about 1 to 2 weeks (S) |
| Indie App Catalog | https://indieappcatalog.com/app/submit (has a "Non-App Store" section, V) | 200 | Site live on the domain; install works | Cost and criteria not shown (U); read the form first |
| Indie Hackers | https://www.indiehackers.com/products (free account, "Add a Product") | 200 | Site live on the domain | Free; page is immediate (S) |
| Awesome-ASO | PR to https://github.com/rafaecheve/Awesome-ASO (default branch `master`; edit README, "Tools" section) | 200 | Site live; the tool installs; read CONTRIBUTING.md first | Free; PR-based, unknown time |
| awesome-maestro | PR to https://github.com/ludovicobesana/awesome-maestro | 200 | Article 2 live and its TO VERIFY ticked; see marketing/kit/maestro-community.md for the order (article first, tool later) | Free; PR-based, unknown time |

Do not submit to: awesome-ios (its CONTRIBUTING.md requires an open-source licence, 100+ stars and "not a paid product"; the PR would be closed), BetaList (paid), SaaSHub and Slant before the real domain exists (they reject free subdomains and waitlist pages), Capterra and G2 (not the buyer), Product Hunt for now (low priority, MARKETING.md).

---

## 1. AlternativeTo

- Submit: create an account, verify the email, then "Suggest new application" (FAQ: https://alternativeto.net/faq).
- Fields to fill: name; platforms: Mac (the site may list only Mac); license: Commercial or Freemium. Choose Freemium only if the free tier performs the main purpose. Our free tier does `check` fully and `run` for 2 languages; Manu decides, and the honest default is Freemium with the pricing line above.
- Short description (their field): use the 150-character text.
- Long description: use the 300-character text plus: "Requires an Apple silicon Mac, Maestro 2.x and Java 17+. No frames, captions or store upload."
- Tags: use the master tags.
- "Alternative to": fastlane only (screenshot capture). Do not list it as an alternative to framing tools (ButterKit, AppScreens): it does not make frames or captions.
- Rules (V): do not use the profile to advertise; do not incentivize upvotes (discounts for upvotes can lower the app in ranking); expect a long queue. Do not pay for the $5 priority until the site and install are final; once it is, the $5 is cheap.
- Link has no `utm_source` effect on rank; keep `?utm_source=alternativeto` on the homepage link only.

## 2. DevHunt

- Submit: GitHub login on https://devhunt.org, then the submit button. Launches run weekly.
- Name: shotfleet. Tagline: use the 53-character tagline (their limit may differ; shorten to the 50-character text if needed).
- Description: the 150-character text, then the 300-character text in the long field.
- Category: Developer Tools. Pricing: Freemium, one-time licence.
- Make-it-easy: DevHunt wants a working demo or repo (S). The demo is the free tier: `shotfleet check`, installable with the one-line installer. Do not submit before the installer works.
- Do not ask for upvotes; ask people to try the free command if they want.

## 3. Uneed

- Submit: https://www.uneed.best/submit-a-tool (landing page, English).
- Tagline: the 53-character tagline. Description: the 150-character text. Long description: the 300-character text.
- Pricing: Freemium, one-time licence. Category: Developer Tools.
- Rules (S): a free launch is published in a waiting line with an automatic date; it needs a score of 10 to stay published and 20 to keep the dofollow link. Do not pay for a date until the free launch has shown anything.

## 4. Peerlist Launchpad

- Submit: Launchpad on https://peerlist.io from a verified profile; the launch window opens Mondays and runs the week (S).
- Tagline: the 53-character tagline. Description: 150 characters; long: 300 characters.
- Category: Developer Tools. Tags: the master tags.
- Make the first comment yourself: the unreachable Next button story in 3 sentences, with the article link. Do not ask the audience to upvote.

## 5. Console.dev (email)

To: hello@console.dev
Subject: shotfleet: localized store screenshots from one Maestro flow (free tier)

> Hi,
>
> I am Manu, a solo developer in the Netherlands. I built shotfleet for my own app, which ships in 18 languages, and I am writing because it looks like it fits your selection criteria: a command line tool you can try without signing up.
>
> What it does: it takes one English Maestro flow and runs it in every language your app ships, in parallel on iOS simulators and Android emulators. It reads the translations compiled into the build, rewrites each tap for every language, then checks each screenshot (wrong language, copies, missing screens, store size rules). 18 languages by 4 screens (72 screenshots) took 9 minutes on iOS and 15 on Android on one Mac, with four parallel devices. That is one app and Maestro 2.0.10.
>
> Why it may be interesting: `shotfleet check` is free and works on screenshots made by anything (fastlane snapshot, by hand). `run` is free for 2 languages; a licence unlocks every language and export. It is closed source, signed and notarized, with `--json` output and stable exit codes (0 ok, 1 problems found, 2 setup error) for CI, an MCP server for agents, and docs in the README. Install is one command.
>
> Limits, up front: Apple silicon Mac only; needs Xcode, Maestro 2.x and Java 17+, and Android needs API 33+ emulators. No frames, captions or store upload. Flutter and React Native work from translation files, but I have not yet run a real Flutter or React Native app.
>
> Price: $29 for the first 100 buyers, then $49 once per developer, with a 14-day refund.
>
> Site: https://DOMAIN/ . A short story of the first bug it showed me: https://DOMAIN/the-button-nobody-could-reach
>
> Thanks for reading, and no problem if it is not a fit.
> Manu

Send when: free tier installs on a clean Mac (not before); real domain; `spctl -a -vv -t exec` on the release binary says "Notarized Developer ID" (the email says signed and notarized; research found an older binary that did not, claims C058, so check the release you ship or delete those words). Send once. Do not follow up before two weeks. Console.dev says no sponsored reviews; do not offer payment or a free licence in return for coverage.

## 6. Indie App Catalog

- Submit: https://indieappcatalog.com/app/submit. Pick the "Non-App Store" section if it is offered (it is a Mac command line tool distributed from our site).
- Name, tagline and descriptions: master text. Platforms: macOS (Apple silicon).
- Price: Freemium, one-time licence ($29 for the first 100 buyers, then $49).
- Requirements field (or in the description): "Apple silicon Mac, Maestro 2.x, Java 17+."
- Read the form: cost and criteria were not visible when researched (U).

## 7. Indie Hackers (product page)

- Submit: https://www.indiehackers.com/products, account, "Add a Product".
- Name: shotfleet. Tagline: the 53-character tagline.
- Short description: the 150-character text. Full description: the 300-character text, then two lines: "I built it for my own 18-language app. The first full Android run found an onboarding page whose Next button was unreachable in Japanese, Korean, Chinese and Arabic on a small phone." and "Apple silicon Mac only; needs Maestro 2.x and Java 17+; free to check, free for 2 languages in run; $29 for the first 100 buyers, then $49 once."
- Revenue and other fields: leave blank rather than guess. Do not publish revenue until there is some.
- The story post for Indie Hackers is a separate item (marketing/launch-posts-v2.md owns it); post it after the product page exists. Posting rules for Indie Hackers were not found (U): read them.

## 8. Awesome-ASO (PR)

Repo: https://github.com/rafaecheve/Awesome-ASO. README says: to contribute, edit README.md, use the pencil icon and "Propose file change", and follow CONTRIBUTING.md. The Tools section already lists commercial screenshot tools. Entries are `N. [Name](url) - description.` in alphabetical-ish order.

Entry (place it alphabetically in Tools, between "Screenproof" and "Shotlingo"; the list's numbering is uneven, so use `1.` as the other entries do):

```
1. [shotfleet](https://DOMAIN) - Mac command line tool that captures App Store and Google Play screenshots in every language from one English Maestro flow and checks each image for wrong language, copies and missing screens. Free to check.
```

PR title: `Add shotfleet to Tools`

PR body:

> Adds one entry to Tools. shotfleet captures localized store screenshots from one Maestro flow and checks each image against the app's own strings (wrong language, copies, missing screens, store sizes). I made it. It is closed source, Apple silicon Mac only, free to check and free for 2 languages, paid beyond that. Happy to reword or drop it if a command line tool is out of scope for the list.

Ready when: site live on the domain and the tool installs. If the list's numbering is renumbered by hand, follow what CONTRIBUTING.md says rather than this note.

## 9. awesome-maestro (PR)

See marketing/kit/maestro-community.md for the order, entry text and disclosure. Short version: article PR first (`## Articles`), tool PR only after the Maestro team answers the paid-tools question. The entry format is `- [Name](url) - One sentence.` and the list already includes a paid device cloud.

---

## Before you submit anything

1. Re-open the directory's rules page the same day; the rules above are from a research pass on 2026-10-02 and some were read through a summary (S, not V).
2. Check the site loads on the domain, the installer works on a clean Mac (a `/download/VERSION` 404 on the old workers.dev address means no release was published at research time), and the price line says $29 for the first 100 buyers.
3. Keep a log: directory, date submitted, status, the visit count by `utm_source` after two weeks.
