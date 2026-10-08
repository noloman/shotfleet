# 6. The MCP server and the agent skills

Back to the [index](../ARCHITECTURE.md). Written at `285e099` (0.1.6). This guide gives names, not line numbers: lines drift with every release. For line numbers use [the generated function map](../engineering/12-function-map.md).

shotfleet reaches AI coding agents two ways. **Skills** are instruction files an agent reads (zero code, zero risk). The **MCP server** gives the agent
callable tools (code that runs with the user's privileges). They overlap on purpose: the skills use the CLI, the MCP server wraps the same functions.

## 6.1 The MCP server

`shotfleet mcp` (`cmd_mcp`) is a Model Context Protocol server on stdin and stdout: JSON-RPC 2.0, one message per line.

### Protocol behaviour

- Only `2025-11-25` and `2025-06-18` (`MCP_VERSIONS`). `initialize` echoes the client's version when it is one of these, else answers with the
  newest. The comment above the constant says why not others: 2025-03-26 requires JSON-RPC batches, and 2026-07-28 has no `initialize` and needs
  `server/discover` and per-request `_meta`. A batch (a JSON array) gets error `-32600`. An unparseable line gets `-32700`; an unknown method `-32601`.
  Notifications (no `id`: `initialized`, `cancelled`) are ignored. `ping` returns `{}`.
- It writes with `sys.__stdout__`, the real stdout, because `mcp_call` redirects `sys.stdout` and `sys.stderr` into a buffer while a tool runs. A stray
  `print` inside a tool therefore cannot corrupt the protocol.
- Capabilities: `{"tools": {}}`. No resources, no prompts. `serverInfo.version` is `VERSION`.
- **Progress.** If the client passes `_meta.progressToken`, a heartbeat thread (`MCP_HEARTBEAT_S = 30`) sends `notifications/progress` carrying the
  last non-empty output line, because Claude Code drops a stdio call that is silent for 30 minutes and a `run` can take an hour.

### Tools (`MCP_TOOLS`)

| Tool | Does | Input schema | Annotations |
|---|---|---|---|
| `check` | `check_any(...)` on a folder; writes `check.json` and `index.html` to the report folder, **replacing** those two files if they are there; runs no program | `folder` (required), `app`, `strings` (array of globs, or one string), `report`, `full`; `additionalProperties: false` | `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: true`, `openWorldHint: false` (it overwrites its report) |
| `doctor` | `cmd_doctor()` with no fix: reports, installs nothing | none (`additionalProperties: false`) | `readOnlyHint: true`, `openWorldHint: true` (asks shotfleet.com for the latest version) |
| `run` | `apply_free_tier()` then `cmd_run(config, locales)`: boots devices, installs and runs the config's app (and, with `[capture]`, its test bundle), replaces the output folder's screenshots and report | `config` (required), `locales` (non-empty array), `full`, `hooks`; `additionalProperties: false` | `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: false`, `openWorldHint: true` |

There is deliberately no `export` tool, no `activate`, no `init`, no `skill` over MCP. Licence handling stays in the user's terminal so the key never passes through an
agent.

`mcp_call(name, args, progress)` is the dispatcher:

1. Resets `LAST_REPORT` and `REPORTS` so a call that never reaches `check` cannot return the previous call's report.
2. Runs the tool with stdout and stderr captured in a `StringIO`.
3. **Returns a short summary by default** (`mcp_summary`): `{"exit", "screenshots", "languages", "problems_total", "problems" (first 100, each cut to
   300 characters), "notes_total", "notes", "reports" (absolute paths of every check.json)}` plus a `more` hint when truncated. Why: a 40-language,
   10-screen full report is about 67,000 characters, and Claude Code moves tool results over 50,000 to a file. `full: true` returns
   `{"exit", ...reports_json()}` instead.
4. Any exception becomes `isError: true` with the message plus the last 2,000 characters of captured output. One bad call never kills the server
   (`except Exception`, which is the only broad catch in the program, and says why).
5. For `doctor`, or `check` and `run` that produced no report, the reply is the captured log text.

### Safety gates and where they stop

The threat is a prompt-injected agent, or a `shotfleet.toml` from a repo you just cloned, using the tools to run something on the user's Mac. The 2026-10-07 security review (S1, S2) found two holes; both are closed on main.

| Gate | What it does | Limit |
|---|---|---|
| **Config commands are opt-in** (S1). `config_commands(config)` lists every command a config makes `run` execute: `[hooks]` (shell), `[capture] build` (shell), `[ios] simctl` (`xcrun simctl` on the Mac), `[android] shell` (`adb shell`). `mcp_call` refuses the call with a line naming them unless `hooks` is exactly `True` | with `hooks: true` the call sets `NO_HOOKS = False` and `CONFIG_COMMANDS = True`; without it, `[hooks]` are skipped, and a config that also has any of the other three is **refused before anything runs** ("... has commands that run on this Mac or its devices: [capture] build. Over MCP they only run when you pass hooks: true. Read them in the config first"). A string `"true"` does not count. A `finally` restores both flags | **the last guard:** `refuse_config_commands` is called inside `capture_build` and `run_setup`, so even a path that `config_commands` missed cannot run a command with `CONFIG_COMMANDS` false. `run_hook` honours `NO_HOOKS`. These are the only `/bin/sh` sites. Over MCP the **app and the test bundle still install and run on the simulators** (that is what `run` is for), so the tool description says to point it only at a project you trust. The CLI is unchanged |
| **`check` runs no program** (S2). `mcp_call` returns an error as soon as `ocr_command` is among the arguments, whatever its value, and passes `None` to `check_any` | `shotfleet check --ocr-command` in a terminal is the only way. The tool is no longer marked `readOnlyHint`, because it overwrites `check.json` and `index.html` | `SHOTFLEET_OCR` in the **server's own environment** is still honoured by `cmd_check`: whoever configured the server set it |
| **Arguments are validated** | `mcp_path` accepts only a non-empty string and returns an absolute, `~`-expanded path, so a value is never read as an option by a program it is handed to; `strings` is a list of strings or one string (clients send one since 0.1.4); `locales` is a non-empty list, and every code goes through `check_locales` (`SAFE_LOCALE`) in `cmd_run` | **`additionalProperties: false` is only in the `inputSchema` and advisory to clients; `mcp_call` never checks for extra keys** (`run` with `{"bogus": 1}` proceeds, and `full: "yes"` counts as true by truthiness). No valid call can break, but no unknown one is refused either |
| **Licence is re-read per call** | `run` calls `apply_free_tier()` like the CLI, which resets `LOCALE_CAP` and re-runs `require_licence`, so a key activated while the server is up lifts the cap. `check` needs no licence and never calls it | with `SHOTFLEET_KEY` set in the server's environment and refused, `apply_free_tier` raises and the call returns `isError` (no silent 2-language run). An MCP `run` skips the Maestro version refusal/warning that the CLI's `main_dispatch` does (the deny list `MAESTRO_BAD` is empty today, so nothing differs) |
| **No licence key in the protocol** | no tool takes or returns one | `SHOTFLEET_KEY` can still be in the server's environment; README tells users not to pass it with `claude mcp add --env` because it lands in plain text in `~/.claude.json` |
| **Annotations** | hints for the client's own permission UI | hints only; the client decides |
| **`check` writes only its report** | into `./shotfleet-check` in the **server's** working directory (never inside the checked folder), or the run folder for shotfleet output, or `report` | `check` never changes a screenshot |

Verified by the final review of `cb32bca` (`shotfleet-rc-build/code-review-2026-10-07/final-merged.md`), from source with no devices: `tools/list` shows `check`, `doctor`, `run`; `check` with `ocr_command` is refused; `run` on a config with a `[capture]` build is refused
without `hooks`, and with `hooks: "true"`, and the build ran (marker file) only with `hooks: true`; `locales: ["de", "../x"]` and `locales: "de"` are refused. Tests: `tests/test_security.py` (`McpRunRunsNoConfigCommandUnlessAsked`,
`McpCheckRunsNoProgram`, `LocalesAreNeverPaths`, `LockFilesInTmp`; 16 tests, each fails on `c18473f`).

Remaining limits on main:

- A config with a `[capture]` build is refused over MCP without `hooks: true` **even when the test bundle is already built** and the build would be skipped (`--no-build` has no MCP argument). Conservative, and the tool description says so.
- On a successful MCP `run` the summary drops the log lines "free tier: capturing 2 of N languages" and the licence note; only `languages` in the summary shows the cap, and an agent is not told why. Cheap fix if wanted: a `note` field when `LOCALE_CAP` is set.
- See [11](11-security-and-privacy.md) for the other trust boundaries.

## 6.2 The agent skills

`skill/` holds three skills, each a folder with `SKILL.md` (frontmatter `name` and `description`, then a short body):

| Skill | For |
|---|---|
| `shotfleet/` | the main skill: decision tree, commands, exit codes, `--json` reading, flow writing. `references/`: `troubleshooting.md`, `flow-writing.md`, `config.md`, `ci.md`, `licence.md` (loaded on demand) |
| `shotfleet-ci/` | add `shotfleet check` to GitHub Actions or another CI; `SHOTFLEET_KEY` |
| `shotfleet-review/` | turn a `check.json` into a fix list; a table of every problem line and what it means |

Distribution paths:

- **Inside the program.** `build.sh` passes `--add-data skill:skill`; `cmd_skill` copies the folders to `~/.claude/skills` (Claude Code, Cursor) and
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
