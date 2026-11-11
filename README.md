# shotfleet

**Localized App Store and Google Play screenshots from one English Maestro flow.** Every language your app ships, captured in parallel, checked, and ready for fastlane. Free and open source.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ea4aaa.svg)](https://github.com/sponsors/noloman)

```
$ shotfleet run shotfleet.toml
capturing 18 locales on 4 simulators...
ok   ar       4/4 screenshots
ok   de       4/4 screenshots
...
captured 18/18 locales in 534s on 4 simulators
checked 72 screenshots in 18 languages: 0 problem(s)
```

## The problem

Localized screenshots often end up as the English set copied into every language folder. The UI script taps English buttons ("Next", "Settings"), so it can't run in German or Japanese without a separate copy per language, and nobody maintains 20 copies.

shotfleet reads the translations **compiled into your app** and rewrites your script for each language: "Next" becomes "Weiter", "次へ" or "İleri". Then it runs every language at once and **checks the result**, so a wrong-language, copied, blank or missing screenshot never reaches a store listing.

## What you get

- **One flow, every language.** Write the Maestro steps once in English; shotfleet translates the taps from your app's own strings.
- **iOS and Android** from the same file, in parallel on simulators and emulators.
- **A check that catches real mistakes:** screenshots in the wrong language, copies across languages, blank frames, missing screens, ambiguous translations before anything runs, and the size and count rules of both stores.
- **A review page** (`out/index.html`): a grid with a row per language and a column per screen, problems outlined in red.
- **fastlane export:** `shotfleet export` writes the folders `deliver` and `supply` expect, and skips any language that failed a check.
- **Works with** native iOS and Android, Compose Multiplatform, Flutter, React Native, .NET MAUI and Unity (from your translation files), and with screenshots you already have (`shotfleet check` on a fastlane folder).
- **Made for AI agents too:** an MCP server (`shotfleet mcp`) and agent skills for Claude Code, Cursor, Codex, Gemini CLI and GitHub Copilot.
- **Signed, notarized, no account, no key, no telemetry service to sign in to.** Everything runs on your Mac.

## Get started

```bash
curl -fsSL https://shotfleet.com/install.sh | sh   # Apple silicon Macs; or: brew install noloman/tap/shotfleet
shotfleet doctor --fix                             # checks Maestro, Java, Xcode, the Android SDK; fetches what is missing
cd path/to/MyApp                                   # build the app once for the simulator or as a debug APK first
shotfleet init                                     # writes shotfleet.toml and a starter flow.yaml
shotfleet run --locales en                         # try one language, then: shotfleet run
```

Then edit `flow.yaml` (plain Maestro steps in English, a `takeScreenshot:` per store image), review `out/index.html`, and export with `shotfleet export out --fastlane fastlane/`. The [guide](docs/guide.md) has the details: install options, config, CI, tips for tricky screens and the honest list of limits.

## Support shotfleet

shotfleet is built and maintained by one person and costs nothing to use. If it saves you or your team the tedious hours of hand-capturing screenshots in every language, please consider sponsoring it.

**[Sponsor on GitHub](https://github.com/sponsors/noloman)**

Sponsorship pays for the time that keeps it useful:

- keeping it working as Xcode, Android, Maestro and the store rules change,
- support for more frameworks and device types,
- testing on real simulators and emulators, which takes machine time,
- answering issues quickly.

Not ready to sponsor? Starring the repo, telling a teammate and filing a good bug report all help just as much.

## Documentation

- [Guide](docs/guide.md): everything in detail, including what `check` looks at, config, CI and limits
- [Linux and CI](docs/linux.md)
- [shotfleet.com](https://shotfleet.com): docs, guides and what's new
- [Agent skills](https://github.com/noloman/shotfleet-skills)

## Contributing

Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and ideas go in [GitHub issues](https://github.com/noloman/shotfleet/issues).

## License

[MIT](LICENSE). Copyright (c) 2026 Manuel Lorenzo Parejo.
