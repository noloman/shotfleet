# research/ index

One line per note: date, what it decided, whether it was applied. Written 2026-10-05 during the docs refresh (audit `docs-audit-2026-10-05.md`, applied on branch `claude/docs-refresh`). "Applied" below means a change reached the repo; it does not mean it is deployed. A note's own header is the better source for its details.

## Current (2026-10-05)

| Note | Decided / found | Applied? |
|---|---|---|
| `docs-audit-2026-10-05.md` | Audit of README, site, skill and internal docs after 0.1.1: 9 false or stale, 10 missing, 17 internal, 10 owner decisions | Applied on `claude/docs-refresh` except what the owner has not approved (see that branch's commits); the owner items it lists in section (d) are decided in chat |
| `release-0.1.1-evidence-2026-10-05.md` | What 0.1.1 shipped (build e2e1998, main 2ccda21), gate 65 of 65, smoke 36/0, how to rebuild | Record; STATUS and `docs/handoff.md` section 14 now point to it |
| `0.1.2-plan.md` | Scope, order and risks for 0.1.2 (pipeline A1 to A6, B1 to B4, PR #44 last) | Plan. B1 (`--json` over every report) done in #68; B2 half done (#69 is wording; an invalid key still runs 2 languages) |
| `limits-platform-reach-2026-10-05.md` | Which Macs and OS versions can run shotfleet; the standalone-Python build for macOS 13; hosted-runner tests | Applied by 0.1.1 and #55 (build, `tools/macho-minos.py`, the macOS line `Built for macOS 13 or later on Apple silicon; tested on macOS 27.`) |
| `limits-catalan-check-macos-2026-10-05.md` | The wger Catalan screen is judged differently on macOS 14, 15 and 27 | Caveat applied in README and docs (33 languages is the macOS 27 number; Catalan, Croatian, Hungarian judged more weakly) in the docs refresh. Its proposed last sentence about `--app` giving the same answer on every macOS was not used: it is not shown |
| `limits-first-run-2026-10-05.md` | First-run pain from `curl | sh` to the first screenshot; proposed README Quickstart | Messages fixed in 0.1.1. README quickstart: see the docs refresh branch (owner approved the reorder after the audit) |
| `limits-capture-reliability-2026-10-05.md` | Where a run can hang or leave a mess | Applied in part by 0.1.1 (the CHANGELOG bullet "Capture reliability"); the rest is open or in `0.1.2-plan.md` |
| `limits-check-quality-2026-10-05.md` | False and missed problems in `check` | Applied in part by 0.1.1 (the CHANGELOG bullet "`check` says could not read"); the rest is open |
| `limits-product-improvements-2026-10-05.md` | Ranked product ideas for a paying buyer | Finding 2 applied (#69 free-tier message); the rest is a backlog |
| `limits-release-engineering-2026-10-05.md` | What makes a release repeatable and recoverable | Cited by `0.1.2-plan.md` (what waits and why); not applied |
| `refund-process-2026-10-05.md` | How refunds work on Gumroad and what shotfleet does; the law | Terms wording applied in 0.1.1; the runbook is `docs/refund-runbook.md`. Postal address and consumer-rights lines: NOT applied (owner) |
| `xcode-27-ios27-attempt-2026-10-05.md` | iOS 27: four-simulator e2e inconclusive, one-simulator repro passed in 78 s | Applied in the docs refresh (runtime pin advice, Limits line) |
| `resume-limits-catalan-check.md` | Another session's resume file for the Catalan note | Leftover; the note it describes exists. Not edited here |

## Earlier notes (history; statuses are in each file)

| Note | Date | Subject |
|---|---|---|
| `go-live-gate.md` | 2026-10-03 | Evidence per gate before 0.1.0 went live (updated 2026-10-05) |
| `gumroad-setup.md` | 2026-10-02 | Why and how shotfleet sells through Gumroad |
| `tax-nl-2026-10.md` | 2026-10-03 | Dutch registration and VAT for the sales; owner task |
| `profit-plan-2026-10-03.md` | 2026-10-03 | What would make the product more complete and profitable |
| `maestro-2-11.md` | 2026-10-04 | Maestro 2.11.0: failed first, fixed, now tested |
| `frameworks.md` | 2026-10-05 | Framework support and the real-app runs (wger, obytes, kotlinconf-app, Rocket.Chat) |
| `real-apps.md` | 2026-10-01 | First real-app runs |
| `limits-text.md` | 2026-10-04 | Hierarchy text, typed text and `launchApp` options |
| `limits-platforms.md` | 2026-10-02 | Platform limits (macOS only, Android phone only, API 33+) |
| `e2-tesseract-parity.md` | 2026-10-03 | `check` on Tesseract alone against macOS text recognition |
| `release-candidate.md` | 2026-10-02 | The frozen program tested without network accounts |
| `review-2026-10-03.md` | 2026-10-03 | Code review of `shotfleet.py` and `ocr.swift` |
| `sellable-audit.md` | 2026-10-02 | Evidence behind STATUS, gate by gate |
| `claims-audit.md` | 2026-10-02 | Public claims audit; the register is `tests/claims.json` |
| `cold-test-2.md` | 2026-10-02 | A new buyer with only the README and the binary |
| `first-run.md` | 2026-10-01 | First-run findings from the buyer's view |
| `setup-friction.md` | 2026-10-02 | Zero to first screenshot, and extension points |
| `audit.md` | 2026-10-01 | First code and README audit |
| `content-control.md` | 2026-10-02 | Can shotfleet decide what the app shows (screenshot mode, `[expect]`) |
| `all-languages.md` | 2026-10-01 | Supporting all languages and localization setups |
| `store-specs.md` | 2026-10-01 | Store screenshot specifications, raw page text |
| `roadmap-2026-10.md` | 2026-10-02 | Plan for the first sale and the 60 days after |
| `pricing-2026-10.md` | 2026-10-02 | Functionality, competitors and price |
| `market-2026.md`, `marketing-research.md` | 2026-10-01, 2026-10-02 | Market and channel research |
| `web-service.md`, `website-localization.md` | 2026-10-02 | Two ideas not pursued: a credits website, a localized site (later, not now) |
| `seo-audit.md`, `site-critique.md`, `site-critique-2.md` | 2026-10-02, 2026-10-03 | Site audits; status tables inside |
| `ga-setup.md` | 2026-10-02 | GA4 setup for shotfleet.com |

Folders: `experiments-2026-10-04/`, `proposed-platform-reach/` (the proposed macOS 13 patch, merged through #55), `real-apps-2026-10-03/`, `real-apps-2026-10-04/`, `real-apps-2026-10-05/` (screenshots and logs behind `frameworks.md` and the claims register).
