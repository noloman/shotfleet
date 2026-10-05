# Go-live gate (2026-10-03)

Go live only when every row has evidence. "Evidence" is a command and its output summary written in the Result column; "not tested" is allowed only in the last section, with the reason. No GitHub Actions: everything runs locally.

The files that ship are tested, not their predecessors: the release is built from final `main`, signed and notarized, then the checks below run on that tarball and package, and again on what the live URL serves after the deploy.

| # | What | How | Result |
|---|---|---|---|
| G1 | Final code on main, all local checks green | `tools/check-claims.sh` on the commit that is built | REBUILT 2026-10-04 from main 081853b (contains a1cfcf0, the start-up crash fix): `tools/check-claims.sh` exit 0, 798 tests (4 skipped) and 59 worker checks. |
| G2 | iOS fixture end to end on Maestro 2.0.10 and 2.11.0 | `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios`, once per Maestro | |
| G3 | The release binary (not the source) runs the fixture end to end with a real licence | same script with `SHOTFLEET_BIN=<built binary>` and `SHOTFLEET_KEY=<real key>` | 2026-10-04 22:14-22:41 on the signed release build of main 081853b with the real product ID, activated with the owner's real key: `SHOTFLEET_E2E=1 SHOTFLEET_BIN=<binary> tools/fixture-e2e.sh --android --keep`, 65 of 65 assertions (iPhone 17 Pro Max + iPad 13" + Android phone; export, hooks, planted failures caught), 27 min on a loaded Mac. The earlier 65/65 on e833a85 predates a1cfcf0 and is superseded. |
| G4 | Release artifacts built from final main: tarball and installer package, signed and notarized | `packaging/build.sh` with the Application and Installer identities and the notary profile | 2026-10-03, built from main 7bebd9f with the real product ID applied (temp worktree): `packaging/build.sh` exit 0; Apple notary Accepted for the program zip and for the package; tarball 9.2 MB, package 9.2 MB. The shipped build will be rebuilt by go-live and the G5-G7 checks repeated on it. REBUILT 2026-10-04 from 081853b: `packaging/build.sh` exit 0 in 126 s; notary Accepted for the program zip (008b9344-6e82-4e65-8433-e25e715445de) and the package (a7c22d9e-f70a-44a2-b4e3-b68e0717c43e); tarball 9,732,997 bytes sha256 079233aa7cb3aaf33b317300b9dcbb25548621c75b827e17dc3e8e255781e30f; package 9,744,665 bytes. go-live.sh rebuilds through release.sh, so the shipped files get new hashes; the code is the same while main has no shipping change after 081853b. |
| G5 | Gatekeeper accepts them | quarantined tarball runs (`--version` under 90 s); `spctl -t install` on the package says Notarized Developer ID; `stapler validate`; `codesign --verify --deep --strict` | pass: package `pkgutil --check-signature` Developer ID Installer, notarization trusted; `stapler validate` ok; `spctl -t install` accepted, source=Notarized Developer ID; tarball `codesign --verify --deep --strict` ok, hardened runtime, team 2357A78TMR; quarantined fresh extract prints the version in 2.3 s. REBUILT 2026-10-04: quarantined tarball `--version` in 2.4 s; `spctl -t install` accepted (Notarized Developer ID); `stapler validate` ok; `codesign --verify --deep --strict` valid, hardened runtime, team 2357A78TMR. |
| G6 | Licence on the signed hardened-runtime binary against the real Gumroad API | free tier refuses `export`; `activate` with the real key counts one use; again counts none; `SHOTFLEET_KEY` validates; a made-up key is refused | pass on the signed hardened-runtime binary: no licence, `export` refused (exit 2, nothing written); activate in a new home counts a use (real API uses 1 to 2), activating again in the same home counts none (stays 2); `SHOTFLEET_KEY` with the real key passes the gate (the next error is the missing run); a made-up key is refused for `SHOTFLEET_KEY` and for `activate`, both with "That license does not exist for the provided product". The test key now holds 2 of 3 slots. |
| G7 | Install paths | `install.sh` against a local server serving the real tarball and checksum (temp HOME, PATH untouched); the package expands and its post-install script is correct | pass: real `install.sh` (copy limited to a temp folder) against a local server serving the real tarball and checksum: installs, link works, `--version` 0.1.0, no quarantine flag on the installed binary; a wrong checksum is refused and installs nothing; the real PATH folders were not touched. Package payload: 185 files under /usr/local/lib/shotfleet plus the post-install link. REBUILT 2026-10-04: real install.sh (limited to a temp folder) against a local server serving the new tarball and checksum: installs, link works, `--version` 0.1.0, no quarantine flag; wrong checksum refused (exit 1, nothing installed); clean-environment start `env -i ... --version` and `doctor` run to the end (the a1cfcf0 bug showed there). |
| G8 | Real apps with the release binary | CrossfitTracker iOS (18 languages) and Android, 0 problems | |
| G9 | Site rehearsal off the production domain | transformed page deployed to a throwaway worker; `tools/golive/smoke.sh` against it; downloads, checksum, VERSION, links, CSP | pass: transformed page plus the real tarball, checksum, VERSION and package deployed to the throwaway worker `shotfleet-staging` (no routes, no KV); `tools/golive/smoke.sh` 35 of 36 ok, the one failure is the http to https redirect, which `workers.dev` does not do; on the real domains `curl -I` shows http://shotfleet.com and http://www.shotfleet.com answer 301 to https. The package served from the staging site has the same SHA-256 as the build and `spctl -t install` accepts it with a quarantine flag (a browser-style download). |
| G10 | Production smoke right after the deploy | `tools/golive/smoke.sh https://shotfleet.com <product url>`, a real `install.sh` from the live URL into a temp HOME, `--version` equals `/download/VERSION` | 2026-10-05 ~08:20 (go-live ran at 08:02-08:11: commits 5fa4f7c Gumroad product ID, 5bbec86 Site: sale open): `env -i sh tools/golive/smoke.sh https://shotfleet.com https://8954369651852.gumroad.com/l/shotfleet` = 36 checks, 0 failed (sale page has no waitlist markers, checkout link in 3 places, VERSION 0.1.0, archive 9,731,376 bytes matches its .sha256, install.sh checksum logic accepts it, unpacked program says shotfleet 0.1.0, robots/sitemap/terms/privacy 200, http redirects to https). The served archive downloaded fresh: sha256 8b36c7f8...6218 equals the published one; quarantined `--version` 5.4 s; signed Developer ID Application team 2357A78TMR, hardened runtime. `tools/golive/storefront.sh` ok before: product published, licence keys on, product ID in page, 14-day refund, price 49, made-up key rejected. A real `install.sh` from the live URL into a temp HOME was NOT run (it can link into /opt/homebrew/bin on this Mac); G7's temp-limited copy covers the logic. |
| G11 | Rollback is written and rehearsed | waitlist page redeploy from the previous commit; Gumroad product unpublish; which commands, in which order | written below; production Cloudflare version before go-live: 5716b430-26b9-4765-9933-292007154379 (11:19:51Z); production today is the waitlist and /download/VERSION answers 404. |

## Not tested, and why (accepted risk)

- A refunded key being refused on the real API: Gumroad lists no test purchases in Sales, so nothing can be refunded without a real paid sale. The code path is unit-tested and the live purchase object carries the fields it reads.
- A clean macOS user or second Mac: creating a user needs an administrator password and no VM tool is installed. Substitute: temp HOME, `env -i`, PATH without Homebrew.
- Outside developers: none available to this session.
- The installer package installed by Installer.app with an administrator password: needs the owner's password.
- Android on a fixture app: none exists; CrossfitTracker Android is the substitute (G8).
- Seller-side legal and tax steps (KvK registration): the owner's.

## Rollback (G11)

Before go-live: `cd site && npx wrangler deployments list` and note the newest version id (today: 5716b430-26b9-4765-9933-292007154379). Other sessions also deploy the site, so read it again right before the go-live.

If the sale page or a download is wrong after the deploy:
1. Site back to the waitlist: `cd site && npx wrangler rollback <version id noted above> --name shotfleet` (Cloudflare restores that version, assets included). Then `tools/golive/smoke.sh` is expected to show the waitlist again.
2. Stop sales at the source: Gumroad product page, Product tab, Unpublish (the product stays, nothing is deleted).
3. Repo: `git revert` the commit "Site: sale open" and the "Gumroad product ID" commit if the program build is at fault, then rebuild with `packaging/release.sh`.
4. Buyers already holding keys keep working: the licence check only needs the product ID, which does not change.
Irreversible parts: emails and posts the owner sends, and sales that already happened (refund from the Gumroad Sales page, 14-day policy).

## Post-launch verification (independent, 2026-10-05, on the files shotfleet.com serves)

Run from a clean download, not from the build folder:
- The published SHA-256 matches the downloaded tarball (8b36c7f8...).
- The program starts with an empty home and a bare PATH (`env -i`): `shotfleet 0.1.0`. This is the crash found on 2026-10-04 (find_sdk called is_mac before it existed: every Mac without an Android SDK failed at `--version`); the live build has the fix.
- `codesign --verify --deep --strict` ok, hardened runtime, team 2357A78TMR; a quarantined copy prints the version in 1.2 s.
- The installer package: `spctl -t install` accepted (Notarized Developer ID), `stapler validate` ok, signed with the Developer ID Installer certificate, notarization trusted.
- The live `install.sh`, run unchanged except that its target folder is limited to a temp HOME: downloads 0.1.0 from shotfleet.com, installs, `shotfleet --version` works, no quarantine flag on the installed binary, the real PATH folders gain no link.
- The sale page has no waitlist text, the Gumroad link three times, `/download/VERSION` answers 0.1.0.

Still not run (unchanged): a refunded real key being refused (needs a real paid sale), a clean macOS user or second Mac, outside developers, and the package installed by Installer.app with an administrator password.

## Release 0.1.1 (2026-10-05)

Live 13:27. Full evidence, hashes, the rollback id and the rebuild recipe: [research/release-0.1.1-evidence-2026-10-05.md](release-0.1.1-evidence-2026-10-05.md). Device gate 65 of 65 on the signed standalone-Python build (iOS 26.4 pinned), production smoke 36 checks and a live install test passed.

