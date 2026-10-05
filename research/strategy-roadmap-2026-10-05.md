# Strategy roadmap: how to make shotfleet more sellable (2026-10-05)

Research and planning only. No code, README, site, `tests/claims.json` or packaging was changed. Written on branch `claude/strategy-roadmap` from main `44cd5f2` (PR #70 merged; CHANGELOG "Unreleased" holds PRs #68 to #70). Web facts were read on 2026-10-05 with a fetch and search tool; where only a search summary was available, the source says so.

Tags: **CONFIRMED** = read in the repo (file named) or on a primary page (URL, 2026-10-05). **INFERENCE** = my reasoning, with the test that would settle it. Money is USD. Not legal or tax advice.

Builds on, not repeated here: `research/sellable-audit.md`, the `limits-*-2026-10-05.md` notes, `research/0.1.2-plan.md`, `docs/device-wishlist.md`, `research/refund-process-2026-10-05.md`, `research/profit-plan-2026-10-03.md`, `research/pricing-2026-10.md`, `research/market-2026.md`, `STRATEGY.md`, `STATUS.md`, `LAUNCH.md`, `docs/handoff.md`, `marketing/kit/README.md`.

## 1. Summary: the five moves, in order

Where we are (CONFIRMED, STATUS.md and the live page): the product is on sale at $29 (first 100) then $49, there are 0 real sales, the owner is one developer, 0.1.1 is live, and 49 of 131 claim rows are not green (60 proven, 22 fixed, 27 evidence, 17 partial, 2 unverifiable, 1 untested, 2 removed). The product works on the owner's Mac. What is missing is **proof a stranger can see, a reason to try it for free, and people who know it exists**. Features are not the bottleneck (the 2026-10-03 profit plan said the same).

1. **Put proof on the page (weeks 1 to 2).** Record the 75 s demo (script exists), publish one real sample run (the 72-image grid, `index.html`, `check.json`, the planted failure), fix the one stale line on `/alternatives` (it still says "not run on a real Flutter or React Native app"), and publish the three guide drafts once their TO VERIFY items are ticked (the live installer now exists, so the open items of articles 1 and 2 can be run).
2. **Make `check` the front door.** One page and a three-line recipe: "check the screenshots you already have, free, in a minute, nothing uploaded". It needs no Maestro and no Java, so it is the lowest-friction path and every fastlane, asc or hand-made user can try it. Conversion happens at `run` for all languages and at `export`.
3. **Prove the two unknowns that decide refunds (weeks 1 to 3):** a clean-Mac cold run with 2 outside developers (this also gives the first real quotes) and a start test on an older macOS. Use design partners (a free key for an honest write-up, written permission for any quote). Add a Gumroad "Workflow" email after purchase (install line, three steps, "reply if stuck"): free, CONFIRMED to exist.
4. **Ship 0.1.2 as planned, trimmed:** pipeline A1 to A4 and A6, then B1 to B3, plus an update notice and one Gumroad update email per release. Move B4 (Android text from the UI tree) off the critical path. Then one distribution item: a tiny public GitHub Action and a Homebrew tap in the already existing, empty public repo `noloman/shotfleet-releases` (owner decision on public repos).
5. **Keep $29 then $49; test Team/CI demand at zero cost.** An email-only "Team and CI, $149 per repo" interest block (no checkout), a price decision at 25 sales or day 45, and the existing day-60 gate (2026-12-04): fewer than 15 sales means stop building and keep shotfleet as a free tool plus a reputation piece.

Order logic: 1 and 3 remove the reasons not to buy; 2 widens the top of the funnel at no cost; 4 protects buyers once they arrive; 5 avoids building Team features nobody asked for.

## 2. Evidence

### 2.1 Who buys, and why now

| Segment | Why they would pay | Evidence | Verdict |
|---|---|---|---|
| Indie iOS + Android developer, 10+ languages, on fastlane or Maestro | One flow for both platforms, no UI-test code, every image checked | fastlane issues with the same symptom: #11457 "Snapshot does not change language, all screenshots in simulators system language", #8895, #9043, #12917, #17823 (search results, https://github.com/fastlane/fastlane/issues/11457, 2026-10-05; titles CONFIRMED, bodies not read); the owner's own case (WOD Tracker, 18 languages) | **Core buyer** |
| Flutter, React Native, Expo, KMP teams that use Maestro | Maestro is their E2E tool; shotfleet reads their translation files | Maestro's community page lists a React Native sample, an Expo E2E guide and a fastlane plugin (https://docs.maestro.dev/extra-materials/community/community-projects, CONFIRMED); real runs: wger (Flutter), obytes (Expo), kotlinconf-app (Compose), HackerNewsKMP (STATUS.md row 10, CONFIRMED). INFERENCE: the largest group already inside Maestro | **Second buyer**, best content target |
| Freelancers and small agencies with client apps | Several apps, several languages, hours per release | Terms already allow "client and commercial work" per developer (`site/public/terms.html`, CONFIRMED); AppScreens sells an "Extended Licence for client work" in its $180/yr plan (https://appscreens.com/pricing, CONFIRMED) | Reachable by word of mouth, not ads |
| Localization teams, QA vendors | Language checks in CI | Lokalise and Crowdin match strings to screenshots, not store images (search, secondary) | Long sales cycle; skip now (profit plan agrees) |
| Developers using AI agents | A deterministic check an agent cannot do reliably | `shotfleet mcp` and the skill exist (README, CONFIRMED); ButterKit and StoreScreens also ship MCP (market-2026.md) | A discovery channel, not a segment that pays alone |

Why now:
- Localized screenshots matter. Vendor case studies report +33% (FiftyThree/Paper, https://splitmetrics.com/customers/fiftythree-localizes-screenshots-for-app-store/) to +36% conversion; these are vendor claims, not neutral data. One developer writes that non-English install rate was "roughly a third" of English before he localized (https://dev.to/rishbz/i-localized-my-app-store-screenshots-into-8-languages-heres-what-actually-moved-installs-3e4c, CONFIRMED as stated by one person).
- Pipelines keep breaking. Xcode 27 removed Simulator.app for Device Hub, and `open -a Simulator` scripts fail (https://github.com/expo/expo/issues/46671, https://github.com/anthropics/claude-code/issues/79991, titles CONFIRMED). `xcrun simctl io ... screenshot` is reported unchanged (search summary of https://charleswiltgen.github.io/Axiom/reference/device-control-ref; secondary). shotfleet's fixture passed on Xcode 27.0 with the iOS 26.4 runtime and one language ran on an iOS 27 runtime (STATUS.md row 9, CONFIRMED). iOS 27 went public on 2026-09-14 (search summary; secondary).
- Apple and Google automate listing text and upload, not capture or verification. Asset Library and an App Store Connect API for assets arrive this fall (https://developer.apple.com/wwdc26/guides/app-store/, CONFIRMED as announced; API details not read). INFERENCE: more automated text raises the odds of a translated listing over English screenshots, which `check` finds.
- Capture is getting crowded and cheap; the check is not. asc CLI (7.7k stars, MIT, release 5.10.0 on 2026-10-04) has `screenshots capture/frame/review/upload` and a `matrix` plan over devices and locales. Its docs name only iOS simulators and macOS apps, no Android, and nothing that checks the language inside an image (https://github.com/rudrankriyam/App-Store-Connect-CLI, https://docs.asccli.sh/commands/screenshots, https://api.github.com/repos/rorkai/App-Store-Connect-CLI/releases/latest; "no language check" is an absence in the pages I read, not proof). Marteso (iOS only) makes localized framed screenshots from one UI-test run and states nothing about verifying the language (https://www.marteso.com/blog/screenshot-pipeline-fastlane-alternative, 2026-06-02).
- The site is already findable. A search for "Maestro locale screenshots multiple languages fastlane snapshot alternative 2026" returned shotfleet.com (WebSearch, 2026-10-05, CONFIRMED). A Maestro-screenshots article by a large Flutter educator exists (https://codewithandrea.com/tips/automated-screenshot-generation-maestro/, 2025-03-17, says "for each device & language" by hand), so the topic has an audience and an author who could be written to. INFERENCE: intent queries are small, long-tail and not dominated.

### 2.2 Competitors and prices (re-read 2026-10-05)

| Tool | Price (CONFIRMED on its page unless noted) | What it does | Gap shotfleet fills |
|---|---|---|---|
| fastlane snapshot, screengrab | Free. Release 2.240.1 on 2026-09-15 (api.github.com/repos/fastlane/fastlane/releases/latest) | UI-test code per platform, run once per language | No UI-test code, one flow for both, checked output |
| asc CLI | Free, MIT | iOS capture matrix, frame, review, upload | Android; language and store-rule checks; no app changes |
| Maestro | Local CLI, Studio, Viewer, MCP free; Cloud $250 per device per month; no locale feature on the pricing page (https://maestro.dev/pricing) | The flow engine we build on | Per-language selectors, parallel runs; we are an add-on |
| ButterKit | Free (watermarked, 50 languages, ASC upload); Pro **$99 one-time**, 5 Macs, free updates, 14-day refund; Supporter $39/yr (https://butterkit.app/pricing). Search snippets showed $49 and $79 elsewhere; the vendor page says $99 | Frames, captions, AI translation, upload; the page does not say whether it re-captures per language | We feed it; it does not verify |
| AppScreens | Free (no localizations); Pro $99/yr (10 languages); Scale $180/yr (80+) (https://appscreens.com/pricing). Roundups quote $25 and $50 a month: stale or other billing | Web editor over uploaded screenshots, both stores | Not a capture tool |
| Marteso | Free starter for 2 apps; paid tiers not stated | iOS ASO platform with a GitHub-triggered screenshot pipeline | iOS only, no check stated |
| LocaShot, LocalizeShots, Screenshot Studio, ScreenshotWhale, Previewed | $5 to $30 a month or packs (market-2026.md; secondary) | AI redraw of designed screenshots | Redrawn text over an unchanged UI is the guideline 2.3.3 mismatch; none found that checks the real app |
| Applitools, App Percy | $199 to $667 a month (profit plan; secondary) | Visual regression | Not "right language"; too dear for indies |

Where shotfleet is different and defensible (INFERENCE from the table; tested by absence only):
1. the **language check of the real app's text** against its own compiled strings, plus store-rule linting;
2. **one flow on both platforms** with per-device-class sets (iPhone, iPad, phone, tablet);
3. it runs **locally**: no app or screenshot upload;
4. it **checks images made by any tool**.

Not defensible: capture itself (asc, agents, fastlane), framing, upload. The moat is depth and accuracy of the check plus real-app evidence: track record, not code that can be copied in a weekend. Main threat: asc CLI adds a language check (it already has `lint` for template markers in metadata).

### 2.3 Market size is unknown

Earlier notes estimated 1,000 to 2,200 reachable buyers and a year-one range of about $700 to $15,000, most likely about $3,000 (`research/profit-plan-2026-10-03.md`; stacked guesses, INFERENCE, "off by 2 to 3 times either way"). I could not improve it today: no source gives the share of apps with 10+ languages, and Reddit and Stack Overflow were unreachable. Treat the first 60 days as the measurement, not a forecast. CONFIRMED arithmetic (`research/gumroad-setup.md`, https://gumroad.com/pricing): net per sale is $24.46 at $29, $41.88 at $49 and $128.98 at $149; 100 founder sales are $2,446 net; 10 sales are about $245 net. A Discover-marketplace sale costs 30% flat instead of 10% + $0.50 (https://gumroad.com/pricing).

## 3. Funnel fixes

### 3.1 What stops a visitor from buying today (ranked by my estimate of lost sales)

1. **No proof from anyone but the owner.** The home page has no video, no quote, no third-party result (grep of `site/public/index.html`, CONFIRMED). The strongest assets (a bug found in WOD Tracker, "108 of 120 screenshots flagged" in another app) are good but self-reported.
2. **The free path is buried.** The page's hero has two links, "Buy shotfleet" and "See a real run"; the free `check` appears only in a small "Free at launch" block under the price (CONFIRMED). A visitor who is not ready to pay cannot try anything in one click. `check` needs no Maestro, no Java and no key, so it is the cheapest trial we have.
3. **Prerequisites and unmeasured first run.** Apple silicon, Xcode and a Debug simulator build, Maestro, Java 17+, Android SDK API 33+ (CONFIRMED, `site/public/llms.txt`). The first `doctor` took 62 to 68 s and looked hung; the whole path from `curl | sh` to a first screenshot has never been timed on a clean Mac, and "about 10 minutes" (claim C019) is unverifiable (CONFIRMED, `research/limits-first-run-2026-10-05.md`, `STATUS.md` gate 7).
4. **A visible contradiction.** `/alternatives` says "I haven't run it on a real Flutter or React Native app yet" while the home page and `llms.txt` say wger (Flutter) and the obytes template (Expo) ran end to end (CONFIRMED, both files read today). A careful reader will notice, and the Flutter/RN group is the second buyer segment.
5. **No way to stay in touch.** The home page has no email box and no `mailto:` (CONFIRMED); the waitlist ended at go-live. Every visitor who is not buying today is lost. INFERENCE: for a niche tool with 1 to 2% conversion this is most of the traffic.
6. **Price context.** The free comparison is fastlane (free) and asc CLI (free); the paid comparison is ButterKit at $99 once and AppScreens at $99 to $180 a year (CONFIRMED, 2.2). $29 or $49 is not out of line (INFERENCE), but the page never says why paying beats free for this buyer. An EU buyer pays the price plus VAT (a Dutch buyer saw $29 plus $6.09, STATUS.md, CONFIRMED).
7. **Checkout page polish.** STATUS.md lists no cover image or thumbnail, tipping on, "customers also bought" recommending Keysi, and the discount-code box set to Never (CONFIRMED). Gumroad says Discover is on by default for products with a category (https://help.gumroad.com/article/79-gumroad-discover, search summary; secondary), which changes the fee to 30% on sales that come through it.
8. **Looks unmaintained?** No changelog page, no "last release" on the site, no feed (the kit says `/feed.xml` does not exist; CONFIRMED in `marketing/kit/README.md`). 0.1.1 shipped on the day of 0.1.0, which is a good story that nobody can see.
9. **Install trust.** `curl -fsSL ... | sh` of a closed binary is a real objection. The program is notarized and the installer package is stapled (STATUS.md, CONFIRMED), but the page shows only the curl line.
10. **Older macOS.** 0.1.1 targets macOS 13+, but has not been started on any Mac older than 27 (CHANGELOG, CONFIRMED). The site says what was tested; keep that.

### 3.2 Specific, small, shippable items

Effort: XS under 2 h, S under 1 day, M 1 to 3 days. "Owner" means only the owner can do it. Site pages are frozen for me; these are proposals for the coordinator or the owner.

| # | Item | Why | Effort | Who | Touches |
|---|---|---|---|---|---|
| F1 | **Sample run page** (`/sample`): the real 72-image grid, `index.html` review report, a `check.json` excerpt, and the planted failure; downloadable zip | Proof anyone can open; also citable by AI search | S | Agent builds, owner picks images | Claims behind "18 x 4, 9 and 15 minutes", "108 of 120"; reuse the existing sources |
| F2 | **60 to 75 s demo video** from `marketing/kit/demo-video.md`, self-hosted (the CSP allows only `'self'`, so an embed from a video site would not load) | The single biggest trust item for a CLI | Owner 2 h | Owner records | None if it shows only real output |
| F3 | **"Check my screenshots" page** (`/check`) and a hero link: three commands, what it flags, one flagged example, "no account, nothing uploaded". Say only "fastlane snapshot, screengrab and plain folders" (the 0.1.1 CHANGELOG removed "any tool") | Free trial in one click; every free capture tool becomes a source | S | Agent | README "Check screenshots you already have", C048 |
| F4 | **Fix the stale line on `/alternatives`**, add an **asc CLI row** (7.7k stars, the most visible free alternative, absent from the table), re-date "checked" to 2026-10-05 (ButterKit $99 and AppScreens $99/$180 are unchanged since 2026-10-02, CONFIRMED) | Removes a contradiction, adds the competitor people will search for | XS | Agent | C031, C037, C013 wording |
| F5 | **Email box**: "release notes and Team/CI interest", reusing the existing worker signup (`site/worker.test.mjs` has signup tests, CONFIRMED); one question "what would you check in CI?" | Keeps non-buyers; measures Team demand for free | S | Agent builds; owner approves wording and re-reads the privacy page | Privacy page (waitlist and purge text) |
| F6 | **Cold test with 2 outside developers**, stopwatch, from the install line to the first PNG (kit exists in `docs/device-wishlist.md` row 2); then put the measured median on the page instead of "about 10 minutes" | Decides refunds and replaces an unprovable claim | Owner finds people, 1 h each | Owner | C019 |
| F7 | **Three design partners**: free key for an honest write-up; written permission before any quote (`marketing/kit/outreach.md`) | First third-party proof | Owner | Owner | None (no quote before permission) |
| F8 | **Changelog page and feed** from `CHANGELOG.md` (`/changelog`, `/feed.xml`) | Shows life, feeds newsletters that want an RSS link (the kit's newsletters file says so) | S | Agent | None |
| F9 | **Gumroad product polish**: cover image, thumbnail, three-line description with the free path, decide tipping, "customers also bought" and Discover category | A product page with no image looks abandoned | XS | Owner (Claude can drive Chrome and stops at MANU ONLY steps) | None |
| F10 | **Gumroad Workflow**: automatic email on purchase with the install line, the three steps (`activate`, `doctor`, `init`) and "reply to this email if stuck" (https://gumroad.com/help/article/131-using-workflows-to-send-automated-updates, search summary; CONFIRMED that Workflows send to buyers of a chosen product) | Fewer stuck buyers, fewer refunds, a support channel the buyer sees | XS | Owner | Terms text on support |
| F11 | **Install trust line** under the install command: "signed and notarized by Apple, SHA-256 published, runs locally", plus the `.pkg` link for people who do not pipe curl to sh | Answers objection 9 | XS | Agent | C057, C058 |
| F12 | **Download counter** (count requests to `/download/shotfleet-macos-arm64.tar.gz` in the Worker, no personal data) and GA key events `cta_click`, `pricing_view` | The product phones nothing home by design (privacy page, CONFIRMED), so downloads are the only free-user signal | S | Agent; owner re-reads privacy | Privacy page |
| F13 | **One real run of the README "In CI" recipe on GitHub** (README says it has not been; cost about a dollar of macOS minutes at $0.062 a minute, `docs/device-wishlist.md`), then publish the recipe as a copy-paste page | CI buyers are the team tier | XS plus owner OK to spend | Owner | README "In CI" |

Not recommended: a live "N of 100 left" counter (nothing true feeds it; the smoke test and the site tests fail the page if a counter number appears, LAUNCH.md, and MARKETING.md bans "only N left"), pop-ups, a chat widget, a paid trial. A free time-limited full trial is not needed: `check` plus 2 languages in `run` already is the trial.

<!-- PART3 -->
