# Launch drafts: edits for 0.1.6

Made 2026-10-07 on `claude/launch-drafts`, after merging `origin/main` (285e099, 0.1.6). Source of the list: section 6 of `marketing/week-1007/APPROVAL-PACKET.md` on `origin/claude/marketing-week-1007`, checked against main's CHANGELOG, site, privacy page and the two guides. Nothing was posted, sent or submitted. Old and new text are shortened with `...`; the files hold the full text.

## Packet section 6, edit by edit

| # | Where | Status |
|---|---|---|
| 1 | README gate 1, "cask at 0.1.4" | Done: gate rewritten (0.1.6 live), cask line says 0.1.6 |
| 2 | AnywhereRoles lines | Done, the other way round than the packet: the showcase is live with 0.1.6, so the 127/103 numbers stay (with the 15 false lines the site admits), the 108-of-120 fallback is removed |
| 3 | "only outside call is the licence check" | Done in 01, 02, 10 and the facts table |
| 4 | Free licence line in 01 | Done |
| 5 | Guide links | Done in 01, 02 (both subs), 05 |
| 6 | CI answer | Kept to macOS runners; no Linux, Docker or Action anywhere (gate 3) |
| 7 | Marketing plan 1.4 Linux claim | Not pasted anywhere (gate 3 says so) |
| 8 | Kit files directories.md section 5 and outreach.md section 1 | Not edited (outside the files I was given). The drafts no longer point at them: the Console.dev email is now in 07 section 6, and launch-day.md points to the drafts. outreach.md section 1 still says Flutter and React Native were never run: fix it before using it |
| 9 | 07 directories | Done: Console.dev, Indie App Catalog (Non-App-Store form), MCP registry, Glama; App Store form noted as not fitting |
| 10 | 02 Reddit | Done: live-read caveat, r/SideProject draft, r/macapps note, AI-use line |
| 11 | 01 What it doesn't do | Done |
| 12 | 10 "Only Maestro?" | Done, with paid like `run`, 2 languages free, iOS only |
| 13 | 02 "The paid part" | Done |
| 14 | 03 "What it isn't" | Done |
| 15 | "fastlane folders" claims | Done: snapshot, screengrab and supply folders where the claim is about `check`; 08 voice-over says snapshot or screengrab only (the clip shows a plain folder) |

XCUITest wording everywhere: "new in 0.1.6" plus "not run end to end yet" (the CHANGELOG says its device test hasn't passed; its first run lost its simulators on an overloaded Mac). No draft says it works on a device.

## Every edit


### `marketing/launch-drafts/README.md`

- **Why:** Say which version the drafts match.
  - Old: > Written 2026-10-06. Nothing in this folder has been posted
  - New: > Written 2026-10-06, updated 2026-10-07 so every claim is true for 0.1.6 (every edit is in CHANGES.md). Nothing in this folder has been posted

- **Why:** The guide pages exist now (live with 0.1.6).
  - Old: (those still say Flutter was never run on a real app, and link guide pages that don't exist yet)
  - New: (those still say Flutter was never run on a real app)

- **Why:** Edit 10 of the approval packet: r/SideProject draft added.
  - Old: > r/iOSProgramming (App Saturday), r/androiddev (monthly showcase thread), r/FlutterDev (probably skip, see file)
  - New: > r/iOSProgramming (App Saturday), r/androiddev (monthly showcase thread), r/SideProject, r/FlutterDev (probably skip), r/macapps (no draft, see file)

- **Why:** Edit 9 of the approval packet: four directories added.
  - Old: > AlternativeTo, SaaSHub, Awesome-ASO, awesome-maestro (and why not awesome-ios / awesome-android-ui)
  - New: > AlternativeTo, SaaSHub, Awesome-ASO, awesome-maestro, Console.dev, Indie App Catalog, MCP registry, Glama (and why not awesome-ios / awesome-android-ui)

- **Why:** Gates rewritten for 0.1.6 (edits 1, 2, 6, 7 of the packet): 0.1.5 gate passed, AnywhereRoles and guides gate folded into 'live with 0.1.6', XCUITest gate says new but unproven, Docker/Action kept out, calendar added.
  - Old: > ## Gates: check these the day you post 1. **0.1.5 is live.** `curl -s https://shotfleet.com/download/VERSION` printed `0.1.4` on 2026-10-06. Several drafts mention the 0. ...
  - New: > ## Gates: check these the day you post Calendar: launch week starts Mon 19 Oct. Show HN is Tue 20 or Wed 21 Oct. Nothing about shotfleet goes on HN, Product Hunt or Reddi ...

- **Why:** Edit 15: supply folders are fixed in 0.1.6 (the 0.1.5 false 'missing' lines are gone).
  - Old: > | check flags wrong language, blank screens, store sizes; works on fastlane snapshot/screengrab folders, no Maestro, free | site home (New in 0.1.5), alternatives; C157, ...
  - New: > | check flags wrong language, blank screens, store sizes; works on fastlane snapshot, screengrab and supply folders (supply since 0.1.6), no Maestro, free | site home, wh ...

- **Why:** The showcase is on main and live with 0.1.6; its text also admits the 15 false lines and the failed runs, so the drafts do too.
  - Old: > | AnywhereRoles: 127 problems, 103 translated captions over English; 120 Android (15 x 8) + 108 iPhone (18 x 6) recaptured, 0 problems | post-015 branch; C222 to C229 (ga ...
  - New: > | AnywhereRoles (my app): check found 127 problems on the old Play screenshots, 103 translated captions over English, 15 false 'missing' lines from a 0.1.4 supply-name bu ...

- **Why:** Edit 1: 'cask at 0.1.4' is stale.
  - Old: > | Homebrew: `brew install noloman/tap/shotfleet` (tap live, cask at 0.1.4 on 2026-10-06) | whats-new 0.1.5; C181, C192 |
  - New: > | Homebrew: `brew install noloman/tap/shotfleet` (cask at 0.1.6; confirm with `brew info` the day you post) | whats-new 0.1.5; C181, C192 |

- **Why:** Edit 11 wording, plus the honest 'not run end to end'.
  - Old: > | Apple silicon only, macOS 13+, needs Maestro and Java 17+ | site home |
  - New: > | Apple silicon only, macOS 13+; capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests (new in 0.1.6, not run end to end yet) | site home, whats-n ...

- **Why:** Edit 3: 'the only outside call is the licence check' was false.
  - Old: > | App and screenshots never uploaded; licence key checked with Gumroad | site home, privacy; C004, C085 |
  - New: > | App and screenshots never uploaded; licence key checked with Gumroad when you activate and about once a week; `doctor` also asks shotfleet.com for the latest version nu ...

- **Why:** Licence facts for 0.1.6: calendar year, 3 Macs, spare activations.
  - Old: > | $29 first 100 buyers, then $49 once per developer, a year of updates, 3 activations, 14-day refund no questions asked | site home, terms; C054, C056 |
  - New: > | $29 first 100 buyers, then $49 once per developer; a year of updates (a calendar year from the purchase; versions you have keep working); use it on up to 3 of your Macs ...

- **Why:** Facts the new text relies on.
  - Old: (nothing)
  - New: > three rows at the end of 'Facts used': guides, XCUITest, MCP


### `marketing/launch-drafts/01-show-hn.md`

- **Why:** Dates from the launch plan.
  - Old: > Tuesday to Thursday, about 8 to 10 in the morning US Eastern
  - New: > Plan: Tue 20 or Wed 21 Oct, the week of the 19th (not 13 or 14 Oct, that's Keysi's launch). About 8 to 10 in the morning US Eastern

- **Why:** Edit 2: AnywhereRoles is live, so the 127/103 numbers are allowed. Also says what the other 24 problems were (same as the site), the version used, the failed runs, and adds supply (edit 15).
  - Old: > The free part, if you just want to try something: `shotfleet check` works on screenshots you already have, including fastlane snapshot and screengrab folders, no Maestro, ...
  - New: > The free part, if you just want to try something: `shotfleet check` works on screenshots you already have, including fastlane snapshot, screengrab and supply folders, no ...

- **Why:** Edit 11: XCUITest is in 0.1.6. Kept the 'not run end to end' limit from the CHANGELOG, so it never says it works on a device.
  - Old: > > - Apple silicon Macs only (macOS 13+). It needs Maestro and Java 17+. No Intel, Linux or Windows. > - It's built on Maestro. Support for your own XCUITest tests on iOS ...
  - New: > > - Apple silicon Macs only (macOS 13+). No Intel, Linux or Windows. > - Capturing needs Maestro and Java 17+, except on iOS, where it can also run your existing XCUITest ...

- **Why:** Edit 3: the old line was false, doctor also calls shotfleet.com.
  - Old: > > - It's closed source. Your app and screenshots never leave your Mac; the only outside call is the licence check with Gumroad.
  - New: > > - It's closed source. Your app and screenshots never leave your Mac. It talks to Gumroad for the licence, and `doctor` asks shotfleet.com for the latest version number ...

- **Why:** Edit 4 plus the licence facts (calendar year, 3 Macs).
  - Old: > $29 for the first 100 buyers, then $49, one-time, with a year of updates and a 14-day refund.
  - New: > $29 for the first 100 buyers, then $49, one-time. It covers a year of updates (a calendar year from your purchase; the versions you have keep working), up to 3 of your Ma ...

- **Why:** Edit 5: the guides are live, so link them with their own utm_source. (Guide pages don't run the visit counter, so the tag only shows in referrers.)
  - Old: > Short clips of each command are at https://shotfleet.com/demo?utm_source=hn
  - New: > Short clips of each command are at https://shotfleet.com/demo?utm_source=hn > > Two write-ups that don't need the tool: why fastlane snapshot gives you English in every f ...

- **Why:** Gate references renumbered; the old fallback to '108 of 120' is gone because the section is live.
  - Old: > - Gate 1 (0.1.5 live) and gate 2 (AnywhereRoles section live) from README.md. Without gate 2, replace the AnywhereRoles sentences with: "On the store screenshots of anoth ...
  - New: > - Gate 1 (0.1.6 live, guides and AnywhereRoles loading) and gates 2 and 3 from README.md. If the guides or the AnywhereRoles section don't load, cut the guide sentence an ...

- **Why:** The kit answers still say 'only the licence call' and 'needs Maestro'.
  - Old: > Kit answer 8 (Flutter) is out of date: a real Flutter app has run since. Kit answer 2 (notarization): the docs and claims C181 now say the Homebrew build is signed and no ...
  - New: > Kit answer 8 (Flutter) is out of date: a real Flutter app has run since. Kit answer 2 (notarization): the docs and claims C181 now say the Homebrew build is signed and no ...


### `marketing/launch-drafts/02-reddit.md`

- **Why:** Edit 10: the live-read caveat from section 4 of the packet.
  - Old: > **How the rules were read:** Reddit blocks my tools, so I couldn't open the sidebars. What's below comes from search summaries on 2026-10-06 and the older notes in `resea ...
  - New: > **How the rules were read:** Reddit blocks my tools (403 on every `about/rules.json`; Claude in Chrome and the built-in browser both refuse reddit.com), so I couldn't ope ...

- **Why:** 0.1.6 is live, so this is no longer conditional; date from the packet.
  - Old: > pick the day well (after 0.1.5 is live, and ideally after 0.1.6 so the XCUITest part can be said as available).
  - New: > pick the day well: Sat 24 Oct at the earliest, which is after Show HN and after 0.1.6 is live, so the XCUITest part can be said as available (with its 'not run end to end ...

- **Why:** Edit 10: the template asks for AI use.
  - Old: > and a template with the tech stack and the development challenges. The draft below includes both anyway.
  - New: > and a template with the tech stack, the development challenges and an AI-use line. The draft below includes all three anyway.

- **Why:** Edit 2: 103 is allowed now (the section is live). Wording fixed: it's 103 of the 127 problems, not '103 problems'.
  - Old: > On the old Google Play screenshots of another of my apps, check found 103 problems where the captions were translated but the app under them was still English.
  - New: > On the old Google Play screenshots of another of my apps, AnywhereRoles, check found 103 screenshots where the captions were translated but the app under them was still E ...

- **Why:** Edit 13: the 'coming in 0.1.6' sentence, with the honest limit.
  - Old: > Running your own XCUITest screenshot tests instead of a Maestro flow is coming in 0.1.6, not out yet.
  - New: > On iOS it can also run your own XCUITest screenshot tests instead of a Maestro flow (new in 0.1.6, paid like this, 2 languages free). I haven't run that path end to end y ...

- **Why:** Edit 11 wording, plus the privacy fact (edit 3 idea) since this post lists limits.
  - Old: > **Limits.** Apple silicon only, needs Maestro and Java 17+ for `run`.
  - New: > **Limits.** Apple silicon only, closed source. Capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests. `doctor` asks shotfleet.com for the latest v ...

- **Why:** Edits 10 and 5: AI-use line for the App Saturday template, guide link with its own utm_source at the end, licence facts.
  - Old: > Price: check is free, run is free for 2 languages. Every language is $29 for the first 100 buyers, then $49, one-time. > > https://shotfleet.com/?utm_source=reddit-iospro ...
  - New: > **AI use.** I used Claude (Anthropic's coding assistant) to help write and test the code and to draft the docs and this post. I decide what ships, and the numbers above a ...

- **Why:** Gate references renumbered; the 108-of-120 fallback is dropped because the AnywhereRoles section is live.
  - Old: > **Before posting:** gates 1 and 2 in README.md. The tech stack lines (Python packaged with PyInstaller, Vision) come from DISTRIBUTION.md and the code, not from the site; ...
  - New: > **Before posting:** gates 1 to 3 and 5 in README.md. The tech stack lines (Python packaged with PyInstaller, Vision) come from DISTRIBUTION.md and the code, not from the ...

- **Why:** Edits 15 and 5: supply is only fine after 0.1.6; Maestro guide linked with its own utm_source; says capture needs Maestro and Java.
  - Old: > including screengrab output (it ignores screengrab's timestamped file names). Runs on Apple silicon Macs only. Paid for more than 2 languages in a run: $29 for the first ...
  - New: > including screengrab output (it ignores screengrab's timestamped file names) and supply folders (fixed in 0.1.6). Runs on Apple silicon Macs only, and capturing needs Mae ...

- **Why:** Edit 10: r/SideProject draft; packet section 4 lists r/macapps as no draft.
  - Old: (nothing)
  - New: > new sections: r/SideProject draft, r/macapps note (r/FlutterDev renumbered to 5)


### `marketing/launch-drafts/03-product-hunt.md`

- **Why:** 0.1.6 is live; XCUITest isn't proven enough to be a reason for a second launch.
  - Old: > - You can launch again later only for a significant new version (so 0.1.6 with XCUITest could be a second launch; don't spend it on a minor release).
  - New: > - You can launch again later only for a significant new version. 0.1.6 is already out when this launches, and its XCUITest part hasn't run end to end, so don't plan a sec ...

- **Why:** Dates from the launch plan.
  - Old: > Whatever day: one you can spend answering comments.
  - New: > Whatever day: one you can spend answering comments. Not 14 Oct (that's Keysi's Product Hunt day). Suggestion: Sun 25 Oct, after Show HN and App Saturday.

- **Why:** The site says the Android flow took several failed runs; so do we.
  - Old: > I had made one English capture and translated only the captions. I recaptured it with shotfleet: 120 Android and 108 iPhone screenshots, 0 problems.
  - New: > I had made one English capture and translated only the captions. I recaptured it with shotfleet: 120 Android and 108 iPhone screenshots, 0 problems (several failed runs c ...

- **Why:** Edit 2, with the 15 false lines as on the site.
  - Old: > On the old Google Play screenshots of another of my apps, check found 127 problems, 103 of them translated captions over an app still in English.
  - New: > On the old Google Play screenshots of another of my apps (AnywhereRoles), check found 127 problems: 103 were translated captions over an app still in English, and 15 were ...

- **Why:** Edit 14.
  - Old: > What it isn't: no frames, captions or upload (use ButterKit, AppScreens or fastlane for that). Apple silicon Macs only. It needs Maestro for capturing; your own XCUITest ...
  - New: > What it isn't: no frames, captions or upload (use ButterKit, AppScreens or fastlane for that). Apple silicon Macs only, closed source. Capturing needs Maestro and Java 17 ...

- **Why:** Edit 15 plus the year of updates.
  - Old: > Free: check (works on fastlane snapshot and screengrab folders too), and run for 2 languages. Every language: $29 for the first 100 buyers, then $49, one-time, 14-day ref ...
  - New: > Free: check (works on fastlane snapshot, screengrab and supply folders too), and run for 2 languages. Every language: $29 for the first 100 buyers, then $49, one-time, wi ...

- **Why:** Edit 15.
  - Old: > "check works on screenshots you already have, like fastlane folders. No simulator needed, and it's free."
  - New: > "check works on screenshots you already have, like fastlane snapshot, screengrab or supply folders. No simulator needed, and it's free."

- **Why:** 108-of-120 fallback dropped; section is live.
  - Old: > - Gates 1 and 2 in README.md. Without gate 2, replace the AnywhereRoles sentences in the comment with: "On the store screenshots of another of my apps, check flagged 108 ...
  - New: > - Gates 1 to 3 in README.md. If the AnywhereRoles section isn't live, cut the AnywhereRoles sentences from the comment.


### `marketing/launch-drafts/04-indie-hackers.md`

- **Why:** Dates from the launch plan.
  - Old: > A weekday morning US Eastern (Tuesday to Thursday).
  - New: > A weekday morning US Eastern. Launch week starts Mon 19 Oct, so Mon 19 or Tue 20 Oct; not 13 or 14 Oct.

- **Why:** Edit 2, with the 15 false lines as on the site.
  - Old: > When I finally checked those Google Play screenshots, there were 127 problems, 103 of them translated captions over an app still in English.
  - New: > When I finally checked those Google Play screenshots, there were 127 problems. 103 were translated captions over an app still in English, and 15 were false alarms from a ...

- **Why:** Licence facts for 0.1.6.
  - Old: > One-time licence on Gumroad: $29 for the first 100 buyers, then $49. Free tier:
  - New: > One-time licence on Gumroad: $29 for the first 100 buyers, then $49. It covers a year of updates (a calendar year), and you can use it on up to 3 of your Macs. Free tier:

- **Why:** 0.1.6 is the current version.
  - Old: > I'm on [VERSION: 0.1.5, check https://shotfleet.com/download/VERSION] now.
  - New: > I'm on [VERSION: 0.1.6, check https://shotfleet.com/download/VERSION] now.

- **Why:** 108-of-120 fallback dropped.
  - Old: > - The 127/103 line needs gate 2 (README.md). Without it: "flagged 108 of 120 screenshots: translated captions over an app still in English" (C107).
  - New: > - The 127/103/15 line needs the AnywhereRoles section live (README.md gate 1). If it isn't, say only "the captions were translated but the app under them was still in Eng ...


### `marketing/launch-drafts/05-newsletter-pitches.md`

- **Why:** Edit 5 idea: the guides exist now, and curators prefer articles.
  - Old: > If one of the guide articles in `site/draft/guides/` is published by then (the button story is the best fit), send that link instead and keep the tool to one line. The te ...
  - New: > The two guides are live with 0.1.6: send the matching one instead of the home page and keep the tool to one line. iOS Dev Weekly: `https://shotfleet.com/guides/fastlane-s ...

- **Why:** Edit 11 style: 0.1.6 has XCUITest; honest limit kept.
  - Old: > On the old Google Play screenshots of another of my apps it found 103 translated captions over an app still in English. The paid part runs one English Maestro flow in eve ...
  - New: > On the old Google Play screenshots of another of my apps it found 103 translated captions over an app still in English. The paid part runs one English Maestro flow in eve ...

- **Why:** Edit 15: supply is fixed in 0.1.6.
  - Old: > Its check command is free and also reads screengrab output, flagging the wrong language, blank screens and Play size problems.
  - New: > Its check command is free and also reads screengrab and supply folders, flagging the wrong language, blank screens and Play size problems.

- **Why:** Gate references renumbered; 108-of-120 fallback dropped.
  - Old: > - Gate 1 (0.1.5 live: screengrab file names) and gate 2 (the 103 number) in README.md. Without gate 2, iOS Dev Weekly's second sentence becomes: "On the store screenshots ...
  - New: > - Gates 1 and 2 in README.md (0.1.6 live, XCUITest not proven). If AnywhereRoles isn't live, drop iOS Dev Weekly's second sentence.


### `marketing/launch-drafts/06-short-posts.md`

- **Why:** Dates from the launch plan.
  - Old: > Thread on launch day; standalone posts one or two a week after that, not all at once.
  - New: > Thread on launch week's Monday (19 Oct), not as a reaction to Show HN; standalone posts one or two a week after that, not all at once. Nothing on 13 or 14 Oct (Keysi's la ...

- **Why:** Edit 15: add supply (fixed in 0.1.6). 103 is allowed now (edit 2).
  - Old: > > check is free, and it works on screenshots you already have, also fastlane snapshot and screengrab folders. No Maestro, no account. > > On the old Play screenshots of a ...
  - New: > > check is free, and it works on screenshots you already have, also fastlane snapshot, screengrab and supply folders. No Maestro, no account. > > On the old Play screensh ...

- **Why:** Re-count after the supply edit.
  - Old: > **4/5** [257]
  - New: > **4/5** [265]

- **Why:** Edit 2: post E is no longer skipped. Dropped '127' from the short text (15 of those were false alarms from my own bug) so the short post says only the part that is exactly true.
  - Old: > **E. AnywhereRoles before and after** [247], no clip (or a pair of the AnywhereRoles frames from the home page once they're live) > Before: check found 127 problems on my ...
  - New: > **E. AnywhereRoles before and after** [247], image: one Android and one iPhone frame from the AnywhereRoles section of the home page (`site/public/img/showcase/`; alt tex ...

- **Why:** Gates renumbered; 108-of-120 fallback dropped.
  - Old: > - Gate 1 (0.1.5 live) for "screengrab folders" and the brew line; gate 2 (AnywhereRoles live) for thread 4/5 and post E. Without gate 2: in 4/5 use "it flagged 108 of 120 ...
  - New: > - Gate 1 (0.1.6 live) for the supply wording and the brew line, and the AnywhereRoles section live for thread 4/5 and post E. If it isn't live, cut the last sentence of 4 ...

- **Why:** Re-count after edits.
  - Old: (counts)
  - New: > thread 4/5 and post E counts recomputed below


### `marketing/launch-drafts/07-directories.md`

- **Why:** Version.
  - Old: > Updated short descriptions (the kit's ones predate 0.1.5):
  - New: > Updated short descriptions (the kit's ones predate 0.1.6):

- **Why:** Edit 15: supply folders, within 300 characters (shortened 'iOS simulators and Android emulators' to 'iOS and Android').
  - Old: > - **300 characters:** `shotfleet runs one English Maestro flow in every language your app has, on iOS simulators and Android emulators at once, then checks each screensho ...
  - New: > - **300 characters:** `shotfleet runs one English Maestro flow in every language your app has, on iOS and Android at once, then checks each screenshot for the wrong langu ...

- **Why:** Edit 11 wording for the directory long text.
  - Old: > Needs Maestro and Java 17+ for capturing. Made by a solo developer.`
  - New: > Capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests (new in 0.1.6). Made by a solo developer.`

- **Why:** Gate renumbered; Docker/Action kept out.
  - Old: > - Gate 1 in README.md (0.1.5 live) for the screengrab wording.
  - New: > - Gate 1 in README.md (0.1.6 live) for the supply wording, and gate 3 (no Linux, Docker or Action in any text).

- **Why:** Edit 9, plus edit 8 (the Console.dev email replaces the stale kit one). Added the MCP hooks:true fact.
  - Old: (nothing)
  - New: > new sections 6 to 9: Console.dev email (0.1.6 text), Indie App Catalog (Non-App-Store form; App Store form noted as not fitting), Official MCP Registry (server.json version 0.1.6), Glama (skip)


### `marketing/launch-drafts/08-demo-video-script.md`

- **Why:** The video must not claim more than the clips show.
  - Old: > ## Rules to respect
  - New: > ## Rules to respect - The clips were recorded before 0.1.6. They show doctor, init, a run, check, export and CI; they don't show XCUITest or supply folders, so don't add ...

- **Why:** Edit 15: the clip itself shows a plain folder; 'fastlane folders' in general overstated it before 0.1.6, and the voice-over doesn't need supply.
  - Old: > > [5] check also works on screenshots I already have, like fastlane folders. No simulator. It's free, and nothing is uploaded.
  - New: > > [5] check also works on screenshots I already have, like fastlane snapshot or screengrab folders. No simulator. It's free, and nothing is uploaded.

- **Why:** Edit 15: supply is fixed in 0.1.6; the YouTube text is read next to a live 0.1.6 site.
  - Old: > The check is free and works on screenshots you already have, including fastlane snapshot and screengrab folders.
  - New: > The check is free and works on screenshots you already have, including fastlane snapshot, screengrab and supply folders.


### `marketing/launch-drafts/10-faq-objections.md`

- **Why:** Edit 12.
  - Old: > > For capturing, yes, today it's Maestro: one flow in English, and shotfleet rewrites it for each language. Running your own XCUITest screenshot tests on iOS is coming in ...
  - New: > > For capturing, mostly yes: one flow in English, and shotfleet rewrites it for each language. On iOS it can also run your existing XCUITest screenshot tests instead of a ...

- **Why:** Licence facts for 0.1.6.
  - Old: > It's $29 for the first 100 buyers, then $49 once, not a subscription, with a 14-day refund.
  - New: > It's $29 for the first 100 buyers, then $49 once, not a subscription. You get a year of updates (a calendar year from your purchase; the versions you have keep working), ...

- **Why:** Edit 15: supply fixed in 0.1.6.
  - Old: > They also work together: run shotfleet check on the folder snapshot or screengrab writes.
  - New: > They also work together: run shotfleet check on the folder snapshot, screengrab or supply writes.

- **Why:** Edit 3: the answer didn't mention doctor's calls.
  - Old: > > Your app and your screenshots are never uploaded; everything runs on your Mac. The licence key is checked with Gumroad when you activate and about once a week after tha ...
  - New: > > Your app and your screenshots are never uploaded; everything runs on your Mac. The licence key is checked with Gumroad when you activate and about once a week after tha ...

- **Why:** Edit 6 kept to macOS runners (no Linux, Docker or Action). Adds the 0.1.6 CI-key behaviour.
  - Old: > check can, on any macOS runner, with no simulator: `--json` for the result, exit code 0 for all good, 1 for problems, 2 for a setup error. The docs have a GitHub Actions ...
  - New: > check can, on any macOS runner, with no simulator: `--json` for the result, exit code 0 for all good, 1 for problems, 2 for a setup error. The docs have a GitHub Actions ...

- **Why:** The number is old.
  - Old: > [If asked how many are sold: say the true number. It was 0 on 2026-10-06.]
  - New: > [If asked how many are sold: say the true number. It was 0 on 2026-10-06; re-check Gumroad first.]

- **Why:** Security fact and licence facts for 0.1.6.
  - Old: (nothing)
  - New: > three new answers at the end: AI agent / MCP and hooks:true, after the year of updates, how many Macs


### `marketing/kit/launch-day.md`

- **Why:** Dates and the 'where this stands' note for the 19 Oct launch week.
  - Old: > Claude has posted nothing and will not. Written 2026-10-02.
  - New: > Claude has posted nothing and will not. Written 2026-10-02, updated 2026-10-07 for launch week. **Where this stands (2026-10-07):** shotfleet 0.1.0 has been live since 20 ...

- **Why:** Pointers: the kit files they used to point to predate 0.1.5 and 0.1.6; the drafts are the newer text.
  - Old: > | What | File | |---|---| | Waitlist email | marketing/launch-email.md | | Show HN title, first comment, 15 answers | show-hn.md | | Social thread (launch-day thread) | s ...
  - New: > | What | File | |---|---| | Show HN title, first comment | marketing/launch-drafts/01-show-hn.md | | Short answers for comment threads | marketing/launch-drafts/10-faq-ob ...

- **Why:** Make the preflight check the version that is meant to be live.
  - Old: > `shotfleet --version`, `shotfleet doctor`, `shotfleet check`
  - New: > `shotfleet --version` (must print 0.1.6), `shotfleet doctor`, `shotfleet check`

- **Why:** The one-time test already ran; 0.1.6 changed activations (5 per key).
  - Old: > 5. One real purchase with FOUNDER29 and one refund, end to end: checkout, key arrives, `shotfleet activate`, all languages work, refund, key stops validating (roadmap N2) ...
  - New: > 5. The purchase and refund test was part of the 2026-10-05 go-live (LAUNCH.md section 6). Before launch week, do one activation on a clean Mac with the 0.1.6 build: `shot ...

- **Why:** Tags used by the new drafts.
  - Old: > `peerlist`, `consoledev`.
  - New: > `peerlist`, `consoledev`, `reddit-sideproject`, `reddit-iosprogramming`, `reddit-androiddev`, `producthunt`, `alternativeto`, `saashub`. (The guides' own tags, like `hn-g ...

- **Why:** Day 0 is no longer 'go live'; that happened on 2026-10-05.
  - Old: > ## Day 0: go live and tell the list
  - New: > ## Day 0 (Mon 19 Oct): tell the list and post the thread The 08:15, 08:30 and 09:15 rows were done on 2026-10-05; skip them and instead check that the site, `curl -s http ...

- **Why:** Pointer to the updated draft.
  - Old: > Use the first-comment backstory in show-hn.md as the base; mention the price once | show-hn.md (first comment, shortened) |
  - New: > Use marketing/launch-drafts/04-indie-hackers.md and fill its placeholders; mention the price once | launch-drafts/04-indie-hackers.md |

- **Why:** The updated thread has 5 posts, not 6.
  - Old: > Social launch thread on Mastodon, Bluesky and X, six posts each, each network with its own `utm_source` in post 1 and post 6 | social.md "Launch-day thread" | Three threa ...
  - New: > Social launch thread on Mastodon, Bluesky and X, five posts each (the draft has 5), each network with its own `utm_source` in the last post | marketing/launch-drafts/06-s ...

- **Why:** r/SideProject draft exists now (packet edit 10); r/macapps stays a skip.
  - Old: > r/macapps once, only if the sidebar you read today allows self-promotion and you have not posted there in 30 days (reported rule, unverified). Skip if unsure | write a sh ...
  - New: > r/SideProject post, after you read its sidebar today | marketing/launch-drafts/02-reddit.md section 3 | Posted once | | 11:45 | r/macapps: skip (a command-line tool is a ...

- **Why:** Tie Day 1 to the drafts' gates.
  - Old: > Go only if: Day 0 install and checkout still work this morning,
  - New: > Day 1 is Tue 20 or Wed 21 Oct. Go only if: the gates in marketing/launch-drafts/README.md pass, Day 0 install and checkout still work this morning,

- **Why:** Pointer to the updated draft.
  - Old: > | 13:30 | Read show-hn.md top to bottom: title option 1, first comment, the 15 answers. Replace "Maestro 2.0.10" with the output of `maestro --version` if you ran on a ne ...
  - New: > | 13:30 | Read marketing/launch-drafts/01-show-hn.md and 10-faq-objections.md top to bottom: title, first comment, the short answers. Replace "Maestro 2.0.10" with the ou ...

- **Why:** Pointer.
  - Old: > Leave the text box empty | show-hn.md "Title options" |
  - New: > Leave the text box empty | launch-drafts/01-show-hn.md "Title" |

- **Why:** Pointer.
  - Old: > immediately, from the file | show-hn.md "First comment" |
  - New: > immediately, from the file | launch-drafts/01-show-hn.md "First comment" |

- **Why:** Pointer; the kit answers predate 0.1.6.
  - Old: > Use the matching answer in show-hn.md for the question;
  - New: > Use the matching answer in launch-drafts/10-faq-objections.md (or the older, longer ones in marketing/kit/show-hn.md) for the question;

- **Why:** Packet edit 8: the kit's Console.dev email is stale.
  - Old: > | 2 | Console.dev email, only if the free tier installs on a clean Mac (it does, from Day -1) | directories.md section 5 |
  - New: > | 2 | Console.dev email, only if the free tier installs on a clean Mac (it does, from Day -1) | marketing/launch-drafts/07-directories.md section 6 |

- **Why:** The guides exist now.
  - Old: > | 4 | Newsletters, article links only, one each (not the landing page) | newsletters.md |
  - New: > | 4 | Newsletters, one each: send the matching guide (live with 0.1.6), not the landing page | marketing/launch-drafts/05-newsletter-pitches.md |

- **Why:** Dates and pointers; the kit's directories.md section numbering is old.
  - Old: > | 5 | AlternativeTo (if not already in the queue), Indie App Catalog | directories.md sections 1 and 6 |
  - New: > | 5 | AlternativeTo (if not already in the queue), Indie App Catalog (Non-App-Store form) | marketing/launch-drafts/07-directories.md sections 1 and 7 | | 6 | Sat 24 Oct: ...

- **Why:** True for the new guide links.
  - Old: > Install and download file hits are not counted (they are static files), so installs are unknown;
  - New: > Install and download file hits are not counted (they are static files), and neither are visits to the guide pages (they don't run the counter), so installs are unknown;

- **Why:** 0.1.6 licence facts.
  - Old: (the Uses row shows how many activations it has used)
  - New: (the Uses row shows how many activations it has used; a key can be activated 5 times from 0.1.6, 0.1.5 and older stop at 3, so Reset the row if they ran out)

- **Why:** Say-nots for the false or unproven claims found in this pass.
  - Old: > 9. Never say: Flutter or React Native "work" on real apps, it "catches all localization bugs",
  - New: > 9. Never say: Flutter or React Native "work" in general (one real Flutter app and one Expo app have run, nothing more), that the XCUITest path works on a device (it hasn' ...


### `LAUNCH.md`

- **Why:** Say what is current; the go-live record stays.
  - Old: > is still live and is a promise on the privacy page.
  - New: > is still live and is a promise on the privacy page. > **2026-10-07:** 0.1.6 is published. Launch week is Mon 19 Oct, Show HN Tue 20 or Wed 21 Oct; nothing about shotfleet ...

- **Why:** Licence facts true for 0.1.6.
  - Old: > a free tier (`check` plus 2 languages in `run`), 14-day refunds.
  - New: > a free tier (`check` plus 2 languages in `run`), 14-day refunds, a year of updates (a calendar year from the Gumroad sale date), use on up to 3 of the buyer's Macs, and f ...

- **Why:** Pointer for launch week.
  - Old: > Posting and emailing stay yours, as agreed.
  - New: > Posting and emailing stay yours, as agreed. For launch week (19 Oct) the post texts and their gates are in `marketing/launch-drafts/README.md`.

- **Why:** Edit: the 5 only applies from 0.1.6.
  - Old: > A key has 5 activations (3 Macs plus 2 spare for reinstalls);
  - New: > From 0.1.6 a key has 5 activations (3 Macs plus 2 spare for reinstalls; 0.1.5 and older still stop at 3);

- **Why:** 0.1.6 licence behaviour, so support answers match the product.
  - Old: > is the whole job. The terms say exactly this.
  - New: > is the whole job. The terms say exactly this. A buyer asking about the year of updates: it is the Gumroad sale date plus a calendar year, compared with each build's froze ...

## Checked, no change needed

- `09-email-other-app-users.md`: still true (no consent list, so don't send); its two product claims (captions translated over an English app; check is free) match the site.
- Prices, the 9 and 15 minute numbers (M1 Pro, my app, Maestro 2.0.10), the unreachable Next button, the Turkish clash, Homebrew, the 14-day refund and Apple silicon only: unchanged and still true.

## For Manu before posting

- The live home page contradicts itself: its stats row says "108 of 120 old App Store screenshots of AnywhereRoles" while the AnywhereRoles section says 127 problems on the old Google Play screenshots (103 captions over English). The drafts use only the section's numbers. One of the two lines on the site needs fixing.
- The "AI use" line in the App Saturday post is my guess at the wording. Confirm or change it.
- 01 says the app was recaptured with 0.1.4 (what the site says), not 0.1.6.
- Guide pages don't run the visit counter, so `utm_source=hn-guide` and the like only show in referrers.
- Gates to re-check on the day: `curl -s https://shotfleet.com/download/VERSION` is 0.1.6, `brew info --cask noloman/tap/shotfleet` says 0.1.6, `/guides` loads, Gumroad sales count, `tools/check-claims.sh`.
