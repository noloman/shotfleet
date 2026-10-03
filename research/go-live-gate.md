# Go-live gate (2026-10-03)

Go live only when every row has evidence. "Evidence" is a command and its output summary written in the Result column; "not tested" is allowed only in the last section, with the reason. No GitHub Actions: everything runs locally.

The files that ship are tested, not their predecessors: the release is built from final `main`, signed and notarized, then the checks below run on that tarball and package, and again on what the live URL serves after the deploy.

| # | What | How | Result |
|---|---|---|---|
| G1 | Final code on main, all local checks green | `tools/check-claims.sh` on the commit that is built | |
| G2 | iOS fixture end to end on Maestro 2.0.10 and 2.11.0 | `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios`, once per Maestro | |
| G3 | The release binary (not the source) runs the fixture end to end with a real licence | same script with `SHOTFLEET_BIN=<built binary>` and `SHOTFLEET_KEY=<real key>` | |
| G4 | Release artifacts built from final main: tarball and installer package, signed and notarized | `packaging/build.sh` with the Application and Installer identities and the notary profile | |
| G5 | Gatekeeper accepts them | quarantined tarball runs (`--version` under 90 s); `spctl -t install` on the package says Notarized Developer ID; `stapler validate`; `codesign --verify --deep --strict` | |
| G6 | Licence on the signed hardened-runtime binary against the real Gumroad API | free tier refuses `export`; `activate` with the real key counts one use; again counts none; `SHOTFLEET_KEY` validates; a made-up key is refused | |
| G7 | Install paths | `install.sh` against a local server serving the real tarball and checksum (temp HOME, PATH untouched); the package expands and its post-install script is correct | |
| G8 | Real apps with the release binary | CrossfitTracker iOS (18 languages) and Android, 0 problems | |
| G9 | Site rehearsal off the production domain | transformed page deployed to a throwaway worker; `tools/golive/smoke.sh` against it; downloads, checksum, VERSION, links, CSP | |
| G10 | Production smoke right after the deploy | `tools/golive/smoke.sh https://shotfleet.com <product url>`, a real `install.sh` from the live URL into a temp HOME, `--version` equals `/download/VERSION` | |
| G11 | Rollback is written and rehearsed | waitlist page redeploy from the previous commit; Gumroad product unpublish; which commands, in which order | |

## Not tested, and why (accepted risk)

- A refunded key being refused on the real API: Gumroad lists no test purchases in Sales, so nothing can be refunded without a real paid sale. The code path is unit-tested and the live purchase object carries the fields it reads.
- A clean macOS user or second Mac: creating a user needs an administrator password and no VM tool is installed. Substitute: temp HOME, `env -i`, PATH without Homebrew.
- Outside developers: none available to this session.
- The installer package installed by Installer.app with an administrator password: needs the owner's password.
- Android on a fixture app: none exists; CrossfitTracker Android is the substitute (G8).
- Seller-side legal and tax steps (KvK registration): the owner's.
