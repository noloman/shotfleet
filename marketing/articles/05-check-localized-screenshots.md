# Article 5: check that every localized screenshot is in its language

Status: draft for Manu to publish. Not published. Written 2026-10-06 by the SEO pass (research/seo-audit-2026-10-06.md section 8).

| Field | Value |
|---|---|
| Title (H1) | How to check that your localized App Store and Google Play screenshots are really in each language |
| Title tag (under 60 chars, the search-result title) | How to check localized App Store and Play screenshots |
| Meta description (under 160 chars) | Translated captions over an English app, English copied into every folder, a missing screen: how to find each one by hand, and with one free command. |
| Slug | `/check-localized-screenshots` |
| Target query | check localized app store screenshots / verify localized screenshots / app store screenshots wrong language / localized screenshots show english |
| Why this can rank | The results for these queries are design-tool vendors (LocaShot, AppShotter, Lingue) and generic advice ("have a native speaker review them", "match the UI language to the locale"). Nobody shows how to find the problem in a folder you already have (web search, 2026-10-06; see research/seo-audit-2026-10-06.md section 6). |
| Canonical | Our domain. Any cross-post must point its canonical URL here. |

## Internal link plan

- Product: link "shotfleet" once in the intro (disclosure) to `https://shotfleet.com/`, and the docs check section `https://shotfleet.com/docs#check` where the commands are.
- Other articles: article 1 (fastlane snapshot all in English) from the "the app never got the language" cause; article 3 (the button nobody could reach) from the end.
- Comparison: `https://shotfleet.com/alternatives` where other tools come up.
- Overlap: 04-ideas.md item 4 (QA checklist, 10 failures) covers the same ground in a longer form. Publish this one first; when item 4 is written, link it from here or merge it into this page, not a second URL for the same query.

## TO VERIFY BEFORE PUBLISHING

1. The example result lines quoted in "What the output looks like" are copied from recorded runs (claims C179 and the article 1 TO VERIFY item 2), not from a fresh run. Re-run `shotfleet check` on one clean and one broken folder with the current release and paste its real lines, or keep these and say which version printed them.
2. The `ls MyApp.app/*.lproj` check (ticked for article 1 item 4 on a String Catalog build) and the Android source-folder advice: confirm the `values-<lang>` folders match what the built APK ships on one real app (research/real-apps.md lists subscrifi: 8 shipped = repo values-*).
3. Read the docs check section on the day and make sure every rule listed under "With one command" is still in it (store rules change with releases).
4. This page links article 1 (`/guides/fastlane-snapshot-screenshots-all-english`). Publish it together with or after article 1, never before, or that link is a 404.
5. Get one screenshot pair for the page (a German caption over an English app), from one of my own apps, with width and height set and alt text that describes both languages. The 108 of 120 numbers on the home page come from such a set (claims, home page "108 of 120").

Sources used (read 2026-10-06):
- https://shotfleet.com/docs#check (the commands and the list of what check reports)
- Home page numbers: "108 of 120 store screenshots of another of my apps flagged by shotfleet check: the captions were translated, but the app under them was still in English"
- Claims backing shotfleet sentences: C022, C024, C025, C026, C048, C072, C175, C177, C179, C210 (proven or evidence).

---

# How to check that your localized App Store and Google Play screenshots are really in each language

The short answer: compare the text in each screenshot with your app's own translations for that language. If the German folder shows English words, it's wrong. You can do it by hand for a few languages, or with one free command for all of them.

I make a tool for this (shotfleet, which comes up below), so keep that in mind. The checks by hand need nothing from me.

## What goes wrong

These are the six failures `check` looks for. I found the first three in my own apps' store folders:

1. **The English set copied into every language folder.** Someone needed screenshots for every listing, so English went everywhere.
2. **Translated captions over an English app.** The marketing text on top is German, but the app under it is still in English. In one of my apps, shotfleet's check flagged 108 of 120 store screenshots for this.
3. **A listing in a language the app doesn't have.** The store page is in Traditional Chinese, but the app has no Traditional Chinese, so the screenshots can't be in it.
4. **A language with fewer screens than the others.** One run failed halfway and nobody noticed.
5. **The same image in two languages.** Often a screen with no text, sometimes a copy by mistake.
6. **Sizes or counts the store refuses.** Too many screenshots for one listing, a transparent image, or a missing iPad set.

## Check by hand

Start with what your build really ships. On iOS, every language is a folder inside the app:

```bash
ls MyApp.app/*.lproj
```

A String Catalog with no explicit English entries has no `en.lproj`, because English is the key. On Android, look at the `values-<lang>` folders of your app module.

Then open each language folder of screenshots and look for three things: words in the wrong language in the app's own UI (not only in the caption), a screen that looks the same as in English, and a folder with fewer files than the others. For languages you can't read, compare the shape of the text with the English screen: if the lines have exactly the same length and the same words in the same places, it's probably English.

This works for three or four languages. With twenty, nobody does it carefully.

## With one command

`shotfleet check` reads every screenshot and compares its text with your app's strings. It's free and it doesn't need Maestro. Point it at your fastlane folder and your build:

```bash
shotfleet check fastlane/screenshots                       # fastlane snapshot
shotfleet check fastlane/metadata/android                  # fastlane screengrab
shotfleet check fastlane/ --app path/to/MyApp.app          # a fastlane folder with both
shotfleet check shots/ --locale en --app path/to/MyApp.app # a flat folder of one language
```

It reports the wrong language, copies, missing screens, listings in a language your app doesn't have, and the store rules: sizes, at most 10 (App Store) or 8 (Play) per listing, no transparency, a 6.9" or 6.5" iPhone set, and a 13" iPad set when the app runs on iPad. The full list is in the [docs](https://shotfleet.com/docs#check). Your folders are never changed; the report goes to `./shotfleet-check`.

Pass `--app` (or `--strings` for Flutter, React Native and other frameworks) when you can. Without a build it relies on language detection, which can't judge short screens.

## What the output looks like

On a real fastlane snapshot set of one of my apps (English and German), it said:

```text
checked 24 screenshots in 2 languages: 13 problem(s)
```

Eleven of those were German screens whose app UI was still English. On a clean set of another app, 220 screenshots in 20 languages:

```text
checked 220 screenshots in 20 languages: 0 problem(s)
```

Any problem makes `check` exit with 1. That's what makes it useful before an upload: put it between `snapshot` and `deliver` in a fastlane lane, and a wrong set stops the lane. The lane is in the [docs](https://shotfleet.com/docs#fastlane-lane).

## What it can't see

- Scripts macOS text recognition can't read (Greek, Hebrew, most Indic scripts). For those, `check` still catches copies and missing screens and says which screens it couldn't read, or you give it Tesseract.
- Very short screens with no build to compare against.
- Anything that isn't in the image: your store description, your keywords.

If your screenshots come from fastlane snapshot and they're all English, the cause is usually in the setup, not the app: see [why your fastlane snapshot screenshots are all in English](https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english). Other tools, and when not to use mine, are on the [comparison page](https://shotfleet.com/alternatives).
