# Market research 2026 (researched 2026-10-01)

Scope: only what is NEW or MISSING versus STRATEGY.md and marketing/competitors.md.
Method: web search + page fetch. Reddit and Stack Overflow are blocked for the research tool (not verified there at all);
Hacker News search returned only launch posts with 0-3 comments (no pain-point threads). So pain-point evidence below is
from GitHub issues, vendor pages and developer forums. "(summarizer)" = page was read through a summarizing fetch, so wording
is paraphrase-risk; re-open before quoting publicly.

## 1. Competitors and adjacent tools (new or changed)

| Tool | Price (as found) | Platforms | Does that shotfleet doesn't | Complaints found |
|---|---|---|---|---|
| ButterKit (butterkit.app) | $99 once or $39/yr per its comparison page (other sources say $79 once: conflict, unverified) | Apple-first, some Play presets, macOS only | One-click Simulator capture, link to a fastlane screenshots folder, built-in MCP server for agents, translation of screenshots + metadata, upload to ASC, "App Store preview" in every language | macOS-only; I did not confirm it does automatic multi-locale capture (its page does not say) |
| AppScreens | $25/mo or $90/yr | iOS, Play, other stores | 80+ languages with RTL layout, upload to ASC and Play, CPP/PPO variants | Needs account + internet; manual import; no Xcode integration (per ButterKit's page, biased source) |
| Screenshots.pro | Free / $19 mo (localization) / $49 mo (API) | iOS + Android frames | REST API for CI, auto-translate | No simulator capture mentioned |
| AppLaunchpad | Free w/ watermark; Pro $29/mo or $180/yr | iOS + Android | AI bulk localization 80+ languages | Highest monthly price in roundups |
| Previewed | Free w/ watermark; from $12/mo; $9.99 once for 3D/video | iOS | 3D and video exports | n/a |
| Screenshot Studio (appstorescreenshotstudio.com) | Free trial; weekly/monthly/yearly + lifetime (amounts not shown) | iPhone, iPad, Mac, Watch, TV, Vision, Android phones | Imports from Simulator/device, AI translation, bulk upload to ASC across all platforms and locales | None found |
| ScreenshotWhale | Free (3 gen/mo); $9.99/mo; $19.99; $29.99; $14.90 one-time 30-day pack | iOS + Android, editor integrates with Cursor/Windsurf/Copilot/Cline | AI lays out raw screenshots into 22 device sizes, 10 languages (paid plans say up to 5) | Free tier watermarked and capped |
| LocaShot, LocalizeShots | LocalizeShots $4.99/mo or $59.99/yr; LocaShot not checked | iOS + Android | AI localizes already-designed screenshots in 30-40 languages in seconds | Risk (my inference): they redraw text over the image, not the real app in that language, which is exactly the mismatch Apple rejects (section 2) |
| Emerge Tools -> Sentry Snapshots | Emerge: free for OSS, indie/enterprise tiers (no amounts found). Sentry Snapshots: beta | iOS + Android | Generates screenshots from SwiftUI/Compose Previews with one annotation (`@EmergeAppStoreSnapshot`); no emulator run | Early version "rough edges" per Emerge; Emerge was acquired by Sentry May 2025 |
| asc CLI (rudrankriyam/App-Store-Connect-CLI) | Free | iOS | Commands: `screenshots capture/frame/review-generate/review-approve/plan/apply/run/upload/sizes`, dimension validation, resumable uploads (docs.asccli.sh) | Local automation "experimental"; capture needs a running simulator; multi-locale capture = set simulator locale per UDID |
| StoreScreens CLI | Free MIT, 27 stars when checked | iPhone/iPad/Watch/Mac | MCP integration, web version | Localization, parallelism and checks not documented on repo page |
| fastlane | Free; actively maintained (issue #30040 filed May 2026 against 2.334.0) | iOS + Android (separate tools) | frameit, deliver/supply upload, huge community | See section 2 |
| Maestro CLI 2.x | Free local; Cloud $250 per concurrent device per month (aggregator, check maestro.dev/pricing) | iOS + Android | 2.9.0 (Aug 2026) lets a flow switch dark/light mid-run; Maestro Viewer + Studio for AI agents | `maestro test` cannot set locale; only `start-device`/`cloud --device-locale` (docs.maestro.dev) |
| Applitools / Percy | Applitools free 100 checkpoints/mo, then ~$99-199/mo; Percy web $599/mo, App Percy 1,000 free screenshots/mo (aggregators) | web+mobile | Baseline diffing across releases | Not about "is this the right language"; expensive for indies |
| Paparazzi / Roborazzi / swift-snapshot-testing | Free | Android JVM / iOS | Parameterize tests over locale/font/theme without an emulator | They make test goldens, not store images; not researched deeper |
| Bitrise / Codemagic | Not researched for price | both | Both just run fastlane snapshot in CI (Codemagic blog, Bitrise docs); no screenshot-specific step found | n/a |
| Xcode Cloud | Not researched; no screenshot feature found | iOS | n/a | Could not verify either way |

Takeaway: ButterKit now has MCP + fastlane folder link + Simulator capture, so "agent-friendly + folder-compatible" is table stakes.
Nothing found verifies the output language. Closest thing is asc's `review-*` (a human gallery) and ButterKit's preview.

## 2. Developer pain points (evidence)

- fastlane snapshot recompiles per language, slow. #15938: "fastlane snapshot is _much_ slower (like 3x slower)"; proposes
  launch arguments so it's "one build, run all languages on every simulator in parallel" (summarizer). https://github.com/fastlane/fastlane/issues/15938
- Language silently not applied. #11457: "All screenshots are always in the default simulator language/locale"; the workaround
  `localize_simulator` gives "ugly statusbar" because simulators are erased (summarizer). https://github.com/fastlane/fastlane/issues/11457
  Same class: #7097, #9278, #8895, #1643 (titles only).
- Parallel simulators flaky. #10771 "Snapshot with concurrent_simulators fails the tests"; #13657 "failing randomly when using multiple simulator". https://github.com/fastlane/fastlane/issues/10771 , https://github.com/fastlane/fastlane/issues/13657
- Xcode drift keeps breaking it. #30040 (May 2026): OS 26.4.1 truncated to 26.4 in the xcodebuild destination, snapshot fails; closed via PR #30054. https://github.com/fastlane/fastlane/issues/30040
- Android: screengrab locale not applied. #11696 "Screengrab locale not changing", #14307 Kotlin LocaleTestRule "Locales not getting changed", #14308 duplicate screenshots (titles only). https://github.com/fastlane/fastlane/issues/14307
- Maestro locale: only via `--device-locale`; docs: "Maestro attempts to change the system language and region before running any Flow." No locale in flow or `maestro test`. https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales
- Maestro: iOS permission-dialog helper only dismisses English labels; open since Aug 2025. Quote: "System permissions popups are auto-dismissed for a variety of languages other than English." https://github.com/mobile-dev-inc/maestro/issues/2654 (summarizer; this breaks any non-English capture run that hits a permission prompt)
- Maestro: `--device-locale` once changed the wrong Android device: "The maestro emulator starts, but the locale is changed on the other device." Fixed (2.8.0 per search snippet). https://github.com/mobile-dev-inc/maestro/issues/2209
- Maestro parallel: `--shards` split tests rather than run all on each device; request "run the whole test on every device" closed via PR #1955. https://github.com/mobile-dev-inc/Maestro/issues/1844 . Also #2713 Maestro 2.0.2 could not detect ARM64 Android emulators on Apple Silicon (title only).
- Rejections: Guideline 2.3.3 when translated captions sit on an English UI; "Localized listings need localized screenshots OR drop the localization claim" (vendor blog, appstorescreenshotstudio.com, so treat as marketing). https://appstorescreenshotstudio.com/posts/app-store-screenshot-rejections/ ; https://appscreenshotstudio.com/blog/app-store-screenshot-translation-mistakes-2026
- Reviewers miss localizations. Apple forum 2.3 rejection: "The reviewer didn't change the iOS system language settings" (summarizer). https://developer.apple.com/forums/thread/739868 (shows that language claims in metadata are scrutinised)
- Stale locales on Play: "A screenshot swap applied only to the default language leaves old creative running in every other market" (applaunchpad blog). https://theapplaunchpad.com/blog/google-play-store-screenshot-requirements/
- Scale: 20 languages x 6 devices x 5 shots = 600 images (fastlane docs/Khan Academy). https://blog.khanacademy.org/?p=347

Not found: Reddit/SO threads (blocked). I could not quantify demand beyond GitHub issues.

## 3. Store requirements (2026)

Apple (developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications, summarizer, re-verify numbers):
- 1-10 screenshots per device class per localization; JPEG/PNG; no alpha.
- iPhone 6.9" 1260x2736 (portrait) listed; third-party guides say 1320x2868 recommended and 1290x2796 accepted. Required if app runs on iPhone;
  if no 6.9" set, 6.5" (1284x2778) is required and gets scaled up. Smaller classes are scaled from the next size up.
- iPad 13" 2064x2752 required if app runs on iPad (2048x2732 older); 11" and others scaled from it.
- Watch: required, one size per generation (e.g. 416x496 Series 10-12, 422x514 Ultra 3/4); Apple says same size across all localizations for Watch.
- Mac: 16:10 sizes, 1280x800 to 2880x1800; Apple TV 1920x1080 or 3840x2160; Vision Pro 3840x2160.
- Custom product pages: up to 70 per app since 2025-10-29; each up to 10 screenshots, up to three localizations per page, own screenshots/video (adapty, mobileaction; not verified on Apple).
- NEW at WWDC26 (beta, public fall 2026 with iOS 27): Asset Library in ASC, new "Header" asset (image/video, renamed Feature Banner),
  creative assets submitted independently of a build, product-page preview tool incl. languages, header is a PPO test variable,
  ASC API for the Asset Library ("later this summer" per Phiture). https://developer.apple.com/videos/play/wwdc2026/205/ ; https://phiture.com/blog/wwdc26-updates/

Google Play (support.google.com/googleplay/android-developer/answer/9866151, summarizer):
- Min 2 screenshots total, max 8 per device type; JPEG/24-bit PNG, 320-3840 px, long side at most 2x short, 8 MB each.
- Phone: 16:9 or 9:16, min 1080 px. 7" and 10" tablet, Chromebook: min 4 each, 1080-7680 px. Wear OS: 1:1, min 384x384, app UI only, no frames/backgrounds.
  Android TV: at least 1 plus banner. Automotive: 2 portrait + 2 landscape for non-parked categories (800x1280, 1024x768). Android XR: 4-8, 8:5, rec 3840x2400.
- Large-format promotion eligibility: at least 4 screenshots at 1080 px+; games at least 3.
- Text-bearing graphics should be localized per language.
- Experiments: 1 default-graphics experiment or up to 5 localized experiments at once, up to 3 variants each (third-party guides, not Play docs).

Caveat: some third-party guides disagree on exact Apple pixels; rely on ASC's own page (and `asc screenshots sizes`) before hardcoding.

## 4. Ranked feature ideas

Score = evidence strength x how much it differentiates from free tools. "Pay?" = would it justify $79.

1. Fix the non-English capture traps inside `run` (permission dialogs in any language, status bar override, locale set per device, never the wrong device). Effort M. Pay: YES, it is the product.
   Evidence: Maestro #2654 (open), #2209, fastlane #11457 "ugly statusbar", docs say no locale in `maestro test`.
2. Store-spec linter in `check` (per-class size, count, alpha, Watch same-size across locales, Play: min 2 / max 8, 4+ at 1080 px for promo, tablet 4+, Wear 1:1 no frames) plus
   "locale in app/listing but no screenshot set" and "set identical to default locale". Effort S-M. Pay: partly (good free funnel).
   Evidence: Apple + Play specs above; stale-locale warning (applaunchpad); asc only checks dimensions.
3. `check` for framed / captioned images (ButterKit, AppScreens, LocaShot output): OCR the caption language and the in-app UI language separately, flag
   translated caption over wrong-language UI. Effort M (needs region split heuristic). Pay: YES, nobody else does it.
   Evidence: 2.3.3 mismatch rejections; AI localizers (LocaShot/LocalizeShots) sell exactly this workflow.
4. Multi-device-class runs from one flow: iPad 13", Android tablet 7/10", plus Watch/Wear as follow-ons, output in the exact fastlane folder/size per class. Effort L. Pay: YES for iPad/tablet.
   Evidence: iPad 13" required if app runs on iPad; Play tablet min 4 and promo eligibility; Screenshot Studio covers all Apple classes.
5. Variant sets for CPP / PPO / Play experiments: tag flows or flow variants, emit per-variant folders (and per-locale), validate counts (10 per CPP; 3 variants Play). Effort M. Pay: maybe (unproven demand).
   Evidence: 70 CPP limit; AppScreens sells CPP/PPO; WWDC26 Asset Library + API makes bulk upload easier.
6. Handoff recipes, not upload: emit `asc screenshots plan/upload` and `fastlane deliver/supply` commands; later maybe consume the ASC Asset Library API once it ships. Effort S. Pay: no, removes friction.
   Evidence: asc has plan/apply/upload; ButterKit and Screenshot Studio upload; STRATEGY says do not build upload.
7. Agent surface: MCP server next to the Claude skill (`shotfleet check` as a tool returning JSON findings). Effort S-M. Pay: indirect.
   Evidence: ButterKit ships MCP, StoreScreens supports MCP, Maestro Viewer targets agents. Strategy had MCP as "if demand shows up"; competitors have moved, so move it up.
8. Appearance matrix (light/dark as extra capture dimension) using Maestro 2.9 theme switch. Effort S-M. Pay: low.
   Evidence: only that Maestro 2.9.0 added it; I found no developer asking for dark-mode store shots. Skip unless asked.
9. Marketing claim, not a feature: shotfleet does not depend on `xcodebuild -destination` OS matching (fastlane #30040) or rebuilding per language (#15938). Effort S. Pay: n/a.
   Needs verification against how shotfleet actually runs before publishing.

Not supported by this research (don't chase): live Reddit sentiment, price elasticity for a $79 CLI, Xcode Cloud / Bitrise / Codemagic specifics, swift-snapshot-testing.
