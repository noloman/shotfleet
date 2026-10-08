# Show HN kit

Owner: Manu posts, from his own account, and answers for hours. Nothing here has been posted. Written 2026-10-02.
Where: https://news.ycombinator.com/submit (rules: https://news.ycombinator.com/showhn.html and https://news.ycombinator.com/newsguidelines.html).

## Ready when (all of these, not some)

1. The sale is live on the real domain and `go-live.sh` has run. A waitlist page does not qualify for Show HN (the rules exclude sign-up pages and landing pages) and must not be the link.
2. `curl -fsSL https://shotfleet.com/install.sh | sh` installs on a clean Apple silicon Mac, and `shotfleet check` runs without a key. (At research time `/download/VERSION` returned 404, so no release was published; claims C057.)
3. Notarization of the release build is proven: `spctl -a -vv -t exec $(which shotfleet)` says "Notarized Developer ID" for the binary that `go-live.sh` shipped, and a quarantined install on a clean user account opens without a prompt (roadmap step: "Build, sign, notarize", research/roadmap-2026-10.md). What is true today: a notarized 0.1.0 folder build ran quarantined (DISTRIBUTION.md), but the final gate-ON release build has not been through `spctl` yet. Until it has, this file says "signed" and never "notarized".
4. The free tier works end to end: `shotfleet run --locales en,de` captures 2 languages with no key (claims C048 is partial: not exercised on a frozen build in one test; run it).
5. `tools/check-claims.sh` is green.
6. Manu has the day free: first 3 hours answering every comment, then check every hour. Do not ask anyone to upvote, comment or share; do not post the link in other places "to help". Vote rings are detected and punished.

Do not post on a Friday evening, or when you cannot answer. Timing advice (Tuesday to Thursday morning US Eastern) comes from vendor blogs and is unverified; the one hard rule is that the product is runnable.

## Title options

HN rules: no superlatives, no editorializing, not clickbait, "Show HN:" prefix, under about 80 characters.

1. `Show HN: One English Maestro flow, every language your app ships, checked` (72) [recommended: matches the plan and the product]
2. `Show HN: shotfleet, localized iOS and Android screenshots from one Maestro flow` (79)
3. `Show HN: I ran my app in 18 languages and one onboarding button was unreachable` (78) [story title; HN may read it as a blog post, so only use with a link to the tool and not to the article]
4. `Show HN: A free check that your localized store screenshots are in the right language` (84; too long, shorten before use)

URL to submit: `https://shotfleet.com/?utm_source=hn` (the homepage; the funnel counter reads `utm_source`, see the watch list in marketing/kit/launch-day.md). Do not submit the article as the Show HN link.

## First comment (post it yourself, right after submitting)

> Hi HN, I'm Manu, a solo developer in the Netherlands. I ship a workout app in 18 languages. My Maestro screenshot flow tapped English buttons, so I could not run it in German or Japanese without a copy of the flow per language, and my "localized" store screenshots ended up as the English set copied into every language folder.
>
> shotfleet is what I built to fix that. You write one English Maestro flow. It reads the translations compiled into your .app or APK, rewrites every text tap for each language ("Next" becomes "Weiter", "次へ", "İleri"), runs all the languages in parallel on iOS simulators and Android emulators, and checks each screenshot against your app's own strings: wrong language, copies, missing screens, App Store and Play size rules. Then it exports to fastlane's folders; fastlane does the upload.
>
> The first full Android run is the story that made me keep going. Japanese, Korean, Chinese and Arabic all got stuck on one onboarding page: the text is taller, the page did not scroll, and Next was below the bottom of a small phone. English fit, so I had never seen it. The fix was a vertical scroll on two pages (8 lines). The write-up is here: https://shotfleet.com/the-button-nobody-could-reach?utm_source=hn (the tool did not detect the missing button; the capture got stuck and I looked at why).
>
> Numbers, so you can judge them: 18 languages x 4 screens = 72 screenshots took 9 minutes on iOS and 15 minutes on Android, on one M1 Pro Mac, 4 simulators or emulators in parallel. One app, Maestro 2.0.10. Yours will differ.
>
> Limits, up front:
> - Apple silicon Mac only. The installer refuses Intel Macs.
> - Needs Maestro 2.x and Java 17+ (Maestro needs it), Xcode for iOS, the Android SDK for Android, and API 33+ emulators for Android per-app languages.
> - You write the flow (`shotfleet init` writes a starter). No frames, no captions, no store upload.
> - Closed source, one signed binary for Apple silicon.
> - Flutter and React Native work from your translation files. I have run it end to end on one public Flutter app (wger) and one Expo template (obytes), on iOS and Android; other Flutter or Expo apps and bare React Native I have not run, so I do not claim it works there.
> - The checks read text, they do not understand layout. Scripts macOS text recognition cannot read (Greek, Hebrew, most Indic scripts) only get the weaker checks unless you plug in Tesseract.
>
> Price and free tier: `shotfleet check` is free (no account, no licence) and works on fastlane snapshot/screengrab folders and on a plain folder per language (I have not tried other tools' exports). `run` is free for 2 languages. A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49 once per developer, with a year of updates and a 14-day refund.
>
> Install: `curl -fsSL https://shotfleet.com/install.sh | sh` (checksum-verified; read the script first if you like, it is short). I would like to hear how you check localized screenshots today, and what would stop you from trying it.

Before posting: if (and only if) `spctl` on the release binary says "Notarized Developer ID", change "one signed binary" to "one signed and notarized binary" (and see answers 1 and 2); replace "Maestro 2.0.10" with the version you ran; check that `https://shotfleet.com/install.sh` is final.

---

## The 15 hardest likely questions, with honest answers

### 1. "Closed source and curl | sh. Why should I run this?"

> Fair. I will not pretend that is nothing. What I can say: the install script is about 15 lines of shell, so read it before you pipe it. It refuses anything that is not macOS on Apple silicon, downloads one tarball and its SHA-256, checks the sum, and puts the program in `~/Library/Application Support/shotfleet`. The program is signed with my Apple Developer ID. `shotfleet check` needs no key and no account, so you can try the part that reads screenshots first. As far as network use goes, I went through the code: the only hosts it talks to are the licence store (Gumroad) when you activate and about weekly after that, my site for a version number when you run `doctor`, and 127.0.0.1 for Maestro. I have not done a packet capture, so if you care, run it behind Little Snitch and tell me what you see. It is closed source today, and I know that rules it out for some of you.

Honest limits: the tool is not auditable by reading it. Say that, do not argue it. Add "and notarized" after "signed" only once `spctl` confirms it on the release binary (answer 2).

### 2. "Is it notarized? Gatekeeper?"

> It is signed with my Developer ID. I notarized the 0.1.0 build and a quarantined copy of it opened without a prompt on my Mac, but I have not yet run `spctl` on the exact release binary you download, so I am not going to tell you it is notarized until I have. Here is how to check yourself: `spctl -a -vv -t exec $(which shotfleet)` should print "Notarized Developer ID". If it does not, tell me and I will fix it. Also note that the `curl` install does not set the quarantine flag, so Gatekeeper is not consulted on that path anyway; a browser download is.

If `spctl` on the release binary does print "Notarized Developer ID" by the time you post, use instead: "Yes: signed with a Developer ID and notarized by Apple; `spctl -a -vv -t exec $(which shotfleet)` prints Notarized Developer ID, and a quarantined copy opens without a prompt." State only what you ran. The honest status today is in research/roadmap-2026-10.md (claims C058 is evidence, not proof, for the release build).

### 3. "Why not fastlane snapshot?"

> If you have a maintained UI-test suite and snapshot works for you, keep it. It is free and good. Two reasons I did not: snapshot runs your UI tests, so you write and maintain test code per platform, and it only knows how to capture. I wanted one flow in plain English for both iOS and Android with no test code in the app, and I wanted something that reads every image afterwards, because the failure I kept hitting was a good-looking image in the wrong language. And shotfleet's `check` works on snapshot's output, so they can sit next to each other.

Do not say fastlane "is slow", "is not parallel" or "runs one language at a time" (fastlane has a `concurrent_simulators` option; claims C094). Do not quote speed comparisons: no timed head-to-head has been run.

### 4. "Why not just use Maestro and its locale flag?"

> You can, and for two or three languages I would. Maestro's docs say a flow cannot set the locale itself; the documented way is `--device-locale` on `maestro start-device` plus tags. That works per device, one language at a time. What shotfleet adds is the rewrite of the text taps for each language (it knows what "Next" is in German from your app), the parallel run across devices, a fresh state per language, and the check afterwards. It is built on Maestro and I am not affiliated with it; I do not speak for the Maestro project.

Do not say Maestro "recommends one flow per locale", and do not imply endorsement.

### 5. "What leaves my machine? Privacy?"

> Your app and your screenshots are never uploaded; the program runs on your Mac. Network use: licence activation and a weekly re-check with the store that sold the key (the key and the product ID, no Mac name), a version lookup on my site when you run `doctor`, and local traffic to Maestro. `check` and `init` need no network. I checked this by reading every URL in the code, not with a network capture.

Keep this answer in line with the live privacy page. Claims C004, C085 are partial.

### 6. "Intel Macs? Linux? Windows? Can I run it in CI?"

> Not on Intel: the binary is arm64 only and the installer refuses Intel Macs. I have no date for an Intel build and will not promise one. Not on Linux or Windows either: iOS simulators need a Mac, and `check` uses the text recognition built into macOS. In CI it runs on a macOS runner. Exit codes are stable (0 all good, 1 problems found, 2 setup error) and `run`, `check` and `export` take `--json`. The GitHub Actions recipe in the README for `check` has not been run on GitHub yet; the command in it is the one I tested locally. For `run` and `export` in CI you set `SHOTFLEET_KEY`.

(The installer still prints "Intel build coming" in its refusal message; that is wording, not a commitment. Do not repeat it. Ask the lead to change it if it is still there.)

### 7. "What do I need installed? Java? Which Maestro version did you test?"

> A Mac with Apple silicon, Xcode for iOS, the Android SDK for Android (API 33+ emulators, because per-app languages arrived in Android 13), Maestro 2.x, and Java 17 or newer, which Maestro itself needs (`shotfleet doctor` checks all of these and says how to fix what is missing). I developed and measured everything on Maestro 2.0.10. Newer Maestro releases exist (2.11.0 was current when I looked) and I have not run the whole thing on them, so if one breaks it, tell me which and I will fix it.

Before posting: replace "2.0.10" and "2.11.0" with what `maestro --version` and the latest release say that day. Claims C033 and C073 are partial: say exactly this list, nothing more.

### 8. "What about Flutter and React Native?"

> It works from your translation files (ARB, i18next JSON, .po and others) instead of reading the built app, because those frameworks do not keep readable strings in the build. I have tested the readers on real translation files taken from public projects. I have not run a real Flutter or React Native app through it end to end, so I will not say it works there. If you have one and try it, I would like to hear what happens.

### 9. "Why is it paid? Why $29 / $49?"

> Capturing is becoming free: fastlane, Maestro on its own, and newer tools. What I charge for is the multi-language run and the export, because that is where my own time went. The free parts are `check` and a 2-language `run`, so you can see real results on your own app first. $29 for the first 100 buyers, then $49 once per developer, with a year of updates; after that your version keeps working as long as macOS, Xcode and Maestro let it. I do not have demand data at any price yet; this launch is partly how I find out. Payment goes through Gumroad as merchant of record; prices are before VAT where it applies.

(Say "Gumroad handles VAT" only after checking that the live checkout does; claims C055 is unverifiable.)

### 10. "What is the refund policy?"

> 14 days. Reply to the Gumroad receipt or email hello@shotfleet.com and I refund it, by hand through Gumroad. If shotfleet does not work for your app I would rather know why than keep the money.

### 11. "How does the checking work? Is it OCR?"

> Two ways. On iOS during a run, shotfleet reads the on-screen text straight from the app's accessibility tree through Maestro's driver while each screenshot is up, so it is exact and works in any script. For screenshots made by other tools, or on Android, it reads the image with the text recognition built into macOS and compares what it finds with your app's own strings for that language. It reads 33 languages on my Mac (depends on your macOS version). For scripts it cannot read it still catches other-language screens, copies and missing screens, and it says which screens it could not read. If macOS text recognition hangs (it sometimes does until a restart), `check` switches to Tesseract when it is installed. The first check after a restart can take minutes while macOS compiles its model.

Check against README Limits and claims C027 (partial), C071, C072 before posting; keep to those facts.

### 12. "What can it not do?"

> It does not make frames or captions and does not upload to the stores. It does not run on real devices, only simulators and emulators. It does not translate text you type into fields (demo data stays the same in every language). It does not judge layout or design, only text, copies, missing screens and store sizes. It does not catch every localization bug. The unreachable button above is a bug the tool did not detect; the capture got stuck. It needs the Maestro flow to be written by you.

### 13. "Does it need changes in my app? My app has its own language picker."

> No code changes, but you need a simulator build for iOS (Debug-iphonesimulator) and an API 33+ emulator for Android per-app languages. On iOS it sets the language with launch arguments; on Android it uses per-app locales. If your app keeps its own saved language choice that overrides the system one, I have not tested that case, so I cannot promise it works.

(Claims C006 is partial: the in-app picker case is untested. Do not say "nothing in your app changes" without this caveat.)

### 14. "9 and 15 minutes: how reproducible is that?"

> It is one app (18 languages, 4 screens each), on an M1 Pro with 32 GB, with 4 simulators or emulators in parallel, Maestro 2.0.10, the first attempt. It will change with your Mac, your load, your app's startup time, and any Maestro or Xcode update. I would treat it as a rough scale, not a benchmark.

### 15. "Can't an AI agent or the asc CLI do this for free?"

> They can capture, and some of them well; capture is the cheap part. I could not find a tool that checks each screenshot against the app's own strings for the right language, and I built this because I kept shipping wrong-language images. That is an absence claim, so tell me if you know one. There is a Claude Code skill and an MCP server (`shotfleet mcp`, with `check`, `run` and `doctor`), so an agent can call it. asc uploads, and I plan to make a recipe: shotfleet export then the asc upload command.

(Only say "plan to make a recipe" if you still plan it. Do not say asc "cannot" do anything you have not read in its current docs.)

---

## While you answer

- Be plain. No "thanks for the great question". If you do not know, say so and say you will find out.
- Never reply to a critical comment with the price. Reply to what was asked.
- Do not edit the title after posting unless a moderator asks.
- When someone finds a bug, thank them and file it. A real bug reported in the thread is worth more than a defence.
- After 24 hours, write down every question you could not answer well. They go into the README or the FAQ.
