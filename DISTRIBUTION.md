# How shotfleet gets to buyers

## What a buyer's Mac has today (measured 2026-10-01)

- `/usr/bin/python3` is **3.9.6**. shotfleet needs 3.11+ (`tomllib`), so `python3 shotfleet.py` fails out of the box
  unless the buyer installed a newer Python with Homebrew.
- The `check` step compiles `ocr.swift` with `swiftc` on first use. iOS developers have it (Xcode). Android-only developers
  may only have the Command Line Tools, or nothing.
- So "download a .py file" is not good enough for a paid product: two of the first-run failures are ours, not theirs.

## Recommendation

**One signed, notarized, universal binary, installed with Homebrew or a download, unlocked with a licence key.**

| Piece | Choice | Why |
|---|---|---|
| Package | A single executable built with PyInstaller (Python bundled), plus the prebuilt `ocr` helper, universal (Apple silicon + Intel) | No Python or Swift needed on the buyer's Mac; source not shipped as plain text |
| Trust | Signed with Manu's Developer ID and notarized by Apple | Without it Gatekeeper blocks the download ("cannot be opened") |
| Install | `brew install noloman/shotfleet/shotfleet` and a `.tar.gz` / `.pkg` on the download page | Homebrew is how Mac developers install CLIs; the tap is one small public repo |
| Where binaries live | A public `noloman/shotfleet-releases` repo (binaries + changelog only); source stays in the private `noloman/shotfleet` | Homebrew needs a public URL; nothing paid is exposed because the binary needs a key |
| Payment | Lemon Squeezy checkout from the site (merchant of record: handles VAT/sales tax worldwide) | Already in the plan; one fee, no tax paperwork |
| Licence | `shotfleet activate <key>` validates once with Lemon Squeezy's licence API, stores it in `~/Library/Application Support/shotfleet`, re-checks at most weekly, works offline for 30 days | Honest buyers never notice; casual sharing stops |
| Free vs paid | `check`, `doctor`, `init` free; `run` and `export` need a key | STRATEGY.md 2.1: checking is the funnel |
| Updates | `shotfleet --version` / `doctor` mention a newer release (GitHub releases API); `brew upgrade` installs it | A year of updates is part of the $79 |
| CI | Same binary; key passed as `SHOTFLEET_KEY` | Team licence later |

A licence check in a Python app can be removed by a determined person. At $49–79 that's acceptable: the goal is to make
paying the easy path, not to win against crackers.

## Alternatives considered

- **pip / pipx package.** Developer-friendly, but needs Python 3.11+ (most Macs don't have it) and ships readable source.
  Fine for an open-source/free tier, not for the paid tool.
- **Mac App Store app.** Sandboxing blocks driving simulators, emulators and Maestro. Not possible.
- **Web service (upload screenshots, we check them).** Possible for `check` only, but needs servers and handles people's
  unreleased app screenshots. Not worth it for a few $k/year.
- **Source + licence on the honour system.** Simplest, but the Python 3.9 problem remains.

## What it takes (and who)

| Step | Who | Effort |
|---|---|---|
| PyInstaller build script + universal `ocr` binary, `activate` command, key check, free/paid split, tests | Claude | ~1 day |
| Developer ID certificate (needs the Apple Developer account) and an app-specific password for notarization | Manu | 15 min |
| Lemon Squeezy store + product ($79, $49 founder discount code) + licence keys enabled; API key | Manu | 30 min |
| `noloman/homebrew-shotfleet` and `noloman/shotfleet-releases` public repos | Manu creates, Claude fills | 10 min |
| Release script: build, sign, notarize, upload, update the tap formula | Claude | ~half a day |
| Site: buy button, install instructions, licence/refund terms | Claude drafts, Manu approves | ~half a day |

Only needed once the founder sale opens (STRATEGY.md week 4). Until then the waitlist is enough.

## Status (2026-10-01)
- Done and tested: `packaging/build.sh` (one 9 MB executable with the OCR helper; no Python or Swift needed),
  `activate`/`deactivate`, licence gate on `run`/`export` (released builds only; tested against a fake Lemon Squeezy API,
  and the real API answers unknown keys correctly), `doctor` update notice, Homebrew formula (installed, tested and
  removed through a local tap), `packaging/release.sh`.
- Apple silicon only for now: Intel needs a universal2 Python (python.org installer) for the build.
- Signing/notarization steps are in build.sh but untested until Manu's Developer ID exists.
- Startup takes ~1 s+ (one-file build unpacks itself each run; 6 s measured on an overloaded Mac). Re-measure when idle;
  switch to a folder build if it's slow.
- Waiting on Manu: Lemon Squeezy store/product with licence keys, Developer ID + notary profile,
  `noloman/homebrew-shotfleet` and `noloman/shotfleet-releases` repos. Then `packaging/release.sh`.
