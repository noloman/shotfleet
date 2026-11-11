# How shotfleet gets to buyers

> **Update, 2026-11-11:** shotfleet is now free and open source (MIT), funded through GitHub Sponsors. The license check, `shotfleet activate`, the price, the free tier, refunds and the Gumroad product were removed (versions up to 0.1.10 were sold). Wherever this document describes them, it describes the paid period and no longer applies; `LICENSE`, `README.md` and `CHANGELOG.md` are current.

> History: written before the sale opened. The sale has been live since 2026-10-05, so the waitlist wording below (for example the waitlist as the only list to email) describes the pre-sale state.

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
| Install | `curl -fsSL https://shotfleet.com/install.sh \| sh` (checksum-verified), the main way. Also a Homebrew cask in the public tap `noloman/homebrew-tap`: `brew install noloman/tap/shotfleet` (same tarball, from `/download/<version>/`) | One line, no public repos needed (Homebrew was the first plan; see Status) |
| Where binaries live | The shotfleet site's `/download` folder (no public source repo; source stays private; the empty `noloman/shotfleet-releases` is reserved for a later Action, tap and plugin) | The installer reads it over HTTPS and checks the SHA-256 |
| Payment | Gumroad product linked from the site (merchant of record since 2025-01-01: handles VAT/sales tax worldwide, added on top of the price; Individual account, Netherlands bank payout; the same account sells Keysi) | Lemon Squeezy and Polar end in a Stripe check that asks for a KvK (none here; dropped 2026-10-02). Gumroad: 10% + $0.50 plus card 2.9% + $0.30, so about $24.46 net at $29 (research/gumroad-setup.md) |
| Licence | `shotfleet activate <key>` validates once with the store's licence API (Gumroad keys: four groups of 8 hex characters, no secret in the app, one use count per key, 5 activations: 3 Macs plus 2 spare for reinstalls; a key from any other store is refused, with no network call), stores it in `~/Library/Application Support/shotfleet`, re-checks at most weekly, works offline for 30 days (an activated Mac; a CI key only on a machine where it passed a check in the last 30 days, see CI below) | Honest buyers never notice; casual sharing stops |
| Free vs paid | `check`, `doctor`, `init` free; `run` free up to 2 languages; every language and `export` need a key | STRATEGY.md 2.1: checking is the funnel |
| Updates | `shotfleet doctor` mentions a newer release (read from the site's `/download/VERSION`; `--version` makes no network call); re-running `install.sh` installs it | A year of updates is part of the $49: a key covers every version released within a year of the purchase (the same date a year later) (the build's baked-in release date against Gumroad's sale date); later versions run as the free tier |
| CI | Same binary; key passed as `SHOTFLEET_KEY`, checked online on each run, no activation used. With Gumroad unreachable it counts as licensed only on a machine where that key passed a check in the last 30 days (a hash of the key and the date are noted); otherwise it is refused (changed in 0.1.6, owner decision 2026-10-06) | A made-up key no longer works just by blocking Gumroad; it takes forging a file too. Team licence later |

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
| Gumroad product ($49, `FOUNDER29` $20 off for the first 100, applied automatically, License key block on the Content page, 14-day refund policy) and the payout review (research/gumroad-setup.md section 6, LAUNCH.md) | Manu | 30 min plus review |
| `noloman/homebrew-shotfleet` and `noloman/shotfleet-releases` public repos | Manu creates, Claude fills | 10 min |
| Release script: build, sign, notarize, upload, update the tap formula | Claude | ~half a day |
| Site: buy button, install instructions, licence/refund terms | Claude drafts, Manu approves | ~half a day |

Only needed once the founder sale opens (STRATEGY.md week 4). Until then the waitlist is enough.

## Status (2026-10-01)
- **Owner decision 2026-10-05:** the public GitHub repo `noloman/shotfleet-releases` exists and is empty. It is kept for later, to hold only a GitHub Action, a Homebrew tap and a fastlane plugin, plus release downloads if ever needed. The core program stays closed source in the private repo, and nothing is published there today. `noloman/homebrew-shotfleet` is not created.
- Decision: the program is not published in a public repo. The signed, notarized program is served from the shotfleet site; buyers install with
  `curl -fsSL https://shotfleet.com/install.sh | sh` (checksum-verified; installs on the PATH).
  `doctor` announces newer versions from `/download/VERSION`. A Homebrew formula was tried through a local tap and
  removed in 0.1.2 (it was stale). 2026-10-06: published as a cask (Homebrew's docs put proprietary binary-only software in casks) in
  `noloman/homebrew-tap`, pointing at the immutable `/download/<version>/` tarball; `tools/bump-homebrew.sh <version> <tap checkout>` updates it per release.
- Signing and notarization: done with the existing Developer ID (2357A78TMR) and the `KeysiNotary` profile (shotfleet's own `ShotfleetNotary` from 2026-10-05; "not found" usually means the screen locked, see packaging/README.md). Apple accepted
  the 0.1.0 build; a quarantined copy runs without a Gatekeeper prompt.
- Licence: `activate`/`deactivate`, `run`/`export` gated in released builds only; tested against a fake Gumroad licence API
  (the earlier Lemon Squeezy path was removed 2026-10-03).
- Apple silicon only for now (Intel needs a universal2 Python for the build).
- Folder build, not one file: starts in ~0.1 s instead of ~1.2 s (the one-file build unpacked itself on every launch;
  measured 5 runs each). install.sh puts the folder in ~/Library/Application Support/shotfleet/app and links the
  command onto the PATH. Every binary is re-signed (PyInstaller's own signing of Homebrew's Python framework was
  rejected by Apple's notary); notarization accepted, quarantined install tested.
- Gumroad is the store: its licence keys count activations (5 per key, for 3 Macs plus reinstalls; a refused attempt and a repeat on the same Mac count
  nothing; `deactivate` cannot give one back, so a sixth activation means an email); refunds, chargebacks and disputes are
  refused; weekly re-checks and CI keys don't count; a Gumroad outage is not a verdict. Tested against a fake API built from Gumroad's help pages and source.
- Left for Manu: create the Gumroad product and give the product URL and ID (LAUNCH.md). Then `packaging/go-live.sh`.
- Go-live is rehearsed before it is run: `packaging/go-live.sh --dry-run <product URL> <product ID>` does every step on a copy,
  `tools/golive/storefront.sh <product URL> <product ID>` reads the live Gumroad product (published, licence keys on, refund policy)
  and `tools/golive/smoke.sh https://shotfleet.com <product URL>` checks the live site afterwards, both tested offline
  (tests/test_golive.py). Order of steps: LAUNCH.md.
