# Reddit ads: the one $30 experiment

Owner: Manu creates the Reddit ads account, adds the payment method and starts the campaign. Claude only wrote the copy. Nothing here has been created or paid. Written 2026-10-02.
Source: MARKETING.md phase 2 ("One paid experiment, about $30"). Ads are separate from the subreddits' ban on organic promotion, but each subreddit's ad rules and Reddit's ad policies are unread by our tools (Reddit is blocked for them): read both in the ads manager before paying.

## What this buys, and what it does not

It buys learning: do paid clicks from developers in these communities reach the pricing section and the free command? It does not buy sales. One $29 sale nets about $24.46 after Gumroad's fees (research/gumroad-setup.md), so a single sale pays most of it back, and none is not a failure. Reddit's current cost per click is unverified (no number was obtainable); do not assume one.

## Ready when (all of these)

1. The sale is live and `curl -fsSL https://shotfleet.com/install.sh | sh` installs on a clean Apple silicon Mac. Do not send paid traffic to a waitlist.
2. The page states the first-100 price in plain text (there is no counter), and the ad body that mentions $29 (variant B) says "first 100 buyers" and "before VAT" like the page. The first-100 price is the only urgency that is true; it must match the page.
3. The site has had at least one week of organic traffic, so there is a baseline (see "Baseline" below).
4. `tools/check-claims.sh` is green and the home page says Apple silicon, Maestro 2.x and Java 17+.
5. You have read Reddit's ad policy and the ad-format limits in the ads manager that day. The limits used here (headline up to 100 characters, body up to 150) come from the brief; if the manager shows different limits, shorten rather than lengthen.

## Budget and schedule

Total: $30, hard cap in the campaign settings (lifetime budget, not daily-and-forget). Suggested: $5 a day for 6 days, same budget split evenly across the two variants. Pause anything on day 3 that Reddit rejects or shows zero delivery for; do not raise bids to force delivery.

## Targeting

Communities (Reddit's "community" or subreddit targeting; pick all four in one ad group per variant, not one group per community, so the budget is not split too thin):

- r/iOSProgramming
- r/androiddev
- r/FlutterDev
- r/reactnative

Notes:
- Flutter and React Native readers will land on a page that says it works from translation files and has not yet run a real Flutter or React Native app. The ad copy below never mentions either framework, so nobody is promised more than the page says.
- Country: choose the markets you can serve in English (for example United States, United Kingdom, Canada, Australia, Netherlands, Germany). Reddit's data on audience size by country was not available; the list is a starting guess, not a finding. Exclude nothing else; do not add interest or keyword targeting on top.
- Placement: feed only. Leave off conversion-optimisation and any "optimise for" setting that spends faster than you can watch.
- Device: all. Desktop clicks are likelier to convert for a Mac tool, but there is no data here, so do not restrict on a guess.

## Ad variants

Both variants say what the thing is, who it is for, and the real limits live on the landing page. Neither uses a countdown, "only X left", or a claim from tests/claims.json that is not proven, evidence or fixed. Character counts are exact.

### Variant A: the tool, plainly

- Headline (89 characters): `Maestro screenshots stuck in English? Run one flow in every language and check each image`
- Body (141 characters): `shotfleet reruns your English Maestro flow in every language on iOS and Android, then checks each screenshot. Mac, Apple silicon. Free check.`
- Call to action button: "Learn more" (or the closest the manager offers; not "Install" or "Download").
- URL: `https://shotfleet.com/?utm_source=reddit-ads&utm_content=a`

### Variant B: the question, with the first-100 price

- Headline (86 characters): `Did your German and Japanese store screenshots really come out in German and Japanese?`
- Body (137 characters): `Free command checks fastlane screenshots against your app's own strings. Or run 2 languages free. $29 for the first 100 buyers, then $49.`
- Call to action button: "Learn more".
- URL: `https://shotfleet.com/?utm_source=reddit-ads&utm_content=b`

Use variant B only while the live count shows the first-100 offer is still open. If the count has reached 100, edit the body to drop the price sentence and say `$49 once, free to check.` instead.

Why the copy is safe:
- "Free check" and "2 languages free": claims C032 (`check` is free, proven), C049 (fixed) and C048 (free `run` for 2 languages; partial, so the ad says only what the README says).
- "$29 for the first 100 buyers, then $49": claims C042, C043 (fixed): the founder price is for the first 100 buyers, whoever buys first.
- "checks each screenshot", "against your app's own strings": claims C026, C027 (proven, partial wording kept narrow); `check` compares screenshots with the strings of the app you point it at.
- "Mac, Apple silicon": the installer refuses Intel Macs (README Limits).
- No speed numbers in the ad, so nothing needs a "one app, one Mac" footnote.

Do not add: "every" localization bug, "catches everything", Flutter or React Native, frames, captions, upload, "recommended by" anyone, a Maestro logo or any Maestro endorsement, testimonials.

## Tracking

Both links use `utm_source=reddit-ads`, the one tag the site's funnel counter splits on (site/public/analytics.js reads `utm_source` only). `utm_content` is not stored by the counter, so the A and B split comes from Reddit's own dashboard (clicks per ad); the site shows the combined funnel for `reddit-ads`. At this budget the sample is too small to call a winner between A and B; treat it as two looks, not a test.

Watch on days 1, 3 and at the end:

```sh
site/signups.sh --visits
```

Read the lines that contain `|reddit-ads|` and compare: `view` (page loaded), `runs` (the real-run section scrolled into view), `pricing` (the price section scrolled into view), `cta` (a button clicked). Also from Reddit: impressions, clicks, spend. Also from Gumroad: any order that day (UTM source).

## Baseline

Before starting, copy the organic numbers from `site/signups.sh --visits` for the last 7 days: for each organic source (direct, hn, mastodon, bluesky, x, github, and so on), `pricing` divided by `view`. Write the overall organic ratio down. Nothing below can be judged without it.

## Stop rule

1. Stop when the $30 is spent. The lifetime cap does this; also stop by hand if spend passes $30 for any reason.
2. Pause early if, after $10 of spend, there are clicks from Reddit but fewer than 3 `view` events for `reddit-ads` on the site (the ad is not reaching the page, or the tag is wrong): fix the link, do not top up.
3. No top-up, ever, unless the final `pricing` per `view` for `reddit-ads` is above the organic ratio and there is at least one `cta` click or a free-tier install that can be traced to it. Even then, add at most another $30 and apply the same rule.
4. Do not run it again for a different message until the first result is written down in one paragraph: spend, clicks, views, pricing views, CTA clicks, orders, what you would change.

## What to write down afterwards

Spend, impressions, clicks, cost per click (this is the CPC the research could not find), views, `runs`, `pricing`, `cta`, orders, refunds. Put the paragraph in MARKETING.md under the measuring section. MARKETING.md's rule stands: no sponsored newsletter slots or other paid placements until conversion by channel is known.

## If something goes wrong

- Ad rejected: read the reason, change only the words it names, resubmit once. Do not argue and do not make a second account.
- A commenter on the ad asks something: answer plainly as the author, disclose it is your product, and do not reply with the price.
- Spend runs faster than planned: pause the campaign first, then investigate.
