# Changelog

## Unreleased
- **Maestro 2.11.0 works and is tested:** it only lets `takeScreenshot` write inside its own artifact folder, so the first real run (2026-10-03) captured nothing. Flows now name screenshots relative to Maestro's working directory and shotfleet moves them into `raw/<locale>/` afterwards (both Maestro layouts; the live screen-text capture watches Maestro 2.11's folder too). Fixture e2e on a Mac: 2.11.0 iOS 36/36 and Android 29/29, 2.0.10 iOS 36/36 and Android 29/29. `MAESTRO_TESTED` is now `("2.0.10", "2.11.0")`, `doctor --fix` installs 2.11.0, and the "run refuses Maestro 2.11 and newer" stopgap is removed. Details and the load during the runs: `research/maestro-2-11.md`.
- **Polar and Lemon Squeezy code removed:** shotfleet is sold through Gumroad only. The Polar licence path (`polar_post`, `polar_valid`, `is_polar_key`, the `polar` store in the saved licence) and the Lemon Squeezy one (`licence_api`, `ls_ours`, the `SHOTFLEET_LICENCE_API` setting) and their tests are gone; no Polar key was ever sold and no Lemon Squeezy key unlocked anything (no product id was set), so nothing that exists stops working. `shotfleet activate` now refuses a key that is not a Gumroad key (four groups of 8) without any network call; a saved licence from an older store is refused with a message to activate the Gumroad key, and `shotfleet deactivate` removes it. Gumroad keys are unchanged.
- **Site:** the round-2 critique and the SEO audit worked through (statuses in `research/site-critique-2.md` and `research/seo-audit.md`): dark-theme pennant and check-mark contrast, 44 px footer, docs and zoom targets, scroll cues on the comparison table, print, no `unsafe-inline` in the style CSP, favicon.ico and apple-touch-icon, sitemap `lastmod`, "not on sale yet" notes that `go-live.sh` removes, and `tests/test_site_audit.py`.
- **Site claims proven in tests:** `tests/test_claims_site.py`, `tests/browser_site.cjs` (Chromium, `/api` stubbed) and more checks in `site/worker.test.mjs` now cover the prices, Apple silicon and Java prerequisites, internal links, what the worker stores and refuses, the 404 page and the signup, contact and counter scripts (claims C002, C033, C042, C077 to C084, C087, C088, C101, C104). The privacy page now says contact messages keep your country and that a removal can take a minute to reach every Cloudflare location.
- **E1 result, run 6:** one emulator fails like two (Maestro cannot find the localized Next button on the Linux runner), so two emulators on 2 vCPUs is not the cause; recorded in `docs/linux.md`, `STATUS.md` and `docs/agent-tasks/05`.
- **Android emulators that fail to start now explain themselves:** each emulator's output is kept in `<tmp>/shotfleet-emulator-logs/`; shotfleet stops at once, with the exit code and the log tail, when the emulator process exits (before, a dead emulator looked like a 600 s hang: "emulators did not boot in time"); a real timeout shows the log tails and the likely cause (no usable `/dev/kvm` on Linux, else memory and CPU); and a full disk is named with its fix (the emulator wants 12 GB free). Found by experiment E1 on a GitHub runner.
- **`doctor --fix` and Google's new Android CLI:** Google's newest command-line tools turned `sdkmanager` into a shim for their Android CLI. Two consequences are handled. It refuses to unpack into an SDK folder whose path contains `..` ("Illegal entry path escaping destination directory"), so every SDK path is now normalised (found on a GitHub runner, where the workspace path has `..`). And it reports usage data to Google unless told `--no-metrics`, which `sdkmanager` itself rejects, so package installs now go through `android --no-metrics --sdk=ROOT sdk install` when that program is present, and through plain `sdkmanager` otherwise.
- **Agent tasks:** `docs/agent-tasks/` holds seven self-contained prompts for what needs a Mac or a KVM Linux machine, and why each is open. `tools/watch-upstream.sh` runs the Maestro and Apple-size watchers locally.
- **Apple size watch:** `tools/apple-specs-watch.py` compares every screenshot size on Apple's specification page with the table `check` uses. First run found four landscape sizes of old devices (960x600, 1136x600 for the 3.5" and 4" iPhones, 2048x1496 and 1024x748 for the 9.7" iPad) that `check` would have called wrong; they are now accepted.
- **Tests:** `tests/test_claims_unit.py` proves five more claims in the register (free-tier cap and licence reach both platform runs, the Gumroad and Polar licence answers, hook variables and exit codes, a translated caption over an English UI) and adds init checks for every framework and archive kind; no change to `shotfleet.py`.
- **`check` knows the iPhone Duo screenshot sizes** (outer 1398x2034, inner 2007x2853; Apple opens uploads later this year). A Duo-only set still needs a 6.9" or 6.5" iPhone set.
- **Maestro watch:** `tools/latest-maestro.py` fetches the newest stable Maestro release and checks it against what shotfleet relies on, failing if something is gone; a compatible newer version is reported as "needs a real run", never as tested. `tools/watch-upstream.sh` runs this and the Apple size check together on your machine; the two GitHub workflows for them are manual-only (this repo runs its checks locally).
- **Compatibility:** `tools/maestro-compat.py` checks any Maestro against what shotfleet relies on, without a device (2.0.10 and the newest, 2.11.0, both pass); tar extraction passes an explicit filter (Python 3.12 deprecates the default, 3.14 changes it); the Linux CI job also runs Python 3.13 with deprecation warnings as errors.
- **`doctor --fix`:** downloads what `doctor` found missing after one question (`--yes` skips it): Maestro 2.0.10 pinned by SHA-256,
  a Java 21 runtime (checksum from Adoptium) and Google's Android command-line tools plus the SDK pieces. Never `sudo`, no shell
  files or PATH edits, no Xcode; `SSL_CERT_FILE` is honoured for proxies. Maestro from `~/.shotfleet` is used before the one on the PATH.
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
