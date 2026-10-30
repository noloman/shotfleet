# Screenshot mode: telling your app what to show

shotfleet controls the language, the status bar, permissions and a fresh start. It does not know your app's data. If your screens need demo content (a logged-in user, a few jobs, a filled chart), the app has to provide it when it is launched for screenshots. This is the same pattern fastlane snapshot uses, and it is how real apps do it.

Status: iOS launch arguments are used by real apps today; Android and the other patterns below are described from their source code and Maestro's docs and have **not** been run through shotfleet on a device yet. The `[ios] simctl`, `[android] shell` and `[expect]` settings are tested without a device only.

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

shotfleet can run a `setprop` on every emulator right after it boots: put the command in `[android] shell` in `shotfleet.toml` (for example `shell = ["setprop debug.myapp.screenshot 1"]`, run as `adb -s <serial> shell <command>`; see the README, "Device setup"). The commands are unit-tested as command lines; whether your app sees the property on a real emulator has not been tried. The `[ios] simctl` list does the same for simulators.

## Typed text per language

`inputText: ${name}` plus an `[inputs]` table in `shotfleet.toml` sets typed text per language on iOS. Android runs use the `[inputs]` defaults only. See the README.

## Deep links

`openLink: myapp://debug/seed?...` works in a flow and is not touched by shotfleet's translation of selectors. On iOS, the first deep link opened on a simulator can show a one-time system confirmation, so tap it optionally in the flow.

## Apps that seed demo data relative to now

If your demo data is built around today's date (a calendar, a planner, a habit tracker), screenshots are only consistent on a fixed date. shotfleet has no clock option yet (it is tracked in the repository's issues); you can set the date yourself with `[android] shell` on an emulator that allows root:

- Use a **Google APIs** emulator image. Play Store images do not allow `adb root`, and `adb shell` then runs as the shell user, where `date` fails.
- Turn off automatic time and time zone first, or the clock snaps back.
- `[android] shell` runs `adb shell <command>`, so run `adb root` yourself before the run (for example in a `before_run` hook) and keep the commands in the list to what the shell user may do after that.

A failing `[android] shell` command stops the run (exit 2); for `date` and system settings the message now says that root is the usual reason. The status bar clock shotfleet shows is fixed (9:41): a screen that also shows the app's own "now" will disagree with it until the clock option exists.

## Compose apps: selecting by id in every language

Jetpack Compose apps expose no resource ids to Maestro unless you ask for them, so a flow can only select by visible text. Text selectors are translated per language, but one label can sit on several screens ("Week" as a view tab and as a settings row). To make `id:` selectors work, add this in a debug or benchmark build (not the release you ship):

```kotlin
Modifier.semantics { testTagsAsResourceId = true }   // once, on the root composable
```

and give the elements a `Modifier.testTag("view_week")`. Then `- tapOn: { id: "view_week" }` works in every language. When a text selector fits more than one string in the app, `run` prints a warning per language naming the strings; use an `id:` or `index:` selector for that step. Not run on a device yet.

## What shotfleet will not do for you

It does not change what your backend returns, set the date for you (see above for doing it by hand), log in, or fake in-app purchases or push notifications. If your screens come from a server, point a debug build at a staging account or a local mock server, using a `before_run` hook if you want it automated.

## Checking that the content is really there

`shotfleet check` compares each screenshot's text with your app's strings, and an `[expect.<screenshot>]` table in `shotfleet.toml` lists texts that must (`any`, `all`) or must not (`not`) be on a screen, per language. `run` checks them automatically; `shotfleet check <out> --content shotfleet.toml` checks screenshots you already have. See the README, "Expected content". It proves the texts you list are present, not that the data looks right.
