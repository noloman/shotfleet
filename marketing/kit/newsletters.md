# Newsletter submissions (article links only)

Owner: Manu submits. Nothing here has been submitted. Written 2026-10-02.
Rule: submit an article, never the landing page, one link per newsletter, once. None of them guarantees inclusion; accept silence. Do not follow up before four weeks. Do not ask anyone to share it.
Ready when: the real domain is live; the article is published and indexed; the page is clean (no popup, no cookie banner: the site has none); the blog has an RSS feed (needed for the iOS Dev Directory, see below; the site had no feed at research time, so add `/feed.xml` first); and the article's TO VERIFY list is ticked. Do not submit before launch week unless an article is final: MARKETING.md puts newsletters in days 2 to 7 of launch week.

Routes were read on 2026-10-02 from each site (V) except where marked.

| Newsletter | Reach as stated | Article to send | Route | Rule that matters |
|---|---|---|---|---|
| iOS Dev Weekly | not disclosed | Article 1 (fastlane snapshot stuck in English) | Form: https://suggest.iosdevweekly.com (fields: name, email, link, who published it, blog post yes/no, Swift library yes/no, reason for inclusion) | Do not submit links from blogs already in the iOS Dev Directory: the curator reads them by RSS. Add the blog to the directory instead. Reason: "a few words" |
| SwiftLee Weekly | 21,681 email subscribers (V, their about page) | Same submission as iOS Dev Weekly (see below) | Its writers' page (https://swiftlee-weekly.com/for-writers/) sends suggestions to the iOS Dev Weekly form above, and says to register the site in the iOS Dev Directory | Wants a clear title, one focused outcome, practical details from real work, screenshots or evidence, a view beyond the official docs, a clean page |
| Android Weekly | "more than 80,000" (V) | Article 2 (one Maestro flow in every language) | "Submit" section on https://androidweekly.net (anchor `#submit-stuff`; the exact form was not read, so open it and follow it) | "Links in each issue will be chosen by us." No published rule on tools or self-promotion |
| Kotlin Weekly | 22,907 (V) | Article 3 (the button nobody could reach; includes a Compose snippet) | Email mailinglist@kotlinweekly.net, subject: `Link for submission - Kotlin Weekly` | One link per mail; sponsorship uses the same address, do not mention it |
| KMP Weekly | not shown | Article 5 (Google Play screenshots in every language) when it exists; before that, article 3 only if Kotlin Weekly has not run it after 3 weeks | https://kmpweekly.com/submit (form; its fields were not shown to the reader), or hello@kmpweekly.com | Kotlin Multiplatform angle: Compose Multiplatform resources are read on both platforms (README) |

Do not send the same article to Kotlin Weekly and Android Weekly in the same fortnight; their readers overlap.

---

## iOS Dev Weekly and SwiftLee Weekly (one submission serves both)

First, in order:

1. Add the blog to the iOS Dev Directory so the curators find new posts by RSS: https://iosdevdirectory.com ("Add a Site", /contributing). Requirements read there: an RSS feed, and content about Apple platforms or Swift. Our site's article 1 is about fastlane and iOS screenshots, so it qualifies; the product page does not need to.
2. Wait for the directory to list the site. The iOS Dev Weekly form says links from directory blogs are already read, so do not also submit the same link by form to "make sure". Use the form only if the directory declines the site, or for a link that is not on your own blog.

Form text, if you do use it (https://suggest.iosdevweekly.com):

- Name / email: Manu Lorenzo.
- Link: `https://DOMAIN/fastlane-snapshot-screenshots-all-english`
- Link publisher: self-authored.
- Blog post: yes. Swift library: no.
- Reason for inclusion (short and specific):

> Practical diagnosis of why fastlane snapshot screenshots come out in English in every language folder, from the docs and old issue threads, plus a free way to check each image against the app's own strings. Disclosure: I make the tool the last section mentions, which is optional.

SwiftLee note: the writers' guide asks for one focused outcome, real development detail, and evidence. Article 1 has: one outcome (find out why your screenshots are in English), the real fastlane docs and issue links, and a measured check on my own folders (252 images, about 25 seconds, one real problem found). If a screenshot of the report grid is added to article 1 before submission it matches the "screenshots or evidence" criterion.

---

## Android Weekly (article 2)

Open https://androidweekly.net and use the Submit section. Suggested text if it has a free field:

> Title: Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps
> Link: `https://DOMAIN/maestro-one-flow-every-language`
> Note: A tutorial for running one Maestro flow in several languages on Android (per-app locales, Android 13+, set with `adb`) and iOS, with four traps that make every run silently English (a default in the flow header that beats the command line, clearState resetting the app language on Android, and others). Author's note: I make a paid tool in this area; it is mentioned once at the end and the article stands without it.

## Kotlin Weekly (article 3)

To: mailinglist@kotlinweekly.net
Subject: Link for submission - Kotlin Weekly

> Hi,
>
> A short story with a real Compose fix: in Japanese, Korean, Chinese and Arabic the Next button of my Android onboarding sat below the bottom of a small phone, because the page did not scroll and the translated text runs taller. The fix is a `verticalScroll(rememberScrollState())` on two columns. The article shows the diff, the image of the broken screen, and how to test for it in your own app.
>
> https://DOMAIN/the-button-nobody-could-reach
>
> I wrote it. I also make a paid command line tool that found the problem while running my app in every language; the article says plainly that the tool did not detect the button itself, and mentions it only at the end.
>
> Thanks,
> Manu

Check before sending: the article's TO VERIFY items 2, 4, 5 and 6 (which languages, whether the repo owner is fine with the snippet, what Skip does, whether users were affected).

## KMP Weekly (article 5 later, or article 3 as a fallback)

Use the form at https://kmpweekly.com/submit, or write to hello@kmpweekly.com:

> Hi, an article for the Kotlin Multiplatform audience: how to produce Google Play (and App Store) screenshots in every language an app ships, using emulators and fastlane, including Compose Multiplatform apps whose strings are in Compose resources. Link: `https://DOMAIN/google-play-screenshots-every-language-emulators`. I wrote it; I also make the tool the last section mentions, optionally. Thanks, Manu.

Do not send this until article 5 exists and its steps have been run (see articles/04-ideas.md). If you need to send something sooner, send article 3 with the Kotlin Weekly text above, adjusted to say the app code is Compose, and only after three weeks without it appearing in Kotlin Weekly. Do not claim that the tool has been run on a Kotlin Multiplatform app unless you have the run: the repo's real-app notes include a Compose Multiplatform app (Kuokka) with iOS and Android runs, but state only what you re-check.

---

## After sending

Log date, newsletter, article, and the `utm_source` visits afterwards. Add `?utm_source=androidweekly` and the like to the link only if the form lets you choose the URL; do not alter a canonical URL on the article itself. If a newsletter links the article, thank the editor by replying to the issue email, not by posting.
