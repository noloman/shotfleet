# Release 0.1.1: what shipped, the evidence, and how to build it again (2026-10-05)

Live since 13:27 (Cloudflare version `65c62221-aa1b-41af-ae2d-81c9ec0dd204`, replacing `609fa866-1216-4bf4-acbb-c0788fcbbad2`, the rollback target). Deployed by the 0.1.1 release owner session after the device gate passed and Manu approved ("Yes, deploy after the gate passes"). Nothing was posted anywhere.

## What it is

Main `2ccda21` (PR #63) = the 0.1.1 candidate `c4affd4` + PRs #53 (`8c2e647`), #54 (`2744af4`), #52 (`33fd8a9`), #51 (`1abc335`) + the standalone-Python build change + the line "Built for macOS 13 or later on Apple silicon; tested on macOS 27." (README, docs page, claim C131 `evidence`). Build commit `e2e1998`; shipping files (`shotfleet.py`, `ocr.swift`, `packaging/*`, `shotfleet.spec`, `site/public/install.sh`) at the merged tip equal that commit.

Published files (kept in `/Users/manu/Developer/shotfleet-rc-build/0.1.1/`): tarball 10,705,287 B sha256 `6f6b5bfcdccf5b4dbda10a76eedcb302daa91cdce9f19ee45bb9942d92c06c6d`; pkg 10,723,486 B sha256 `3847bc6556e40017bbacb7469d7711c29a9eb561ea27c668f36d3a021bd7defc`. The 0.1.0 live files are archived in `/Users/manu/Developer/shotfleet-rc-build/0.1.0-live/` (tarball sha256 `8b36c7f884eedde2e8e56b82e6f4100b2c4242253ffab105b6afd2e0ec786218`).

## Evidence

- **Device gate (G3), 2026-10-05 11:41-12:36:** `tools/fixture-e2e.sh --android --keep` with `SHOTFLEET_BIN` on the signed 0.1.1 build, iOS pinned to 26.4 by a one-line uncommitted patch of the script in the build copy (`runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"`, because an iOS 27 runtime of unknown origin was installed): **65 of 65 assertions, 54 min 57 s**. iPhone attempt 1 failed ar, de and ja, then tr on attempt 2, under load (start: load 284, free memory 41 %, swap 16,969 of 18,432 MB; the Mac was thrashing until the coordinator stopped seven idle Gradle daemons at 12:27; end: load 23, free memory 73 %, swap 6,086 of 7,168 MB). The 60 min kill was extended to 13:07 at 12:30 (coordinator's OK, run was still progressing); it finished at 12:36 and was not killed.
- **Full local gate on the final tip:** `tools/check-claims.sh` exit 0, 854 tests (21 skipped), 59 worker checks. (An earlier run failed once: my new README sentence broke the quote of claim C033; fixed by giving the line its own bullet.)
- **Minimum macOS:** `python3 tools/macho-minos.py dist/shotfleet` = 2 Mach-O files at macOS 11.0, 1 (`ocr`) at 13.0, none at 27.0 (0.1.0: 52 of 56 at 27.0). Python: uv standalone cpython 3.14.2.
- **Notarization:** Apple Accepted the program zip `592f0b9f-ae19-460f-ae2a-8e3e8d8268eb` and the pkg `bcc023c2-8b36-4ec0-9c70-f1e6141551ba`; quarantined `--version` 1 s; `spctl -t install` accepted (Notarized Developer ID); hardened runtime, team 2357A78TMR.
- **In the frozen build:** a made-up key in the real format reached Gumroad and was refused (TLS and certifi work; nothing written to the licence file); `check` on 72 CrossfitTracker screenshots in 18 languages = 0 problems (same as from source); clean-environment start and `doctor` run; local `install.sh` test installs and refuses a wrong checksum.
- **Production after the deploy:** `/download/VERSION` = 0.1.1; served tarball and pkg hash to the values above; `tools/golive/smoke.sh`: 36 checks, 0 failed; the live `install.sh` (a copy limited to a temp HOME) installed `shotfleet 0.1.1` with no quarantine flag.
- **iOS 27:** an iOS 27.0 runtime (24A434) is installed on this Mac by an unknown session or Xcode. The 4-simulator e2e on it was killed at its 35 min limit under load 735 and 21.6 GB swap (inconclusive, not a proven hang); a one-simulator repro on a quiet Mac passed (`research/xcode-27-ios27-attempt-2026-10-05.md`). A config without a `runtime` pin lands on iOS 27 while it is installed.

## Not proven

- Starting on any Mac older than macOS 27 (none available; a macOS 14/15 runner test is planned after this release, `docs/handoff.md`). The Mach-O minimum is a build fact, not proof.
- A refunded key being refused on the real Gumroad API (needs a paid sale by a second person); a clean Mac with nothing installed.

## How to build it again

`packaging/build.sh` runs `pip install --upgrade pyinstaller certifi`, so with no network the 0.1.1 build used a wrapper as `PYTHON`:

- `PYTHON=/Users/manu/Developer/shotfleet-rc-build/0.1.1/tools-stage/python-wrapper.sh PIP_NO_INDEX=1 DEVELOPER_ID='Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)' INSTALLER_ID='Developer ID Installer: Manuel Lorenzo Parejo (2357A78TMR)' NOTARY_PROFILE=KeysiNotary packaging/build.sh`, run from a clean worktree of the commit to build.
- The wrapper execs the uv-managed standalone Python `/Users/manu/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/bin/python3.14`; after `-m venv <dir>` it copies a `pth.txt` into `<dir>/lib/python3.14/site-packages/offline.pth` (pointing at PyInstaller 6.22.3 from the main checkout's `build/venv` site-packages and certifi 2026.6.17 vendored inside pip) and writes a `bin/pyinstaller` launcher that runs `python -m PyInstaller`.
- With network access the plain recipe works: `PYTHON=$(uv python find 3.14 --managed-python) packaging/build.sh` (the old Homebrew route stays the default when `PYTHON` is unset; it gives macOS 27 minimums).
- Then `python3 tools/macho-minos.py dist/shotfleet` (target: nothing above 13.0), the quarantined `--version` run, the TLS test with a made-up key from a temp HOME, `check` on real screenshots, and the fixture e2e on the unpacked binary.
- Publish the tested artifacts, not a rebuild: copy them into a tree's `site/public/download/` (untracked) together with `VERSION` and the `.sha256`, deploy from that tree (a site deploy from a tree without `download/` could delete the downloads), and record the current live version id first. Rollback: `npx wrangler rollback <id>`; this deploy's script is `deploy-011.sh` (scratch).
