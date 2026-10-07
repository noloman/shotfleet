# Article 2: one Maestro flow in every locale

Status: published to site/public/guides/ on 2026-10-06 at Manu's word (goes live with the 0.1.6 site deploy). Written 2026-10-02; every TO VERIFY item below was run (iOS and Android, Maestro 2.0.10). Edits when publishing: removed the pointer to this TO VERIFY list (readers can't see it); the article 3 link (a 404, unpublished) now points at the same story on the home page; 'Next' becomes 'Weiter', or (Nächste|Weiter) only when the app has two translations (C016); the four simulators are the iOS run's; the Flutter/React Native line now says what README says since 2026-10-03 (run end to end on wger and the obytes Expo template); added a link to guide 1. Claims C251-C254.

| Field | Value |
|---|---|
| Title (H1) | Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps |
| Title tag (under 60 chars, the search-result title) | One Maestro flow in every language, on iOS and Android |
| Meta description (under 160 chars) | Maestro can't set the locale inside a flow. How to run one flow in every language on iOS and Android, and the four traps that give you English by mistake. |
| Slug | `/maestro-one-flow-every-language` |
| Target query | maestro multiple languages / maestro locale / maestro screenshots different languages / maestro device-locale |
| Why this can rank | Few tutorials; results are the Maestro docs, vendor docs and one Medium post (research/marketing-research.md 3.3). The docs do not cover the traps. |
| Canonical | Our domain. Cross-posts point their canonical here. Also submit the link to the Maestro docs community articles page and awesome-maestro (see marketing/kit/maestro-community.md). |

## Internal link plan

- Product: one disclosed mention near the end, link to `https://shotfleet.com/` (and `#price` only in the last paragraph).
- Free command: `shotfleet check` in the "read the images" step, linking to article 1 and the install section.
- Article 3 (the button nobody could reach): link from the long-text trap.
- Do not link the product from the first three sections. The tutorial has to stand alone.

## TO VERIFY BEFORE PUBLISHING

Run each on a throwaway app (tools/fixture-app has en, de, ja, ar, tr on iOS) with the Maestro version you state in the article. The Maestro installed on this Mac is 2.0.10, upstream is 2.11.0 (research/limits-text.md). State the version you tested.

1. Code read: shotfleet.py:714 writes `AppleLanguages: "(<lproj>)"` and `AppleLocale: "<locale>"` as literals under `launchApp.arguments`, so the argument names and shape are right; TICKED 2026-10-03 (ran it): with `launchApp: arguments: AppleLanguages: "(${APP_LANG})"` and `AppleLocale: "${APP_LOCALE}"` the variables expand. Maestro 2.0.10, iPhone 17 simulator iOS 26.4, throwaway SwiftUI app with `en`, `de`, `ja`: the `de` run showed "Einstellungen" and "Fertig", all three runs exited 0. The Maestro log line still prints `(${APP_LANG})` unexpanded, so do not judge by the log. iOS flow below: `launchApp` with `arguments: AppleLanguages: "(${APP_LANG})"` and `AppleLocale: "${APP_LOCALE}"`. Does `${...}` expand inside `arguments` values? If not, generate the file per language with `sed`. shotfleet itself writes literal values per language and ran 18/18 on iOS, but not through env variables.
2. `takeScreenshot: shots/${APP_LANG}/02_onboarding` writes to that folder (env in the path). TICKED 2026-10-03 (ran it): files appeared as `shots/en/`, `shots/de/`, `shots/ja/` under the folder where `maestro` was started; the log line shows the path unexpanded. Maestro 2.11.0 is NOT covered by this tick: a shotfleet session (3891c0, 2026-10-04, not run by me) reports that on 2.11.0 an absolute path outside Maestro's artifact folder is rejected, and that a relative name like `de/01_welcome` works on both versions but lands under the run's debug output folder on 2.11.0, not in the working directory. Re-run this item before writing "tested with 2.11.0"; `${...}` inside `launchApp: arguments` has not been tested on 2.11.0 by anyone.
3. `maestro --device "$UDID" test -e APP_LANG=de -e APP_LOCALE=de_DE flow.yaml` (flag order is from the morse_app PR and Maestro docs). TICKED 2026-10-03 (ran it, iOS): `maestro --device "$UDID" test -e APP_LANG=de -e APP_LOCALE=de_DE flow.yaml` ran for en, de and ja on 2.0.10. `--device`/`--udid` is a global option listed before the commands in `maestro --help`; `-e, --env` belongs to `test`.
4. Code read: shotfleet.py:1237 issues `adb shell cmd locale set-app-locales <pkg> --locales <lp>`, so the command is what shotfleet itself uses; running it on an API 33+ emulator and `get-app-locales` is still to do. Android: `adb -s SERIAL shell cmd locale set-app-locales PACKAGE --locales de` on an API 33+ emulator, then `cmd locale get-app-locales PACKAGE`. Android's own page (developer.android.com/guide/topics/resources/app-languages) does not mention this shell command; the claim rests on community posts and on shotfleet's code, so run it and say what you saw. TICKED 2026-10-03 (ran it): API 36 emulator (AVD `shotfleet_android`, 1080x1920, the repo's `tools/fixture-app-android`, package `com.shotfleet.fixture`): `cmd locale get-app-locales` printed `Locales for com.shotfleet.fixture for user 0 are []`, after `set-app-locales ... --locales de` it printed `[de]`, and the launched app showed "Willkommen" and "Weiter". Only API 36 was run, not 33 to 35; the 33+ statement rests on the Android docs.
5. Code comment read: shotfleet.py:1178 says clearState "wipes the per-app language shotfleet just set" and strips it from the flow on Android; the with/without run is still to do. Android trap: `clearState` in `launchApp` resets the app language (shotfleet's code comment says `pm clear` also resets it). Run the flow with and without it and confirm. TICKED 2026-10-03 (ran it, API 36, Maestro 2.0.10): with the language set to `de`, a flow with `launchApp` and no `clearState` left `get-app-locales` at `[de]`; a flow with `launchApp: clearState: true` left it at `[]`. `pm clear` alone also reset it to `[]` after `set-app-locales de`, so the order in the article (clear first, then set the language, then launch without `clearState`) is right. A full flow with the language set from outside, run for `de`, `ja` and `en`, produced "Einstellungen" and "Fertig" (de) and the Japanese screen (ja). Also seen: a `takeScreenshot` straight after `launchApp` gave a blank white image on Android, the same race as on iOS.
6. `runFlow` with `when: platform: iOS` / `Android` runs the right branch TICKED 2026-10-03 (ran it on both): the same flow with `runFlow: when: platform: iOS` and `platform: Android` blocks ran only the iOS block on the iOS 26.4 simulator and only the Android block on the API 36 emulator (no file from the other block appeared). Checked 2026-10-03: the `when: platform:` condition is documented on https://docs.maestro.dev/maestro-flows/flow-control-and-logic/conditions (example `runFlow: when: platform: Android`), not on the runFlow page; the Sources below name the right page.
7. The env-precedence trap (header `env:` default beating `-e`): reproduce on your Maestro version. The report is for 2.10 in https://github.com/RogerioDoCarmo/morse_app/pull/216; Maestro's parameters page says constants in a subflow override parameters from the parent, which is related but not the same. If you cannot reproduce it, rewrite that trap as "check this" instead of "this happens". TICKED 2026-10-03 (ran it, iOS): on Maestro 2.0.10 a flow with `env: APP_LANG: en` and `APP_LOCALE: en_US` in the header, run with `-e APP_LANG=de -e APP_LOCALE=de_DE`, produced the English screen and `t1/en_welcome.png`. The header default beat `-e`. The article says 2.10 for the PR report and now also that I saw it on 2.0.10. Also found: `maestro --device X -e APP_LANG=de test flow.yaml` (trap 2) does not fail silently on 2.0.10: it prints `Unknown options: '-e', 'APP_LANG=de'` and the usage text and exits with code 2. The article's trap 2 is rewritten.
8. Port 7001 trap (re-tested 2026-10-03, see the end of this item); background: shotfleet.py:885-889 and claims C098 (`evidence`) back the 2.0.10 statement. two `maestro test` processes on two Android devices at the same time. Our note is for 2.0.10 (port 7001 to 7128 per shard) and says the port is random per shard in 2.11. Re-test or drop it. TICKED 2026-10-03 (ran it, API 36, Maestro 2.0.10, two emulators of the same phone AVD on ports 5570 and 5572, one `maestro test` process each, started together): each process passed when run alone. Together, in two attempts, one of the two failed each time: `java.util.concurrent.TimeoutException` (attempt 1 process A, attempt 2 process B), and in attempt 1 the other process threw `NoSuchFileException: /Users/manu/Library/Logs/maestro/<timestamp>` while finishing and then hung until I killed it (both processes started in the same second, so a shared timestamped log folder is a possible cause). During the run `lsof` showed one java process listening on TCP 7001. I did not see one process drive the other's device (the screenshots that were written had the right language), and I did not prove that port 7001 is the cause. The article's trap 4 is reworded to what I saw. Not run: `--shard-split`, and Maestro 2.11.
9. iOS permission alerts stay English while the app is German: measured once with Maps on `main` (research/pricing-2026-10.md). Android not tested. Keep the sentence as "I measured this once on iOS". TICKED 2026-10-04 (ran it): fresh iPhone 17 simulator, iOS 26.4, `simctl privacy reset all`, then `simctl launch com.apple.Maps -AppleLanguages "(de)" -AppleLocale de_DE`. Maps' own screen was German ("Mitteilungen aktivieren", "Später") while the location permission alert was English ("Allow \"Maps\" to use your location?", "Allow Once", "Allow While Using App", "Don't Allow"). Android permission dialogs were not tested and the article says so.
10. Re-open the Maestro docs pages cited and make sure the short phrases still match (locales page, launchApp, parameters-and-constants, scrollUntilVisible). TICKED 2026-10-03 (opened the pages, nothing run): locales page says there is "no place within a Flow itself" and `--device-locale` works with `maestro start-device` and `maestro cloud`, not `maestro test`, matches the article; launchApp `arguments` ("key-value pairs to pass as launch arguments") and `clearState` match; parameters page quote about constants in a subflow overriding parent parameters matches; scrollUntilVisible: `DOWN` is the default direction and an element is visible when fully displayed (`visibilityPercentage` 100), matches. NOT found: `permissions: all: allow` is not on the launchApp page (it shows `all: deny` and single permissions), so the article's "skip them with `permissions: all: allow`" was replaced by a line saying the `permissions` setting exists and was not tested.

Sources fetched 2026-10-02:
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales
- https://docs.maestro.dev/reference/commands-available/launchapp
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/parameters-and-constants
- https://docs.maestro.dev/reference/commands-available/runflow
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/conditions (for `when: platform:`)
- https://developer.android.com/guide/topics/resources/app-languages (per-app languages arrived in Android 13, API 33)
- https://github.com/RogerioDoCarmo/morse_app/pull/216
- Claims for shotfleet sentences: C015, C016, C098 (evidence), C070 (partial, README tip), C073.

---

# Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps

You wrote a Maestro flow for your app and now want the same screens in German, Japanese and Arabic, for screenshots or for a smoke test. The docs are short on this, and the failure mode is quiet: every run goes green and the images are in English.

I build a tool around this problem (shotfleet, mentioned once near the end). Everything before that is plain Maestro and `adb`.

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

Doing all of the above by hand for 18 languages on two platforms is a lot of scripting, and that is the work shotfleet does. It reads the translations compiled into your build and rewrites every text selector in your English flow for each language, so `tapOn: "Next"` becomes `Weiter` in German, or `(Nächste|Weiter)` if your app has two translations for it. It runs the languages in parallel on simulators and emulators and checks each image. On my own app, 18 languages by 4 screens (72 screenshots) took 9 minutes on iOS (four simulators in parallel) and 15 on Android, on one Mac. That is one app and Maestro 2.0.10, so treat it as a data point. `run` is free for 2 languages; a licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once, 14-day refund.

## When not to use shotfleet

If your app has ids on everything you tap, three or four languages, and one platform, the loop above is enough. If you test on real devices or in a device cloud, shotfleet does not help; it runs simulators and emulators on your Mac. It needs an Apple silicon Mac, Maestro 2.x and Java 17+, and Android needs API 33+ emulators. It makes no frames or captions and does not upload to the stores. For Flutter and React Native it works from your translation files. I have run that end to end on one real Flutter app (wger) and one real Expo app (the obytes template), on iOS and Android, and not yet on any other.
