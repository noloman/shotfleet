# Releasing shotfleet: build, test, gate, publish, verify, roll back

The rule: **publish the bytes you tested, never a rebuild.** `packaging/release.sh` (build and deploy in one run, used once by `go-live.sh`) ships different bytes than it tested; use the steps below instead.

1. **Preflight** (read-only, about a minute): `packaging/preflight.sh`. Signing certificates present and not close to expiry, `notarytool history` with the keychain profile, `wrangler whoami`, clean git tree, free disk, the uv standalone Python 3.14 at macOS 11.0. Fix every FAIL first.
2. **Build** from a clean worktree of the commit to release, with the standalone Python (a Homebrew Python makes the build need this Mac's macOS):
   `PYTHON=$(uv python find 3.14 --managed-python) DEVELOPER_ID=... INSTALLER_ID=... NOTARY_PROFILE=KeysiNotary packaging/build.sh`
   (defaults in `packaging/release.sh`). It signs, notarizes, writes `dist/shotfleet-<version>-macos-arm64.tar.gz` and `.pkg`. Copy both out of `dist/` to a durable folder: the next build deletes `dist/`.
3. **Verify the build** (read-only): `tools/verify-release.sh <tarball> <pkg>`. Every Mach-O file verifies, team id 2357A78TMR, hardened runtime, a quarantined `--version` run, `tools/macho-minos.py` at or below 13, and for the pkg `spctl` and `stapler`. Ends with PASS or FAIL.
4. **Test and gate those exact files:** `tools/check-claims.sh` (exit 0), then the device gate in `docs/device-queue.md` order (`tools/fixture-e2e.sh --android --keep` with `SHOTFLEET_BIN` on the unpacked build). A rebuild after this point voids the gate.
5. **Record what was tested:** `packaging/publish.sh --make-manifest <version> <tarball> <pkg> > manifest.txt` (version, size, sha256). Keep the manifest with the files.
6. **Publish** from a fresh worktree of `origin/main` (the release merged, `shotfleet.py`, the top `CHANGELOG.md` heading and the docs "Last checked against version" line all say the version):
   `SHOTFLEET_RELEASE_DIR=<durable folder, not /tmp> packaging/publish.sh --dry-run --manifest manifest.txt --artifacts <folder> --checkout <Gumroad URL>` first; it checks everything and prints the plan.
   The real run is the same command without `--dry-run`, and needs the owner's go-ahead. It refuses a file that differs from the manifest, a version that disagrees, a dirty tree, HEAD not `origin/main`, or an unreadable live version id; stages the files in `site/public/download`; archives the shipped bytes and what was live before in `$SHOTFLEET_RELEASE_DIR/archive/`; writes the current Cloudflare version id to `$SHOTFLEET_RELEASE_DIR/state/rollback-<version>-<time>.txt`; runs `wrangler deploy`; checks the served files' hashes, `VERSION`, `install.sh`, `tools/golive/smoke.sh` and a live install into a temp HOME; **rolls back by itself on any failure** (also if the script is stopped).
7. **Verify live** (already done by step 6; repeat by hand any time): `env -i sh tools/golive/smoke.sh https://shotfleet.com <Gumroad URL>`.
8. **Roll back by hand** if something turns up later: `cd site && npx wrangler@latest rollback <id from state/rollback-*.txt> -y`, then check `curl https://shotfleet.com/download/VERSION`. A site deploy from a tree without `site/public/download` can delete the downloads: only ever deploy through `publish.sh`.

`publish.sh` is rehearsed with fakes in `tests/test_release_scripts.py` (a fake wrangler and a local web server). It has not been run against the real Cloudflare; the first real run should come after a rehearsal on the throwaway worker `shotfleet-staging`.
