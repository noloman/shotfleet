# Short posts: X, Bluesky, Mastodon

**Where:** your own accounts. Mastodon: iosdev.space or androiddev.social style instances are where the audience is.

## Rules to respect

- Limits: X 280 characters (free account), Bluesky 300, Mastodon 500. Every post below is **under 280 including the link**, so the same text fits all three. Character counts are in brackets (counted with the `?utm_source=x` link; the Bluesky and Mastodon tags are a few characters longer and still fit).
- Change the tag per network: `utm_source=x`, `utm_source=bluesky`, `utm_source=mastodon`.
- On Mastodon you may add up to 3 hashtags at the end (#iOSDev #AndroidDev #Localization); skip hashtags on X and Bluesky.
- Attach the clip as a native video (the `-square.mp4` files are 1080 x 1080 and silent with burned-in subtitles). Add alt text to every clip.
- Mastodon instances usually ask that promotional posts be marked or kept occasional; check your instance's rules. Don't tag people, don't ask for reposts, don't DM.
- Disclosure: thread post 1 says "I made"; every standalone post says "I made" or "my tool" too.

**Clips** (on `origin/claude/demo-video` in `marketing/demo-video/web/`, and on the site at `/media/demo/`): c1-doctor, c2-init, c3-run-ios, c4-run-android, c5-check, c6-check-existing, c7-store-rules, c8-export, c9-ci. They're real recordings on the repo's fixture app (5 languages), not WOD Tracker; the subtitles say "my app", so don't add a caption saying it's a real store app.

## Best time

Weekdays, 14:00 to 17:00 Netherlands time (morning US East, afternoon Europe). Thread on launch day; standalone posts one or two a week after that, not all at once.

---

## Thread (5 posts)

**1/5** [255], clip: `c3-run-ios-square.mp4`
> I made a Mac tool for App Store and Google Play screenshots in every language.
>
> You write one Maestro flow in English. It runs that flow in every language your app has, on several simulators at once, then checks every screenshot.
>
> It's called shotfleet. 🧵

Alt text: "Terminal: shotfleet run captures 5 languages on 2 iPhone simulators, sped up 29 times, then a grid of the real screenshots."

(The one emoji is optional; drop it if you prefer none.)

**2/5** [268], image: `site/public/img/bug_zh.jpg`
> Why I built it: on a small Android phone, my onboarding's Next button was out of reach in Japanese, Korean, Chinese and Arabic. Taller text, a page that didn't scroll.
>
> English fit, so I never saw it. The screenshot run got stuck there. The fix: make two pages scroll.

Alt text: "Chinese onboarding page on a small phone, with no Next button visible."

**3/5** [224], clip: `c5-check-square.mp4`
> The check reads the text in each screenshot and compares it with your app's own strings.
>
> Here I put a German screenshot in the Japanese folder on purpose. Caught. It also flags blank screens and sizes the stores won't take.

Alt text: "Terminal: shotfleet check reports that the Japanese screenshot shows German strings, and that one image appears in two languages."

**4/5** [257], clip: `c6-check-existing-square.mp4`
> check is free, and it works on screenshots you already have, also fastlane snapshot and screengrab folders. No Maestro, no account.
>
> On the old Play screenshots of another of my apps it found 103 translated captions over an app still in English. My mistake.

Alt text: "Terminal: shotfleet check on a plain folder labelled German finds Japanese strings. No simulator used."

**5/5** [270], no media
> One run on my M1 Pro: 18 languages x 4 screens, 9 min on iOS, 15 on Android.
>
> Apple silicon Macs only. Free: check, and 2 languages. Every language: $29 for the first 100 buyers, then $49, one-time.
>
> brew install noloman/tap/shotfleet
> https://shotfleet.com/?utm_source=x

---

## Standalone posts (5)

**A. The Turkish clash** [255], clip: `c2-init-square.mp4`
> In Turkish, "Next" and "Advanced" are the same word: İleri.
>
> My tool rewrites a Maestro flow's taps into every language from the app's own strings, so that clash would tap the wrong button. It warns before the run now.
>
> https://shotfleet.com/?utm_source=x

Alt text: "Terminal: shotfleet init finds 5 languages in an iOS build and an Android APK and writes a config and an English flow."

**B. Store rules** [264], clip: `c7-store-rules-square.mp4`
> Your app runs on iPad? Then the App Store wants 13-inch iPad screenshots too.
>
> shotfleet check (my tool, free) flags that, and any screenshot size the stores won't take. Here: one image resized to 1000x2000, caught by name.
>
> https://shotfleet.com/demo?utm_source=x

Alt text: "Terminal: shotfleet check reports the missing 13-inch iPad set, then names a 1000 by 2000 screenshot as not an App Store size."

**C. Android in one flow** [246], clip: `c4-run-android-square.mp4`
> Same English Maestro flow, now on Android emulators: per-app language on each one, 5 of 5 languages, 0 problems.
>
> One flow for iOS and Android, no copy per language. I made this for my own 18-language app.
>
> https://shotfleet.com/demo?utm_source=x

Alt text: "Terminal: shotfleet run on 2 Android emulators, sped up 16 times, 5 of 5 languages and 0 problems, then a grid of the real screenshots."

**D. CI** [230], clip: `c9-ci-square.mp4`
> shotfleet check in CI: it only needs a macOS runner, no simulator. --json for the result; exit code 0 means all good, 1 means problems, 2 means a setup error.
>
> I made it, and check is free.
>
> https://shotfleet.com/docs?utm_source=x

Alt text: "A GitHub Actions workflow that installs shotfleet and runs check, then check --json printing exit code 0."

**E. AnywhereRoles before and after** [247], no clip (or a pair of the AnywhereRoles frames from the home page once they're live)
> Before: check found 127 problems on my app's old Play screenshots. 103 were translated captions over an app still in English.
>
> After recapturing with my tool: 120 Android and 108 iPhone screenshots, 0 problems.
>
> https://shotfleet.com/?utm_source=x

---

## Before posting

- Gate 1 (0.1.5 live) for "screengrab folders" and the brew line; gate 2 (AnywhereRoles live) for thread 4/5 and post E. Without gate 2: in 4/5 use "it flagged 108 of 120 store screenshots of another of my apps: translated captions over an app still in English"; skip post E.
- Re-count after any edit. A quick way: `python3 -c "import sys; print(len(sys.stdin.read().strip()))"` and paste the post.
