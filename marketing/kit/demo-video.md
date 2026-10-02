# Demo video: 75 seconds

Owner: Manu records and edits. Claude wrote the script. Nothing is recorded or published. Written 2026-10-02.
Where it goes: the site (hero or the "runs" section), the Show HN first comment (as a link), the launch-day thread (short clip), directory listings that take a video (DevHunt, Uneed, Peerlist), the Maestro community PR if they want a cover.
Ready when: you have a clean Mac user (or a clean desktop), four free simulators, the real app build, a real `shotfleet run` recorded start to finish, and a review grid that contains one deliberately planted failure (said so on screen). No other agent may be using the simulators during the recording (a busy Mac makes the timing wrong).

## Rules for the footage

1. Everything on screen is real output. Do not retype or edit terminal text. Sped-up sections must say "sped up" on screen.
2. Use one number set only: 18 languages x 4 screens, 72 screenshots, 9 minutes iOS, 15 minutes Android, 4 simulators in parallel, one Mac. The timings are one app, one machine (M1 Pro), Maestro 2.0.10; say "one app" on screen at the end if you can fit it, otherwise in the video description.
3. The red outline in the grid must be a planted failure (for example the German image replaced by the English one). Show it with the on-screen text "planted to test the check". Never present it as a bug found in the wild.
4. Do not show other companies' logos or any customer data. Hide your username and home folder in the prompt (set `PS1` to `$ `), close notifications, hide the Dock.
5. No claims about frames, captions, store upload, Flutter or React Native, or Maestro endorsement.
6. Price line only if the sale is live when you publish. If not, cut the price line and keep the free-tier line.

## Specs

1920x1080, 30 fps, MP4. Terminal font size at least 22 pt, dark theme, window cropped to the text. Burned-in captions of the voice-over (most people watch muted). No music, or royalty-free music you have a licence for (name it in the description). Voice-over optional: the on-screen text carries the story on its own. Export a 20-second clip (shots 4 and 5) for X, Bluesky and Mastodon, and a square or 4:5 crop if a site needs it.

## Script and shot list

| Time | Shot | On-screen text | Voice-over (about 190 words; if it feels rushed at a normal pace, drop the second sentence of each cell) |
|---|---|---|---|
| 0:00 to 0:08 | Full-screen `site/public/img/bug_zh.jpg`: the Chinese onboarding page with no Next button. Slow zoom to the empty bottom of the screen | "Chinese. Small Android phone. No way forward." Then: "Also Japanese, Korean, Arabic." | "My app ships in 18 languages. On a small Android phone, in Chinese, there was no way past this page. Japanese, Korean and Arabic too. English fit, so I never saw it." |
| 0:08 to 0:17 | Editor, `flow.yaml`: a few lines with `tapOn: "Next"`. Highlight "Next" | "A Maestro flow taps English buttons." Then: "So it cannot run in German." | "The reason: my screenshot flow tapped English buttons. It could not run in German or Japanese, so my localized screenshots were the English set, copied." |
| 0:17 to 0:27 | Terminal: `shotfleet init path/to/MyApp.app path/to/app-debug.apk` and `cat shotfleet.toml` (the two-line config) | "shotfleet init. Two lines of config." | "shotfleet reads the translations compiled into your app. You keep one English flow and a two-line config." |
| 0:27 to 0:45 | Terminal: `shotfleet run`. Cut to the four simulators booting and tapping. Time-lapse the middle; keep the per-language `ok` lines readable; end on the real summary line | "shotfleet run. 4 simulators in parallel. (sped up)". At the end, the summary as printed: "captured 18/18 locales ... checked 72 screenshots in 18 languages: 0 problem(s)" | "It rewrites every tap for every language, so Next becomes Weiter, 次へ, İleri, and runs them all in parallel. 18 languages by 4 screens, 72 screenshots: nine minutes on iOS, fifteen on Android." |
| 0:45 to 0:58 | Browser: `out/index.html`, the review grid. Scroll slowly: one row per language, one column per screen. Stop on the planted failure outlined in red | "A row per language. A column per screen." Then: "Red: a German image that is really English (planted to test the check)." | "Then it reads every screenshot back and compares it with your app's own strings. Wrong language, copies, missing screens, store sizes. Problems are outlined in red." |
| 0:58 to 1:07 | Terminal: `shotfleet check fastlane/ --app path/to/MyApp.app`, cut to the summary line and the report | "shotfleet check. Free. Any screenshots." | "The check also works on screenshots from any tool, like fastlane snapshot. It is free." |
| 1:07 to 1:15 | End card on a plain background | "Free: check, and run for 2 languages." / "$29 for the first 100 buyers, then $49 once." (only if the sale is live) / "Apple silicon Mac. Maestro 2.x. Java 17+." / `https://shotfleet.com` | "Free to check, free for two languages in a run. Apple silicon Mac, Maestro and Java 17 or newer. Details at the link." |

Running time 75 seconds. If it runs long, cut the editor shot (0:08 to 0:17) to 5 seconds first, then the `init` shot.

## What to record (checklist)

1. Reset the demo: clean `out/`, fresh simulators named `shotfleet-1` to `shotfleet-4`, the app build installed fresh.
2. Record the screen for the whole `run` (about 9 minutes on iOS) in one take, plus the terminal at full size. Edit down; the time-lapse speed is whatever fits 18 seconds.
3. Plant the failure before opening the grid: copy `out/raw/en/01_*.png` over the German one, run `shotfleet check out`, then open the resulting `index.html`. Restore afterwards. (Confirm the exact folder names on your build before relying on this path.)
4. Record `shotfleet check` on a real fastlane folder; the real timing (about 25 seconds for 252 images on my Mac) can be shown but only say it on screen if the clip really shows it.
5. Export one full video, one 20-second clip, and a still of the grid for social posts.

## Honesty checks before you publish

- The video must not say "catches all localization bugs". The first sentence says what happened: a missing button in four languages, found because the run got stuck, not because the tool detected a button.
- Compare every number on screen with README, `tests/claims.json` (C007, C012, C030) and `marketing/kit/social.md`.
- Add the video link only to places that list it as a demo, never in a reply to someone who asked a question.
