# Product Hunt

**Where:** https://www.producthunt.com/posts/new (you are the maker and the hunter; no need for a "hunter").

Note: MARKETING.md lists Product Hunt as "not worth it now". This draft is here so it's ready if you change your mind, not a push to do it.

## Rules to respect (https://www.producthunt.com/launch, read 2026-10-06)

- Don't ask people to upvote. You may share the link and ask people to have a look and comment.
- Launch day starts at 12:01 AM Pacific Time and lasts 24 hours.
- You can launch again later only for a significant new version. 0.1.6 is already out when this launches, and its XCUITest part hasn't run end to end, so don't plan a second launch around it.
- Disclose that you made it: the first comment is yours, as the maker.

## Best time

Schedule for 12:01 AM PT, which is 09:01 in the Netherlands, so you're awake for the whole US day. Tuesday to Thursday has the most traffic and the most competition; a Saturday or Sunday launch is quieter and easier to be seen on. For a small dev tool with no audience to bring, a weekend launch is the honest choice. Whatever day: one you can spend answering comments. Not 14 Oct (that's Keysi's Product Hunt day). Suggestion: Sun 25 Oct, after Show HN and App Saturday.

## Name

shotfleet

## Tagline (57 of 60 characters)

`Localized store screenshots from one English Maestro flow`

Alternatives:
- `Check your store screenshots are in the right language` (54)
- `App Store and Play screenshots in every language, checked` (57)

## Description (239 characters; keep under 260)

> A Mac command-line tool that runs one English Maestro flow in every language your app has, on iOS and Android, then checks every screenshot for the wrong language, blank screens and store sizes. check is free, also on fastlane screenshots.

## First comment (maker)

> Hi, I'm Manu. I made shotfleet, on my own.
>
> I have an app in 18 languages, and my store screenshots were a mess. My Maestro flow only worked in English, because it taps buttons by their text. So I wrote a tool that reads the translations in my app and rewrites the flow for each language. "Next" becomes "次へ" in Japanese, "Weiter" in German.
>
> Then I added a check, because a screenshot in the wrong language looks perfectly fine until a Japanese user sees it. On the old Google Play screenshots of another of my apps (AnywhereRoles), check found 127 problems: 103 were translated captions over an app still in English, and 15 were false alarms from a bug of mine, fixed in 0.1.6. I had made one English capture and translated only the captions. I recaptured it with shotfleet: 120 Android and 108 iPhone screenshots, 0 problems (several failed runs came first).
>
> One run on my M1 Pro: 18 languages x 4 screens in 9 minutes on iOS and 15 on Android. The first full Android run also showed me a Next button that nobody could reach in Japanese, Korean, Chinese and Arabic on a small phone. English fit, so I'd never seen it.
>
> What it isn't: no frames, captions or upload (use ButterKit, AppScreens or fastlane for that). Apple silicon Macs only, closed source. Capturing needs Maestro and Java 17+, except on iOS with your own XCUITest screenshot tests (new in 0.1.6; I haven't run that end to end yet).
>
> Free: check (works on fastlane snapshot, screengrab and supply folders too), and run for 2 languages. Every language: $29 for the first 100 buyers, then $49, one-time, with a year of updates and a 14-day refund. Install with `brew install noloman/tap/shotfleet`.
>
> I'll be here all day. I'd like to know how you handle localized screenshots now.

## Gallery (images 1270 x 760 recommended; PH takes PNG, JPG or GIF, so convert the .webp posters)

Use the existing posters from `site/public/media/demo/` (also on `origin/claude/demo-video` in `marketing/demo-video/web/`). They are real frames from the fixture-app recording; resize or pad to 1270 x 760.

1. `c5-check-poster.webp`, caption:
   > I put a German screenshot in the Japanese folder on purpose. check read the text and caught it. The real output passed with 0 problems.
2. `c3-run-ios-poster.webp`, caption:
   > One English Maestro flow, every language the app has, on several iPhone simulators at once. Then every screenshot is checked.
3. `c7-store-rules-poster.webp`, caption:
   > check flags screenshot sizes the App Store won't take, and a missing 13-inch iPad set.

Optional 4th: `c6-check-existing-poster.webp`, "check works on screenshots you already have, like fastlane snapshot, screengrab or supply folders. No simulator needed, and it's free."

Video slot (PH wants a YouTube link): upload the cut from `08-demo-video-script.md` to YouTube first (unlisted is fine), then paste the link. Uploading to YouTube is yours to do.

Thumbnail: the app icon from `marketing/logo/` (240 x 240).

## Topics (pick 3; check the names in the form, PH renames topics now and then)

1. Developer Tools
2. Mac
3. Android (or "iOS" / "Apple" if offered; there may also be a "Languages" or "Localization" topic, which fits better than either)

## Links

- Website: `https://shotfleet.com/?utm_source=producthunt`
- Pricing: Paid, with a free tier (PH's "Free options" box)

## Before launching

- Gates 1 to 3 in README.md. If the AnywhereRoles section isn't live, cut the AnywhereRoles sentences from the comment.
- Don't tell friends to upvote. Posting "I launched on Product Hunt today" on your own social accounts is fine.

Disclosure line (in the comment): "I made shotfleet, on my own."
