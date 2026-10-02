# Outreach emails and messages

Owner: Manu sends, from his own address. Nothing here has been sent. Written 2026-10-02.
Rules for every message below: send once, no follow-up before the stated wait, never offer payment or a licence in return for coverage (except design partners, where the licence is for an honest write-up and nothing is promised about its tone), accept silence. Do not DM anyone who has not written to you first, except where the person publicly asked for exactly this help and invited replies. Re-read the target's current page the same day.

Facts you may use: 18 languages x 4 screens = 72 screenshots, 9 minutes iOS and 15 minutes Android, one M1 Pro Mac, 4 devices in parallel, one app, Maestro 2.0.10. Free: `shotfleet check`, and `run` for 2 languages. $29 for the first 100 buyers, then $49 once per developer, a year of updates, 14-day refund. Apple silicon only, Maestro 2.x, Java 17+. Never claim: Flutter or React Native on a real app, frames, captions, store upload, "catches all localization bugs", any Maestro endorsement.

---

## 1. Design partners (3 to 5 people, free licence for an honest write-up)

Who: only people who publicly said they have a locale or screenshot problem (a GitHub issue, a Maestro Slack question, a post) and invited help. Write to the thread or to the email on their public profile, never to a private DM.
Ready when: the free tier installs on a clean Mac and a licence key can be issued (the Polar benefit exists: LAUNCH.md). Track each person in a note: name, where they asked, date sent, answer.
Wait: 2 weeks, then stop.

Subject (email) or first line (thread reply): `Your locale screenshot problem: I may have a tool, and a free licence if you try it`

> Hi NAME,
>
> I saw your post about LINK-TO-THEIR-POST (a few words on what they said, in their words). I make shotfleet, a Mac command line tool that runs one English Maestro flow in every language an app ships, on iOS and Android, and checks each screenshot against the app's own strings. I built it for my own 18-language app, so I disclose that I am the author.
>
> I am looking for a handful of developers who will try it on a real app and tell me honestly what happened, including what did not work. If you are up for it, I will give you a full licence for free (normally $29 to $49). In return I would like a short, honest write-up from you: a paragraph, a post, or a reply to me, your choice, positive or negative.
>
> Terms, so there are no surprises: the licence is yours either way. I will not quote you, name you or use your app's name anywhere without your written yes to the exact words, and you can say no after seeing them. You owe me nothing if it does not work for your app.
>
> What it needs: an Apple silicon Mac, Xcode for iOS, the Android SDK for Android, Maestro 2.x and Java 17+. It does not make frames or captions and does not upload to the stores. I have not run it on a real Flutter or React Native app yet, so if that is your stack you would be an early test for me, not a safe bet.
>
> If this is not for you, no problem, and thank you for reading.
> Manu

After yes: send the licence key and install line (`curl -fsSL https://shotfleet.com/install.sh | sh`, then `shotfleet activate <key>`). Offer to help with the first run by email; log the minutes it takes (MARKETING.md: support minutes per sale).
Before any quote goes public: send the exact text and the exact place it will appear, wait for a written yes in reply, keep that email. Two signed-off quotes before any testimonial appears on the site (MARKETING.md phase 0, item 8).

---

## 2. Console.dev

The full email is in marketing/kit/directories.md section 5. Short version of the plan: send it once, to hello@console.dev, only when the free tier installs on a clean Mac and the release binary is checked with `spctl -a -vv -t exec` (say "signed" if it is not yet notarized). Wait two weeks before one follow-up at most. Console.dev states that it has no sponsored reviews, so offer nothing.

---

## 3. Indie Dev Monday

What it is: a newsletter that spotlights indie app developers. Research (research/marketing-research.md section 5) lists the route as the form or newsletter@indiedevmonday.com; open their site and use the current form first, and email only if there is none.
The ask is a spotlight on you and your apps, not a pitch for the tool.
Ready when: the sale is live and the site loads on shotfleet.com. Wait: 4 weeks.

Subject: `Indie Dev Monday suggestion: a solo dev who ships a workout app in 18 languages`

> Hi,
>
> I am Manu, a solo developer in the Netherlands. I ship a workout app on iOS and Android in 18 languages, and I also build tools for my own workflow.
>
> One story that might suit the newsletter: my "localized" store screenshots were the English set copied into every language folder, because my UI test could only tap English buttons. Fixing that led to a small tool, shotfleet, and its first full Android run found an onboarding page whose Next button was below the bottom of a small phone in Japanese, Korean, Chinese and Arabic. The fix in my app was 8 lines. I wrote it up here: https://shotfleet.com/the-button-nobody-could-reach?utm_source=indiedevmonday
>
> If a spotlight on my apps or that story fits, I am happy to answer questions or send images. If not, thank you for the newsletter anyway.
> Manu

Check before sending: article 3's TO VERIFY items 1 (app name), 2 (languages observed) and 6 (whether users were affected); name the app the way the store listing does.

---

## 4. asc CLI recipe pitch (App Store Connect CLI)

Where: GitHub Discussions, or an issue only if the repo's contributing page asks for ideas there: https://github.com/rudrankriyam/App-Store-Connect-CLI . Read the repo's contributing notes and discussion categories first. Do not open an issue that is only an advertisement; this is a docs and recipe suggestion, and the post must be useful without clicking anything.
Ready when: the recipe has been run end to end on a real app, so everything in the post is something you did. Today `asc screenshots` exists (`asc screenshots --help` lists upload and a local capture and frame workflow marked experimental), but the exact upload command with shotfleet's export folders has not been run: run it first and paste the real command and output. If you cannot run it, do not post.
Wait: none to expect; one reply is a good result.

Title: `Recipe: upload localized screenshots exported by shotfleet with asc`

> Hi, I am the author of shotfleet, a closed-source Mac command line tool that captures localized App Store and Google Play screenshots from one Maestro flow and checks them (free for 2 languages, paid beyond that). Disclosure done, here is the useful part.
>
> `shotfleet export` writes fastlane-style folders (`screenshots/<locale>/` for iOS). Here is what I ran to upload that folder with asc: PASTE THE REAL COMMAND AND ITS REAL OUTPUT HERE, and the asc version (`asc --version`).
>
> What I did not test: WHAT YOU DID NOT TEST (for example other device sizes or the iPad 13-inch set).
>
> If a short recipe like this would be useful in your docs, I am happy to write it as a pull request in whatever format you prefer. If it is out of scope, that is fine.

Do not say asc cannot do something unless you have read its current docs for it. The project has its own screenshot capture commands; do not position shotfleet against them, say what yours adds (one flow in every language, the per-image check).

---

## After sending anything here

Log date, recipient, what was sent, and the answer in one note. Check `site/signups.sh --visits` after 2 weeks for each `utm_source` you used (`indiedevmonday`, `consoledev`). Questions you could not answer go into the README FAQ list.
