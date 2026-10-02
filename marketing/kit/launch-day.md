# Launch day checklist (Manu posts everything)

Owner: Manu, who does all posting from his own accounts. Claude has posted nothing and will not. Written 2026-10-02.
Plan it comes from: MARKETING.md phase 1 and research/marketing-research.md section 6.2 (Day 0 waitlist email, Indie Hackers and social; Day 1 Show HN; Days 2 to 7 directories and newsletters). The sale cannot open before Polar approves (LAUNCH.md) and the Dutch tax question is answered.

Times below are your local time (Netherlands). Show HN is timed for the US morning, which is early afternoon for you; the advice that Tuesday to Thursday is best comes from vendor blogs and is unverified. The one hard rule is that the product is runnable and you can answer for hours. Do not launch on a Friday, on a day with a flight, or on a day you cannot reply within the hour.

Files you will paste from (all in marketing/kit/ unless noted):

| What | File |
|---|---|
| Waitlist email | marketing/launch-email.md |
| Show HN title, first comment, 15 answers | show-hn.md |
| Social thread (launch-day thread) | social.md |
| Directory forms and the Console.dev email | directories.md |
| Maestro community | maestro-community.md |
| Newsletters | newsletters.md |
| Demo video script | demo-video.md |

---

## Day -1: preflight (do not skip; about 2 hours)

1. `tools/check-claims.sh` is green. If not, nothing is posted.
2. Everything in "Still to verify by running" in marketing/kit/README.md that is marked "before launch" has been run, or the sentence that depends on it is deleted from the file you will paste.
3. Clean Mac or clean user account: `curl -fsSL https://shotfleet.com/install.sh | sh`, `shotfleet --version`, `shotfleet doctor`, `shotfleet check` on a folder of screenshots with no key, `shotfleet run --locales en,de` with no key. Write down what you saw. If any of these fails, do not launch; fix first.
4. `spctl -a -vv -t exec $(which shotfleet)` on the installed binary. If it prints "Notarized Developer ID", you may say "notarized" in show-hn.md; if not, every file says "signed" only (show-hn.md explains).
5. One real purchase with FOUNDER29 and one refund, end to end: checkout, key arrives, `shotfleet activate`, all languages work, refund, key stops validating (roadmap N2). Do not skip: a failed activation is a paying buyer's first screen.
6. Assets exist and are the real ones: grid image with a planted red outline, terminal capture, ribbon image, bug image `site/public/img/bug_zh.jpg`, demo video (marketing/kit/social.md lists them). Alt text written.
7. Read, in a browser, the current rules of every place you will post that day (Show HN guidelines, r/macapps sidebar if you use it, Indie Hackers). Reddit's rules are unread by our tools.
8. Know your tags (the site's funnel counter reads `utm_source`): `hn`, `indiehackers`, `mastodon`, `bluesky`, `x`, `macapps`, `devhunt`, `uneed`, `peerlist`, `consoledev`.
9. Sleep. Show HN day is a long day.

---

## Day 0: go live and tell the list

| Time | Do | Paste from | Check |
|---|---|---|---|
| 08:00 | Coffee. Open three tabs: the site, Polar's dashboard (orders, FOUNDER29 redemptions), a terminal in the repo | none | Polar approved; checkout link in hand |
| 08:15 | `POLAR_ORG_ID=16188b30-3a8a-4fdc-8282-d350ae6ec1bb packaging/go-live.sh --dry-run <checkout link>` first (LAUNCH.md has the id) | none | "dry run clean" |
| 08:30 | The real run: same command without `--dry-run`. It builds, signs, notarizes, uploads, deploys and prints the waitlist | none | No error; the site on https://shotfleet.com/ shows Buy, not the waitlist |
| 09:00 | Run the preflight item 3 again on the live site (clean Mac or user): install line from the page, not from memory | none | Install works from the page |
| 09:15 | Buy button: open it logged out, confirm the founder price shows ($29) and the counter reads N of 100 left. Do not complete a purchase | none | Price and counter correct |
| 09:30 | Waitlist email: copy the addresses from the go-live output into BCC, subject and body as written. Only use the addresses on the list, from your own account; do not add anyone. Send once | marketing/launch-email.md | Sent; tag in the buy link is already `#price` (no utm needed for your own list) |
| 09:45 | Indie Hackers: add the product page (name, tagline, descriptions) | directories.md section 7, link `https://shotfleet.com/?utm_source=indiehackers` | Page live |
| 10:15 | Indie Hackers story post: your own short story of the unreachable Next button, not the $49 validation draft in marketing/launch-posts-v2.md (that draft predates the sale and says fastlane runs languages one after another, which is unverifiable: claims C094). Use the first-comment backstory in show-hn.md as the base; mention the price once | show-hn.md (first comment, shortened) | Posted once |
| 10:45 | Social launch thread on Mastodon, Bluesky and X, six posts each, each network with its own `utm_source` in post 1 and post 6 | social.md "Launch-day thread" | Three threads live; state $29 once, in post 6 only |
| 11:30 | r/macapps once, only if the sidebar you read today allows self-promotion and you have not posted there in 30 days (reported rule, unverified). Skip if unsure | write a short plain post from the first comment in show-hn.md; no price beyond once | Skip is fine |
| 12:00 | Step away. Answer replies on your threads as they arrive | none | See "Watch" below |
| 17:00 | First look at numbers (below). Write the three numbers down: visits, pricing views, signups or orders | none | Notes saved |
| 18:00 | Done for the day. Re-read tomorrow's Show HN files once, replace every placeholder (Maestro version, notarized or signed) | show-hn.md | `grep -n "DOMAIN\|SOURCE" marketing/kit/show-hn.md` prints nothing |

---

## Day 1: Show HN (the only post that needs your whole attention)

Go only if: Day 0 install and checkout still work this morning, nothing in "If something breaks" is open, and you are free until at least 21:00.

| Time | Do | Paste from | Check |
|---|---|---|---|
| 11:00 | Run the clean install and a `shotfleet check` again. Open the site and the buy page. Tidy your HN profile: real name, one line, your email is optional | none | Everything still works |
| 13:30 | Read show-hn.md top to bottom: title option 1, first comment, the 15 answers. Replace "Maestro 2.0.10" with the output of `maestro --version` if you ran on a newer one | show-hn.md | Facts match what you ran |
| 14:45 | Open https://news.ycombinator.com/submit. Title: option 1. URL: `https://shotfleet.com/?utm_source=hn`. Leave the text box empty | show-hn.md "Title options" | Title under about 80 characters, no superlatives |
| 15:00 | Submit. Do not share the link anywhere. Do not ask anyone to vote or comment, not even a friend | none | Post appears under "new" |
| 15:02 | Post the first comment yourself, immediately, from the file | show-hn.md "First comment" | Comment is the top comment |
| 15:05 | Open your own post from `/newest` or your profile in a logged-in tab to check it is not flagged or showing "[dead]"; if it is, see "If something breaks" | none | Visible |
| 15:05 to 18:00 | Answer every comment, in order of arrival, within about 15 minutes. Use the matching answer in show-hn.md for the question; reply to what was asked, not to the price. If you do not know, say so and say you will find out | show-hn.md "The 15 hardest likely questions" | See "How to answer" |
| 18:00 | Now every 30 minutes until 21:00. Check `site/signups.sh --visits` once (below) | none | Numbers noted |
| 21:00 | Then once an hour while the post is on the front page or comments keep arriving; go to bed when it has fallen off | none | |
| Next morning | Answer overnight comments. List the questions you could not answer well; they go into the README or FAQ | none | List saved |

Do not post the HN link on social media while it is live "to help"; vote rings are detected and punished (show-hn.md). Post the social threads on Day 0, not as a reaction to HN.

---

## Days 2 to 7 (one thing a day, none of them in a hurry)

| Day | Do | Paste from |
|---|---|---|
| 2 | Console.dev email, only if the free tier installs on a clean Mac (it does, from Day -1) | directories.md section 5 |
| 2 | DevHunt submission (GitHub login, submit button on the home page; the `/submit` path 404s) | directories.md section 2 |
| 3 | Uneed submission | directories.md section 3 |
| 4 | Peerlist Launchpad: verified profile, a launch week that starts on a Monday | directories.md section 4 |
| 4 | Newsletters, article links only, one each (not the landing page) | newsletters.md |
| 5 | Maestro Slack: announce only if the channel rules you read allow it and the paid-tools question was answered; otherwise keep answering questions | maestro-community.md |
| 5 | AlternativeTo (if not already in the queue), Indie App Catalog | directories.md sections 1 and 6 |
| 6 | Design-partner emails (first batch of 3) | outreach.md section 1 |
| 7 | Write down the week's numbers per source and the questions people asked; update MARKETING.md's measuring section | none |

Reddit ads (marketing/kit/reddit-ads.md) wait for a week of organic baseline, so start them no earlier than Day 8.

---

## Watch

Funnel by source, day, browser language and event (this prints signups with email addresses first, so do not run it on a shared screen; it needs `npx wrangler` logged in, and takes a while because it reads one key at a time):

```sh
site/signups.sh --visits | grep "$(date +%F)"
```

Each line reads `hit:<day>|<source>|<language>|<event> <count>`. Events: `view` (page loaded), `runs` (the real-run section seen), `pricing` (the price section seen), `cta` (a button clicked). Compare by source: `hn`, `indiehackers`, `mastodon`, `bluesky`, `x`, `macapps`, and the direct visits (empty source). Install and download file hits are not counted (they are static files), so installs are unknown; ask in threads and count the Polar activations.

Also keep open:
- Polar dashboard: orders, FOUNDER29 redemptions (the counter on the buy page should move; if it does not, tell Claude), refunds.
- Your inbox: refund and support emails. Write down the minutes each one takes (MARKETING.md: stop marketing and fix setup friction first if support per sale passes 30 minutes).
- Hacker News: your post's comment count and rank, and https://news.ycombinator.com/newest for the first minutes.

Do not read anything into the first hours. This plan has no conversion forecast to compare against (research section 6.4); the decision rules are in STRATEGY.md (50 sales at $29 within 60 days keeps investing; under 15 means a free or open tool).

---

## How to answer questions (any channel)

1. Plain, short, first person. No "great question", no emoji, no exclamation marks.
2. Answer what was asked. Never reply to criticism with the price or a discount.
3. If you do not know: "I do not know. I will find out and reply here." Then do.
4. Only state things you ran or that are in tests/claims.json as proven, evidence or fixed. If it is partial, say the narrow version (show-hn.md answers do this).
5. A bug report is a gift: thank them, reproduce, file it, say so in the thread.
6. Closed source and `curl | sh` questions: answer from show-hn.md answer 1; do not argue.
7. Mention that you built it whenever the tool comes up. Never DM anyone who did not write to you.
8. Do not edit the HN title after posting unless a moderator asks.
9. Never say: Flutter or React Native "work" on real apps, it "catches all localization bugs", Maestro endorses it or that fastlane "is slow" or "not parallel".

---

## If something breaks

Stop posting new things first; keep answering. Write down the time and what you saw.

| Problem | Do |
|---|---|
| `install.sh` fails or the download 404s | Say so in the thread within minutes ("the installer is broken for X, fixing, thanks"). Fix by re-running `packaging/release.sh` or asking Claude to check `site/public/download` (VERSION, tarball, .sha256). Test on a clean Mac before saying it is fixed |
| Checksum mismatch reports | Treat as urgent: it is a real integrity problem. Pull the download (ask Claude to remove the tarball from `site/public/download` and redeploy), say so publicly, rebuild |
| Checkout or licence activation fails for a buyer | Reply by email within the hour, refund immediately if they ask, find the cause in Polar's activation records, tell the thread what happened |
| Counter does not move or shows a wrong number | Remove the claim from your next posts; tell Claude. Never type a number by hand into a post |
| A statement in a post or the site turns out false | Correct it in the thread the same hour ("I said X; that is wrong, the truth is Y") and tell Claude to fix the site and add a test to tests/claims.json. Do not delete the post |
| Site down or wrong page | Check `curl -sI https://shotfleet.com/`; Cloudflare dashboard; if the go-live deploy is the cause, ask Claude to revert the go-live commits and redeploy the waitlist. There is no one-command rollback script |
| Show HN is flagged, shows [dead] or does not appear | Do not repost. Email hn@ycombinator.com once, politely, asking whether it was flagged and why; accept the answer. Do not ask friends to vouch |
| A harsh comment | Answer the technical content, thank them for the feedback, move on. Never argue about closed source |
| A real security concern about the binary | Take it seriously, say what you know and do not know, offer to help check (Little Snitch, `spctl`), fix if real |
| You cannot keep up | Say so in the thread once ("slow to reply, back at HH:MM") and keep the promise |

After 48 hours, write one paragraph: what happened per source, what broke, what you would change. Put it in MARKETING.md. Then stop and let the numbers accumulate.
