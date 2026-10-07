# Newsletter pitches

You submit these yourself through each newsletter's own form. One link per newsletter, once. No follow-up before four weeks; silence is a normal answer. Never offer money or a free licence for coverage.

Curators pick articles far more often than product pages. The two guides are live with 0.1.6: send the matching one instead of the home page and keep the tool to one line. iOS Dev Weekly: `https://shotfleet.com/guides/fastlane-snapshot-screenshots-all-english?utm_source=iosdevweekly-guide`. Android Weekly: `https://shotfleet.com/guides/maestro-one-flow-every-language?utm_source=androidweekly-guide`. The texts below work for either; swap the link. (Guide pages don't run the visit counter, so these tags only show in referrers.)

---

## iOS Dev Weekly

**Route:** the form at https://suggest.iosdevweekly.com (fields: name, email, link, "Link source" = "I wrote it", blog post yes/no, Swift library = No, and a reason). Read 2026-10-06. If your site is in the iOS Dev Directory (https://iosdevdirectory.com), the curator already reads it by RSS, and the form asks you not to submit those links.

**Best time:** any weekday; the issue usually goes out on Fridays (from memory, not checked today), so earlier in the week has a better chance for that week.

**Link:** `https://shotfleet.com/?utm_source=iosdevweekly`

**Reason for inclusion:**

> I made shotfleet, a Mac command-line tool whose free check command reads a folder of App Store screenshots, including fastlane snapshot output, and flags any that show the wrong language, a blank screen or a size App Store Connect won't take. On the old Google Play screenshots of another of my apps it found 103 translated captions over an app still in English. The paid part runs one English Maestro flow in every language the app has; since 0.1.6 it can also run your own XCUITest screenshot tests, which I haven't run end to end yet. Short clips of each command are at shotfleet.com/demo.

---

## Android Weekly

**Route:** the "What do you want to submit?" section on https://androidweekly.net ("Suggest a link for an upcoming Android Weekly Issue"). They say: "Links in each issue will be chosen by us." Read 2026-10-06; open the form for its exact fields.

**Best time:** any weekday; the issue usually goes out on Sundays (from memory, not checked today).

**Link:** `https://shotfleet.com/?utm_source=androidweekly`

**Text:**

> I made shotfleet, a Mac command-line tool that runs one English Maestro flow in every language an Android app has, on several emulators at once, using per-app languages and the strings from the APK. On my own app it showed an onboarding Next button that was below the screen in Japanese, Korean, Chinese and Arabic on a small phone, because the page didn't scroll. Its check command is free and also reads screengrab and supply folders, flagging the wrong language, blank screens and Play size problems. Disclosure: it's a paid tool with a free tier.

---

## Fresh Flutter [VERIFY: I couldn't find this newsletter]

I searched on 2026-10-06 and found no newsletter called "Fresh Flutter" or a submit form for it. Check the name and its route before using this. Other Flutter newsletters I found: Flutter Developer Weekly (https://flutterdeveloperweekly.com, editor Mark Winters, no contact form seen in the old research), Widget Tricks (Substack). flutterweekly.net now redirects somewhere unrelated, so treat it as gone.

Only send this one if you're fine with the Flutter claim being "one real app". It is.

**Link:** `https://shotfleet.com/?utm_source=freshflutter` (change the tag to match the newsletter)

**Text:**

> I made shotfleet, a Mac command-line tool for App Store and Google Play screenshots in every language. For Flutter it reads your ARB translation files, because the built app doesn't keep the strings readable. I've run it end to end on one real Flutter app, wger, on iOS and Android, and its free check command showed that wger's Japanese screens were mostly English (its Japanese is about 30% translated). It's a paid tool with a free check, Apple silicon Macs only.

---

## Before sending

- Gates 1 and 2 in README.md (0.1.6 live, XCUITest not proven). If AnywhereRoles isn't live, drop iOS Dev Weekly's second sentence.
- Log the date and newsletter so you don't send twice.
