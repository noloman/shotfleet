# research/ index

One line per note: date, what it decided, whether it was applied. Written 2026-10-05 during the docs refresh (audit `docs-audit-2026-10-05.md`, applied on branch `claude/docs-refresh`). "Applied" below means a change reached the repo; it does not mean it is deployed. A note's own header is the better source for its details.

## Current (2026-10-05)

| Note | Decided / found | Applied? |
|---|---|---|
| `docs-audit-2026-10-05.md` | Audit of README, site, skill and internal docs after 0.1.1: 9 false or stale, 10 missing, 17 internal, 10 owner decisions | Applied on `claude/docs-refresh`. Of the owner items in its section (d) these were approved in chat and applied: D1 (privacy page in the past tense), D3 (the macOS line on the home page and the other pages), D5 (Maestro 2.0.10 next to the timings), D7 (quickstart order). Not changed: terms.html (D2), the licence design (D6), founder price (D8), marketing/, site/draft/ |
| `release-0.1.1-evidence-2026-10-05.md` | What 0.1.1 shipped (build e2e1998, main 2ccda21), gate 65 of 65, smoke 36/0, how to rebuild | Record; STATUS and `docs/handoff.md` section 14 now point to it |
| `0.1.2-plan.md` | Scope, order and risks for 0.1.2 (pipeline A1 to A6, B1 to B4, PR #44 last) | DONE: 0.1.2 is live since 2026-10-05 16:07 (first real `packaging/publish.sh` run, device gate 65 of 65); its "Outcome" section says what shipped and what moved to 0.1.3 (PR #44 not shipped). State: `STATUS.md`, `docs/handoff.md` section 15 |
| `limits-platform-reach-2026-10-05.md` | Which Macs and OS versions can run shotfleet; the standalone-Python build for macOS 13; hosted-runner tests | Applied by 0.1.1 and #55 (build, `tools/macho-minos.py`, the macOS line `Built for macOS 13 or later on Apple silicon; tested on macOS 27.`) |
| `limits-catalan-check-macos-2026-10-05.md` | The wger Catalan screen is judged differently on macOS 14, 15 and 27 | Caveat applied in README and docs (33 languages is the macOS 27 number; Catalan, Croatian, Hungarian judged more weakly) in the docs refresh. Its proposed last sentence about `--app` giving the same answer on every macOS was not used: it is not shown |
| `limits-first-run-2026-10-05.md` | First-run pain from `curl | sh` to the first screenshot; proposed README Quickstart | Messages fixed in 0.1.1. README quickstart reordered in the docs refresh (install, doctor --fix, init, run, then activate; `xcode-select -p` and first-doctor notes), mirrored in docs.html and the skill; the proposed `about 350 MB` figure was not used (not verified) |
| `limits-capture-reliability-2026-10-05.md` | Where a run can hang or leave a mess | Applied in part by 0.1.1 (the CHANGELOG bullet "Capture reliability"); the rest is open or in `0.1.2-plan.md` |
| `limits-check-quality-2026-10-05.md` | False and missed problems in `check` | Applied in part by 0.1.1 (the CHANGELOG bullet "`check` says could not read"); the rest is open |
| `limits-product-improvements-2026-10-05.md` | Ranked product ideas for a paying buyer | Finding 2 applied (#69 free-tier message); the rest is a backlog |
| `limits-release-engineering-2026-10-05.md` | What makes a release repeatable and recoverable | Cited by `0.1.2-plan.md` (what waits and why); not applied |
| `refund-process-2026-10-05.md` | How refunds work on Gumroad and what shotfleet does; the law | Terms wording applied in 0.1.1; the runbook is `docs/refund-runbook.md`. Postal address and consumer-rights lines: NOT applied (owner) |
| `xcode-27-ios27-attempt-2026-10-05.md` | iOS 27: four-simulator e2e inconclusive, one-simulator repro passed in 78 s | Applied in the docs refresh (runtime pin advice, Limits line) |
| `strategy-roadmap-2026-10-05.md` | Five moves to make shotfleet more sellable with 0 sales: proof on the page, `check` as the free front door, an older-macOS and clean-Mac test, 0.1.2 trimmed, a zero-cost Team/CI demand test; day-60 gate 2026-12-04 | Plan and owner decisions; nothing applied. 0.1.2 shipped as the fourth move says (without PR #44) |
| `ga4-investigation-2026-10-05.md` | GA4 shows no data for shotfleet.com: nothing is broken (a clean browser that accepted the banner showed up in Realtime within a minute); the property is empty because of no real traffic yet, the consent gate and the owner's tracker blocker | Read-only; no code fix needed, nothing proposed; the remaining items are the owner's |
| `workarounds-older-macos-2026-10-05.md` | How to get evidence on macOS 13, 26.0 to 26.2 and a clean Mac without owning one: Tart VMs after the release gate (about 65 GB of downloads, needs approval), a volunteer's Mac running a self-test script, a paid Mac mini only as a fallback; a clean-environment run on this Mac already passed | Research; branch `claude/workarounds-older-macos` (self-test in `research/proposed-selftest/`). Not run: no VM, no download. 0.1.3 item |
| `workarounds-reach-distribution-2026-10-05.md` | Ranked reach and distribution items for 0 sales: the Gumroad update line first, versioned immutable download URLs as the prerequisite for a GitHub Action and a Homebrew tap (drafts tested offline), no Intel or Linux work without demand | Research; drafts on branch `claude/workarounds-reach-distribution` (`research/proposed-tap/`, `research/proposed-action/`). Nothing created on GitHub or Homebrew. 0.1.3 item if the owner agrees |
| `workarounds-maestro-resources-2026-10-05.md` | Maestro dependency and Mac resource appetite: measure on a quiet Mac first (2.0.10 took 404 s, 2.11.0 826 s with retries at 4 iOS simulators), capacity planner warn-only, a cheap Maestro watcher plus a deny list | Research; prototype on branch `claude/workarounds-maestro-resources`, not wired. 0.1.3 items |
| `workarounds-text-recognition-2026-10-05.md` | Text recognition was not permanently wedged: cold compiles of the OCR helper by a root `ANECompilerService` take 35 to 122 s under load while shotfleet waits about 60 to 90 s; `usesCPUOnly` and the compute-device APIs do not avoid the compile | Research; proposal in `research/proposed-ocr/` on branch `claude/workarounds-text-recognition`, not applied. Corrects the earlier "needs a reboot" wording (`docs/handoff.md` section 15). 0.1.3 item |
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
