# Done-for-you run (draft, for Manu to approve before it goes anywhere public)

Purpose: the cheapest test of whether anyone pays for localized, checked screenshots. No new code; Manu runs shotfleet on his Mac.
Price to test: $149 per app per run (about two hours of Manu's time at the start, minutes once a flow exists). Compare: ButterKit $99, AppScreens $90/yr.

## The offer (short version for a post or DM)

> I'll capture your app's store screenshots in every language it ships, on iOS and Android, check each one
> (right language, no copies, nothing missing, store size rules), and send them back in fastlane's folders.
> You send a simulator build or APK and say which 4–6 screens you want. $149 per app, refunded if it doesn't work.

## What I need from the buyer
1. A simulator build (`Debug-iphonesimulator` .app, zipped) and/or a debug APK. No source code.
2. The screens, in plain words: "onboarding page 3, home, a finished workout, paywall". I write the Maestro flow.
3. Demo data notes (typed text isn't translated, so say what should be in the fields).

## What they get
- `screenshots/<locale>/` (deliver) and `metadata/android/<locale>/images/phoneScreenshots/` (supply), plus iPad 13" if the app runs on iPad.
- The review grid (`index.html`) and `check.json`.
- Their flow file, so they can rerun it themselves with a shotfleet licence.

## Rules
- Their builds and screenshots stay on my Mac and are deleted 30 days after delivery.
- If the check finds a bug in their app (like the unreachable Next button), I tell them; that is part of the value.
- Every done-for-you customer is offered a licence at the founder price for the next release.
