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

## Claude Code

Copy or symlink the skill folders into a skills directory. Per user:

```bash
mkdir -p ~/.claude/skills
cp -R skill/shotfleet skill/shotfleet-ci skill/shotfleet-review ~/.claude/skills/
```

Or per project, so the whole team gets them (commit the folders):

```bash
mkdir -p .claude/skills
cp -R skill/shotfleet skill/shotfleet-ci skill/shotfleet-review .claude/skills/
```

A symlink (`ln -s "$PWD/skill/shotfleet" ~/.claude/skills/shotfleet`) keeps them up to date when you update the
folder. Restart Claude Code or start a new session; ask "check my fastlane screenshots with shotfleet" to try it.

To give Claude Code tools instead of instructions, the program also runs an MCP server:
`claude mcp add shotfleet -- shotfleet mcp` (tools `check`, `run`, `doctor`). Its `check` writes the report into a
`shotfleet-check` folder inside the folder it checks; the skills use the CLI with `--report` instead.

## Codex, Cursor, Gemini CLI and other agents

These read a project instructions file, not skill folders. Paste the block from
[`docs/AGENTS-snippet.md`](../docs/AGENTS-snippet.md) into the file your agent reads:

| Agent | File |
|---|---|
| Codex and agents that read AGENTS.md | `AGENTS.md` |
| Claude Code (instead of skills) | `CLAUDE.md` |
| Cursor | `.cursorrules` or `.cursor/rules/shotfleet.mdc` |
| Gemini CLI | `GEMINI.md` |

The block names what shotfleet is, the six commands (`doctor`, `init`, `run`, `check`, `export`, `activate`) and the
rules. For more detail it points at `skill/shotfleet/`: keep that folder in the repo, or paste the contents of
`skill/shotfleet/references/troubleshooting.md` next to it.

## One command

The installed program carries these skills: `shotfleet skill install` copies them into `~/.claude/skills`, `shotfleet skill install --project` into `./.claude/skills`, and `--dir <folder>` into another agent's skills folder. Skills that are already there are kept unless you pass `--force`.
