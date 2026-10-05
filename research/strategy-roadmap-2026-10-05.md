# Strategy roadmap: how to make shotfleet more sellable (2026-10-05)

Research and planning only. No code, README, site, `tests/claims.json` or packaging was changed. Written on branch `claude/strategy-roadmap` from main `44cd5f2` (PR #70 merged; CHANGELOG "Unreleased" holds PRs #68 to #70). Web facts were read on 2026-10-05 with a fetch and search tool; where only a search summary was available, the source says so.

Tags: **CONFIRMED** = read in the repo (file named) or on a primary page (URL, 2026-10-05). **INFERENCE** = my reasoning, with the test that would settle it. Money is USD. Not legal or tax advice.

Builds on, not repeated here: `research/sellable-audit.md`, the `limits-*-2026-10-05.md` notes, `research/0.1.2-plan.md`, `docs/device-wishlist.md`, `research/refund-process-2026-10-05.md`, `research/profit-plan-2026-10-03.md`, `research/pricing-2026-10.md`, `research/market-2026.md`, `STRATEGY.md`, `STATUS.md`, `LAUNCH.md`, `docs/handoff.md`, `marketing/kit/README.md`.

## 1. Summary: the five moves, in order

Where we are (CONFIRMED, STATUS.md and the live page): the product is on sale at $29 (first 100) then $49, there are 0 real sales, the owner is one developer, 0.1.1 is live, and 49 of 131 claim rows are not green (60 proven, 22 fixed, 27 evidence, 17 partial, 2 unverifiable, 1 untested, 2 removed). The product works on the owner's Mac. What is missing is **proof a stranger can see, a reason to try it for free, and people who know it exists**. Features are not the bottleneck (the 2026-10-03 profit plan said the same).

1. **Put proof on the page (weeks 1 to 2).** Record the 75 s demo (script exists), publish one real sample run (the 72-image grid, `index.html`, `check.json`, the planted failure), fix the one stale line on `/alternatives` (it still says "not run on a real Flutter or React Native app"), and publish the three guide drafts once their TO VERIFY items are ticked (the live installer now exists, so articles 1 and 2 can be closed).
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

<!-- PART2 -->
