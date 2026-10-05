---
name: shotfleet-ci
description: Add shotfleet check to CI so a pull request fails when localized App Store or Google Play screenshots are in the wrong language, copied, missing or out of store spec. Use when the user wants to run shotfleet in GitHub Actions or another CI, gate a pull request on screenshots, parse shotfleet --json output, or use SHOTFLEET_KEY. Uses only what the shotfleet docs say.
---

# shotfleet in CI

`shotfleet check` needs only a Mac runner (macOS text recognition) and no simulators. It is free and needs no
licence. It takes `--json`: stdout is only JSON, progress goes to stderr.

## Exit codes

| Code | Meaning | CI result |
|---|---|---|
| 0 | all good | pass |
| 1 | problems found | fail, show `problems` |
| 2 | setup error, stderr says what to fix | fail, show stderr |
| 130 | interrupted | fail |

## Steps

1. Find the fastlane folder in the repo (`screenshots/<locale>/` for iOS, `metadata/android/<locale>/images/phoneScreenshots/` for Android) and the build to check against: a simulator `.app` (`Debug-iphonesimulator`) or a debug `.apk`. Flutter, React Native, MAUI, Unity: use `--strings '<glob>'` on the translation files instead of `--app`.
2. Add `.github/workflows/screenshots.yml`. This is the recipe from the docs (https://shotfleet.com/docs), adapt `MyApp` and the paths:

```yaml
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

3. Tell the user what you changed and that the docs say this recipe has not been run on GitHub yet; the `check` command itself is tested. Do not claim the workflow passes until it has run.
4. Other CI systems: build the app, install shotfleet on a macOS Apple silicon agent, run the same `shotfleet check` line, keep `check.json` and `shotfleet-check/` as artifacts.

## `run` and `export` in CI

Need the licence: set `SHOTFLEET_KEY` from the CI secret store (GitHub: `env: SHOTFLEET_KEY: ${{ secrets.SHOTFLEET_KEY }}`).
It is checked online each run and uses none of the 3 activations. It fails open on purpose: with the licence server unreachable the run counts as licensed, with no offline time limit for a CI key (so a refunded key keeps working until a run reaches Gumroad); an activated Mac still stops after 30 days offline.
With an invalid key `export` refuses and `run` captures only 2 languages. The docs give no CI recipe for `run`
(it needs simulators and Maestro on the runner); do not invent one.

## Reading `check.json`

`exit`, `screenshots`, `problems` (list of `<locale>/<file>: <what>` lines), `notes` (informational). Print `problems` in
the job summary; a count of issues is the number of root causes, not lines (see the `shotfleet-review` skill).

## Do not

- Do not put the licence key in the workflow, the repo, a log or an artifact.
- Do not let CI upload to the stores or edit the fastlane folder; `check` never touches it.
- Do not use an Intel runner; the installer refuses Intel Macs.
- Do not claim more than the docs do: details in the `shotfleet` skill, `references/ci.md`.
