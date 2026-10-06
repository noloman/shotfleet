# 11. Security model and privacy

Back to the [index](../ARCHITECTURE.md). Sources: `site/public/privacy.html` (what is promised), the code (what happens), and the 2026-10-07 security review
(`shotfleet-rc-build/code-review-2026-10-07/security.md`, kept outside the repo).

## What leaves the machine

Promise, from the privacy page: **the user's app and screenshots are never uploaded.** There is no shotfleet backend. Every outbound request in the program:

| Request | When | Sends | Code |
|---|---|---|---|
| `POST api.gumroad.com/v2/licenses/verify` | `activate` (two calls on a new Mac, one on a known one), weekly re-check by `run` and `export`, every `run`/`export` with `SHOTFLEET_KEY` | licence key, product id, `increment_uses_count`; the request carries the IP address and Python's default user agent; no Mac name, no program version | `gumroad_verify` (`:4921`) |
| `GET shotfleet.com/download/VERSION` | `doctor` | an ordinary page request; nothing about the user | `latest_release` (`:3541`) |
| Downloads | only `doctor --fix`, after a printed plan and one confirmation | IP and `shotfleet/<version>` as user agent. Maestro from GitHub (pinned sha256), a Java 21 JRE from Adoptium (link and sha256 from Adoptium's API), Google's Android command-line tools (sha1 from Google's manifest, or Homebrew) | `download` (`:3644`), `install_*` |
| Android SDK installs | `doctor --fix` | go through `android --no-metrics sdk install` when Google's `android` program sits next to `sdkmanager`, because Google's newer tools report usage unless told not to | `sdkmanager_invocation` (`:3787`) |
| Maestro analytics | every run | disabled: shotfleet sets `MAESTRO_CLI_NO_ANALYTICS=1` | `ios_run_inner`, `android_run_inner` |
| Website visitors | on shotfleet.com | first-party counters (event, source, language, day; no cookie, no IP stored); Google Analytics 4 **only after "Accept analytics"** | [08](08-website.md) |

`check`, `init`, `export`, `skill`, `mcp` and `run`'s capture make no network request at all (a test, `NothingIsUploaded` in `tests/test_cli_claims.py` and `G1NothingLeavesTheMac` in `test_shotfleet.py`, guards this).
Reports (`check.json`, `index.html`) contain **absolute and relative paths and the app's own on-screen text**; they stay on disk. Treat a report as sensitive if the app's screens are.

## Trust boundaries

Think of shotfleet as a program that **runs things on behalf of whoever wrote the files you point it at**.

| Input | Trusted? | What it can do | Defences |
|---|---|---|---|
| The CLI user | yes | everything | n/a |
| `shotfleet.toml` | **as trusted as a Makefile** | `[hooks]`, `[capture] build` run `/bin/sh -c`; `[ios] simctl` runs `xcrun simctl`; `[android] shell` runs on the emulator; `flow` and `app` choose what runs | Config keys are strictly validated; commands are printed; `--no-hooks`. Over MCP hooks are opt-in (`hooks: true`), which on main covers only `[hooks]` (see below). A config from a repo you just cloned deserves a read first. |
| `flow.yaml` | a Maestro flow can run shell via `runScript`/JS and drive the device | same as running Maestro yourself | shotfleet rewrites text only |
| Translation files (`strings = glob`, `--strings`) | **data from the project** | read, never executed (`.ts`/`.js` parsed as data); a locale code becomes a folder name | On main nothing validates a locale code from a file before it becomes `out/raw/<locale>` (S3, fix in flight). Archive extraction everywhere checks `is_relative_to` (and tar symlink targets). |
| Built apps (`.app`, `.apk`) | **run on simulators/emulators as the user** | the app runs; strings are read via `plutil`/`aapt2`/zip | simulator and emulator processes run with the user's rights; `unpack_build` refuses members outside its folder and tar symlink escapes |
| Screenshot folders given to `check` | data | images are read for size and alpha by hand-written parsers, text by Vision/Tesseract | file names become report text; the HTML gallery `html.escape`s every value (including the injected "not verified" block) |
| APKs and `.app`s from other people given to `check --app` | data | only their strings and `Info.plist` are read, not run | `aapt2` and zip readers |
| `--ocr-command` / `SHOTFLEET_OCR` | **runs a program** | argv from `shlex.split`, no shell | user-supplied only; on main the MCP `check` tool also accepts it (S2) |
| MCP client | **untrusted when an agent can be prompt-injected** | calls `check`, `doctor`, `run` with arguments | protocol validation; hooks opt-in; short answers; no licence or export tool. Gaps below. |
| Downloads from the network | checked | Maestro, JRE, Android tools | sha256/sha1 compared before unpack; `.part` then rename; TLS via certifi or the user's CA bundle |
| `licence.json`, `ci-checked.json` | user-writable | unsigned | an honesty system ([05](05-licensing.md)) |
| `/tmp/shotfleet-*.lock` | predictable names in a shared directory | | `flock`; on main opened `O_CREAT` mode 0o666 and followed through symlinks (S4, fix in flight) |

General properties: every subprocess is an argv list (no `shell=True` on untrusted text; the three `/bin/sh -c` sites are the user's own config strings); zip and tar extraction check
`is_relative_to`; downloads are checksum-pinned; the worker stores no raw IP and echoes no input; the CSP is `default-src 'self'` with GA hosts allow-listed; the HTML report escapes everything.

## Known issues on main and the fixes in flight

From the security review at `c18473f` (all marked VERIFIED by the reviewer unless noted):

| Id | Severity | Issue | Status |
|---|---|---|---|
| S1 | high | MCP `run` executes `[capture] build` (and `[ios] simctl`, `[android] shell`) without `hooks: true` | fix in flight, `claude/016-security-fixes` working tree |
| S2 | high | MCP `check` accepts an undocumented `ocr_command` that runs a program, under a tool marked `readOnlyHint` | same |
| S3 | medium | a locale code from a translation file or build (`../../x`) becomes a path segment: out-of-tree `rmtree`, write, export copy | same: `SAFE_LOCALE` and `inside()` |
| S4 | medium | predictable world-writable `/tmp` lock files followed through symlinks | same: `open_lock` |
| S5 | low | committed reports leak absolute local paths | not fixed: repo hygiene, do it before the repo is ever public |
| S6 | low (plausible) | `install.sh` verifies a same-origin checksum, no out-of-band signature; bin-dir fallback edge | not fixed: a real signature needs a signing key and design; the signed, notarized `.pkg` is the path with a real signature |
| S7 | low (plausible) | `publish.sh` version check is a glob | same fix branch: digits and dots only |

The in-flight work is described in [06-mcp-and-skills.md](06-mcp-and-skills.md#in-flight-on-claude016-security-fixes): the branch ref itself has no commits ahead of main; the changes sit uncommitted in a worktree.
Licence-side weaknesses (bypasses of the update window, CI offline behaviour) are in [05](05-licensing.md).

## Rules when you change code here

1. Never build a shell command from text that came from a file, a flow, a build or a client. Argv lists only. If a config string must be a shell command, it needs an explicit opt-in on every non-terminal path.
2. Anything that becomes part of a path (locale, device name, screenshot name) must be validated or checked with `is_relative_to` before delete, write or copy.
3. Read translation and config files as data; never `eval`, `import` or run them.
4. Do not add a network call. If you must, it needs the owner's decision, a privacy-page change (a test lists what the page says), a claim row and a way to turn it off.
5. Do not log keys. Never print `licence.json`. Skills tell agents the same.
6. No new third-party host on the site without a CSP, privacy and test change.
