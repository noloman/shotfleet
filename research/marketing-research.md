# Marketing research for shotfleet (researched 2026-10-02)

Scope: where the first buyers can honestly come from for a $29 (first 100) then $49 one-time macOS CLI by an unknown solo founder,
with a free tier (`check` + 2 languages in `run`). Sale opens after Polar's review (earliest ~2026-10-16). Waitlist: 0 signups at last check.

Method and limits (read first):
- Web search + page fetch. Every fetch went through a summarizing model, so wording is paraphrase-risk: re-open a page before quoting it publicly.
  Tags: **(V)** = a page I read that states it first-hand, **(S)** = secondary source (aggregator, blog, vendor) or search snippet only,
  **(U)** = could not verify. GitHub numbers came from the GitHub API today and are exact. Hacker News numbers came from HN's Algolia API today.
- Reddit is blocked for the research tools (reddit.com and old.reddit.com refused). **No subreddit rule below was read on Reddit itself.**
  Rule text comes from third-party rule directories (LeadsRover, ReplyHey) that quote the rules. Manu must read each sidebar before posting.
- No keyword-difficulty or search-volume numbers were obtainable (the Ahrefs and Similarweb connectors in this session are not authorized;
  Ahrefs' free generator page returns no data without an interactive query). Section 3 therefore uses SERP composition and competitor content volume as evidence.
- No public "first 100 users" numbers exist for ButterKit, AppScreens, Shotbot, simshot, StoreScreens or Tuist that I could find. Section 4 says what is and is not known.

---

## 0. Summary of what matters most

1. **The highest-fit audience is the Maestro community**, because Maestro's own docs say a flow cannot set the locale (see 1.9). That is our exact gap, and the places to reach those people are free and small.
2. **Hacker News works for this category only with a runnable free tier and a story, and the base rate is low.** 25 Show HN posts about App Store screenshot tools: all but one got 1-4 points (the best, 17, in 2017). A waitlist page does not qualify as a Show HN at all.
3. **Existing launch drafts conflict with sub rules.** marketing/launch-posts-v2.md plans one post to r/iOSProgramming + r/androiddev. r/androiddev's rule is reported as "No App Promotion or Recruiting Testers" (S), r/reactnative as "no self promotion" (S), r/iOSProgramming as feedback threads only (S). Read live before posting; expect to use comments and answers rather than link posts.
4. **A custom domain is a prerequisite for most directories and for backlinks.** SaaSHub rejects free-subdomain sites and waitlist pages (V). The URL is also baked into the binary (roadmap R6), so decide the domain before the first sale, not after.
5. **SEO is slow but the long-tail troubleshooting queries (fastlane snapshot stuck in English, Maestro locale, screengrab locale) are served by GitHub issues and old docs, not by polished pages.** Both direct competitors publish heavily (ButterKit ~175 URLs, AppScreens ~67 blog/guide URLs, including an "appscreens-vs-fastlane" page).
6. **The honest scarcity is real:** first 100 buyers at $29. Show a live counter fed by Polar's FOUNDER29 redemptions; do not invent any other urgency.

---

## 1. Where indie mobile developers discover tools, ranked by likely yield for us

Ranking is my judgment (fit x reachability x cost for a solo founder with no audience), not measured data. "Yield" is expected quality of visitors, not volume.

| Rank | Channel | Why for us | Cost / effort | Main risk |
|---|---|---|---|---|
| 1 | Maestro community (Slack, docs community pages, awesome list) | Exact pain; people already searching for locale handling | Hours; helpful answers first | Paid tool may not be listed; PR lead time ~5 weeks |
| 2 | Show HN (once, after sale is live and free tier installs) | Only channel with a documented path to hundreds of technical visitors | 1 day prep + 1 day answering | Category base rate is 1-4 points; closed binary + curl-pipe-sh draws skepticism |
| 3 | Long-tail SEO + founder stories on own domain | Compounds; competitors prove demand exists | 2-3 posts per week of work | 4-12 weeks before any traffic (my estimate, no data) |
| 4 | Mobile newsletters (Android Weekly, Kotlin Weekly, KMP Weekly, iOS Dev Weekly, SwiftLee Weekly) | Exactly the buyer; free to submit | 30 min per submission | They want an article, not a product page; no guarantee |
| 5 | Reddit (r/macapps, r/SideProject, feedback threads, answers) | Feedback and a few early users; poor for direct sales per screenfast.app | Ongoing, 15 min/day | Bans; rules restrict most dev subs |
| 6 | Indie Hackers (product page + one story post) | Free, evergreen, Google-indexed listing; audience is founders, not mobile devs | 1-2 h | Low conversion for a mobile-dev tool |
| 7 | Directories (AlternativeTo, DevHunt, Uneed, Peerlist, Console.dev, Indie App Catalog, Awesome-ASO) | Backlinks and a few visits; section 2 | 3-4 h total | Lead times; most accept only a live product |
| 8 | Build-in-public on Mastodon (iosdev.space), Bluesky, X | Where Indie Dev Monday, iOS Dev Weekly, Android Weekly are announced | 10 min/day | Unknown yield; slow |
| 9 | Product Hunt | Badge + dofollow backlink; poor conversion for solo founders per secondary sources | 50-120 h per vendor blogs (S) | Time sink |
| 10 | YouTube / podcasts | Own 90-second demo video matters; pitching creators does not pay at this size | Demo: 2 h | Creators teach basics, rarely review tools |
| 11 | Slack/Discord (iOS Folks, Kotlin Slack, ASO Stack) | Reputation and answers, not links | Ongoing | Promo-only accounts are deleted |
| n/a | Apple Developer Forums | Code-level Q&A only; not a promotion venue | none | Do not use |

### 1.1 Hacker News

- Show HN rules (V, https://news.ycombinator.com/showhn.html): must be something people can try; "blog posts, sign-up pages, newsletters, lists" do not qualify; landing pages do not qualify; "make it easy for users to try your thing out, ideally without barriers such as signups or emails"; you must be the creator and available to discuss it; do not ask friends to upvote. **Implication: the waitlist page cannot be the link. Post only when `curl ... | sh` installs and the free tier runs without a key.**
- Guidelines (V, https://news.ycombinator.com/newsguidelines.html): do not use HN primarily for promotion; do not solicit upvotes or comments; no editorializing or superlatives in titles.
- Evidence on base rates (HN Algolia API, fetched today):
  - Show HN posts with "app store screenshots": 25 hits, almost all 1-4 points, 0-2 comments; best 17 points / 4 comments (2017); newest in 2026 include LocaShot (3 pts), GlotShot (1), ezscreenshots (3), StoreMock (2). The category is crowded with generators; none is a capture-and-verify tool.
  - Show HN around Maestro: three posts, 1-3 points each (maestro-iOS-device, maestro-runner, a Maestro cloud alternative). Yet maestro-runner has 494 GitHub stars (GitHub API): HN points are a poor proxy for adoption.
  - The Maestro project itself: "Maestro - Next generation mobile UI automation", 185 points / 66 comments, 2025-03-01 (V, https://news.ycombinator.com/item?id=43174453). Open source, founder answered pricing questions in the thread.
  - Localization tools that did well: Lingo.dev 89 pts / 72 comments, LocaFlow 89, Quicklang 43 (search-engine summary of HN hits; these are free/open or free-plan tools).
  - A paid Mac dev tool precedent: DevUtils.app, Show HN 2020-09-28, 241 points / 105 comments (V, https://news.ycombinator.com/item?id=24604291). Open source with a paid pre-built version; commenters asked for Mac App Store distribution and the creator listed it within days.
  - Vendor claim (S, daily.dev business blog, biased): median Show HN is 2 points, 50 points is top ~6%, 250+ top ~1%. https://business.daily.dev/resources/hacker-news-marketing-developer-tools-show-hn-launch-day-sustained-coverage/
  - One anecdote with real numbers (S, https://www.siwan.io/blog/indie-hacker-revenue-report): DocAPI Show HN, ~800 unique visitors in 24 h, ~40 free signups, 1 paid within 24 h, 12 paid within two weeks; the author says weak docs cost week-two signups. One data point, not a benchmark.
- What makes it work for a paid tool (from the above + https://www.markepear.dev/blog/dev-tool-hacker-news-launch (S) and https://www.lucasfcosta.com/blog/hn-launch (S)): specific title, say how you make money, easy free try, a first comment with backstory and technical detail, answer every comment, never ask for votes (HN detects rings, per the second source).
- Shotfleet-specific cautions: (a) closed source and a `curl | sh` installer on a workers.dev subdomain will be questioned; say plainly why it is signed/notarized and checksum-verified (DISTRIBUTION.md); (b) macOS-only, Apple silicon only, needs Xcode and Maestro; say it up front; (c) the draft title in launch-posts-v2.md is fine ("One English Maestro flow, every language your app ships, checked") but avoid "checked" claims beyond what is proven.
- Timing guidance from vendor blogs (Tue-Thu morning US Eastern) is (S) and unverified; the one hard rule is not to launch before the product is runnable.

### 1.2 Reddit (rules NOT read first-hand; verify each sidebar)

| Subreddit | What third-party rule directories say | Source | Use |
|---|---|---|---|
| r/iOSProgramming | Promotion only in designated feedback threads, not raw links | (S) https://www.replyhey.com/subreddits ; https://screenfast.app/blog/reddit-promotion-indie-ios-app (dated 2026-07-07) | Answer questions; use the feedback thread; no link post |
| r/androiddev | "No App Promotion or Recruiting Testers"; verified 2026-06-01 by the directory | (S) https://leadsrover.io/subreddits/r/androiddev | Do not post the product. A story-first technical post with no product link might pass; ask mods first |
| r/reactnative | "It is not allowed to promote your company in any way, shape or form" | (S) https://leadsrover.io/subreddits/r/reactnative | Do not post |
| r/FlutterDev | Directory says restricted; unverified detail | (S) replyhey (conflicting detail elsewhere) | Read sidebar; likely answers only |
| r/swift | Directory says restricted | (S) replyhey | Read sidebar |
| r/SideProject | Allowed ("any day, any post if you built it", explain process); other directory lists it as restricted: conflicting | (S) https://leadsrover.io/subreddits/r/sideproject ; https://www.soar.sh/blog/self-promotion-rules-by-subreddit-database (2026-05-31) | Best candidate for a build story post |
| r/macapps | "Infrequent self-promotion is permitted; not more than once per developer in 30 days"; verified 2026-06-04 | (S) https://leadsrover.io/subreddits/r/macapps | One post, at launch; our app is a Mac CLI but audience is Mac power users, fit unproven |
| r/indiehackers | One self-promo post with "SHOW IH" flair, for feedback | (S) https://leadsrover.io/subreddits/r/indiehackers | One post, after launch |
| r/ASO, r/kotlin | Not found in any directory | (U) | Read sidebar |

Playbook claims worth keeping (S, https://screenfast.app/blog/reddit-promotion-indie-ios-app): build comment history for 2-6 weeks first; weave the product into a story; share links when asked; Reddit gives feedback more than sales. One indie founder's first 100 users came 60 from Reddit, 25 Discord, 15 Indie Hackers, 0 from Hacker News or Twitter, but the product was a niche powerlifting site, not a dev tool (V, https://www.indiehackers.com/post/how-i-got-my-first-100-users-2fc9d71c34): niche community beats general tech audiences when the niche exists. Our niche is "Maestro users" and "teams shipping 10+ languages".

### 1.3 Indie Hackers

- Free account; "Add a Product" creates a product page that Google indexes (S, https://www.indiehackers.com/products, https://wheretosubmit.org/guides/indiehackers-submission-guide). Posting rules not found (U).
- Audience skews founders; expect feedback, not many mobile-dev buyers. Worth doing because it is free and the product page ranks for the brand name over time (S).

### 1.4 Social: X, Bluesky, Mastodon

- iOS Dev Space is a Mastodon instance for iOS developers (S, https://github.com/iOSDevSpace); Android Weekly, iOS Dev Weekly and Indie Dev Monday are on Mastodon/Bluesky/X (V on their sites). Bluesky starter packs for iOS/indie Apple developers exist (S, https://blueskystarterpack.com/ios).
- How much a new account gets here is unmeasured (U). Use it to post the true stories in section 4 with screenshots and to tag no one.

### 1.5 Newsletters (all free to submit; none guarantees inclusion)

| Newsletter | Reach (as stated) | How to submit | Notes |
|---|---|---|---|
| iOS Dev Weekly | not disclosed; now owned by Mobile Seasons GmbH (droidcon) since May 2026 (V https://iosdevweekly.com/about) | Form at https://suggest.iosdevweekly.com (V) | Form says: do not submit links from blogs already in the iOS Dev Directory (the curator reads them by RSS); add your blog to the directory instead; give a short reason the link merits inclusion. Accepts blog posts and libraries, from self or others. Submit the article, not the product |
| SwiftLee Weekly | 21,681 email + 9,150 LinkedIn (V https://swiftlee-weekly.com/about/) | No form; contact via X or LinkedIn per the page | Five community links per issue, chosen from iOS Dev Directory / iOS Feeds and followed writers; sponsorship never buys a link. Wants "practical experience, a clear outcome" |
| Android Weekly | "more than 80,000" (V https://androidweekly.net/) | "Submit" link in the site nav (exact URL not confirmed; /suggest returned 404) | "Links ... will be chosen by us"; covers tutorials, libraries, tools |
| Kotlin Weekly | 22,907 (V https://kotlinweekly.net/) | Email mailinglist@kotlinweekly.net, subject "Link for submission - Kotlin Weekly" | One sponsor per issue; sponsorship by the same address |
| KMP Weekly | not shown | https://kmpweekly.com/submit (V nav link), hello@kmpweekly.com | Fits Compose Multiplatform proof (Kuokka, HackerNewsKMP) |
| Indie Dev Monday | not shown | Form on site, DM @IndieDevMonday or @joshdholtz, or newsletter@indiedevmonday.com (V https://indiedevmonday.com/faq) | Spotlights indie developers/apps; whether dev tools are in scope is not stated (U) |
| Console.dev | not shown | Email hello@console.dev (V https://console.dev/selection-criteria); third-party source says editorial review 1-2 weeks (S) | Accepts commercial and open-source; no sponsored reviews; criteria include self-service try, CLI/API, docs, easy install. Our free tier helps |
| React Native Newsletter (Infinite Red) | monthly | https://reactnativenewsletter.com/submit ; newsletters@infinite.red (V) | Only after a real React Native run (claims discipline) |
| This Week In React | 40,297 (V https://thisweekinreact.com/) | No submit path on page; contact the editor via his site | Only after real RN run |
| Flutter Developer Weekly | not shown | Editor Mark Winters, contact email not visible (V https://flutterdeveloperweekly.com/) | Only after real Flutter run. flutterweekly.net now redirects to an unrelated GitHub org: treat as defunct (V) |
| Swift Weekly Brief | n/a | n/a | About Swift.org open-source projects: not a fit |

Editorial reality: SwiftLee Weekly says there is "no guaranteed path" and selects by experience and outcome; iOS Dev Weekly asks you to rely on your blog being in the directory. So the asset is a good article on our own domain (section 3 and 4), submitted once, not a pitch for the product.

### 1.6 Product Hunt

- Rules (V, https://www.producthunt.com/launch): you can launch as often as you have significant iterations; you cannot ask people directly to upvote (ask them to visit and comment).
- Is it worth it for a solo founder's dev tool in 2026? Mostly (S, vendor/blog sources, no primary data): average indie launch gets 47 signups and under 3 paying customers (https://getlaunchlist.com/blog/how-to-launch-on-product-hunt-2026); DevHunt converts better per visitor for dev tools; treat PH as a badge and backlink, not acquisition. An opinion piece claiming PH is dead for indies cites no data and promotes a competitor (V, https://dev.to/indiehackerksa/why-product-hunt-no-longer-works-for-indie-founders-aom). **Verdict: skip until after Show HN and directories; low priority.**

### 1.7 dev.to, Hashnode, Medium

- Maestro articles live on dev.to and Medium (search results); the official Maestro "community articles" page takes links by pull request (section 1.9). Cross-post with the canonical URL pointing at our own domain so SEO credit stays with us.
- ProAndroidDev is a Medium publication for Android; its submission guidelines were not found (U). dev.to community-guidelines page returned 404 (U).

### 1.8 YouTube and podcasts

- Official Maestro channel hosts its own demos and live sessions (S, search results). Big iOS channels (Sean Allen 230K+, Hacking with Swift 175K+ per a ranking blog (S)) teach Swift basics; no evidence they review CLI tools from unknown founders.
- Podcasts: Launched by RevenueCat (hosted by Charlie Chapman, S) and Under the Radar (Marco Arment and David Smith, S) are indie-app shows; no public guest-submission route found (U). Antoine van der Lee's RocketSim story is told on RevenueCat's blog (V, section 4).
- **Realistic action: record one 60-90 second terminal screen capture of `shotfleet run` plus the review grid, and use it everywhere. Do not pitch creators yet.**

### 1.9 Maestro community (best fit)

Facts (V unless noted):
- Maestro docs: "There is no place within a Flow itself (such as `launchApp` or `config.yaml`) to define the locale." Locale is set by `--device-locale` on `maestro start-device` and `maestro cloud`, not on `maestro test`. https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales (summarizer; re-open before quoting). The docs recommend tags plus `--device-locale`; they do **not** say "one flow per locale", so do not put that phrase in public copy (STRATEGY.md and marketing/competitors.md use it).
- Public evidence of the failure mode: a developer's repo documents (2026-09-20/21) that a flow's `env:` default beat the command line in Maestro 2.10 so every "Portuguese" screenshot was English; he caught it only by reading "App language: English" in the image. https://github.com/RogerioDoCarmo/morse_app/pull/216 . This is the story "screenshots silently in the wrong language", and it is a citation, not someone to contact.
- Slack: https://slack.maestro.dev/ , channel `#maestro-questions` (V, docs page). Workspace rules not found (U).
- Official community-projects page: https://docs.maestro.dev/extra-materials/community/community-projects . Sections: IDE support, frameworks and samples, DevOps and CI/CD; **it lists only free/open-source projects and states no submission route**. Source file: `resources/community/community-projects.md` in https://github.com/mobile-dev-inc/maestro-docs (85 stars, pushed 2026-09-18). Pull requests are the route: PR #130 (adds awesome-maestro to official resources) opened 2025-05-04, merged 2025-06-10; PR #149 (links a community article) opened 2025-09-17, merged 2025-10-22; PR #204 (adds a reporter to community projects) opened 2026-09-20, still open today. **Lead time is about 5 weeks and a closed-source paid tool may be refused: ask in Slack or open an issue first.**
- Community articles page (same repo, `articles.md`): accepts links to community articles via PR (#149 precedent). This is the more likely acceptance: a tutorial article rather than a product listing.
- Awesome list the docs point to: https://github.com/ludovicobesana/awesome-maestro (20 stars, 32 commits, CC0, pushed 2026-09-20; sections Articles, Tools and Integrations, Showcases, Talks, Guides, Example Projects, Official Resources). It already lists BrowserStack, a paid device cloud, so a paid tool is plausible. Two other repos with the same name exist with 0 stars (ibrahimsn98, ewertonce): ignore them. Submission: fork + PR per its CONTRIBUTING.md.
- Maestro Showcase page is customer success videos with no submission route (V).

### 1.10 fastlane community

- fastlane is under the Mobile Native Foundation since 2023 (S, https://github.com/MobileNativeFoundation/discussions/discussions/194); repo has 42,193 stars, pushed today (GitHub API).
- **No awesome-fastlane list worth listing on exists** (GitHub search returned one 37-star list last touched 2017).
- Plugin listing is automatic: a gem named `fastlane-plugin-<name>` published on RubyGems appears via `fastlane add_plugin` and https://docs.fastlane.tools/plugins/available-plugins/ (V create-plugin doc; the available-plugins page shows scores by contributors, downloads, tests, MIT license; the listing mechanism itself is not spelled out). STRATEGY.md lists a fastlane plugin as pending; a thin public gem that shells out to the signed binary is the free listing, but it makes a public repo (DISTRIBUTION.md decided no public repos for the program itself; a wrapper gem is separate).
- Pain evidence to cite in content: fastlane issues #8895, #9043, #11457, #11736, #12917 (snapshot not switching language), https://github.com/fastlane/fastlane/issues/11457 (V titles from search; bodies via summarizer in research/market-2026.md).

### 1.11 ASO communities

- ASO Stack Slack (Phiture): 6,000+ members per its page (S); guidelines (V, https://phiture.com/aso-stack-slack-community/guidelines/): no direct selling or excessive advertising, no solicitation by DM, products relevant to ASO may be promoted only in `#promotion`. Screenshots are a core ASO asset, so `#promotion` is allowed once with a real description; do not DM.
- Awesome-ASO list (https://github.com/rafaecheve/Awesome-ASO, 51 stars, pushed 2026-09-27): PR-based, and its Tools section already lists commercial screenshot tools (AppStills, appdesigns). Free listing, uncertain that a CLI fits; try one PR.
- Phiture, AppFigures, AppTweak blogs: contribution routes not found (U). r/ASO rules: not found (U).

### 1.12 Slack / Discord / forums

| Community | Rule found | Use |
|---|---|---|
| iOS Folks / iOS Developers Slack | Invite-only; "If your only posts are ones promoting your own work or jobs, we will delete them" ; no unsolicited marketing DMs (V https://github.com/iOS-Developers-Slack/Code-Of-Conduct) | Only if already a member; contribute first |
| Kotlin Slack | Code of conduct has no promotion rule; "refrain from cross-posting the same message on multiple channels. It is considered spamming"; use `#meta` if unsure (V https://kotlinlang.org/docs/slack-code-of-conduct.html) | Ask in `#meta` before any mention |
| ASO Stack | see 1.11 | `#promotion` only |
| Swift Forums, Swift Discord | Code of Conduct only; promotion rules not found (U) | Skip |
| RevenueCat community | Categories: Get Help, Learn and Share (Tips and Discussion), What's New; no showcase category (V https://community.revenuecat.com/) | A tip thread if useful; no promotion |
| Apple Developer Forums | Code-level questions (S) | Do not use |

---

## 2. Free directories and lists (verified to exist on 2026-10-02)

Only entries I could verify exist now. "Lead time" is stated by the source or marked unknown.

| Directory | Submit | Requirements for us | Accepts paid CLI? | Lead time / cost |
|---|---|---|---|---|
| AlternativeTo | Account, then "Suggest new application" (V https://alternativeto.net/faq) | Fields: platforms, license (Commercial / Freemium), descriptions, tags; email verification. Do not use profiles to advertise; do not incentivize upvotes | Yes: license classes include Freemium and Commercial. Pick "Freemium" only if the free tier performs the main purpose (V) | Free queue "usually sits in our backlog for at least a few months"; optional $5 one-time priority review in 1-2 business days (V). nofollow, DR 80 (S, https://launchdirectories.com/directory/alternativeto) |
| DevHunt | https://devhunt.org , GitHub login for submission (S) | Weekly launches; accepts beta and waitlist products if the site is live and explains the product (S). Wants working demo or repo (S) | Yes, commercial tools are listed (V devhunt.org) | Free; ads cost $149/week banner (V), not needed |
| Uneed | https://www.uneed.best/submit-a-tool (V) | Digital product with a landing page, in English (S). Free launch needs a score of 10 to stay published and 20 to keep the dofollow link (S) | Yes | Free waiting line with auto date; $29.99 to choose the date (S) |
| Peerlist Launchpad | https://peerlist.io (V) | Verified Peerlist profile; launch window opens Mondays and runs the week (S, August 2026) | Yes (S) | Free, one launch per week (S) |
| Console.dev | Email hello@console.dev (V) | See 1.5; criteria are real and demanding (docs, install, dev workflow) | Yes, commercial accepted (V) | ~1-2 weeks editorial (S); no fee; no sponsored reviews |
| Indie App Catalog | https://indieappcatalog.com/app/submit ; has a "Non-App Store" section (V) | Indie Apple-platform apps; developer tools shown on the home page (V) | Likely; cost and criteria not shown (U) | Unknown |
| Indie Hackers products | Free account, Add a Product (S) | URL, description, stack | Yes | Immediate page (S) |
| SaaSHub | https://saashub.com/services/submit | **Rejects waitlist pages, unreleased products and free-subdomain sites (workers.dev would count)**; needs a quality website; Developer Tools is an accepted category (V) | Yes, once on a real domain and released | Approval time not stated |
| Awesome-ASO | PR to README (V repo) | See 1.11 | Lists commercial tools | PR-based, unknown |
| awesome-maestro | PR (V repo) | See 1.9 | Lists a paid cloud already | PR-based, unknown |
| Maestro docs: community articles / projects | PR to mobile-dev-inc/maestro-docs | See 1.9 | Projects page: free/open only today | ~5 weeks (V PR dates) |
| fastlane available plugins | Publish `fastlane-plugin-shotfleet` gem | See 1.10 | n/a | Automatic once on RubyGems |
| Product Hunt | https://www.producthunt.com/launch | Free; see 1.6 | Yes | Same day |
| BetaList | https://betalist.com/submit (login wall; not read) | Secondary sources say all submissions are now paid ($39/$99/$299, refund if not selected) (S, https://smollaunch.com/guides/launching-on-betalist) and conflict on queue length | Pre-launch products are its core | **Not free: skip** |

Not worth it / do not apply:
- **awesome-ios** (https://github.com/vsouza/awesome-ios, 53,495 stars): its CONTRIBUTING.md (V, read from the repo) hard-rules require 100+ stars, an OSI open-source license, more than one contributor, Swift Package Manager support, and "Is not a paid product". Shotfleet fails four. Do not submit. (awesome-swift and awesome-android-ui are for libraries and UI; same logic, not verified individually.)
- **Changelog News**: its submit page says commercial products are not accepted unless sponsored, and no how-to guides (V https://changelog.com/news/submit). A story post might be taken on its own merit (the bug story), not the product.
- **Slant**: forbids vendors from adding their own product and excludes presale products (S). Skip.
- **Capterra / G2**: not our buyer; skipped as instructed.

Order to submit, by lead time: AlternativeTo (months, consider the $5 priority) and Console.dev (weeks) first, once there is a runnable free tier and the real domain; DevHunt, Uneed, Peerlist at launch week; the rest after the first article exists.

---

## 3. SEO

### 3.1 What I could and could not measure
- No keyword volume or difficulty (see method note). To get numbers: authorize the Ahrefs connector, or use Google Search Console on the new domain after 2-4 weeks of impressions.
- What I did check: who ranks for each intent (search results today), and how much content each competitor publishes (their sitemaps).

### 3.2 Competitor content volume (V, sitemaps fetched today)
- ButterKit (https://butterkit.app/sitemap.xml): ~175 URLs: 67 docs, 25 changelog entries, 15 templates, 7 compare pages (vs AppLaunchpad, Picasso, Figma, Helm, AppScreens, alternatives), 2 guides (screenshot sizes, design cheatsheet), platform/category pages.
- AppScreens (https://appscreens.com/sitemap.xml): 67 blog/guide URLs incl. `/blog/appscreens-vs-fastlane`, `/blog/app-screenshot-localization-checklist`, `/blog/how-to-translate-localize-app-store-screenshots`, `/blog/best-app-store-screenshot-tools-2026`, `/blog/how-to-take-app-store-screenshots`.
- Marteso (iOS only, ASO platform with screenshot pipeline) publishes "fastlane alternative" and "frameit vs Marteso" posts (S, https://www.marteso.com/blog/screenshot-pipeline-fastlane-alternative, 2026-06-02). Others (Screenshot Bro, ScreenMagic, ezscreenshots, appstorescreenshotstudio) target "fastlane alternative" and "frameit alternative".
- Lesson: head terms ("app store screenshot sizes", "best screenshot tools 2026", "screenshot generator") belong to vendors with hundreds of pages. Do not write for them.

### 3.3 Search intents and who ranks today

| Intent (query) | Who ranks (search results today) | Our chance |
|---|---|---|
| automate app store screenshots all languages | Medium "Automate App Store Screenshots: 2026 Guide" (AppScreenshotStudio), a GitHub how-to, fastlane docs, Khan Academy blog, Screenshots Pro, AppScreens | Low for the head term; fine as a supporting long-tail |
| fastlane snapshot alternative | appstorescreenshotstudio (frameit alternative), appscreenmagic, ezscreenshots, Marteso, screenshotbro, AlternativeTo "Fastlane Alternatives", a fastlane issue | Medium: all are framing/design tools or iOS-only; none covers Android capture + verification |
| fastlane snapshot wrong language / all English | Only GitHub issues: #8895, #9043, #10846, #11457, #11736, #12917 (and old `fastlane-old/snapshot` issues) | **Good**: the SERP is bug threads, not guides |
| maestro screenshots multiple languages / locale | Maestro docs (locale pages), BrowserStack and TestingBot docs, a Medium post on localized screenshots, a developer's repo PR | **Good**: few tutorials; real gap |
| google play screenshots every language automate | fastlane screengrab docs, proandroiddev, lambdasoup, droidunplugged, screenshots.live | Medium: Android is under-served versus iOS, but Google's own docs rank |
| localized app store screenshots checklist / verify | AppScreens, appstorescreenshotstudio, screenshotbro, appstorelocalization.com, Apple's help page | Medium-hard; we need unique data (our bug list) |
| app store screenshot rejection 2.3.3 | appstorescreenshotstudio, shotluma, almostdone.ai (vendor blogs, marketing tone) | Medium: nobody shows a verified before/after |

Demand evidence for the troubleshooting intents: six fastlane issues on language not applied (above), Maestro #2654 on English-only permission-dialog dismissal (open since Aug 2025, per research/market-2026.md), the morse_app PR above.

### 3.4 Articles worth writing (6-8), in order

All hosted on our own domain, with canonical links on any cross-post. Claims must stay inside what is proven (README, research/roadmap-2026-10.md section 1).

1. **"Why your fastlane snapshot screenshots are all in English (and how to check every language in 30 seconds)"**. Intent: snapshot language not applied. Angle: the real causes (launch arguments vs simulator locale, `localize_simulator` status-bar side effect per issue #11457), then a free verification step: `shotfleet check fastlane/ --app MyApp.app` (the free command). Why we win: the SERP is only issue threads; we offer a diagnosis plus a tool that is free for this use.
2. **"Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps"**. Intent: maestro multiple languages. Angle: tutorial with both platforms, port 7001 sharing on Android parallel runs, the env-precedence trap in 2.10 (cite the PR), `--device-locale` limits. Why we win: only docs and a few Medium posts exist. Test every snippet on the Maestro version we state (roadmap risk R1: only 2.0.10 was run; 2.11 is current).
3. **"The first run found a button nobody could reach" (founder story)**. Intent: long-tail "next button off screen Japanese Android small phone", plus shareable story for HN, newsletters, Reddit comments. Angle: ja/ko/zh/ar onboarding on a small Android phone, the review grid image, the two-line fix. Why: true, specific, evergreen, link-worthy. Needs the actual grid screenshot with permission-safe app content.
4. **"Localized app store screenshots QA checklist: 10 ways a localized listing is wrong"**. Intent: localization checklist, 2.3.3 mismatch. Angle: only failures we actually saw (copies of the English set in every folder, Chinese captions over an English app, size/count/alpha rules, a language with no translation) plus Apple/Google spec links. Why: competitors' checklists are generic; ours is data-backed. Medium-hard.
5. **"Automating Google Play screenshots in every language with emulators and fastlane supply"**. Intent: Play screenshots all locales. Angle: per-app locale needs API 33+ (README), Play limits (min 2, max 8, 320-3840 px per Google's page, see research/market-2026.md section 3), parallel emulators. Why: Android coverage is thin; we can show 15 min for 18 languages (README) with the honest setup cost.
6. **"fastlane snapshot alternatives in 2026: an honest table"**. Intent: fastlane snapshot alternative. Angle: free options first (snapshot/screengrab, Maestro `--device-locale`, StoreScreens, asc CLI, simshot), then framing tools (ButterKit, AppScreens) as complements, then shotfleet, with a "when not to buy this" column. Why: honest comparison pages are linked and quoted; but this SERP is contested by vendors, so rank 6th. The draft exists at site/draft/alternatives.html (unpublished).
7. **"iOS permission alerts stay English while your app is German: what that does to UI-test taps"**. Intent: Maestro permission localization (cite issue #2654). Angle: our measurement on `main` with Maps (roadmap section 1), the `launchApp: permissions: all: allow` workaround from the README. Why: tiny, precise, nobody else measured; good for newsletters.
8. **"Plural forms in screenshot flows: 'Round 2 of 12' in Arabic, Russian and Polish"**. Intent: niche; mostly link bait for the localization crowd. Angle: CLDR plural categories (Arabic 6, Russian 4, Polish 4, Japanese 1, https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html) and how the tap selector matches every form (README). Lowest priority.

Blocked until proof exists: a "Flutter / React Native localized screenshots" article. Readers loaded real translation files but no real Flutter/RN app was run (roadmap section 1). Write it only after one real run.
Do not write: "app store screenshot sizes 2026", "best screenshot tools", "screenshot generator": vendor territory.

### 3.5 On-site prerequisites (observed in site/public)
- `<title>` is "shotfleet - localized store screenshots"; meta description and canonical exist; canonical points at the workers.dev host.
- `robots.txt` allows all but has no `Sitemap:` line; no `sitemap.xml` was found in site/public.
- alternatives page is in site/draft, not published. No article section yet.
- Anonymous funnel counter exists (analytics.js sends view / pricing / cta / runs with utm_source or referrer host to /api/hit).
- Move to a real domain before building backlinks; a workers.dev address also blocks SaaSHub and looks temporary on HN. Binary and install.sh contain the current URL (roadmap R6): do the move before release.

### 3.6 AI search
No verified data on whether LLM assistants cite small dev-tool sites. Low-cost hygiene that costs nothing: a clear one-paragraph definition on the home page, a plain-text README-like docs page, and the comparison table in text (not images).

---

## 4. Founder-led content and how comparable tools got early users

### 4.1 True stories we already have (each needs its proof asset; claims limited to proven items)

| Story | Source in repo | Where it fits | Caution |
|---|---|---|---|
| The unreachable Next button in ja/ko/zh/ar on small Android phones | README, marketing/launch-posts-v2.md | Show HN, blog #3, newsletters | App is CrossfitTracker in README but "WOD Tracker" on the site (roadmap R5): use one name |
| Turkish "Next" and "Advanced" are both "Ileri": the tool warns before running | README (collision warning) | X thread, blog #2 | Fine |
| Translated captions over an English app (Traditional Chinese listings) found in committed fastlane folders | README (check section) | Blog #4 | Say it was found in the author's own committed screenshots |
| The OCR step: macOS text recognition's ANECompilerService sometimes hangs until restart; first compile takes 30 s to minutes; Tesseract fallback | README Limits, research/market table | HN comment, short post "why my OCR step hung" | Details only Manu holds; keep it to what he measured |
| iOS permission alerts are drawn in device language (stays English) | roadmap section 1 (measured with Maps) | Blog #7 | Do not claim live permission-alert taps (launch-posts rule) |
| Parallel Maestro on Android: two `maestro test` processes on different devices share host port 7001 | launch-posts-v2 (Maestro Slack post) | Maestro Slack, blog #2 | Re-verify on the Maestro version we recommend |
| Plural forms and numbers in labels ("Round 2 of 12") matched in every plural form | README Limits | Blog #8 | Fine |
| 18 languages x 4 screens: iOS 534 s, Android 15 min 24 s | README, roadmap | Everywhere as one number set | One app, Maestro 2.0.10 only: say so |
| Solo-founder honesty: no company registration, Polar as merchant of record, price reasoning | research/pricing-2026-10.md, LAUNCH.md | Indie Hackers post | Do not publish tax or personal details; Manu decides |
| Timed head-to-head fastlane vs shotfleet on one app | STRATEGY.md proposes it | Blog + Show HN follow-up | Not done yet as far as I can tell: do the measurement before claiming |

### 4.2 Comparable launches and what is actually documented

| Tool | What is documented | Takeaway for us | Source |
|---|---|---|---|
| DevUtils.app (paid Mac dev utility) | Show HN 2020-09-28: 241 pts / 105 comments; open source with a paid prebuilt version; Mac App Store listing requested in comments and live within days; $9 one-time; later $100 MRR on the Mac App Store by 2021-09-05 per the founder's Indie Hackers page (S) | A paid Mac dev tool can do well on HN when people can try or read it and distribution friction is fixed fast | V https://news.ycombinator.com/item?id=24604291 ; S https://www.indiehackers.com/product/devutils-app |
| RocketSim (Antoine van der Lee, Simulator tool) | Blog since May 2017 (140,000 unique monthly visitors, 20,000 newsletter subscribers by Sep 2024); first sponsorship deal Aug 2019; launched the app in 2019 to his own audience: "he realized he had his audience ... and could just send an email to them" (paraphrase); roughly $62K ARR end of 2023, approaching $100K at the 2026 interview; active trials rose from 40 to 120 a day after shipping the top-voted feature (a public roadmap with user votes) | The winning path was years of audience first. We have none, so the substitutes are niche communities and search | V https://www.fakemayo.com/p/growing-a-blog-about-swift-to-140k-visitors-per-month ; V https://www.revenuecat.com/blog/growth/antoine-van-der-lee-rocketsim-launched-podcast-2026/ ; S RevenueCat case study |
| ButterKit (direct competitor; frames, localization, upload) | Solo founder; App Store listing dated 2026-05-18 (S snippet); free tier plus one-time Pro; the site invests in docs (67 pages), a changelog (25 entries) and compare pages; listed on many launch directories (EarlyHunt, PeerPush, ShinyLaunch, Startuups, ShipyardHQ, The Hack Stack per search results); the founder says he built it for his own apps. **No first-100 figure found** | Content volume plus directories plus a generous free tier, not a viral launch. Price listings differ by channel: Mac App Store shows Pro $19.99/yr or $49.99 lifetime in one snippet while its site shows $99 (S: verify before using in copy) | V https://butterkit.app/about/ ; V sitemap ; S https://apps.apple.com/us/app/butterkit-screenshot-studio/id6751829199 |
| Shotbot (framed screenshots, indie app) | Soft launch with friends and family devices, then Mastodon posts from a public build; prototype in 3 days, ~3 months to release mostly due to Apple developer account issues. No user numbers | Build in public on Mastodon is a real small-scale channel for Apple indies | S https://indieappspotlight.com/p/issue-1-shotbot (page returned 522; from search snippet) |
| asc CLI (free, MIT) | 7,577 GitHub stars, created 2026-01-20, release 5.9.1 on 2026-10-01 (GitHub API); 23 agent skills in the docs | Free + agent-friendly + frequent releases build a following fast; we will not out-free it, so we integrate (run its upload) | V GitHub API ; S https://asccli.sh/ |
| StoreScreens CLI, appshot, simshot (free, small) | 27 and 26 stars, simshot copies 0-17 stars (GitHub API) | A free capture tool alone does not attract a crowd; the field is wide open for verification, but also nobody is loud | V GitHub API |
| Maestro itself | HN 185 pts / 66 comments on its post; adopters named in the thread (Meta, Block, DoorDash, Stripe, Disney per the founder) | Our buyer pool is people already adopting Maestro | V https://news.ycombinator.com/item?id=43174453 |
| 1000 Pound Club (not a dev tool) | First 100 users: Reddit 60, Discord 25, Indie Hackers 15, Twitter 0, Hacker News 0 (first week of September 2023) | Niche communities beat general tech sites when the product is niche | V https://www.indiehackers.com/post/how-i-got-my-first-100-users-2fc9d71c34 |
| Sensei (Cindori, Mac utility) | AMA: organic search first, press releases to Apple-ecosystem blogs, own newsletter; no numbers | Search plus press, again no virality | V https://www.indiehackers.com/post/i-grew-my-revenue-to-300-000-as-a-solo-indie-mac-developer-ama-c200c97cfc |

Honest conclusion: the documented routes to a first hundred are (1) an owned audience, (2) niche communities, (3) one good HN moment, (4) search over months. Shotfleet has none of (1) and can start (2) and (4) now. Treat a 50-sales-in-60-days target (STRATEGY.md) as a hypothesis the next 6 weeks will test, not as something this research supports.

---

## 5. Partnerships and outreach

Only organizations and public routes; no individuals named beyond what a publication's own page states. Priority order by fit.

| Who | Audience | Realistic ask | Angle | Route |
|---|---|---|---|---|
| Maestro (mobile.dev) community: Slack, awesome-maestro, docs articles | People hitting the locale gap | (1) Answer locale questions in `#maestro-questions`; (2) a tutorial link in community articles; (3) a listing in awesome-maestro; (4) ask whether paid tools may appear in community projects | "Maestro cannot set the locale in a flow; here is a documented way, and a tool if you want it automated" (be an add-on; never position against Maestro, per STRATEGY) | https://slack.maestro.dev/ ; PRs to https://github.com/mobile-dev-inc/maestro-docs and https://github.com/ludovicobesana/awesome-maestro |
| Android Weekly, Kotlin Weekly, KMP Weekly | Android, Kotlin, Compose Multiplatform developers | One link to article #5 or #3 | Compose Multiplatform proof (Kuokka, HackerNewsKMP) and Android per-app locale | Section 1.5 routes |
| iOS Dev Weekly, SwiftLee Weekly | Apple developers | One link to article #1 or #7 (not the product) | Specific measurements (permission alerts, hanging OCR service) | Section 1.5; add our blog to the iOS Dev Directory first (the form's own advice) |
| Console.dev | Dev tool evaluators | A tool review | Free tier, CLI, JSON/exit codes, docs | hello@console.dev |
| Indie Dev Monday | Indie app developers | A spotlight on Manu and the story of his apps, not a pitch | "I build the tool for my own 18-language app" | Form / newsletter@indiedevmonday.com |
| ButterKit, AppScreens (framing tools) | Same buyers one step later | Cross-link recipe: "capture with shotfleet, frame with X"; their import formats | Complements, not competitors (STRATEGY says so) | Their contact pages; cold, low odds. Neither lists a partner program for tools that I could verify (U) |
| asc CLI project (App Store Connect CLI) | iOS developers using agents | Recipe: `shotfleet export` then `asc screenshots upload` | Same | GitHub issues/discussions on https://github.com/rudrankriyam/App-Store-Connect-CLI |
| fastlane (Mobile Native Foundation) | fastlane users | Publish a `fastlane-plugin-shotfleet` gem; an article for the fastlane community | Fills the "verify" gap fastlane does not cover | RubyGems; MNF GitHub org (https://github.com/MobileNativeFoundation) |
| Crowdin Store, Lokalise Apps, Phrase partners | Teams translating strings in a TMS | An integration guide: "after pulling translations, verify them in screenshots"; a store listing is a poor fit because those are web apps | Needs traction before a partnerships person replies | Crowdin: https://store.crowdin.com/pages/publish ; Lokalise: partners@lokalise.com then review form (V https://developers.lokalise.com/docs/lokalise-apps) ; Phrase: https://phrase.com/partners (Verified Solution) ; Tolgee: public Slack and GitHub (S) |
| ASO Stack (Phiture) | ASO professionals, agencies | One `#promotion` post; offer the done-for-you run to consultants for clients | Verification and localized captures | Slack invite via https://phiture.com/aso-stack-slack-community/ |
| RevenueCat community, Launched podcast, Sub Club | Indie and subscription app developers | A tip thread; no pitch | Hold until a customer story exists | https://community.revenuecat.com/ |
| RevenueCat Shipaton 2026 | Developers who just shipped a new app | Build window Aug 1 to Sep 30, awards Oct 22 (V https://revenuecat-shipaton-2026.devpost.com/); the `#ShipatonSale` route for tools is moot now that submissions closed | Observation only: hundreds of freshly shipped apps need store assets; speculative | n/a |
| Localization agencies | Teams outsourcing translations | The $149 done-for-you run (marketing/done-for-you.md) as a service they resell | Needs a case study first | Not verified which agencies accept; (U) |

Expected outcomes are low until there is a case study with a real customer's permission. Ask once, offer something useful, accept silence.

---

## 6. Pre-launch, launch, post-launch: what a solo founder can do honestly and cheaply

### 6.1 Next two weeks (2026-10-02 to 2026-10-16), before the sale opens
Ordered by value per hour.

1. **Decide and buy the domain; point the site, canonical, binary update-check and installer at it** (roadmap R6). Everything below builds links to it. Add `sitemap.xml` and a `Sitemap:` line to robots.txt. (~2 h)
2. **Publish three articles on the new domain**: #1 (snapshot stuck in English), #2 (Maestro locales), #3 (the unreachable button). Search indexing takes weeks, so start now; each must contain a copy-paste step that works. (~2-3 days of writing and testing)
3. **Record the 60-90 s demo** and save the review-grid image with the red outlines. These two assets feed every channel. (~2 h)
4. **Fix the credibility gaps HN will find** (roadmap R5): README CI recipe runs `python3 shotfleet.py` though source is private; "Apple silicon only" is not on the site; WOD Tracker vs CrossfitTracker naming; state the tested Maestro version. (~half a day)
5. **Join `#maestro-questions` and answer locale questions** with no link for the first week. Ask there whether the community-projects page lists paid tools. (15 min/day)
6. **Post the build story on Mastodon (iosdev.space), Bluesky and X** with the grid and no price. Use `?utm_source=` tags (the funnel counter reads them). (30 min/week)
7. **Open the AlternativeTo listing now** (months in queue; consider the $5 priority; license "Freemium"), and email Console.dev when a free tier installs. Do not submit directories that reject waitlists (SaaSHub, Slant) until the site is live and on the domain. (1 h)
8. **Recruit 3-5 design partners from real asks** (people who post a locale/screenshot problem publicly and say yes): give a free full licence for an honest write-up or quote. Written permission before any quote; no testimonials from anyone who has not used it. The done-for-you offer (marketing/done-for-you.md) is the same idea at $149.
9. **Add a live "founder price: N of 100 left" counter** from Polar's FOUNDER29 redemptions at launch. It is the only urgency that is true. (1 h; do it with go-live)
10. **Do not** run a Show HN before the free tier installs; a waitlist page does not qualify (V).

### 6.2 Launch week (after Polar approves and `go-live.sh` has run)
Sequence, not a blast:
- Day 0: email the waitlist (marketing/launch-email.md); Indie Hackers product page and one story post; r/macapps once if the rules still say so and it fits.
- Day 1-2: Show HN (title "Show HN: One English Maestro flow, every language your app ships, checked"), first comment with backstory, limits and pricing as in launch-posts-v2.md; answer for the next several hours.
- Day 2-7: DevHunt, Uneed, Peerlist; submit article links to Android Weekly, Kotlin Weekly, KMP Weekly, iOS Dev Weekly; Maestro slack announcement only if `#maestro-questions` rules allow; r/SideProject build story if its sidebar allows.
- Replace the planned r/androiddev and r/reactnative posts with answers in existing threads.

### 6.3 After launch (weeks 2-6)
- Publish articles #4-#7 one per week; each links to a free command (`check`).
- Maestro docs PRs (community articles first); fastlane plugin gem; Awesome-ASO and awesome-maestro PRs.
- Follow-up Show HN only for a genuinely new thing (head-to-head benchmark, Flutter/RN real run, CI recipe actually run).
- Collect two case studies with written permission.

### 6.4 What to measure
Existing instrumentation: waitlist signups with source (site/worker.js), anonymous page counters by source and day (`view`, `pricing`, `cta`, `runs`), Polar orders and FOUNDER29 redemptions, refunds and licence activations.
Measure, by channel (utm tag):
1. Visits, pricing views, CTA clicks (existing).
2. Installs (check whether install.sh / download hits are counted; I did not verify) and free-tier first run reached.
3. Free tier to paid: orders divided by installs, per channel.
4. Activations per order, refunds in 14 days, and the stated refund reason.
5. Support emails per buyer and time to first successful run (the friction that causes refunds, roadmap R4).
6. Questions asked in public threads (research data: what people ask, not just how many).
Keep the decision rule as written in STRATEGY.md (50 sales at $29 within 60 days keeps investing; under 15 means a free/open tool). This research gives no basis to forecast conversion; the DocAPI anecdote (800 visitors, ~40 signups, 12 paid in 2 weeks) is one unrelated data point.

---

## 7. Do-not-do list

Spam patterns that get a solo founder banned or ignored:
- **Posting the same text to several subreddits or Slack channels** (the Kotlin Slack guideline calls cross-posting spam; r/androiddev, r/reactnative and r/iOSProgramming restrict promotion, per third-party rule directories). Do not run the single "alternating platforms" post in launch-posts-v2.md without reading each sidebar and asking mods.
- **Drive-by link drops, promo-only accounts**: iOS Folks deletes posts when "your only posts are ones promoting your own work"; Reddit playbooks say to build 2-6 weeks of activity first (S).
- **Soliciting upvotes, comments or votes** on HN (guidelines forbid it; HN detects voting rings, S), Product Hunt (rule: cannot ask for upvotes), or AlternativeTo (incentivizing upvotes with discounts may drop the app in ranking, V).
- **Using AlternativeTo or Slant user profiles to advertise** (AlternativeTo blocks such accounts, V; Slant forbids vendors editing their own product, S).
- **DMing people from Slack or forums** (ASO Stack prohibits solicitation in DMs, V; iOS Folks prohibits unsolicited marketing DMs, V).
- **Product links in GitHub issues** on fastlane or Maestro threads that are not about the product (my judgment, no rule cited): answer the question and mention the tool only when asked or when the tool is the answer, with disclosure that you built it.
- **Paid upvote or "launch crew" services** (an opinion piece cites $500+; S): not worth it and against the rules above.
- **Paid ads and sponsored newsletter slots now**: at $29 the net is about $27 after Polar's 5% + $0.50 (research/pricing-2026-10.md; international and payout fees extra). I found no verified CPC for our keywords and no published newsletter prices (Android Weekly and SwiftLee Weekly list none; DevHunt banners are $149/week, V). Revisit when conversion by channel is known.
- **Fake urgency or social proof**: no resetting countdown timers, no "only X left" that is not the live FOUNDER29 count, no testimonials or logos without written permission and real use, no invented numbers (the sample numbers in vendor blogs here are not ours to repeat).
- **Overclaiming the product**: do not claim Flutter, React Native, MAUI or Unity runs (only sample files were run), live permission-alert taps, frames, captions, store upload, Android tablets beyond what is shipped, or "catches all localization bugs"; do not say "Maestro partner" or imply Maestro endorses it.
- **Quoting "Maestro's docs say one flow per locale"**; the current page recommends tags plus `--device-locale` (re-read it and quote exactly, or leave it out).
- **Launching a Show HN with a waitlist page**, or before the free tier installs on a clean Mac.
- **Submitting to awesome-ios** (hard rules exclude paid and closed-source tools; the PR will be closed) and to BetaList expecting free listing (reported as paid-only).
- **Burning the founder-price list**: mention $29 once per post and once in the launch email.

---

## 8. Open items I could not verify (for Manu or a later pass)

| Item | Why open | How to settle |
|---|---|---|
| Current text of every subreddit's rules (iOSProgramming, androiddev, FlutterDev, reactnative, swift, SideProject, macapps, ASO, kotlin) | Reddit blocked to tools; rule directories disagree for r/SideProject | Read each sidebar and wiki in a browser; screenshot the rule you rely on |
| Keyword volume and difficulty | Ahrefs/Similarweb connectors not authorized in this session; no free API | Authorize the Ahrefs connector in claude.ai settings, or watch Search Console for 4 weeks |
| Android Weekly's exact submit URL | `/suggest` is 404; page says "Submit" in nav | Click Submit on androidweekly.net |
| Whether Maestro will list a paid tool on the community-projects page | Page lists only free tools, no submission text | Ask in Slack or open an issue before a PR |
| BetaList pricing and queue | Login wall; secondary sources conflict | Open betalist.com/submit in a browser |
| Rules of Indie Hackers posting, dev.to, ProAndroidDev, Slack workspaces of Maestro and Kotlin (promotion) | Not found | Read in each |
| Whether install.sh downloads are counted | Not checked in worker.js | Read site/worker.js; add an event if missing |
| ButterKit's Mac App Store vs website pricing | Snippet vs site conflict ($19.99/yr or $49.99 lifetime vs $99) | Re-open both before any price comparison in public copy |
| Subscriber counts for iOS Dev Weekly, KMP Weekly, Flutter Developer Weekly, Indie Dev Monday | Not published on pages read | Use as unknown |
| Podcast/YouTube guest routes | Not found | Skip for now |
