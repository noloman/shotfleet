# Changelog

## Unreleased
- **Frameworks:** `init` in a Flutter, React Native, Expo, Capacitor, .NET MAUI or Kotlin Multiplatform project folder finds
  the build where that framework puts it, writes the `strings` line for the translation files it finds and prints the
  framework's own build commands; EAS `.tar.gz` and `.zip` builds are unpacked by `init`. Translations written as objects
  in code (`.ts`, `.js`) and Android `<string-array>` are read.
- **Build hook:** `init` in a framework project leaves a commented `[hooks] before_run` with that framework's build command.
- **Flows:** `launchApp` options may be written on one line, `- launchApp: { permissions: { all: allow } }`.
- **Linux:** `check` reads screenshots with Tesseract where macOS text recognition does not exist (and Tesseract now gets one
  thread per process: four screenshots took 73 s, now 0.5 s), `doctor` reports Tesseract and KVM, the Android SDK and image
  logic knows Linux folders and the host CPU's architecture, and `.strings`, `.stringsdict` and `Info.plist` are read in
  Python when `plutil` and `PlistBuddy` are absent. Android `run` on a Linux emulator is coded but untried.
- **Store:** sales and licences go through Gumroad (Polar was dropped: its payout provider asks a Dutch resident for a KvK). A Gumroad key has 3 activations; refusing a key never uses one, activating again on the same Mac counts nothing, and refunded, charged-back or disputed purchases stop working at the next weekly check (a won dispute keeps working). `deactivate` cannot give an activation back, so moving to a fourth Mac means an email. Polar and Lemon Squeezy keys still work.
- **Simpler setup:** only the build is required in `shotfleet.toml`; bundle id, package and flow are read or defaulted.
  One config and one flow serve iOS and Android (an `appId:` header is set per build), `shotfleet run` needs no
  arguments, `init` takes several builds, and a typo or wrong type in the config is refused with a one-line message.
- **Licence:** Polar added as a store (keys start with `SHOTFLEET-`), alongside Lemon Squeezy and Gumroad. `run` without a
  licence captures up to 2 languages; `export` and all languages need a key.
- **Extending:** `[hooks]` (before/after run and export), `[overrides.<locale>]` for what to tap in one language,
  `shotfleet-<name>` plugins on the PATH, `--no-hooks`.
- **Setup help:** `doctor` finds Homebrew's keg-only Java and passes `JAVA_HOME` to Maestro, checks Java 17+, and says what
  to do next; `check` handles a fastlane folder holding both stores when given `--app`.
- **Readers:** a locale folder beats a short namespace file name (`locales/en/app.json`), i18next namespaces that share a
  key both survive, gettext `.po` files use their `Language:` header and plural forms, an empty accessibility tree falls
  back to OCR, and partly translated languages are reported instead of skipped silently.
- **Site:** redesigned; signup asks what you build with.

## 0.1.0
First release: `run` (one English Maestro flow, every language, parallel simulators/emulators), `check` (any
screenshots: language, copies, missing screens, store rules; free), `export` (fastlane deliver/supply folders),
`init`, `doctor`, `mcp`. Reads String Catalogs, .strings/.stringsdict, Android resources, Compose Multiplatform,
and Flutter/React Native/.NET/Unity translation files.
