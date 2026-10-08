# Build-in-public calendar: Mastodon (iosdev.space), Bluesky, X

Owner: Manu posts, from his own accounts. Nothing here has been posted. Written 2026-10-02.
Ready when: domain is live and the site renders the article pages; accounts exist on the three networks. Week 1 and 2 posts need the assets listed below, not the sale. The launch-day thread needs the sale live and the free tier installing (packaging/go-live.sh run, `curl ... install.sh | sh` works on a clean Mac).

## Rules

1. Two posts a week, one story each, always with the asset. No price in weeks 1 and 2 (MARKETING.md phase 0). Price at most once per post, and only after the sale is live.
2. Do not tag anyone, do not ask for boosts, likes or reposts, do not DM. Reply to people who answer.
3. Add alt text to every image (describe it, do not repeat the post).
4. Links carry a source tag so the site's funnel counter can split visits: `?utm_source=mastodon`, `?utm_source=bluesky`, `?utm_source=x`. The counter reads `utm_source` (site/analytics.js). Use the article URL as the link when the post is about the article. In every draft below, replace `SOURCE` with `mastodon`, `bluesky` or `x` according to the network you are pasting into (three separate pastes, three tags); never leave the word SOURCE in a posted link.
5. Keep the text under 270 characters including the link so the same text fits X, Bluesky (300) and Mastodon (500). Mastodon may add up to 3 hashtags (#iOSDev, #indiedev, #Maestro or #localization); do not add them on X or Bluesky. A few drafts below run over 270 characters once the real URL is added; drop the last sentence of the post rather than the link.
6. Facts allowed: 18 languages x 4 screens, 72 screenshots, 9 minutes iOS and 15 minutes Android on one Mac, 4 simulators in parallel; one app (my workout app), Maestro 2.0.10; the unreachable Next button; Turkish "Next" and "Advanced"; price $29 for the first 100 buyers then $49 once; free: `check`, plus `run` for 2 languages; 14-day refund. Never claim Flutter or React Native on real apps, frames, captions, store upload, or any Maestro endorsement.

## Assets (make once, reuse)

| Asset | What it is | Source or how to make it |
|---|---|---|
| Grid image | The review grid (`out/index.html`): a row per language, a column per screen, problems outlined in red. Screenshot of the HTML, one with a red outline | Run `shotfleet run`, open `out/index.html`. Needs a planted problem for the red outline (for example a copied German image) and must say so in the alt text |
| Terminal capture | Dark terminal, readable at phone size: the `run` summary or the `check` command | Record the real output; do not retype it. README sample: `captured 18/18 locales in 534s on 4 simulators` and `checked 72 screenshots in 18 languages: 0 problem(s)` |
| Ribbon image | One screen in several languages side by side, each with the language code in a ribbon and its name as caption, like the site gallery | Take 5 or 6 files from the 72 real screenshots (the `train_*` set in `site/public/img/` is this app) |
| Short clip | 10 to 20 seconds, no sound needed: `shotfleet run` start to finish sped up, ending on the grid | Cut from the demo video (marketing/kit/demo-video.md) |
| Bug image | `site/public/img/bug_zh.jpg`: Chinese onboarding page, no Next button | Exists in the repo |

## Calendar

Posting days are suggestions (Tuesday and Friday). Week 1 starts Monday 2026-10-05; shift as needed. Replace the second post of the week in which the sale opens with the launch-day thread below.

### Week 1: the story and the numbers

**Post 1.1 (Tue)** Asset: bug image.
> Small Android phone, Chinese: my app's onboarding had no way forward. Japanese, Korean and Arabic too. Longer text, a page that did not scroll, Next below the screen. English fit, so I never saw it. The fix was 8 lines. https://shotfleet.com/the-button-nobody-could-reach?utm_source=SOURCE

Alt text: "Chinese onboarding page with four goal cards and a Skip link, but no Next button."
Before posting: confirm which languages were observed (article 3 TO VERIFY item 2).

**Post 1.2 (Fri)** Asset: terminal capture of the `run` summary.
> 18 languages x 4 screens = 72 screenshots of my app. 9 minutes on iOS, 15 on Android, one Mac, 4 simulators in parallel, from one English Maestro flow. I am building this as a tool for my own app. https://shotfleet.com/?utm_source=SOURCE

Alt text: "Terminal output ending with: captured 18 of 18 locales on 4 simulators, checked 72 screenshots in 18 languages, 0 problems."

### Week 2: how it checks

**Post 2.1 (Tue)** Asset: grid image with the red outline.
> The review grid: a row per language, a column per screen. Every screenshot is read back and compared with the app's own strings. This red box is a German image that was really English (I planted it to test). https://shotfleet.com/?utm_source=SOURCE

Do not post unless the red-outline image really is a planted failure and the post says so.

**Post 2.2 (Fri)** Asset: ribbon image (one screen, five or six languages).
> Same screen, six languages, one English Maestro flow. The tool reads the translations compiled into the build and rewrites "Next" into Weiter, 次へ or İleri before each run. https://shotfleet.com/maestro-one-flow-every-language?utm_source=SOURCE

Link only once article 2 is live. If not, link `https://shotfleet.com/?utm_source=SOURCE`.

### Week 3: the details nobody lists

**Post 3.1 (Tue)** Asset: terminal capture of the collision warning.
> In my app's Turkish strings, "Next" and "Advanced" are the same word (İleri). A test that taps "Next" can hit the wrong button. The tool warns before anything runs and lets you pin the tap with below:. Little details like this are most of the work.

Terminal capture: run on the real app and show the real warning line (README documents the form: `'Next' -> 'İleri' also means 'Advanced'`). No link needed.

**Post 3.2 (Fri)** Asset: terminal capture of `shotfleet check`.
> shotfleet check is free: point it at a fastlane screenshots folder and a build of your app. It tells you which language folders show another language, which images are copies and which are missing. No account. https://shotfleet.com/fastlane-snapshot-screenshots-all-english?utm_source=SOURCE

Needs: article 1 live and the free tier installing. Mac only, Apple silicon, say so if asked.

### Week 4: Maestro tip and honest limits

**Post 4.1 (Tue)** Asset: terminal capture (a flow header with the `env:` default highlighted) or none.
> Maestro locale tip: a default in the flow's env: header can beat -e on the command line. One developer documented it on 2.10: every "Portuguese" screenshot was English. Look at the images, not the exit code. https://github.com/RogerioDoCarmo/morse_app/pull/216

Needs: reproduced on a Maestro version you name (article 2 TO VERIFY item 7). If you could not reproduce it, write "one developer reported" (already the case) and do not add "I confirmed". No utm on third-party links.

**Post 4.2 (Fri)** Asset: grid image.
> What shotfleet does not do: frames, captions, store upload. Mac with Apple silicon only; needs Maestro 2.x and Java 17+. Free: check, and run for 2 languages. If you ship in 10+ languages, how do you verify your screenshots today? https://shotfleet.com/?utm_source=SOURCE

If the sale is live you may add one line: "$29 for the first 100 buyers, then $49 once." Only once, and only with the live count if the site shows it.

## Launch-day thread (sale live, free tier installs)

Post as a thread on each network from its own account. If the Show HN goes up the same day, post the Show HN first and answer its comments before the threads. Use the matching `utm_source` in the link of post 1 and post 6.

1. (asset: grid image)
> shotfleet is out. One English Maestro flow, every language your app ships, on iOS and Android, and every screenshot checked. 18 languages x 4 screens took 9 minutes on iOS and 15 on Android on one Mac. A thread on what it does and does not do. https://shotfleet.com/?utm_source=SOURCE

2. (asset: bug image)
> Why I built it: my screenshot flow tapped English buttons, so "localized" screenshots were the English set copied into every folder. Then the first Android run stuck on one page: in Japanese, Korean, Chinese and Arabic, Next was below the screen.

3. (asset: ribbon image)
> How: it reads the translations compiled into your build and rewrites each tap in your English flow, so "Next" becomes Weiter, 次へ or İleri. Then it runs the languages in parallel on simulators and emulators, and compares each image with the app's own strings.

4. (asset: terminal capture of the collision warning)
> It warns when two labels clash in a language (Turkish "Next" and "Advanced" are both İleri) and reports wrong-language images, copies, missing screens and store size rules. It does not make frames or captions and does not upload; fastlane does that.

5. (no asset)
> Limits up front: Apple silicon Mac only. Needs Maestro 2.x and Java 17+, Xcode for iOS, the Android SDK for Android. Android needs API 33+ emulators. Flutter and Expo work from translation files; I have run one public Flutter app (wger) and one Expo template (obytes; template commit not recorded) end to end, not other Flutter or Expo apps or bare React Native.

6. (asset: short clip)
> Free: shotfleet check on any screenshots, and run for 2 languages. A licence unlocks every language and export: $29 for the first 100 buyers, then $49 once, with a 14-day refund. Install and details: https://shotfleet.com/?utm_source=SOURCE

Fix before posting: use the real live count if the site shows "N of 100 left"; otherwise keep the sentence as written. State the price once, in post 6 only.

## After each post

Answer replies the same day. If someone asks a technical question you cannot answer, say so and note it for the FAQ. Log for each post the visits by source from `site/signups.sh --visits` after 3 days, so MARKETING.md's measuring section has real numbers.
