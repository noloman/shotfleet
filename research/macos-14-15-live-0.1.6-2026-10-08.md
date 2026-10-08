# Live 0.1.6 on macOS 14 and 15 (2026-10-08)

One manual dispatch of `.github/workflows/macos-compat.yml` (run 37741184849, started 2026-10-08 07:04 UTC, about $0.25 of runner minutes, approved by Manu for this weekend's promotion). It installs from the LIVE https://shotfleet.com/install.sh into a temporary HOME on GitHub's Apple-silicon runners and runs `--version`, `doctor` and `check` on two sample screenshots.

| Image | macOS | install.sh | `--version` | `doctor` | text recognition | `check` (2 sample PNGs) |
|---|---|---|---|---|---|---|
| macos-14 | 14.8.9 | ok | `shotfleet 0.1.6` | ran to the end (Maestro missing, as expected on a bare runner) | ready | ran, no crash |
| macos-15 | 15.7.9 | ok | `shotfleet 0.1.6` | ran to the end | ready in 1 s | ran, no crash (3 problem(s) reported on the two arbitrary samples, which is the point of the check) |

Both jobs concluded `success`.

What this adds: the evidence for macOS 14 and 15 in `docs/compat.md` was for the 0.1.1 build; this is the build customers get now (0.1.6, the live bytes).

Still not covered (no hosted runner exists, or a runner cannot do it): macOS 13 and 26.0/26.1, simulators and emulators, Gatekeeper on a browser-downloaded file (curl sets no quarantine; the quarantined first run was checked separately on 2026-10-08 with `tools/verify-release.sh` on the live tarball: signed, hardened runtime, runs), and a real buyer's Mac.

`docs/compat.md` row 50 still says "0.1.1, not 0.1.2"; update it to point here in the post-weekend docs pass (main is frozen outside `research/` until Manu's go).
