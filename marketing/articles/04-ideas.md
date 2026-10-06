# Article ideas 4 to 8 (outlines, in publishing order)

Written 2026-10-02 from research/marketing-research.md section 3.4. One article a week after launch (MARKETING.md phase 2). Each ends with the same free next step: `shotfleet check` on a folder the reader already has. Rules for every one: first person (Manu), no hype, no invented numbers, every shotfleet sentence backed by a claim marked proven or evidence in tests/claims.json (or the code), no claims about Flutter or React Native on real apps, frames, captions, store upload or Maestro endorsement. Every technical step must have been run before publishing; the "Run first" line says what.

Do not write for head terms ("app store screenshot sizes", "best screenshot tools"). Vendors with hundreds of pages own them.

---

## 4. Localized app store screenshots QA checklist: 10 ways a localized listing is wrong

- Slug: `/localized-screenshots-qa-checklist`
- Target query: localized app store screenshots checklist; app store screenshot rejection 2.3.3; verify localized screenshots.
- Angle: only failures that were actually seen, with the folder name and the check that finds each. Competitors' checklists are generic; this one has data.
- Outline:
  1. The English set copied into every language folder (the starting point of the whole project).
  2. Translated captions over an app that is still in English (found in my own committed fastlane folders: Traditional Chinese listings; check `shotfleet check` output, claims C030).
  3. A listing in a language the app does not have (same example).
  4. A language that produced fewer screenshots than the others (missing).
  5. The same image in two languages (copies; note the 40 character blind spot for very short screens, claims C003).
  6. Sizes the store does not accept; count above 10 (App Store) or 8 (Play); transparency; 6.9" or 6.5" iPhone set missing; 13" iPad set missing when the app runs on iPad (claims C022).
  7. Play notes: 320 to 3840 px per side and the recommendation rule (README check section).
  8. Two words that translate to the same string, so a UI test taps the wrong button (Turkish "Next" and "Advanced", both "İleri").
  9. A button the flow cannot reach in long languages (link article 3).
  10. Dialogs drawn by the OS in a different language than your app (README tips).
  Each item: what it looks like, how to find it by hand, how `check` reports it, the Apple or Google spec link.
- Run first: re-run `shotfleet check` on a folder with each planted failure and paste real output. Link the official Apple screenshot specifications and Google Play preview assets pages; re-read them the day you publish (limits change).
- Honest paragraph: what `check` cannot see (scripts macOS cannot read, very short screens, anything outside the image).
- Overlap: article 5 (05-check-localized-screenshots.md, drafted 2026-10-06) answers the short query "check localized screenshots". When this checklist is written, merge it into that page or link the two; do not publish two pages for the same query.
- Priority: medium. This is where a unique data set matters, so wait until at least one design partner has shared a real before and after (with written permission).

## 5. Automating Google Play screenshots in every language with emulators and fastlane supply

- Slug: `/google-play-screenshots-every-language-emulators`
- Target query: google play screenshots every language automate; fastlane screengrab locale; android emulator screenshots multiple languages.
- Angle: Android is under-served compared with iOS. Show the manual path (per-app locales on API 33+, emulator images, fastlane supply folder layout `metadata/android/<locale>/images/phoneScreenshots/`), then the honest cost: 18 languages by 4 screens took 15 min 24 s on one Mac with 4 emulators (claims C007), versus iOS 9 min.
- Outline: the Play rules (2 to 8 screenshots, 320 to 3840 px; cite Google's page and re-read it); per-app languages arrived in Android 13 (API 33), see developer.android.com/guide/topics/resources/app-languages; setting a language from the shell (verify the `cmd locale set-app-locales` command, see article 2); why `clearState` resets the language; read-only emulators and snapshot boots (ROADMAP: 4 to 5 s instead of 21 to 23 s per boot); the `fastlane supply` upload command from the README, screenshots only.
- Run first: every adb command on a real API 33+ emulator; the supply command on a test track (never production). Re-time with the stated machine (M1 Pro, 32 GB, claims C007) and say the machine.
- Honest paragraph: needs API 33+ emulators; tablet sets only as far as the README says; no upload, fastlane does that.
- Link target for Android Weekly, Kotlin Weekly and KMP Weekly submissions (marketing/kit/newsletters.md) if article 3 is not accepted first.

## 6. fastlane snapshot alternatives in 2026: an honest table

- Slug: `/fastlane-snapshot-alternatives`
- Target query: fastlane snapshot alternative.
- Angle: free options first, with a "when not to buy this" column that includes shotfleet. Honest comparison pages get linked and quoted. The SERP is contested by vendors, so this is sixth.
- Outline: table of fastlane snapshot and screengrab, Maestro with `--device-locale` (docs), StoreScreens CLI, asc CLI, simshot, ButterKit and AppScreens as framing complements, shotfleet. Columns: what it does, platforms, price, what it checks, who should not use it. Then a short section "capture with anything, check with shotfleet".
- Facts to re-check the day you publish (prices change): ButterKit Pro (the repo notes $99 one-time on its site and a different figure in one Mac App Store snippet; open both before writing a number), AppScreens Pro and Scale per year, Maestro Cloud per device per month, simshot status. A draft already exists at `site/draft/alternatives.html`; do not publish it until claims C094 (fastlane "one language after another") is reworded to "runs your languages one after another on each simulator" and the table row about parallel is checked against fastlane's `concurrent_simulators` option.
- Run first: a timed head-to-head of fastlane snapshot versus shotfleet on the same app, with setup time and run time, if the article claims any comparison number. Not done yet (research 4.1). Without it, say nothing about relative speed.
- Honest paragraph: for a single language, one platform, or an existing UI-test suite, fastlane is the better answer.

## 7. iOS permission alerts stay English while your app is German: what that does to UI-test taps

- Slug: `/ios-permission-alerts-stay-english-ui-tests`
- Target query: maestro permission dialog localization; ios permission alert language ui test; maestro allow while using app german.
- Angle: tiny, precise, nobody else measured it. System permission alerts are drawn by iOS in the device language, which stays English when you only change the app's language with launch arguments. I measured this once with Maps on `main` (research/pricing-2026-10.md). A flow that taps "Allow While Using App" keeps working because the text is English; one that taps a translated label does not.
- Outline: the measurement (what was run, on which iOS), the Maestro issue about English-only permission dialog dismissal (#2654, open when last read; re-read), the `launchApp: permissions: all: allow` workaround from the README, the Android side (shotfleet installs with every permission granted; this half is untested, do not claim it).
- Run first: repeat the measurement on a second app and on the current iOS; screenshot the German app with an English alert. Do NOT claim live permission-alert taps in shotfleet (the launch posts forbid it, claims C070 is partial).
- Priority: low effort, good for newsletters.

## 8. Plural forms in screenshot flows: "Round 2 of 12" in Arabic, Russian and Polish

- Slug: `/plural-forms-screenshot-flows`
- Target query: localized plural forms ui test; arabic plural forms android strings; cldr plural categories.
- Angle: link bait for the localization crowd. CLDR plural categories differ by language (Arabic six, Russian four, Polish four, Japanese one; confirm on https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html the day you publish). A tap selector for "Round 2 of 12" has to match every plural form, and numbers have to be translated with the same numbers.
- Outline: why a string with a number cannot be matched by its template alone; what the stringsdict and Android `<plurals>` tables look like; how shotfleet matches a label with numbers in every plural form (README Limits, claims C015); one worked example per language with real output from the tool.
- Run first: generate the real translated selectors for one app in ar, ru, pl and paste them; verify them by reading the app's strings by hand.
- Priority: lowest. Write it after the sale has data.

---

## Order and gates

| # | Title (short) | Gate before writing |
|---|---|---|
| 4 | QA checklist | One real before and after, with permission |
| 5 | Google Play in every language | Run every adb and supply step |
| 6 | fastlane alternatives | Prices re-read; C094 reworded; head-to-head only if timed |
| 7 | Permission alerts | A second measurement |
| 8 | Plural forms | Real tool output in three languages |

Blocked until proof exists: any "Flutter or React Native localized screenshots" article. Readers loaded real translation files, but no real Flutter or React Native app has been run (README Limits). Write it only after one real run.
