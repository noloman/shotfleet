# Show HN

**Where:** https://news.ycombinator.com/submit, from your own account.
**Link to submit:** `https://shotfleet.com/?utm_source=hn` (the home page, not an article; Show HN excludes blog posts and landing pages, and the home page has a free thing to try).

## Rules to respect (read 2026-10-06 at https://news.ycombinator.com/showhn.html)

- Title starts with "Show HN:". No superlatives, no clickbait, keep it under 80 characters.
- It has to be something people can try. `shotfleet check` is free with no account, so that's the "try it" part. Say so in the first comment.
- Don't ask anyone to upvote or comment, and don't post the link elsewhere "to help". HN detects voting rings.
- Be there to answer. Plan the first 3 hours for replies, then check every hour.
- Don't edit the title after posting unless a moderator asks.

## Best time

Plan: Tue 20 or Wed 21 Oct, the week of the 19th (not 13 or 14 Oct, that's Keysi's launch). About 8 to 10 in the morning US Eastern (14:00 to 16:00 in the Netherlands). That advice comes from blogs, not from HN; the real rule is: post on a day you can answer for hours. Not on a Friday evening.

## Title

Recommended (77 characters):

`Show HN: shotfleet, localized store screenshots from one English Maestro flow`

Other options:

- `Show HN: Localized App Store and Play screenshots from one English Maestro flow` (79; no product name, says both stores)
- `Show HN: I ran my app in 18 languages and found a button nobody could reach` (75; a story title, which HN may read as a blog post, so riskier on Show HN)

## First comment (post it yourself, right after submitting)

> Hi HN, I'm Manu, a solo developer in the Netherlands. I made shotfleet.
>
> I have a workout app in 18 languages. I wrote a Maestro flow to make the store screenshots, and it only worked in English, because Maestro finds buttons by the text on them. So my "localized" screenshots were the English ones, more or less. I didn't want 18 copies of the flow, so I wrote a tool.
>
> What it does: you write one Maestro flow in English. shotfleet reads the translations compiled into your .app or APK and rewrites every text selector for each language ("Next" becomes "次へ" in Japanese). It boots simulators and emulators, sets the language on each one, runs the flow, and then reads every screenshot back and compares the text with your app's own strings. A screen in the wrong language, a blank screen or a size the stores don't accept gets flagged. When it's all fine, one command puts the screenshots into fastlane's folders.
>
> On my M1 Pro, one run of 18 languages x 4 screens took 9 minutes on iOS and 15 on Android. That's my app on my Mac, so yours will be different.
>
> The thing that made me keep going: on the first full Android run, Japanese, Korean, Chinese and Arabic all got stuck on the same onboarding page. The text was taller, the page didn't scroll, and Next was below the bottom of a small phone. English fit, so I had never noticed. The tool didn't "detect" that, to be fair: the run got stuck and I looked at why. The fix was making two pages scroll.
>
> The free part, if you just want to try something: `shotfleet check` works on screenshots you already have, including fastlane snapshot, screengrab and supply folders, no Maestro, no account. On a real fastlane snapshot set it found a German listing whose app was still in English. On the old Play screenshots of another app of mine, AnywhereRoles, it found 127 problems. 103 were translated captions over an app that was still in English. My own mistake: I had made one English capture and only translated the captions. 15 were false "missing" lines from a bug of mine in how it read supply's file names, fixed in 0.1.6. I recaptured that app with shotfleet 0.1.4 (120 Android and 108 iPhone screenshots) and check found 0 problems. Getting the Android flow to run took me several failed runs first. The real screenshots are on the home page.
>
> What it doesn't do:
> - Apple silicon Macs only (macOS 13+). No Intel, Linux or Windows.
> - Capturing needs Maestro and Java 17+, except on iOS, where it can also run your existing XCUITest screenshot tests instead of a Maestro flow (new in 0.1.6). I haven't run that end to end yet: my first try, on an overloaded Mac, lost its simulators. That path is paid like `run`, 2 languages free.
> - It's built on Maestro. Android capture always goes through a Maestro flow.
> - No frames, captions or store upload. fastlane, ButterKit or AppScreens do that.
> - Flutter and React Native work from your translation files. I've run one real Flutter app (wger) and one Expo app end to end, not more.
> - It's closed source. Your app and screenshots never leave your Mac. It talks to Gumroad for the licence, and `doctor` asks shotfleet.com for the latest version number (`doctor --fix` also downloads Maestro, Java and the Android tools from GitHub, Adoptium and Google).
> - If your app has one or two languages, you probably don't need it.
>
> Price: check is free, and run is free for 2 languages. A licence for every language and the fastlane export is $29 for the first 100 buyers, then $49, one-time. It covers a year of updates (a calendar year from your purchase; the versions you have keep working), up to 3 of your Macs with spare activations for reinstalls, and a 14-day refund. Open-source maintainers and students can email me for a free licence.
>
> Install: `brew install noloman/tap/shotfleet` or `curl -fsSL https://shotfleet.com/install.sh | sh` (short script, read it first if you like). Short clips of each command are at https://shotfleet.com/demo?utm_source=hn
>
> Two write-ups that don't need the tool: why fastlane snapshot gives you English in every folder (https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english?utm_source=hn-guide), and how to run one Maestro flow in every language (https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=hn-guide).
>
> I'd like to hear how you do localized screenshots today, and what would stop you from trying this.

## Before posting

- Gate 1 (0.1.6 live, guides and AnywhereRoles loading) and gates 2 and 3 from README.md. If the guides or the AnywhereRoles section don't load, cut the guide sentence and the "real screenshots are on the home page" line.
- Check `maestro --version` still matches what you'd say if asked (the 9/15 minutes were on Maestro 2.0.10).
- Read the 15 prepared answers in `marketing/kit/show-hn.md` and the short ones in `10-faq-objections.md`. Kit answer 8 (Flutter) is out of date: a real Flutter app has run since. Kit answer 2 (notarization): the docs and claims C181 now say the Homebrew build is signed and notarized. Any kit answer about privacy or Maestro predates 0.1.6: use the lines above and `10-faq-objections.md`.

Disclosure line (already in the comment): "I made shotfleet."
