# shotfleet on older macOS in Tart VMs (2026-10-05) — IN PROGRESS

Status: partial. macOS 26.2 run 1 done (one script bug, see below); 26.2 rerun, 26.0 and 13.6 pending (waiting for the device lock / quiet Mac).
Release tested: the LIVE one from https://shotfleet.com (0.1.2 at the time of the run).

Setup: Tart 2.32.1 (Cirrus Labs, notarized; the GitHub release the Homebrew formula points to, sha256 8554ab4f...4529 matches the formula; `brew install cirruslabs/cli/tart` fails on Homebrew 7 with a `depends_on macos:` error in the tap). Cirrus "vanilla" images (no Homebrew, no Xcode or Command Line Tools, no Java), 4 CPUs, 6 GB, headless, image default login admin/admin. Scripts: `vm-older-macos-2026-10-05/host-run.sh` (gate, pull, run, SSH, delete) and `guest-test.sh` (the tests inside the VM).

## macOS 26.2 (25C56), run 1, 18:28 to 18:37

`tools/selftest.sh --download --licence-probe` inside the VM: **PASS** (raw: `vm-older-macos-2026-10-05/macos-26.2-run1.txt`)

| Test | Result | Key line |
|---|---|---|
| download + checksum + install into a throwaway HOME | PASS | `install into a throwaway HOME: ok` |
| live `install.sh` into a throwaway HOME | PASS | `installed shotfleet 0.1.2 to .../.local/bin` |
| `--version` | PASS | `shotfleet 0.1.2` (no dyld / Expat error on 26.2) |
| `doctor` (150 s limit) | PASS | exit 2 (Java, Maestro, Xcode missing, as expected); `ok text recognition ready in 2 s` |
| `check` on 2 drawn screenshots | PASS | `checked 2 screenshots in 2 languages: 0 problem(s)` |
| licence: made-up key | PASS | refused by Gumroad (`licence probe: ok`) |
| Gatekeeper, .pkg (quarantined, assessments re-enabled) | **rejected by `spctl -t install`** (host 27.0: accepted); `installer -pkg` installed it and `/usr/local/lib/shotfleet/shotfleet --version` printed `shotfleet 0.1.2` | `rejected source=Notarized Developer ID` |
| Gatekeeper, quarantined program from the tarball | not run (script bug) | `spctl -t exec`: `rejected` (same as on the host for a bare command-line program: "does not seem to be an app") |

My own per-test steps (two real wger PNGs, explicit licence.json check, quarantined run) did not run in run 1: the time-limit helper was a shell function called through `env`. Fixed; rerun pending. The Cirrus 26.2 image starts with `assessments disabled`; `sudo spctl --global-enable` turned it on.
