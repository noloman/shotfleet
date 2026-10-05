# Proposed GitHub Action (draft files only; nothing published, no Actions minute used)

Would be the root of the public repo `noloman/shotfleet-releases`. Files: `action.yml` (composite), `summarize.py` (job summary), `example-workflow.yml`, `selfcheck.sh` and `steptest.sh` (offline checks).

## What it does
1. Refuses anything but an Apple-silicon macOS runner (`hw.optional.arm64`, so a Rosetta shell does not matter; the `macos-*-intel` labels fail with a clear message).
2. Installs with the site's `install.sh` (TLS, SHA-256 from the same host), then `codesign --verify --strict -R='anchor apple generic and certificate leaf[subject.OU] = "2357A78TMR" and notarized'` on the installed program. That second check is the part `install.sh` lacks: it fails if the host served a program that is not signed by the owner's team or not notarized. Measured on this Mac (macOS 27, 0.1.1 release): exit 0 on the release file, exit 3 with another team id, `/bin/ls` fails `notarized`. Apple's ticket is looked up online, so it needs the runner's network (it has it).
3. Runs `check` (default), `doctor` or `run` with `--json`, keeps `shotfleet.json` and the stderr log, writes the problems into the job summary, sets outputs `exit-code` and `problems`.
4. Licence: `key` is passed as `SHOTFLEET_KEY` to that one step only, and only when non-empty. `run` is the fail-open case: with a missing or refused key shotfleet captures 2 languages and exits 0 (README "In CI"), so with `require-licence: true` (default) the step fails when the log has a `free tier:` line. A Gumroad outage still counts as licensed, by design (the action cannot tell it from a good key).
5. `cache-home: true` caches `~/.shotfleet` (Maestro, Java) for `run` jobs. `check` needs no cache: the program is a 10 MB download and starts in 0.15 s.

## What `run` in CI would still need (not in the draft)
Simulators and the Maestro flow on the runner: Xcode, a Debug simulator build, `doctor --fix`, Java, and a hosted runner has 3 vCPU and 7 GB (M1) with no nested virtualization, so no Android emulator (research/limits-platform-reach-2026-10-05.md). Four iOS simulators at once on 3 vCPUs is untested. So the action is a `check` action; `run` works only as far as the runner can host it. Say that in its README.

## Cost note (GitHub's pages, search result 2026-10-05; not read on github.com)
- macOS standard runner (M1, 3 vCPU, 7 GB): free in public repositories; in private repositories $0.062 a minute, and each macOS minute uses 10 minutes of the included allowance (2,000 free minutes a month is about 200 macOS minutes).
- Measured 2026-10-05 (platform note): install, `--version`, `doctor` and `check` on two PNGs took 16 s (macos-14) and 29 s (macos-15) of job time, so a `check` job is about 1 billed minute, about $0.06, if it needs no app build. A job that runs `xcodebuild` first pays for the build, which dominates; `--strings` avoids it.

## Not done, and why
- Version pinning: `install.sh` fetches the unversioned latest tarball, so the action cannot pin a version until the site (or the releases repo) serves versioned, immutable files. Same blocker as the Homebrew tap.
- No run on GitHub (owner rule: no Actions). The shell step was run here against a fake `shotfleet` (`steptest.sh`: problems fail, `fail-on-problems: false` passes, free tier fails `run` with exit 2, unknown command refused); the YAML was parsed with Ruby. The `uses: actions/cache@v4` step and `$GITHUB_PATH` handling were not exercised.
- Marketplace listing needs the owner to accept the Marketplace terms and a public repo with `action.yml` at its root; a one-time manual step.
- If published, the example in the product README should say the recipe has run on GitHub only after one real run (README already says it has not).
