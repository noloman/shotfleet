# Launch drafts (Manu posts, Claude drafted)

Written 2026-10-06. Nothing in this folder has been posted, submitted, emailed or paid for. Manu reviews every file and posts from his own accounts.

These replace the older pre-sale drafts in `marketing/launch-posts-v2.md` and parts of `marketing/kit/` (those still say Flutter was never run on a real app, and link guide pages that don't exist yet). The kit's long answer list in `marketing/kit/show-hn.md` is still useful; `10-faq-objections.md` here is the updated short version.

| File | Where it goes |
|---|---|
| 01-show-hn.md | Hacker News, Show HN |
| 02-reddit.md | r/iOSProgramming (App Saturday), r/androiddev (monthly showcase thread), r/FlutterDev (probably skip, see file) |
| 03-product-hunt.md | Product Hunt launch |
| 04-indie-hackers.md | Indie Hackers post |
| 05-newsletter-pitches.md | iOS Dev Weekly, Android Weekly, a Flutter newsletter |
| 06-short-posts.md | X, Bluesky, Mastodon: one 5-post thread, 5 standalone posts |
| 07-directories.md | AlternativeTo, SaaSHub, Awesome-ASO, awesome-maestro (and why not awesome-ios / awesome-android-ui) |
| 08-demo-video-script.md | An 88-second cut of the 9 existing demo clips, with captions |
| 09-email-other-app-users.md | Only if you have consent. Right now there's no such list, so don't send |
| 10-faq-objections.md | Short answers for comment threads |

## Gates: check these the day you post

1. **0.1.5 is live.** `curl -s https://shotfleet.com/download/VERSION` printed `0.1.4` on 2026-10-06. Several drafts mention the 0.1.5 things (check on screengrab output with timestamped names, `doctor` telling Homebrew users to `brew upgrade`, the "What's new" page with 0.1.5). Don't post before it says 0.1.5, or cut those lines.
2. **The AnywhereRoles section is on the live home page.** The numbers (127 problems, 103 translated captions over an English app; then 120 Android + 108 iPhone recaptured with 0 problems) are in claims C222 to C229 on `origin/claude/post-015-candidate`, not on `main` and not on the live site yet. The live site today says something older and different: "108 of 120 store screenshots of another of my apps flagged" (C107). If the section isn't live when you post, either use the C107 wording or drop the AnywhereRoles lines.
3. **XCUITest support is not released.** It's on the post-015 branch for 0.1.6, and its device test hasn't run yet. Every draft says "coming in 0.1.6" or leaves it out. Don't change that until 0.1.6 is on the site.
4. **Sales count.** Gumroad's products page (read only, 2026-10-06) showed 0 sales for shotfleet. Re-check before posting the Indie Hackers draft; the placeholder is `[SALES: 0 as of 2026-10-06, re-check]`.
5. **Reddit rules were read second-hand.** Reddit blocks my tools, so the sub rules in `02-reddit.md` come from search summaries and the older research notes. Open each sidebar yourself before posting.
6. `tools/check-claims.sh` green.

## Rules for every post

- Say "I made this" in every post. Never ask for upvotes, likes or reposts, anywhere.
- Price at most once per post: "$29 for the first 100 buyers, then $49, one-time". Don't say how many $29 copies are left (Gumroad doesn't show a count to buyers, and the site says so).
- Every link to the site carries `?utm_source=<channel>`; the site's counter reads only that tag.
- Don't post the same text in two places. Each draft is written for its place.
- Facts allowed are the ones in "Facts used" below. If you want to add one, find its claims row first.

## Facts used (and where they're backed)

| Fact | Backed by |
|---|---|
| One English Maestro flow, every language the app has, iOS and Android | site home; claims C001 |
| 18 languages x 4 screens, 9 min iOS / 15 min Android, M1 Pro, my app (WOD Tracker), Maestro 2.0.10 | site home, alternatives; C001 |
| Onboarding Next button out of reach in ja, ko, zh, ar on a small Android phone; English fit; fix was making two pages scroll | site home, alternatives |
| Turkish: "Next" and "Advanced" are both "İleri", warned before the run | site home |
| check flags wrong language, blank screens, store sizes; works on fastlane snapshot/screengrab folders, no Maestro, free | site home (New in 0.1.5), alternatives; C157, C175 |
| check on a real fastlane snapshot set found a German listing whose app was still in English | alternatives |
| AnywhereRoles: 127 problems, 103 translated captions over English; 120 Android (15 x 8) + 108 iPhone (18 x 6) recaptured, 0 problems | post-015 branch; C222 to C229 (gate 2) |
| wger (Flutter): German on every screenshot; Japanese about 30% translated, check said so | demo page; C148, C173 |
| Homebrew: `brew install noloman/tap/shotfleet` (tap live, cask at 0.1.4 on 2026-10-06) | whats-new 0.1.5; C181, C192 |
| Apple silicon only, macOS 13+, needs Maestro and Java 17+ | site home |
| App and screenshots never uploaded; licence key checked with Gumroad | site home, privacy; C004, C085 |
| Free: check, doctor, init, run for 2 languages, no account | site home |
| $29 first 100 buyers, then $49 once per developer, a year of updates, 3 activations, 14-day refund no questions asked | site home, terms; C054, C056 |
| Free licence for open-source maintainers and students | site home, terms |
| 9 demo clips from the fixture apps, at /demo | demo page, `origin/claude/demo-video` manifest.json |
