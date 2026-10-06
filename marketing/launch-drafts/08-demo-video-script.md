# Demo video: an 88-second cut of the 9 clips

**Where:** YouTube (your channel; unlisted first if you want to check it), then the Product Hunt video slot, the site, and as a link in posts. Uploading is yours to do.
**Source:** the 9 clips on `origin/claude/demo-video`, `marketing/demo-video/web/*.mp4` (1920 x 1080, 30 fps, silent, English subtitles burned in) and `web/manifest.json`. Same files are on the site in `/media/demo/`.

## Rules to respect

- The clips are recordings on shotfleet's own **fixture app** (5 languages: ar, de, en, ja, tr), run from the repo's source on an M1 Pro on 2026-10-05/06. The burned-in subtitles say "my app". Say once on screen that it's the fixture app, so nobody thinks it's a real store app.
- Sped-up parts already carry a "sped up" badge and the real time in the subtitle. Keep those cuts whole; don't trim the badge away.
- The planted mistakes (German screenshot in the Japanese folder) are shown being made on a copy. Keep the "on purpose" line in.
- YouTube: title, description and tags must describe the video; no misleading thumbnail. Mark it as not made for kids.

## Best time

Upload a day before you need it (Product Hunt or Show HN), so the link works and YouTube has processed it.

## The cut

Every in and out point sits on a subtitle boundary from the clip's `.srt`, so no subtitle is cut in half. Times are in the clip's own timeline.

| # | Clip | In | Out | Length | Burned-in subtitles in this part |
|---|---|---|---|---|---|
| 0 | title card (new) | | | 3 s | "shotfleet: one English flow, every language, checked" + small line "Recorded on shotfleet's fixture app, 5 languages" |
| 1 | c2-init | 00:15 | 00:24 | 9 s | "I write one flow in English. It works for iOS and Android." / "shotfleet changes the flow for every language. I keep just one." |
| 2 | c3-run-ios | 00:05 | 00:23 | 18 s | "Sped up 29x here. Real time: about 6 minutes." ... "All 5 languages done. Then it checks every screenshot." |
| 3 | c4-run-android | 00:17 | 00:28 | 11 s | "5 of 5 languages, 0 problems. The note is about Play rules." / "The real Android screenshots from this run." |
| 4 | c5-check | 00:02 | 00:19 | 17 s | "I copy the real output. Then I make a mistake on purpose:" ... "It also sees the same picture in two languages." |
| 5 | c6-check-existing | 00:06 | 00:21 | 15 s | "I say this folder is German. No simulator is needed." ... "check is free for everyone. Nothing is uploaded." |
| 6 | c8-export | 00:05 | 00:16 | 11 s | "One command copies them into fastlane's Google Play folders." / "Every language gets its own folder. fastlane uploads from there." |
| 7 | end card (new) | | | 4 s | see below |

Total: 88 seconds. If you need it under 80, drop part 3 (Android); part 2 plus the end card still say both platforms.

Not used, on purpose: c1-doctor and c9-ci (good on their own, too slow for a first look), c7-store-rules (use it as a separate short; or swap it in for part 5 with 00:02 to 00:12, "The App Store needs 13-inch iPad screenshots").

## Captions (the burned-in subtitles already do this)

Because the subtitles are burned in, the simplest version has **no voice-over**: music low or silence, the subtitles carry it. That keeps the words exactly the reviewed ones.

## Voice-over (optional, if you want your own voice)

Read slowly; it follows the subtitles so they don't fight each other. About 150 words.

> [0] This is shotfleet. I recorded it on the tool's own test app.
>
> [1] I write one Maestro flow, in English. shotfleet changes it for every language my app has. I only keep one.
>
> [2] Here it runs on iPhone simulators, sped up. Each simulator takes one language at a time. When they're done, it checks every screenshot.
>
> [3] Same flow on Android. Five of five languages, no problems.
>
> [4] Now I make a mistake on purpose. I put the German screen in the Japanese folder. check reads the text and catches it. It also sees the same picture in two languages.
>
> [5] check also works on screenshots I already have, like fastlane folders. No simulator. It's free, and nothing is uploaded.
>
> [6] When it all passes, one command puts the screenshots into fastlane's folders, one per language.
>
> [7] shotfleet. For Apple silicon Macs. The check is free.

## End card (4 s)

```
shotfleet
Store screenshots in every language, checked.
shotfleet.com   ·   check is free   ·   Apple silicon Macs
```

(No price on the card, so the video doesn't go stale when the $29 offer ends.)

## YouTube text

- **Title:** `shotfleet: localized App Store and Google Play screenshots from one Maestro flow`
- **Description:**
  > One English Maestro flow, run in every language the app has, on iPhone simulators and Android emulators, then every screenshot checked for the wrong language. Recorded on shotfleet's own 5-language test app on an M1 Pro; sped-up parts are labelled.
  >
  > The check is free and works on screenshots you already have, including fastlane snapshot and screengrab folders.
  >
  > I made shotfleet. https://shotfleet.com/?utm_source=youtube
  > Each clip on its own: https://shotfleet.com/demo?utm_source=youtube
- **Tags:** app store screenshots, google play screenshots, localization, maestro, fastlane, ios, android

## How to stitch it (ffmpeg, from `marketing/demo-video/web/`)

The title and end cards can be made in Remotion like the clips' own cards (`marketing/demo-video/remotion/`), or as 1920 x 1080 PNGs turned into video. Then:

```sh
cut() { ffmpeg -y -ss "$2" -to "$3" -i "$1.mp4" -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 "part-$4.mp4"; }
cut c2-init           15 24 1
cut c3-run-ios         5 23 2
cut c4-run-android    17 28 3
cut c5-check           2 19 4
cut c6-check-existing  6 21 5
cut c8-export          5 16 6
printf "file '%s'\n" card-title.mp4 part-1.mp4 part-2.mp4 part-3.mp4 part-4.mp4 part-5.mp4 part-6.mp4 card-end.mp4 > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c copy shotfleet-demo-88s.mp4
```

(Re-encoding each cut with the same settings is what makes the final `-c copy` concat safe. Check each part's first frame: the clips have their own fade-in cards at 00:00, which these in points skip.)

The clips' "sped up" stretch in c3 runs from 00:05.7 for 12 s and in c4 from 00:05.7 for 12 s. Part 2 starts at 00:05, so it includes the badge. Part 3 starts at 00:17, after the sped-up part ends, so no badge is needed there.
