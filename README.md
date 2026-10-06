# shotfleet

Localized App Store and Google Play screenshots from **one English Maestro flow**: every language your app ships, captured in parallel, checked, and ready for fastlane.

```
$ shotfleet run shotfleet.toml
capturing 18 locales on 4 simulators...
ok   ar       4/4 screenshots
ok   de       4/4 screenshots
...
captured 18/18 locales in 534s on 4 simulators
checked 72 screenshots in 18 languages: 0 problem(s)
```

## Why

Localized screenshots often end up as **the English set copied into every language folder**. That happens because the UI script that drives the app taps English buttons ("Next", "Settings"), so it can't run in German or Japanese without a separate copy per language.

shotfleet reads the translations **compiled into your app** and rewrites the script for each language. "Next" becomes "Weiter", "次へ" or "İleri". Then it runs every language at once and checks the result.

## What it checks

After capture, every screenshot's text is compared against your app's own strings. On iOS, shotfleet reads the text straight from the app while each screenshot is on screen (exact, in every script); on Android it does the same with Maestro 2.7.0 or newer, from the screen hierarchy Maestro saves for a marker step after each screenshot. Otherwise, and for screenshots made by other tools, it uses macOS's built-in text recognition:

- **Wrong language:** the German folder actually shows English or Japanese strings.
- **Copies:** the same image in two languages.
- **Blank:** a screenshot with nothing drawn but the status bar: an app that paints its first frame after the flow's wait passed (Flutter debug builds and Compose do). `run` captures that language again once, then reports it; wait for text on the screen before `takeScreenshot` (see Tips).
- **Missing:** a language that didn't produce every screenshot.
- **Translation collisions, before anything runs:** for example, `tr: 'Next' -> 'İleri' also means 'Advanced'`. A tap could hit the wrong button there, so you anchor that step with `below:`.

- **Store rules:** sizes each store accepts (every App Store display class, Play's 320–3840 px), at most 10 (App Store) or 8 (Play) per listing, no transparency, a 6.9" or 6.5" iPhone set, a 13" iPad set when the app runs on iPad. Notes (not failures) for Play's 2:1 rule and for listings that can't be recommended by Google Play (fewer than 4 screenshots at 1080px+ in exactly 9:16 or 16:9).
- **Languages your app doesn't have:** a store listing (say Traditional Chinese) whose screenshots can't be in that language because the app isn't translated into it.

### Check screenshots you already have (fastlane snapshot, screengrab, by hand)

`run` needs Maestro. `check` doesn't. Already use fastlane snapshot (XCUITest) or screengrab (Espresso)? `check` works on those screenshots, and it's free. Point it at your fastlane folder and your app build:

```bash
shotfleet check fastlane/screenshots                       # snapshot: screenshots/<locale>/
shotfleet check fastlane/metadata/android                  # screengrab: <locale>/images/phoneScreenshots/
shotfleet check fastlane/ --app path/to/MyApp.app          # a fastlane folder with both: the build picks its half
shotfleet check shots/ --locale en --app path/to/MyApp.app # a flat folder of one language's PNGs, no <locale>/ level
```

Without `--app`, `check` looks for your app build the way `init` does, in the folder you run it from: the newest Debug simulator build of your Xcode project, or your Gradle debug APK. It says in one line which build it used, or that it found none and only judges the language by detection.

screengrab puts a timestamp at the end of every file name (`01Home_1773697012807.png`), different in every language. `check` ignores it when it matches screens across languages, and the report keeps the real names. If one language has the same screen twice with two timestamps (say, left over from an earlier run), that's a problem.

A flat folder of PNGs needs `--locale <code>` because shotfleet does not guess the language of a folder; without it `check` says so and exits 2. `<locale>/` folders ignore `--locale`.

You don't need `export` with fastlane: snapshot and screengrab already write into fastlane's folders. `export` is for screenshots from `shotfleet run`.

A lane that stops when the screenshots are wrong (in `fastlane/Fastfile`; fastlane runs `sh` from the `fastlane/` folder, hence the `cd ..`):

```ruby
platform :ios do
  lane :screenshots do
    snapshot
    sh("cd .. && shotfleet check fastlane/screenshots")      # any problem fails the lane, so nothing is uploaded
    deliver(skip_binary_upload: true, skip_metadata: true, overwrite_screenshots: true, force: true)
  end
end

platform :android do
  lane :screenshots do
    screengrab
    sh("cd .. && shotfleet check fastlane/metadata/android")
    supply(skip_upload_apk: true, skip_upload_aab: true, skip_upload_metadata: true, skip_upload_changelogs: true, skip_upload_images: true)
  end
end
```

Paparazzi, Roborazzi or Compose preview tests: their file names don't carry the language unless you put it there (Paparazzi writes `<package>_<Class>_<test>.png`, plus a name you can add), so `check` can't sort one flat folder into languages. Give each language's images their own folder, with the same names in every language, and check the parent folder. If your test names end in the language (`..._home_de.png`):

```bash
for lp in en de ja; do
  mkdir -p shots/$lp
  for f in src/test/snapshots/images/*_$lp.png; do b=$(basename "$f"); cp "$f" "shots/$lp/${b%_$lp.png}.png"; done
done
shotfleet check shots/ --app app/build/outputs/apk/debug/app-debug.apk
```

For one language, `check <folder> --locale de` works on the flat folder as it is, but then there's nothing to compare it with, so copies and missing screens aren't checked. These tools draw your screens without a device, so there's no real status bar. Neither store asks for a device, only for screens that show your app. `check` reads the text, the sizes and the alpha channel, but it can't tell you whether a drawn screen looks like your app on a phone (fonts can differ, mostly in Chinese, Japanese, Arabic and Indic scripts). I haven't tried it on a real Paparazzi folder yet.

Store codes are mapped back to your app's languages (`de-DE` to `de`, `no` to `nb`, `zh-CN` to `zh-Hans`). The report (`check.json` and `index.html`) goes to `./shotfleet-check` (change it with `--report`), and your fastlane folders are never touched. On WOD Tracker's committed fastlane screenshots (252 iOS, 126 Android) it took about 25 seconds per platform. It found one real problem: the Traditional Chinese listings have Chinese captions over an English app. When we planted English screenshots in the German folder and deleted a Japanese one, both were reported.

Screenshots made in other tools work too. `check` knows Apple's sizes for Apple Watch, Mac, Apple TV and Vision Pro (3840x2160 is both Apple TV and Vision Pro), takes at most 10 per size, and flags a language whose Watch screenshots differ in size from the others (Apple wants one Watch size in every language). `export` takes a plain `<locale>/*.png` folder of such a set once `shotfleet check <folder> --report <folder>` has written its `check.json` there, and copies it into `screenshots/<locale>/` next to your iPhone and iPad sets. Size and count rules only: shotfleet captures iPhone, iPad and Android screens, not these.

`shotfleet run` (not `check`) also surfaces real localization bugs: on WOD Tracker the flow could not tap Next on one onboarding page in Japanese, Korean, Chinese and Arabic on small phones.

## Free and paid

`shotfleet check` is free for everyone, and `run` is free for up to 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once per developer, before VAT or sales tax where it applies, with a year of updates and a 14-day refund. Checkout is on Gumroad (see the site's licence page).

`shotfleet activate <key>` stores your key on this Mac. The key from your Gumroad receipt has 3 activations. Activating again on a Mac that still has the key saved counts nothing; after `shotfleet deactivate`, a new macOS install or a new user account, the same Mac counts again. `shotfleet deactivate` removes it from this Mac but does not give the activation back; if you run out, email hello@shotfleet.com and I'll reset the count. Without a valid licence, `run` captures only 2 languages (the first two of your app's languages unless you pick them with `--locales de,ja`) and says so on a line that starts with "free tier:"; the exit code is 0 if those two pass. If `SHOTFLEET_KEY` is set but refused, that line says why. A `SHOTFLEET_KEY` in CI is never refused just because the licence server is down (see "In CI" below). `check`, `doctor` and `init` are always free, and the 2 free languages work on both platforms and every device size.

## Quickstart (build the app once for the simulator first)

```bash
curl -fsSL https://shotfleet.com/install.sh | sh   # signed, notarized; Apple silicon; then open a new Terminal window
shotfleet doctor --fix                             # checks Maestro, Java, Xcode, Android SDK; shows what is missing, asks once, then fetches Maestro and Java
cd path/to/MyApp                                   # your project; build it once for the simulator in Xcode (Debug) first
shotfleet init                                     # in your project folder: uses the newest Debug simulator build and Gradle debug APK it finds
shotfleet init path/to/MyApp.app path/to/app-debug.apk   # or name a simulator build (Debug-iphonesimulator) and/or an APK yourself
```

Notes: Xcode must be the selected one (`xcode-select -p` shows which); the Android block of `doctor` can be ignored by iOS-only apps; the first `doctor` can take a minute while macOS prepares text recognition. After `init`, try `shotfleet run --locales en`, and run `shotfleet activate <your key>` when you want every language (steps below).

Update: run the install line again. It replaces the program and keeps your licence (the key is stored outside the program folder). `shotfleet doctor` tells you when a newer version is out. A year of updates is included.

`shotfleet doctor --fix` fetches what `doctor` found missing and shows you the plan first: Maestro 2.11.0 (a version the real runs passed on, checked against a pinned SHA-256), a Java 21 runtime (checksum from Adoptium) and Google's Android command-line tools with the SDK pieces `doctor` lists (it accepts the Android SDK licences, which the plan says). It asks once, `--yes` skips the question for CI, it stops at the first step that fails, and it never uses `sudo`, edits your shell files or touches Xcode. Maestro and Java go into `~/.shotfleet` (`SHOTFLEET_HOME` changes that); Android tools go where `ANDROID_HOME` (or `ANDROID_SDK_ROOT`) points, else into the SDK shotfleet found or Android Studio's default folder. Behind a proxy that re-signs HTTPS, point `SSL_CERT_FILE` at its CA bundle. Tried on a Linux machine with none of these installed: `doctor` then reported Maestro 2.0.10 and the Android toolchain as ok, and the Java download was run separately against Adoptium's real API (Java 21.0.12 ran). Run on a Mac (Apple silicon, macOS 27, 2026-10-03) in a throwaway home folder, with Maestro 2.0.10 as the pin of that day; not yet run with the 2.11.0 download, and not on a separate clean user account.

Prefer an installer you can double-click? Each release is also published as a signed, notarized package, `https://shotfleet.com/download/shotfleet-macos-arm64.pkg`. It puts the program in `/usr/local/lib/shotfleet` and links `shotfleet` into `/usr/local/bin`; macOS asks for your password. Use it if the `curl` line is not an option or a browser-downloaded copy shows "Apple could not verify ...".

`shotfleet init` without arguments only reads folders, never builds. For iOS it takes the newest `Debug-iphonesimulator` app in Xcode's default DerivedData folder (`~/Library/Developer/Xcode/DerivedData`) whose `info.plist` points at an Xcode project in this folder, up to two folders below it, or above it. For Android it takes the newest debug APK under `build/outputs/apk/debug` in this folder or up to two folders below it (`app/build/outputs/apk/debug`, `<module>/build/outputs/apk/debug`, `android/app/build/outputs/apk/debug`; a flavour folder such as `apk/free/debug` counts too). It prints which build it chose and how old it is. If it finds nothing it exits with the exact `xcodebuild` and `./gradlew assembleDebug` commands to run, then run `shotfleet init` again. If you build somewhere else (a custom DerivedData location), pass the path as above. A build inside the project folder is written to `shotfleet.toml` as a path relative to the config, so the config can be committed and `run` resolves it from the config's folder; a build outside it keeps its place on this Mac and `init` prints a one-line note that the path is only valid there.

1. Edit the generated `flow.yaml`: [Maestro](https://maestro.mobile.dev) steps in English. Navigate by the text users see and add a `takeScreenshot:` for each store image. No `appId` needed: shotfleet uses each build's own id, so one flow serves iOS and Android.
2. Try one language: `shotfleet run --locales en`.
3. When you want every language: `shotfleet activate <your key>` (from your Gumroad receipt email; `check` and 2 languages in `run` work without one).
4. Run them all: `shotfleet run` (finds `./shotfleet.toml`; both platforms if the file has both, `--platform ios` for one).
5. Review `out/index.html` (`out-ios/` and `out-android/` if the config has both platforms). It's a grid with a row per language and a column per screen, and problems are outlined in red.
6. Export to fastlane: `shotfleet export out --fastlane fastlane/` (`out-ios` or `out-android` if the config has both). That writes `deliver`'s `screenshots/<locale>/` or `supply`'s `metadata/android/<locale>/images/phoneScreenshots/`. Languages that failed a check are skipped, so a bad screenshot never reaches a listing.

## Uploading

shotfleet stops at fastlane's folders; fastlane uploads them. Screenshots only, nothing else touched:

```bash
# App Store: replaces the screenshots of every language folder in fastlane/screenshots
fastlane deliver --skip_binary_upload --skip_metadata --overwrite_screenshots --force

# Google Play: uploads metadata/android/<locale>/images/phoneScreenshots
fastlane supply --skip_upload_apk --skip_upload_aab --skip_upload_metadata --skip_upload_changelogs --skip_upload_images
```

Run `shotfleet check fastlane/` right before uploading: export already skips languages that failed, and the check
also catches folders you edited by hand.

## In CI

`run`, `check` and `export` take `--json`: the result goes to stdout as JSON (`exit`, `screenshots`, `problems` and `notes` for `run` and `check`, merged over every device or platform checked, plus `reports` (one `{report, problems}` each) when there are several; `exit`, `exported`, `skipped` for `export`) and progress goes to stderr. Exit codes: `0` all good, `1` problems found, `2` setup error (the message says what to fix), `130` interrupted.

Checking needs only a Mac (it uses macOS text recognition), with no simulators, so it fits a pull-request job on GitHub's macOS runners. `check` is free and needs no licence. (The recipe as written (the build step, then check with --app) has not been run on GitHub yet. The installer, shotfleet --version, doctor and check on sample screenshots did run on GitHub's macos-14 and macos-15 runners (2026-10-05).)

```yaml
# .github/workflows/screenshots.yml
on: pull_request
jobs:
  check-screenshots:
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - run: xcodebuild -scheme MyApp -sdk iphonesimulator -configuration Debug -derivedDataPath build build
      - run: curl -fsSL https://shotfleet.com/install.sh | sh   # Apple silicon runner
      - run: shotfleet check fastlane/ --app build/Build/Products/Debug-iphonesimulator/MyApp.app --json > check.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: screenshot-check
          path: |
            check.json
            shotfleet-check/
```

To use `run` or `export` in CI, set `SHOTFLEET_KEY` to your licence key (keep it in a secret). It's checked online on each run and uses none of your 3 activations. This check fails open on purpose: if the licence server can't be reached, the run counts as licensed, so a CI job never fails because Gumroad is down. A CI key has no offline time limit and nothing is stored for it, so while Gumroad is unreachable it is not re-checked: a refunded or disabled key keeps working until a run reaches Gumroad, and an outage looks the same as a good key. A Mac where you ran `shotfleet activate` is different: it re-checks about weekly and stops after 30 days offline. With an invalid key, `export` refuses and `run` captures only 2 languages. Which two: the first two of your app's languages, unless you pick them with `--locales de,ja`; `run` says so on a line that starts with "free tier:", and if the key is refused that line says why.

With `--json`, progress goes to stderr, including the "free tier:" line, so a CI job that must capture every language should fail when that line appears, or compare the language count in `run.json`.

## Linux and CI

`check` also runs on Linux, in a Docker image with Tesseract inside: `ghcr.io/noloman/shotfleet-check`. It's free, needs no licence, and is built for amd64 and arm64. It holds the compiled program, Tesseract and aapt2 (for `--app app.apk`).

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" ghcr.io/noloman/shotfleet-check check fastlane/metadata/android --app app-release.apk
```

On GitHub there's an Action for it, [noloman/shotfleet-check-action](https://github.com/noloman/shotfleet-check-action), that runs on `ubuntu-latest`. It fails the job when `check` finds a problem (`warn-only: true` turns problems into warnings), and its outputs are the problem count, the report folder and the JSON from `check --json`. I tested it locally with `docker run` and the same inputs GitHub passes; it hasn't run on GitHub's runners yet.

```yaml
- uses: noloman/shotfleet-check-action@v1
  with:
    folder: fastlane/metadata/android
    app: app/build/outputs/apk/release/app-release.apk
```

What doesn't work on Linux:

- `run` and `export`. The image only runs `check`, and it says so in one line if you try the others. Capturing and exporting need a Mac.
- macOS text recognition (Vision). Tesseract reads the screenshots instead, and it can read fewer scripts. The image has Tesseract data for 34 common languages.
- Without `--app` (or `--strings`) the wrong-language check is much weaker on Linux, because Tesseract doesn't say which language it read. Copies, missing screens and store rules are still checked.

On a real 72-screenshot, 18-language Android set, the image with `--app` gave the same verdict as the Mac: 0 problems on the clean set, and all 3 planted faults found (an English screen in `de/`, a copied image, a missing `ja` screen). Without `--app` it found the copy and the missing screen, but not the English screen in `de/`.

## With AI agents

`shotfleet mcp` is an MCP server with `check`, `run` and `doctor` tools. Add it to Claude Code with
`claude mcp add shotfleet -- shotfleet mcp`, or to any MCP client as the command `shotfleet mcp`.

Three agent skills ship with the program (`shotfleet`, `shotfleet-ci`, `shotfleet-review`). Claude Code, Cursor, Codex,
Gemini CLI and GitHub Copilot all load skills from a folder. `shotfleet skill install` copies them into
`~/.claude/skills` (Claude Code and Cursor read it) and `~/.agents/skills` (Codex, Gemini CLI, GitHub Copilot and Cursor
read it). `shotfleet skill install --project` copies them into `./.claude/skills` and `./.agents/skills` instead.

The skills are also in a public repo, so you can install them without shotfleet first. In Claude Code:
`/plugin marketplace add noloman/shotfleet-skills`, then `/plugin install shotfleet@shotfleet` (the skills plus the
MCP server). For other agents: `gh skill install noloman/shotfleet-skills --all --scope user`.

Your licence key: on your Mac, run `shotfleet activate` once yourself. After that your agent uses the CLI and never
sees the key. In CI, use the `SHOTFLEET_KEY` secret. Don't pass the key with `claude mcp add --env`: it ends up in
plain text in `~/.claude.json`.

### What the MCP tools do

- `check` and `doctor` only look. `check` never changes a screenshot; it writes its report to `./shotfleet-check`, or
  to the folder you pass as `report`.
- `run` boots simulators or emulators and replaces the screenshots in the config's output folder. On a big app that can
  take an hour or more, so if your client asks for progress, the server sends it a line every 30 seconds.
- Over MCP, `run` skips the `[hooks]` commands in your config unless you pass `hooks: true`. A config in a repo you just
  cloned can hold any shell command, and here you wouldn't see it the way you see a command in your terminal.
- I keep the answers short: counts, the first 100 problems and notes, and the path to the full `check.json`. Pass
  `full: true` to get the whole report. For 40 languages with 10 screens each, the whole report is about 67,000
  characters, and Claude Code moves anything over 50,000 to a file instead of showing it.
- The server speaks MCP 2025-11-25 and 2025-06-18. It doesn't do the newer 2026-07-28 yet.

## How it works

| | iOS | Android |
|---|---|---|
| Strings | `*.lproj/*.strings` inside the `.app` | `aapt2 dump resources` of the APK, keeping only languages the app itself ships (libraries add ~70 near-empty ones) |
| Language | launch arguments `-AppleLanguages (de)` | per-app locale `cmd locale set-app-locales` (Android 13+) |
| Devices | N simulators, iPhone 17 Pro Max (1320×2868, App Store 6.9") | N read-only emulators at 1080×1920 |
| Status bar | `simctl status_bar` override: 9:41, full battery | SystemUI demo mode: 9:41, full battery, no notifications |
| Parallelism | one sharded Maestro run | rounds of one language per emulator; Maestro's log says which flow ran where |

Every selector is rewritten to match **any** translation of that English label. If "Next" has two keys, German matches `(Nächste|Weiter)`. Selectors that use `id:` pass through untouched.

## Config

The whole config can be this (`shotfleet init` writes it):

```toml
[ios]
app = "path/to/MyApp.app"

[android]                 # optional: the same file and flow serve both platforms
apk = "path/to/app-debug.apk"
```

Everything else is read from the build or has a default; set it only to change it. A typo or a wrong type is refused
with a one-line message before anything runs.

```toml
[ios]
flow = "flow.yaml"        # default; shared by both platforms (an `appId:` header is set for you)
out = "out"               # default "out", or "out-ios" / "out-android" when the file has both platforms
parallel = 4              # simulators (emulators on Android); default 4
capacity = "warn"         # warn (default) prints a note when the Mac is short of memory or swapping; "off" silences it; the run is never changed
stall_s = 900             # seconds without a new screenshot before a hung simulator or flow is stopped and the languages retried (default 900)
locales = ["de", "ja"]    # default: every language the app ships
base_locale = "de"        # the language your flow is written in (default en)
bundle_id = "com.example.myapp"   # default: read from the app (Android: package, read from the APK)
device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"   # default: 6.9" iPhone
runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"                    # default: newest installed
                          # installing an iOS 27 runtime changes what `run` uses: to stay on a runtime you have tested, pin it
                          # (`xcrun simctl list runtimes` shows the ids)
device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]   # several sizes from one flow: out/<device>/;
                          # `check out` and `export out` handle both, and the App Store takes both in one folder

[android]
devices = ["phone", "tablet"]   # phone 1080x1920 and tablet 1440x2560 (both 9:16, so Play can recommend the
                          # listing); out/<device>/, exported to phoneScreenshots / tenInchScreenshots
                          # "tablet-7" adds a 7" tablet, 1080x1920 at 280 dpi, exported to sevenInchScreenshots
```

### Flutter, React Native, .NET MAUI, Unity and translation-platform exports

These frameworks don't keep their translations in a form shotfleet can read inside the built app, so point it at the
source files instead. Add `strings` to either section (globs, relative to the config):

**Run `shotfleet init` in the project folder** and it does the finding for you. It recognises a Flutter project (`pubspec.yaml`), React Native and Expo (`package.json`), Capacitor, .NET MAUI (a `.csproj` with `UseMaui`) and Kotlin Multiplatform. It looks for the build where that framework puts it (`build/ios/iphonesimulator/Runner.app` and `build/app/outputs/flutter-apk/` for Flutter; a Release simulator build and `android/app/build/outputs/apk/release/` for React Native), writes the `strings =` line for the translation files it finds (`arb-dir` from `l10n.yaml`, `src/locales/*/translation.json`, Lingui `messages.po`, `Resources/Strings/*.resx`, `app/i18n/*.ts`), and when there is no build yet it prints the framework's own command (`flutter build ios --simulator --debug`, `npx expo run:ios --configuration Release --no-bundler`) instead of a plain `xcodebuild`. Give it an EAS `.tar.gz` or a `.zip` build and it unpacks it next to the config. It also leaves a commented `[hooks] before_run` line with the framework's build command in `shotfleet.toml`; uncomment it and `shotfleet run` builds the app first. `init` found the build and wrote the `strings` line with no arguments on wger (Flutter) and the obytes template (Expo), iOS and Android, on a Mac (2026-10-03), and `run` then captured them in German and Arabic (details in `research/frameworks.md`).

```toml
strings = "lib/l10n/*.arb"                      # Flutter
strings = "src/locales/*/translation.json"      # React Native / Expo with i18next
strings = ["Resources/Strings/*.resx"]          # .NET MAUI
```

Supported: `.arb`, i18next/react-intl `.json`, translations written as an object in code (`.ts`, `.js`: Ignite, i18n-js, vue-i18n; read as data, never run, and entries that are code are skipped and counted), (nested keys, `_one`/`_other` plurals), `.xcstrings`, `.strings`,
`.stringsdict`, Android/Compose `strings.xml`, XLIFF (`.xlf`, `.xliff`), `.resx`, gettext `.po`, `.properties`, and
CSV with one column per language (Unity Localization, spreadsheets). ICU plurals (`{count, plural, one{…} other{…}}`)
and placeholders (`%d`, `%1$@`, `{name}`, `{{name}}`) are understood. The language comes from `@@locale`, the file name
(`app_de.arb`, `Resources.de.resx`) or the folder (`locales/de/`, `values-de/`). `check` takes the same files:
`shotfleet check fastlane/ --strings 'lib/l10n/*.arb'`.

## Extending shotfleet

Nothing here is on by default: a config without these tables behaves exactly as above. Go further when you want to.

**Hooks** run your own commands (`/bin/sh`, in the config's folder, output on stderr) around a run and an export:

```toml
[hooks]
before_run   = "make build-sim"                 # a string, or a list of commands run in order
after_run    = 'curl -sS -X POST -H "Content-type: application/json" "$SLACK_WEBHOOK_URL" --data "{\"text\":\"shotfleet $SHOTFLEET_PLATFORM: $SHOTFLEET_PROBLEMS problem(s)\"}"'
before_export = "git diff --quiet"              # a non-zero exit stops the export
after_export  = 'fastlane deliver --skip_binary_upload --skip_metadata --overwrite_screenshots --screenshots_path "$SHOTFLEET_FASTLANE/screenshots"'
# hook_timeout_s = 1800                         # default 600 per command
```

A failing `before_*` hook stops the command (exit 2); a failing `after_*` hook makes the exit code 1, so CI notices.
Variables on every event: `SHOTFLEET_EVENT`, `_VERSION`, `_CONFIG`, `_PLATFORM`, `_OUT`; `before_run` and `after_run` also get
`_BUNDLE_ID` and `_LOCALES` (empty unless restricted); `after_run` gets `_EXIT`, `_PROBLEMS`, `_REPORT` (`<out>/check.json`); the export hooks get `_FASTLANE`, `_REPORT`
(and `_EXIT` after the export). `--no-hooks` skips them for a dry run.

**Overrides** replace what shotfleet would tap for one language, which is the fix for a collision warning (`'Next' ->
'İleri' also means 'Advanced'`) and for labels that aren't in your app's strings:

```toml
[overrides.tr]                         # the language as shotfleet names it: tr, pt-BR, zh-Hans...
"Next" = "İleri"                       # literal text
"Advanced" = "re:Gelişmiş.*"           # "re:" = a regular expression
"Search" = "Ara"
```

**Inputs** set the text a flow types, per language. Write `inputText: ${name}` in the flow and give the values in the config:

```toml
[inputs]                               # typed in every language that has no value of its own
name = "Alex"
[inputs.ja]                            # the language as shotfleet names it; pt covers pt-BR too
name = "田中"
```

The value goes into that language's flow as a Maestro `env:` entry. This works on iOS. Maestro hands any flow to any
emulator, so on Android a name that has a per-language value is read from a small script (`shotfleet_vars.js`) that picks
the emulator's row by `MAESTRO_DEVICE_UDID`. Maestro 2.11.0 sets that variable to the emulator's serial: German and Japanese values showed up as typed in screenshots (device run 2026-10-04, one emulator, one language after the other; two emulators at once and Arabic not run). Maestro 2.0.10 doesn't define it, so on 2.0.10 Android runs type the `[inputs]` defaults only. Check the first screenshots in a script like Japanese or Arabic.

**Device setup** runs your own commands once per simulator or emulator, right after it boots (iOS: after the status bar is set), so an app with a screenshot switch, dark mode, a location or a granted permission looks the way you want:

```toml
[ios]
simctl = ["ui $UDID appearance dark", "location $UDID set 52.3676,4.9041"]   # xcrun simctl <args>; $UDID is the simulator's id
[android]
shell = ["setprop debug.myapp.demo 1", "settings put system font_scale 1.0"]  # adb -s <serial> shell <command>
```

A command that fails stops the run before anything is captured (exit 2) and prints the command. iOS commands apply to every language (a different command per language is not possible: one Maestro process serves all simulators). The Android commands are unit-tested as command lines; whether a given `setprop` or `settings` command takes effect on your emulator image has not been tried on a real one.

**Expected content** checks that what you seeded is really on screen, per language. Name the screenshot as in the flow (`takeScreenshot: 01_home`):

```toml
[expect.01_home]
any = ["Senior iOS Engineer"]          # at least one of these is on screen
[expect.01_home.de]                    # only for the German screenshot (pt covers pt-BR)
all = ["Steinmännchen"]                # every one of these is on screen
[expect.03_log]
not = ["No workouts yet", "Keine Workouts"]   # the empty state must not show
```

`run` checks these automatically; for screenshots you already have, use `shotfleet check out/ --content shotfleet.toml` (free, no licence). A missing or forbidden text is a problem line (`de/01_home.png: expected "Steinmännchen" on screen`), and a table for a screenshot that doesn't exist is reported too. Case, accents and spacing are ignored. On iOS the text is the app's own, so a match is exact in any script. On Android it is read from the picture: a text in a script macOS cannot read (Greek, Hebrew, most Indic) is reported as a note, `could not verify`, never as a pass; `--ocr-command` helps there. This proves the strings you list are present, not that the data looks right.

**Plugins**: `shotfleet foo` runs `shotfleet-foo` from your PATH (like `git` and `gh`), when `foo` isn't a built-in command.

**Anything else**: `run`, `check` and `export` take `--json` and use stable exit codes (0 ok, 1 problems, 2 setup error), so
they script like any other tool; `SHOTFLEET_OCR` / `--ocr-command` swaps the text reader; `strings = "glob"` swaps the
translation source.

## Tips

- **Dialogs that appear late** (disclaimers, consent screens): dismiss them in a loop until your first real screen is visible, not with a fixed wait:
  ```yaml
  - repeat:
      while:
        notVisible: "Welcome"
      times: 15
      commands:
        - tapOn: { text: "Accept", optional: true }
  ```
- **Longer languages push buttons off-screen:** add `scrollUntilVisible` before tapping them.
- **Permission prompts** ("Allow While Using App", "Don’t Allow") are drawn by iOS and Android in the device language, which stays English even while your app runs in German. Write those taps in English; shotfleet keeps the English text matchable. Better still, skip the prompts: on iOS start the flow with
  ```yaml
  - launchApp:
      permissions:
        all: allow
  ```
  (shotfleet adds its language arguments to your options). On Android shotfleet installs with every permission granted.
- **A first screenshot that comes out blank** (Flutter debug builds and Compose put their text in the accessibility tree before they paint): start with `extendedWaitUntil: {visible: "<a text on that screen>", timeout: 60000}`, and if it still happens add a short pause (`extendedWaitUntil: {notVisible: {id: "none"}, timeout: 3000}`). A Flutter debug build can take 30 s to draw on a fresh emulator.
- **Flutter rows and cards are one label:** Flutter joins a row's title and detail line into one label with a newline (`Self-hosted\nConnect to your own instance`), so tap it as `"Self-hosted.*"`; shotfleet translates the part before the `.*` (`.*Register` works too). A line like `New to wger? Register` is one label as well.
- **A language the app only half translates** (wger's Japanese is 30%): the app shows its base language for every missing string. `run` warns when you ask for such a language by name, and `check` reports the screenshots that came out in the base language.
- **Building the app on Xcode 27** (found on wger, the obytes template and kotlinconf-app, 2026-10-03; not shotfleet's doing, but it stops you before the first screenshot): `npx expo run:ios` ends with "Can't determine id of Simulator app" because Xcode 27 has no Simulator.app, so build the generated project yourself, `xcodebuild -workspace ios/<App>.xcworkspace -scheme <App> -configuration Release -sdk iphonesimulator -derivedDataPath ios/build build IPHONEOS_DEPLOYMENT_TARGET=15.1` (Xcode 27 refuses the old deployment targets of some pods), and `init` finds it in `ios/build`. A Kotlin Multiplatform app needs `ARCHS=arm64` on its `xcodebuild` ("Architecture Not Configured in Gradle: ios_x64"; `init` prints it). It also fails with "cannot find X in scope" unless both `:shared:assembleSharedDebugXCFramework` and `:shared:assembleSharedReleaseXCFramework` were built first (a stale release slice gives the same error); `init` says so next to the `xcodebuild` line.
- **Typing a password on iOS in Arabic:** `inputText` into a secure (password) field drops Latin letters when the app runs in Arabic (seen on the Expo app, iOS 26.4: `abcdef` typed nothing, `abc123` typed only `123`, `123456` typed all six); name and e-mail fields are fine. Use digits for a demo password.
- **Free memory before a run:** idle Gradle daemons can hold gigabytes. Run `./gradlew --stop` (once per Gradle version you use) before `shotfleet run`, and close apps you do not need. Four simulators on a loaded Mac can take many times longer.
- **Fresh state:** each language starts from a clean install. On iOS that's `clearState`; on Android shotfleet clears the app data itself, because `clearState` would also erase the app language.

## Limits

- The installed program brings its own Python. Running from source needs Python 3.11+ (macOS's own `python3` is 3.9; `brew install python`).
- Strings are read from the build: `.strings`, `.stringsdict` and String Catalogs on iOS (including those in frameworks, Swift packages and a Watch app), `strings.xml` and `<plurals>` on Android, and Compose Multiplatform resources on both (run end to end on JetBrains' KotlinConf app, iOS and Android, de and en, 2026-10-03). Other frameworks read source files (see Config). Labels with numbers ("Round 2 of 12") are matched and translated with the same numbers, in every plural form.
- Flutter and React Native work from your translation files (run end to end on a real Flutter app, wger, and a real Expo app, the obytes template, on iOS and Android, 2026-10-03; other apps and bare React Native not yet run).
- If you pass `init`, `run` or `check` a Flutter, React Native, .NET MAUI or Unity build, shotfleet tells you what to add: a `hint:` on stderr with the `strings =` line for your translation files, and a warning for a Flutter debug build (DEBUG banner) or a React Native Debug build (Metro dev server). It detects these builds from file names in the bundle, so it may miss some versions, and it never stops a run.
- Text recognition is macOS's. It reads 33 languages (the macOS 27 number; older macOS versions read fewer), including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. A language outside that list but written in Latin script (Catalan, Croatian, Hungarian, Slovak, Slovenian) is judged by language detection on every macOS, like a listed one; macOS reads it with its Latin model, and accents can be lost (Hungarian). Older macOS versions list fewer languages, so on those more of your languages fall under this rule (not tested on macOS 13). For scripts it can't read (Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts), `check` still catches screens in another language, copies and missing screens, and says which screens it couldn't read.
- If macOS text recognition stops answering (the first time, macOS compiles its text model in `ANECompilerService`, which can take minutes on a loaded Mac), `check` waits while that compile is working, up to 6 minutes. If it still gets no answer it says what happened and switches to Tesseract when it's installed (`brew install tesseract tesseract-lang`), saying so in its output; otherwise it tells you to wait for the first compile and re-run, close heavy apps, or install Tesseract. A restart is a last resort. iOS runs mostly aren't affected: they read the app's own text, and only screens where that text proves little go to OCR.
- With Tesseract installed (`brew install tesseract tesseract-lang`), `check` uses it automatically for those scripts: measured on 85 languages, 84 are then verified by reading instead of 66. Another OCR works too: `--ocr-command "<cmd> {image}"` (or `SHOTFLEET_OCR`); placeholders: `{image}`, `{lang}` (ISO code), `{tesseract}` (Tesseract's code), `{tesseract_with_english}` (e.g. `eng+ell`).
- `check` without `--app` relies on language detection, which can't judge short screens; pass `--app` for the full check. With `--app`, a screen with only one or two of the app's strings is also judged by language detection.

- Built for macOS 13 or later on Apple silicon. My full runs, with simulators and emulators, were all on macOS 27. On macOS 14 and 15 I ran the installer, doctor and check for version 0.1.1, and on macOS 26.2 in a virtual machine for 0.1.2. Other macOS versions are not tested yet.
- Tested with Xcode 27.0. The default simulator is the iPhone 17 Pro Max, which needs Xcode 26 or newer; with an older Xcode set `device_type` in the config. Xcode 26.x has not been run.
- iOS 27: one simulator and one language ran with 0 problems (2026-10-05). A run on four simulators at once has not been tried on iOS 27; pin an older runtime if you need a tested setup.
- macOS on Apple silicon only (the installer refuses Intel Macs). Needs Xcode for iOS, the Android SDK for Android, Maestro (tested with 2.0.10 and 2.11.0) and Java 17+ (Maestro needs it). `shotfleet doctor` and `run` say so when yours is another version; other 2.x versions may still work. `shotfleet doctor --fix` installs 2.11.0.
- Android needs API 33+ emulators for per-app languages. shotfleet finds the SDK in `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `~/Library/Android/sdk`, Homebrew's `android-commandlinetools`, or next to an `adb` on your PATH, and uses any installed arm64 `google_apis` or `google_apis_playstore` image of API 33 or newer (or the `system_image` from the config). `shotfleet doctor` prints the `sdkmanager` commands for whatever is missing. The first Android run creates its own emulator, `shotfleet_android`, from that image; your other emulators are not touched.
- Linux: `check` and the Android readers run from source on Linux (see [docs/linux.md](docs/linux.md)): they need Tesseract, there is no Linux installer yet, and `run` on a Linux emulator has not been tried. iOS needs a Mac. For `check` there is also a Docker image (see Linux and CI).
- Text you type isn't translated by itself: it stays the same in every language unless you set `[inputs]` (iOS; on Android it needs a Maestro that sets `MAESTRO_DEVICE_UDID`, which 2.11.0 does and 2.0.10 doesn't; see above).
