# How shotfleet beats the competition

Who we're for: indie developers and small teams shipping a **native iOS and/or Android app in 10+ languages**,
who already use fastlane or Maestro. Promise: **one English flow, every language, both stores, checked.**

The market in one line: capturing screenshots is becoming free (fastlane, StoreScreens, asc, simshot),
framing is a crowded paid market (ButterKit, AppScreens), and **nobody checks the result or covers both
platforms from one flow**. We own checking and cross-platform, and we plug into everyone else.

## 1. Where we beat each competitor

| Competitor | Their strength | Where we win | How we prove it |
|---|---|---|---|
| fastlane snapshot / screengrab | Free, the default, huge community | No UI-test code; one flow for both platforms; languages in parallel; every image checked | Publish a timed head-to-head on WOD Tracker: setup time and run time, fastlane vs shotfleet |
| StoreScreens, asc, simshot (new, free) | Free, agent-friendly, App Store upload | Android; checking; no app changes (simshot needs launch arguments in the app) | "Capture with anything, check with shotfleet" (see 2.1): they become a source of users |
| Maestro / Maestro Cloud | The flow format we build on | Maestro's docs say "one flow per locale"; we keep one flow and run locally for free | Be the add-on: Maestro community projects page, Maestro Slack, never position against them |
| ButterKit, AppScreens, frameit | Frames, captions, upload | We don't compete; we feed them | Export recipes into their import formats; ask for a listing / affiliate swap |
| Drizz, Applitools, Lokalise | Enterprise QA, sales-led | $49 once, local, no account | Not our buyer; mention only on the comparison page |

## 2. Product moves, in order (each one widens the gap)

1. **Check any screenshots, not just our own.** `shotfleet check --app MyApp.app ./fastlane/screenshots`
   reads screenshots made by fastlane, StoreScreens, asc or by hand, and runs the same checks (right language,
   copies, missing). Every free capture tool becomes a funnel into us. Possible free tier: checking is free,
   capturing is paid.
2. **CI mode.** _(done: `--json`, exit codes, Actions recipe; fastlane plugin pending)_ `--json` report, stable exit codes, a GitHub Actions recipe on a macOS runner, and a
   one-command fastlane plugin (`fastlane add_plugin shotfleet`). This is the first thing teams ask for,
   and it's what unlocks a ~$149 team license.
3. **Flutter and React Native strings** (ARB, i18n JSON). The biggest group of buyers we currently turn away.
4. **Agent integration.** A Claude Code skill (and, if demand shows up, an MCP server) so AI agents call
   shotfleet for the checking step instead of reinventing it. Place it next to the asc skills (1k stars).
5. **Distribution polish.** Homebrew tap, signed release, `shotfleet --version` update notice, licence key.

**Not building:** device frames, captions, store upload, a web dashboard. Free or entrenched tools do these;
we integrate instead.

## 3. Launch plan (6 weeks)

| Week | Do | Measure |
|---|---|---|
| 1 | Post the drafts (Reddit, Indie Hackers, X, Maestro Slack) with `utm_source` tags. PR to Maestro's community projects page. | Signups per channel |
| 2 | Publish the head-to-head write-up (fastlane vs shotfleet on WOD Tracker) on the site; send to iOS Dev Weekly, Android Weekly, Indie Dev Monday. | Visits, signups |
| 2–3 | Build `check` for any screenshots (2.1); announce it as a free command. | Downloads of the free command |
| 3 | Show HN with the review grid and the onboarding bug. | Signups, HN comments as research |
| 4 | Founder sale opens for the list: $29 for the first 100, through Gumroad (Lemon Squeezy and Polar end in a Stripe check that asks for a KvK). | Sales (the real Go signal) |
| 5–6 | CI mode + fastlane plugin for buyers; collect two case studies (output grid + quote). | Activation, refunds |

**Decision rule** (replaces "30 signups"): **50 founder sales ($29) within 60 days** of opening the sale means
keep investing (CI, Flutter/RN, team license). Fewer than 15 means it stays a free/open tool for Manu's apps.

## 4. Pricing

- $49 once per developer, a year of updates, keeps working afterwards; optional renewal for updates later.
- $29 founder price for the first 100 buyers, whoever buys first (not a list perk).
- Free tier: `check`, and `run` for up to 2 languages, so people see real results before paying.
- ~$149 team/CI license once CI mode exists.
- Why not $79: research/pricing-2026-10.md (ButterKit Pro is $99 and includes more; both direct competitors have a free tier; no demand data yet). Raise the price as proof arrives.
- If `check` becomes free, `run` (capture + checks + export) is what people pay for.

## 5. Risks and what we do if they happen

| If | Then |
|---|---|
| Maestro ships locale fan-out | Lean harder on checking and local parallel runs; integrate with their feature rather than duplicate it |
| An AI agent tool starts checking languages | We already have the deterministic check plus Android; ship the agent skill so they call us |
| fastlane adds verification | Our edge stays "one flow for both platforms, no UI-test code"; make `check` work on fastlane output so we sit beside it, not against it |
| Few buyers | Open-source it; the benchmark and the bug story still build Manu's reputation |
