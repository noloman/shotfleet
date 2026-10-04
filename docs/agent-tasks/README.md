# Agent tasks: what could not be done in the cloud sandbox

For the full state of the project at the end of the 2026-10-03 session, read `docs/session-handoff-2026-10-03.md` first.

Each file is a self-contained prompt for a local agent session (Claude Code on your Mac, or a Linux machine for E1) and a record of why the work is still open. Written 2026-10-03.
The cloud session that wrote them had no Mac, no simulator, no hardware virtualization and no way to spend money. Start one with: *read `docs/agent-tasks/<file>` on `main` and do it*.

| # | Task | Machine | Why it is open | Blocks |
|---|---|---|---|---|
| 01 | [Run Maestro 2.11.0 on the fixture apps, then promote it](01-maestro-2-11.md) | Mac | no simulator or emulator in the sandbox | promoting 2.11.0 to tested; Android `[inputs]` |
| 03 | [Capture a real Flutter, Expo and Compose app end to end](03-frameworks-real-apps.md) | Mac | no device; each framework has a build trap | README Flutter/React Native wording |
| 04 | [Verify shotfleet on Xcode 27 final (Device Hub)](04-xcode-27-verification.md) | Mac with Xcode 27 | Device Hub replaced Simulator.app; static analysis only | selling the iOS path |
| 05 | [Run the Android fixture on Linux with KVM (experiment E1)](05-e1-android-on-linux-kvm.md) | Linux with /dev/kvm | sandbox has no hardware virtualization | any Linux support claim |
| 06 | [Run three small experiments: Android UI-tree text, Capacitor language, MAUI sample](06-small-experiments.md) | Mac | need an emulator and simulators | text checks on Android; Capacitor and MAUI claims |
| 07 | [Verify and tick the launch articles' TO VERIFY lists](07-verify-the-launch-articles.md) | Mac | TO VERIFY items need real runs | publishing the tutorials the launch plan relies on |

## Not agent work (Manu)

- **A real purchase and refund against the live Gumroad product** (`STATUS.md` gate 5; `tools/release-candidate.sh` is the harness). An agent cannot spend money.
- **Tax and registration question** (`research/tax-nl-2026-10.md`), **go-live approval**, **a clean macOS user and 2 to 3 outside developers for the cold test**, **publishing and posting** everything in `marketing/`.
- **Decisions** listed at the end of `research/profit-plan-2026-10-03.md` section 9.
- **Team and CI interest block on the site.** Proposed, not added, because the site has WAITLIST/SALE markup that `packaging/go-live.sh` rewrites and the wording is a pricing decision. Proposed copy for the pricing section, to go in after the licence card: *Running shotfleet in CI for a team? A per-repository plan (about $149 a year) is an idea, not a product. Tell me what you would check there: hello@shotfleet.com.* Measure replies and count them against the thresholds in the profit plan section 7.

## E1 state

- E1 ran six times on a GitHub-hosted runner (Actions allowed once, now used up). It did not pass: Maestro cannot find the localized "Next" button after the first screenshot, with one emulator as with two. The artifact of run 37138279362 holds the screenshot and Maestro logs; only Manu can download it. See `docs/linux.md` and `docs/session-handoff-2026-10-03.md`.

## How to start one

1. Pick a file; 2. start a local session in the repository on `main`; 3. paste: *read `docs/agent-tasks/<file>` and do it*; 4. review the draft PR it opens.
