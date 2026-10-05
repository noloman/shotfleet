# Proposed Homebrew tap (not published; files only)

Would live in the public repo `noloman/homebrew-shotfleet` (does not exist; owner decision, see the note). Contents: `Formula/shotfleet.rb` (rendered), a 10-line `README.md` with `brew install noloman/shotfleet/shotfleet`. Nothing else.

`render-formula.sh <version> <tarball> <url>` fills the template from the TESTED tarball's SHA-256. The URL must be versioned and immutable; the site serves only the unversioned latest file today.

Tested 2026-10-05 in a throwaway tap on this Mac (created and removed by the test: `brew tap-new --no-git`, then `brew untap`):
- `brew audit --strict --formula`: exit 0, no findings.
- `brew install --formula` of the 0.1.1 release tarball through a `file://` URL: installed to the Cellar in 2 s, `brew test` ran `shotfleet --version` and passed.
- After install, `codesign --verify --deep --strict` exit 0, and `codesign --verify --strict -R='anchor apple generic and certificate leaf[subject.OU] = "2357A78TMR" and notarized'` exit 0: Homebrew did not break the Developer ID signature or the notarization. No `com.apple.quarantine` attribute on the installed file (only `com.apple.provenance`).
- `brew uninstall` and `brew untap` removed everything.
