# shotfleet promo drafts (approved by Manu 2026-10-07)

Drafts only. Nothing here was posted, sent, signed up for or paid. Written 2026-10-07 from MORE-PLACES.md, the two live guides (both return 200; text matches the markdown sources on origin/main except small edits already applied here), the home page (0.1.6) and manulorenzo.me.

Facts used (all from the site or research records): 0.1.6; own XCUITest capture on iOS, new in 0.1.6 and device-tested on iOS 26.4; macOS on Apple silicon; closed source; `check`, `doctor`, `init` free, `run` free for 2 languages; licence $29 for the first 100 buyers, then $49 once, 3 Macs, a year of updates, 14-day refund. Showcases: AnywhereRoles and Kuokka (plus Manu's WOD Tracker run). No other number is used.

| # | Place | Route | Date | Needs from Manu |
|---|---|---|---|---|
| 1a | DEV.to, Maestro guide | Paste into the editor (or New post, Markdown); `canonical_url` in front matter | Thu 15 to Sat 17 Oct | DEV account; pick cover image; press publish; reply to comments |
| 1b | DEV.to, fastlane guide | Same | Thu 15 to Sat 17 Oct, one day after 1a | Same |
| 1c | Hashnode, Maestro guide | New article, paste Markdown, "Are you republishing?" and set the original URL | Thu 15 to Sat 17 Oct | Hashnode account and blog; cover; tags picked from Hashnode's list; publish |
| 1d | Hashnode, fastlane guide | Same | Thu 15 to Sat 17 Oct | Same |
| 2a | Medium: ProAndroidDev (Maestro) | Import the guide at medium.com/p/import (keeps canonical), email editors@proandroiddev.com | Thu 15 to Sun 18 Oct | Medium account; send the pitch; check the canonical line after import |
| 2b | Medium: The Swift Cooperative, or AppCoda (fastlane) | Import, then the publication's own submit route (Cooperative route not checked; AppCoda: appcoda.com/write-for-us) | Thu 15 to Sun 18 Oct | Same; decide which of the two |
| 2c | Medium: Code Well (Codemagic), fallback for either | Codemagic's page "write for Code Well" adds you as editor on request | Only if 2a or 2b says no | Same |
| 3 | Kotlin Slack `#feed` | Post in channel | Fri 16 Oct, after the Android/Kotlin Weekly sends | Slack account; post it |
| 4a | ASO Stack Slack `#promotion` (or `#tools`) | Post in channel | Thu 22 Oct (not on the Show HN day, 20 or 21 Oct, if that moves, post the day after) | Join first (form on Phiture's page); post it |
| 4b | Phiture Mobile Growth Stack Slack `#promotion` | Post in channel | Thu 22 Oct, after 4a | Join route not on the page: look for it by hand |
| 5 | Jeroen Leenarts (AppForce1, Do iOS, CocoaHeadsNL) | Mastodon DM `@appforce1@hachyderm.io`, LinkedIn message, or Meetup "Message" to the CocoaHeadsNL organizers; no personal email found | Around Mon 26 Oct | Fill the bracketed bits (city, Do iOS plans); pick the route; send |
| 6 | Appdevcon 2027 CFP | Sessionize, https://sessionize.com/dawn-conferences-2027/ | Submit in Nov; closes Fri 18 Dec 2026 | Sessionize account; confirm he can travel in March; check the numbers one last time |

Order rules: publish on shotfleet.com first (done, 6 Oct), wait for the guides to index (a few days), then republish with the canonical set. Nothing from this list on Show HN day (Tue 20 or Wed 21 Oct). Medium: one publication per story, so one of 2a/2b/2c per guide, not all three.

---

## 1. DEV.to and Hashnode

Both bodies below are the live guide text, with: the one-line "Originally published" note on top, the guide's own ending as the only promo, and a disclosure line at the bottom. No relative links were left in the sources (checked: every link is already `https://shotfleet.com/...`, `https://docs...` or `https://github.com/...`). Headings and code fences are kept. Two small edits to match the live page: the fastlane "Step 1/Step 2" headings are "Then: ..." and the price line says "with a year of updates and a 14-day refund".

Cover images: I did not make any. Suggestions below use files Manu already has or the site has; DEV crops to 1000 x 420, so keep the middle of the picture clear.

Platform notes:
- DEV.to: max 4 tags, lowercase, no spaces. `published: false` keeps it a draft until Manu flips it. Disclosure also fits their norm of not posting only promo: both posts are real tutorials.
- Hashnode: as far as I know the web editor does not read front matter. Paste the body, then fill title, subtitle, tags (pick from the list), cover, and under "Are you republishing?" paste the original URL. The front matter below is the same data in one place (and works if Manu ever uses the GitHub backup).

### 1a. DEV.to: Maestro guide

````markdown
---
title: "Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps"
published: false
description: "Maestro can't set the locale inside a flow. How to run one flow in every language on iOS and Android, and the four traps that give you English by mistake."
tags: testing, android, ios, mobile
canonical_url: https://shotfleet.com/guides/maestro-one-flow-every-language
# cover_image: add a hosted URL. Suggestion: the same onboarding screen in de, ja and ar side by side, from the WOD Tracker run on shotfleet.com (Manu exports it). Fallback: https://shotfleet.com/og.jpg
---

*Originally published on [shotfleet.com](https://shotfleet.com/guides/maestro-one-flow-every-language).*

You wrote a Maestro flow for your app and now want the same screens in German, Japanese and Arabic, for screenshots or for a smoke test. The docs are short on this, and the failure mode is quiet: every run goes green and the images are in English.

I build a tool around this problem (shotfleet, which comes up in the last three sections). Everything before that is plain Maestro and `adb`.

## What the docs say

Maestro's locale page says there is "no place within a Flow itself" (a `launchApp` or `config.yaml`) to define the locale. The documented route is the `--device-locale` flag on `maestro start-device` (and `maestro cloud`), not on `maestro test`, combined with tags:

```bash
maestro start-device --platform android --device-locale fr_FR
maestro test --include-tags french .maestro/
```

That works, and it changes the whole device. For N languages you start N devices in turn, or restart one. It also means the language lives in your shell script and tags, not in the flow.

## A per-app alternative: no device change

You can also set the language for your app only, and keep the device as it is.

### iOS: launch arguments

`launchApp` takes an `arguments` map of key-value pairs that are passed to the app as launch arguments. iOS reads `AppleLanguages` and `AppleLocale` from them, so one flow can take the language as a variable:

```yaml
# flow.yaml  (no env: default in the header, see trap 1)
appId: com.example.myapp
---
- launchApp:
    clearState: true
    arguments:
      AppleLanguages: "(${APP_LANG})"
      AppleLocale: "${APP_LOCALE}"
- tapOn:
    id: onboarding_next
- takeScreenshot: shots/${APP_LANG}/02_onboarding
```

I ran this on Maestro 2.0.10 against an iOS 26.4 simulator. The `tapOn` before the screenshot matters: when I put a `takeScreenshot` straight after `launchApp`, the image showed the iOS home screen, not the app, in 4 of 4 runs (with and without `clearState`; the Mac was under heavy load at the time). Putting `extendedWaitUntil` with `visible: id: next` first gave the app. Wait for something on screen before the first screenshot.

Everything here was run on Maestro 2.0.10 only. Newer versions can differ: where `takeScreenshot` writes is one thing to check on yours.

Run it once per language, with the variables after `test`:

```bash
for pair in en:en_US de:de_DE ja:ja_JP; do
  maestro --device "$UDID" test \
    -e APP_LANG="${pair%%:*}" -e APP_LOCALE="${pair##*:}" flow.yaml
done
```

### Android: per-app locales (Android 13, API 33 and up)

Android 13 added per-app language preferences. From the outside you set one with a shell command, before the flow starts:

```bash
adb -s emulator-5554 shell pm clear com.example.myapp
adb -s emulator-5554 shell cmd locale set-app-locales com.example.myapp --locales de
```

Then run the same flow without `clearState`, because of trap 3. To keep one file for both platforms, put the iOS `launchApp` in a `runFlow` with `when: platform: iOS` and the Android one in `when: platform: Android`.

### The selectors

A flow that says `tapOn: "Next"` fails in German. Two ways out: tap by `id:` (accessibility identifier on iOS, resource id on Android), which does not change with the language, or write the translated text per language. If your app has ids on everything you tap, you are done and need nothing else in this article.

## Four traps that give you English by mistake

**1. A default in the flow header beats the command line.** One developer documented this with Maestro 2.10, and I reproduced it on 2.0.10 on iOS: the flow had `env: { LOCALE: en }` as a default, and every "Portuguese" and "Spanish" run still came out in English. He fixed it by removing the default from the header, and he caught it only by looking at the images ([PR #216](https://github.com/RogerioDoCarmo/morse_app/pull/216)). Maestro's parameters page says that constants defined in a subflow override same-name parameters from the parent. In my run the file even landed in the `en` folder although I passed `-e APP_LANG=de`. Do not put a default for the language in the header. Pass the language only with `-e`, and look at the first image of each run.

**2. `-e` goes after `test`.** In the same PR the iOS script put `-e` before `test`, and it failed while looking like it passed. On Maestro 2.0.10 I got `Unknown options: '-e', 'APP_LANG=de'`, the usage text and exit code 2, so it only looks like a pass if your script ignores the exit code. The order is `maestro --device X test -e KEY=VALUE flow.yaml`.

**3. On Android, clearing state clears the language.** `clearState` wipes the app's data, and the per-app language goes with it. Clear first with `pm clear`, set the language, then launch without `clearState`. Otherwise you get the system language back.

**4. Parallel runs on Android.** Two separate `maestro test` processes on two devices on one Mac were unreliable for me on Maestro 2.0.10. With two emulators and two `maestro test` processes started together, one of the two failed in both attempts (a `TimeoutException`, or an exception on Maestro's own log folder), while each passed alone. A Maestro process listened on TCP 7001 while it ran, which is my guess for the shared resource; I did not prove it. Run one device at a time, or use one run that shards across devices (`--shard-split`, which I did not test), and check the images of both devices.

Two smaller ones. System permission dialogs are drawn by the OS in the device language, which stays English while your app is German (I measured this on iOS 26.4 with Maps launched in German; I did not test Android), so write those taps in English. `launchApp` also takes a `permissions` setting (see its docs page); I did not test it against a permission dialog. And long languages push buttons off the screen: use `scrollUntilVisible` before the tap, with `direction: DOWN` (it happened to me: [a Next button nobody could reach](https://shotfleet.com/#catch-h) in four languages).

## Read the images, not the exit code

All four traps pass. The only way to catch them is to look at the output, or to have something look for you: `shotfleet check shots/ --app path/to/MyApp.app` reads each image back and reports wrong-language and duplicate images. It is free (no licence, no account) and works on any folder of screenshots, fastlane's too ([how to check a fastlane snapshot folder](https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english)).

## Where shotfleet fits

Doing all of the above by hand for 18 languages on two platforms is a lot of scripting, and that is the work shotfleet does. It reads the translations compiled into your build and rewrites every text selector in your English flow for each language, so `tapOn: "Next"` becomes `Weiter` in German, or `(Nächste|Weiter)` if your app has two translations for it. It runs the languages in parallel on simulators and emulators and checks each image. On my own app, 18 languages by 4 screens (72 screenshots) took 9 minutes on iOS (four simulators in parallel) and 15 on Android, on one Mac. That is one app and Maestro 2.0.10, so treat it as a data point. `run` is free for 2 languages; a licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once, with a year of updates and a 14-day refund.

## When not to use shotfleet

If your app has ids on everything you tap, three or four languages, and one platform, the loop above is enough. If you test on real devices or in a device cloud, shotfleet does not help; it runs simulators and emulators on your Mac. It needs an Apple silicon Mac, Maestro 2.x and Java 17+, and Android needs API 33+ emulators. It makes no frames or captions and does not upload to the stores. For Flutter and React Native it works from your translation files. I have run that end to end on one real Flutter app (wger) and one real Expo app (the obytes template), on iOS and Android, and not yet on any other.

---

*Disclosure: I made shotfleet and it is paid software. The `check` command and 2 languages per `run` are free; the full version is $29 for the first 100 buyers, then $49 once. Everything in the guide above works without it.*
````

### 1b. DEV.to: fastlane guide

````markdown
---
title: "Why your fastlane snapshot screenshots are all in English (and how to check every language)"
published: false
description: "Every language folder shows English? Five causes to rule out in fastlane snapshot, plus a free command that checks each image against your app's own strings."
tags: ios, fastlane, localization, testing
canonical_url: https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english
# cover_image: add a hosted URL. Suggestion: one screen in five languages from Manu's own store screenshots (Stressi or Cairn rows on the home page, "real store screenshots, not shotfleet output") with the wrong-language one marked. Fallback: https://shotfleet.com/og.jpg
---

*Originally published on [shotfleet.com](https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english).*

You set `languages(["en-US", "de-DE", "ja"])` in your Snapfile, ran `fastlane snapshot`, and opened the folders. German and Japanese are there, and every image is in English.

I build a tool in this area (shotfleet, which comes up at the end), so read this with that in mind. The first four causes below need nothing from me.

## How snapshot is supposed to set the language

fastlane's docs say the language reaches your UI tests "via a temporary file which is written by snapshot before running the tests". Your test target includes `SnapshotHelper.swift`, and the docs tell you to call `setupSnapshot(app)` before `app.launch()`. That helper reads the file and passes the language to your app as launch arguments. There is also an option, `localize_simulator`, that sets the Simulator's own system language.

So there are several places where the chain can break. The GitHub issues are old but show the pattern. In #8895 the Simulator language "stays en-US" after an Xcode update. In #12917 the reporter got English from `fastlane snapshot` while a manual Xcode run with the generated language file switched correctly. In #11457 the reporter found that `localize_simulator true` worked but changed the status bar because the simulator was erased. I did not reproduce any of these; they are the documented symptom, from 2017 and 2018. All three are closed.

## Five things to rule out, in order

**1. `setupSnapshot(app)` runs after `app.launch()`, or never.** The docs say to call it before launch, in `setUp()`. If your test launches the app first, the language never reaches it.

**2. You ran the test from Xcode.** The docs say running tests in Xcode does not produce snapshots; only the `fastlane snapshot` command creates the language file and the folders.

**3. The Simulator system language.** Try `localize_simulator(true)` in your Snapfile. Per issue #11457 the cost is a status bar that looks different, because the simulator gets erased.

**4. The app is not translated into that language.** If `de` is in your Snapfile but your build has no German strings, iOS shows your base language and no setting will help. List what your build really ships:

```bash
ls path/to/MyApp.app | grep lproj
```

Compare that list with your Snapfile. The app's base language may not be listed: with a String Catalog that has no explicit English entries, my test build had `de.lproj` and `ja.lproj` and no `en.lproj`. A language that is in the Snapfile but not in the app can only ever produce your base language. I checked this on a small test app: with `de.lproj` deleted from the build, launching with German arguments showed English, and Japanese on the same build still showed Japanese.

**5. The app remembers something.** If your app stores its own language choice or onboarding state, a reused install can show the old language. snapshot has `reinstall_app` and `erase_simulator` for this. On a small test app that saves its own language, launching with German arguments still gave English, and uninstalling and installing the app again gave German (I did that by hand, not with snapshot's option). This and the previous cause are not documented cases from the issue threads, so test them on your app.

## Then: look at every image

With 18 languages and 4 screens that is 72 images. Opening them by hand works until the day you skip one. A faster way is to compare each screenshot with the text your app really contains.

## Then: check the folder you already have

shotfleet's `check` command does that, and it is free: no licence, no account. It does not capture anything and does not touch your fastlane folders. It runs on a Mac and reads each image with the text recognition built into macOS. Give it a simulator build of your app, so it knows your real strings:

```bash
xcodebuild -scheme MyApp -sdk iphonesimulator -configuration Debug \
  -derivedDataPath build build

shotfleet check fastlane/ \
  --app build/Build/Products/Debug-iphonesimulator/MyApp.app
```

For an Android folder, pass the APK instead: `--app path/to/app-release.apk`.

It reads each image and tells you:

- **Wrong language:** the `de-DE` folder shows English strings.
- **Copies:** the same image in two languages.
- **Missing:** a language that did not produce every screenshot.
- **Store rules:** sizes, counts and transparency that App Store Connect or Play would reject.
- **A listing in a language the app does not have:** for example Traditional Chinese screenshots when the app has no Traditional Chinese.

The report (`check.json` and an `index.html` grid with a row per language and a column per screen, problems outlined in red) goes to `./shotfleet-check`.

On the committed fastlane screenshots of my own workout app (252 iOS images) it found one real problem: Traditional Chinese listings with Chinese captions over an app that was still in English. When I planted mistakes in a copy of a clean set (a German screen in English, a Korean screen in Japanese, two copied images), each one was reported. On 220 screenshots of another of my apps (20 languages) a check took 57 to 86 seconds once macOS text recognition was warm. The first check after a restart or a macOS update is slower, because macOS compiles its text-recognition model; that can take minutes, and once took about 40 minutes.

Pass `--app`. Without it `check` falls back to language detection, which cannot judge short screens.

## What this does not tell you

- If `check` says "macOS text recognition didn't answer in time" (or "isn't answering"), macOS is usually still compiling its text-reading model, which can take minutes on a busy Mac the first time (once about 40 minutes on a quiet one). `check` doesn't fail over it: it finishes and marks the screens it couldn't read as "not verified". Run it again later, or install Tesseract (`brew install tesseract tesseract-lang`) and `check` uses it automatically. No restart needed.
- It says the language is wrong. It does not say why. Go back to the five causes.
- macOS text recognition reads 33 languages on macOS 27 (older versions read fewer). For other scripts (Greek, Hebrew, most Indic scripts) `check` still catches other-language screens, copies and missing screens, and says which screens it could not read. With Tesseract installed, `check` uses it for those scripts by itself: in my test, 84 of 85 languages could then be read, against 66 without it.
- Copies are only reported on screens with enough text. Two near-empty screens that are identical can pass.
- It is only as good as your simulator build matching the build that made the screenshots.

## When not to use shotfleet

If your screenshots are already right in every language, you do not need it. If you have only two or three languages, looking at the images yourself is fine. If you already have a maintained UI-test suite and snapshot works for you, keep snapshot; it is free and `check` can sit next to it. If you would rather capture with Maestro, [one Maestro flow in every language](https://shotfleet.com/guides/maestro-one-flow-every-language) shows how, without shotfleet. The tool only runs on an Apple silicon Mac (the installer refuses Intel), and capturing with `shotfleet run` is a separate step with its own requirements (Xcode, the Android SDK for Android, Maestro 2.x, Java 17+, and a Maestro flow you write). It does not make frames or captions and does not upload to the stores. I also have no data yet on how often modern fastlane versions hit the problem in this article; the issue threads are old.

## Where to go from here

If `check` finds wrong-language images and you would rather not maintain per-language UI tests at all, shotfleet also captures: one English Maestro flow, every language your app ships, on iOS and Android. `run` needs Maestro, Java and a flow; on iOS, your own XCUITest or `SnapshotHelper` tests work instead (new in 0.1.6). `run` is free for up to 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once, with a year of updates and a 14-day refund. Details at [shotfleet.com/#price](https://shotfleet.com/#price).

The free part is the `check` command above. Install it, point it at your `fastlane/` folder and read the grid.

---

*Disclosure: I made shotfleet and it is paid software. The `check` command and 2 languages per `run` are free; the full version is $29 for the first 100 buyers, then $49 once. The first four causes above need nothing from me.*
````

### 1c. Hashnode: Maestro guide

````markdown
---
title: "Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps"
subtitle: "Maestro can't set the locale inside a flow. Here is how to run one flow in every language on iOS and Android, and the four traps that give you English by mistake."
slug: maestro-one-flow-every-language
tags: Maestro, Android, iOS, Testing, Localization
cover: (hosted URL; same suggestion as DEV, 1600 x 840 works well here)
# Original article URL, set in the editor under "Are you republishing?":
canonical: https://shotfleet.com/guides/maestro-one-flow-every-language
---

*Originally published on [shotfleet.com](https://shotfleet.com/guides/maestro-one-flow-every-language).*

(Body: identical to 1a, from the line starting "You wrote a Maestro flow" to the end of the "When not to use shotfleet" section, then the same disclosure line.)
````

Hashnode: the body is the same text as in 1a, so paste it from there. Tags to pick from Hashnode's list: Maestro (if it does not exist, use Mobile Testing), Android, iOS, Testing, Localization.

### 1d. Hashnode: fastlane guide

````markdown
---
title: "Why your fastlane snapshot screenshots are all in English (and how to check every language)"
subtitle: "Five causes to rule out in fastlane snapshot, plus a free command that checks each image against your app's own strings."
slug: fastlane-snapshot-screenshots-all-english
tags: iOS, fastlane, Localization, Xcode, Testing
cover: (hosted URL; same suggestion as DEV)
canonical: https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english
---

*Originally published on [shotfleet.com](https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english).*

(Body: identical to 1b, from the line starting "You set languages" to the end of "Where to go from here", then the same disclosure line.)
````

Hashnode body: paste it from 1b.

---

## 2. Medium

How to publish on Medium without losing the canonical: use the import tool (https://medium.com/p/import), paste the guide URL. Medium sets the canonical link to the original by itself. After import, open the draft, then More settings, Advanced settings, and check that "This story was originally published elsewhere" shows the shotfleet.com URL. Import copies text and code; check the YAML code blocks and the two lists afterwards. Medium has no front matter, so no disclosure line is added automatically: add the same disclosure line from section 1 at the bottom. A story can be in only one publication, so choose one per guide.

Sources (all from MORE-PLACES.md, not re-checked today): ProAndroidDev takes outside posts by email at editors@proandroiddev.com (its guidelines page returned 403 to me, so the route is from a search summary); AppCoda wants practical tutorials with a demo project (https://www.appcoda.com/write-for-us/); The Swift Cooperative took over after Better Programming closed (submit route not checked); Code Well adds you as editor on request (https://blog.codemagic.io/write-for-medium-publication-code-well).

| Guide | First choice | Why | Fallback |
|---|---|---|---|
| Maestro, one flow in every language | ProAndroidDev | Android and Kotlin audience, problem-solution posts, half the guide is `adb` and per-app locales | Code Well (Codemagic): a CI vendor's publication, test automation fits; I did not check what it has accepted lately |
| fastlane snapshot all in English | The Swift Cooperative | iOS and fastlane audience, troubleshooting post | AppCoda (but it prefers tutorials with a demo project, and this guide has none, so a weaker fit); then Code Well |

### 2a. ProAndroidDev: pitch email (Maestro guide)

To: editors@proandroiddev.com
Subject: Submission: one Maestro flow in every language on Android and iOS

> Hi,
>
> I'd like to submit a post for ProAndroidDev: "Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps".
>
> It shows how to run the same Maestro flow in German, Japanese and Arabic. Maestro's own docs say there is no place in a flow to set the locale, so the post uses Android 13 per-app locales (`adb shell cmd locale set-app-locales`) and iOS launch arguments, and then lists four traps that give you English by mistake while every run stays green. For example, on Android `clearState` also clears the app language, and a language default in the flow header beats `-e`. I ran everything on Maestro 2.0.10 with an API 36 emulator and an iOS 26.4 simulator, and the post says where I did not test something.
>
> It is already live on my site: https://shotfleet.com/guides/maestro-one-flow-every-language. I'd import it with Medium's import tool so the canonical link points there.
>
> Disclosure: I make shotfleet, a paid Mac tool that does this for you. It comes up in the last three sections, which say when you should not use it. The first part is plain Maestro and adb. If you want, I can cut the tool part from the Medium version.
>
> Thanks for reading,
> Manu Lorenzo
> https://manulorenzo.me

### 2b. The Swift Cooperative: submission note (fastlane guide)

Route: use the publication's own "submit your story" or contact route (not checked: Manu looks it up on the publication's page). If it is a Medium "add to publication" request, paste only the second paragraph and the disclosure.

> Hi,
>
> I'd like to submit "Why your fastlane snapshot screenshots are all in English (and how to check every language)".
>
> It is a troubleshooting post: you list `languages(["en-US", "de-DE", "ja"])` in the Snapfile, and every folder still has English screenshots. It goes through five causes in order (`setupSnapshot` called after launch, running from Xcode, the Simulator language, a build that has no strings for that language, and an app that remembers its own language), with the commands to rule each out. The last part is a command that compares each screenshot with the app's own strings. I tested the causes on small test apps and say which ones I did not reproduce.
>
> It is live at https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english and I'd import it with Medium's import tool, so the canonical stays on my site.
>
> Disclosure: I make shotfleet, a paid Mac tool; the check command in the post is free, and the post says when you do not need it.
>
> Manu Lorenzo, https://manulorenzo.me

### 2c. Code Well (Codemagic): submission note (fallback, either guide)

Route: the "write for Code Well" page on blog.codemagic.io, which adds you as an editor on request. Same text as 2a or 2b, with the first line changed to: "I'd like to be added as a writer for Code Well. The first post would be ..." and one added sentence: "Both guides are about test automation and screenshots in CI-style flows, and the free check command runs in a script, so I thought it could fit your readers." (Only keep that sentence if Manu is happy to claim it: the guides do not show a CI run, so the CI angle is mine, not the guides'.)

---

## 3. Kotlin Slack `#feed` (target Fri 16 Oct)

Channel norms (MORE-PLACES.md, from Kotlin Slack archive threads): `#feed` is where links and self-promotion go. Post the Maestro guide, not the tool. Short, no thread of follow-ups needed. Post after Android Weekly and Kotlin Weekly have sent, so the guide is not competing with itself.

Post:

> Wrote up how to run one Maestro flow in every language, on Android and iOS: Android 13 per-app locales via `adb`, iOS launch args, and four traps that give you English while every run stays green.
> https://shotfleet.com/guides/maestro-one-flow-every-language
> Disclosure: I make shotfleet, a paid Mac tool that automates this. It only comes up in the last 3 sections; the first part is plain Maestro and adb.

(3 lines. Reply to questions in the thread, do not add the price unless asked.)

---

## 4. ASO Stack Slack and Mobile Growth Stack Slack (target Thu 22 Oct)

Rules (https://phiture.com/aso-stack-slack-guidelines, from MORE-PLACES.md): promotion is allowed if it can solve other members' problems; no direct selling or excessive advertising; `#promotion` and `#tools` are the channels. Same family for Mobile Growth Stack (`#promotion`). Join first; joining is not posting.

Labels used (do not mix them): **108 of 120** = the old App Store screenshot set of AnywhereRoles. **127 problems** = the old Google Play set of AnywhereRoles, of which 103 were this same mistake, 15 were false "missing" lines caused by a bug in my own tool (0.1.4, fixed in 0.1.6) and 9 were other things.

### 4a. ASO Stack `#promotion` (or `#tools`)

> Something I found checking my own store screenshots, in case it helps with yours: translated captions are not translated screenshots.
>
> On one of my apps (AnywhereRoles), I ran a check on the old App Store set and 108 of the 120 screenshots were flagged. The captions on top were in German, Japanese and so on, but the app under them was still in English. On the old Google Play set it was 127 problems, 103 of them the same thing (I'd made one English capture and only translated the captions). Another 15 were false alarms from a bug in my own tool, so don't read 127 as 127 wrong images.
>
> Easy way to check yours without any tool: open the screenshot in each language side by side and look at the app text, not the caption. If you want it automated: I made a Mac command-line tool, shotfleet, and its `check` command is free. It reads each image and compares the text with your app's own strings. It needs a simulator build or APK of your app and an Apple silicon Mac. Disclosure: I made it and the capture part is paid ($29 for the first 100, then $49 once; `check` and 2 languages per run are free). It makes no frames or captions and doesn't upload to the stores.
>
> Write-up with the details: https://shotfleet.com/ (the AnywhereRoles section). Happy to answer questions about what check can and can't read.

(Keep the first two paragraphs if it needs to be shorter; they stand alone. Link `https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english` instead of the home page if the channel prefers a how-to.)

### 4b. Mobile Growth Stack `#promotion`

> Quick one for anyone localizing store listings: check the app text under your screenshot captions, not only the captions. On one of my own apps, a check of the old App Store set flagged 108 of 120 screenshots: translated captions over an English app. The old Google Play set had 127 problems, 103 of them the same thing (the others included 15 false alarms from a bug in my own tool).
>
> If useful: I made shotfleet, a Mac command-line tool whose `check` command is free and reads each screenshot against your app's own strings (Apple silicon Mac, needs a simulator build or APK). Disclosure: it's mine, and capturing in every language is paid ($29 for the first 100, then $49 once). Details: https://shotfleet.com/

---

## 5. Email to Jeroen Leenarts (target around Mon 26 Oct)

Public contact route, found 2026-10-07:
- https://www.appforce1.net (home page) links his Mastodon, https://hachyderm.io/@appforce1 (`@appforce1@hachyderm.io`), and his LinkedIn, https://nl.linkedin.com/in/leenarts. The site lists no email address. Neither the podcast page nor the podcast feed's owner field shows one.
- https://www.meetup.com/CocoaHeadsNL/ lists him as organizer with a "Message" button; the group says CocoaHeadsNL also lives on Slack (cocoaheads.nl).
- `info@do-ios.com` is the Do iOS conference address (https://do-ios.com, used there for sponsorship). It is for the conference, so I would not use it for a podcast or meetup ask.
- Do iOS 2026 is 10 to 12 Nov, Amsterdam, NEMO Science Museum (https://do-ios.com).

Best route: a Mastodon DM or LinkedIn message with the short version below; the longer email text works as a Meetup message or if Manu finds an email address. Manu fills the three bracketed bits.

Subject (email or Meetup message): Dutch indie dev, a small tool for localized screenshots (podcast or CocoaHeadsNL?)

> Hoi Jeroen,
>
> I'm Manu, an indie developer based in [city] in the Netherlands, and I'll write in English. I've listened to AppForce1 for [how long / one episode you liked, Manu: be specific or drop this sentence], and I'm [going to Do iOS in November / not at Do iOS this time, Manu: fill in].
>
> I made a small Mac command-line tool called shotfleet. You write one English Maestro flow (or, on iOS, use your own XCUITest screenshot tests), and it takes the App Store and Google Play screenshots in every language your app has, then checks that each image is really in that language. It started because I found my own old store screenshots had translated captions over an app that was still in English: 108 of 120 on the old App Store set of one of my apps. The check part is free, and it's a paid tool for the rest ($29 for the first 100, then $49 once). It's closed source, Apple silicon only. Full disclosure, I'm writing as its maker.
>
> I wrote two guides that I think are useful to iOS developers even without the tool: why fastlane snapshot gives you English in every language folder (https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english), and the Maestro one (https://shotfleet.com/guides/maestro-one-flow-every-language).
>
> One ask: would you be up for a short chat for the podcast, or a mention if it fits an episode? If that is not your thing, I'd happily give a 10 minute lightning talk at a CocoaHeadsNL meetup this winter about what I found in my screenshots, with no tool pitch. And if you prefer neither, no problem at all, I just wanted to say hi before Do iOS.
>
> Groeten,
> Manu Lorenzo
> https://manulorenzo.me · https://shotfleet.com

Short version for a Mastodon DM or LinkedIn message (under 500 characters):

> Hoi Jeroen, Manu here, Dutch-based indie dev. I made shotfleet, a paid Mac tool (its check command is free) that takes store screenshots in every language and checks they're really in that language. I'd love a short AppForce1 chat or a mention, or a 10 min CocoaHeadsNL lightning talk on what I found checking my own screenshots. Disclosure: I'm the maker. Guide: https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english

---

## 6. Appdevcon 2027 CFP (closes Fri 18 Dec 2026)

Where: https://sessionize.com/dawn-conferences-2027/ (MORE-PLACES.md: Amsterdam, March 2027; lightning talks of 20 to 30 min; speaker airfare, hotel and entry covered). The date range for the conference is 16 to 18 Mar in one place and 16 to 19 Mar in another place in MORE-PLACES.md; check https://appdevcon.nl before writing a date anywhere. I could not find a page on manulorenzo.me with a bio sentence (the site builds its content in the browser from `config.js`); the bio below is from that config and from shotfleet.com.

On numbers: the title idea in the brief says "600+ store screenshots". I could not find a total like that in the research records, and the sets I can name (252 iOS images of WOD Tracker, 220 of another app, 120 old App Store screenshots of AnywhereRoles, the old Google Play set whose size I did not find) would be me adding up different checks. So the draft below uses only the figures that stand alone. If Manu re-counts everything he has checked, he can put the real total in the title.

**Title**

Your localized screenshots are probably English: what I found checking my own store listings

(Alternative: "Translated captions, English app: checking store screenshots in 18 languages")

**Abstract (about 150 words)**

I ship my own apps in many languages and I thought their screenshots were localized. They were not. When I checked the old App Store set of one app, 108 of 120 screenshots had translated captions over an app that was still in English. On the old Google Play set, a check found 127 problems, 103 of them the same mistake. I made it myself: one English capture, translated captions on top.

This talk is about how that happens and how to find it in your own listings. We look at where fastlane snapshot, Maestro and UI tests quietly fall back to English, why the run still goes green, what a screen looks like when German is longer than English, and one case where a Next button was off the screen in four languages and nobody noticed. You leave with a checklist, a few commands you can run on your own screenshots, and a sense of what is worth fixing first. It is not a product talk.

**Outline (25 minutes, or a 15 minute cut)**

1. The mistake (3 min): my old App Store and Google Play screenshots, 108 of 120 and 127 problems, and what "translated" really meant.
2. Why nothing warns you (4 min): the run goes green. How the language reaches the app on iOS (launch arguments, `AppleLanguages`) and on Android 13 and up (per-app locales), and where each one breaks.
3. Five causes of English in a fastlane snapshot folder (5 min): `setupSnapshot` after launch, running from Xcode, the Simulator language, a build without that language's strings, an app that remembers its own language.
4. Long text and small screens (4 min): the Next button nobody could reach in Japanese, Korean, Chinese and Arabic on a small Android phone, and the fix (make the page scroll).
5. Checking what you already have (5 min): look at images side by side, compare the text with the app's own strings, find copies and missing screens. Free, with open tools where they exist; I show the tool I made in one slide and say it is paid.
6. Checklist and what I would do first (4 min).

(Cut for 15 minutes: merge 2 and 3, drop 4.)

**Speaker bio**

Manu Lorenzo is a solo developer in the Netherlands. He builds Android and iOS apps with Kotlin and Swift, and the Spring Boot services behind them. His own apps include WOD Tracker (a CrossFit and weightlifting log), AnywhereRoles (remote jobs), Keysi (a macOS shortcut cheat sheet), and Kuokka (a Hacker News reader). He also makes shotfleet, a paid Mac command-line tool that captures and checks localized store screenshots, and he says so up front in the talk. Site: https://manulorenzo.me.

**Why this is useful to the audience (the field for "notes to the committee")**

Every attendee who ships an app in more than one language has a store listing, and almost nobody checks it image by image. The talk gives them a way to check their own listings with commands they can run that afternoon, and a list of the five ways iOS and Android fall back to English without telling you. Everything in it comes from checking my own apps, with numbers I can show, including the false alarms from my own tool. The only mention of a product is one slide, labelled as mine and paid. If the committee prefers, I will drop that slide.

---

## Things I could not do or check

- No personal email for Jeroen was found; the email is written for a DM or Meetup message.
- The Swift Cooperative submit route and the Hashnode "Maestro" tag were not checked.
- ProAndroidDev's guidelines page returned 403; the email address is from MORE-PLACES.md.
- No cover images were made.
- The Appdevcon date (16 to 18 or 16 to 19 Mar) differs inside MORE-PLACES.md and needs a look at appdevcon.nl.
