# Screenshot mode: telling your app what to show

shotfleet controls the language, the status bar, permissions and a fresh start. It does not know your app's data. If your screens need demo content (a logged-in user, a few jobs, a filled chart), the app has to provide it when it is launched for screenshots. This is the same pattern fastlane snapshot uses, and it is how real apps do it.

Status: iOS launch arguments are used by real apps today; Android and the other patterns below are described from their source code and Maestro's docs and have **not** been run through shotfleet on a device yet.

## The contract, in five rules

1. **A debug-only switch.** The app reads a flag such as `SCREENSHOT_MODE` at start and is compiled out of release builds (`#if DEBUG`, `BuildConfig.DEBUG`, or a no-op class in the release source set). shotfleet already needs a Debug simulator build or a debug APK, so this fits.
2. **Seed from inside the app.** When the flag is on, the app creates its own demo data. Nothing is pushed in from outside.
3. **Localize the demo data from the language the app is launched in.** shotfleet launches each language with `AppleLanguages` (iOS) or the per-app locale (Android). Read it (`Locale.preferredLanguages` on iOS) and pick translated demo content, so a German screenshot shows German content.
4. **Seed relative to now.** Dates such as "2 days ago" stay correct whenever you run it.
5. **Optional scene argument.** `SCREENSHOT_SCENE=<name>` lets one launch go straight to one screen.

Seeding is real work: one of the apps this was studied on has about 950 lines of demo code on Android. Do not expect to add it in ten minutes.

## iOS: launch arguments from the flow

```yaml
appId: com.example.myapp
---
- launchApp:
    clearState: true
    arguments:
      SCREENSHOT_MODE: "1"
      SCREENSHOT_SCENE: "home"
- takeScreenshot: 01_home
```

shotfleet adds the language arguments (`AppleLanguages`, `AppleLocale`) to the same `launchApp`, and keeps yours.

Two things that catch people out:

- **Write values as strings.** From Maestro's source, a YAML boolean (`SCREENSHOT_MODE: true`) is passed as the bare word `SCREENSHOT_MODE true`, while a string value gets a leading dash (`-SCREENSHOT_MODE 1`). Apps that read `ProcessInfo.processInfo.arguments.contains("-SCREENSHOT_MODE")` need the dash, so use `"1"`. (Checked against Maestro's source on its main branch, not yet against the version shotfleet tests with.)
- **Maestro cannot set launch environment variables.** If your app reads `ProcessInfo.processInfo.environment["MY_DEMO_SEED"]`, also accept it as an argument (`-MY_DEMO_SEED 1`). One line in the app, and it then works under every tool.

In Swift:

```swift
#if DEBUG
let args = ProcessInfo.processInfo.arguments
let screenshotMode = args.contains("-SCREENSHOT_MODE")
let language = Locale.preferredLanguages.first ?? "en"   // pick localized demo data from this
#endif
```

## Android

Maestro's `arguments:` arrive as **intent extras** on Android. If your demo mode must start before any Activity exists (for example dependency injection in `Application.onCreate`), an extra is too late. Two patterns apps use:

- Read the flag from an intent extra in the launcher Activity, when your setup allows it.
- Read a system property set before the launch, for example `adb shell setprop debug.myapp.screenshot 1` (read it by reflection in debug builds).

shotfleet cannot run a per-device `setprop` today. A setup command per emulator is planned (see `research/content-control.md`, feature F2). Until then, Android apps that need a property can only use the intent-extra route.

## Typed text per language

`inputText: ${name}` plus an `[inputs]` table in `shotfleet.toml` sets typed text per language on iOS. Android runs use the `[inputs]` defaults only. See the README.

## Deep links

`openLink: myapp://debug/seed?...` works in a flow and is not touched by shotfleet's translation of selectors. On iOS, the first deep link opened on a simulator can show a one-time system confirmation, so tap it optionally in the flow.

## What shotfleet will not do for you

It does not change what your backend returns, set the date, log in, or fake in-app purchases or push notifications. If your screens come from a server, point a debug build at a staging account or a local mock server, using a `before_run` hook if you want it automated.

## Checking that the content is really there

`shotfleet check` already compares each screenshot's text with your app's strings. A way to list strings that must appear in every language (an `[expect]` table) is planned and is not available yet.
