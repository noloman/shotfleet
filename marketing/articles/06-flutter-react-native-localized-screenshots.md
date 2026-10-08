# Article 6: localized store screenshots for a Flutter or React Native app

Status: draft for Manu to publish. Not published. Written 2026-10-06 by the SEO pass (research/seo-audit-2026-10-06.md section 8).

| Field | Value |
|---|---|
| Title (H1) | Localized App Store and Google Play screenshots for a Flutter or React Native app, from one Maestro flow |
| Title tag (under 60 chars, the search-result title) | Flutter and React Native screenshots in every language |
| Meta description (under 160 chars) | What I learned running one Maestro flow in every language on a real Flutter app and a real Expo app: the language, the labels, the traps, and the setup. |
| Slug | `/flutter-react-native-localized-screenshots` |
| Target query | flutter localized app store screenshots / flutter screenshots multiple languages / react native expo app store screenshots multiple languages / maestro flutter localization |
| Why this can rank | The results are pub.dev packages that render screens without a device (golden tests, device_preview wrappers) and AI design tools that translate captions; a forum post asks how to do it with Expo and has no real answer. Nothing walks through a real device run on both platforms (web search, 2026-10-06; see research/seo-audit-2026-10-06.md section 6). |
| Canonical | Our domain. Any cross-post must point its canonical URL here. |

## Internal link plan

- Product: link "shotfleet" once in the intro (disclosure) to `https://shotfleet.com/`, and `https://shotfleet.com/docs#strings` where the `strings` key is documented.
- Other articles: article 2 (one Maestro flow in every language) for the iOS and Android language mechanics; article 5 (check localized screenshots) at the end.
- Docs Limits: `https://shotfleet.com/docs#limits` for the Flutter row label and Xcode 27 notes.

## TO VERIFY BEFORE PUBLISHING

1. Everything in "What I ran" is from research/frameworks.md section 15 (2026-10-03, Maestro 2.0.10, Xcode 27.0, Flutter 3.47.6). Re-run at least one Flutter and one Expo app on the current release and Maestro 2.11, and update the versions and dates, or keep the dates and say "on 2026-10-03".
2. The `strings` lines: copy them from the current docs (`/docs#strings`) on the day; the obytes template's path (`src/translations/*.json`) is what `init` wrote in that run, the docs example (`src/locales/*/translation.json`) is a different layout. Keep both and say which is which.
3. The Xcode 27 build line for Expo (`xcodebuild ... IPHONEOS_DEPLOYMENT_TARGET=15.1`) is from the docs Limits; check that it still applies to the Xcode you name.
4. Screenshots for the page: wger in German on iOS and Android, and obytes in Arabic (right to left), from research/real-apps-2026-10-03/, resized, with width, height and alt text. Both are open-source apps; check each licence allows showing its UI, and credit the projects.
5. Do not widen the claim: one Flutter app and one Expo app; bare React Native, other apps, Flutter release builds on Android and Maestro 2.11 were not run (claims C035, C214).

Sources used (read 2026-10-06):
- research/frameworks.md section 15 (the real runs) and https://shotfleet.com/docs#strings, #limits
- https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales (the locale is a device setting, set when the device starts)
- Claims backing shotfleet sentences: C001, C015, C035, C129, C214 (evidence or proven).

---

# Localized App Store and Google Play screenshots for a Flutter or React Native app, from one Maestro flow

If your app is Flutter or React Native, you can take its store screenshots in every language with one Maestro flow, on iOS and Android, without changing the app. You need three things: a way to start the app in each language, text selectors that match in each language, and a wait that's long enough for your framework's first frame.

I make a tool that does this (shotfleet, more below). What follows comes from running it on two real open-source apps on 2026-10-03: wger (Flutter) and the obytes template (Expo with i18next; template commit not recorded), on iOS and Android.

## Does the language reach the app?

Yes, on both platforms, with no code change. On iOS the app is started with `-AppleLanguages`, and it reached Flutter and the Expo app (i18next takes its language from `expo-localization`, and nothing was saved on a fresh install). On Android 13 and newer, the per-app language (`cmd locale set-app-locales`) reached both. Arabic switched the Expo app to right to left on both platforms.

Maestro itself sets the language for the whole device when it starts it (`maestro start-device --device-locale de_DE`), and there's no place inside a flow to set it.

## Do the text selectors match?

This is where it breaks. A flow that says `tapOn: "Log in"` only works in English. In German the button says something else.

shotfleet reads the translations and rewrites each text selector for each language. Flutter and React Native don't keep their translations in a form it can read inside the built app, so you point it at your source files with one line in the config:

```toml
strings = "lib/l10n/*.arb"                  # Flutter
strings = "src/translations/*.json"         # the Expo app I ran (i18next)
```

On both apps, `init` found the build by itself and wrote that line.

Two things I hit:

- **Flutter joins a row into one label.** A row with a title and a detail line is one label with a newline, so `tapOn: "Self-hosted"` finds nothing, even in English. Write `tapOn: "Self-hosted.*"`; shotfleet translates the part before the `.*`.
- **Text the app doesn't translate stays English.** The Expo template's onboarding and login screens are hard-coded English. shotfleet reported those three selectors as untranslated, and the check flagged the two Arabic screenshots that showed English. That was right: the app is English there. Use `id:` selectors (`testID`) for those, as they worked for every input and button I tried.

## Wait for the first frame

A Flutter debug build can take a long time to draw its first frame on a fresh Android emulator. My first screenshot was a white screen with only the status bar. Wait for real text before the first screenshot:

```yaml
- extendedWaitUntil:
    visible: "Log in"
    timeout: 60000
```

shotfleet now flags a blank screenshot and captures that language again once, but the wait in your flow is the real fix.

## Half-translated languages

wger's Japanese was about 30% done, so most of the Japanese screenshots came out in English: Flutter shows the base language for every missing string. shotfleet warns when you ask for such a language by name, and the check reports the screenshots that came out in the base language. That listing isn't usable until the translation is finished.

## The setup, short

```bash
curl -fsSL https://shotfleet.com/install.sh | sh
shotfleet doctor        # what's missing: Maestro, Java, Xcode, Android SDK
shotfleet init          # finds your build, writes the config (with the strings line) and a flow.yaml
                        # edit flow.yaml: your Maestro steps in English, a takeScreenshot for each store image
shotfleet run --locales en,de
```

It needs an Apple silicon Mac, Maestro 2.x and Java 17+, Xcode for iOS and Android API 33+ emulators. `run` is free for up to 2 languages, so you can try this on your own app before paying anything. The details, including the Xcode 27 build line for Expo, are in the [docs](https://shotfleet.com/docs#strings).

## What I didn't run

One Flutter app and one Expo app. Not bare React Native, not other apps, not a Flutter release build on Android. If you try it on yours and something breaks, email me at hello@shotfleet.com.

To check screenshots you already have, from any tool, see [how to check localized screenshots](https://shotfleet.com/guides/check-localized-screenshots).
