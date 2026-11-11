# shotfleet in CI

`run`, `check` and `export` take `--json`: the result goes to stdout as JSON and progress goes to stderr. Exit
codes: `0` all good, `1` problems found, `2` setup error (the message says what to fix), `130` interrupted.

JSON shapes: `check` and `run` give `exit`, `screenshots`, `problems` (and `notes`, and `unverified`: screenshots not read because macOS text recognition was busy, exit 0 unless `--strict`); `export` gives `exit`,
`exported`, `skipped`. With exit 2 the JSON holds only `exit`; the reason is on stderr.

## The pull-request check

Checking needs only a Mac (it uses macOS text recognition) and no simulators, so it fits a pull-request job on
GitHub's macOS runners. `check` needs no key or account. The recipe as written (the build step, then check with --app) has not been run on GitHub yet. The installer, shotfleet --version, doctor and check on sample screenshots did run on GitHub's macos-14 and macos-15 runners (2026-10-05).

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

There is no key or license server: `run` and `export` work in CI like on a Mac.
`run` in CI also needs simulators and Maestro on the runner; the docs do not document a recipe for that.

## One thing to know when a script reads the result (checked in the code on 0.1.1, not on a device)

- A folder with several reports (a multi-device run `out/<device>/`, a config with both platforms, Play listings with phone and tablet sets) is checked once per report. `--json` prints one document: `screenshots`, `problems` and `notes` hold every report, and `reports` lists `{"report": "<path of check.json>", "problems": [...]}` per report so you can tell which device a problem came from. With one report there is no `reports` key.

## Reading the result in a script

```bash
shotfleet check fastlane/ --app <MyApp.app> --json > check.json
code=$?
python3 -c "import json; d=json.load(open('check.json')); print(len(d.get('problems', [])), 'problem(s)'); [print(' -', p) for p in d.get('problems', [])]"
exit $code
```

Hooks (`after_run`) get `SHOTFLEET_EXIT`, `SHOTFLEET_PROBLEMS` and `SHOTFLEET_REPORT`; a failing `after_*` hook makes the
exit code 1 so CI notices (see config.md).
