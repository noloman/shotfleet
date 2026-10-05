# shotfleet skills for AI coding agents

Three skills that let an AI coding agent install, set up, run, check and troubleshoot shotfleet without a human
reading the README:

| Skill | Use |
|---|---|
| `shotfleet/` | the main skill: decision tree, commands, exit codes, `--json`, flow writing, `references/` (troubleshooting, flow-writing, config, ci, licence) |
| `shotfleet-ci/` | add `shotfleet check` to GitHub Actions or another CI |
| `shotfleet-review/` | read a check report and turn it into a fix list |

Each folder has a `SKILL.md` (name and description in the frontmatter, short body). `shotfleet/` loads detail on demand
from its `references/` folder.

## Install

The installed program carries these skills. One command copies them where your agents look:

```bash
shotfleet skill install
```

| Folder | Read by |
|---|---|
| `~/.claude/skills` | Claude Code, Cursor |
| `~/.agents/skills` | Codex, Gemini CLI, GitHub Copilot, Cursor |

`shotfleet skill install --project` copies them into `./.claude/skills` and `./.agents/skills` in your project instead,
so the whole team gets them (commit the folders). `--dir <folder>` copies them into one folder you choose. Skills that
are already there are kept unless you pass `--force`. Start a new agent session, then ask "check my fastlane
screenshots with shotfleet" to try it.

From a copy of this repo you can also copy or symlink the folders yourself, for example:

```bash
mkdir -p ~/.claude/skills ~/.agents/skills
cp -R skill/shotfleet skill/shotfleet-ci skill/shotfleet-review ~/.claude/skills/
cp -R skill/shotfleet skill/shotfleet-ci skill/shotfleet-review ~/.agents/skills/
```

A symlink (`ln -s "$PWD/skill/shotfleet" ~/.claude/skills/shotfleet`) keeps them up to date when you update the
folder.

## MCP

To give your agent tools instead of instructions, the program also runs an MCP server:
`claude mcp add shotfleet -- shotfleet mcp` (tools `check`, `run`, `doctor`), or the command `shotfleet mcp` in any
other MCP client. Its `check` writes the report into a
`./shotfleet-check` folder in the server's working directory (never inside the folder it checks); the skills use the CLI with `--report` instead.

## Rules in the repo (optional)

If your team wants the rules in the repo too, paste the block from
[`docs/AGENTS-snippet.md`](../docs/AGENTS-snippet.md) into the file your agent reads:

| Agent | File |
|---|---|
| Codex, Cursor, GitHub Copilot and agents that read AGENTS.md | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |

The block names what shotfleet is, the six commands (`doctor`, `init`, `run`, `check`, `export`, `activate`) and the
rules. For more detail it points at the installed skill (`shotfleet skill install --project`).
