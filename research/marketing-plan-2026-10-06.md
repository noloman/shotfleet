# shotfleet marketing plan (2026-10-06)

Research and planning only. Nothing was posted, published, submitted, emailed or paid for, and no account was created. Manu posts
everything himself. Branch `claude/marketing-plan` from `origin/main` (a0e39c4, the 0.1.5 release commit).

**Tags.** **[R]** read in the repo or the coordinator-state file (file named). **[W]** read on the web today (URL given, in the text or
under Sources). **INFERENCE** = my estimate, with what would settle it. Money is USD unless marked.

**What this note builds on, and does not repeat.** `MARKETING.md` (2026-10-02 plan), `STRATEGY.md`, `research/marketing-research.md`
(channel rules, newsletters, directories, HN base rates), `research/strategy-roadmap-2026-10-05.md` (30/60/90 days, owner decisions),
`research/reach-roadmap-2026-10-06.md` (branch `claude/reach-roadmap`), `research/seo-audit-2026-10-06.md` (branch
`claude/seo-improvements`), `research/site-claims-audit-2026-10-06.md`, `research/beyond-maestro-2026-10-06.md`,
`research/llm-integration-2026-10-05.md`, `research/ga4-investigation-2026-10-05.md`, and `marketing/kit/` (Show HN with 15 answers,
launch-day hour plan, directories, newsletters, Reddit ads, Maestro community, outreach, social). A parallel agent is writing paste-ready
posts on `claude/launch-drafts` (`marketing/launch-drafts/`). This note decides **what to do, in what order, and why**; the kit and the
drafts hold the words.

---

## 0. Where things stand today (2026-10-06)

| Fact | Source |
|---|---|
| On sale since 2026-10-05 at $49, $29 for the first 100 (FOUNDER29, applied automatically), 14-day refund, Gumroad | [R] LAUNCH.md; [W] Gumroad page JSON: `price 49.0`, `FOUNDER29` $20 off, `refund_policy` 14 days |
| **0 sales.** Gumroad showed no sales on 2026-10-05 15:48; the product page shows 0 ratings | [R] coordinator-state.md; [W] Gumroad page `ratings.count 0` |
| Gumroad creator profile has the **default avatar** and is not verified | [W] Gumroad page JSON (`gumroad-default-avatar-5.png`, `is_verified false`) |
| Live version 0.1.4; 0.1.5 built and on main, waiting for its device gate; 0.1.6 candidate on `claude/post-015-candidate` adds **XCUITest capture** ("Use your existing XCUITest screenshot tests"), fastlane supply names, failure details | [W] https://shotfleet.com/download/VERSION = 0.1.4; [R] CHANGELOG.md on main and on the candidate |
| Site traffic before any announcement: 44 page views in 3 days, all `direct`, mostly Manu and test runs. GA4 works but has almost no data | [R] research/ga4-investigation-2026-10-05.md |
| Brand search for "shotfleet screenshots" returns nothing; Search Console and Bing not set up | [R] research/seo-audit-2026-10-06.md finding 1 |
| Not announced anywhere: no Show HN, no Reddit post (HN search for "shotfleet" finds nothing about it) | [W] hn.algolia.com API |
| Proof assets that exist: 9 captioned demo clips (`site/public/media/demo/c1..c9`), the 18 x 4 WOD Tracker grid, the unreachable-Next-button story, the AnywhereRoles showcase (on the candidate branch), 3 guide drafts rendered, 2 more drafted | [R] |
| **Keysi** (Manu's Mac app) has Show HN planned for **Tue 2026-10-13** and Product Hunt for **Wed 2026-10-14** | [R] scheduled task `keysi-launch-day` |
| The **Go/No-Go task on 2026-10-15** still counts *waitlist signups* on the old `shotfleet.manulorenzop.workers.dev` URL and applies PLAN.md's "30 signups or 5 pre-orders" rule. The waitlist is gone since the sale opened, and STRATEGY.md replaced that rule with "50 sales in 60 days" | [R] `~/.claude/scheduled-tasks/shotfleet-go-no-go/SKILL.md`, PLAN.md, STRATEGY.md |

So the product is ready to sell, and nobody knows it exists. The plan below is about the first strangers, not about scale.

---

## 1. Positioning and ICP

### 1.1 Who has the pain most (ranked)

| # | Segment | Why they feel it | Fit with what is proven | Verdict |
|---|---|---|---|---|
| 1 | **Indie and small-team native iOS + Android apps in 5+ languages** | Every release multiplies screenshots: languages x devices x screens. Each language needs the app really in that language, on both stores | Native strings, both platforms, 18 languages measured on Manu's apps [R site] | **Core buyer** |
| 2 | **Teams already on Maestro** (native, KMP, Flutter, React Native/Expo) | Maestro flows find buttons by their text, so an English flow breaks in German. Maestro's docs: you "cannot" set the locale with `maestro test` ([W] https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales) | Exact gap shotfleet fills; Flutter and Expo each run on one real app only [R] | **Best fit per person reached**, small group |
| 3 | **fastlane snapshot / screengrab users** | Long history of "it stays in English" issues (1.2); output is rarely checked | Free `check` works on snapshot and screengrab output since 0.1.5; 0.1.6 captures from existing XCUITest tests [R] | **Biggest group, enters through the free `check`**, converts later (or never) |
| 4 | **Freelancers and small agencies** with several client apps | Same pain times N apps; per-release hours | Licence allows client work, unlimited apps [R terms] | Word of mouth, not ads |
| 5 | Teams using AI caption/translation tools (ButterKit, Lokalshot, AppScreens AI captions) | Those tools translate the **caption** over one screenshot; the app under it can stay English | `check` finds exactly that: 103 of 127 old AnywhereRoles Play screenshots were translated captions over an English app [R showcase on candidate branch]; 108 of 120 Remoti listing images [R site home, claims C103-area row] | **Sharpest story**, a complement to those tools, not an attack |
| - | Localization vendors, enterprise QA | Long sales cycle | | Skip |

Fastlane's audience is about 2.6 times Maestro's by stars: fastlane 42,205, Maestro 15,958 ([W] GitHub API today).

### 1.2 Their words for the pain (real phrasing, for headlines and SEO)

From fastlane's issue tracker ([W] GitHub search API, titles exact):

- "snapshot always runs in english (does not switch language)" (#9043, https://github.com/fastlane/fastlane/issues/9043)
- "Snapshot does not change language, all screenshots in simulators system language" (#11457, https://github.com/fastlane/fastlane/issues/11457). A commenter added a label for `-AppleLanguages` and it "always stays at en-US".
- "[Regression] snapshot is not changing language of Simulator" (#8895), "Snapshot tests only switch languages when run manually" (#12917)
- "Screengrab locale not changing" (#11696), "Screengrab places screenshots into wrong locale directory" (#14584, 18 comments), "[screengrab] Locales not getting changed -- Kotlin LocaleTestRule" (#14307)

From Maestro ([W]):

- "Launch the app with a specific locale" (#393, https://github.com/mobile-dev-inc/Maestro/issues/393): the asker needs runs "in English, German, etc."
- "start-device --device-locale it_IT on android changes locale on wrong device" (#2209)
- "iOS systems permission helper only dismisses pop ups for English language simulator configurations" (#2654)
- A developer found his "Portuguese" screenshots were English because a flow's `env:` default beat the command line ([R] marketing-research.md, https://github.com/RogerioDoCarmo/morse_app/pull/216).

From writers: Code With Andrea frames the job as replacing manual screenshots "for each device & language" ([W] https://codewithandrea.com/tips/automated-screenshot-generation-maestro/). The arithmetic people quote is "20 languages x 4 devices x 5 screenshots = 400 screenshots" (search summary of iMore, https://imore.com/how-easily-automatically-take-multi-language-screen-shots-app-store-submissions).

Words to reuse: **"stuck in English"**, **"doesn't switch language"**, **"every language, every device"**, **"wrong locale folder"**,
**"translated captions over an English app"**. Words to avoid: "AI", "magic", "catches all localization bugs".

Note: Reddit pages could not be read today (Reddit blocks this machine's fetches with 403, and Chrome was not connected). Reddit phrasing
and rules below come from secondary summaries. Read each sidebar live before posting.

### 1.3 Jobs to be done

1. "When I ship a release in N languages, get me correct store screenshots for both stores without writing UI-test code twice."
2. "Before I upload, tell me which languages are wrong, so a German listing never shows an English app." (`check`, free)
3. "When I add a language, don't make me add work." (one flow, rewritten per language)
4. "Keep my existing setup." (fastlane folders via `export`; existing XCUITest tests from 0.1.6; `check` on anything)

### 1.4 Objections and the honest answer (each answer exists on the site or in `marketing/kit/show-hn.md`)

| Objection | Answer |
|---|---|
| **Price: fastlane is free** | It is, and if your UI tests already run in every language, keep them and run the free `check` on their output. shotfleet is for no test code, one flow for both platforms, and checked output. $29 now ($49 later), once, unlimited apps, 14-day refund; free tier: `check` plus 2 languages per `run`. |
| **Mac only, Apple silicon only** | iOS simulators need a Mac anyway. `check` runs on Linux and in CI through the Docker image and GitHub Action in 0.1.5 [R CHANGELOG]. No Intel build (say so first). |
| **Maestro only** | Only `run` needs Maestro. `check` works on fastlane snapshot and screengrab output. From 0.1.6, `run` also captures from existing XCUITest tests (iOS) [R candidate CHANGELOG]. |
| **Trust: closed source, `curl \| sh`, solo developer** | Signed and notarized; Homebrew cask in `noloman/homebrew-tap`; checksum published; nothing is uploaded (network calls are an allow-list pinned by a test, claims row G1). 14-day refund. Answer from show-hn.md answer 1, never argue. |
| **"Does it work on my app?"** | Proven on Manu's own apps; Flutter and Expo on one real app each. Say exactly that. The free tier is the test. |
| **"Writing the flow is work"** | True, and the showcase says the Android flow took several failed runs [R candidate]. `init` writes a starter flow; one flow replaces one per platform. |

### 1.5 One-line positioning

> **Store screenshots of your app really in every language, checked. One English Maestro flow (or, from 0.1.6, your XCUITest tests) captures iOS and Android in every language your app has, and the free `check` catches screenshots where the app is still in English.**

Short form for titles: **"Localized App Store and Google Play screenshots from one English flow, checked."**

### 1.6 Three message pillars (all backed by facts already on the site or the candidate site)

1. **Really localized, not just captioned.** A translated caption over an English app is not a localized screenshot. Proof: `check` flagged
   108 of 120 store screenshots of one of Manu's apps (home page stat); on the AnywhereRoles Play set, 103 of 127 problems were translated
   captions over an English app (showcase, candidate branch, ships with 0.1.6 site). The WOD Tracker run found an unreachable Next button in
   ja, ko, zh, ar that English hid.
2. **One flow, both stores, no app changes.** 18 languages x 4 screens: 9 minutes on iOS, 15 on Android, on an M1 Pro with Maestro 2.0.10;
   no code added to the app; exports into fastlane's folders.
3. **The check is free and works on what you already have.** fastlane snapshot and screengrab output, hand-made folders, Linux CI via Docker.
   On a real fastlane snapshot set it found a German listing whose app was English (alternatives page).

Every public sentence must match a green row in `tests/claims.json`; run `tools/check-claims.sh` before posting (MARKETING.md rule).

---

## 2. Competitive landscape (checked 2026-10-06)

### 2.1 What they say and charge

| Tool | What it does | Price (vendor page unless marked) | Their headline / angle | Their channels |
|---|---|---|---|---|
| **fastlane snapshot / screengrab** | Captures via UI-test code, one platform each, once per language | Free, MIT | The default for 10 years | GitHub (42k stars), docs, Discussions (1,541 threads) |
| **asc CLI** (rorkai/App-Store-Connect-CLI) | iOS capture matrix, frame, review, upload, agent skills | Free, MIT | Agent-friendly App Store Connect | GitHub (7,679 stars), agent-skill directories |
| **simshot** (FreakLee/simshot) | Batch simulator screenshots per language, iOS | Free | "No UI test target" | GitHub only (0 stars today) |
| **StoreScreens** | XCUITest capture + agent skill, iOS/Mac/Watch | Free | | GitHub (27 stars) |
| **ButterKit** | Mac app: frames, captions, 50-language on-device translation, ASC upload | Free (watermark); Pro $99 once (5 Macs); Supporter $39/yr ([W] https://butterkit.app/pricing) | "Start free. Own it, or support it." | Heavy SEO (~175 URLs [R]), Discord |
| **AppScreens** | Web editor over uploaded screenshots, both stores, AI captions | Free (default language only); Pro $99/yr (10 languages); Scale $180/yr (80+, client work) ([W] https://appscreens.com/pricing) | "Simple pricing for faster app releases" | Blog (~67 URLs [R]), comparison pages incl. vs fastlane |
| **AppScreenshotStudio** | AI-generated designs by chat, device frames, multi-language | Starter $4.99/mo, Growth $9.99/mo, Pro $19.99/mo, annual; API + MCP on Growth ([W] https://appscreenshotstudio.com/pricing) | "A designer gives you one set and no way to know if it works" | Programmatic SEO: many `/compare/*` pages, a glossary, free ASO tools |
| **Screenshots Pro** (screenshots.pro) | Browser template editor over uploaded screenshots | Free; Standard $19/mo; Extended $49/mo; localization only on paid ([W] https://screenshots.pro/) | "No account needed" | Free tool as SEO magnet |
| Lokalshot, Shotlingo, AppShotter, Screenhance, LocaShot | AI-translate captions over your screenshots | $5-30/mo or packs ([R] market-2026.md; secondary) | "Every language in one click" | Product Hunt, Show HN (LocaShot: 3 points, 2026-03-09 [W] HN Algolia) |
| Maestro / Maestro Cloud | The flow engine shotfleet builds on | CLI free; Cloud $250 per device per month ([R] strategy note) | | Slack, Discord, docs, HN (185 points in 2025) |

### 2.2 Where shotfleet wins, honestly

- **It is the only one found that captures the running app per language on both platforms from one flow and then checks the language
  inside each image.** The design tools work on screenshots you give them; the free capture tools don't check.
- **Complement, not rival, to the caption tools.** Their output (one capture, many translated captions) is the failure `check` finds.
  Message: "Make the frames with ButterKit or AppScreens. Check that the app under the caption is in the right language."
- **One-time $29/$49** against $99-$180 a year for the design tools.
- **Free `check` reaches fastlane's larger audience** without asking them to change tools.

### 2.3 Where shotfleet loses, honestly

- No frames, captions or upload: buyers who want marketing images pick ButterKit or AppScreens.
- Apple silicon Macs only, a CLI only, needs Maestro + Java 17 for `run` (until 0.1.6 for XCUITest on iOS).
- Price against free fastlane for teams whose UI tests already work.
- Thin outside proof: all runs are on Manu's apps; 0 reviews, 0 sales; a Gumroad profile with the default avatar.
- Closed source plus `curl | sh` draws HN skepticism.
- Run times are Manu's Mac; loaded Macs drop to 2 simulators and need retries (showcase says so).

### 2.4 What to copy from their channels

- AppScreenshotStudio and ButterKit win search with many "X vs Y" and "X alternative" pages. shotfleet has one `/alternatives` page. Add
  honest per-tool pages later (`/alternatives/fastlane-snapshot`, `/alternatives/butterkit`), only from facts already checked.
- Screenshots Pro uses a free no-account tool as a magnet. shotfleet's equivalent is the free `check` (and later the client-side web
  checker in the reach roadmap).

---

## 3. Channels, ranked by expected buyers per hour of Manu's time

**How the numbers are made (all INFERENCE).** Visit-to-sale of 1% for well-targeted developer traffic (range 0.5 to 2%; the profit plan's
base case is about 2%: 10 buyers on 500 visits). "Hours" are Manu's hours, including replies. Agents draft everything. The first real week
of data replaces these numbers; until then they only order the list. "Rules" were read today where a URL is given; Reddit rules are
secondary summaries.

| Rank | Channel | Angle | Rules that matter | Manu's effort | Expected reach | Buyers per hour (INFERENCE) |
|---|---|---|---|---|---|---|
| 1 | **Newsletters, article links only**: Android Weekly, Kotlin Weekly, iOS Dev Weekly, SwiftLee Weekly, KMP Weekly; for Flutter: Code With Andrea's newsletter, Flutter Tap | The guide, not the product: "one Maestro flow for every language" (Android/KMP), "fastlane snapshot stuck in English" (iOS), the Flutter/RN guide (Flutter) | Free; they pick articles, never landing pages; iOS Dev Weekly wants your blog in the iOS Dev Directory; SwiftLee has no form ([R] marketing-research.md 1.5). I found no newsletter called "Fresh Flutter"; Flutter Developer Weekly, Flutter Tap and Code With Andrea exist ([W] search) | 0.5 h each, after a guide is live | Android Weekly says 80,000+; Kotlin Weekly 22,907; SwiftLee 21,681 ([R]). INFERENCE: 25% chance of inclusion; if included 150 to 600 clicks | **1 to 3** (needs the guide published first) |
| 2 | **Maestro community**: Slack (https://slack.maestro.dev/, `#maestro-questions`, `#showcase`), Discord, GitHub Discussions "Show and tell", the docs community-articles PR, awesome-maestro PR | Answer locale questions with the copy-paste fix, no link for the first 2 weeks; then one `#showcase` post with the WOD Tracker grid; then the article PR | Slack rules not found; promo-only accounts get removed in most Slacks; the docs community-projects page lists only free projects, articles take PRs (~5 weeks) ([R] marketing-research.md 1.9) | 15 min a day + 1 h for PRs | Small (Maestro Discussions has 156 threads in total [W]); highest intent | **0.5 to 1** |
| 3 | **Show HN, once** | Technical story: "a translated caption over an English app is not a localized screenshot", the unreachable Next button, how text selectors get rewritten per language; free `check`; say the price and the closed source up front | Must be runnable without signup; no vote asking; creator present ([W] https://news.ycombinator.com/showhn.html). Category base rate: localized-screenshot Show HNs got 1 to 3 points (2024-03-28: 1; LocaShot 2026-03-09: 3) [W] HN Algolia | 8 to 10 h (prep + answering) | Typical 20 to 100 visits; a front-page tail of 2,000 to 10,000 | **0.2 to 1** expected, with a large tail; also seeds AI-search mentions |
| 4 | **Reddit, sub by sub** | r/androiddev: a substantive post on Rule 5 terms (the unreachable-button story, how it works) or the weekly thread; r/iOSProgramming: **App Saturday, one app once per year**, so spend it on 0.1.6 with XCUITest; r/FlutterDev: only with an "insightful dive" (the Flutter/RN guide); r/SideProject; r/macapps (once per 30 days) | r/iOSProgramming: App Saturday only on Saturdays, one app once a year, proposed 20 karma and a template with tech stack, challenge and AI disclosure ([W] search summary of the sub's reminder post). r/androiddev Rule 5: promotional posts need a thoughtful description and background, no copied marketing text; weekly and monthly showcase threads ([W] search summary). r/FlutterDev: apps only if open source or an insightful dive ([W] search summary). r/reactnative: no self-promotion ([R]) | 1 to 1.5 h per post incl. replies | 50 to 500 visits per post | **0.3 to 1.5** |
| 5 | **SEO guides on shotfleet.com** (drafts exist: articles 1, 2, 3; 5 and 6 on the SEO branch) | The searches people type: "fastlane snapshot not changing language", "maestro locale screenshots", "check localized screenshots", "flutter localized app store screenshots" | Each guide's TO VERIFY list must be ticked (`build-guides.py --publish` refuses otherwise); article 2 is fully ticked [R seo-audit] | 1 h per guide to read and approve | 0 in weeks 1-3; INFERENCE 10 to 40 visits a day across guides by month 3 | **Near 0 now, highest over 6 months**; the guides also feed rank 1 and AI search |
| 6 | **fastlane GitHub Discussions "Show and tell"** + the free Fastfile lane | "A fastlane lane that fails before upload if a language is still English" (snapshot or screengrab, then `shotfleet check`) | Categories include Show and tell; activity is slow ([W] GraphQL: 1,541 discussions, latest 2026-09-29). Never reply to old issues with a link | 1 h | Small but exact; indexed by search and AI | **0.2 to 0.5** |
| 7 | **Directories and lists**: AlternativeTo (as an alternative to fastlane snapshot; queue months, $5 priority review), SaaSHub (needs a real domain and a released product: both true now), DevHunt, Uneed, Peerlist, Console.dev (email), Indie App Catalog, Awesome-ASO PR, awesome-maestro PR; **MCP registries** for `shotfleet mcp` (official MCP registry, Glama) | Per directory a different first sentence (directory-submissions skill): alternative framing on AlternativeTo/SaaSHub, technical depth on DevHunt/Console.dev, agent angle on MCP registries | awesome-ios rejects paid tools (do not submit); BetaList is paid (skip) ([R] marketing-research.md 2) | 3 to 4 h in total | A few visits each; backlinks and AI-search presence | **0.2 to 0.5** |
| 8 | **Partners and affiliates** | Andrea Bizzotto (Code With Andrea teaches Maestro screenshots per device and language, has a 22k Flutter newsletter [W]); the asc CLI author (a hand-off recipe: asc captures iOS, shotfleet checks); ASO newsletters. Offer a Gumroad affiliate cut (Gumroad allows 1 to 75% [R strategy note]) and a free key | One personal email each, only to public business addresses; no follow-up chains | 1 h per partner | Low odds, high payoff | **0.3 to 1**, high variance |
| 9 | **Mastodon (iosdev.space), Bluesky, X** | Build in public: the grid, a clip, "check found X" | No price before the post that announces the sale; disclose you built it | 10 min a day | Small for a new account (INFERENCE) | **0.1 to 0.2**, supports 1 and 3 |
| 10 | **YouTube demo** (the 9 existing clips, c1 to c9, stitched into one 2 to 3 min video with chapters and the .vtt captions) | "Localized App Store and Google Play screenshots from one Maestro flow" | Captions and chapters are what AI answers read (ai-seo skill) | 2 to 3 h | Small at first | **~0.1** early; reuse on site, HN, PH |
| 11 | **Indie Hackers** product page + one story | The build story with real numbers | Founders, not mobile devs | 1 h | Small | **~0.1** |
| 12 | **Product Hunt** | "Localized store screenshots, checked" | Can't ask for upvotes ([R]); needs a warm audience and a 3-week warm-up (directory-submissions skill). **Keysi launches there on 2026-10-14** | 10 to 20 h | Dev CLI with no audience: low (INFERENCE) | **0.05 to 0.2**. Not before mid-November, maybe never |
| 13 | **AI-search visibility** | llms.txt, FAQ schema and definitions are done or on the SEO branch; what is missing is third-party mentions (HN, Reddit, directories, newsletters) | Do not write content "for AI"; no fake mentions | 0 extra hours: it is the side effect of 1 to 7, plus a monthly check (section 6) | n/a | Indirect |
| 14 | **Gumroad Discover** | Passive marketplace | Discover sales cost a flat 30% instead of 10% + $0.50 + card fees ([W] https://checkoutpage.com/blog/gumroad-fees): about $20.30 net at $29 instead of $24.46 | One setting | Dev tools with 0 ratings rarely surface (INFERENCE) | **~0**; owner decision |
| 15 | **Podcasts** (Fragmented for Android, Launched, Under the Radar) | Only with a customer story | No guest route found ([R]) | High | | **~0** now; revisit after 2 case studies |
| 16 | **Cross-promotion from Manu's own apps** | WOD Tracker, Stressi, Cairn and AnywhereRoles users are consumers, not buyers. Useful only as proof ("made with shotfleet" on the AnywhereRoles showcase) and through Manu's developer identity (Keysi's site and HN profile) | Never mention shotfleet in Keysi's Show HN or PH threads (off-topic, looks like a vote ring) | ~0 | | **~0** as a channel; high as proof |
| - | **Paid** (section 6.4) | Only as a measured test | | | | |

**Top 5 by expected buyers per hour:** newsletters (with a published guide), the Maestro community, Show HN, Reddit sub by sub, and the
SEO guides (which also unlock the newsletters). fastlane Show-and-tell and directories follow because they are cheap and exact.

What the ranking says in one line: **publishing two guides is the highest-leverage hour Manu can spend this week**, because ranks 1, 5 and 13
all wait on it, and Show HN and Reddit go better with a guide to link from the first comment.

---

## 4. Launch sequence

The sale is open, but nothing has been announced. Treat the **announcement** as the launch. Two dates shape it:

- **Keysi's Show HN (Tue 10-13) and Product Hunt (Wed 10-14).** Don't announce shotfleet that week. Two Show HNs from one account in a week
  look like promotion, and Manu can only answer one thread well.
- **0.1.6 with XCUITest capture.** That is the strongest news hook ("now works with your existing XCUITest tests, no Maestro needed for
  iOS"). It needs its device e2e first (`tools/fixture-byoc-e2e.sh`, claims C231/C235 still "untested" [R coordinator-state]).

Recommended: **announcement week Mon 2026-10-19 to Sun 10-25**, Show HN on **Tue 10-20 or Wed 10-21**. If 0.1.6 slips, launch on 0.1.5
anyway (the free `check` on fastlane output and the Docker/Action are news too) and use 0.1.6 as the week-3 hook. Decision for Manu.

### 4.1 Pre-launch: Tue 10-06 to Sun 10-18

| When | What | Who |
|---|---|---|
| This week | **Publish two guides**: article 2 (one Maestro flow for every locale, all TO VERIFY ticked) and article 1 (fastlane snapshot stuck in English) or article 5 (check localized screenshots). Confirm `/guides/<slug>` routing with `wrangler dev` first (seo-audit finding 12). Add an RSS feed for the iOS Dev Directory | Agent builds; Manu approves |
| This week | **Search Console and Bing**: verify the domain, submit the sitemap, request indexing of `/`, `/docs`, `/alternatives`, the guides | Manu (needs his Google account) |
| This week | **Trust fixes**: Gumroad profile picture and name (the default avatar shows on the checkout); Gumroad purchase Workflow email (install line, 3 steps, "reply if stuck"); "Free at launch" heading becomes "Free" (site-claims audit) | Manu (Gumroad); agent (site) |
| This week | **Proof**: deploy the 0.1.5 site with the AnywhereRoles showcase and /demo clips once 0.1.5 publishes; one public sample run page if approved (strategy move 1) | Agent, after the release |
| 10-07 to 10-18 | **Maestro community, no links**: join Slack and Discord, answer 3 to 5 locale questions with the fix (kit `maestro-community.md`) | Manu, 15 min a day |
| 10-07 to 10-11 | **Long-lead directories**: AlternativeTo (pay the $5 priority review if approved), Console.dev email, SaaSHub, Indie App Catalog, MCP registry and Glama for `shotfleet mcp` | Manu, about 2 h |
| 10-07 to 10-11 | **Design partners**: 3 emails offering a free key for an honest write-up (kit `outreach.md`), written permission before any quote | Manu |
| 10-12 to 10-14 | **Keysi week**: no shotfleet announcements. Social build-in-public posts are fine | Manu |
| Thu 10-15 | **Go/No-Go, redefined** (section 6.5): is everything ready to announce? Not a sales verdict | Manu + agent |
| 10-16 to 10-18 | Preflight from `marketing/kit/launch-day.md` Day -1: claims check green, clean-Mac install, `check` and a 2-language `run` with no key, buy button shows $29 | Manu, 2 h |

**Waitlist.** LAUNCH.md section 7 has the waitlist email (draft `marketing/launch-email.md`). If it was never sent, send it on announcement
day 1, then purge the list 30 days later (privacy-page promise, `site/signups.sh --purge-waitlist`). If it was sent, the purge date is 30
days after that. Check which.

### 4.2 Announcement week, day by day (Mon 10-19 to Sun 10-25)

| Day | Do | Paste from |
|---|---|---|
| Mon 10-19 | Waitlist email (if not sent). Indie Hackers product page. Social thread on Mastodon, Bluesky, X (`utm_source` per network). fastlane Discussions "Show and tell": the free Fastfile lane | `marketing/launch-email.md`, kit `social.md`, `marketing/launch-drafts/` |
| Tue 10-20 | **Show HN** at about 15:00 CEST. First comment immediately. Answer every comment for the rest of the day. Nothing else | kit `show-hn.md`, launch-drafts |
| Wed 10-21 | Answer overnight HN comments. Newsletter submissions: Android Weekly, Kotlin Weekly (article 2), iOS Dev Weekly suggestion + iOS Dev Directory (article 1 or 5) | kit `newsletters.md` |
| Thu 10-22 | r/androiddev: one substantive post (story and how it works, not marketing text) or the weekly thread, after reading Rule 5 live. DevHunt submission | launch-drafts |
| Fri 10-23 | Maestro Slack `#showcase` post with the grid (if the channel allows tools) and the awesome-maestro PR. Uneed | kit `maestro-community.md` |
| Sat 10-24 | **r/iOSProgramming App Saturday** (one app, once a year: use the template, disclose AI use honestly). Only if 0.1.6 is out or the post is strong; otherwise keep the slot for later | launch-drafts |
| Sun 10-25 | Write the week's numbers per `utm_source` (section 6) and the questions people asked. Questions become FAQ entries | none |

Rules for the week: one place per day, answer within the hour, never post the HN link elsewhere, no "only N left", price once per post.

### 4.3 Weeks 2 to 8 (10-26 to 12-13)

| Week | Hook | Do |
|---|---|---|
| 2 (10-26) | 0.1.6 "use your existing XCUITest tests" (if not used in week 1) | `/whats-new` entry; social post; r/iOSProgramming App Saturday if still unused; Peerlist launch (week starts Monday) |
| 3 (11-02) | Guide 3 published (Flutter/RN, article 6) | Code With Andrea / Flutter Tap submission; r/FlutterDev "insightful dive" post; KMP Weekly |
| 4 (11-09) | First design-partner write-up (with permission) | Case study on the site; send to the partner's audience if they want |
| 5 (11-16) | "What check found in N real store listings" (only with owners' permission, or Manu's own apps) | Article; newsletters; Show HN only if genuinely new |
| 6 (11-23) | YouTube demo from the clips | Embed on home and guides |
| 7 (11-30) | Day-60 gate prep | Read per-channel numbers |
| 8 (12-04) | **Day-60 gate** (STRATEGY.md): 50+ sales keep investing; 15 to 49 narrow to what sold; under 15 stop building, keep it as a free tool | Decide |

Product Hunt, if at all: not before mid-November, with a warm list and the 3-week warm-up, and never in a Keysi week.

---

## 5. Founder price and free keys

### 5.1 "First 100 buyers at $29", honestly

- The scarcity is real: FOUNDER29 has a 100-use limit and Gumroad applies it by itself [R LAUNCH.md]. That is the only urgency allowed.
- **No counter, no "only N left".** Nothing true feeds a number on the page (LAUNCH.md open items). Say "launch price for the first 100
  sales"; never invent a deadline.
- **Tell people when it ends.** Read the FOUNDER29 use count in Gumroad weekly. At about 90 uses, ask an agent to change the site to "the
  $29 price is almost gone", and when it hits 100, to "$49". That is an honest update, not a countdown trick.
- Mention $29 **once per post**, at the end (MARKETING.md rule). Lead with the problem, not the discount.
- Use it as a thank-you, not a lever: "the first 100 people who pay help me find out whether this is worth building further" is true
  (the day-60 gate) and fits HN's taste.
- Open item from LAUNCH.md: what Gumroad shows after the 100th use. Check it before sale 90.

### 5.2 Free keys for open-source maintainers and students

Decided by Manu on 2026-10-06 and live in the 0.1.5 site text [R CHANGELOG 0.1.5]. How to use it as goodwill:

- Mention it in the Show HN first comment and in r/androiddev and r/FlutterDev posts. It answers "closed-source paid tool" with something generous.
- One single-use 100%-off code per request, by email. These don't use up FOUNDER29's 100 (different code) and are not "buyers".
- Ask, don't require: "If it helps, a public note on how it went would mean a lot." Never trade a key for a review or a star.
- OSS maintainers with real localized apps (wger, KotlinConf, Rocket.Chat were run in research) are the best design partners: their
  public repos make honest case studies possible, with permission.
- Track the count. If requests pass about 30 a month, set a rule (one per project).

---

## 6. Metrics and budget

### 6.1 What to track, and where

| Metric | Tool | Status |
|---|---|---|
| Visits, pricing views, CTA clicks by `utm_source`, per day | First-party counter: `site/signups.sh --visits` | Live [R] |
| Same, plus referrers and countries for visitors who accept | GA4 `G-6NY43DB3F4` | Live; mark `cta_click` and `pricing_view` as key events after their first real hit; set the internal-traffic filter to Active after adding Manu's IP [R ga4-investigation] |
| Search impressions, clicks, queries, indexing | **Google Search Console + Bing Webmaster Tools** | **Not set up** (owner) |
| Sales, FOUNDER29 uses, refunds with reason, sales by UTM | Gumroad dashboard (keeps `utm_source` from links) | Live |
| Free-key codes issued | A line per code in a private note | New |
| `check` reach outside the Mac | ghcr.io image pull count; GitHub Action usage (dependents) | Available after 0.1.5 |
| Installs and downloads | Not counted (static files) | Strategy item F12 (counted `/download/` redirect) needs a privacy-page edit first |
| Support minutes per buyer | By hand | Stop rule: over 30 min per sale means fix onboarding before more marketing |
| AI-search visibility | Monthly: 10 queries x ChatGPT, Perplexity, Claude, Google AI Overviews, 3 runs each; log "cited k/3" | New (ai-seo skill method) |

Queries for the AI check: "how to make localized App Store screenshots automatically", "fastlane snapshot not changing language",
"maestro screenshots multiple languages", "check app store screenshots language", "fastlane snapshot alternative", "localized google play
screenshots emulator", "shotfleet".

### 6.2 Weekly targets (INFERENCE; replace with real numbers after week 1)

| Week | Visits | Sales | Leading signals |
|---|---|---|---|
| 10-05 to 10-11 (quiet) | 100 | 0 to 1 | Search Console verified; 2 guides live |
| 10-12 to 10-18 (Keysi week) | 150 | 1 | 3 Maestro answers; directories submitted |
| 10-19 to 10-25 (announcement) | 1,000 to 2,000 | 4 to 10 | HN points, newsletter inclusions, `check` questions in threads |
| 10-26 to 11-08 | 400 a week | 2 a week | 1 design-partner report; refunds explained |
| 11-09 to 12-04 | 300 to 600 a week | 2 to 4 a week | Guide impressions rising in Search Console |

Day 30 (11-04): 3 sales is the floor, 10 the goal (strategy note). **Honest reading:** these targets add up to about 25 to 35 sales by
the day-60 gate. Reaching 50 needs one breakout: a front-page Show HN, a newsletter feature in Android or iOS Dev Weekly, or a partner
recommendation. Plan for the base case, hope for the tail.

If week 3 has 500+ visits and 0 sales, the problem is the page or the install, not reach: stop posting and run the clean-Mac cold test
(strategy note 9).

### 6.3 The EUR 0 plan

Everything in sections 3 to 5 except the optional items below. Manu's time: about 6 hours a week, 10 to 12 in announcement week.

### 6.4 Optional small paid tests (suggestions only; Manu decides and pays)

| Test | Cost | What it buys | When |
|---|---|---|---|
| AlternativeTo priority review | $5 once | Listing in 1 to 2 business days instead of months ([R]) | Now |
| Reddit ads, subreddit targeting (r/iOSProgramming, r/androiddev, r/FlutterDev, r/reactnative), 2 variants, `utm_source=reddit-ads` | $30 to $50 | Reported CPC $0.50 to $3.50 ([W] https://stackmatix.com/blog/reddit-ads-cost-guide-2026, a vendor blog): 10 to 100 clicks. Learning (do paid clicks reach pricing?), not sales. One $29 sale nets $24.46 | After a week of organic baseline, so from about 10-26 (kit `reddit-ads.md`) |
| Uneed paid date | $29.99 | Pick the launch day | Only if the free queue lands in a bad week |
| **Not now:** iOS Dev Weekly sponsorship | $2,500 an issue ([W] https://iosdevweekly.com/sponsorship) | Would need about 102 sales at $24.46 net to break even | Never at this stage |

### 6.5 Decision points

| Date | Decision | Rule |
|---|---|---|
| **Thu 2026-10-15** (scheduled task `shotfleet-go-no-go`) | **The task is stale**: it counts waitlist signups on the old workers.dev URL with a rule STRATEGY.md replaced. On 10-15 nothing has been announced, so a sales verdict would mean nothing. **Recommend Manu rewrites it** as an announcement-readiness check: claims check green; clean-Mac install and free `check` work; 2 guides live and in Search Console; Gumroad avatar and Workflow email done; 0.1.5 live; 0.1.6 status. Go = announce week of 10-19; No-Go = fix the failing item, announce a week later | This note does not edit the task (persistent configuration is Manu's) |
| Sun 10-25 | After announcement week | Keep the channels that produced a pricing view per 50 visits or better; drop the rest |
| Wed 11-04 (day 30) | Floor 3 sales, goal 10 | Below 3 with 1,500+ visits: fix the page and onboarding before any more posts |
| Before sale 90 | FOUNDER29 ending | Site text update; check Gumroad's page after use 100 |
| **Fri 2026-12-04 (day 60)** | STRATEGY.md gate | 50+ keep investing (Team/CI licence if asked); 15 to 49 narrow; under 15 stop building, keep it a free tool and a reputation piece |

---

## 7. What NOT to do, and the risks

### 7.1 Don't

- Post the same text in several subreddits, Slacks or Discords; drop links in threads nobody asked in; reply to old GitHub issues with a link.
- Ask anyone to upvote, star or review, on HN, PH, Reddit or GitHub; share the HN link while it is live; ask friends to comment.
- DM people who did not write first.
- Write or buy fake reviews, testimonials or quotes; use a logo or a quote without written permission and real use.
- Invent urgency: no countdown, no "only N left", no deadline that isn't real.
- Overclaim: "catches all localization bugs", "works with Flutter/React Native" (beyond one real app each), "Maestro endorses", "fastlane
  is slow", frames, captions, upload, Intel, run times as anything but "on my M1 Pro, with my app".
- Use other people's apps' findings in public (for example the subscrifi results in the coordinator state) without the owner's permission.
  If subscrifi is Manu's own app, say so when citing it.
- Mention shotfleet in Keysi's launch threads, or launch both in one week.
- Submit to awesome-ios (paid tools rejected) or BetaList (paid); pay for a directory-submission service.
- Post anything before `tools/check-claims.sh` is green.

### 7.2 Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Nobody notices: Show HN gets 1 to 3 points like the category's history | High | Don't depend on one post; newsletters and guides compound; re-try HN only with something genuinely new |
| Install or first-run friction on a stranger's Mac (Maestro, Java, Xcode, load) turns visits into refunds | Medium | Clean-Mac cold test with 2 outside developers before announcing; `doctor --fix`; the purchase Workflow email; answer support within hours |
| Trust: closed source, `curl \| sh`, unknown solo seller with a default Gumroad avatar and 0 ratings | Medium | Signed and notarized, Homebrew cask, checksum, network allow-list, 14-day refund; fix the Gumroad profile now |
| Five releases in two days read as "unstable" | Medium | Frame as "fixed what real runs found, same day"; keep `/whats-new` plain; no release in announcement week unless it fixes a blocker |
| A claim turns out wrong in public | Medium | Correct it in the thread the same hour; fix the site; add a claims row (launch-day.md) |
| Maestro ships locale fan-out, or asc/fastlane add a check | Low to medium | Lean on `check` (works on anything) and XCUITest capture; integrate, don't fight |
| Keysi and shotfleet compete for Manu's time | High | Separate weeks; this plan keeps shotfleet's announcement after Keysi's |
| The 10-15 task posts a meaningless "No-Go" from 0 waitlist signups | High if unchanged | Rewrite or disable it (6.5) |
| Reddit bans for self-promotion | Medium | Read sidebars live; one post per sub; story first; Reddit gives feedback more than sales |
| Tax/KvK question unresolved when the first payout arrives | Medium | Accountant step before the first payout (STATUS.md, Manu only) |

---

## 8. One page: do this next week (Wed 10-07 to Tue 10-13)

**Decide (10 minutes)**
- [ ] Announcement week: 10-19 (recommended, Show HN Tue 10-20 or Wed 10-21), or later.
- [ ] Rewrite or disable the 10-15 `shotfleet-go-no-go` task (6.5).
- [ ] Optional spend: $5 AlternativeTo priority (yes/no); Reddit ads test from 10-26 (yes/no).

**Publish and set up (about 3 hours)**
- [ ] Approve guide 2 (Maestro, every locale) and one of guide 1 or 5 for publishing; agent ships them with an RSS feed.
- [ ] Verify shotfleet.com in Google Search Console and Bing Webmaster Tools; submit the sitemap; request indexing of 6 pages.
- [ ] Gumroad: real profile picture and name; purchase Workflow email (install line, 3 steps, "reply if stuck"); decide Discover on/off.
- [ ] Mark `cta_click` and `pricing_view` as GA4 key events once they appear.

**Community, no links yet (15 minutes a day)**
- [ ] Join the Maestro Slack and Discord; answer 3 locale questions with the fix (kit `maestro-community.md`).
- [ ] Read live, and note: r/androiddev Rule 5, r/iOSProgramming App Saturday rules, r/FlutterDev rules, r/SideProject, r/macapps.

**Long-lead listings (about 2 hours)**
- [ ] AlternativeTo (as alternative to fastlane snapshot), SaaSHub, Console.dev email, Indie App Catalog, the MCP registry and Glama for `shotfleet mcp`. Different first sentence on each.

**People (1 hour)**
- [ ] 3 design-partner emails with a free key offer (kit `outreach.md`); 1 partner email to Code With Andrea (affiliate + free key).
- [ ] Check whether the waitlist email went out; if yes, put the purge date in the calendar.

**Don't, this week**
- [ ] No Show HN, Product Hunt or Reddit post for shotfleet; Keysi has 10-13 and 10-14.

---

## Sources (read 2026-10-06)

Web:
- Gumroad product page (read only): https://8954369651852.gumroad.com/l/shotfleet
- fastlane issues: https://github.com/fastlane/fastlane/issues/9043 , https://github.com/fastlane/fastlane/issues/11457 , https://github.com/fastlane/fastlane/issues/8895 , https://github.com/fastlane/fastlane/issues/12917 , https://github.com/fastlane/fastlane/issues/11696 , https://github.com/fastlane/fastlane/issues/14584 , https://github.com/fastlane/fastlane/issues/14307
- fastlane Discussions (Show and tell category): https://github.com/fastlane/fastlane/discussions
- Maestro issues: https://github.com/mobile-dev-inc/Maestro/issues/393 , https://github.com/mobile-dev-inc/Maestro/issues/2209 , https://github.com/mobile-dev-inc/Maestro/issues/2654 ; Discussions: https://github.com/mobile-dev-inc/maestro/discussions
- Maestro locales doc: https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales ; community: https://docs.maestro.dev/extra-materials/community , Slack https://slack.maestro.dev/
- Code With Andrea, Maestro screenshots: https://codewithandrea.com/tips/automated-screenshot-generation-maestro/ ; newsletter: https://www.codewithandrea.com/newsletter/
- iMore on multi-language screenshots: https://imore.com/how-easily-automatically-take-multi-language-screen-shots-app-store-submissions
- ButterKit pricing: https://butterkit.app/pricing
- AppScreens pricing: https://appscreens.com/pricing
- AppScreenshotStudio pricing: https://appscreenshotstudio.com/pricing ; compare pages: https://appscreenshotstudio.com/compare
- Screenshots Pro: https://screenshots.pro/
- simshot: https://github.com/FreakLee/simshot ; asc CLI: https://github.com/rorkai/App-Store-Connect-CLI ; StoreScreens: https://github.com/ciscoriordan/storescreens-cli
- Lokalshot / AppShotter / Screenhance (search results): https://hunted.space/product/lokalshot , https://www.capterra.com/p/10046307/AppShotter/ , https://screenhance.com/app-store-screenshot-translator
- HN Show HN rules: https://news.ycombinator.com/showhn.html ; HN search API: https://hn.algolia.com/api/v1/search?query=screenshots%20localized&tags=show_hn
- r/iOSProgramming App Saturday (mirror of the sub's reminder post, via search): https://reddit.birdcat.cafe/r/iOSProgramming/comments/1k4lasw/reminder_app_saturday
- r/androiddev Rule 5 (search summary of a mirror): https://redlib.hbubli.cc/r/androiddev/s/w1T0bZ4NHD
- r/FlutterDev rules (search summary): https://thehiveindex.com/communities/r-flutterdev/
- Gumroad fees incl. Discover 30%: https://checkoutpage.com/blog/gumroad-fees
- iOS Dev Weekly sponsorship: https://iosdevweekly.com/sponsorship
- Reddit ads CPC (vendor blog): https://stackmatix.com/blog/reddit-ads-cost-guide-2026
- Localized screenshots lift (vendor case study): https://splitmetrics.com/cases/fiftythree-localizes-screenshots-for-app-store
- Apple caption text indexing since June 2025 (secondary, with a caveat that captions rarely rank alone): https://appdrift.co/blog/app-store-screenshot-text-indexing
- GitHub star counts: GitHub REST API, `repos/<owner>/<repo>`

Repo and local (read only): MARKETING.md, STRATEGY.md, PLAN.md, LAUNCH.md, STATUS.md, CHANGELOG.md (main and `claude/post-015-candidate`),
`site/public/index.html`, `site/public/alternatives.html`, `tests/claims.json`, `marketing/kit/*`, `marketing/competitors.md`,
research notes listed at the top, `/Users/manu/Developer/shotfleet-rc-build/coordinator-state.md`, scheduled tasks `shotfleet-go-no-go`
and `keysi-launch-day`.

Skills followed: marketing:campaign-plan (structure), marketing:competitive-brief (section 2), directory-submissions (rank 7, per-directory
positioning, MCP registries), ai-seo (rank 13, the monthly check), pricing (positioning only; prices unchanged), aso (buyers' world:
localized screenshots and caption indexing).
