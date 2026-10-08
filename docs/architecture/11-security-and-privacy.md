# 11. Security model and privacy

Back to the [index](../ARCHITECTURE.md). Sources: `site/public/privacy.html` (what is promised), the code (what happens, `origin/main` `285e099`), and the 2026-10-07 security review
(`shotfleet-rc-build/code-review-2026-10-07/security.md`, kept outside the repo) with its fixes, which are merged.

## What leaves the machine

Promise, from the privacy page: **the user's app and screenshots are never uploaded.** There is no shotfleet backend. Every outbound request in the program:

| Request | When | Sends | Code |
|---|---|---|---|
| `POST api.gumroad.com/v2/licenses/verify` | `activate` (two calls on a new Mac, one on a known one), weekly re-check by `run` and `export`, every `run`/`export` with `SHOTFLEET_KEY` | licence key, product id, `increment_uses_count`; the request carries the IP address and Python's default user agent; no Mac name, no program version. Limited to 20 s in all (`gumroad_fetch`) | `gumroad_verify` |
| `GET shotfleet.com/download/VERSION` | `doctor` | an ordinary page request; nothing about the user | `latest_release` |
| Downloads | only `doctor --fix`, after a printed plan and one confirmation | IP and `shotfleet/<version>` as user agent. Maestro from GitHub (pinned sha256), a Java 21 JRE from Adoptium (link and sha256 from Adoptium's API), Google's Android command-line tools (sha1 from Google's manifest, or Homebrew) | `download`, `install_*` |
| Android SDK installs | `doctor --fix` | go through `android --no-metrics sdk install` when Google's `android` program sits next to `sdkmanager`, because Google's newer tools report usage unless told not to | `sdkmanager_invocation` |
| Maestro analytics | every run | disabled: shotfleet sets `MAESTRO_CLI_NO_ANALYTICS=1` | `ios_run_inner`, `android_run_inner` |
| Website visitors | on shotfleet.com | first-party counters (event, source, language, day; no cookie, no IP stored); Google Analytics 4 **only after "Accept analytics"** | [08](08-website.md) |

`check`, `init`, `export`, `skill`, `mcp` and `run`'s capture make no network request at all (a test, `NothingIsUploaded` in `tests/test_cli_claims.py` and `G1NothingLeavesTheMac` in `test_shotfleet.py`, guards this).
Reports (`check.json`, `index.html`) contain **absolute and relative paths and the app's own on-screen text**; they stay on disk. Treat a report as sensitive if the app's screens are.

## Trust boundaries

Think of shotfleet as a program that **runs things on behalf of whoever wrote the files you point it at**.

| Input | Trusted? | What it can do | Defences |
|---|---|---|---|
| The CLI user | yes | everything | n/a |
| `shotfleet.toml` | **as trusted as a Makefile** | `[hooks]`, `[capture] build` run `/bin/sh -c`; `[ios] simctl` runs `xcrun simctl`; `[android] shell` runs on the emulator; `flow` and `app` choose what runs | Config keys are strictly validated (`package` and `avd` values are shape-checked, `locales` and `base_locale` must be language codes); commands are printed; `--no-hooks`. Over MCP **every** config command is opt-in (`hooks: true`): `[hooks]`, `[capture] build`, `[ios] simctl` and `[android] shell` (S1, fixed; [06](06-mcp-and-skills.md)). A config from a repo you just cloned deserves a read first. |
| `flow.yaml` | a Maestro flow can run shell via `runScript`/JS and drive the device | same as running Maestro yourself | shotfleet rewrites text only |
| Translation files (`strings = glob`, `--strings`) | **data from the project** | read, never executed (`.ts`/`.js` parsed as data); a locale code becomes a folder name | A language code from a file, a build, the config, `--locales` or MCP must match `SAFE_LOCALE` (`:35`: letters, digits, `-`, `_`) or it is skipped with a note (files, via `safe_strings`) or refused (config and options, via `check_locales`); and `inside(root, ...)` refuses any path that resolves outside its root before each `rmtree`, write and export copy (S3, fixed). Archive extraction everywhere checks `is_relative_to` (and tar symlink targets). |
| Built apps (`.app`, `.apk`) | **run on simulators/emulators as the user** | the app runs; strings are read via `plutil`/`aapt2`/zip | simulator and emulator processes run with the user's rights; `unpack_build` refuses members outside its folder and tar symlink escapes |
| Screenshot folders given to `check` | data | images are read for size and alpha by hand-written parsers, text by Vision/Tesseract | file names become report text; the HTML gallery `html.escape`s every value (including the injected "not verified" block) |
| APKs and `.app`s from other people given to `check --app` | data | only their strings and `Info.plist` are read, not run | `aapt2` and zip readers |
| `--ocr-command` / `SHOTFLEET_OCR` | **runs a program** | argv from `shlex.split`, no shell | user-supplied only (the command line, or `SHOTFLEET_OCR` in the environment where the process starts); the MCP `check` tool refuses an `ocr_command` argument (S2, fixed) but the MCP server still honours `SHOTFLEET_OCR` from its own environment |
| MCP client | **untrusted when an agent can be prompt-injected** | calls `check`, `doctor`, `run` with arguments | protocol validation; every config command opt-in; `check` runs no program; path and locale arguments validated; short answers; no licence or export tool. `additionalProperties: false` is advisory (the server does not reject extra keys). |
| Downloads from the network | checked | Maestro, JRE, Android tools | sha256/sha1 compared before unpack; `.part` then rename; TLS via certifi or the user's CA bundle |
| `licence.json`, `ci-checked.json` | user-writable | unsigned | an honesty system ([05](05-licensing.md)) |
| `/tmp/shotfleet-*.lock` | predictable names in a shared directory | | `flock`, opened by `open_lock`: `O_NOFOLLOW`, mode `0o600`, and used only if it is a regular file of this user (else the run goes on without the lock, with a note); same names, so one user's sessions still take turns (S4, fixed) |

General properties: every subprocess is an argv list (no `shell=True` on untrusted text; the `/bin/sh -c` sites are the user's own config strings, and every one is behind the MCP opt-in); zip and tar extraction check
`is_relative_to`; downloads are checksum-pinned; the worker stores no raw IP and echoes no input; the CSP is `default-src 'self'` with GA hosts allow-listed; the HTML report escapes everything.

## The security review of 0.1.6: what was found and what main does now

From the security review at `c18473f` (all marked VERIFIED by the reviewer unless noted). Each fix has a test in `tests/test_security.py` (or `test_release_scripts.py` for S7) that fails on `c18473f` and passes on main.

| Id | Severity | Issue | Status on `285e099` |
|---|---|---|---|
| S1 | high | MCP `run` executed `[capture] build` (and `[ios] simctl`, `[android] shell`) without `hooks: true` | fixed: `config_commands` refuses before anything runs; `refuse_config_commands` in `capture_build` and `run_setup` is the last guard |
| S2 | high | MCP `check` accepted an undocumented `ocr_command` that runs a program, under a tool marked `readOnlyHint` | fixed: refused over MCP; `check` is `destructiveHint: true`; schemas `additionalProperties: false` (advisory); `mcp_path` |
| S3 | medium | a locale code from a translation file or build (`../../x`) became a path segment: out-of-tree `rmtree`, write, export copy | fixed: `SAFE_LOCALE`, `check_locales`, `safe_strings`, `inside()`; `package` and `avd` shape-checked |
| S4 | medium | predictable world-writable `/tmp` lock files followed through symlinks | fixed: `open_lock` for the device locks and the OCR warm-up lock |
| S5 | low | committed reports leak absolute local paths | not fixed: repo hygiene, do it (and `.gitignore shotfleet-check/`) before the repo is ever public |
| S6 | low (plausible) | `install.sh` verifies a same-origin checksum, no out-of-band signature; bin-dir fallback edge | not fixed: a real signature needs a signing key and design; the signed, notarized `.pkg` is the path with a real signature |
| S7 | low (plausible) | `publish.sh` version check was a glob | fixed: digits and dots only, `X.Y.Z` (the version goes into file names and paths) |

Also left as is, on purpose: MCP `run` still installs and runs the config's app and prebuilt test bundle on the simulators, and `EMU_LOG_DIR` is unchanged.
The MCP side is described in [06-mcp-and-skills.md](06-mcp-and-skills.md#safety-gates-and-where-they-stop). Licence-side weaknesses are in [05](05-licensing.md), including its
[known limits of client-side licensing](05-licensing.md#known-limits-of-client-side-licensing).

## Rules when you change code here

1. Never build a shell command from text that came from a file, a flow, a build or a client. Argv lists only. If a config string must be a shell command, it needs an explicit opt-in on every non-terminal path.
2. Anything that becomes part of a path (locale, device name, screenshot name) must be validated or checked with `is_relative_to` before delete, write or copy.
3. Read translation and config files as data; never `eval`, `import` or run them.
4. Do not add a network call. If you must, it needs the owner's decision, a privacy-page change (a test lists what the page says), a claim row and a way to turn it off.
5. Do not log keys. Never print `licence.json`. Skills tell agents the same.
6. No new third-party host on the site without a CSP, privacy and test change.
