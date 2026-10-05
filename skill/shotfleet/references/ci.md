# shotfleet in CI

`run`, `check` and `export` take `--json`: the result goes to stdout as JSON and progress goes to stderr. Exit
codes: `0` all good, `1` problems found, `2` setup error (the message says what to fix), `130` interrupted.

JSON shapes: `check` and `run` give `exit`, `screenshots`, `problems` (and `notes`); `export` gives `exit`,
`exported`, `skipped`. With exit 2 the JSON holds only `exit`; the reason is on stderr.

## The pull-request check

Checking needs only a Mac (it uses macOS text recognition) and no simulators, so it fits a pull-request job on
GitHub's macOS runners. `check` is free and needs no licence. The recipe as written (the build step, then check with --app) has not been run on GitHub yet. The installer, shotfleet --version, doctor and check on sample screenshots did run on GitHub's macos-14 and macos-15 runners (2026-10-05).

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

Adapt `MyApp` (scheme and `.app`) and the `fastlane/` path. For Android screenshots, pass a debug APK as `--app`.
For Flutter and React Native replace `--app ...` with `--strings '<glob>'`.

Notes:
- The job fails when `shotfleet check` exits 1 or 2; the artifact step runs anyway (`if: always()`).
- The report goes to `./shotfleet-check`; change it with `--report`.
- Use the runner's Apple silicon image; the installer refuses Intel Macs.
- Other CI systems: the same three steps (build, install, `shotfleet check ... --json`), on a macOS agent.

## run and export in CI

Set `SHOTFLEET_KEY` to the licence key, kept in the CI system's secret store (GitHub: repository secret, exposed as an
env var of the step). It is checked online on each run and uses none of the 3 activations. The check fails open on purpose: if the licence
server can't be reached (no network, a Gumroad 5xx, an unreadable answer), the run counts as licensed, so a CI job never fails
because Gumroad is down. A CI key has no offline time limit and nothing is stored for it, so while Gumroad is unreachable it is
not re-checked: a refunded or disabled key keeps working until a run reaches Gumroad, and an outage looks the same as a good
key. A key that is not four groups of 8 hex characters is refused without contacting Gumroad. A Mac where `shotfleet activate`
was run is different: it re-checks about weekly and stops after 30 days offline. With an invalid key `export` refuses (exit 2) and `run` captures only 2 languages.
`run` in CI also needs simulators and Maestro on the runner; the docs do not document a recipe for that.

```yaml
      - run: shotfleet export out --fastlane fastlane/ --json
        env:
          SHOTFLEET_KEY: ${{ secrets.SHOTFLEET_KEY }}
```

Never write the key into the workflow file, the repo, a log line (`echo`, `set -x`), or an artifact.

## Two things to know when a script reads the result (checked in the code on 0.1.1, not on a device)

- A folder with several reports (a multi-device run `out/<device>/`, a config with both platforms, Play listings with phone and tablet sets) is checked once per report. `--json` prints one document: `screenshots`, `problems` and `notes` hold every report, and `reports` lists `{"report": "<path of check.json>", "problems": [...]}` per report so you can tell which device a problem came from. With one report there is no `reports` key.
- A `run` whose `SHOTFLEET_KEY` is missing or invalid does not fail: it captures 2 languages and exits 0 if those pass. It says `free tier: capturing 2 of N languages` (progress, so on stderr with `--json`); a CI job that must capture every language should fail on that line or compare the language count in `run.json`.

## Reading the result in a script

```bash
shotfleet check fastlane/ --app <MyApp.app> --json > check.json
code=$?
python3 -c "import json; d=json.load(open('check.json')); print(len(d.get('problems', [])), 'problem(s)'); [print(' -', p) for p in d.get('problems', [])]"
exit $code
```

Hooks (`after_run`) get `SHOTFLEET_EXIT`, `SHOTFLEET_PROBLEMS` and `SHOTFLEET_REPORT`; a failing `after_*` hook makes the
exit code 1 so CI notices (see config.md).
