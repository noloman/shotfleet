# Marketing kit: index

Owner of every item below: **Manu posts**. Claude prepared the text; nothing here has been posted, sent, submitted or paid. Written 2026-10-02. Domain: https://shotfleet.com (bought and live). Plan: ../../MARKETING.md. Research: ../../research/marketing-research.md. Claims source of truth: ../../tests/claims.json (`tools/check-claims.sh` must be green before anything goes out).

Rules that apply to every file: no price in build-in-public posts before the sale is live; $29 for the first 100 buyers is the only urgency and only while the live count is true; mention the price once per post; disclose that you built it; do not ask for upvotes; do not cross-post identical text; never claim Flutter or React Native on real apps, frames, captions, store upload, or any Maestro endorsement. Every link to our own site carries `?utm_source=<channel>` (the funnel counter reads only that tag).

**Links that 404 today:** the guide pages these files link to (`/fastlane-snapshot-screenshots-all-english`, `/maestro-one-flow-every-language`, `/the-button-nobody-could-reach`) exist only as drafts in `site/draft/guides/`; `/google-play-screenshots-every-language-emulators` is a planned article with no draft yet. Publish the guides (move them into `site/public/`, add them to `sitemap.xml`) before posting anything that links to them, or drop the link.

## Kit files (marketing/kit/)

| File | Where it is posted | Ready when | Owner |
|---|---|---|---|
| launch-day.md | Not posted; the hour-by-hour checklist for Day -1, Day 0, Day 1 and Days 2 to 7, with what to watch and what to do if something breaks | Read the day before launch | Manu |
| show-hn.md | https://news.ycombinator.com/submit (title, first comment, 15 prepared answers) | Sale live; installer works on a clean Apple silicon Mac; `shotfleet check` and a 2-language `run` work with no key; `spctl` run on the release binary (say "signed" until it prints Notarized Developer ID); claims check green; Manu free for the day | Manu posts |
| social.md | Mastodon (iosdev.space), Bluesky, X: two posts a week for 4 weeks, plus the launch-day thread | Week 1 and 2: assets exist (bug image exists; grid, terminal capture, ribbon need making). Launch thread: sale live and installer works | Manu posts |
| directories.md | AlternativeTo, DevHunt, Uneed, Peerlist, Console.dev (email), Indie App Catalog, Indie Hackers, Awesome-ASO (PR), awesome-maestro (PR, see maestro-community.md) | Each directory's rules re-read the same day; installer works on a clean Mac; Console.dev only after the free tier installs | Manu submits |
| maestro-community.md | Maestro Slack `#maestro-questions` (answers first, no link in weeks 1 and 2), awesome-maestro PR, Maestro docs community PR | Joined and rules read; for PRs: article 2 live with its TO VERIFY list done, paid-tools question answered | Manu posts |
| newsletters.md | iOS Dev Weekly and SwiftLee Weekly (via the iOS Dev Directory or form), Android Weekly, Kotlin Weekly, KMP Weekly: article links only | Article published and indexed, RSS feed `/feed.xml` exists, article's TO VERIFY done; days 2 to 7 of launch week | Manu submits |
| outreach.md | Email or thread reply: design partners (free licence for an honest write-up, written permission before any quote), Console.dev, Indie Dev Monday, the asc CLI recipe pitch | Installer works; a licence can be issued; asc recipe actually run before it is posted | Manu sends |
| reddit-ads.md | Reddit ads manager: the one $30 experiment, 2 variants, `utm_source=reddit-ads` | Sale live; counter live; a week of organic baseline from `site/signups.sh --visits`; ad policy read in the manager | Manu creates and pays |
| demo-video.md | Site, social, Show HN comment, newsletters: the 75-second script and shot list | A clean `run` recorded, a planted red-outline failure made | Manu records |

## Articles (marketing/articles/)

| File | Where it is posted | Ready when | Owner |
|---|---|---|---|
| 01-fastlane-snapshot-stuck-in-english.md | Our site at `/fastlane-snapshot-screenshots-all-english`; then iOS Dev Weekly and SwiftLee Weekly | TO VERIFY items 1 to 4 and 6 run or checked (item 2 needs the live installer); site footer links it | Manu publishes |
| 02-one-maestro-flow-every-locale.md | Our site at `/maestro-one-flow-every-language`; then Android Weekly, awesome-maestro, Maestro docs community | Every snippet run on the Maestro version named in the article (all ten TO VERIFY items); this is the article most likely to be quoted | Manu publishes |
| 03-the-button-nobody-could-reach.md | Our site at `/the-button-nobody-could-reach`; then Kotlin Weekly, social post 1.1, directories | Items 1, 2, 4, 5, 6 answered by Manu (his app and his facts) | Manu publishes |
| 04-ideas.md | Not posted: outlines for articles 4 to 8 | An outline is promoted to an article only after its commands have been run | Manu |

Also in marketing/ (older, outside this kit): launch-email.md (waitlist email, ready to send on Day 0), launch-posts-v2.md (r/iOSProgramming and r/androiddev single post is dropped by MARKETING.md; its Indie Hackers draft predates the sale and contains a claim we cannot back, see launch-day.md), done-for-you.md ($149 offer, only after a customer story), competitors.md, store-locales.md.

## Done in this pass

- Every `https://DOMAIN` placeholder in kit/ and articles/ is now https://shotfleet.com.
- utm tags added: `hn` (Show HN link and article link in the first comment), `consoledev`, `awesomeaso`, `awesomemaestro`, the four newsletter tags, and `indiedevmonday` in outreach.md; social.md says to replace `SOURCE` with `mastodon`, `bluesky` or `x` per network; directories.md lists one tag per directory.
- show-hn.md: complete, with 15 prepared answers (closed source and `curl | sh`, notarization, why not fastlane snapshot, Maestro locale flag, privacy, platforms and CI, requirements and Maestro version, Flutter and React Native, price, refund, how the check and OCR work, what it cannot do, app changes, reproducibility of 9 and 15 minutes, AI agents and asc). Notarization wording fixed: the 0.1.0 folder build was notarized and ran quarantined (DISTRIBUTION.md), but the exact release binary has not been through `spctl` (claims C058 is evidence only, and research/pricing-2026-10.md reports the checkout binary as unnotarized), so the files say "signed" until it has. The installer is 15 lines, not 20, and the file now says so.
- Ticked from the repo in the articles (search "TICKED"): article 1 items 5 and 7; article 2 items 1, 4, 5, 8 (code evidence, still to run, see below); article 3 items 3 (the 1080x1920 figure only) and 7.

## Still to verify by running

Before launch (Manu, on a clean Mac or user account unless noted):

1. `curl -fsSL https://shotfleet.com/install.sh | sh` installs the release; `shotfleet check` and `shotfleet run --locales en,de` work with no key (claims C057 untested; C048 partial). At research time `/download/VERSION` returned 404.
2. `spctl -a -vv -t exec $(which shotfleet)` on the release binary says Notarized Developer ID, and a quarantined copy opens without a prompt (C058; roadmap step "Build, sign, notarize").
3. Real purchase with FOUNDER29 and a refund, end to end, including `shotfleet activate`, all languages, deactivate, key stops validating after the refund (roadmap N2); FOUNDER29's use count in Gumroad moves with a real purchase (there is no counter on the page).
4. Gumroad handles VAT as merchant of record (C055 unverifiable until the live checkout shows it): the page says prices are before VAT where it applies; do not say "VAT included" anywhere.
5. GitHub Actions recipe for `check` run on GitHub once (README says it has not been); fix the README line that runs `python3 shotfleet.py` if it is still there.
6. Maestro version: state what you ran (2.0.10 on the dev Mac; 2.11.0 was current upstream in research) and whether the 18-language run was repeated on a newer one.
7. Network use: the answer in show-hn.md rests on reading the code, not on a packet capture; run Little Snitch or `nettop` once if you want to say more.
8. App with its own in-app language picker (C006 partial): untested; keep the caveat or test it.
9. Assets: grid image with a planted red outline (and alt text that says planted), terminal captures of the real `run` and `check` summaries, the real Turkish collision warning line, the ribbon image, the demo video.

Articles (each item is in that article's TO VERIFY list):

- Article 1: item 1 (`xcodebuild` command with a real scheme), item 2 (`shotfleet check` with the released installer), item 3 (reproduce causes 4 and 5, or soften), item 4 (`ls MyApp.app/*.lproj` with a String Catalog), item 5 (re-time on the final build, after a restart too), item 6 (re-open the issue links and fastlane docs).
- Article 2: all ten items run on a throwaway app and the version named: `${...}` inside launch `arguments` (1), env path in `takeScreenshot` (2), `maestro --device ... test -e` flag order (3), the Android `cmd locale set-app-locales` / `get-app-locales` run (4), `clearState` resets the Android app language, with and without (5), `runFlow` with `when: platform` (6), the `env:` header default beating `-e` on your Maestro version (7), the port 7001 trap with two devices (8), iOS permission alerts stay English (9, measured once), and the Maestro docs phrases re-read (10).
- Article 3: item 1 (public app name) decided 2026-10-03: WOD Tracker; items 2 (which of ja, ko, zh, ar were really stuck; only zh has an image), 3 (dp density), 4 (repo owner fine with the snippet), 5 (Skip really exits onboarding), 6 (did a shipped release have the bug), 7 (no run log is kept), 8 (free repro steps), 9 (generic Compose advice).
- Outreach: the asc recipe command and output (run it, paste it); the Indie Dev Monday form and the asc repo's current contribution notes.
- Reddit ads: Reddit's ad policy and the character limits in the manager.
