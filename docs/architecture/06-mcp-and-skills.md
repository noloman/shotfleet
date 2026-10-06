# 6. The MCP server and the agent skills

Back to the [index](../ARCHITECTURE.md). Anchors are `shotfleet.py:LINE` at `c18473f`.

shotfleet reaches AI coding agents two ways. **Skills** are instruction files an agent reads (zero code, zero risk). The **MCP server** gives the agent
callable tools (code that runs with the user's privileges). They overlap on purpose: the skills use the CLI, the MCP server wraps the same functions.

## 6.1 The MCP server

`shotfleet mcp` (`cmd_mcp`, `:4861`) is a Model Context Protocol server on stdin and stdout: JSON-RPC 2.0, one message per line.

### Protocol behaviour

- Only `2025-11-25` and `2025-06-18` (`MCP_VERSIONS`, `:4859`). `initialize` echoes the client's version when it is one of these, else answers with the
  newest. The comment above the constant says why not others: 2025-03-26 requires JSON-RPC batches, and 2026-07-28 has no `initialize` and needs
  `server/discover` and per-request `_meta`. A batch (a JSON array) gets error `-32600`. An unparseable line gets `-32700`; an unknown method `-32601`.
  Notifications (no `id`: `initialized`, `cancelled`) are ignored. `ping` returns `{}`.
- It writes with `sys.__stdout__`, the real stdout, because `mcp_call` redirects `sys.stdout` and `sys.stderr` into a buffer while a tool runs. A stray
  `print` inside a tool therefore cannot corrupt the protocol.
- Capabilities: `{"tools": {}}`. No resources, no prompts. `serverInfo.version` is `VERSION`.
- **Progress.** If the client passes `_meta.progressToken`, a heartbeat thread (`MCP_HEARTBEAT_S = 30`) sends `notifications/progress` carrying the
  last non-empty output line, because Claude Code drops a stdio call that is silent for 30 minutes and a `run` can take an hour.

### Tools (`MCP_TOOLS`, `:4771`)

| Tool | Does | Input schema | Annotations |
|---|---|---|---|
| `check` | `check_any(...)` on a folder; writes `check.json` and `index.html` to the report folder | `folder` (required), `app`, `strings` (array of globs), `report`, `full` | main: `readOnlyHint: true`, `openWorldHint: false` |
| `doctor` | `cmd_doctor()` with no fix: reports, installs nothing | none (`additionalProperties: false`) | `readOnlyHint: true`, `openWorldHint: true` (asks shotfleet.com for the latest version) |
| `run` | `apply_free_tier()` then `cmd_run(config, locales)`: boots devices, replaces the output folder's screenshots and report | `config` (required), `locales`, `full`, `hooks` | `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: false`, `openWorldHint: true` |

There is deliberately no `export` tool, no `activate`, no `init`, no `skill` over MCP. Licence handling stays in the user's terminal so the key never passes through an
agent.

`mcp_call(name, args, progress)` (`:4824`) is the dispatcher:

1. Resets `LAST_REPORT` and `REPORTS` so a call that never reaches `check` cannot return the previous call's report.
2. Runs the tool with stdout and stderr captured in a `StringIO`.
3. **Returns a short summary by default** (`mcp_summary`, `:4808`): `{"exit", "screenshots", "languages", "problems_total", "problems" (first 100, each cut to
   300 characters), "notes_total", "notes", "reports" (absolute paths of every check.json)}` plus a `more` hint when truncated. Why: a 40-language,
   10-screen full report is about 67,000 characters, and Claude Code moves tool results over 50,000 to a file. `full: true` returns
   `{"exit", ...reports_json()}` instead.
4. Any exception becomes `isError: true` with the message plus the last 2,000 characters of captured output. One bad call never kills the server
   (`except Exception`, which is the only broad catch in the program, and says why).
5. For `doctor`, or `check` and `run` that produced no report, the reply is the captured log text.

### Safety gates and where they stop

| Gate | What it does | Limit |
|---|---|---|
| **Hooks are opt-in.** `run` over MCP sets `NO_HOOKS = args.get("hooks") is not True` and restores it in a `finally` | the config's `[hooks]` shell commands do not run unless the call says `hooks: true`. Reason: a `shotfleet.toml` from a repo you just cloned can hold any shell command, and over MCP the user does not see it the way they see a terminal command | **on main it covers only `[hooks]`.** `[capture] build` (a `/bin/sh -c` string), `[ios] simctl` and `[android] shell` still run without `hooks: true` (security finding S1) |
| **Free-tier cap** | `run` calls `apply_free_tier()` like the CLI | an MCP `run` skips the Maestro version refusal/warning that the CLI's `main_dispatch` does (the deny list `MAESTRO_BAD` is empty today, so nothing differs) |
| **No licence key in the protocol** | no tool takes or returns one | `SHOTFLEET_KEY` can still be in the server's environment; README tells users not to pass it with `claude mcp add --env` because it lands in plain text in `~/.claude.json` |
| **Annotations** | hints for the client's own permission UI | hints only; the client decides |
| **`check` writes only its report** | into `./shotfleet-check` in the **server's** working directory (never inside the checked folder), or the run folder for shotfleet output, or `report` | `check` never changes a screenshot |

Known gaps on main, from the 2026-10-07 security review (`shotfleet-rc-build/code-review-2026-10-07/security.md`, all VERIFIED by the reviewer):

- **S1 (high):** MCP `run` executes `[capture].build` from the config without `hooks: true`.
- **S2 (high):** `mcp_call` passes `args.get("ocr_command")` into `check_any`, which runs that program (`external_ocr`), although the schema does not list `ocr_command` and the tool
  advertises `readOnlyHint: true`. `SHOTFLEET_OCR` in the server's environment is also honoured.

### In flight on `claude/016-security-fixes`

That branch name currently points at the same commit as `main` (`c18473f`); the work exists as **uncommitted changes in the worktree**
`shotfleet-rc-build/security-fixes-wt` (11 files, about 170 lines added to `shotfleet.py`, plus tests; the review note says regression tests are in
`tests/test_security.py`). This section reads that working-tree diff and the review's "Fix status"; it may change or be committed differently.

- **MCP `run` refuses commands from the config without `hooks: true`.** New `config_commands(config_path)` lists `[hooks]`, `[capture] build`, `[ios] simctl`
  and `[android] shell`; over MCP without `hooks: true` a config that has any of the last three is refused with a line naming them. A second module
  flag `CONFIG_COMMANDS` plus `refuse_config_commands()` is called inside `capture_build` and `run_setup` as the last guard. CLI behaviour is unchanged.
- **MCP `check` no longer takes `ocr_command`:** passing it returns an error pointing at `shotfleet check --ocr-command` in a terminal. `check` is no
  longer marked `readOnlyHint` (it overwrites its report: `destructiveHint: true`, `idempotentHint: true`). Both schemas get `additionalProperties: false`.
  New `mcp_path()` makes MCP path arguments absolute and string-only so they are never read as options by programs they are handed to; `strings` accepts
  a string or a list; `locales` must be a non-empty list.
- **Language codes are validated before they become folder names** (S3): `SAFE_LOCALE` (letters, digits, `-`, `_`) is applied to translation files, build tables, the
  config's `locales` and `base_locale`, `--locales` and the MCP `locales`; a bad one is skipped with a note (files) or refused (config and options). `inside(root, ...)` refuses any
  path that resolves outside its root before each `rmtree`, write and export copy. `package` and `avd` config values are shape-checked.
- **Lock files** (S4): new `open_lock` opens `/tmp/shotfleet-*.lock` with `O_NOFOLLOW`, mode `0o600`, and only uses a regular file owned by the current user (otherwise the run continues
  without the lock, with a note). Same file names, so locking between one user's sessions is unchanged.
- **`packaging/publish.sh`** accepts a manifest version only of digits and two dots (S7).
- Not fixed and why (S5 absolute paths in committed reports, S6 `install.sh` same-origin checksum): recorded in the review.

## 6.2 The agent skills

`skill/` holds three skills, each a folder with `SKILL.md` (frontmatter `name` and `description`, then a short body):

| Skill | For |
|---|---|
| `shotfleet/` | the main skill: decision tree, commands, exit codes, `--json` reading, flow writing. `references/`: `troubleshooting.md`, `flow-writing.md`, `config.md`, `ci.md`, `licence.md` (loaded on demand) |
| `shotfleet-ci/` | add `shotfleet check` to GitHub Actions or another CI; `SHOTFLEET_KEY` |
| `shotfleet-review/` | turn a `check.json` into a fix list; a table of every problem line and what it means |

Distribution paths:

- **Inside the program.** `build.sh` passes `--add-data skill:skill`; `cmd_skill` (`:4685`) copies the folders to `~/.claude/skills` (Claude Code, Cursor) and
  `~/.agents/skills` (Codex, Gemini CLI, Copilot, Cursor); `--project` writes `./.claude/skills` and `./.agents/skills`; `--dir` writes one folder. Existing
  skills are kept unless `--force`. It finds the source at `sys._MEIPASS/skill` in a release or next to the file from source.
- **Public repo.** `noloman/shotfleet-skills` (MIT, skills only, a Claude Code plugin with its own marketplace and `.mcp.json` that starts `shotfleet mcp`).
  At each release run `sh tools/sync-public-skills.sh <checkout>`; it copies `skill/`, sets the plugin version and prints the diff, and never pushes. A skill removed here is
  removed there.
- `docs/AGENTS-snippet.md` is a block to paste into `AGENTS.md`, `CLAUDE.md` or `GEMINI.md`.

The skills are **tested like code** (`tests/test_agent_skills.py`): every `shotfleet <command> ...` inside a code fence or backticks in the skills, the snippet and
`llms.txt` is parsed with the program's real argparse parser (placeholders like `<dir>` replaced with sample values), every `references/` link must resolve,
frontmatter must be well formed, no em dashes or banned phrases, and the problem-line fragments the review skill explains must exist in `shotfleet.py`. Change a flag and
this test fails until the skill text agrees. The skills say what the tool does not do ("Do not claim Flutter or React Native work beyond reading their translation
files") and tell agents never to ask for or print the licence key; keep those rules when editing.

### Adding an MCP tool

1. Add a dict to `MCP_TOOLS` with `name`, `title`, a `description` that says what it changes and how long it takes, honest `annotations` (when in doubt
   `readOnlyHint` is false), and an `inputSchema` with `additionalProperties: False`.
2. Add a branch in `mcp_call`. Validate every argument (types, absolute paths, no option-looking strings), call an existing `cmd_*` or `check_any`, and keep output
   captured. Anything that runs a program or a shell command from user-supplied or config-supplied text needs an explicit opt-in argument like `hooks`.
3. Return a short summary; large payloads belong behind a `full` flag.
4. Tests: `tests/test_shotfleet.py` class `Mcp` shows how the protocol is tested without a client (its `serve()` helper runs `python3 shotfleet.py mcp` as a subprocess, writes JSON-RPC lines to its stdin and reads the replies). Update `README.md`
   ("What the MCP tools do"), `skill/README.md`, the main skill's last paragraph and the docs page; claims quote them.
5. A real-client check (`claude -p` with a throwaway MCP config) passed for 0.1.4 and is the model for a manual test.
