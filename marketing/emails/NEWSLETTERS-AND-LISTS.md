# Newsletters and awesome lists: ready-to-use submissions

For Manu. Written 2026-10-07. **Drafts only.** Nothing was submitted, emailed, opened as a PR, commented or signed in. You approve each item by number (N1, N2, ...), then send it yourself, once.

Angle: we submit the two GUIDES as articles. shotfleet is only the tool the guide mentions. Maestro guide for Android, Kotlin and testing readers; fastlane guide for iOS and Swift readers.

| # | Target | Type | Route | Readers | When | Status |
|---|---|---|---|---|---|---|
| N1 | iOS Dev Weekly (this also covers SwiftLee Weekly, see N2) | newsletter | form https://suggest.iosdevweekly.com | 40k+ | Thu 15 Oct (or Fri 9 to Mon 12 Oct if 0.1.6 is live) | after 0.1.6 |
| N2 | SwiftLee Weekly | newsletter | no own route: Antoine's page says to use the iOS Dev Weekly form or the iOS Dev Directory | 30k+ | same submission as N1, nothing extra | covered by N1 |
| N3 | Android Weekly | newsletter | form at the bottom of https://androidweekly.net/#submit-stuff ("What do you want to submit?") | 80k+ | same day as N1 | after 0.1.6 |
| N4 | Kotlin Weekly | newsletter | email mailinglist@kotlinweekly.net | 22.9k | day after N3 | after 0.1.6 |
| N5 | Software Testing Weekly | newsletter | Tally form https://tally.so/r/5BW4vN | 9.3k | Mon 12 Oct (not 13-14) or Mon 19 Oct; their issue is Friday | after 0.1.6, promo risk |
| N6 | Fatbobman's Swift Weekly | newsletter | email fatbobman@gmail.com (public on his About page; no submission form exists) | 5k+ | same week as N1, after it | after 0.1.6, low odds |
| N7 | Last Week in Flutter | newsletter | no route found (Substack, no About/contact text) | ? | after the Flutter/RN guide is live | find contact, after guide 3 |
| N8 | React Native Newsletter | newsletter | form https://reactnativenewsletter.com/submit | monthly | only after the Flutter/RN guide is live | hold (guide 3 not live) |
| N9 | KMP Weekly | newsletter | https://kmpweekly.com/submit or hello@kmpweekly.com | ? | no issue since Feb 2026 | low, hold |
| N10 | jetc.dev, Flutter Weekly, This Week In React, Changelog News and the rest of the dead/skip list | newsletter | none | n/a | never | skip |
| L1 | jaywcjlove/awesome-mac (115k stars) | awesome list | PR (4 files) | n/a | any day after 0.1.6 | after 0.1.6 |
| L2 | rafaecheve/Awesome-ASO | awesome list | PR | n/a | any day after 0.1.6 | after 0.1.6 |
| L3 | ludovicobesana/awesome-maestro, tool entry | awesome list | PR | n/a | any day after 0.1.6 | after 0.1.6 |
| L4 | ludovicobesana/awesome-maestro, article entry (Maestro guide) | awesome list | PR (own PR, rules say one thing per PR) | n/a | after the guide is live | after 0.1.6 |
| L5 | ZoranPandovski/awesome-testing-tools | awesome list | PR | n/a | after L3 merges, or skip | weak fit |
| L6 | punkpeye/awesome-mcp-servers | awesome list | PR | n/a | needs a public GitHub repo and a Glama listing | hold |

Skip, don't submit: awesome-ios, awesome-swift, awesome-cli-apps, awesome-i18n, awesome-android, awesome-kotlin, awesome-flutter, awesome-react-native (they reject closed-source or paid tools); iCHAIT/awesome-macOS is unlikely. Dead or no route: iOS Goodies, #AndroidDev Digest, Indie iOS Focus, This Week in Swift, Swift by Sundell, Flutter Weekly, Changelog News (refuses tutorials and commercial products), This Week In React (sponsor only), Bytes, Phiture ASO Monthly (no submission address).

---

## Read this first

**"After 0.1.6" means:** `curl https://shotfleet.com/download/VERSION` says `0.1.6` AND `https://shotfleet.com/guides/maestro-one-flow-every-language` returns 200. Checked today: VERSION is `0.1.5`, `/guides` and both guide URLs are 404. Every newsletter item links a guide, so none can go before both are true. Re-check the URL right before each send.

**Calendar:** nothing public on Tue 13 and Wed 14 Oct (Keysi launch). Window A: Fri 9 to Mon 12 Oct, only if 0.1.6 is live by then. Window B: Thu 15 to Sun 18 Oct, ahead of launch week (19 Oct, Show HN 20 or 21 Oct). Newsletters need about a week of lead, so aim for A, fall back to B. Don't submit any of them in launch week; it clutters the launch and the Show HN has the day.

**Facts I checked today, and what differs from the earlier drafts (8 to 17 in EMAIL-DRAFTS.md):**
- shotfleet.com has **no RSS or Atom feed** (`/rss.xml` and `/feed.xml` are 404, no `<link rel="alternate">` on the home page). So the iOS Dev Directory route (draft 8's first choice) is not possible. The form is the route. If you want the directory later, add a feed first. That also means SwiftLee Weekly has no separate route: Antoine's own page says he finds articles through the directory, iOS Feeds and the iOS Dev Weekly form, and caps each issue at five links.
- Draft 8 used "108 of 120 store screenshots flagged on my own apps". The fastlane guide says something different (252 committed iOS images of the workout app, one real problem: Traditional Chinese captions over an app still in English). The newsletter text now uses only what the guide says, so a reader who clicks finds the same numbers. Use the 108 of 120 figure only if it is in a published page.
- Draft 9 had no exact route for Android Weekly. It is the "What do you want to submit?" block at the bottom of the home page (anchor `#submit-stuff`), with the line "Links in each issue will be chosen by us. Please be aware that we can't pick every link." I did not open the form, so field names are unchecked.
- Draft 10 (Kotlin Weekly) pitched article 3 ("the button nobody could reach"), which is not published (it is only in `site/draft/guides/`). N4 now pitches the live Maestro guide and keeps the scrollUntilVisible detail.
- Drafts 14 to 16 used the slug `flutter-localized-store-screenshots`. The real draft file is `flutter-react-native-localized-screenshots` ("Flutter and React Native screenshots in every language"), and it is **not published** (`site/draft/guides/`, article 06 says "Not published"). N7 and N8 are held for it. Draft 14's Flutter Developer Weekly: flutterdeveloperweekly.com loads but the research list marks Flutter Weekly dead, and I could not confirm a recent issue, so I dropped it.
- **0.1.6 and XCUITest:** the guides don't mention it, and it is still "not run end to end on a device yet". None of the texts below mention it. Draft 8's optional 0.1.6 sentence is removed on purpose; add it only after the device run passes.
- The Maestro guide mentions React Native in one sentence. That's not an RN angle, so N8 waits for the Flutter/RN guide.
- Software Testing Weekly's form says: not all links can be included, articles 1 to 2 weeks old are preferred, and **product or service promotional articles must go through their sponsorship page**. The Maestro guide is mostly plain Maestro and adb and says up front that the tool is mentioned once, so I think it passes as an article, but it can be treated as promotional. Say so openly (the text does), and accept a "no" or a sponsorship reply as the answer.

**Rules for all:** once per target, no follow-up chain, silence is an answer. One ask each. No money or licence offered for coverage. Honest about limits: closed source, paid, Apple silicon Mac only. Mention the price at most once; the newsletter texts below don't mention it at all (the guide does). Log each send (date, target, utm_source) in one note.

---

## N1. iOS Dev Weekly (and SwiftLee Weekly)

- **Route:** form https://suggest.iosdevweekly.com. Fields (read today): name, email address, link, who published it (source/author), blog post yes/no, Swift library yes/no, reason. The form asks you not to submit links from blogs already in the iOS Dev Directory; shotfleet is not in it, so the form is fine. Don't also add shotfleet to the directory (pick one route).
- **When:** Thu 15 Oct, or Fri 9 to Mon 12 Oct if 0.1.6 is live. One submission also reaches SwiftLee Weekly's curator (N2).
- **Prerequisite:** the fastlane guide URL returns 200.
- **Name:** Manu Lorenzo
- **Email:** the address you want replies at
- **Link:** `https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english?utm_source=iosdevweekly&utm_medium=newsletter`
- **Who published it:** I wrote it (shotfleet.com)
- **Blog post:** yes. **Swift library:** no.
- **Reason:**

> Why every language folder from fastlane snapshot can be English: five causes to rule out in order (setupSnapshot after launch, running from Xcode, the Simulator language, a build without that language's strings, an app that remembers its own language), with the fastlane issue threads behind them. It ends with a free way to check each screenshot against your app's own strings. I make the tool it mentions at the end, closed source and paid; the first four steps need nothing from me.

## N2. SwiftLee Weekly

- **Route:** none of its own. https://swiftlee-weekly.com/for-writers/ points to the iOS Dev Directory and the iOS Dev Weekly form. N1 is the submission. Don't write to Antoine separately.
- **Status:** covered by N1.

## N3. Android Weekly

- **Route:** the "What do you want to submit?" block at https://androidweekly.net/#submit-stuff. Open it for the field names; paste the title, link and note below.
- **When:** same day as N1.
- **Prerequisite:** `/guides/maestro-one-flow-every-language` returns 200.
- **Title:** `Run one Maestro flow in every language: Android per-app locales, iOS launch arguments, and four traps`
- **Link:** `https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=androidweekly&utm_medium=newsletter`
- **Note:**

> How to run one Maestro flow in several languages: Android per-app locales (Android 13+, set with adb) and iOS launch arguments, plus four traps that quietly give you English, like a default in the flow header that beats the command line, and clearState wiping the app's language on Android. All plain Maestro and adb. I wrote it. I also make a paid tool in this area; it's mentioned once at the end.

## N4. Kotlin Weekly

- **To:** `mailinglist@kotlinweekly.net` (their site: "If you want to submit an article for the next issue, please do also drop us an email"). 22.9k readers; issue goes out on Sundays.
- **When:** the day after N3. Android Weekly readers overlap a little; one link on two lists is fine.
- **Prerequisite:** Maestro guide URL returns 200.
- **Subject:** `Link for submission - Kotlin Weekly`

> Hi,
>
> A guide for people who test or screenshot Android apps with Maestro: how to run the same flow in German, Japanese, Arabic and so on, using Android 13 per-app locales (`cmd locale set-app-locales`), and four traps that make every run quietly English. One of them is that `clearState` also clears the app's language. There's also a note on long translations pushing a button off the screen, fixed with `scrollUntilVisible`.
>
> https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=kotlinweekly&utm_medium=newsletter
>
> I wrote it. I also make a paid tool in this area, closed source; the guide mentions it once at the end and everything before that is plain Maestro and adb.
>
> Thanks,
> Manu

## N5. Software Testing Weekly

- **Route:** Tally form https://tally.so/r/5BW4vN ("Submit a link for the next issue"). I could read one visible field and the rules; the full field list wasn't readable. Contact for the editor (Dawid Dylowicz) is LinkedIn only: https://www.linkedin.com/in/dawid-dylowicz/. Use the form, not LinkedIn.
- **When:** Mon 12 Oct (if 0.1.6 is live) or Mon 19 Oct. The issue goes out Friday, they prefer articles 1 to 2 weeks old, so send within about 10 days of the guide going live.
- **Prerequisite:** Maestro guide URL returns 200.
- **Link:** `https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=softwaretestingweekly&utm_medium=newsletter`
- **Description (paste in whatever text box the form has):**

> A testing guide: how to run one Maestro flow in every language on iOS and Android, and the four traps that make every run pass while the screenshots are in English (a language default in the flow header, `-e` placed before `test`, Android `clearState` wiping the app language, parallel runs on two devices). Written from runs on Maestro 2.0.10. I wrote it. Disclosure: I make a paid tool for this; the guide mentions it once at the end, and the traps and commands stand without it. If you treat that as promotional, I understand.

## N6. Fatbobman's Swift Weekly

- **Route:** email `fatbobman@gmail.com`, public on https://fatbobman.com/en/about/. Neither the weekly page nor the About page states a submission policy, so this is a courtesy note; odds are lower.
- **When:** same week as N1, after it.
- **Prerequisite:** fastlane guide URL returns 200.
- **Subject:** `Link suggestion for Fatbobman's Swift Weekly: fastlane snapshot screenshots in English`

> Hi,
>
> In case it fits an issue: a guide on why fastlane snapshot screenshots can come out in English in every language folder, with five causes to rule out in order and the fastlane issues behind them. It ends with a free command that checks each image against your app's own strings.
>
> https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english?utm_source=fatbobman&utm_medium=newsletter
>
> I wrote it. I make the tool mentioned at the end (closed source, paid, Apple silicon Macs only); the first four steps need nothing from me. Thanks for the newsletter either way.
>
> Manu

## N7. Last Week in Flutter (Ryan Edge)

- **Route:** **find contact.** The Substack home page shows no submission text, and a search found none. Look in a recent issue's footer or reply to the issue email (Substack lets readers reply to the author). Don't guess an address.
- **When:** only after the Flutter/RN guide (`/guides/flutter-react-native-localized-screenshots`) is published. Not before.
- **Text, when it's live and you have a route:**

> Hi Ryan,
>
> A guide for Flutter readers: how to get App Store and Google Play screenshots in every language of a Flutter app, from one Maestro flow, and what went wrong on a real app (a white first frame on a fresh Android emulator, labels that don't match the translations).
>
> https://shotfleet.com/guides/flutter-react-native-localized-screenshots?utm_source=lastweekinflutter&utm_medium=newsletter
>
> I wrote it. I also make a paid tool the guide mentions; I've run it on one real Flutter app and one real Expo app, not more.
>
> Manu

## N8. React Native Newsletter (Infinite Red)

- **Route:** form https://reactnativenewsletter.com/submit. Fields: email address, Twitter handle, article category (blog post, video, node module, React Native app, other), article/video link, brief summary. Or newsletters@infinite.red; use the form. Monthly.
- **When:** only after the Flutter/RN guide is live. The Maestro guide alone has no real RN angle, so don't use it here.
- **Category:** Blog Post
- **Link:** `https://shotfleet.com/guides/flutter-react-native-localized-screenshots?utm_source=rnnewsletter&utm_medium=newsletter`
- **Summary:**

> How to get App Store and Google Play screenshots in every language from one Maestro flow for a Flutter or React Native app, tested on one real Expo app (the obytes template) and one real Flutter app. I wrote it; I make a paid tool the guide mentions, closed source.

## N9. KMP Weekly

- **Route:** https://kmpweekly.com/submit or hello@kmpweekly.com. No issue since Feb 2026, so probably dormant.
- **Status:** hold. Don't send. Nothing KMP-specific is published (draft 11 needed an article that doesn't exist).

---

## L1. awesome-mac (jaywcjlove/awesome-mac)

- **Route:** one PR, four files. Section "Developer Utilities" (zh "开发者工具", ja "開発者ユーティリティ", ko "개발자 유틸리티"; look up the exact heading in each file). The EN list is alphabetical here: put the line **between SecureCRT and Site Sucker**. In README-zh.md put it between SecureCRT and SnippetsLab; in README-ja.md between SecureCRT and Site Sucker; in README-ko.md SecureCRT isn't there, so put it between SaneHosts and SnippetsLab (Korean order is loose).
- **PR title:** `Add Shotfleet to Developer Utilities (EN/ZH/JA/KO)`
- **When:** any day after 0.1.6. It links the home page, not a guide.
- **Prerequisite:** none beyond 0.1.6. No paid/freeware icon: the list marks only freeware, open source and App Store.
- **README.md:**

```
* [Shotfleet](https://shotfleet.com/?utm_source=awesome-mac&utm_medium=awesome-list) - CLI that captures localized App Store and Google Play screenshots from one Maestro flow and checks each one.
```

- **README-zh.md:**

```
* [Shotfleet](https://shotfleet.com/?utm_source=awesome-mac&utm_medium=awesome-list) - 命令行工具,用一个 Maestro 流程为每种语言截取 App Store 和 Google Play 截图,并检查每张图。
```

- **README-ja.md:**

```
* [Shotfleet](https://shotfleet.com/?utm_source=awesome-mac&utm_medium=awesome-list) - 1つの Maestro フローから全言語の App Store / Google Play スクリーンショットを撮影し、各画像を検証する CLI ツール。
```

- **README-ko.md:**

```
* [Shotfleet](https://shotfleet.com/?utm_source=awesome-mac&utm_medium=awesome-list) - 하나의 Maestro 플로우로 모든 언어의 App Store 및 Google Play 스크린샷을 캡처하고 각 이미지를 검사하는 CLI 도구.
```

- **PR body:**

> Adds Shotfleet, a macOS command-line tool (Apple silicon) that captures App Store and Google Play screenshots in every language from one Maestro flow and checks them. Closed source, paid, with a free tier. Added to all four README files, alphabetical in Developer Utilities. I'm the author.

(Note: the zh/ja/ko lines are my translations, short and plain. Ask a native reader if you know one; the maintainer may fix them.)

## L2. Awesome-ASO (rafaecheve/Awesome-ASO)

- **Route:** one PR to README.md, section Tools, **after Screenproof** (before Shots and Shotlingo). Their rules: `[Name](link) - Description.`, name plus description under 100 characters, no marketing language, individual PR, commit message `Add Company Foo.io` style. Existing lines are numbered list items (`12. [Screenproof](...)`); copy the numbering style of the neighbours.
- **PR title:** `Add Shotfleet`
- **When:** any day after 0.1.6.
- **Entry:**

```
12. [Shotfleet](https://shotfleet.com/?utm_source=awesome-aso&utm_medium=awesome-list) - CLI that captures store screenshots in every language from one Maestro flow and checks them.
```

(Name plus description is 91 characters before the URL. Recount after any edit.)

- **PR body:** `Adds Shotfleet (macOS CLI, closed source, free tier) to Tools. I'm the author.`

## L3. awesome-maestro, tool entry (ludovicobesana/awesome-maestro)

- **Route:** PR to README.md, section "Tools and Integrations" (it's not alphabetical; add at the end of that section). One thing per PR.
- **PR title:** `Add Shotfleet to Tools and Integrations`
- **When:** any day after 0.1.6.
- **Entry:**

```
- [Shotfleet](https://shotfleet.com/?utm_source=awesome-maestro&utm_medium=awesome-list) - macOS CLI built on Maestro flows: runs one English flow in every language on iOS simulators and Android emulators, then checks each screenshot's language.
```

- **PR body:** `Adds Shotfleet, a closed-source, paid macOS CLI (free tier) that drives Maestro flows to capture localized store screenshots on iOS and Android. I'm the author.`

## L4. awesome-maestro, article entry

- **Route:** separate PR, same README, section "Articles" (end of section).
- **PR title:** `Add article: one Maestro flow in every language`
- **When:** after `/guides/maestro-one-flow-every-language` is live (it 404s today).
- **Entry:**

```
- [Run one Maestro flow in every language](https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=awesome-maestro&utm_medium=awesome-list) - iOS launch arguments, Android per-app locales, and four traps that give you English by mistake.
```

- **PR body:** `Adds a guide on running one Maestro flow in several languages (Maestro 2.0.10, iOS and Android). I wrote it; it mentions my paid tool once, near the end.`

## L5. awesome-testing-tools (ZoranPandovski/awesome-testing-tools)

- **Route:** PR to `readme.md`, Mobile Testing Tools, between Sherlo and tapflow (the file is `readme.md`, lower case). Their rules: search for duplicates, one PR per suggestion, matching section, a useful title.
- **Fit:** weak. It's a screenshot tool, not a test framework. Send only after L3 is merged, or skip.
- **PR title:** `Add Shotfleet to Mobile Testing Tools`
- **Entry:**

```
- [Shotfleet](https://shotfleet.com/?utm_source=awesome-testing-tools&utm_medium=awesome-list) - macOS CLI that runs one Maestro flow in every language on iOS simulators and Android emulators and checks each screenshot's language.
```

## L6. awesome-mcp-servers (punkpeye)

- **Hold.** It needs a public GitHub repo and a Glama listing; shotfleet is closed source with no public repo. MCP server install for the record: `claude mcp add shotfleet -- shotfleet mcp`.

---

## Sources (read 2026-10-06 and 2026-10-07)

androidweekly.net home (submit block), softwaretestingweekly.com footer and the Tally form, suggest.iosdevweekly.com, swiftlee-weekly.com/for-writers, fatbobman.com About, reactnativenewsletter.com/submit, kotlinweekly.net, lastweekinflutter.substack.com, the READMEs and contributing files of awesome-mac, Awesome-ASO, awesome-maestro and awesome-testing-tools (via the GitHub API), the two guides on origin/main (`site/public/guides/`), `site/draft/guides/`, `marketing/articles/` on main (01 and 02 are the two guides, merged but not live; 03, 05, 06 are drafts, unpublished), and the live site (VERSION 0.1.5, no feed).
