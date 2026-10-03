# Competitors and positioning (researched 2026-10-01)

Full source list: see the analysis in the session; key findings, with links:

| Tool | Captures app | Platforms | Languages | Checks output | Price |
|---|---|---|---|---|---|
| fastlane snapshot/screengrab | yes, via UI tests | iOS + Android (separate code) | one after another | no | free |
| StoreScreens (2026, github.com/ciscoriordan/storescreens-cli) | yes, XCUITest + agent skill | iOS/Mac/Watch | per locale | no | free |
| asc CLI `screenshots capture` | yes, agent-driven, experimental | iOS/macOS | not documented | no | free |
| simshot | yes, bash loop | iOS | sequential | no | free |
| Maestro / Maestro Cloud | yes | iOS + Android | docs: one flow per locale; parallel only in Cloud | no | free / $250 per device per month |
| Marteso | XCUITest pipeline + framing | iOS | ? | no | unclear |
| ButterKit, AppScreens, AppLaunchpad, Rotato | no, framing/captions only | both | n/a | no | $40–180/yr or $80–199 once |
| Drizz, Applitools, Lokalise | QA / translator context | both | cloud | visual/AI | sales-led |

## Positioning
- For: indie and small-team native iOS/Android developers shipping in 10+ languages, already on fastlane or Maestro.
- Promise: one English flow, every language, both stores, checked. No per-locale tests.
- Win on: verification (language, copies, missing, word clashes), Android parity, zero-edit onboarding from an existing Maestro flow.
- Don't build: frames, captions, store upload. Integrate instead (fastlane folders, frameit, ButterKit, AppScreens, asc upload).
- Next features buyers will ask for: CI mode (exit codes + JSON), Flutter / React Native strings.

## Pricing
$49 once per developer (a year of updates, keeps working afterwards, 14-day refund); $29 for the first 100 buyers, whoever buys first. (The earlier $79 / $49-for-the-list plan is dropped.)
A team/CI license (~$199) once CI mode exists.

## Channels ($0)
1. Maestro Slack + a PR to Maestro's community-projects docs page.
2. Show HN, r/iOSProgramming, r/androiddev, leading with the bug it found and the review grid.
3. iOS Dev Weekly, Android Weekly, Indie Dev Monday: a technical write-up, not a pitch.
4. "Alternatives to fastlane snapshot / StoreScreens" comparison page.
5. A Claude Code / asc skill so agents call shotfleet for the verification step.

## Risks
- Maestro adds locale fan-out: stay a Maestro add-on, compete on local parallelism + checks.
- AI agents make capture trivial: capture is already free; sell deterministic verification.
- Small market: pre-sell the founder tier; ~50 sales in 60 days is the real go signal.
