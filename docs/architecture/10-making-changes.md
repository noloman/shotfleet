# 10. Making common changes safely

Back to the [index](../ARCHITECTURE.md). Each recipe lists the files that must change together. The tests are built to fail when you miss one; treat a red
test as a pointer, not an obstacle.

## Ground rules

1. Work in a **durable worktree** (for example `git worktree add /Users/manu/Developer/shotfleet-rc-build/<name>-wt -b claude/<name> origin/main`), never in `/tmp` (a reboot wipes it) and never in
   another session's directory. The machine is shared by many agent sessions: do not kill or delete a process or folder you cannot prove you created.
2. Run the full check as `sh tools/check-claims.sh > <durable file> 2>&1; echo rc=$?` and push only when that `rc` is 0. **Never gate a push through a pipe**
   (`| tail`): the pipe hides the exit code.
3. No GitHub Actions. Commit messages end with `[skip ci]`.
4. Anything that boots a simulator or emulator takes the device lock ([02](02-capture.md#29-device-locks-and-sharing-a-machine)) and has a hard time limit.
5. Do not change shared state (Gumroad, deploys, `main`) in parallel with another agent: check the sessions and message the coordinator first.
6. Prefer the smallest change with a named ceiling (`ponytail:` comment) to new structure.

## Add a language or a translation-file format

*Adding a store listing language:* add the code to `APP_STORE` and/or `PLAY` (`shotfleet.py:252-258`, copied from fastlane's folder names; `marketing/store-locales.md`), then check `store_code` maps your
app locales onto it (`PRIMARY` if the language has several regions, `CANON`/`LANG_CANON` for alias spellings). Add a test next to `Export` or the store-code tests.

*Making `check` read a language:* add its code to `TESSERACT` (`:3231`) and, for scripts needing script detection, `OSD_SCRIPT`; if it is Latin script that Vision lacks, `LATIN_UNLISTED`; if
detection confuses it with another, `TWINS`. Extend the Docker image's `LANGS`. Measure with `tools/langmatrix.py` and a real screenshot set.

*A new translation-file format* (for `strings = "glob"` and `check --strings`):
1. Add a branch to `read_translation_file` (`:646`) returning `{locale: {key: text}}`; plurals as `key#form` (use `icu_forms` for ICU text); take the locale from the file when it says one,
   else `locale_from_path` (`:486`).
2. If files of this kind are named by convention, teach `locale_from_path` and the "unsupported" message at the end of the function.
3. If a framework uses it: add an entry to `FRAMEWORKS` (`:853`) for `framework_hint` and, for `init`, a branch in `detect_project` (`:4272`) with its translation glob, build folders and build commands.
4. Tests in `SourceFiles` or `LocalizationFormats` (`tests/test_shotfleet.py`) and `tests/test_projects.py`; update README "Supported" list, the docs page config table, `skill/shotfleet/references/config.md`
   (`test_config_md_lists_every_key_table_and_hook_event`). Never **execute** user files: parse them as data.
5. Say in README and the skills only what you ran. Flutter and React Native are "run end to end once each"; keep claims that narrow.

## Add a check rule

See [03-check.md](03-check.md#36-extending-the-check). In short: pure helper or inline condition in `cmd_check`, `problems` if a store or the user would be hurt, `notes` otherwise; a unit test with a faked
reader; the line added to `skill/shotfleet-review/SKILL.md`'s table (a test checks fragments exist in the program); a CHANGELOG bullet; a claim row if public text promises it. Decide whether the rule
needs the evidence type (app text exact, OCR approximate): never report a failure from a reader that may simply have failed to read.

## Add a store rule or size

See [04-export-and-store-rules.md](04-export-and-store-rules.md#43-changing-a-store-rule).

## Add a config key

1. Add it to `KEYS` (`:60`) with its type (or `CAPTURE_KEYS`, `TABLES`, `HOOK_EVENTS`, `EXPECT_KEYS` for tables), and validate value ranges in `check_section` (`:161`) with a message that says the fix.
2. Use it in the run code with a default that equals the old behaviour.
3. Document it: README "Config", `docs.html` config table, `skill/shotfleet/references/config.md`. Tests that compare these lists with `KEYS` will fail until all agree.
4. If it can run a command, it is a trust-boundary change: see [11](11-security-and-privacy.md) and MCP's `hooks` gate.

## Add a CLI command or flag

Add the subparser in `main()` (`:4769`), the name to `COMMANDS` (`:4745`), a branch in `main_dispatch` (`:5357`), and decide: needs licence? (call `require_licence()` or `apply_free_tier()` there), `--json`
support (`main()` handles any command with a `json` attribute), exit codes ([01](01-code-layout.md#exit-codes)). Update the module docstring (it is already incomplete), README, docs page, skills and the agents
snippet (`tests/test_agent_skills.py` parses every documented command with the real parser).

## Add an MCP tool

See [06-mcp-and-skills.md](06-mcp-and-skills.md#adding-an-mcp-tool).

## Change licence behaviour

See [05-licensing.md](05-licensing.md#operating-it): code, unit tests, `tools/release-candidate.sh`, terms, home page, docs, `llms.txt`, README, skills, claims, together. If you touch how the release date reaches the program, change `packaging/build.sh` (`_release.py`, `--paths`, `--hidden-import`) and the 2020-sale check in `tools/release-candidate.sh` with it; `packaging/build-linux.sh` and the `Dockerfile` do not write `_release` (see the appendix).

## Add or change a site claim

1. Edit the words in the page (or README, `llms.txt`, launch text).
2. Find the row in `tests/claims.json` whose `where_text` quotes them (`grep` the old words) and update `where_text`; or add a new row: next free `C###`, `claim`, `where` and `where_text` (exact quote), honest
   `status`, `proof`, `layer`, `assertion`, `fix`.
3. Prove it at the lowest layer that can: a unit test (`proven`, name it as `Class.test_name` in `proof`), a site test, a fixture or device run (`evidence` with a dated record in `research/`). If nothing
   can prove it yet, status `partial` or `untested` and say what is missing; better, soften the words until they are true.
4. Never write a number, price, date, version support or "works with X" without a row. `test_site.py` bans phrases like "works with any app" and "guarantee".
5. No em dashes. Run `tools/check-claims.sh`; fix what it names.

## Change what a release contains

Edit `packaging/build.sh` (and `Dockerfile`/`build-linux.sh` if shared inputs changed). `packaging/requirements-build.txt` changes only on purpose: download the wheels, hash them, edit the file,
rebuild, record versions ([07](07-packaging-and-release.md)). Never `pip install` anything else into the build venv.

## Release checklist

[07-packaging-and-release.md section 7.8](07-packaging-and-release.md#78-release-checklist).

## Gotchas from history

- **Shared Mac.** Many agent sessions use the same simulators, emulators and `/tmp`. Two device jobs at once voided runs (load 600 to 1000, simulators hung). One device job at a time under the lock;
  hard limits on every waiter (one without a limit held the lock 8 hours); ownership before kill or delete (a work folder deleted by mistake voided a gate run).
- **Device queue.** `docs/device-queue.md` is the protocol; the files live in `/tmp` and vanish on reboot; waiters die with their sessions.
- **`/tmp` is wiped on reboot.** Anything you need later (merge trees, release archives, logs, rollback ids) goes in `shotfleet-rc-build/`, not `/tmp`. `publish.sh` refuses a temp release directory.
- **Never gate a push (or a merge) through a pipe.** Use `> file 2>&1; echo rc=$?`.
- **Durable worktrees.** Merge and check in `shotfleet-rc-build/merge-tree`-style folders so a reboot or another session's cleanup cannot remove them.
- **Locked keychain is not a lost profile** ([07](07-packaging-and-release.md#the-notary-profile-gotcha-read-this-before-your-first-release)). Unlock, keep awake, retry before asking for credentials.
- **Text recognition "hangs" are compiles.** `ANECompilerService` can compile for 40 minutes; do not reboot; `check` waits within its budget and says what it is doing ([03](03-check.md)).
- **Do not run a release gate on a loaded Mac.** Start at memory pressure level 1; stop idle Gradle daemons (`./gradlew --stop`); no unlocked emulators.
- **Installing a new iOS runtime changes `latest_ios_runtime()` for every run** on the machine; do it only when nothing is queued.
- **Version strings live in several places** and the release scripts compare them: `shotfleet.py` `VERSION`, top `CHANGELOG.md` heading, docs page "Last checked against version", `whats-new.html`; the Dockerfile's example
  build arg is stale by design.
- **Maestro versions:** `MAESTRO_TESTED` changes only after a real fixture run passed on that version; a version goes on `MAESTRO_BAD` only with a reproduced failure and a research note. Run `tools/maestro-compat.py` on a new one first.
- **STATUS.md and `docs/handoff.md` lag the code.** Trust `shotfleet.py`; update them when you finish.
- **Do not trust a doc over the code.** Add what you find to [the mismatch appendix](13-mismatches.md).
