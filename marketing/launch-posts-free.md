# Launch drafts

Drafts only. Post them yourself, under your own name. Every number below comes from the README (the Quickspan run, the by-hand baseline). Check each community's current self-promotion rules before posting; they change.

Posting tips that apply to all of them:

- Be present for the first two hours to answer questions. That matters more than the wording.
- Don't ask for upvotes or stars anywhere, and don't cross-post the same text on the same day.
- If someone points out a limit, agree with it plainly. The guide has an honest list of limits.

---

## 1. Show HN

**Title** (keep under 80 characters):

> Show HN: Shotfleet – localized app store screenshots from one English Maestro flow

**URL:** https://github.com/noloman/shotfleet

**First comment** (post it right after submitting; HN prefers a text comment over a long pitch):

> Hi HN, I'm the author. I ship an Android/iOS app in several languages, and every release I hit the same chore: store screenshots in every language. The UI script taps English buttons, so it can't run in German or Japanese without a copy per language, and in practice the English set ends up copied into every folder.
>
> shotfleet takes one Maestro flow written in English, reads the translations compiled into your built app, and rewrites the taps per language ("Next" becomes "Weiter" or "次へ"). It runs all languages in parallel on simulators/emulators, then checks the results against your app's own text and the store rules: wrong-language screenshots, copies across languages, blank frames, missing screens, wrong sizes. `shotfleet export` writes the folders fastlane's `deliver` and `supply` expect and skips any language that failed a check.
>
> A real run: my own app Quickspan, 5 languages x 5 screenshots on one Android emulator, 25 screenshots, 0 problems, 343 s to capture. By hand I measured about 1.5 hours for 17 screenshots in 2 languages (roughly 2.5 minutes per screenshot per language), which is where the "20 languages is about 15 hours" estimate in the README comes from.
>
> Honest limits: it needs a Mac (Apple silicon for the installer), it depends on Maestro, and on Maestro 2.0.10 per-language text inputs are ignored on Android (fixed in 2.11.0; the case study documents both runs). The guide lists the rest.
>
> It was a paid product for a short while with zero sales, so I made it free and MIT licensed. If it's useful to you there's a GitHub Sponsors link in the README, but nothing is gated. Feedback on frameworks that don't work well is the most useful thing you could give me.
>
> Repo: https://github.com/noloman/shotfleet — Site: https://shotfleet.com

---

## 2. r/androiddev

**Title:**

> I got tired of hand-capturing Play Store screenshots in every language, so I built an open source tool for it (free, MIT)

**Body:**

> I ship an Android app in 5 languages and the screenshot chore was eating hours every release: 17 screenshots in 2 languages took me about 1.5 hours by hand.
>
> The problem is that a UI automation script taps English text, so it breaks in other languages. shotfleet reads the strings compiled into your debug APK, translates a single English Maestro flow for each language, runs the languages in parallel on emulators, and then checks the output (wrong language, copies, blank frames, missing screens, Play Store size and count rules). `shotfleet export` writes the `supply` folder structure for fastlane.
>
> On my own app (Quickspan, 5 languages x 5 screenshots, one emulator) it captured 25 screenshots in 343 s with 0 problems flagged. It works with native Android, Compose Multiplatform, Flutter, React Native and others, since it reads translation files.
>
> Limits I know about: it runs on macOS, uses Maestro, and Maestro 2.0.10 ignores per-language text inputs on Android (2.11.0 fixes it).
>
> It's free and MIT licensed. Repo: https://github.com/noloman/shotfleet
>
> If you try it and hit a framework or screen it can't handle, please open an issue; that's the most useful feedback I can get.

*Rule note:* r/androiddev limits self-promotion and may want this in the periodic showcase thread or flaired as a project. Read the sidebar and pick the matching flair or thread before posting. If it is removed, repost in the showcase thread.

---

## 3. r/iOSProgramming

**Title:**

> Open source: localized App Store screenshots from one English Maestro flow, with a check for wrong-language and copied screenshots

**Body:**

> Localized App Store screenshots tend to end up as the English set copied into every language folder, because the UI script taps English buttons.
>
> shotfleet translates one English Maestro flow per language using the strings compiled into your built app, runs all languages in parallel on simulators, and checks every screenshot (wrong language, duplicates across languages, blank frames, missing screens, App Store size and count rules). `shotfleet export` writes the folders `deliver` expects and skips any language that failed a check.
>
> Numbers from a real run on my own app (Android in that case, 5 languages x 5 screenshots, 343 s, 0 problems). By hand I measured about 2.5 minutes per screenshot per language, so 20 languages is roughly 15 hours every release.
>
> Works with native iOS, Flutter, React Native, Compose Multiplatform, .NET MAUI and Unity. Needs a Mac. Free and MIT licensed: https://github.com/noloman/shotfleet
>
> Happy to hear what breaks on your app; I'd rather fix real cases than guess.

*Rule note:* r/iOSProgramming has restrictions on self-promotion. Check the sidebar first. The only run with published numbers is on Android; say so if asked about iOS timings, and don't invent iOS figures.

---

## 4. dev.to article

**Title:** How I stopped hand-capturing store screenshots in 5 languages

**Tags:** android, ios, testing, opensource

**Body:**

Every release I used to spend an afternoon on store screenshots. Not designing them, just capturing them: launch the app, switch the device language, tap through the same five screens, repeat for the next language. When I timed it on my own app, 17 screenshots in 2 languages took about 1.5 hours. That is roughly 2.5 minutes per screenshot per language. At 20 languages it would be around 15 hours, and it repeats at every release.

### Why the obvious automation fails

The standard answer is to script it with a UI automation tool. I use [Maestro](https://maestro.mobile.dev). The catch is that the script taps text: "Next", "Settings". In German those buttons say "Weiter" and "Einstellungen", so the script only works in English, and keeping one copy per language doesn't scale. In practice, people end up with the English screenshots copied into every language folder, and the store listing looks untranslated.

### The approach

The translations already exist: they are compiled into your app. So:

1. Write the flow once, in English.
2. Read the strings from the built app and rewrite each tap per language ("Next" becomes "Weiter" or "次へ").
3. Run every language in parallel on simulators or emulators.
4. Check the result before it reaches a store.

I built this as an open source tool, [shotfleet](https://github.com/noloman/shotfleet). A project looks like this:

```bash
shotfleet doctor --fix        # checks Maestro, Java, Xcode, Android SDK
shotfleet init                # writes shotfleet.toml and a starter flow.yaml
shotfleet run --locales en    # try one language first
shotfleet run                 # then all of them
shotfleet export out --fastlane fastlane/
```

### What the check catches

This is the part I care about most. A run that "finished" can still produce bad screenshots, so shotfleet checks each one against your app's own text and the store rules:

- a screenshot in the wrong language,
- the same screenshot copied across languages,
- blank frames and missing screens,
- ambiguous translations (flagged before anything runs),
- the size and count limits of both stores.

Problem screenshots are outlined in red on a review page (`out/index.html`), a grid with a row per language and a column per screen. `shotfleet export` skips any language that failed a check, so a bad set doesn't get uploaded by accident.

### A real run

I used it on [Quickspan](https://github.com/noloman/adaptive-calendar), my own Android app: 5 languages (en, de, ja, ko, es) x 5 screenshots on one emulator. That is 25 screenshots, 0 problems flagged, 343 seconds to capture.

It wasn't flawless, and the case study says so. On Maestro 2.0.10 the text typed into the first screen was identical in every language, because that version ignores per-language `[inputs]` on Android. After upgrading to Maestro 2.11.0, a rerun for de, es and ko (15 screenshots, 0 problems) typed the phrase in each language.

### Limits

It needs a Mac and it depends on Maestro. The [guide](https://github.com/noloman/shotfleet/blob/main/docs/guide.md) has the honest list.

### Free and open source

I originally sold it, and it sold nothing, so it is now free and MIT licensed. If it saves you time and you want to support its upkeep (keeping up with Xcode, Android and Maestro changes), there's a [GitHub Sponsors](https://github.com/sponsors/noloman) page. Starring the repo or filing a good bug report helps just as much.

Repo: https://github.com/noloman/shotfleet — Site: https://shotfleet.com
