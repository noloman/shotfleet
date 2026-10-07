# Kuokka dogfood re-run, 2026-10-07

- App: Kuokka (me.manulorenzo.kuokka), Manu's Hacker News reader. Debug simulator build 2.0.14 (289) built 2026-10-05 15:07 from the branch review-prompt-redesign (commit 285c7897, not the App Store version). origin/main had no simulator build.
- Tool: shotfleet 0.1.5 (released binary). No "free tier:" line was printed in any run.
- Device: 1 iPhone 17 Pro Max simulator, iOS 26.4, `parallel = 1`. Quiet Mac (free memory 47-49 %, load 6-9, 3 checks 60 s apart) when the lock was taken at 10:56.
- Flow: flow.yaml (onboarding, optional tap on "Not Now" for the analytics dialog, then 5 screens: feed, first story's comments, Radar, Bookmarks, Account). One English flow, shotfleet translated the taps.
- Runs (all rc=0, 5/5 screenshots per language, 1 attempt each, `check` 0 problems):
  - run3 de, ja: 154 s wall; run4 ko, es: 132 s; run5 fr, pt-BR: 252 s. 30 screenshots, 6 languages x 5 screens.
  - `shotfleet check out-runN --app Kuokka.app` after each: 0 problems, 0 notes, 0 unverified (run3/4/5/check.json).
- Earlier the same day (logs/): run1 de, ja with a first version of the flow: 10/10 captured, but the story tap hit "Schliessen" on a hint card, and the Bookmarks tap by text did nothing. run2: failed at a tap point I wrote as "94.5%" (Maestro 2.0.10 wants whole percent). Both were my flow, not shotfleet; fixed before run3.
- Frames reviewed (every one of the 30): live Hacker News at capture time. Feed frames show other companies' logos (OpenAI favicons) and HN usernames. Story frames show a user's comment (one is about a death). Bookmarks frames show the same story title and its author under "continue reading". None of those are on the site. Used: Radar (de, ja, fr) and Account (ko, es, pt-BR), which contain no Hacker News content.
- Not run: Android (the only release APK is 2.0.8; branch APKs are 2.0.1x debug builds from unmerged work), iPad.
