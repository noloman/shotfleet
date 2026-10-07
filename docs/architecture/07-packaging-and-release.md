# 7. Packaging and release

Back to the [index](../ARCHITECTURE.md). Primary sources: `packaging/README.md` (the release procedure, kept current by the release engineer),
`packaging/*.sh`, `tools/verify-release.sh`, `research/limits-release-engineering-2026-10-05.md`, `research/notary-profile-2026-10-06.md`.

**The rule: publish the bytes you tested, never a rebuild.** Everything below exists to make that checkable.

## 7.1 What a release is

Four files per version, built for Apple silicon macOS 13 or later:

| File | What |
|---|---|
| `shotfleet-<version>-macos-arm64.tar.gz` | a PyInstaller **one-folder** build (`dist/shotfleet/`): the executable, Python, the `ocr` helper, the `skill/` folder. A folder starts in about 0.15 s; a one-file build unpacks itself on every launch (about 1.2 s, measured). |
| `shotfleet-<version>-macos-arm64.pkg` | an installer package that lays the folder at `/usr/local/lib/shotfleet` and links `/usr/local/bin/shotfleet`. Files the Installer lays down carry no quarantine flag, so Gatekeeper never checks them at run time. |
| `...tar.gz.sha256` | the checksum `install.sh` verifies |
| `VERSION` | the latest version number, read by `doctor` and the publish checks |

The Linux `check` image (`ghcr.io/noloman/shotfleet-check`) is built separately and is not part of the Mac release.

## 7.2 The build (`packaging/build.sh`)

1. **Read-only guards first.** If `DEVELOPER_ID` and `NOTARY_PROFILE` are set it runs `packaging/notary-check.sh` before anything (a locked keychain
   would otherwise be found minutes later, after the build).
2. **Pinned Python.** `PINNED_PYTHON` (default `3.14.2`) must be a uv-managed **python-build-standalone** interpreter (`uv python install 3.14.2`,
   found with `uv python find 3.14.2 --managed-python`). Any other version, or a Homebrew Python, is refused. Why: Homebrew's Python is built for the
   macOS it was built on (27.0 measured on 2026-10-05), so a PyInstaller folder made from it needs that macOS; the standalone one is built for macOS 11.
   The script copies the interpreter into a temp dir and runs `tools/macho-minos.py --max 11` on it (that tool reads regular files only, hence the copy).
3. **Pinned inputs.** `build/venv` is made fresh; only `packaging/requirements-build.txt` is installed, with `pip install --only-binary=:all: --require-hashes`:
   PyInstaller 6.22.3, hooks-contrib 2026.8, certifi 2026.6.17, macholib, altgraph, packaging, setuptools, with sha256 of the wheels. A hash mismatch
   stops the build ("do not build until you know why"). The file also holds PyInstaller's Linux wheel hashes for the Docker image. `tests/test_pinned_build_inputs.py` checks no unpinned install is left.
4. **The OCR helper:** `swiftc -O -target arm64-apple-macos13.0 ocr.swift -o build/ocr` (`MACOS_MIN`, default 13.0: Vision's newer text models start there).
5. **The release date, then PyInstaller.** The build writes `build/_release.py` containing `RELEASE_DATE = "YYYY-MM-DD"` (the build day, `date -u`; it errs in the buyer's favour because a build is published days later, never earlier) *after* `build/` was recreated. Then `--onedir --name shotfleet --add-binary build/ocr:. --add-data skill:skill --paths $PWD/build --hidden-import _release`, so PyInstaller freezes that module into the program's compiled archive (PYZ) and `baked_release_date()` (`shotfleet.py:5012`) finds it by `import _release`. Why a module, not `--add-data`: a loose file in `_internal/` could be deleted by the user with one `rm`, which turned the licence's update window off, and the code signature would not notice (a bare Mach-O signature seals only the executable; review note N2). Verified by the reviewer on a mini program with the same flags (the date prints, no loose `_release` file in `_internal`, it still prints after the source module is moved away) and by `tools/release-candidate.sh` on the real frozen build (below). The licence use of the date is in [05](05-licensing.md#the-update-window). Then re-sign.
6. **Signing** (when `DEVELOPER_ID` is set): the helper first, then every Mach-O file in the folder **deepest first**, then frameworks, then the main executable with
   hardened-runtime entitlements (`packaging/entitlements.plist`: `disable-library-validation` and `allow-unsigned-executable-memory`, because the one-folder build
   loads Python's libraries at launch). It re-signs everything PyInstaller already signed because PyInstaller's own signing leaves a Python framework with a signature Apple's
   notary rejects. `codesign --verify --deep --strict` closes the step. Team id `2357A78TMR`.
7. **Notarization** (when `NOTARY_PROFILE` is set): zip the folder with `ditto`, run `notary-check.sh` again, `xcrun notarytool submit --wait`, require
   `status: Accepted`. Then do not trust the verdict alone: unpack the tarball that will ship, set the quarantine attribute, and **run it** (`--version`, 90 s
   alarm). `spctl` cannot assess a bare executable, but a quarantined, not-notarized copy hangs and is killed, while a notarized one prints its version.
8. **The package** (`packaging/pkg.sh`, if `INSTALLER_ID` is set): `pkgbuild` with a `postinstall` that links the binary, signed with the Developer ID **Installer**
   certificate, notarized, `stapler staple` and `validate`, and `spctl --assess --type install` must say `source=Notarized Developer ID`.
9. `tools/macho-minos.py dist/shotfleet` prints the oldest macOS the build runs on (informational here; enforced by `verify-release.sh`).

Linux: `packaging/build-linux.sh` makes an unsigned folder with the same pinned inputs and no Swift helper; `Dockerfile` builds the `check` image from the
compiled program, never from `shotfleet.py` (it asserts no `.py` ships). Neither writes the `_release` module (only `build.sh` does), so a frozen Linux build prints the "no usable release date" warning from `baked_release_date` on every start; harmless for `check`, see the appendix.

### The notary profile gotcha (read this before your first release)

`xcrun notarytool ... --keychain-profile ShotfleetNotary` says **"Error: No Keychain password item found for profile"** when the Mac's screen has been locked for
more than about five minutes. It is **locked, not missing**: notarytool stores the profile in the data-protection keychain, which locks 5 minutes after
the screen locks, and it prints the same text as for a profile that was never stored. `security find-generic-password` cannot see that item, so it proves nothing
(`research/notary-profile-2026-10-06.md`: 25 of 25 errors in one night were "keychain is locked" while the Mac was locked; the profile worked again
after unlock). Before any notarization:

- unlock the Mac and keep it awake. `packaging/release.sh` runs the build under `caffeinate -di` (display and system stay awake); do the same for a manual build;
- `packaging/notary-check.sh` (read-only `notarytool history`, 60 s limit) fails fast with that explanation; the build runs it before the build and again right before each upload;
- only if it still fails after unlocking, store the profile again (the script prints the command; it prompts for the app-specific password, never paste it into a command or chat).

The profile is named `ShotfleetNotary` by default (an earlier one, `KeysiNotary`, was shared with another product).

## 7.3 Verify the build (`tools/verify-release.sh`)

Read-only: unpacks copies into a temp dir. For a tarball or folder: every Mach-O file verifies (`codesign --verify --strict`, the program also `--deep`) with
team id `2357A78TMR`, the hardened runtime flag is set, a **quarantined** copy prints its version (asks Apple's servers on first run, about 10 s; `--no-run`
skips), and `tools/macho-minos.py` stays at or below 13 (`--max-macos`). For a `.pkg`: the signature (Developer ID Installer, the team), `spctl -t install` and
`xcrun stapler validate`. `--manifest` checks each file against the manifest. Ends with PASS or FAIL; exit 1 on FAIL. The minos tool reads `LC_BUILD_VERSION minos`
(or the old `LC_VERSION_MIN_MACOSX`) of every Mach-O file; the released build declares two files at 11.0 and the `ocr` helper at 13.0.

## 7.4 The release gate: test the exact files

The gate is **local**. There is no hosted CI gate (`tools/check-claims.sh` plus the device runs below); every workflow is manual.

1. `tools/check-claims.sh` exits 0 on the commit being released.
2. **Non-device proofs on the built bytes** (recorded as `proofs.out` per release, for example `shotfleet-rc-build/0.1.2/`): a quarantined `--version`, `spctl` and `stapler`,
   codesign (hardened runtime, team id), an `env -i` start (the 0.1.0 candidate crashed at start on any Mac without an Android SDK, a `NameError` at import found only by this),
   TLS in the frozen build (a made-up key reaches Gumroad and is refused, nothing written), `check` on 72 real screenshots with 0 problems, `install.sh` in a throwaway `HOME`
   (a wrong checksum is refused).
3. **The fixture end-to-end on the built binary**, in the order and under the lock of `docs/device-queue.md`:
   `SHOTFLEET_E2E=1 SHOTFLEET_BIN=<unpacked build>/shotfleet tools/fixture-e2e.sh --android --keep` (the binary needs a licence for the export step: activate it or set
   `SHOTFLEET_KEY`). It builds `tools/fixture-app` (SwiftUI, en/de/ja/ar/tr, two screens) and `tools/fixture-app-android`, then drives `init`, `doctor`, `run` (iPhone and
   iPad, de/ja/ar/tr), `check`, `export`, and **plants a copied screenshot and a missing one and expects `check` to catch both**. Passing means iOS 36 of 36 and Android 29 of 29
   assertions (65 in all). It refuses to run without `SHOTFLEET_E2E=1`, needs 5 GB free and memory pressure that is not critical, and has a hard limit.
   `tools/fixture-byoc-e2e.sh` does the same for `[capture]` on 2 simulators (de, ja); it has not passed for the finished feature yet.
4. **A rebuild after this point voids the gate.** Gate runs are about 37 to 55 minutes on a quiet Mac, longer under load.

Lessons written into the gate rules (`docs/handoff.md` section 17): start only at memory pressure level 1, not by "free percentage" (a run with 34 percent free and 15 GB of
swap still starved); no busy Gradle or Kotlin daemon at the start (idle daemons held 21 GB once); every emulator under the device lock (an unlocked one broke a gate); a pool simulator
that hung is replaced, not reused. The 0.1.3 and 0.1.4 releases were gated on **combined evidence** from two runs of the same signed build (iOS in one, Android in another)
because memory failures on the shared Mac voided full runs; both decisions are written in `docs/handoff.md` so nobody reads them as one 65/65 run.

## 7.5 Publish (`packaging/publish.sh`)

`publish.sh` builds nothing. Sequence:

1. `packaging/publish.sh --make-manifest <version> <tarball> <pkg> > manifest.txt` records version, size and sha256 of the **tested** files.
2. `SHOTFLEET_RELEASE_DIR=<durable folder, not /tmp> packaging/publish.sh --dry-run --manifest manifest.txt --artifacts <folder> --checkout <Gumroad URL>`
   runs every check and prints the plan, staging, archiving, deploying and rolling back nothing.
3. The real run (needs the owner's go-ahead) is the same command without `--dry-run`.

What the real run does, in order, and why:

| Step | Why |
|---|---|
| Check the two artifacts against the manifest (size and sha256), exactly two files listed | a file that differs from the tested one is never published |
| Check the **tree** (and the manifest's own `version X.Y.Z` line, which must be digits and two dots only: it goes into file names and paths, so `9.9.9;x` or `9.9.9.1` is refused; security finding S7): `shotfleet.py` `VERSION`, the top `CHANGELOG.md` heading and the docs page's "Last checked against version X" line must all equal the manifest version; no `<!-- RELEASE_DATE -->` placeholder in the CHANGELOG heading or `site/public/whats-new.html`; no `RESUME.md`; git tree clean; `HEAD` is `origin/main` (`PUBLISH_ALLOW_BRANCH=1` overrides) | the site text must not claim a version the downloads do not have |
| Require `SHOTFLEET_RELEASE_DIR` as an absolute, **durable** path (refuse `/tmp`, `/private/tmp`, `/var/folders`) | `/tmp` is wiped on reboot; the rollback id and the shipped bytes live there |
| Verify every earlier version kept in `$SHOTFLEET_RELEASE_DIR/archive/<X.Y.Z>/` against its `SHA256SUMS` (and kept `manifest.txt`) | see "versioned downloads" below |
| Read the live Cloudflare version id (`wrangler deployments list`) and refuse to deploy without it | that id is the rollback target |
| Stage the files into `site/public/download/`, archive the shipped bytes plus `SHA256SUMS` and the manifest in `archive/<version>/`, copy what is live now to `archive/live-before-<version>/` (best effort), stage `/download/<version>/` for this and every archived version | |
| Write the rollback id to `$SHOTFLEET_RELEASE_DIR/state/rollback-<version>-<time>.txt` | durable, outside `/tmp` |
| `wrangler deploy` in `site/` | |
| Verify the live site: `/download/VERSION` equals the version (retried), the tarball, `.sha256` and pkg hashes, every versioned file of every version, `install.sh` returns 200, the `immutable` header, `tools/golive/smoke.sh` (36 checks, run under `env -i`), and a **live install into a temp HOME** whose `--version` must print `shotfleet <version>` | |
| **Roll back automatically** on any failure after the deploy, also on Ctrl-C or when the script dies (`trap`), to the recorded id | |
| Write `state/published-<version>-<time>.txt` | |

It has a `--staging` mode targeting the throwaway worker `shotfleet-staging` (`site/wrangler.staging.toml`: no routes, no custom domains, no bindings, only its own
`workers.dev` address) for rehearsals. `check_staging` refuses to run when that config names the production worker, has any route, zone, `[env]`, binding or any table other than
`[assets]`, or when `PUBLISH_BASE` is not `https://shotfleet-staging.<account>.workers.dev` (there is no default base in staging mode), and `wr()` aborts any
`deploy` or `rollback` whose base names `shotfleet.com`. Its tests (`tests/test_release_scripts.py`: fake wrangler plus a local web server) rehearse the real script; it
was also rehearsed once against the real Cloudflare staging worker on 2026-10-05, and its first real production run was 0.1.2.

### Why there is no "site-only deploy"

A Cloudflare Workers static-assets deploy **replaces every static asset**. `site/public/download/` is in `.gitignore` (the tarballs are not in git), so a deploy from a fresh
checkout, or from any tree without that folder, would delete the downloads: `install.sh` and `doctor`'s update check would break the moment the site text was updated. `packaging/README.md` says it
outright: "A site deploy from a tree without `site/public/download` can delete the downloads: only ever deploy through `publish.sh`." The same property is why every old version has to
be staged again on every publish. And because the site's own text (docs "Last checked" line, `whats-new`, `llms.txt`) states a version and the downloads must match it, `publish.sh`
refuses a tree whose `shotfleet.py`, CHANGELOG heading or docs line disagrees with the manifest. There is deliberately no flag that skips those checks; the only overrides are
`PUBLISH_ALLOW_BRANCH=1` (publish a tree that is not `origin/main`) and the test-only `SHOTFLEET_ALLOW_TMP_DIR=1`. If you only changed site text you still have to go through `publish.sh` with the already-tested
artifacts of the current version (my reading of the script, not a documented procedure: the manifest is for the artifacts, the tree's `VERSION` must still equal it, and an
existing `archive/<version>/` is accepted only when its `SHA256SUMS` match). A rollback to a deployment older than the versioned folders
removes those folders until the next publish.

### Versioned downloads

`/download/<file>` and `/download/VERSION` are always the **latest** (`Cache-Control: no-cache`, `site/public/_headers`). `/download/<version>/shotfleet-macos-arm64.tar.gz`, its
`.sha256` and the `.pkg` are **permanent and never change** (`public, max-age=31536000, immutable`). They exist so that old versions stay installable (a buyer whose year of updates ended can keep
the version they had, which the licence wording relies on), so Homebrew casks and GitHub Actions can pin a version, and so a bad release can be rolled back by reinstalling. To add an older release by hand (once):
create `archive/<X.Y.Z>/` with the tarball (and pkg if its hash is recorded) and a `SHA256SUMS` written from the **recorded** hashes (release evidence or manifest), never from the files themselves.
Cloudflare limits: 25 MiB per file, 20,000 files per version on the free plan; a release is four files of about 10 MB.

## 7.6 After publishing

- **Smoke the live site** by hand any time: `env -i sh tools/golive/smoke.sh https://shotfleet.com <Gumroad URL>`. It is read-only: pages and release files fetched into a temp dir,
  the CSP header, `install.sh` is a shell script that refuses non-arm64 and checks SHA-256, `VERSION` parses, the archive matches its `.sha256`, `install.sh`'s checksum logic accepts it
  (run only up to its checksum check with a fake arm64 `uname` and a temp HOME), the unpacked program prints the version, robots and sitemap, HTTP redirects to HTTPS.
- **Homebrew:** `sh tools/bump-homebrew.sh <version> <checkout of noloman/homebrew-tap>` reads the published `/download/<version>/` `.sha256`, checks it against the tarball, rewrites
  `Casks/shotfleet.rb`'s version and sha256, prints the diff and never pushes. Then `brew audit --new --strict --cask noloman/tap/shotfleet`, commit and push the tap yourself. It is a cask (not a formula)
  because Homebrew's docs say proprietary binary-only programs go in casks; `doctor` tells a Homebrew install to `brew upgrade --cask noloman/tap/shotfleet` (`update_command`, `:3924`).
- **Public skills:** `sh tools/sync-public-skills.sh <checkout of noloman/shotfleet-skills>`, review, push.
- **Linux `check` image:** from the same clean worktree, `gh auth token | docker login ghcr.io -u noloman --password-stdin`, then `packaging/docker-check.sh` (buildx for amd64 and arm64, pushes
  `:<version>` and `:latest`, runs `--version` from the registry on both CPUs; `PUSH=0` builds locally only). Bump the pinned version in `noloman/shotfleet-check-action` after.
  The first time: delete the `DOCKER-PENDING` marker lines in `site/public/docs.html` and `llms.txt` and add an empty `site/DOCKER_PUBLISHED` (`tests/test_site.py` `DockerPending`).
- **Rollback by hand:** `cd site && npx wrangler@latest rollback <id from state/rollback-*.txt> -y`, then `curl https://shotfleet.com/download/VERSION`. A Worker rollback does not change what Gumroad or installed copies hold.

## 7.7 Other release-adjacent scripts

| Script | Purpose |
|---|---|
| `packaging/preflight.sh` | Read-only, about a minute: both Developer ID certificates present and not within 14 days of expiry, `notarytool history` works, `wrangler whoami`, clean tree, 5 GB free, the uv Python at macOS 11.0. Prints OK or FAIL per check, exit 1 on any FAIL. |
| `packaging/release.sh` | Build **and** deploy in one run. Its own header says it was used once, by `go-live.sh`; it ships bytes it did not test. Use build, test, publish instead. It does hold `caffeinate -di` around the build. |
| `packaging/go-live.sh` | Launch day for 0.1.0: set `GUMROAD_PRODUCT_ID`, flip the site from waitlist to Buy, deploy. `--dry-run` rehearses on a temp copy. Not used for later releases. |
| `tools/release-candidate.sh` | Build the frozen program with a TEST product id (it starts with `RCTEST`, which is what lets a frozen build honour `SHOTFLEET_GUMROAD_API`) into a temp copy and run the licence and release checks against a fake Gumroad (needs `SHOTFLEET_RC=1`). The licence part now covers five activations then a refused sixth that burns nothing, a CI key during an outage on a machine that never passed a check (must refuse) and on one that did (must pass), and the baked release date: a purchase from 2020 must answer "your licence covers every shotfleet version released until 2021-01-01" (`sale=` control call), a message only the dated path produces. It does not check that the baked date is today's; `build.sh` writes it. Nothing is notarized, deployed or sent. |
| `tools/selftest.sh` | One script a person runs on any Mac (`sh selftest.sh --download`) that installs the release in a throwaway folder and prints one PASS/FAIL block: used for macOS-version and clean-Mac evidence. Not part of the product. |
| `tools/status.sh` | Prints the numbers `STATUS.md` quotes, from the repo and the live site (read-only). |
| `tools/watch-upstream.sh` | Runs the two upstream watchers on this machine about monthly and before a release: newest stable Maestro against what shotfleet relies on (`tools/latest-maestro.py`, which downloads 315 MB only when a new tag appears), and Apple's size page against `APPLE_SIZES` (`tools/apple-specs-watch.py`). |
| `tools/maestro-compat.py` | Checks a Maestro folder against `MAESTRO_INTERFACE` (flags, log lines, env vars, flow keys) with no device. Run it first when a new Maestro appears; it does not replace the fixture run. |
| `tools/pretend-mac.py` | Runs one test module as if on an Apple-silicon Mac (platform and CPU flipped), to catch Mac-only failures before a Mac run. |

## 7.8 Release checklist

(Compact version; the long one with commands is `packaging/README.md`.)

1. Everything for the release merged to `main`; `VERSION` set; top `CHANGELOG.md` heading `## X.Y.Z (<!-- RELEASE_DATE -->)` (the placeholder waits until release day); docs page "Last checked against version X.Y.Z"; `tools/check-claims.sh` rc 0.
2. `packaging/preflight.sh` all OK. Unlock the Mac. Tell other sessions to hold merges.
3. Build from a **clean worktree of that commit** with `DEVELOPER_ID`, `INSTALLER_ID`, `NOTARY_PROFILE=ShotfleetNotary` under `caffeinate -di`.
4. `tools/verify-release.sh <tarball> <pkg>` PASS; non-device proofs.
5. Device gate on the exact files under the device lock; keep logs in a durable folder.
6. `publish.sh --make-manifest`; `--dry-run`; owner says go; real run from a fresh worktree of `origin/main`. Dates filled in CHANGELOG and `whats-new.html` first.
7. Verify live (publish already did); Homebrew bump; public skills sync; Docker image; update `STATUS.md` and `docs/handoff.md`.
8. If anything is off: roll back by the recorded id.
