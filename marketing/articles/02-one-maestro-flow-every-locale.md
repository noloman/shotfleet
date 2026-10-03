# Article 2: one Maestro flow in every locale

Status: draft for Manu to publish on the new domain. Not published. Written 2026-10-02. Every snippet below is UNRUN here (no free simulator or emulator in this session); see the TO VERIFY list. Do not publish until each item is ticked.

| Field | Value |
|---|---|
| Title (H1) | Run one Maestro flow in every language: iOS launch arguments, Android per-app locales, and the traps |
| Meta description (under 160 chars) | Maestro cannot set the locale inside a flow. Here is how to run one flow in every language on iOS and Android, and the four traps that give you English by mistake. |
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

1. PARTLY TICKED (code read): shotfleet.py:714 writes `AppleLanguages: "(<lproj>)"` and `AppleLocale: "<locale>"` as literals under `launchApp.arguments`, so the argument names and shape are right; whether `${...}` expands inside them is still to run. iOS flow below: `launchApp` with `arguments: AppleLanguages: "(${APP_LANG})"` and `AppleLocale: "${APP_LOCALE}"`. Does `${...}` expand inside `arguments` values? If not, generate the file per language with `sed`. shotfleet itself writes literal values per language and ran 18/18 on iOS, but not through env variables.
2. `takeScreenshot: shots/${APP_LANG}/02_onboarding` writes to that folder (env in the path).
3. `maestro --device "$UDID" test -e APP_LANG=de -e APP_LOCALE=de_DE flow.yaml` (flag order is from the morse_app PR and Maestro docs).
4. PARTLY TICKED (code read, not run): shotfleet.py:1237 issues `adb shell cmd locale set-app-locales <pkg> --locales <lp>`, so the command is what shotfleet itself uses; running it on an API 33+ emulator and `get-app-locales` is still to do. Android: `adb -s SERIAL shell cmd locale set-app-locales PACKAGE --locales de` on an API 33+ emulator, then `cmd locale get-app-locales PACKAGE`. Android's own page (developer.android.com/guide/topics/resources/app-languages) does not mention this shell command; the claim rests on community posts and on shotfleet's code, so run it and say what you saw.
5. PARTLY TICKED (code comment read, not run): shotfleet.py:1178 says clearState "wipes the per-app language shotfleet just set" and strips it from the flow on Android; the with/without run is still to do. Android trap: `clearState` in `launchApp` resets the app language (shotfleet's code comment says `pm clear` also resets it). Run the flow with and without it and confirm.
6. `runFlow` with `when: platform: iOS` / `Android` runs the right branch (syntax confirmed from docs.maestro.dev/reference/commands-available/runflow; not run).
7. The env-precedence trap (header `env:` default beating `-e`): reproduce on your Maestro version. The report is for 2.10 in https://github.com/RogerioDoCarmo/morse_app/pull/216; Maestro's parameters page says constants in a subflow override parameters from the parent, which is related but not the same. If you cannot reproduce it, rewrite that trap as "check this" instead of "this happens".
8. PARTLY TICKED: shotfleet.py:885-889 and claims C098 (`evidence`) back the 2.0.10 statement; the re-test on your Maestro version is still to run. Port 7001 trap: two `maestro test` processes on two Android devices at the same time. Our note is for 2.0.10 (port 7001 to 7128 per shard) and says the port is random per shard in 2.11. Re-test or drop it.
9. iOS permission alerts stay English while the app is German: measured once with Maps on `main` (research/pricing-2026-10.md). Android not tested. Keep the sentence as "I measured this once on iOS".
10. Re-open the Maestro docs pages cited and make sure the short phrases still match (locales page, launchApp, parameters-and-constants, scrollUntilVisible).

Sources fetched 2026-10-02:
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales
- https://docs.maestro.dev/reference/commands-available/launchapp
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/parameters-and-constants
- https://docs.maestro.dev/reference/commands-available/runflow
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

**1. A default in the flow header beats the command line.** One developer documented this with Maestro 2.10: the flow had `env: { LOCALE: en }` as a default, and every "Portuguese" and "Spanish" run still came out in English. He fixed it by removing the default from the header, and he caught it only by looking at the images ([PR #216](https://github.com/RogerioDoCarmo/morse_app/pull/216)). Maestro's parameters page says that constants defined in a subflow override same-name parameters from the parent. Do not put a default for the language in the header. Pass the language only with `-e`, and look at the first image of each run.

**2. `-e` goes after `test`.** In the same PR the iOS script put `-e` before `test`, and it failed silently while looking like it passed. The order is `maestro --device X test -e KEY=VALUE flow.yaml`.

**3. On Android, clearing state clears the language.** `clearState` wipes the app's data, and the per-app language goes with it. Clear first with `pm clear`, set the language, then launch without `clearState`. Otherwise you get the system language back.

**4. Parallel runs on Android.** Two separate `maestro test` processes on two devices share a host port (7001 in the version I used, 2.0.10) and can drive each other's device. Use one run that shards across devices (`--shard-split`). Newer Maestro versions pick a port per shard, so check yours.

Two smaller ones. System permission dialogs are drawn by the OS in the device language, which stays English while your app is German (I measured this once on iOS, with Maps), so write those taps in English or skip them with `permissions: all: allow` in `launchApp`. And long languages push buttons off the screen: use `scrollUntilVisible` before the tap, with `direction: DOWN` ([article 3](https://shotfleet.com/the-button-nobody-could-reach) has the story).

## Read the images, not the exit code

All four traps pass. The only way to catch them is to look at the output, or to have something look for you: `shotfleet check shots/ --app path/to/MyApp.app` reads each image back and reports wrong-language and duplicate images. It is free (no licence, no account) and works on any folder of screenshots.

## Where shotfleet fits

Doing all of the above by hand for 18 languages on two platforms is a lot of scripting, and that is the work shotfleet does. It reads the translations compiled into your build and rewrites every text selector in your English flow for each language, so `tapOn: "Next"` becomes `(Nächste|Weiter)` in German. It runs the languages in parallel on simulators and emulators and checks each image. On my own app, 18 languages by 4 screens (72 screenshots) took 9 minutes on iOS and 15 on Android on one Mac, four simulators in parallel. That is one app and Maestro 2.0.10, so treat it as a data point. `run` is free for 2 languages; a licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once, 14-day refund.

## When not to use shotfleet

If your app has ids on everything you tap, three or four languages, and one platform, the loop above is enough. If you test on real devices or in a device cloud, shotfleet does not help; it runs simulators and emulators on your Mac. It needs an Apple silicon Mac, Maestro 2.x and Java 17+, and Android needs API 33+ emulators. It makes no frames or captions and does not upload to the stores. For Flutter and React Native it works from your translation files; I have tested that on real translation files but not on a real Flutter or React Native app yet, so I do not claim it.
