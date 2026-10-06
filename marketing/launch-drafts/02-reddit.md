# Reddit

Three subs, three different texts. Don't cross-post the same text.

**How the rules were read:** Reddit blocks my tools, so I couldn't open the sidebars. What's below comes from search summaries on 2026-10-06 and the older notes in `research/marketing-research.md`. Open each sidebar and the pinned posts yourself before posting, and screenshot the rule you rely on.

The 10% rule: Reddit's old self-promotion guideline is that about 1 in 10 of your posts and comments should be about your own thing. Before these posts, it helps if your account has some normal, helpful comments in these subs (answers about Maestro, fastlane, localization, screenshots). If the account is mostly empty, spend a week answering questions first.

---

## 1. r/iOSProgramming: App Saturday post

**Rules (second-hand, check the sidebar):**
- Promoting your own app or tool is only allowed in **App Saturday** posts, on Saturday in your own time zone.
- One app, **once per year**. So this post is the one shot for shotfleet; pick the day well (after 0.1.5 is live, and ideally after 0.1.6 so the XCUITest part can be said as available).
- The mods proposed a minimum of about 20 sub karma in the last 6 months, and a template with the tech stack and the development challenges. The draft below includes both anyway.
- Use the App Saturday flair if there is one.

**Best time:** Saturday morning US Eastern (afternoon in the Netherlands), so it's Saturday for most readers.

**Title:** `App Saturday: a free check that your localized App Store screenshots really show the right language`

**Body:**

> I made this. It's a Mac command-line tool called shotfleet, and the part I think most of you can use is free.
>
> **The problem.** I have an app in 18 languages. Store screenshots in every language are a pain, and the failure I kept hitting was quiet: a screenshot that looks fine, but the app in it is in the wrong language. On the old Google Play screenshots of another of my apps, check found 103 problems where the captions were translated but the app under them was still English. Nobody tells you; the listing just looks a bit wrong to a Japanese user.
>
> **The free part.** `shotfleet check` reads every screenshot in a folder and compares the text with your app's own strings. It flags the wrong language, blank screens and sizes the App Store doesn't accept (and a missing 13-inch iPad set). It works on fastlane snapshot output, no Maestro and no account needed:
>
> ```
> brew install noloman/tap/shotfleet
> shotfleet check fastlane/ --app MyApp.app
> ```
>
> On a real fastlane snapshot set it found a German listing whose app was still in English.
>
> **The paid part.** `shotfleet run` takes one Maestro flow written in English and runs it in every language your app has, on several simulators at once. It rewrites the text taps from your app's translations ("Next" becomes "Weiter", "次へ"). On my M1 Pro, 18 languages x 4 screens took 9 minutes on iOS. Running your own XCUITest screenshot tests instead of a Maestro flow is coming in 0.1.6, not out yet.
>
> **Tech stack.** Python, shipped as one signed binary for Apple silicon. Maestro drives the app. For reading text it uses the app's accessibility tree on iOS during a run, and macOS's built-in text recognition (Vision) for screenshots made by other tools. `simctl` for the simulators, launch arguments for the language.
>
> **Development challenges.**
> - Translated words clash. In Turkish, "Next" and "Advanced" are both "İleri", so a tap could hit the wrong button. It warns before the run now.
> - macOS text recognition sometimes takes minutes to wake up on a busy Mac. check now waits, then marks screens it couldn't read as "not verified" instead of guessing.
> - Simulators that stop answering on a loaded Mac. One now costs 60 seconds instead of 300, and the next run replaces it with a fresh one. Only shotfleet's own simulators are ever deleted.
>
> **Limits.** Apple silicon only, needs Maestro and Java 17+ for `run`. No frames, captions or upload (fastlane does that). If your app has one or two languages you probably don't need it.
>
> Price: check is free, run is free for 2 languages. Every language is $29 for the first 100 buyers, then $49, one-time.
>
> https://shotfleet.com/?utm_source=reddit-iosprogramming
>
> How do you check your localized screenshots today? Happy to answer anything.

**Before posting:** gates 1 and 2 in README.md. The tech stack lines (Python packaged with PyInstaller, Vision) come from DISTRIBUTION.md and the code, not from the site; they're true, but cut them if you'd rather not say. The "103 problems" sentence depends on gate 2; without it, say "on the old store screenshots of another of my apps, check flagged 108 of 120: translated captions over an app still in English" (claim C107).

---

## 2. r/androiddev: monthly showcase thread comment (not a post)

**Rules (second-hand, check the sidebar):**
- The sub doesn't allow app promotion or self-promotion in normal posts ("No App Promotion or Recruiting Testers" per a rules directory, verified there 2026-06-01).
- There's a monthly showcase thread (titles like "October 2026 Showcase" / "Interesting Android Apps") where self-promotion is allowed. It's meant for Android projects; a Mac tool for Android developers is a grey area, so keep it short and useful.
- Don't make a standalone post about shotfleet. If you want one, message the mods first (draft below) and only post if they say yes.

**Best time:** early in the month, when the new showcase thread is fresh; any weekday morning US Eastern.

**Comment in the showcase thread:**

> I made a Mac tool for Google Play (and App Store) screenshots in every language: shotfleet.
>
> The story that started it: my Android onboarding had a Next button that was out of reach in Japanese, Korean, Chinese and Arabic on a small phone. The text was taller, the page didn't scroll, and the button ended up below the screen. English fit, so I never saw it. I only found it because my screenshot run got stuck on that page. The fix was making two pages scroll.
>
> What it does: one Maestro flow written in English, run in every language your app has, on several emulators at once. It sets the per-app language (Android 13+ emulators) and rewrites the text taps from the strings in your APK. On my M1 Pro, 18 languages x 4 screens took 15 minutes on Android. Then it checks every screenshot for the wrong language, blank screens and Play size rules, and exports to fastlane's folders.
>
> Free: `shotfleet check` on screenshots you already have, including screengrab output (it ignores screengrab's timestamped file names). Runs on Apple silicon Macs only. Paid for more than 2 languages in a run: $29 for the first 100 buyers, then $49 once.
>
> https://shotfleet.com/?utm_source=reddit-androiddev
>
> Feedback welcome, especially from people who already use screengrab.

**Message to the mods (only if you want a standalone post):**

> Hi, I made a paid Mac command-line tool for localized Google Play and App Store screenshots (with a free check command). I'd like to post a technical write-up about an onboarding bug it showed me (a Next button below the screen in 4 languages on small phones, fixed with a scroll) and how I test per-app locales on emulators. The tool would be mentioned once at the end. Is that OK here, or should it stay in the showcase thread? Thanks, Manu

---

## 3. r/FlutterDev: probably skip

**Rules (second-hand):** apps can only be posted if they're open source, or if the post is an insightful dive into how it was built; "No advertising of apps" is a rule. shotfleet is closed source and paid, so a promo post would likely be removed.

**Is a Flutter post honest at all?** Partly. Flutter works from translation files (ARB), and I've run exactly one real Flutter app end to end: wger, on iOS and Android, in German and Japanese, on 2026-10-03. German showed on every screenshot. wger's Japanese is about 30% translated, so those screens showed English, and check said so. That's one app, not a track record.

**Recommendation:** don't post a launch here. If you want to be in this sub, answer questions about localized screenshots or golden tests when they come up, and mention check only when it answers the question. If later you have a real dive worth posting (for example how Flutter keeps its strings out of the build, and what that means for screenshot tools), write that as the post and mention the tool once at the end.

**A reply you can use in a thread, when someone asks about localized screenshots in Flutter:**

> I made a Mac tool for this (shotfleet), so take it with that in mind. For Flutter it reads your ARB files, because the built app doesn't keep the strings in a readable form. I've only run one real Flutter app through it so far (wger, iOS and Android, German and Japanese). The free part, `shotfleet check`, compares each screenshot's text with your translations, which is how it showed that wger's Japanese screens were still mostly English (its Japanese is about 30% translated). https://shotfleet.com/?utm_source=reddit-flutterdev
