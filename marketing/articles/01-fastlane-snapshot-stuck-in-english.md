# Article 1: fastlane snapshot stuck in English

Status: draft for Manu to publish on the new domain. Not published. Written 2026-10-02.

| Field | Value |
|---|---|
| Title (H1) | Why your fastlane snapshot screenshots are all in English (and how to check every language) |
| Meta description (under 160 chars) | Every language folder shows English? Five causes to rule out in fastlane snapshot, plus a free command that checks each image against your app's own strings. |
| Slug | `/fastlane-snapshot-screenshots-all-english` |
| Target query | fastlane snapshot wrong language / fastlane snapshot not changing language / fastlane screenshots all english |
| Why this can rank | The results for this query are old GitHub issues (#8895, #9043, #10846, #11457, #11736, #12917), not guides (research/marketing-research.md 3.3). |
| Canonical | Our domain. Any cross-post (dev.to, Medium) must point its canonical URL here. |

## Internal link plan

- Product: link the word "shotfleet" once in the intro (disclosure) to `https://shotfleet.com/`, and once at the end to `https://shotfleet.com/#price`. Add `?utm_source=article-snapshot` only on links used outside our own domain.
- Free command: the call to action is `shotfleet check`, with a link to `https://shotfleet.com/#price`, which is where the install command sits (site/public/index.html has no separate install anchor; the sections are `#run`, `#catch`, `#flow`, `#apps`, `#price`).
- Other articles: link to article 2 (one Maestro flow in every locale) in the "when not to use" paragraph; link to article 4 in 04-ideas.md (QA checklist) once it exists.
- Footer of the site links to this article (MARKETING.md phase 0).

## TO VERIFY BEFORE PUBLISHING

1. The build command in "Step 2" (`xcodebuild ... -sdk iphonesimulator`) with your real scheme name. It is the command from the README CI recipe, which has not been run on GitHub yet. TICKED 2026-10-03 (ran it): `xcodebuild -scheme MyApp -sdk iphonesimulator -configuration Debug -derivedDataPath build build` on Xcode 27.0 (27A266a), exit 0, `** BUILD SUCCEEDED **`, 60 s wall time with other jobs running on the Mac, and `build/Build/Products/Debug-iphonesimulator/MyApp.app` exists. The scheme was a throwaway SwiftUI app with a String Catalog (made with xcodegen in a scratch folder), not a real app. Not run: a workspace or a real app with several targets.
2. `shotfleet check fastlane/ --app build/Build/Products/Debug-iphonesimulator/MyApp.app` on a clean Mac with the released installer (`curl ... install.sh | sh`). At the time of writing `/download/VERSION` returned 404, so the installer does not work until the first release is published (claims C057). PARTLY TICKED 2026-10-05 (ran it, release 0.1.0 is now live): the live `install.sh` (sha256 of the script starts 2273fd6b) with the install folder edited to a temp HOME so the Mac's own folders stay untouched, `env -i`, bare PATH: it downloaded, passed the checksum and printed `installed shotfleet 0.1.0`; the article's command `shotfleet check fastlane/ --app .../MyApp.app` (15 screenshots in three locales copied from a real fastlane folder, read only, and the throwaway app) ran with no licence and wrote `shotfleet-check/check.json` and `index.html`, exit code 1 because it reported problems. NOT clean: on this Mac macOS text recognition was wedged (a root-owned ANECompilerService had spun for 10 hours), so with a bare PATH `check` stopped after 47 s and again after 2 min 45 s with `macOS text recognition isn't answering (its ANECompilerService is stuck ...); restarting the Mac fixes it. Or install Tesseract`. With `/opt/homebrew/bin` on the PATH it found Tesseract and finished in 1 min 43 s. So the macOS-recognition path of the released binary is still to run on a healthy Mac. The article now mentions the message and the Tesseract fallback. TICKED 2026-10-06 (ran it after the Mac restarted, release 0.1.4): live `install.sh` into a temp HOME, `env -i`, bare PATH with no Tesseract, so only macOS text recognition could read. The article's command on a real app: `shotfleet check fastlane/screenshots --app remoti.app` (220 committed fastlane iOS screenshots in 20 languages from the remoti repo, copied read only, and its Debug-iphonesimulator build) printed `checked 220 screenshots in 20 languages: 0 problem(s)`, exit 0, 57 s at load 100-170. A second run on 72 Android screenshots: 0 problems, exit 0, 29 s at load 680-910. No 'isn't answering' message either time. Not run: a different Mac (this is the build Mac).
3. Cause 4 ("the app is not translated into that language, so iOS falls back to English") and cause 5 ("the app saved its own language choice"). They are my reasoning, not from an issue thread. Reproduce each once, for example by deleting `de.lproj` from a build and re-running, then edit or soften the text. TICKED 2026-10-03 (ran both, no fastlane involved, on an iOS 26.4 iPhone 17 simulator with the build from item 1, launching with `-AppleLanguages "(de)" -AppleLocale de_DE`): (a) with `de.lproj` present the screen shows "Willkommen" and "Weiter"; with `de.lproj` deleted from a copy of the build it shows "Welcome" and "Next", while `ja` on the same build still shows Japanese. (b) A test app that saves its own language choice in `UserDefaults` (written once with a `-saveLanguage en` launch argument) showed English on the next launch with the same German arguments; after uninstalling and installing again it showed German. That uninstall and install is what `reinstall_app` does according to the docs, but I did not run snapshot's own option. A first attempt wrote the value with `simctl spawn defaults write`, which lives outside the app container and survived the uninstall; that was my method, not a finding.
4. That `ls MyApp.app/*.lproj` lists the languages of a build that uses a String Catalog (it should: Xcode compiles catalogs into `.lproj` folders; confirm on your app). TICKED 2026-10-03 (ran it): the build from item 1, whose catalog has `de` and `ja` entries, contains `de.lproj` and `ja.lproj` and no `en.lproj`, because the catalog has no explicit English entries (English is the key). The article now says so.
5. The timing sentence (about 25 seconds, and minutes after a restart) is from claims C030 and README; re-time on the final build. PARTLY TICKED 2026-10-02 (read from the repo, nothing run): README line 42 says about 25 seconds per platform for 252 iOS and 126 Android images; C030 is `evidence` (PLAN.md, research/first-run.md ~30 s, cold-test-2 28 s) and ROADMAP records about 4 minutes for the first check after a restart. Still to run: re-time on the final build. 2026-10-05: not possible yet. The 252 and 126 image folders no longer exist in the app repo (it holds 90 iOS images now), no simulator build of that app is on this Mac, macOS text recognition is wedged (see item 2) and the Mac was at load 200. The only timing I have is 1 min 43 s with Tesseract on 15 images under that load, which says nothing about the 25 seconds. 2026-10-06 (0.1.4, macOS text recognition, warm, not the first check after the restart): 220 iOS images of another real app in 57 s at load 100-170 (item 2). That is roughly half the speed of 'about 25 seconds for 252 images', on a busy Mac; the 252-image set is gone, so the sentence below now says 'under a minute'. Cold timing (the first check after a restart) was not measured: 0.1.4 proof D took 747 s while macOS compiled its model on a quiet Mac.
6. Re-open the four issue links and the fastlane docs page and check that the one-line descriptions below still match. The issues are from 2017 and 2018, so do not imply the bug exists in current fastlane without a fresh reproduction. TICKED 2026-10-03 (opened the pages): there are three issue links, not four, plus two docs pages. #8895 (opened 2017-04-16, closed): language stays en-US after updating to Xcode 8.3, matches. #11457 (2018-01-06, closed): `localize_simulator true` fixes it and gives an "ugly statusbar" because the simulators are erased, matches. #12917 (2018-07-17, closed): English from fastlane, correct when run manually in Xcode with the generated language file, matches. Docs: the temporary-file sentence, `setupSnapshot(app)` before `app.launch()` in `setUp()`, `localize_simulator`, `reinstall_app`, `erase_simulator`, and the warning that running the test in Xcode does not create the snapshots all match. Added "All three are closed" to the text.
7. Confirm the anchor names on the final site (`#price`, install section). TICKED 2026-10-02 (read from the repo, nothing run): `#price` and `#run` exist in site/public/index.html; there is no install-section anchor, so the article links `#price` (the install command is in that block). Done, unless the site is redesigned.

Sources used (fetched 2026-10-02):
- https://docs.fastlane.tools/actions/snapshot/ and https://docs.fastlane.tools/getting-started/ios/screenshots/
- https://github.com/fastlane/fastlane/issues/8895, /11457, /12917
- Claims backing shotfleet sentences: C015, C026, C028, C030, C032, C071 (proven or evidence); the "needs Mac" and Apple silicon statements come from README Limits and install.sh.

---

# Why your fastlane snapshot screenshots are all in English (and how to check every language)

You set `languages(["en-US", "de-DE", "ja"])` in your Snapfile, ran `fastlane snapshot`, and opened the folders. German and Japanese are there, and every image is in English.

I build a tool in this area (shotfleet, which comes up at the end), so read this with that in mind. The first four steps below need nothing from me.

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

## Step 1: stop guessing, look at every image

With 18 languages and 4 screens that is 72 images. Opening them by hand works until the day you skip one. A faster way is to compare each screenshot with the text your app really contains.

## Step 2: check the folder you already have

shotfleet's `check` command does that, and it is free: no licence, no account. It does not capture anything and does not touch your fastlane folders. It needs a Mac, because it uses the text recognition built into macOS, and it needs a simulator build of your app so it knows your real strings:

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

On the committed fastlane screenshots of my own workout app (252 iOS images) it took under a minute and found one real problem: Traditional Chinese listings with Chinese captions over an app that was still in English. When I planted English screenshots in a German folder and deleted a Japanese one, both were reported. The first check after a restart is slower, because macOS compiles its text-recognition model once; it can take minutes.

Pass `--app`. Without it `check` falls back to language detection, which cannot judge short screens.

## What this does not tell you

- If `check` says "macOS text recognition didn't answer in time" (or "isn't answering"), macOS is usually still compiling its text-reading model, which can take minutes on a busy Mac the first time (once about 40 minutes on a quiet one). `check` doesn't fail over it: it finishes and marks the screens it couldn't read as "not verified". Run it again later, or install Tesseract (`brew install tesseract tesseract-lang`) and `check` uses it automatically. No restart needed.

- It says the language is wrong. It does not say why. Go back to the five causes.
- macOS text recognition reads 33 languages. For other scripts (Greek, Hebrew, most Indic scripts) `check` still catches other-language screens, copies and missing screens, and says which screens it could not read. You can plug in Tesseract for full coverage.
- Copies are only reported on screens with enough text. Two near-empty screens that are identical can pass.
- It is only as good as your simulator build matching the build that made the screenshots.

## When not to use shotfleet

If your screenshots are already right in every language, you do not need it. If you have only two or three languages, looking at the images yourself is fine. If you already have a maintained UI-test suite and snapshot works for you, keep snapshot; it is free and `check` can sit next to it. The tool only runs on an Apple silicon Mac (the installer refuses Intel), and capturing with `shotfleet run` is a separate step with its own requirements (Xcode, the Android SDK for Android, Maestro 2.x, Java 17+, and a Maestro flow you write). It does not make frames or captions and does not upload to the stores. I also have no data yet on how often modern fastlane versions hit the problem in this article; the issue threads are old.

## Where to go from here

If `check` finds wrong-language images and you would rather not maintain per-language UI tests at all, shotfleet also captures: one English Maestro flow, every language your app ships, on iOS and Android. `run` is free for up to 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once (14-day refund). Details at https://shotfleet.com/#price.

The free part is the `check` command above. Install it, point it at your `fastlane/` folder and read the grid.
