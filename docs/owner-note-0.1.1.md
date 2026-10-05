# What changed in 0.1.1, and why (note for Manu, 2026-10-05)

Plain words, one page. Nothing here is posted anywhere. "Measured" means a test; "read" or "expect" means a report or a guess.

## The problem in 0.1.0

0.1.0 was built on this Mac with Homebrew's Python, which has two consequences:

1. **It only starts on a very new macOS.** 52 of the 56 program files in the 0.1.0 download need macOS 27.0 or newer (measured on the live file by two sessions). The site named no minimum, so a buyer on an older Mac would get a failure and no explanation.
2. **It probably fails even on macOS 26.0 to 26.2.** Python reads XML through a system library (Expat), and 0.1.0 needs newer Expat functions than those macOS releases have. Homebrew's own Python crashed the same way on 26.1 and 26.2, and the advice there was to update to 26.3. shotfleet loads it at start-up, so expect a crash before the first message. This is read from public reports, **not tested on a real 26.0 to 26.2 Mac**.

So 0.1.0 probably works only on macOS 26.3 and later. No buyer has reported a crash; there is no evidence either way.

## What 0.1.1 changes

It is built with a stand-alone Python and a text-reading helper built for macOS 13, and Expat travels inside the download. Measured on the real build: program files need macOS 11 to 13, none 27; Apple accepted notarization of the zip and the pkg; the quarantined run works; `check` on 72 CrossfitTracker screenshots in 18 languages gives 0 problems; the Gumroad licence call works from the packaged program. The README and docs now say: "Built for macOS 13 or later on Apple silicon; tested on macOS 27."

It also carries four fixes: `check` no longer calls an unreadable screenshot a problem (the Arabic case); capture cleans up after a stuck simulator, keeps earlier results when a run fails, and two runs no longer steal each other's devices; a plain `doctor` no longer offers the 600 MB download by mistake; and a refunded key is refused with a clear message, with terms wording that matches the Gumroad page.

**Release gate, 2026-10-05, 12:36: PASS.** On the signed standalone build the fixture app passed all 65 assertions on iPhone, iPad and Android (66 PASS lines, 0 FAIL). The iPhone run needed a second attempt for Turkish (`tr`) because the Mac was under heavy load, and it was pinned to iOS 26.4.

## Tested on macOS 14 and 15 (2026-10-05, after the deploy)

Two manual GitHub runs (about $0.25 in all) installed the LIVE 0.1.1 from shotfleet.com on Apple-silicon macOS 14.8.9 and 15.7.9: install, `shotfleet --version` (0.1.1), `doctor` (ran to the end, text recognition ready in 1 s) and `check` on two sample screenshots all worked, with no start-up error. It does not prove simulator runs, Gatekeeper, macOS 13, macOS 26.0 to 26.2, or a clean Mac. One oddity: macOS 14 cannot read Catalan text (check says so), macOS 15 reads it. Details: research/limits-platform-reach-2026-10-05.md.

## iOS 27 and a lesson about memory

On a quiet Mac, iOS 27 with Maestro 2.0.10 captured one language in 78 s with 0 problems. The earlier 35-minute stall was memory thrashing: idle Gradle daemons from several projects held about 21 GB. **Lesson:** idle Gradle daemons can silently fill the memory; `gradle --stop` (once per Gradle version) frees it. A 4-simulator iOS 27 run is untested.

## Still unproven

- **macOS 13 and 26.0 to 26.2, and a real Mac older than 27.** No hosted runner exists for those (docs/device-wishlist.md, row 1).
- A refunded key being refused: needs a paid sale by a second person, not your own card (docs/refund-runbook.md).
- A clean Mac with nothing installed, as a buyer has it.

## What I would do

1. The site and Gumroad page should carry the same macOS line as the README; decide when it goes up.
2. Find one older Mac or a macOS 13 to 15 VM for the first unproven item.
3. Decide the owner items in the refund note: who makes the paid test sale, a postal address, the policy after 14 days.

Sources: research/limits-platform-reach, limits-first-run, limits-capture-reliability, limits-check-quality (all 2026-10-05) and refund-process-2026-10-05, on their draft PR branches until merged.
