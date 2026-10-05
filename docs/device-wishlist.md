# Device and machine wishlist, ranked by value to buyers (2026-10-05)

One list of everything the 2026-10-05 limits notes could not measure without a real machine, device or person. Device slots are scarce (`docs/device-queue.md`: one device job at a time, a hard time limit per step), so the order is by what a buyer would feel, not by how easy the test is. Each row says where the detail is. Nothing here has been run.

Sources (all on origin branches until merged): `research/limits-platform-reach-2026-10-05.md` (platform), `research/limits-capture-reliability-2026-10-05.md` (capture), `research/limits-check-quality-2026-10-05.md` (check), `research/limits-first-run-2026-10-05.md` (first run), `research/refund-process-2026-10-05.md` (refunds).

## A. Needs a machine or a person, no simulator

| # | Test | Why a buyer cares | Cost | Detail |
|---|---|---|---|---|
| 1 | **Older Apple-silicon Mac (macOS 13, 14, 15 or 26), or a VM of one.** Does the 0.1.0 folder start? Does the rebuilt standalone-Python folder (minimum macOS 13) start, run `doctor`, `check` on fixture PNGs, and does the bundled `ocr` read text? Also: `flock` on `/tmp` under the hardened-runtime binary. | Decides who can run shotfleet at all. 0.1.0 needs the macOS it was built on (27.0 for 52 of 56 files) and the site names no minimum. | An older Mac, or a Tart VM (macOS 12+ guests, about 25 GB each) or a manual GitHub runner (macOS 14, 15, 26 at $0.062 per minute, about $2 for four targets). A VM or runner cannot run simulators. | platform note, "How to build 0.1.1+ for older macOS" and "Testing older macOS without an older Mac" |
| 2 | **Clean-Mac outside tester**, two people: Xcode only, no Homebrew, Java, Maestro, Android Studio. Stopwatch and screen recording from the install line to the first PNG; first `doctor` time; `doctor --fix --yes` (350 MB); every dialog and stopping point. Repeat once with Homebrew. Combine with row 1 when the tester's Mac is older. | First impression and refunds. Everything from the first `run` onward on a clean Mac is unverified. | Two people, about an hour each. | first-run note, "What needs a real clean Mac or an outside tester" |
| 3 | **A paid sale by a second person, then a full refund.** Expect `the key was disabled`, or `refunded: true`, at the next check (set `checked` back 8 days). | The only proof that a refunded key is refused. A $0 sale cannot be refunded and the owner paying with their own card breaks Gumroad's rules. | One buyer, about $29, a small fee. Owner action. | refund note, section 7 and 9 |

## B. Needs saved screenshots only (no device slot)

| # | Test | Why a buyer cares | Detail |
|---|---|---|---|
| 4 | Vision versus Tesseract on every saved real-app PNG: how often Tesseract returns nothing or junk where Vision reads fine; planted wrong-language folders (de/nl, es/pt, nb/da, plus two distant pairs) with and without Vision; the blank detector on finished and still-loading frames; "isn't responding" words in real app text; one Nynorsk screenshot. | A false "problem" or a false pass is what a buyer sees in `check`. | check-quality note, "What to measure on real screenshots" |

## C. Needs simulators or emulators (take the device lock, per-step kill limit)

| # | Test | Why a buyer cares | Detail |
|---|---|---|---|
| 5 | **4-simulator iOS run on Maestro 2.0.10 and 2.11.0**: how often one simulator's `bootstatus` wedges, per-shard hang frequency, driver-start timeouts; whether a killed Maestro or adb server really holds the output pipe. | A multi-language run that hangs is the most visible failure. | capture note; platform note (last bullet) |
| 6 | **Real Flutter, Expo and Compose apps end to end, and the Maestro 2.11.0 promotion** (already on `docs/handoff.md`). | Framework coverage is what the site promises. | `docs/handoff.md` sections 1, 3, 5 |
| 7 | **Android emulator details:** `adb emu kill` on a hung emulator and whether the launcher's process tree includes qemu on macOS and Linux; whether `pm clear` keeps the permissions `adb install -g` grants. | Dirty state left after a failed Android run. | capture note |
| 8 | **iOS 27 simulator runtime run**, and Xcode 26.x and Xcode 16 Macs (device type names, the `device_type` fallback). | New OS versions break capture first. | platform note; `docs/handoff.md` |

## D. Rare, later

| # | Test | Detail |
|---|---|---|
| 9 | A Linux machine with 4 or more cores and KVM: two emulators, then an 18-language real app. ARM Linux only to confirm no emulator exists. | platform note |
| 10 | An Intel Mac with Xcode 26 (the note recommends not building Intel now). Android API below 33 for `cmd locale set-app-locales`. Wear OS, TV, foldable, 7" tablet. | platform note, `research/limits-platforms.md` |

## How to use this list

Run row 1 and row 2 together on one older Mac as soon as one is available, because they need no simulator and answer the two questions that block buyers. Row 4 can run on any quiet Mac at any time. Rows 5 to 8 share one device window: take `/tmp/shotfleet-devices.lock`, set a kill limit for each step, and release it when done.
