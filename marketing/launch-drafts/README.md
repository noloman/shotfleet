# Launch drafts (Manu posts, Claude drafted)

Written 2026-10-06, updated 2026-10-07 so every claim is true for 0.1.6 (every edit is in CHANGES.md). Nothing in this folder has been posted, submitted, emailed or paid for. Manu reviews every file and posts from his own accounts.

These replace the older pre-sale drafts in `marketing/launch-posts-v2.md` and parts of `marketing/kit/` (those still say Flutter was never run on a real app). The kit's long answer list in `marketing/kit/show-hn.md` is still useful; `10-faq-objections.md` here is the updated short version.

| File | Where it goes |
|---|---|
| 01-show-hn.md | Hacker News, Show HN |
| 02-reddit.md | r/iOSProgramming (App Saturday), r/androiddev (monthly showcase thread), r/SideProject, r/FlutterDev (probably skip), r/macapps (no draft, see file) |
| 03-product-hunt.md | Product Hunt launch |
| 04-indie-hackers.md | Indie Hackers post |
| 05-newsletter-pitches.md | iOS Dev Weekly, Android Weekly, a Flutter newsletter |
| 06-short-posts.md | X, Bluesky, Mastodon: one 5-post thread, 5 standalone posts |
| 07-directories.md | AlternativeTo, SaaSHub, Awesome-ASO, awesome-maestro, Console.dev, Indie App Catalog, MCP registry, Glama (and why not awesome-ios / awesome-android-ui) |
| 08-demo-video-script.md | An 88-second cut of the 9 existing demo clips, with captions |
| 09-email-other-app-users.md | Only if you have consent. Right now there's no such list, so don't send |
| 10-faq-objections.md | Short answers for comment threads |

## Gates: check these the day you post

Calendar: launch week starts Mon 19 Oct. Show HN is Tue 20 or Wed 21 Oct. Nothing about shotfleet goes on HN, Product Hunt or Reddit on 13 or 14 Oct: that's Keysi's launch. Directory forms and private emails can go any time.

1. **0.1.6 is live.** `curl -s https://shotfleet.com/download/VERSION` prints `0.1.6`, `brew info --cask noloman/tap/shotfleet` says 0.1.6, and `https://shotfleet.com/guides` and the AnywhereRoles section on the home page both load (the drafts link to them). If one of these isn't true, cut the lines that depend on it.
2. **XCUITest is new, not proven.** It's in 0.1.6, but its device test (`tools/fixture-byoc-e2e.sh`) hasn't passed: the first run, on an overloaded Mac, lost its simulators. Every draft says "new in 0.1.6" with "not run end to end yet". Never write that it works on a device. If the test passes before you post, change the line to say only what its log shows.
3. **Linux, Docker and the GitHub Action stay out.** The 0.1.5 changelog lists the `check` Docker image and the Action, but the docs page still has `DOCKER-PENDING`, the Action repo is 404 and ghcr pulls are denied. Don't mention them anywhere until `grep -c DOCKER-PENDING site/public/docs.html` prints 0 and both are public. "Mac only" stays true.
4. **Sales count.** Gumroad's products page (read only, 2026-10-06) showed 0 sales. Re-check before posting the Indie Hackers draft; the placeholder is `[SALES: 0 as of 2026-10-06, re-check]`.
5. **Reddit rules are second-hand.** Reddit blocked all my tools (403 on `rules.json`, Chrome and the built-in browser refuse reddit.com), so the sub rules in `02-reddit.md` come from a third-party snapshot ("last checked July 2026") and the older notes. Open each sidebar and the pinned posts yourself and screenshot the rule you rely on.
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
| check flags wrong language, blank screens, store sizes; works on fastlane snapshot, screengrab and supply folders (supply since 0.1.6), no Maestro, free | site home, whats-new 0.1.5 and 0.1.6; C157, C175 |
| check on a real fastlane snapshot set found a German listing whose app was still in English | alternatives |
| AnywhereRoles (my app): check found 127 problems on the old Play screenshots, 103 translated captions over English, 15 false 'missing' lines from a 0.1.4 supply-name bug (fixed in 0.1.6), 9 others; recaptured with 0.1.4: 120 Android (15 x 8) + 108 iPhone (18 x 6), 0 problems; several failed runs first | site home, 'A real app: AnywhereRoles' (live with 0.1.6) |
| wger (Flutter): German on every screenshot; Japanese about 30% translated, check said so | demo page; C148, C173 |
| Homebrew: `brew install noloman/tap/shotfleet` (cask at 0.1.6; confirm with `brew info` the day you post) | whats-new 0.1.5; C181, C192 |
| Apple silicon only, macOS 13+; capturing needs Maestro and Java 17+, except iOS with your own XCUITest tests (new in 0.1.6, not run end to end yet) | site home, whats-new 0.1.6 |
| App and screenshots never uploaded; licence key checked with Gumroad when you activate and about once a week; `doctor` also asks shotfleet.com for the latest version number, and `doctor --fix` downloads Maestro, Java and the Android tools from GitHub, Adoptium and Google | privacy page |
| Free: check, doctor, init, run for 2 languages, no account | site home |
| $29 first 100 buyers, then $49 once per developer; a year of updates (a calendar year from the purchase; versions you have keep working); use it on up to 3 of your Macs, with spare activations for reinstalls (5 per key from 0.1.6); 14-day refund no questions asked | site home, terms, CHANGELOG 0.1.6 |
| Free licence for open-source maintainers and students | site home, terms |
| 9 demo clips from the fixture apps, at /demo | demo page, `origin/claude/demo-video` manifest.json |
| Two guides: why snapshot screenshots are all English (5 causes), and one Maestro flow in every language | `/guides`, live with 0.1.6 |
| Running your own XCUITest screenshot tests on iOS (`[capture]` table), paid like `run`, 2 languages free, iOS only; device test hasn't passed | CHANGELOG 0.1.6 |
| `shotfleet mcp` refuses a config's build and shell commands unless the call passes `hooks: true`; `check` no longer takes `ocr_command` over MCP | CHANGELOG 0.1.6 |
