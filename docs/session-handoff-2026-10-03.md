# Handoff: end of the 2026-10-03 cloud session

Read this first if you are an agent picking the project up. Written at the end of a long cloud session (Linux container, no Mac, no device). `STATUS.md` is the living gate table; this file says what changed, what is proven, and what is open, with the exact next step for each.

## Rules that still apply (from `STATUS.md`)

- Local checks are the gate: `tools/check-claims.sh`. Check its **exit code** (`> /tmp/gate.out 2>&1; echo $?`), never through a pipe to `tail`.
- No GitHub Actions. The one exception (the E1 KVM experiment) is used up; `e1-android-kvm.yml`, `maestro-latest.yml` and `apple-specs.yml` are manual-only. `ci.yml` still runs on every push (Linux Python 3.11/3.13, macOS 3.12): Manu has not decided whether to keep the 3.13 job.
- `[skip ci]` in every commit and merge message. Every download needs Manu's OK (file, source, size).
- Nothing is called tested or proven without a passing real run or test. Do not claim Linux `run` support, a Maestro 2.11.0 device run, Xcode 27 `run`, Mac `doctor --fix`, or Flutter/React Native/MAUI real-app runs: none has happened.
- Never use sudo in product code. Do not touch the user's installs. Commits end with `Co-Authored-By: Claude ... <noreply@anthropic.com>` and a `Claude-Session:` line.

## State of `main`

All work from the session is merged (PRs #11, #14, #16 to #22, #24 to #27). Gate on `main`: 788 tests (41 skipped as Mac-only) plus 59 worker checks, exit 0; same suite on Python 3.11. Claims register: 126 claims, 57 proven, 17 fixed, 52 not green (24 evidence, 19 partial, 5 unverifiable, 2 untested, 2 removed).

What shipped this session:

| Area | What |
|---|---|
| `doctor --fix` | Downloads pinned Maestro (SHA-256), Temurin 21 and Google's Android tools, one question, never sudo. Works with Google's new Android CLI (`sdkmanager` is a deprecated shim): SDK paths are cleaned (`..` is refused by the new tool) and installs go through `android --no-metrics --sdk=ROOT sdk install`. |
| Android emulator failures | Emulator output kept in `<tmp>/shotfleet-emulator-logs/`; a dead emulator fails at once with exit code and log tail instead of looking like a 600 s hang; a full disk (needs 12 GB free) and a missing `/dev/kvm` are named with their fix. The phrase "emulators did not boot in time" is kept on purpose (the skill's troubleshooting guide quotes it). |
| Compatibility | `tools/maestro-compat.py` (28 static checks; 2.0.10 and 2.11.0 pass), `tools/latest-maestro.py`, `tools/apple-specs-watch.py`, `tools/watch-upstream.sh` (run monthly and before a release), `tools/pretend-mac.py`. `docs/compat.md` is the table of what was checked and how. |
| `check` | Knows the iPhone Duo sizes and four old-device landscape sizes (found by the Apple spec watcher). |
| First-run fixes (#25) | Wrong builds, locale names, missing Xcode runtime, `init` keeps your config; config refuses `parallel`/`timeout_s` below 1 and an empty `locales`. Config validation lives in `check_section`. Covered by tests only, not run on a Mac. |
| Licence | Polar code removed (#27): Gumroad is the only store. Lemon Squeezy code was removed afterwards on `main` as well (see `STATUS.md`, claim C093). |
| Site (#20, #21) | 25 of 29 critique items and 6 of 17 SEO items fixed, CSP without `unsafe-inline`, contrast and touch targets, no-JS privacy forms, 53 audit tests, Chromium checks. |
| Docs (#24, #22) | Documents corrected to match the program; old $79 plan marked superseded in `marketing/`; guide links that 404 flagged in `marketing/kit/README.md`. |
| Tests | `test_claims_unit.py`, `test_claims_site.py` (+ `browser_site.cjs`), `test_first_run.py`, `test_site_audit.py`, `test_doctor_fix.py`, `test_handoff_docs.py` (every path named in the docs must exist). |

## E1 (Android `run` on Linux with KVM): answered after this session was archived

Update, written afterwards from the repository: the answer came in on `main` (PR #33, see `docs/linux.md` and `STATUS.md`). The screenshots of the failed runs (the run 37138279362 artifact) show Android's "System UI isn't responding" dialog over the app, with the localized button ("Weiter") visible underneath: the language switch worked, the dialog blocked Maestro's tap, and the 2-core runner is why it appeared. Emulators now hide error dialogs and turn animations off at boot, `check` reports a system dialog on a screenshot as a problem (before, it said 0 problems on those screenshots), and `run` picks the emulator count from cores and memory on Linux. Result: the fixture e2e PASSED with ONE emulator on a 2-core GitHub runner (13 of 13 assertions). Still unproven: two emulators, a machine with 4+ cores, the 18-language timing and a real app. Do not claim Linux `run` support beyond that. `docs/agent-tasks/05` is the follow-up.

## Open work, by who can do it

**Manu only**
- Delete the remote branch `e1-kvm-run` (the remote refused deletion from the cloud). Merged PR branches can be deleted too. Decide on the Python 3.13 job in `ci.yml`.
- Money and launch: Gumroad test purchase and publish (gate 1/3), one real key end to end: activate, refund, refused (gate 5; harness `tools/release-candidate.sh`), the Dutch tax/KvK question (`research/tax-nl-2026-10.md`), go-live (`packaging/go-live.sh --dry-run <url> <id>` first), clean-Mac cold test with 2 to 3 outside developers, posting everything in `marketing/`.
- Site: www to apex redirect, "Licence" vs "license", AI-crawler `robots.txt` choice, Search Console and Bing, HSTS, a live PageSpeed run, publish or drop the guide drafts in `site/draft/guides/` (the Google Play guide has no draft yet).
- Confirm "joining the list does not reserve the launch price" is the intent. Re-run `check` on the real screenshots before launch to confirm the "108 of 120" figure (claim C107).
- Strategy decisions at the end of `research/profit-plan-2026-10-03.md` (launch first vs build, open vs closed core, a $149 done-for-you offer). Cleanup: `marketing/launch-posts.md` is superseded by `launch-posts-v2.md`; `site/draft/alternatives.html` has diverged from the published page on purpose (a test pins that).

**A local agent on a Mac** (prompts are ready in `docs/agent-tasks/01` to `07`): Maestro 2.11.0 on the fixture apps then promote it (new `MAESTRO_DEVICE_UDID` may fix Android `[inputs]`); `doctor --fix` on a real Mac and the real-app regression; Flutter (wger), Expo, Compose, MAUI real apps; Xcode 27 final with Device Hub; small experiments; ticking the launch articles' TO VERIFY lists. Also: run the first-run fixes (#25) and the licence change (#27) on a Mac before release; the macOS-only paths are untested.

**A Linux machine with KVM**: `docs/agent-tasks/05`.

**Any agent, no device needed**
- The remaining 52 claims need real runs, third-party pages or Manu's settings; reword the ones that cannot be proven instead of leaving them (`research/claims-audit.md`).
- Site items still open: zoom prev/next, fingerprinted caching, `/llms-full.txt`, WebP, the guides, a header join button on `/alternatives`.
- Review findings status: `research/review-2026-10-03.md`. Run `tools/watch-upstream.sh` before any release.

## Where things are

`STATUS.md` (gates, risks, plan), `docs/handoff.md` (items 1 to 12, how to promote a Maestro version, etc.), `docs/compat.md`, `docs/linux.md`, `docs/agent-tasks/`, `research/profit-plan-2026-10-03.md`, `tests/claims.json` (register), `CHANGELOG.md`.

## Process notes that cost time this session

- Parallel agents branched from an old `main`; each needed a merge, with `CHANGELOG.md` and `STATUS.md` conflicts every time. Tell agents to merge latest `main` before reporting, and to leave `STATUS.md` counts to the integrator.
- `/tmp/gate.out` is shared between sessions; use your own file and trust the exit code.
- A subagent can stop without a final report; check its branch (`git log origin/main..<branch>`) rather than waiting.
- Validate YAML before pushing a workflow; do not chain with `;`.
