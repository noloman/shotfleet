# 10. Contributing

Scope: how to change shotfleet without breaking it or its promises: the standing rules from the owner, repo conventions (claims discipline, wording, branches, claim ids, merges, commits, reviews), recipes for the common changes (a language, a check, a command, a config key, an MCP tool, a store rule, the Maestro matrix), what not to do, and a first-week checklist. Anchors are `shotfleet.py:LINE` at `7e5176c` (0.1.7). The 0.1.6-era recipe page is [../architecture/10-making-changes.md](../architecture/10-making-changes.md); this chapter is checked against 0.1.7.

## 10.1 Standing rules (from the owner)

These come from the owner (Manu) and from incidents ([11](11-history-and-decisions.md)). An agent or engineer follows them without being asked each time.

1. **Ask before any outward action.** Posts, emails, account or Gumroad changes, ads, deploys, publishes, releases, pushes to a shared branch, GitHub Actions runs, anything that spends money: only with the owner's explicit yes for that exact action, every time. Reading, building locally, running tests and committing on a branch are fine.
2. **No GitHub Actions.** All workflows are `workflow_dispatch` only; the local gate is the gate (D13 in [11](11-history-and-decisions.md)). Commit messages carry `[skip ci]`.
3. **One device job at a time.** Anything that boots a simulator or emulator takes the lock in `docs/device-queue.md` first, has a hard time limit, and releases the lock. The Mac is shared by many sessions.
4. **Never kill, delete or stop what you did not create.** Prove ownership first (process cwd, parent chain, a log naming the folder). A deleted work folder once voided a release gate run.
5. **Do not edit shared state in parallel.** Gumroad, deploys, `main`, the release folder: check which other sessions are active and tell the coordinator first. Many agents work in the same repo at once; each uses its own worktree.
6. **Do not rebuild instead of publishing the tested artifacts.** A release ships the exact bytes that passed the gate (`packaging/publish.sh` checks their SHA-256). Rebuilding makes different bytes (D11).
7. **Do not re-add Polar or Lemon Squeezy.** shotfleet is sold through Gumroad only; their code was removed on 2026-10-03 and the reasons are in `research/gumroad-setup.md` (D4).
8. **Never put secrets in the repo or in chat:** no licence keys, buyer emails, API tokens, notary credentials, cards. (`GUMROAD_PRODUCT_ID` and the GA4 measurement id are public by nature.)
9. **Never claim what was not run.** Public words and docs say only what a test, a fixture run or a dated record shows ("tested" needs a run).
10. **Do not run a release gate on a loaded Mac**, and do not install a new iOS runtime while jobs are queued (it changes `latest_ios_runtime()` for every run on the machine).

## 10.2 Repo conventions

### Claims discipline

**Every public promise is a row in `tests/claims.json`.** A "public promise" is any number, price, date, version support, "works with X", "tested on Y" or behaviour statement on the site, the README, `llms.txt`, the skills, launch texts or the docs page. A row is:

```json
{"id": "C280", "claim": "...", "where": ["README.md", "site/public/docs.html"], "where_text": ["exact quote in the first file", "exact quote in the second"],
 "status": "proven|evidence|fixed|partial|unverifiable|untested|removed|policy",
 "proof": "...", "layer": "unit|site|fixture|device|legal", "assertion": "...", "fix": "..."}
```

`tests/test_claims.py` enforces: the schema; each `where_text` quote is still in its file (so changing words without updating the row fails); a `removed` claim really is gone; no `false` claim is published; `fixed` / `removed` rows say how and why (`fixed_by` is `code`, `wording` or `removed`, and a code fix names its test); a `proven` row names a test class and method that exist (`proof` text like `ClassName.test_name`); the status counts add up. `evidence` means a dated record exists (in `research/` or a release folder) rather than an automated test; `policy` is the owner's decision with nothing to test. Prove a claim at the lowest layer that can: a unit test, then a site test, then a fixture or device run. If nothing can prove it yet, soften the words until they are true. See [06](06-packaging-and-release.md) for how the whole gate runs.

**Narrow wording.** Say what was run and no more: "Flutter and React Native were each run end to end once" rather than "works with Flutter". `tests/test_site.py` (`BANNED`) rejects phrases such as "works with any app", "works with every", "guarantee", "ai-powered", "universal binary", and a list of earlier wrong claims. Prices: only $29 and $49 are shipped prices (`PriceAgreement`). Version statements: `Maestro (tested with 2.0.10 and 2.11.0)` is pinned in the README, the skills and a test.

**Wording rules.** Plain English, first person where the author speaks, no marketing tone, **no em dashes** anywhere public (tests enforce it on the site, the skills and the docs page; these engineering docs follow it too), no emoji.

### Code conventions

See [01 section 1.9](01-runtime-architecture.md#19-conventions): `Fail` for user-facing errors with a sentence that names the fix; no tracebacks for known failures; argv lists not shells; timeouts everywhere a device can hang; pure core / impure edge; `canon()` before comparing locales; `norm()` before comparing text; `ponytail:` comments mark deliberate shortcuts with their ceiling, so grep for them before "fixing" something naive.

### Branches, worktrees and claim ids

- **Branch names:** `claude/<topic>` (for example `claude/docs-refresh`, `claude/workarounds-text-recognition`); work scoped to a release carries its number: `claude/013-versioned-urls`, `claude/015-no-banners`, `claude/016-licence-fixes`, `claude/017-upload-gate`. This worktree's branch, `claude/app-launch-readiness-d770fd`, is an auto-named one. `main` is the integration branch; the owner or the release coordinator merges.
- **Worktrees:** `git worktree add /Users/manu/Developer/shotfleet-rc-build/<name>-wt -b claude/<name> origin/main`. Durable locations only: `/tmp` is wiped by a reboot and other sessions clean up there. Merge trees and release folders also live under `shotfleet-rc-build/` ([06](06-packaging-and-release.md)).
- **Claim ids** are sequential `C###` (the highest in this worktree is `C280`; `origin/main` has already moved on to at least `C287`, commit `b5dd971`). Parallel branches both pick "the next free number" and collide. The merge tool `claims_merge.py` (kept in `/Users/manu/Developer/shotfleet-rc-build/`, **not** in the repo) does a 3-way merge of `tests/claims.json` by id: it keeps one-sided changes, stops if both sides changed the same row, and **renumbers ids that both sides added differently** to the next free numbers, printing the mapping (for example the 0.1.7 merge `97d897e` renumbered C266 to C280, recorded in its commit message). Use it, then fix any quote in code or docs that cites the old id, and run the full check. Do not hand-edit a 273-row JSON file in a merge conflict.
- **Merge discipline:** merge and check in a durable `merge-tree` worktree; push only on the check's own exit code (`sh tools/check-claims.sh > <durable log> 2>&1; echo rc=$?`, push when `rc=0`; **never gate through a pipe**, which hides the exit code). Commit messages end with `[skip ci]`.

### Commits and reviews

- Subject in the imperative with what changed and for whom (`git log` shows the house style: "0.1.7 upload gate: store coverage matrix, check --compare, export --print-upload [skip ci]"); body explains why. End with the attribution trailer the session was told to use (`Co-Authored-By: ...`).
- A change that touches `shotfleet.py` needs: unit tests that fail without the change; the README / docs page / skill / `llms.txt` / CHANGELOG updated in the same commit when behaviour is user-visible; claim rows updated; `tools/check-claims.sh` at exit 0. A change that touches device behaviour also needs the **device run named in its PR** (or an explicit "not run on a device" statement), under the device lock.
- Open PRs that change `shotfleet.py` are rebased on `main` before merge, "do not merge blind" (`docs/handoff.md` section 13). Review notes for risky areas (licence, MCP) are written as files and cite lines; the 0.1.6 licence reviews found their issues that way ([05](05-licence-and-money.md)).
- `git config core.hooksPath .githooks` once per clone makes `.githooks/pre-commit` run `tools/check-claims.sh` on every commit. (A fresh worktree may not have it set; run the script by hand.)

## 10.3 Recipes

### Add a language

Three different things are called "adding a language":

1. **A store listing language** (so `export` can name its folder): add the code to `APP_STORE` and/or `PLAY` (`shotfleet.py:252`, `:255`; copied from fastlane's folder names, `marketing/store-locales.md`), then check `store_code` (`:272`) maps the app's locale onto it (`PRIMARY` when a language has several regions, `CANON` / `LANG_CANON` for alias spellings). Test next to the Export tests.
2. **Making `check` judge a language:** `TESSERACT` (`:3345`) for the Tesseract name; `OSD_SCRIPT` if its script needs script detection; `LATIN_UNLISTED` (`:2909`) if it is Latin script that Vision lacks; `TWINS` (`:2891`) or `CYRILLIC` if detection confuses it with another; extend the Docker image's `LANGS`; measure with `tools/langmatrix.py` and a real screenshot set (`research/all-languages.md`).
3. **Reading a new translation-file format** (for `strings = "glob"`, `check --strings`): add a branch in `read_translation_file` (`:646`) returning `{locale: {key: text}}` with plurals as `key#form`; teach `locale_from_path` (`:486`) the naming convention; add the extension to the "don't know how to read" message; if a framework uses it, add to `FRAMEWORKS` (`:853`) and a branch in `detect_project` (`:4538`). Parse files as data, never execute them. Tests in `SourceFiles`/`LocalizationFormats` (`tests/test_shotfleet.py`) and `tests/test_projects.py`; update README "Supported", the docs page, `skill/shotfleet/references/config.md`.

### Add a check rule

Pure helper or inline condition in `cmd_check`; `problems` when a store or the user would be hurt, `notes` otherwise; a unit test with a faked reader; the line in `skill/shotfleet-review/SKILL.md`'s table (a test checks the fragments exist in the program); a CHANGELOG bullet; a claim row if public text promises it. Never fail on a reader that may simply have failed to read ([03 section 3.12](03-check-ocr-export.md#312-extending-the-check)).

### Add a store rule or size

`APPLE_SIZES` (`:4805`) for sizes; `store_rules` (`:4879`) for counts and rules; `coverage_matrix` (`:3448`) only reports what `store_rules` already knows, so change the rule first. `tools/apple-specs-watch.py` compares every size on Apple's page with `APPLE_SIZES` (run monthly through `tools/watch-upstream.sh`); the prose rules are read by a person once a month. Source: `research/store-specs.md`. Update the claims that quote the rule.

### Add a config key

Add to `KEYS` (`:60`) (or `CAPTURE_KEYS`, `TABLES`, `HOOK_EVENTS`, `EXPECT_KEYS`) with its type; validate ranges in `check_section` (`:161`) with a message that says the fix; use it with a default equal to the old behaviour; document it in README "Config", `docs.html` and `skill/shotfleet/references/config.md` (tests compare these lists with `KEYS`). If the key can run a command it is a trust-boundary change: see the MCP `hooks` gate ([04](04-setup-mcp-skills.md#43-the-mcp-server)).

### Add a command or flag

Add the subparser in `main()` (`:5065`), the name to `COMMANDS` (`:5041`), a branch in `main_dispatch` (`:5675`); decide whether it needs a licence (`require_licence()` or `apply_free_tier()` there), `--json` support (any command with a `json` attribute is handled by `main()`), and exit codes. Update the module docstring (already incomplete), README, the docs page, the skills and `docs/AGENTS-snippet.md`: `tests/test_agent_skills.py` parses every documented `shotfleet ...` command with the real parser, so a doc that names a flag that does not exist fails.

### Add an MCP tool

[04 section 4.3](04-setup-mcp-skills.md#43-the-mcp-server): `MCP_TOOLS` entry with honest annotations, a branch in `mcp_call`, free-tier and `hooks` behaviour, tests, README, skills.

### Change licence behaviour

Together: `shotfleet.py`, the unit tests, `tools/release-candidate.sh`, `site/public/terms.html`, `index.html`, `docs.html`, `llms.txt`, README, the skill `references/licence.md` and `ci.md`, and the claims. If you touch how the release date reaches the program, change `packaging/build.sh` (`_release.py`, `--paths`, `--hidden-import`) and the 2020-sale check in `tools/release-candidate.sh` with it ([05 section 5.9](05-licence-and-money.md#59-testing-the-licence-and-changing-it)).

### Add or change a site claim

Edit the words; find the row whose `where_text` quotes them (grep the old words) and update it, or add a row with the next free `C###`; prove it at the lowest layer; run `tools/check-claims.sh` and fix what it names ([07](07-website-and-backend.md)).

### Extend the Maestro compatibility matrix

The matrix is `MAESTRO_TESTED` (`:3915`) plus `docs/compat.md`. Procedure (each step has a tool; details in [08](08-testing.md)):

1. `tools/latest-maestro.py` / `tools/watch-upstream.sh` notice a new upstream version (the `maestro-latest.yml` workflow exists but is manual-only).
2. Vet it **offline** first: `tools/maestro-compat.py` checks the new Maestro's jars against `MAESTRO_INTERFACE` (`:3902`): the CLI flags shotfleet passes, the log lines it parses, the env variables it sets, the flow keys it writes.
3. Run the fixture end to end for real on the new version, iOS and Android, under the device lock (`tools/fixture-e2e.sh`). Record the evidence in `research/` and `docs/compat.md`.
4. Only then extend `MAESTRO_TESTED`, update the places that quote the pair (README "Maestro (tested with 2.0.10 and 2.11.0)", the skills, the troubleshooting reference, `tests/test_handoff_docs.py` which pins those quotes) and decide whether `MAESTRO_PIN` (what `doctor --fix` installs) moves.
5. A version goes on `MAESTRO_BAD` **only** with a reproduced failure and a research note; "untested" only warns.

### Change what a release contains

Edit `packaging/build.sh` (and `Dockerfile` / `packaging/build-linux.sh` if shared inputs changed). `packaging/requirements-build.txt` changes only on purpose: download the wheels, hash them, edit the file, rebuild, record the versions ([06](06-packaging-and-release.md)). Never `pip install` anything else into the build environment.

## 10.4 What not to do

- Do not add a server, an account system or telemetry to the program without the owner (D5; the privacy promise is "nothing leaves your machine except what you ask for").
- Do not weaken a test to make a claim pass; change the words or get the evidence.
- Do not "fix" the accepted licence limits by obfuscation ([05 section 5.8](05-licence-and-money.md#58-known-limits-of-client-side-licensing-accepted)).
- Do not use `--no-verify`, force-push, or edit another session's worktree.
- Do not print, log or commit anything from `~/Library/Application Support/shotfleet/licence.json`.
- Do not add a dependency to `shotfleet.py`; the standard library plus the optional `certifi` import is the contract (the build environment is pinned and hash-checked).
- Do not change `INFRA_ERRORS`, the capacity thresholds or the OCR budget without a measurement; each constant cites the run it came from.
- Do not trust a doc over the code. Add what you find to the corrections list in the [README](README.md#documentation-corrections).

## 10.5 First week checklist

Day 1, read and run (no devices):
- [ ] Read the [README](README.md) of this folder, then [01](01-runtime-architecture.md), [03](03-check-ocr-export.md) and [05](05-licence-and-money.md). Skim [11](11-history-and-decisions.md).
- [ ] `git log --oneline | head -30`; read the top three entries of `CHANGELOG.md`.
- [ ] `python3 --version` is 3.11 or newer; `node --version` works.
- [ ] `sh tools/check-claims.sh > ~/check-claims.log 2>&1; echo rc=$?` (about 1 to 3 minutes; read the last line). `git config core.hooksPath .githooks`.
- [ ] `python3 -m unittest tests.test_shotfleet.TranslateFlow` to see one fast module; read its tests to see how `translate_flow` is specified.

Day 2, run the program without a device:
- [ ] `python3 shotfleet.py --help`, `python3 shotfleet.py doctor` (source runs are unlicensed).
- [ ] `python3 shotfleet.py check` on a folder of PNGs with `--locale en` (needs Tesseract on Linux or macOS text recognition on a Mac; the first macOS run may spend minutes compiling a model: that is the [ANE issue](03-check-ocr-export.md#35-the-slow-first-run-anecompilerservice), not a hang).
- [ ] Read `tests/claims.json` rows C001 to C020 and the matching `tests/test_claims.py`.

Day 3 to 4, change something small safely:
- [ ] Pick a CHANGELOG-sized fix (a message, a hint). Write the test first, make it pass, update the doc and claim rows it touches, run the full check.
- [ ] Read [06](06-packaging-and-release.md) end to end and the last release folder under `shotfleet-rc-build/` (read-only). Do **not** run `publish.sh` or any script that deploys.

Day 5, devices (only with the owner's OK and the lock):
- [ ] Read [08](08-testing.md) and `docs/device-queue.md`. Take the lock, run `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` only when the Mac is quiet (memory pressure level 1, no stray Gradle daemons), with a time limit; release the lock.

Always: ask the owner before anything outward ([10.1](#101-standing-rules-from-the-owner)).
