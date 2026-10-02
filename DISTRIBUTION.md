# How shotfleet gets to buyers

## What a buyer's Mac has today (measured 2026-10-01)

- `/usr/bin/python3` is **3.9.6**. shotfleet needs 3.11+ (`tomllib`), so `python3 shotfleet.py` fails out of the box
  unless the buyer installed a newer Python with Homebrew.
- The `check` step compiles `ocr.swift` with `swiftc` on first use. iOS developers have it (Xcode). Android-only developers
  may only have the Command Line Tools, or nothing.
- So "download a .py file" is not good enough for a paid product: two of the first-run failures are ours, not theirs.

## Recommendation

**One signed, notarized Apple silicon program, installed with a one-line `curl` script, unlocked with a licence key.**

| Piece | Choice | Why |
|---|---|---|
| Package | A single executable built with PyInstaller (Python bundled), plus the prebuilt `ocr` helper, Apple silicon only (arm64) | No Python or Swift needed on the buyer's Mac; source not shipped as plain text |
| Trust | Signed with Manu's Developer ID and notarized by Apple | Without it Gatekeeper blocks the download ("cannot be opened") |
| Install | `curl -fsSL https://shotfleet.com/install.sh \| sh` (checksum-verified). No Homebrew formula is published | One line, no public repos needed (Homebrew was the first plan; see Status) |
| Where binaries live | The shotfleet site's `/download` folder (no public repos; source stays private) | The installer reads it over HTTPS and checks the SHA-256 |
| Payment | Polar checkout from the site (merchant of record: handles VAT/sales tax worldwide; personal accounts allowed, Netherlands supported; ID check through Stripe) | Lemon Squeezy asks for a KvK (none here). Polar Starter: 5% + $0.50, +1.5% international cards, Stripe payout fees |
| Licence | `shotfleet activate <key>` validates once with the store's licence API (Polar: SHOTFLEET- keys, no secret in the app; Gumroad and Lemon Squeezy keys still work), stores it in `~/Library/Application Support/shotfleet`, re-checks at most weekly, works offline for 30 days | Honest buyers never notice; casual sharing stops |
| Free vs paid | `check`, `doctor`, `init` free; `run` free up to 2 languages; every language and `export` need a key | STRATEGY.md 2.1: checking is the funnel |
| Updates | `shotfleet doctor` mentions a newer release (read from the site's `/download/VERSION`; `--version` makes no network call); re-running `install.sh` installs it | A year of updates is part of the $49 |
| CI | Same binary; key passed as `SHOTFLEET_KEY` | Team licence later |

A licence check in a Python app can be removed by a determined person. At $29–49 that's acceptable: the goal is to make
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
| Polar account (personal, ID check; review up to 14 days) + product ($49, `FOUNDER29` $29 code for the first 100) + a License Key benefit: done except the review (LAUNCH.md) | Manu | 30 min plus review |
| `noloman/homebrew-shotfleet` and `noloman/shotfleet-releases` public repos | Manu creates, Claude fills | 10 min |
| Release script: build, sign, notarize, upload, update the tap formula | Claude | ~half a day |
| Site: buy button, install instructions, licence/refund terms | Claude drafts, Manu approves | ~half a day |

Only needed once the founder sale opens (STRATEGY.md week 4). Until then the waitlist is enough.

## Status (2026-10-01)
- Decision: no public repos. The signed, notarized program is served from the shotfleet site; buyers install with
  `curl -fsSL https://shotfleet.com/install.sh | sh` (checksum-verified; installs on the PATH).
  `doctor` announces newer versions from `/download/VERSION`. The Homebrew formula (packaging/shotfleet.rb) is kept
  for later if buyers ask for `brew install`; it was tested through a local tap.
- Signing and notarization: done with the existing Developer ID (2357A78TMR) and `KeysiNotary` profile. Apple accepted
  the 0.1.0 build; a quarantined copy runs without a Gatekeeper prompt.
- Licence: `activate`/`deactivate`, `run`/`export` gated in released builds only; tested against a fake licence API,
  and the real Lemon Squeezy API rejects unknown keys correctly.
- Apple silicon only for now (Intel needs a universal2 Python for the build).
- Folder build, not one file: starts in ~0.1 s instead of ~1.2 s (the one-file build unpacked itself on every launch;
  measured 5 runs each). install.sh puts the folder in ~/Library/Application Support/shotfleet/app and links the
  command onto the PATH. Every binary is re-signed (PyInstaller's own signing of Homebrew's Python framework was
  rejected by Apple's notary); notarization accepted, quarantined install tested.
- Gumroad as a second store: its licence keys work too (activation counts uses, at most 3 Macs; refunds and
  chargebacks are refused; weekly re-checks don't count). Tested against a fake API built from Gumroad's source.
- Left for Manu: finish the Polar account review and make the checkout link (LAUNCH.md). Then `packaging/go-live.sh`.
