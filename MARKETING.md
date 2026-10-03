# shotfleet marketing plan

Written 2026-10-02 from research/marketing-research.md (channels, rules, SEO), STRATEGY.md, research/roadmap-2026-10.md and research/website-localization.md.
**Rule: Claude prepares, Manu posts.** Nothing here is published by an agent. Every post, listing and email is drafted in `marketing/` and pasted by Manu after reading the target's current rules.

## The one-sentence position

"Write one Maestro flow in English. shotfleet runs your app in every language you ship, on iOS and Android, and checks every screenshot." Proof asset: 18 languages x 4 screens in 9 minutes (iOS) and 15 (Android), and the first run found a button nobody could reach.

Who buys: indie and small-team iOS/Android developers (including Flutter, React Native, KMP) shipping in more than 2 languages. What we never say: Flutter or React Native "work" beyond what is proven, frames, captions, upload, "catches all localization bugs", any Maestro endorsement. `tests/claims.json` is the source of truth for claims; `tools/check-claims.sh` must pass before anything is posted.

## What wins and why (ranked by fit x reach x cost for an unknown solo founder)

1. **Maestro community** (Slack `#maestro-questions`, awesome-maestro, docs community articles). Maestro's docs say a flow cannot set the locale: that is our exact gap. Answer questions first, no links in week 1.
2. **One Show HN**, only after the sale is live and the free tier installs on a clean Mac. A waitlist page does not qualify. Base rate for this category is low (24 of 25 got 1-4 points), so the post must carry a real story and a runnable free tier.
3. **Long-tail SEO and founder stories on our own domain** (slow, compounds). Competitors prove demand: ButterKit about 175 URLs, AppScreens about 67.
4. **Newsletters** that want an article, not a product page: Android Weekly, Kotlin Weekly, KMP Weekly, iOS Dev Weekly, SwiftLee Weekly. Submit an article, never the landing page.
5. **Reddit** (answers and feedback threads, r/macapps, r/SideProject), rules read live. The old "one post alternating r/iOSProgramming and r/androiddev" plan is dropped.
6. Indie Hackers page plus one story, free directories (AlternativeTo, DevHunt, Uneed, Peerlist, Console.dev, Indie App Catalog, Awesome-ASO, awesome-maestro), build-in-public on Mastodon (iosdev.space), Bluesky, X.
Not worth it now: Product Hunt, paid ads, sponsored slots, YouTube pitching, awesome-ios (rejects paid/closed tools), BetaList (paid).

## Phases

### Phase 0, now to 2026-10-16 (before the sale opens): build the base

| # | What | Who | Done when |
|---|---|---|---|
| 1 | Custom domain: buy, point site, canonical, update check, installer. Needed for SaaSHub-type directories, backlinks and Chinese reach; the URL is baked into the binary | Manu buys; Claude wires | Site and `/download/VERSION` live on it |
| 2 | Three articles on that domain: (a) fastlane snapshot stuck in English, (b) one Maestro flow for every locale, (c) the button nobody could reach. Each has a copy-paste step that was run | Claude drafts (`marketing/articles/`), Manu publishes | Indexed, linked from the site footer |
| 3 | 60-90 s demo video and the review-grid image with red outlines | Claude scripts and renders the grid; Manu records | Both files exist |
| 4 | Credibility fixes HN will find (claims audit fixes, Apple silicon, Java 17+, CI recipe, Maestro version tested) | Claude | `tools/check-claims.sh` green, deployed |
| 5 | Join `#maestro-questions`, answer locale questions, ask whether paid tools may be listed | Manu, with Claude's drafted answers (`marketing/kit/`) | 5 useful answers, no link |
| 6 | Build story on Mastodon, Bluesky, X with the grid, no price, `?utm_source=` tags | Manu posts from `marketing/kit/social.md` | 2 posts a week |
| 7 | AlternativeTo listing now (months in queue); email Console.dev when the free tier installs | Manu submits from `marketing/kit/directories.md` | Listing pending |
| 8 | 3-5 design partners from people who publicly report a locale problem: free licence for an honest write-up, written permission before any quote | Manu asks | 2 signed-off quotes before any testimonial appears |
| 9 | Founder price shown as plain text ("launch price, first 100 buyers", kept by go-live). A live "N of 100 left" number would need Gumroad's use count for FOUNDER29, which only the dashboard shows (reading it by API needs Manu's Gumroad token, which must not go into the site), so no number is shown | none planned | Text live at launch; the count is read by hand in Gumroad |

Measurement is already in place: visits, pricing views, CTA clicks and runs-section views by source (`site/signups.sh --visits`), signups with source, country and browser language. Gumroad gives orders, FOUNDER29 uses, refunds and sales by UTM source (links carry `utm_source` and `utm_campaign`, which Gumroad keeps).

### Phase 1, launch week (after the Gumroad product is published, the first payout review has started and `packaging/go-live.sh` runs)
- Day 0: email the waitlist (`marketing/launch-email.md`); Indie Hackers product page and one story post; r/macapps once if its rules allow.
- Day 1-2: Show HN with title "Show HN: One English Maestro flow, every language your app ships, checked". First comment: backstory, limits, pricing. Manu answers for hours.
- Day 2-7: DevHunt, Uneed, Peerlist; send article links (not the product) to the newsletters above; Maestro Slack announcement only if the channel rules allow.

### Phase 2, weeks 2-6
- One new article a week (#4 to #8 in `research/marketing-research.md` section 3.4), each ending in a free `check` command.
- Maestro docs community PR; awesome-maestro and Awesome-ASO PRs; `fastlane-plugin-shotfleet` gem; recipe with the asc CLI.
- Two case studies with written permission. A second Show HN only for something genuinely new (Flutter or React Native real run, CI recipe actually run, benchmark).
- Done-for-you offer ($149 per app, cap 10) once a customer story exists.
- **One paid experiment, about $30:** Reddit ads targeted at r/iOSProgramming, r/androiddev, r/FlutterDev and r/reactnative (ads are separate from the subs' ban on organic promotion). Two ad variants, `utm_source=reddit-ads`, run only once the sale is live and the funnel counter has a week of organic baseline. It buys learning (do clicks reach pricing?), not sales; one $29 sale nets about $27 and pays it back. Stop when the budget is spent; no top-up without a pricing view per click above the organic rate. Manu creates the ad account and payment; Claude writes the copy. Reddit's current CPC is unverified.

## Measuring, and when we change course

Per channel (utm tag): visits, pricing views, CTA clicks, installs, free-tier first run, orders, activations, refunds in 14 days with the stated reason, support minutes per sale.
Decision rules: STRATEGY.md and roadmap gates G0 to G6 (50 sales at $29 within 60 days keeps investing; under 15 means a free or open tool). If support per sale passes 30 minutes, stop marketing and fix setup friction first.
Localization (Japanese, then Korean) starts only at the trigger in `research/website-localization.md` (15 or more signups, or 100 or more visits from JP or KR in 30 days).

## Do not

Cross-post the same text to several subreddits or Slack channels; drive-by links; ask for upvotes anywhere; DM people; paid ads or sponsored slots yet; fake urgency or any "only X left" that is not the live FOUNDER29 count; testimonials or logos without written permission and real use; quote "Maestro says one flow per locale" (the docs now recommend tags plus `--device-locale`); a Show HN with a waitlist page; mention $29 more than once per post.

## Open items (need a decision or a fact)

1. Domain name (Manu).
2. Reddit sidebars (blocked for our tools): Manu reads each before posting.
3. Whether install and download hits are counted (they are static files, so no): add a counted `/download/` redirect when the domain moves.
4. The Gumroad product (LAUNCH.md, research/gumroad-setup.md section 6), what Stripe asks after the first sales, and the Dutch tax question: the sale cannot open before the product exists.
