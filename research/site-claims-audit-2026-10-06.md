# Site claims audit, 2026-10-06

Read only: nothing on the site was changed. I checked the live site (https://shotfleet.com, serving 0.1.3, `download/VERSION` = `0.1.3`) and `site/public` on origin/main 52f33df (the 0.1.4 site with the informal copy), and compared each claim with:

- the code: `shotfleet.py` on 52f33df (VERSION 0.1.4);
- the Gumroad product page https://8954369651852.gumroad.com/l/shotfleet, fetched without logging in on 2026-10-06;
- `tests/claims.json` (161 rows: 63 proven, 53 evidence, 22 fixed, 18 partial, 2 unverifiable, 2 removed, 1 untested);
- `docs/compat.md` and the research notes it cites.

**Live and main differ only in wording.** A diff of the visible text of every page shows no changed fact, price or limit. Main also adds the "What it saves you" section, the skills text in the docs and the c3 to c9 demo clips. So each finding below applies to both, unless the row says "main only".

## Verdict on "Free at launch"

**Misleading. Replace the heading with "Free".**

What is really free, in the code (`shotfleet.py:4306-4462`, `main_dispatch` at 4494):

- `check`, `doctor` and `init` never call the licence check. No licence, no account, no network call to Gumroad.
- `run` without a valid licence captures `FREE_LANGUAGES = 2` languages (`shotfleet.py:4311`). By default that's the first two of the app's languages, or the ones picked with `--locales`. Both platforms and the iPad and tablet sizes are included, because the cap only counts languages (claims C044). The MCP `run` tool has the same cap.
- `export` is refused without a licence (`require_licence()` at 4494).
- **The cap is per run.** `cap_locales` (4318) cuts each run to 2 languages, and the test `FreeTierOnAFrozenBuild.test_the_cap_is_per_run_two_runs_of_two_languages_give_four` pins this. So a free user can capture every language, two at a time, and copy the files by hand. Only `export` and the convenience of one run are really paid. This is a business decision for the owner, not a buyer risk. I don't suggest putting it on the site.
- **Nothing ends the free tier.** There is no date, no version check and no build switch. `FREE_LANGUAGES` is a constant.

How each place describes it:

| Where | Wording | Time limit? |
|---|---|---|
| index.html:337 (live and main) | "Free at launch" | **yes, it suggests the free tier will end** |
| terms.html:42 | "`shotfleet check` is free for everyone, and `run` is free for up to 2 languages" | no |
| docs.html:75 | "check, doctor and init are always free" | **no, it says "always"** |
| alternatives.html table | "Free: check and 2 languages in run" | no |
| llms.txt | "`check` is free for everyone. `run` is free for up to 2 languages." | no |
| index.html JSON-LD | Offer "Free tier", price 0 | no |
| Gumroad description | "check is free for everyone, and run is free for up to 2 languages" | no |
| Gumroad refund fine print | "The free tier keeps working either way." | no |
| claims.json C048 | "Free at launch: capture 2 languages with run; no account" (proven) | proves the cap, not the "at launch" |

So "at launch" is the only time-limited wording anywhere, and it contradicts "always free" in the docs. A buyer reads "at launch" as "free for now, paid later". That makes the free tier look like a trial, which it isn't, and it puts doubt on the promise in the terms. Suggested heading: **"Free"**, or **"Free, no licence needed"**. The three bullets are correct: "Check any screenshots, from fastlane or by hand", "Capture up to 2 languages with `run`", "No account". If the owner wants to keep the right to change the free tier, the honest way is a sentence in the terms ("I may change what the free tier does in a later version; the version you have keeps what it has"), not "at launch" on the price card.

## Findings, wrong and misleading first

Verdicts: **wrong**, **misleading**, **stale**, **unverifiable**, **correct**. Line numbers are for `site/public/*` on 52f33df.

### Wrong or misleading

| # | Page | Exact sentence | Verdict | Evidence | Suggested wording |
|---|---|---|---|---|---|
| 1 | index.html:337 | "Free at launch" | misleading | No time limit in code (`shotfleet.py:4311`, `require_licence` 4404); docs.html:75 says "always free"; terms, Gumroad, llms.txt have no time limit | "Free" |
| 2 | index.html:311 and 320, docs.html:61, alternatives.html:89, demo.html:122, llms.txt:17, Gumroad description | "Built for macOS 13 or later on Apple silicon; tested on macOS 27." | misleading | docs/compat.md:49-51: every device run was on one Mac on macOS 27.0. macOS 14.8.9 and 15.7.9 ran only install, `--version`, `doctor` and `check`, and only for 0.1.1, not 0.1.2+. macOS 13 and 26.0-26.2 were never run. "Built for 13" is a Mach-O minimum (C131: "a build fact, not proof that it runs") | "I build it to start on macOS 13 or later on Apple silicon. I've only done full runs on macOS 27. On macOS 14 and 15 I've checked that it installs and that `check` works. I haven't tried macOS 13." |
| 3 | index.html:328 (and terms.html:40) | "Up to 3 of your Apple silicon Macs and your CI, unlimited apps" | misleading | It's 3 activations for life, not 3 Macs at a time. `cmd_activate` (`shotfleet.py:4365-4381`) counts one Gumroad use per new activation. `cmd_deactivate` (4392) can't give one back. A Mac counts as "known" only while its `licence.json` has the key (4372), so a reinstall, a new user account or deactivate-then-activate on the same Mac uses another one. C045 is "partial" for this reason | "3 activations, for up to 3 of your own Macs, plus your CI. Setting up the same Mac again (new macOS, new user, or after `deactivate`) uses one too. If you run out, email me and I'll reset it." |
| 4 | index.html:139 (hero caption) | "I didn't change anything in the app to get them." | misleading | The same page, index.html:177, says "It was a small fix in my app: I made two pages scroll" (CrossfitTracker commit 687ffccd, C106). These screenshots were taken after that fix. C006 proves the mechanism (launch arguments, per-app locale), not that the app wasn't changed | "I didn't add any test code or anything else to the app to get them." |
| 5 | index.html:329 | "A year of updates; after that your version keeps working while macOS and your tools allow" | misleading | It leaves out the licence check. After the first year the program still asks Gumroad weekly and stops unlocking after 30 days without an answer (`shotfleet.py:4424-4433`). If the Gumroad product or API goes away, every paid Mac drops to the free tier. terms.html:48 says this ("as long as the licence check can run"); the price card doesn't | "A year of updates. After that, the version you have keeps working for as long as macOS, Xcode and Maestro allow, and the licence check with Gumroad still works." |
| 6 | index.html:327 | "Every language, both platforms, iPad and tablets, and export to fastlane" | misleading | Free users already get both platforms and the iPad and tablet sizes. The cap counts languages only (C044, `TierReachesBothPlatformRuns.test_the_cap_counts_languages_only_so_ipad_and_tablet_sets_run_in_both_tiers`). A buyer can think the free tier is iPhone-only or one platform | "Every language and export to fastlane. Both platforms, iPad and tablets work in the free version too." |
| 7 | index.html:325 and 333, terms.html:55, Gumroad description | "$29 launch price, first 100 buyers" / "the first 100 buyers pay the founder price" | misleading (small) and partly unverifiable | Gumroad page: list price $49 (`price_cents: 4900`), code FOUNDER29 $20 off is auto-applied (`discount_code` in the page JSON). The 100 limit isn't visible publicly (STATUS.md:17 says "limit 100"). research/refund-process-2026-10-05.md:40: a refunded FOUNDER29 sale probably still counts as one of the 100 (inference from Gumroad's source). Not tested: whether the owner's test purchase used one, and what the page shows after use 100 (strategy-roadmap-2026-10-05.md:167). There's no way for a buyer to see how many are left | "$29 for the first 100 sales, then $49. Gumroad applies the $29 by itself, so you see the real price at checkout." |
| 8 | index.html:325, llms.txt, Gumroad | "Prices are before VAT where it applies." | misleading (small) | terms.html:55 says Gumroad collects "sales tax or VAT". Gumroad adds tax on top of the price (research/gumroad-setup.md:33), and in some US states that's sales tax, not VAT. A US buyer told "before VAT" doesn't expect tax | "Prices are before VAT or sales tax, which Gumroad adds at checkout where it applies." |
| 9 | privacy.html:52 | "whether the call should count as an activation (only the first call on a new Mac does)" | wrong (small) | Activation makes two calls: first `increment_uses_count=false` to look, then `true` to count (`shotfleet.py:4370` and 4376). It's the second call that counts | "and whether the call should count as an activation (only one call counts, when you activate on a new Mac)" |
| 10 | privacy.html:52 | "It sends nothing else. `shotfleet doctor` also asks this site for the latest version number" | misleading (incomplete) | `doctor --fix` downloads from github.com (Maestro), api.adoptium.net (Java) and dl.google.com (Android tools) with the header `User-Agent: shotfleet/<version>` (`shotfleet.py:3147-3150`, 3170, 3204). So the program version does go to those three hosts. The MCP `doctor` tool also asks shotfleet.com (`shotfleet.py:4201`) | Add: "If you let `shotfleet doctor --fix` download what's missing, it gets Maestro from GitHub, Java from Adoptium and the Android tools from Google. Those requests carry your IP address and shotfleet's version number. Nothing about your app is sent." |
| 11 | terms.html:58 | "shotfleet is provided as it is. ... If something goes wrong, my liability is limited to what you paid." | misleading (legal risk, inference) | For EU consumers, the legal conformity rights for digital content (Directive 2019/770) can't be signed away, and research/refund-process-2026-10-05.md:88 lists what the law asks a seller to state (address, withdrawal information, conformity rights), which the terms don't give. Gumroad is the merchant of record, which may cover part of this. Not checked by a lawyer | "I can't promise it will work with every app, every Xcode or every emulator. As far as the law allows, my liability is limited to what you paid. This doesn't take away any rights the law gives you as a consumer." Get a lawyer to check this one. |
| 12 | index.html:155 (main), similar hero index.html:47 | "Then it reads every image back and compares the text with your app's own strings, so a screen that came out in the wrong language gets caught." | misleading for some languages | docs.html:269: macOS text recognition can't read Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts. On Android (pixels, Maestro 2.0.10) those screens are "could not verify", not a pass. A buyer with a Hebrew or Hindi listing would expect full checking | Add after it: "For a few scripts macOS can't read, like Greek, Hebrew and most Indian scripts, it tells you which screens it couldn't check." |
| 13 | terms.html:44 | "activating again on a Mac that already holds it counts nothing" | misleading (small) | True only while that Mac's `licence.json` still has the key (`shotfleet.py:4372`). After `deactivate`, a new user account or a clean install, the same Mac counts again | "Activating again on a Mac that still has the key saved counts nothing. After `shotfleet deactivate`, a new macOS install or a new user account, it counts again." |

### Numbers from one run on my own Mac

All of these are labelled "on my app" or "on my own apps", so none is wrong. But each is one run, on one 32 GB M1 Pro, and some readers will take them as typical.

| # | Page | Exact sentence | Verdict | Evidence | Suggested wording |
|---|---|---|---|---|---|
| 14 | index.html:144, 155, 230; alternatives.html; docs.html:281 | "9 min · 15 min for that run on iOS and on Android" / "18 languages × 4 screens took 9 minutes on iOS and 15 on Android, on one Mac" | correct, one run | PLAN.md 2026-10-01: iOS 534 s, Android 15m24s, first attempt (C007, C105, "evidence"). A later run gave 404 s and 415 s for 19 languages (demo.html, C147), so the numbers aren't stable from run to run. docs.html:272: "Four simulators on a loaded Mac can take many times longer" | "On my M1 Pro with 32 GB, one run of 18 languages × 4 screens took 9 minutes on iOS and 15 on Android. Your Mac and your app will give other times." |
| 15 | index.html:145, 177; alternatives.html | "4 languages shared one unreachable Next button on Android" / "Japanese, Korean, Chinese and Arabic all got stuck" | unverifiable in part | C012 and C158: only the Chinese screenshot (img/bug_zh.jpg) is kept. "No run log, flow or commit is kept in the repo"; ja, ko and ar are only stated | Keep the sentence. It's my own story, and the fix commit exists. If I want it watertight, add the other three screenshots to `img/`. |
| 16 | index.html:146 | "108 of 120 store screenshots of another of my apps flagged by `shotfleet check`: translated captions over an English UI" | correct, one app | research/real-apps.md:85 (C107, "evidence"): one of the 120 was viewed by hand | "On another of my apps, `check` flagged 108 of its 120 store screenshots: the captions were translated, but the app under them was still in English." (the same fact, a bit clearer) |

### Stale

| # | Where | Text | Verdict | Evidence | Suggested change |
|---|---|---|---|---|---|
| 17 | tests/claims.json C080 | where_text "I'll email you once, when it's ready." on index.html | stale | Not on index.html (live or main) any more. The privacy.html part ("To send you one email when shotfleet is available to buy") is still there | Drop index.html from `where`/`where_text`. Keep the privacy part as "unverifiable" (a commitment). |
| 18 | tests/claims.json C088 | "You're on the list." / "One more thing, if you like: what do you build with?" on index.html, status proven | stale | Neither sentence is on index.html now (`grep` finds nothing; there's no signup form). The proof tests a form that is gone | Set status to "removed" with a note that the waitlist form was taken off at go-live. |
| 19 | tests/claims.json C056 | proof: "FOUNDER29 ... which does not exist yet" | stale proof | STATUS.md:17: FOUNDER29 is live, $20 off, limit 100, auto-applied; the Gumroad page JSON shows it | Update the proof. Keep the open point: what the page shows after use 100. |
| 20 | tests/claims.json C057 | proof: "`download/VERSION` is 404: no release is published", status untested | stale | `https://shotfleet.com/download/VERSION` returns `0.1.3` (2026-10-06) | Re-test install.sh on the live site and update the row. |
| 21 | tests/claims.json C045 | proof: "Never run against the real Gumroad with this product (no product exists yet)" | stale proof | The product exists and is published (STATUS.md:17) | Update. If a real activation has been done, say so; if not, say "product live, no real activation test yet". |
| 22 | docs/compat.md:41-42 | Flutter: "works up to the build; no device run"; Expo: "works up to the build; no device run" | stale | research/frameworks.md section 15 (line 246, 2026-10-03): wger and obytes ran end to end on iOS and Android. The site (index.html:320, demo.html, C035) already says this | Change both rows to: "real run 2026-10-03: wger (Flutter, debug build) and the obytes template (Expo) on iOS and Android, see research/frameworks.md section 15". |
| 23 | demo.html "Releases" list (main) | newest entry is 0.1.3 | stale once 0.1.4 ships | CHANGELOG has 0.1.4 (2026-10-06) | Add the 0.1.4 release gate line once it's written down, or say "0.1.4: no device gate" if there wasn't one. |
| 24 | demo.html:135 (main), page source | `<!-- TODO(coordinator): the Maestro 2.11.0 vs 2.0.10 quiet-Mac measurement ... Not public text until then. -->` | correct but public in the page source | An HTML comment, not shown on the page, but crawlers and AI readers see it | Move the note to docs/handoff.md. |

### Unverifiable (promises that depend on me or on Gumroad)

| # | Page | Exact sentence | Verdict | Evidence | Suggested wording |
|---|---|---|---|---|---|
| 25 | terms.html:51, index.html, Gumroad refund policy | "You can ask for a refund within 14 days of buying and you'll get it, no questions asked" | correct as a promise; the process is by hand | C054 "partial": refunds are done by hand in Gumroad (docs/refund-runbook.md). Gumroad tells buyers to reply to the receipt, which goes to the support email set in Gumroad (refund-process-2026-10-05.md:90). Not checked: that this support email is hello@shotfleet.com | No change to the text. Check that the Gumroad support email is hello@shotfleet.com. |
| 26 | terms.html:52, docs.html:229 | "A refund ends the licence. The key stops unlocking every language and `export` the next time shotfleet checks it with Gumroad" | correct in code, never tried for real | `gumroad_verify` reads `refunded`/`chargebacked`/`disputed` and the 404 "disabled" answer (`shotfleet.py:4352-4362`). strategy-roadmap-2026-10-05.md:295: "whether a refunded real key is refused" not tested | No change. Test it with the first real refund. |
| 27 | terms.html:48, index.html:329, docs.html:77 | "A year of updates is included." | correct, not enforced | C051 "partial": downloads are open to anyone (`install.sh`, `/download`), the key never expires, and no code compares a release date with a purchase date. Today every buyer gets every update. Harmless for buyers, but a future "renewal" would need new code, and that code mustn't break "your version keeps working" | No change now. When renewal comes, give it a date in the terms. |
| 28 | privacy.html:68 | "I will delete the waitlist within 30 days after I send the launch email, or sooner if you ask." | unverifiable, at risk | C081 "partial": nothing does this automatically. STATUS.md:29 and :85 still list the launch email as not sent, so the 30 days haven't started. If the email is never sent, the list is kept with no end date | "I'll delete the early-access list by 2026-11-30, or sooner if you ask." (a fixed date doesn't depend on the email) |
| 29 | alternatives.html table and text | ButterKit "Free (watermarked), Pro $99 once", "5 Macs and a 14-day refund"; AppScreens "Pro $99/yr, Scale $180/yr" | correct on 2026-10-06 | Re-fetched butterkit.app/pricing and appscreens.com/pricing on 2026-10-06: the same prices and limits. ButterKit's pricing page doesn't say it captures from the Simulator; the table says "Yes (from the Simulator)" | Change the date to "Checked on 2026-10-06". For "Yes (from the Simulator)", point to the ButterKit page that says so, or change it to "Not stated on its pricing page". |
| 30 | index.html:311, terms.html:43 | "there's no Intel build yet" / "for now" | a soft promise | ROADMAP doesn't plan an Intel build that I could find | If there's no plan: "There's no Intel build." |

### Checked and correct

| Page | Sentence | Evidence |
|---|---|---|
| index.html:334, terms.html:48, docs.html:229 | "The licence is checked online once and then about weekly, and works offline for 30 days (a CI key is checked on every run)." | `LICENCE_RECHECK_DAYS, LICENCE_OFFLINE_DAYS = 7, 30` (`shotfleet.py:4306`); the CI key path at 4408-4413 checks on every `run`/`export` and lets the run through if Gumroad can't be reached (C046 proven). It's only checked when you use `run` or `export`, which "about weekly" covers |
| docs.html:252 | the CI key "fails open ... a refunded or disabled key keeps working until a run reaches Gumroad" | `shotfleet.py:4409-4411`, honest and complete |
| terms.html:42, docs.html:75, llms.txt | "check is free for everyone, and run is free for up to 2 languages" | `shotfleet.py:4311`, 4494-4496; C032, C048 proven |
| index.html:139 and others | "your app and screenshots are never uploaded" | Every network call in `shotfleet.py`: Gumroad verify (4342), shotfleet.com VERSION (3062), doctor --fix downloads (3170, 3204), Maestro on 127.0.0.1 (1284). None sends an app or a screenshot. Hooks are the user's own commands |
| privacy.html:52 | Gumroad gets "your key, the product ID, and whether the call should count"; "no Mac name, no activation id and no program version"; "Python's standard user-agent string" | `shotfleet.py:4339-4342`: the form has exactly those three fields, and the Request has no headers, so the user-agent is Python-urllib |
| privacy.html:36 | "By default this site sets no cookies and loads nothing from other servers." | `_headers` CSP allows only Google hosts, and ga.js loads them only after consent (C076). No external `src` in any page |
| terms.html:44, docs.html:229, Gumroad | "A key can be activated 3 times"; deactivate can't give one back | `MAX_MACS = 3`, `shotfleet.py:4374-4376`, 4397 (C050 proven; the reset by hand hasn't been tried) |
| terms.html:55 | Gumroad is the merchant of record; may refund on its own in the first 90 days; Brazil's 7 days | research/refund-process-2026-10-05.md:33, 78 (verified from Gumroad's help) |
| index.html, alternatives, docs, llms.txt, Gumroad | $29 / $49, 14-day refund, 3 activations, a year of updates | the same on every page and on Gumroad (C042 proven) |
| index.html:320, alternatives.html:88, llms.txt | Flutter and React Native "run end to end on a real Flutter app, wger, and a real Expo app, the obytes template, on iOS and Android, 2026-10-03; other apps and bare React Native not yet run" | research/frameworks.md section 15 (C035). Correct and hedged. wger was a debug build, and docs.html:268 warns about the DEBUG banner |
| docs.html:62, 64 | "Tested with Xcode 27.0", "Xcode 26.x has not been run", Maestro "tested with 2.0.10 and 2.11.0" | docs/compat.md:12, 52 |
| docs.html:280 | "iOS 27: one simulator and one language ran with 0 problems" | docs/compat.md |
| demo.html evidence list | release gates, hosted runners, real apps | C143-C153 (evidence rows with records); each says what wasn't run |

## Outside the site, but buyers see it

- **The Gumroad seller name is "8954369651852"**, with the default avatar and `is_verified: false` (page JSON). On the checkout page, a buyer pays a number, not "Manuel Lorenzo Parejo". That hurts trust at the moment of paying. Set the profile name and picture in Gumroad settings.
- The Gumroad description still says "every language your app ships", the old wording. Harmless.
- Gumroad's own page has its Google Analytics and Facebook pixel flags on (`gr:google_analytics:enabled`, `gr:fb_pixel:enabled`). privacy.html links to Gumroad's policy, which covers this. No change needed.

## Method

- Live pages fetched with curl on 2026-10-06. Main read from `site/public` on 52f33df. Visible text diffed page by page.
- The code read in full around the licence (`shotfleet.py:4302-4521`), the version check (3059) and the downloads (3147-3210). Every `urlopen` in the file listed.
- Gumroad: the public page HTML (product JSON: `price_cents`, `discount_code`, `refund_policy`, `description_html`). I didn't log in and didn't buy anything.
- claims.json: every row with a `site/public` location whose status isn't proven, fixed or removed, plus C042-C056, C080, C088, C131.
- No simulators, emulators or the device lock were touched.
