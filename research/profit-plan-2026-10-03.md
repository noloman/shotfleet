# What would make shotfleet more complete and profitable (2026-10-03)

Question asked: investigate what else we can do to create a better, more complete product, and a sellable one we can profit from.
Method: the repo's own plans (STRATEGY, ROADMAP, STATUS, research/market-2026, pricing-2026-10, roadmap-2026-10, gumroad-setup) were read first and not redone. Four
research threads then looked for what is new or missing: platform and competitor moves, demand and willingness to pay, adjacent uses of the same engine, and
distribution. Reddit and Stack Overflow were not reachable; much of the web evidence was read through summarisers. Tags: **[P]** primary page read,
**[S]** secondary or summarised, **[E]** my estimate, **[U]** could not verify. Where two sources disagree it says so.

## 1. Bottom line

1. **As scoped, shotfleet is a good side income, not a business.** Net per sale on Gumroad is $24.46 at $29 and $41.88 at $49. Year one lands between about **$700 and
   $15,000, most likely about $3,000** [E, section 3]. The earlier $3,000-a-year goal is realistic, and not much more than that on the current shape.
2. **The bottleneck is reach, not features.** Nobody knows the product exists: an empty waitlist, no audience, a niche where the best comparable launches got 1 to 5
   points on Hacker News [P]. The successful comparables (RocketSim, Screen Studio) either had an audience first or are broad-appeal tools [S].
3. **Nothing found makes the product unnecessary.** Apple's WWDC26 work (Asset Library, Product Page Preview) and Google's I/O Gemini features are about upload, preview and
   listing *text*; neither captures the real app in each language or verifies it [P]. Maestro still has no per-flow locale feature [P]. Nobody sells "one Maestro flow, selectors
   rewritten from the app's own strings, then verified" [S].
4. **The one way to a materially bigger outcome is a continuing use, not a one-off one.** Store screenshots are needed a few times a year. Localization QA on every release
   (clipped text, untranslated strings, wrong language, pseudo-locale layout) is continuous, fits a per-repo CI licence, and has no mobile-specific product under about $199 a
   month [S]. The demand for it is **unproven**, so the plan below tests it before building it.
5. **Do not build first. Launch, measure, then build what the first buyers and the Team waitlist ask for.** The remaining blockers to a first sale are in STATUS.md (money
   path, published release, a real key, cold test); none of them is a missing feature.

## 2. What the new evidence says

| Finding | Evidence | What it means |
|---|---|---|
| Apple adds Asset Library, Product Page Preview and an ASC API for assets this fall; nothing generates or translates screenshots | developer.apple.com/wwdc26 guides and the Apple newsroom, June 2026 [P]; the API detail is [S] | Upload and preview move to Apple. Capturing and checking stay ours. Plan a hand-off recipe once the API is documented |
| **Xcode 27 final (14 Sep) replaces Simulator.app with Device Hub**; agents in Xcode can boot simulators, drive an app and take screenshots | Apple session 258 [P]; Michael Tsai's page not read [S] | **Real risk to verify before selling:** shotfleet drives `simctl`. The dev Mac has an iOS 27 runtime, but no record says which Xcode the real runs used. Run the fixture e2e on Xcode 27 final |
| Apple banned alpha channels in screenshots on 8 Jul; new sizes on 9 Sep (iPhone Duo, 18 Pro, Watch Ultra 4 / Series 12) | ASC release notes [P] | `check` already rejects alpha. The Duo sizes (1398x2034 outer, 2007x2853 inner) were missing from the size table; **added in this change** (uploads open "later this year") |
| Google Play I/O 2026: Gemini fills listing text, translates subscription benefits, makes custom listings. Nothing on screenshots | Android Developers blog [P] | Text is being automated, screenshots are not. Mismatch (translated text, English screenshots) becomes more likely, which is what `check` finds |
| Maestro 2.9 to 2.11: dark mode commands, better locale reliability. No per-flow locale | maestro.dev changelog [P] | Maestro keeps investing in locale *reliability*, which helps us. Stay an add-on |
| fastlane is community-maintained (Mobile Native Foundation), snapshot has no new locale or parallel work | GitHub releases [S] | The default is in maintenance mode: an opening for "one flow, both platforms" |
| **asc CLI** already captures, checks sizes and uploads multi-locale screenshots, free, weekly releases; no language or duplicate check | docs.asccli.sh [S] | The closest overlap. It could add checks. Our moat is the depth of the check and Android, not capture |
| Agents (Claude Code, Codex, Xcode 27) can DIY capture; the framing CLI `appshot` was archived in July with "use Claude or Codex" | GitHub [S] | Capture is becoming free; deterministic verification is the part an agent does unreliably. Keep selling the check |
| Competitor prices: AppScreens $99 to $180 a year; ButterKit one-time (**$99 on its page when read on 2 Oct [P]; one source says $79, another $40 to 60**); AppLaunchpad $15 to 29 a month | vendor pages [P/S] | $29 to 49 one-time is not out of line. Pricing in this space is mixed one-time, subscription and credits |
| Mobile visual / locale QA: Applitools from about $667 a month, App Percy $199 a month, Drizz (funded, 2026) pricing undisclosed | vendor pages [P/S] | A gap between free scripts and $199+ a month for mobile locale QA. Demand for a cheap version is **[U]** |

## 3. The money, with the arithmetic

Fees (Gumroad direct link: 10% + $0.50, plus card processing 2.9% + $0.30; research/gumroad-setup.md). VAT is passed through. Dutch income tax is **not** modelled.

| Price | Net per sale | Sales for $3,000 | for $10,000 | for $30,000 |
|---|---|---|---|---|
| $29 (founder) | $24.46 | 123 | 409 | 1,227 |
| $49 | $41.88 | 72 | 239 | 716 |
| $99 | $85.43 | 35 | 117 | 351 |
| $149 | $128.98 | 23 | 78 | 233 |
| $199 | $172.53 | 17 | 58 | 174 |

**Audience size [E, stacked guesses, off by 2 to 3 times either way].** 1.15 million App Store publishers (42matters, 3 Oct 2026 [S]) x about 25% still shipping x 5 to 10%
with 10+ languages x about 50% small teams = 7,000 to 15,000 potential buyers; x about 15% on an Apple-silicon Mac who would adopt a Maestro-flow workflow = **roughly 1,000 to
2,200 reachable**. No source gives the share of apps with 10+ localizations (not found).

**Year one** (visits x visit-to-purchase; the traffic and conversion inputs are assumptions with no source for this niche; the research found only signup-style benchmarks):

| Case | Visits | Buyers | Net |
|---|---|---|---|
| Pessimistic | 2,000 x 1.5% | 30, all at $29 | about $730 |
| Base | 6,000 x 2% | 120 (100 at $29, 20 at $49) | about $3,280 |
| Optimistic | 15,000 x 2.7% | 400 (100 at $29, 300 at $49) | about $15,000 |

(The demand thread computed these with lower fees and got $800 / $3,600 / $16,300; the table above uses the real Gumroad fees.)

Signals that temper the optimistic case: fastlane's whole Open Collective has raised **$190 from 13 people** [P], so the exact audience rarely pays for tooling; and a one-time price
with a year of updates gives little renewal income. Signals for it: a manual run costs 10 to 30 hours per release by one developer's account [S, vendor-adjacent blog], and
the audience is paying $99 to $180 a year for framing tools.

## 4. Levers that move the number, ranked

| Lever | Effect | Evidence | Cost | Verdict |
|---|---|---|---|---|
| Reach: free channels in section 6 | Multiplies everything; 2,000 to 15,000 visits is the whole uncertainty | Channel facts [S/P] | Manu's time | **Do first** |
| Team / CI licence per repo (about $149 a year) | $149 is 3.1 times the net of a $49 sale; 20 teams = about $2,600 | STRATEGY says teams ask for CI first; no price evidence [U] | S to build the licence; the CI action M | **Test by waitlist, build on signal** |
| Locale QA as a continuing use (section 5) | Turns a yearly need into a per-release need; widens buyers to apps *preparing* to localize | Pain [S]; nobody under $199 a month [S]; demand [U] | M | **Validate first** |
| Done-for-you run at $149 per app (roadmap X7) | 22 orders = $3,000 net; costs about 2 hours each | Already planned | Manu's time | Keep as a capped side offer |
| Affiliates: 30% link to 5 to 10 people who write about fastlane or Maestro | Pays only on sale; clawed back on refund | Gumroad mechanics [S]; no norm found | None | Do, small |
| Raise to $79 after the founder 100 | $68 net vs $42 | One indie anecdote of a small rise with unchanged conversion [S] | None | Test, do not assume |
| Subscription instead of one-time | Recurring, but high friction for an indie CLI | Competitors mix models [S] | Medium | No. Keep one-time with optional paid updates |
| Open-source the check engine | Discovery: the rival tools in this ecosystem are all MIT; registries want a package | Registries need an npm/Docker target [S]; fastlane donations show little revenue | Decision | Keep closed for launch; revisit at the day-60 gate (STRATEGY risk row) |
| Paid sponsorships (iOS Dev Weekly is about EUR 2,500 an issue, sold out until December) | One issue costs about 70 sales of net | iosdevweekly.com/sponsorship [P] | Cash | **No** |
| MCP marketplaces that pay | Fewer than 5% of servers are monetised; no per-developer data | [S] | Low | List for discovery only, do not count on revenue |

## 5. Product: what makes it more complete

What is already strong (README, STATUS): one English flow for both platforms, parallel capture, a deep check (language from the app's own text on iOS, copies, missing,
store size and count rules, store listings in languages the app lacks), fastlane export, an MCP server and a Claude skill, `doctor --fix`. What the research says is missing, in order:

| # | Addition | Why (evidence) | Effort | Differentiation |
|---|---|---|---|---|
| 1 | **Verify on Xcode 27 final / Device Hub / iOS 27** | Simulator.app is replaced; every buyer will have it | S (a Mac and an hour) | Prevents a launch-day failure |
| 2 | **Layout check: clipped or ellipsised text, text still in the source language** | Truncation is the best-documented localization bug [S]; the code has **no** truncation or overflow check (searched) | M | Applitools-style AI is the only mobile option today and costs $667 a month [P] |
| 3 | **Pseudo-locale pass:** run the same flow with Xcode's double-length strings and Android's en-XA / ar-XB | Needs no translations, so it also serves apps that have *not* localized yet, which widens the market beyond "10+ languages" [E, my inference]; pseudolocales are a developer-side tool, not a CI step [S] | S to M | Nobody wraps it around a flow |
| 4 | **CI: a GitHub Action and a fastlane plugin** | STRATEGY item 2.2; teams ask first; unlocks the Team licence | S to M | Table stakes |
| 5 | Baseline per locale: fail a PR when a screen drifts | Needed to make 2 and 3 a *continuing* check | M | Competes with App Percy at a fraction of the price |
| 6 | Push source-language screenshots to Crowdin / Lokalise / Phrase via their public screenshot APIs | APIs exist [P]; on iOS the app's own text gives exact string matches with no OCR; **paid demand [U]** | S to M each | Add-on, not a product |
| 7 | Hand-off to Apple's Asset Library API | Ships this fall; docs not read [S] | S | Removes a manual step |
| 8 | Android `run` on Linux (experiment E1) | Android-first teams on Linux CI | M | Widens the audience; needs a KVM machine |
| 9 | Keep store specs current (Duo added now) | Apple changed specs on 8 Jul, 19 Aug, 9 Sep [P] | S per change | Credibility of `check` |

**Not worth building now** (the evidence points the same way as STRATEGY): frames and captions (crowded, `appshot` archived, agents replacing framing CLIs), store upload,
a hosted service (Apple's licence terms), enterprise features such as SSO and audit logs (no evidence anyone would pay a solo vendor for them), selling to localization agencies
(long relationship sales; no agency found buying a screenshot-verification tool [U]).

## 6. Getting the first 100 buyers at zero budget

From the distribution thread; sequence from day 0 = the sale opens. Free routes only. Several submission details were not verified against the live forms.

| Day | Action | Note |
|---|---|---|
| 1 to 2 | List the MCP server in the official MCP registry (Smithery and Glama take separate submissions); submit the Claude skill to the skill directories | The registry stores metadata only: it needs an npm or Docker target, so a thin wrapper may be needed [U] |
| 3 to 10 | Write two tutorials: "Maestro screenshots in 10 languages, iOS and Android" and "fastlane screengrab / snapshot locale not changing: why, and what to do" | These match real open fastlane issues (#11696, #8895, #21385) [P]; answer those threads helpfully, with disclosure |
| 8 | Join the Maestro Slack; post only where it answers a question; open a PR on the docs' community-projects page, which has no screenshot entry [P] | |
| 12 | Email Indie Dev Monday with the one-person story | Free; the founder is a fastlane co-creator [S] |
| 14 | Submit the tutorials (not the product page) to Kotlin Weekly (22,907 subscribers per the agent's read [S]), Android Weekly, SwiftLee Weekly, iOS Goodies | They want articles |
| 21 | Offer a 30% Gumroad affiliate link to 5 to 10 people who write about fastlane or Maestro | |
| 28 | Show HN on a Tuesday to Thursday morning US time, titled around the Maestro / MCP angle | Expect a few hundred visits, not a launch [P: 1 to 5 points is typical] |
| 30 | Count which channel sent buyers; drop the rest | |

Skip: paid newsletter slots, a generic "screenshot maker" Show HN or Product Hunt, and acquisition outreach to Maestro or fastlane (no precedent found).

## 7. Cheap experiments before any new build

Run them on the same visitors, inside the 60-day window STRATEGY already defines. Thresholds are my proposals [E], not data.

| Experiment | How | Build it if |
|---|---|---|
| Is there a Team / CI buyer? | A "Team and CI, $149 a year per repo" block on the site with an email box and one question ("what would you check in CI?"). No checkout | 15 or more emails, or 3 replies naming layout or CI needs |
| Is the layout check wanted? | Ask every buyer and every support mail one line: "what did shotfleet miss?". Count mentions of clipped text, overflow, RTL | 5 mentions |
| Do cheaper screenshots sell to non-localized apps? | Put the pseudo-locale idea in the Team block and in one tutorial; count clicks | Clicks per visit comparable to the main call to action |
| Price headroom | After the founder 100, show $79 to half of visitors (or just raise it and watch) | Conversion drops by less than half |

Kill rule from STRATEGY stays: fewer than 15 sales in 60 days means a free tool and the benchmark as a reputation piece.

## 8. Risks and what stays unverified

- **Xcode 27 / Device Hub** can break the iOS path (section 2). Highest-priority check on a Mac.
- **asc CLI adds language and duplicate checks.** Then depth of checking, Android and one flow for both platforms are the moat.
- **The audience estimate and the traffic and conversion inputs are guesses.** The two Show HN data points (Screen Studio about $30,000 in a month, self-reported 2022) and RocketSim (audience first) are outliers.
- **Not found at all:** any share of apps with 10+ localizations; any ButterKit or AppScreens user or revenue count; any price a team would pay for a mobile locale check; any developer quote about what they would pay.
- Reddit and Stack Overflow were not reachable, so pain-point evidence skews to GitHub issues and vendor pages.
- Fee, tax and entity questions are unchanged: Manu's registration question (STATUS gate 4) still sits ahead of the first payout.

## 9. Decisions for Manu

1. Launch first and test Team demand with the waitlist block (recommended), or build the layout check first? The research favours launching first.
2. Keep the code closed for launch, or open the check engine to get discovery? Revisit at day 60.
3. Approve the free-channel plan in section 6, which means public posts by Manu.
4. Whether to keep the $149 done-for-you offer given the time it costs.
