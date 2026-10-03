# Verify and tick the launch articles' TO VERIFY lists

**Needs:** your Mac, Xcode, fastlane, Maestro, an Android emulator; the released installer if `/download/VERSION` answers 200.

## Context

Three article drafts are ready in `marketing/articles/` (01 fastlane snapshot stuck in English, 02 one Maestro flow in every locale, 03 the button nobody could reach). They are not published because their `TO VERIFY BEFORE PUBLISHING` lists have unticked items: `tools/build-guides.py` refuses to publish an article until each item says TICKED. They are the tutorials the launch plan relies on (`research/profit-plan-2026-10-03.md` section 6). Do not publish anything; Manu posts.

## Steps

For each unticked item in articles 01, 02 and 03: do what it says (run the command, reproduce the cause, re-time the claim, open the linked issues) and edit the article to match what you saw. Add `TICKED <date> (<what you ran>)` to the item only when you ran it; otherwise leave it and say why. Fix any sentence the run contradicts. Items needing the live installer wait if `https://shotfleet.com/download/VERSION` still returns 404. Item 1 of article 03 (the public app name: WOD Tracker or CrossfitTracker) is Manu's decision: list the options, do not choose. Then draft article 04 from `marketing/articles/04-ideas.md` only if its claims can be run the same way.

## Passed when

`python3 tools/build-guides.py` lists which articles are now verified; the ones whose items are all ticked are publishable.

## Record

The articles themselves (the TO VERIFY lists), `STATUS.md` row 15.

## Rules for every task in this folder

- Work on a new branch off `main`; open a **draft** PR with the evidence (commands, versions, counts, times). Do not merge it.
- Every commit and merge message ends with `[skip ci]`. This repo's checks run locally: run `tools/check-claims.sh` before committing; it must end `ok`.
- Nothing is called tested, proven or supported without a run that passed. If a run fails, change no claim, write what failed (command, log lines) in the file named under "Record", and stop.
- Downloads: the first message of your session lists each download (file, source, size) and waits for no one, but never exceeds what the task lists. No `sudo`. Do not touch `~/.maestro` or other installs: use scratch folders.
- Keep the Mac quiet: no other session using simulators or emulators (`xcrun simctl list devices booted`, `adb devices`), at least 30 GB free. If not, stop and say so.
- Commits end with: `Co-Authored-By: <the model that wrote it>` and the session link, as the harness instructs.
