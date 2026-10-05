# Product improvements for a paying buyer, 2026-10-05

Scope: what would give an indie developer shipping localized store screenshots more value or fewer walls, beyond the themes other notes cover (check quality, capture reliability, platform reach, refunds, first-run friction). Read: STATUS.md, README, roadmap-2026-10, market-2026, sellable-audit, review-2026-10-03, limits-text, docs/handoff.md, tests/claims.json, `shotfleet.py` on origin/main 4755d1e (0.1.1 string). Every finding says how it was checked. Nothing here ran on a device.

Constraint from the coordinator while 0.1.1 is gated: no change to `shotfleet.py`, `site/`, `packaging/` or `tests/claims.json`. So every code fix below is a proposal with the exact place to change it; the one thing implemented is documentation for agents (section 4).

## 1. Top three

### 1. `--json` reports only the last of several checks, so CI can see `exit: 1` with `problems: []` (CONFIRMED by repro)

`check_any` (shotfleet.py ~3909) checks once per report: each device folder of a multi-device run, each Play listing kind (phone and tablet sets). `run` does the same per platform (`cmd_run` loops over ios and android). Every `cmd_check` overwrites the global `LAST_REPORT` (line ~2564), and the `--json` branch of `main` (line ~3686) prints only that one file.

Repro (scratch script, not committed): a folder with `ipad/` and `iphone/` subfolders, each with a `run.json`; the real `main(["check", folder, "--json"])` and `check_any` dispatch, with `cmd_check` replaced by a stub that writes a `check.json` and sets `LAST_REPORT` the way the real one does. The iPad has a problem, the iPhone has none: output `{"exit": 1, "screenshots": [], "problems": [], "notes": []}`. The problem is in the human log on stderr and in `ipad/check.json`, but a CI step that reads `problems` (the README and `skill/shotfleet/references/ci.md` show exactly that) prints "0 problem(s)" while failing. `export --json` is fine (it accumulates `EXPORT_RESULT`). README "In CI" promises `problems` for `run` and `check`; a buyer who set `device_types` (the iPad 13" rule makes that common: an app that runs on iPad needs it) or both platforms hits this on the first CI job.

Fix (proposal, about 8 lines, device-free, testable with the same stub): keep a list `REPORTS` next to `LAST_REPORT`, append in `cmd_check`, and in `main` print `screenshots`, `problems`, `notes` as the concatenation of all of them plus a `reports` list of `{"report": path, "problems": [...]}` when there is more than one. A single report stays byte-identical, so no existing consumer breaks. Same for `mcp_call` (the MCP `run` and `check` tools return the same last-report-only text).

### 2. A missing or invalid `SHOTFLEET_KEY` turns a CI `run` into a green 2-language run (TRACED in code, not run)

`apply_free_tier` (~3892) catches `NoLicence` from `require_licence` (which raises `SHOTFLEET_KEY isn't a valid licence` for a refunded or typo'd key, and the "need a licence" text when no key is set), prints a `note:` and sets `LOCALE_CAP = 2`. `cap_locales` keeps the first two languages of an alphabetical list and `run` goes on; exit is 0 when those two pass. `export` refuses (exit 2), but a nightly `run` job just shrinks. README says so ("With an invalid key ... `run` captures only 2 languages"), so it is documented, but nothing in the machine-readable output says it: `run.json` and `check.json` have no `free_tier` or "skipped languages" field, and `--json` carries only the check. The buyer finds out when the store listing for the 16 other languages is stale, or when export fails weeks later.

Same boundary, for the interactive free tier: the two languages are the first two alphabetically (`ar`, `bg`... not the ones the trial user cares about), and the message `free tier: capturing 2 of 18 languages (ar, bg). shotfleet activate <key> unlocks every language` does not say that `--locales de,ja` picks which two (the cap applies after `--locales`, line 1548). A trial user judging the product on Arabic and Bulgarian is the wrong sample.

Fix (proposal, licence code, so after 0.1.1 is shipped): (a) when `SHOTFLEET_KEY` is set and refused, make `run` exit 2 like `export` does (CI never wants the silent downgrade; a missing key can keep the free tier); (b) write `"free_tier": true, "languages_skipped": [...]` into `run.json` and `check.json`; (c) put "pick them with --locales" in the cap message. Wording-only interim: section 4.

### 3. A buyer learns about 0.1.1 only if they run `doctor` and read its last lines (CONFIRMED by reading; product promise: "a year of updates")

`latest_release()` is called in one place, `cmd_doctor` (~2990). `run`, `check`, `export` never mention a newer version; the weekly licence check sends no version by design (the privacy page says so, and says `doctor` is the only other call: "`shotfleet doctor` also asks this site for the latest version number"). `tests/claims.json` C051 already records that the year of updates is a promise with no mechanism. The update itself works (re-running `install.sh` replaces the folder in place; it is idempotent), but a buyer who ran `doctor` once during setup has no reason to run it again. Claims: C051 is `partial`.

What can be done without touching code or the privacy page today: Gumroad's "send an update to customers" email for each release, with the changelog heading and the one-line install command, costs nothing and reaches exactly the paying buyers (owner action, a public-facing step, so only proposed here). What needs code and a privacy-page edit together (so a later release, not 0.1.1): `run` and `export` print one line "shotfleet 0.1.2 is out" after finishing, from a cached lookup (once a day, `~/Library/Application Support/shotfleet/latest.json`), off with `SHOTFLEET_NO_UPDATE_CHECK=1` and always off under `--json` and when `CI` is set. Do not ship the code without the privacy sentence, because the current text would then be false.

## 2. Ranked table

Value is to a paying buyer; cost S under 1 day, M 1 to 3; risk is to the release; "devices" means a simulator or emulator is needed to verify.

| # | Improvement | Value | Cost | Risk | Devices? | Status |
|---|---|---|---|---|---|---|
| 1 | `--json` merges all reports (+ `reports` list); same in MCP | High for CI buyers and agents (a wrong "0 problems") | S | Low: a single report unchanged | No | Proposal; repro in section 1 |
| 2 | Invalid `SHOTFLEET_KEY` fails `run`; `free_tier` and skipped languages in `run.json`; free tier hint about `--locales` | High for CI, medium for trial users | S | Medium: licence code, needs the release-gate licence rehearsal again | No (the licence is tested against a fake API) | Proposal; wording interim in the skill doc |
| 3 | Update notice for buyers: Gumroad update email now; cached one-line notice in `run`/`export` with a privacy-page edit later | Medium-high (the "year of updates" promise, and fixes like the 0.1.1 blank-frame retry never reach people who do not run `doctor`) | Email: S, owner; notice: S + page | Notice: privacy claim must change first | No | Proposal |
| 4 | `export out` when the config had both platforms: say "out-ios / out-android exist, did you mean one of them?" (README's own step 5 command is `export out`; the error today is only "no shotfleet run in out") | Medium: hits the first export of every two-platform buyer | S (3 lines in `cmd_export`) | Low | No | Proposal |
| 5 | `shotfleet licence` (or a line in `doctor`): activated or not, which key (last 4), last check, offline days left, activations used | Medium: today a buyer cannot tell whether a CI or new Mac is licensed without running `run` and reading for `free tier:` (the agent skill even tells agents not to read the licence file) | S | Low (read-only; Gumroad `uses` needs one network call, cache not needed) | No | Proposal |
| 6 | `export --dry-run` and, in `--json`, a reason per skipped language (`failed check`, `no listing in that language`, `capture failed`); today `skipped` lists only checked-bad languages and "no store listing" skips go to the log only | Medium: the first export into a git-tracked fastlane folder is a leap of faith; CI needs a machine-readable reason | S-M | Low | No | Proposal |
| 7 | `activate` with a mistyped key points at `shotfleet.com/#price`, the purchase page, which is odd for someone who already bought; point at the receipt email and `hello@shotfleet.com` | Low-medium | S | Low (licence text, claim C-licence wording tests) | No | Proposal |
| 8 | `run`/`check` write a one-screen `summary.md` for a pull-request comment (languages ok, problems, link to `index.html`) | Medium for team buyers; unproven demand | M | Low | No | Not recommended yet (roadmap L1 trigger: 3 asks) |
| 9 | Report grid and `run.json` carry timing per language and the retry count (already in `run.json` as `attempts`; not shown) | Low | S | Low | No | Skip |

What I checked and found fine (no action): the config format refuses a typo with a suggestion (`'paralel'; did you mean 'parallel'?`), a wrong type, bad TOML with line and column, a bad `[hooks]`/`[overrides]` shape, and a missing config or folder, each in one worded line, exit 2 (run from source in a scratch folder: six messages read). `export` replaces only same-size PNGs in a listing folder, so iPad and 6.5" sets stay. Exit codes 0/1/2/130 hold on every path read.

## 3. Product page versus code (tests/claims.json)

48 of 126 claims are not green; the ones that touch what a buyer does after paying: C051 "a year of updates" (no mechanism, see top 3), C045 "3 Macs and your CI" (partial: the counter is per key, a fourth Mac needs an email), C047 refund stops working at the next weekly check (a refunded key unproven until a real sale), C054 "14-day refund" (process; owned by the refunds note), C057 the install one-liner (claims.json predates go-live; the install ran live and in the release gate). Nothing else I read contradicts the code: free `check`, free `run` for 2 languages, licence-only `export` match `require_licence` and `apply_free_tier`. The one honest gap in the free-tier line is top 3's second half (which two languages).

## 4. What I implemented

Documentation only, since code is frozen: `skill/shotfleet/references/ci.md` now has a section "Two traps when a script reads the result" (checked in code on 0.1.1): a `--json` over several reports shows only the last report (trust `exit`, read each `check.json`), and a run with a missing or invalid `SHOTFLEET_KEY` captures 2 languages without failing, with the line to watch for. This is what an agent reading the skill needs until the code fixes land. `python3 -m unittest tests.test_agent_skills tests.test_docs`: 46 tests OK. No change to `shotfleet.py`, `site/`, `packaging/` or `tests/claims.json`, so the full `tools/check-claims.sh` was not run (coordinator: the Mac is overloaded, and no code changed).

## 5. Recommend building next (after 0.1.1 ships; items 1, 2 and 4 together are one small PR with unit tests, about a day)

1. Items 1 and 4 in one PR (no licence code; a test per fix; the `--json` test is the stub repro above made real with a two-device folder). Then item 2 as its own PR because it touches licence code and needs the licence rehearsal re-run.
2. Item 3's owner half now: a Gumroad update email with each release (decide with the owner; public-facing). Build the in-program notice only together with the privacy sentence, in 0.1.2.
3. Items 5 and 6 when the first buyers write about activations or about export fear; both are small and read-only.

## 6. Unverified

- Item 1 was run with a stub in place of `cmd_check` (the real `main`, `check_any` and `device_runs` were used); a run on real screenshots was not done. The same loss for `run` over two platforms and for Play listings is read from the same code, not run.
- Item 2 is traced, not run: no frozen build and no gate-ON licence environment was used. The alphabetical choice of the two free languages is read from `shipped_locales` (returns `sorted(...)`).
- Item 3: that no other command checks for updates is a grep of `latest_release`; the Gumroad update-email feature was not opened (no account access in this task).
- Items 4 to 9 are read from code and README only.
