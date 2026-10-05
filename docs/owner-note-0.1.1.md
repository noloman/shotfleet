# What changed in 0.1.1, and why (note for Manu, 2026-10-05)

Plain words, under a page. Nothing here is posted anywhere. Where I know something from a test I say so; where I read it or guess it, I say that too.

## The problem in 0.1.0

0.1.0 was built on this Mac with Homebrew's Python. That has two consequences:

1. **It only starts on a new macOS.** 52 of the 56 program files inside the 0.1.0 download say they need macOS 27.0 or newer (measured on the live tarball by two sessions). The site names no minimum macOS, so a buyer on an older Mac gets a failure and no explanation.
2. **It probably fails even on macOS 26.0 to 26.2.** Python reads XML through a system library called Expat. 0.1.0 needs newer Expat functions than those macOS releases carry. Homebrew's own Python crashed the same way on 26.1 and 26.2 ("Symbol not found: _XML_SetAllocTrackerActivationThreshold"), and Homebrew's advice there was to update to macOS 26.3. shotfleet loads this library the moment it starts, so I expect a crash before the first message. This is read from public reports, **not tested on a real 26.0 to 26.2 Mac**.

So 0.1.0 probably works only on macOS 26.3 and later. Buyers on anything older would have seen it crash. Nobody has reported that yet; there is no evidence either way about real buyers.

## What the fix is

0.1.1 is built with a stand-alone Python (not Homebrew's) and its text-reading helper is built for macOS 13. The Expat library travels inside the download instead of coming from the Mac. On the real 0.1.1 build, the 0.1.1 session measured: 3 program files instead of 56, with minimum macOS 11 to 13 and none at 27; Apple accepted the notarization of both the zip and the pkg; the quarantined run works; `check` on the 72 CrossfitTracker screenshots in 18 languages gives 0 problems; the licence call to Gumroad works from the packaged program.

0.1.1 also carries four earlier fixes (draft PRs #51 to #54):
- **check:** a screenshot the text reader could not read is now "could not read", not a false problem (the Arabic case).
- **capture:** a wedged simulator no longer leaves the others booted, two runs on the same devices no longer steal each other's, and a failed run keeps the results it already had.
- **first run:** a plain `doctor` no longer offers the 600 MB download plan by mistake, and install and `init` messages say what to do next.
- **refunds:** a refunded key is refused with a clear message, and the terms wording now matches the Gumroad page.

## What is still unproven

- **Running on any Mac older than macOS 27.** Nobody has started 0.1.1 (or 0.1.0) on one. One real Mac, or a VM of macOS 13 to 15, would settle it (docs/device-wishlist.md, row 1). A hosted GitHub macOS runner exists for macOS 14 and 15 only, none for 26.0 to 26.2 or 13.
- **A full run on iOS 27**, and the other real-device tests ranked in docs/device-wishlist.md.
- **A refunded key being refused.** It needs a paid sale by a second person (not your own card; Gumroad can suspend an account for that). See docs/refund-runbook.md.
- **A clean Mac with nothing installed**, as a buyer would have it (first-run note).

## What I would do

1. After 0.1.1 is live, add one line to the site and the Gumroad page naming the minimum macOS, once it is measured on a real older Mac.
2. Find one older Mac or VM for the first unproven item; it is the most valuable single test.
3. Decide the few owner items in the refund note (who makes the paid test sale, a postal address, the refund policy after 14 days).

Sources: research/limits-platform-reach-2026-10-05.md, research/limits-first-run-2026-10-05.md, research/limits-capture-reliability-2026-10-05.md, research/limits-check-quality-2026-10-05.md, research/refund-process-2026-10-05.md (all on their draft PR branches until merged).
