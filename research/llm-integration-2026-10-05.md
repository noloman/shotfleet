# shotfleet with LLMs and AI coding agents (research, 2026-10-05)

Question from the owner: "it'd be nice that paying users could easily integrate our app with LLMs and AI somehow.. perhaps with skills? I don't know, let's first investigate this".

Research and a recommendation only. Nothing was built. Base: `origin/claude/014-candidate` at `a698c96` (shotfleet 0.1.3 in source).

Labels: **measured** = I ran it, or read it in the code or in official docs today. **INFERENCE** = my judgement, not tested.

## Short answer

Most of the work is already done. shotfleet ships three Agent Skills, a `shotfleet skill install` command, an MCP server
(`shotfleet mcp`), `--json` output, stable exit codes, an AGENTS.md block and an `llms.txt`. What is missing is mostly
**distribution and a few sharp edges**:

1. The skills only reach people who already installed the program. They live in a private repo, so none of the one-line installers
   (`/plugin marketplace add`, `gh skill install`, `npx skills add`, `gemini skills install`, Codex `$skill-installer`) can find them.
2. `shotfleet skill install` writes to `~/.claude/skills` only. Codex, Gemini CLI and Copilot (personal) read `~/.agents/skills`, which
   the command never writes to. Our own docs say "Codex, Cursor, Gemini CLI ... read a project instructions file, not skill folders",
   and that is no longer true.
3. The MCP server works, but it is thin: no tool annotations, no `report` argument, the full screenshot list in every answer (big
   runs will go over Claude Code's 50,000-character tool-result limit), and it echoes back any protocol version the client asks for.
4. Problems in `check.json` are English sentences. Agents can read them (the review skill maps every line), but there is no stable
   code to branch on.

Top 3, with effort:

| # | What | Effort |
|---|---|---|
| 1 | `skill install` also writes `~/.agents/skills`, and fix the docs that say other agents can't use skills | 1-2 hours |
| 2 | A small **public** repo with just the skills, plus a Claude Code plugin marketplace in it (skills + `shotfleet mcp`) | half a day, then a sync step per release |
| 3 | MCP server hardening: annotations, `report` and summary output, `structuredContent`, version pinning, `no_hooks` on `run` | about 1 day |

Build first: **#1**. It turns the command people already have into one that covers Claude Code, Cursor, Codex, Copilot, Gemini CLI,
OpenCode and the rest, needs no decision about public repos, and fixes text on our own site that is now wrong.

Keep skills and agent support **free and public**. They are documentation that sells the paid part; the licence gate stays where it
is (`run` beyond 2 languages, and `export`).

---

## 1. What exists today, and how good it is

### 1.1 Inventory (measured, read from `origin/claude/014-candidate`)

| Piece | Where | State |
|---|---|---|
| Skill `shotfleet` | `skill/shotfleet/SKILL.md` (104 lines, 10.3 KB) + `references/` (troubleshooting 18.7 KB, config 10.8 KB, flow-writing 5.5 KB, ci 4.7 KB, licence 3.2 KB) | Good. Decision tree, commands, exit codes, `--json` shape, a "do not" list (no key in chat, no upload, no editing fastlane, ask before `run`) |
| Skill `shotfleet-review` | `skill/shotfleet-review/SKILL.md` (71 lines) | Good. Maps every problem line to a cause and who fixes it (app, flow, capture), with an output template |
| Skill `shotfleet-ci` | `skill/shotfleet-ci/SKILL.md` (64 lines) | Good, honest ("this recipe has not been run on GitHub yet") |
| Install command | `shotfleet skill install [--project] [--dir D] [--force]` (`cmd_skill`, shotfleet.py ~line 4091) | Works. Copies from the bundled `skill/` folder (PyInstaller `--add-data skill:skill` in `packaging/build.sh`) |
| MCP server | `shotfleet mcp` (`cmd_mcp`, `mcp_call`, `MCP_TOOLS`) | Works for `check`, `run`, `doctor`. Hand-written JSON-RPC over stdio, no SDK |
| Paste-in block | `docs/AGENTS-snippet.md` | Fine content; lives only in the private repo; its last rule points at `skill/shotfleet/`, a path users don't have |
| `llms.txt` | `site/public/llms.txt` (3.2 KB) | Good summary and links. No Markdown copies of the pages behind it |
| Docs page | `site/public/docs.html#agents` | Short section: `claude mcp add shotfleet -- shotfleet mcp`, the three skills, the install command |
| `--json` | `run`, `check`, `export` | stdout is only JSON, progress on stderr. `doctor` has no `--json` |
| Exit codes | 0 good, 1 problems, 2 setup error, 130 interrupted | Stable, documented, tested |
| Config hooks | `[hooks]` `before_run`, `after_run`, `before_export`, `after_export`; env `SHOTFLEET_EXIT`, `SHOTFLEET_PROBLEMS`, ... | Useful for agents too (e.g. `after_run` posts a summary). Not agent-specific |
| Tests | `tests/test_agent_skills.py`, 20 tests | Strong: every documented command parses with the real parser, JSON keys match, every problem line in the review skill exists in the program, prices match the site, no em dash, no banned phrases |

### 1.2 What I ran (measured)

- `python3 -m unittest tests.test_agent_skills`: **20 tests OK** (18.6 s). I did not run the full suite.
- `shotfleet skill install --dir <scratch>/skills`: installed `shotfleet`, `shotfleet-ci`, `shotfleet-review`.
- MCP handshake by hand: `initialize` answered with `protocolVersion` = whatever I sent (`2025-06-18`), `serverInfo` `shotfleet 0.1.3`;
  `tools/list` returned the three tools; `resources/list` returned `-32601 unknown method` (correct: no resources capability declared).
  I did **not** call the `run` or `check` tools (no simulators, no Maestro on this shared Mac), and did not connect a real MCP client.
- Size of a real `check.json` (`research/real-apps-2026-10-04/wger-android-19-languages/check.json`): 60 screenshots, 8,691 characters,
  **about 144 characters per screenshot**.
- Skill descriptions: 611, 430 and 376 characters (spec limit 1024). Main `SKILL.md` is about 2,600 tokens (spec advice: under 5,000).
- `gh repo view noloman/shotfleet`: **private**.

### 1.3 What a paying user can do today (measured from code and vendor docs)

On their Mac, after `curl -fsSL https://shotfleet.com/install.sh | sh` and `shotfleet activate <key>`:

- Claude Code: `shotfleet skill install`, then ask "check my fastlane screenshots". Or `claude mcp add shotfleet -- shotfleet mcp`.
- Cursor: works with the same `shotfleet skill install`, because Cursor also loads `~/.claude/skills` ([Cursor docs](https://cursor.com/docs/context/skills)).
- GitHub Copilot: works per project with `shotfleet skill install --project` (Copilot reads `.claude/skills`), not per user
  ([GitHub docs](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)).
- Codex, Gemini CLI, OpenCode and others: only with `--dir ~/.agents/skills`, which none of our docs tells them.
- Any MCP client (Cursor, Codex, Copilot, Claude Desktop...): add the command `shotfleet mcp`.
- CI: `check --json` on a Mac runner; `run`/`export` with `SHOTFLEET_KEY` from the secret store.

The licence works the same for an agent as for a person: the agent runs the CLI, the CLI reads
`~/Library/Application Support/shotfleet/licence.json`. The agent never needs the key, and the skills tell it never to ask for it.

### 1.4 What is missing or hard

| Gap | Why it matters | Evidence |
|---|---|---|
| No public home for the skills | Every popular installer (`/plugin marketplace add`, `gh skill install`, `npx skills add`, `gemini skills install`, Codex `$skill-installer`) reads a git repo or a URL. Ours is private. People who haven't installed shotfleet can't try the skills, and nobody finds them in skill directories | measured: repo private |
| `skill install` ignores `~/.agents/skills` | That folder is the shared one: Codex, Gemini CLI, Copilot (personal), Cursor and OpenCode read it. Claude Code does not | measured: code; vendor docs below |
| Our docs are out of date | `skill/README.md`: "Codex, Cursor, Gemini CLI and other agents: These read a project instructions file, not skill folders." All of them read skill folders now | measured |
| AGENTS snippet not shipped | `docs/AGENTS-snippet.md` is only in the private repo, and its last rule points at `skill/shotfleet/`, a path a buyer doesn't have | measured |
| MCP: no tool annotations | Clients can't tell `check` (read-only) from `run` (boots simulators for minutes, runs the config's `[hooks]` shell commands) | measured: `MCP_TOOLS` has no `annotations` |
| MCP: whole report in every answer | 144 chars per screenshot: 40 languages x 10 screens is about 58,000 characters before problems, over Claude Code's 50,000-character limit, so the answer goes to a file instead of the conversation | size measured; limit from [Claude Code MCP docs](https://code.claude.com/docs/en/mcp); the overflow itself is INFERENCE |
| MCP: `check` has no `report`, `locale`, `content` | The skill has to tell agents to prefer the CLI. Two ways to do one thing | measured |
| MCP: protocol version echo | The server answers `initialize` with whatever version the client sent. The current spec is `2026-07-28`, which drops `initialize` entirely and adds `server/discover`. Claiming a version we don't implement may mislead a client | code measured, spec from the [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog); the effect on real clients is INFERENCE |
| MCP `run` sends no progress | Claude Code aborts a stdio tool call after 30 minutes with no response and no progress notification | limit measured from the docs; that a big run hits it is INFERENCE |
| Problems are sentences, no codes | Fine for an LLM, harder for scripts and CI summaries; any rewording breaks parsers | measured: `problems: ["<locale>/<file>: <what>"]` |
| `doctor` has no `--json` | An agent has to parse `MISSING` lines | measured |
| Cloud agents can't run it | Claude Code on the web, Codex cloud and the Copilot cloud agent run in Linux sandboxes; shotfleet needs a Mac (Linux `check` exists from source only, no installer) | measured: `docs/linux.md` |

Verdict: the content is good and better tested than most skills I found. The weak parts are reach (where people get it) and the MCP edges.

---

## 2. The landscape (official docs, read 2026-10-05)

### 2.1 Agent Skills (SKILL.md)

- An open format started by Anthropic, now listed at [agentskills.io](https://agentskills.io) with more than 40 clients: Claude Code,
  Claude (claude.ai and API), ChatGPT and Codex, Cursor, GitHub Copilot, VS Code, Gemini CLI, OpenCode, Amp, Goose, Junie, Kiro, Roo
  Code, Factory and others (measured).
- Spec ([agentskills.io/specification](https://agentskills.io/specification)): `name` up to 64 chars, lowercase and hyphens, must match
  the folder; `description` up to 1024; optional `license`, `compatibility`, `metadata`, `allowed-tools`. Body under 500 lines, under
  5,000 tokens recommended; references one level deep. Validator: `skills-ref validate`. shotfleet's skills fit all of this (measured).
- Where each tool looks (measured from each vendor's docs):

| Tool | User folder | Project folder | Installer |
|---|---|---|---|
| Claude Code | `~/.claude/skills` | `.claude/skills` | plugins and marketplaces ([docs](https://code.claude.com/docs/en/skills)). Does **not** read `.agents/skills` |
| Cursor | `~/.cursor/skills`, `~/.agents/skills`, also `~/.claude/skills`, `~/.codex/skills` | `.cursor/skills`, `.agents/skills`, also `.claude/skills` | Cursor plugin marketplace from a GitHub repo ([docs](https://cursor.com/docs/context/skills)) |
| Codex | `~/.agents/skills` | `.agents/skills` | `$skill-installer <name>`, plugins ([docs](https://learn.chatgpt.com/docs/build-skills)) |
| GitHub Copilot | `~/.copilot/skills`, `~/.agents/skills` | `.github/skills`, `.claude/skills`, `.agents/skills` | `gh skill install owner/repo` (gh 2.90+, preview since April 2026) ([docs](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [changelog](https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/)) |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` | `gemini skills install <git url>` ([docs](https://geminicli.com/docs/cli/skills/)) |
| About 20 agents | | | `npx skills add owner/repo` (Vercel's skills.sh) ([overview](https://dev.to/stevengonsalvez/skillssh-npm-for-agent-skills-35jc)) |

Takeaway (INFERENCE from the table): writing to **`~/.claude/skills` and `~/.agents/skills`** covers every agent listed. And every
one-line installer needs a reachable git repo or URL.

### 2.2 Claude Code plugins and marketplaces

- A plugin bundles skills, agents, hooks and MCP servers as one install ([plugins](https://code.claude.com/docs/en/plugins)).
- A marketplace is a `.claude-plugin/marketplace.json`. It can live in a GitHub repo, on any git host, **at a plain HTTPS URL**, or in a
  folder ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).
- Plugin sources include `github`, `git-subdir`, `url`, `npm`, `archive` (a zip over HTTPS with a `sha256` pin), and `command`: a
  command on the user's machine that prints a plugin folder path, re-run once per session
  ([marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference)).
- So shotfleet could ship a Claude Code plugin with **no public repo at all**: host `marketplace.json` on shotfleet.com and point the
  entry at `{"source": "command", "command": "shotfleet skill path"}` (a new tiny subcommand that prints the bundled folder) or at a
  pinned zip on the site. Users run `/plugin marketplace add https://shotfleet.com/<path>/marketplace.json`. (Mechanism measured from
  the docs; that it works for us is INFERENCE, not tried.)
- Archive downloads can carry auth headers from a `headersHelper` command, so a paid-only plugin is technically possible. Not
  recommended (section 5).
- Background auto-update for third-party marketplaces is **off by default**; users turn it on or run `/plugin marketplace update`
  (measured). With a `command` source the plugin follows the installed shotfleet version each session, so this matters less (INFERENCE).
- An enabled plugin costs context on every turn (each skill's name and description), and its MCP servers start with every session
  (measured). Three short descriptions is small; still a reason to keep them tight.
- Claude Code lifecycle hooks in a plugin: I found no hook that helps shotfleet users. A `PostToolUse` hook on `shotfleet check`
  would only repeat what the review skill does. Skip (INFERENCE).

### 2.3 MCP

- Current spec is **`2026-07-28`**: stateless, no `initialize` handshake, a required `server/discover`, a required `resultType` on
  results, `ttlMs`/`cacheScope` on list results, `ping` removed. Clients must treat results without `resultType` from older servers
  as complete ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). Older clients still speak
  `2025-06-18` / `2025-11-25`.
- Tools can declare `annotations` (behaviour hints), `outputSchema` and return `structuredContent`; the spec says a human SHOULD be
  able to deny tool calls, and clients SHOULD confirm sensitive ones ([tools](https://modelcontextprotocol.io/specification/latest/server/tools)).
- Claude Code: stdio servers get a 30-minute idle timeout (progress notifications reset it) and a wall-clock default of about 28 hours;
  text results over 50,000 characters or 25,000 tokens go to a file; a tool can raise the character cap with
  `_meta["anthropic/maxResultSizeChars"]` up to 500,000 ([Claude Code MCP](https://code.claude.com/docs/en/mcp)).
- One-click install for Claude Desktop is the `.mcpb` bundle ([Anthropic](https://www.anthropic.com/engineering/desktop-extensions),
  [MCP blog](https://blog.modelcontextprotocol.io/posts/2025-11-20-adopting-mcpb/)). Node is recommended; our server is a signed
  PyInstaller binary that `install.sh` already puts on the Mac, so a bundle adds little.
- **Maestro ships the same pattern**: `maestro mcp`, inside the CLI, added with `claude mcp add maestro -- maestro mcp`, free
  ([maestro.dev/mcp](https://maestro.dev/mcp)). Users who write flows with an agent will want Maestro's MCP (look at the screen, tap)
  next to shotfleet (rewrite for every language and check). They fit together; we don't need to copy Maestro's tools.

Skill + CLI versus MCP (INFERENCE, my judgement):

| | Skill + CLI | MCP server |
|---|---|---|
| Works in | every agent that has a shell | every MCP client, including ones without a shell (Claude Desktop) |
| Context cost | name + description until used | tool schemas (deferred by tool search in Claude Code) |
| Long runs | the shell shows progress; the agent can background it | one blocking call, no progress today, idle timeouts |
| Report location, flags | everything the CLI has | only what we expose |
| Safety | the agent's own shell permission prompts show the exact command | per-tool prompts; annotations help the client |
| Maintenance | text + the tests we already have | a hand-rolled protocol that changed under us this summer |

Skill + CLI is the main path for coding agents. Keep the MCP server for MCP-only clients and for people who like tools; make it
honest and small rather than bigger.

Security notes for the MCP server (code measured, risk is INFERENCE):
- `run` executes the config's `[hooks]` shell commands. An agent tricked by prompt injection in a cloned repo into calling `run` on a
  hostile `shotfleet.toml` runs those commands. The CLI has the same property, but there the agent's shell prompt shows the command.
  Mark `run` as not read-only and open-world, and add a `no_hooks` argument that defaults to true over MCP.
- `check` only reads, and writes `./shotfleet-check` in the server's working folder. Mark it read-only.
- `claude mcp add --env SHOTFLEET_KEY=...` would store the key in plain text in `~/.claude.json`. The docs should say: activate the Mac
  instead; use `SHOTFLEET_KEY` only from CI secrets.

### 2.4 AGENTS.md / CLAUDE.md / Cursor rules

- AGENTS.md is stewarded by the Agentic AI Foundation (Linux Foundation); read by Codex, Cursor, Copilot, Gemini CLI, Jules, Zed, Aider,
  Devin and more; nested files supported ([agents.md](https://agents.md/)).
- Claude Code now reads a repo's `AGENTS.md` too, alone or next to CLAUDE.md ([Claude Code memory](https://code.claude.com/docs/en/memory)).
- So one block in `AGENTS.md` reaches nearly everyone. Our snippet's table (CLAUDE.md, `.cursorrules`, GEMINI.md) can shrink to
  "put it in AGENTS.md". Now that every big agent loads skills, the snippet matters less: it is for teams that want the rules in the repo.

### 2.5 llms.txt

- A proposal by Jeremy Howard: H1, short summary, H2 link lists; pages should also exist as Markdown at the same URL plus `.md`
  ([llmstxt.org](https://llmstxt.org/)). OpenAI, Anthropic and Google publish their own; Lighthouse audits it (measured, from that page).
  `llms-full.txt` is not part of the proposal.
- Ours is good. The missing piece is a Markdown copy of `docs.html` (`/docs.md`) so an agent reading the docs gets clean text, not
  39 KB of HTML. Low value, low effort.

### 2.6 Output formats agents handle well

What we have already matches the usual advice: JSON only on stdout, progress on stderr, stable exit codes, a fixed key set, and
tests that pin it. Two additions would help (my design suggestions, INFERENCE; there is no standard):
- a stable `code` per problem (`wrong_language`, `copy`, `missing`, `untranslated_app`, `blank`, `alpha`, `bad_size`, `too_many`,
  `iphone_size_set`, `ipad_required`, `expect_missing`...), with `locale` and `file` fields, next to the existing sentences;
- `doctor --json` (`{"exit", "ios": {...}, "android": {...}, "missing": [...]}`).

### 2.7 What others do

| Tool | Agent story | Source |
|---|---|---|
| fastlane snapshot | Nothing official. A community `fastlane-mcp-server`, and a community "fastlane snapshot" skill on a skills site | [lyderdev/fastlane-mcp-server](https://github.com/lyderdev/fastlane-mcp-server), [mcpmarket](https://mcpmarket.com/tools/skills/fastlane-snapshot) |
| Maestro | MCP server inside the CLI, free | [maestro.dev/mcp](https://maestro.dev/mcp) |
| AppScreenshotStudio | Paid, credit-based; local stdio MCP via `npx`, account API key in an env var; 9 tools | [docs](https://appscreenshotstudio.com/docs/mcp) |
| Design generators (AppScreens, Picasso, AppLaunchFlow) | Mostly web editors; several open-source MCP servers make mockups | [roundup](https://www.applaunchflow.com/blog/best-app-store-screenshot-generators-2026), [store-screenshot-mcp](https://github.com/k984530/store-screenshot-mcp), [appscreen-mcp](https://github.com/AppSolves/appscreen-mcp), [appshots-mcp](https://github.com/Murzav/appshots-mcp) |
| RevenueCat (a paid dev tool) | Claude Code plugin with skills plus an MCP server, free to install; the account is the gate | measured: installed on this Mac as the `revenuecat` plugin |

Nobody in screenshots does the **check** part for agents. The design tools make frames, fastlane captures, and nobody tells the
agent "German screen 3 shows English". That is our angle (INFERENCE).

---

## 3. Ranked options

Scored for a paying user (and for sales), smallest useful version first.

| Rank | Option | User value | Effort | Risk | What it takes |
|---|---|---|---|---|---|
| 1 | `skill install` writes `~/.claude/skills` **and** `~/.agents/skills` (with `--project`: `.claude/skills` and `.agents/skills`); fix the docs | High: one command covers every agent | 1-2 h | Very low: two copies of the same files; the `--force` and "kept" rules stay | Change the `cmd_skill` default to two folders; update `skill/README.md`, `docs.html#agents`, the snippet's last rule ("run `shotfleet skill install --project`"), one test |
| 2 | Public skills repo `noloman/shotfleet-skills` with `.claude-plugin/marketplace.json` (plugin = 3 skills + `.mcp.json` running `shotfleet mcp`), and a `.cursor-plugin/marketplace.json` | High for reach: `/plugin marketplace add noloman/shotfleet-skills`, `gh skill install`, `npx skills add`, `gemini skills install`, the Cursor marketplace, skill directories | Half a day, then a copy step in `packaging/publish.sh` per release | Low: the skills are already in a free download. Two copies can drift, so the publish step copies and nobody hand-edits | New public repo; `claude plugin validate`; a release step that copies `skill/` and bumps `version`; a line on the site |
| 2b | Same for Claude Code only, without a public repo: `marketplace.json` on shotfleet.com, entry source `command: shotfleet skill path` | Claude Code only | 2-3 h | Low. Not tried; needs Claude Code 2.1.229+ | New `skill path` subcommand; the JSON on the site |
| 3 | MCP hardening | Medium: MCP clients get a safer, smaller tool | ~1 day | Medium: hand-rolled protocol; test with a real client before shipping | `annotations` (`check` read-only; `run` not read-only, open-world); `check` gets `report`, `locale`, `content`; summary result by default (counts + problems + notes, no screenshot list); `structuredContent` plus the text copy; answer `initialize` only with versions we implement (`2025-06-18`, `2025-11-25`); `no_hooks` true by default on `run`; progress notifications during `run`; one end-to-end test with `claude -p` on a fixture folder (`check` only) |
| 4 | Problem codes in JSON | Medium for CI and scripts; small for LLMs (they read sentences fine) | ~1 day (17 `problems` and 10 `notes` call sites, tests, skill tables) | Low if additive: keep `problems` strings, add `issues: [{code, locale, file, text}]` | A code per call site; the review skill table gains a code column; a test that every code is documented |
| 5 | `doctor --json` | Low-medium | 2-3 h | Low | Collect the lines `doctor` already prints |
| 6 | `/docs.md` and `<link rel="alternate" type="text/markdown">` | Low | 1-2 h | None | Generate from `docs.html` at build, or keep by hand |
| 7 | `.mcpb` bundle for Claude Desktop | Low: our buyers live in terminals and IDEs | 1 day | Medium: another package to sign and test | Skip for now |
| 8 | Paid-only plugin (archive + a `headersHelper` that mints a token from the licence) | Negative for sales | 2-3 days + a server | High: needs a licence server we don't have (Gumroad is the only backend) | Skip |
| 9 | Claude Code plugin hooks, subagents, extra slash commands | Low. Skills already show up as `/shotfleet` and so on | | | Skip until someone asks |

---

## 4. Recommended plan, in small steps

Each step stands alone and can ship in a patch release.

1. **Fix what is wrong (1-2 h).** `skill install` writes both `~/.claude/skills` and `~/.agents/skills` (with `--project`: `.claude/skills`
   and `.agents/skills`). Rewrite the "Codex, Cursor, Gemini CLI" part of `skill/README.md` and the docs section: every major agent reads
   skill folders now. Snippet rule 8 becomes "run `shotfleet skill install --project`". Extend the install test for the second folder.
2. **Say it on the site (1 h).** One short block with the buyer sentences from section 6, on the home page or the docs page. Publish
   the `AGENTS.md` snippet on the docs page (it isn't anywhere public today).
3. **Decide public or not (owner, 5 minutes).** Recommendation: public, skills only, no program code.
4. **Public skills repo + marketplace (half a day).** `noloman/shotfleet-skills`: `skills/shotfleet*/`, `.claude-plugin/marketplace.json`,
   `.claude-plugin/plugin.json`, `.mcp.json` (`shotfleet mcp`), a README with the install line for each agent and "needs shotfleet
   installed: `curl -fsSL https://shotfleet.com/install.sh | sh`". Validate with `claude plugin validate`. Install it once from the
   repo in a clean Claude Code profile. Add the copy step to `packaging/publish.sh`.
5. **MCP, the safe minimum (half a day).** Annotations, no echoed protocol version, `no_hooks` default on `run`, `report` on `check`,
   summary result by default. One test that runs `check` through the server on `tests/fixtures`.
6. **MCP, the rest when someone uses it (half a day).** `structuredContent` + `outputSchema`, progress notifications during `run`,
   `server/discover` for `2026-07-28` clients. Wait for a real user asking (Gumroad emails, the hello@ inbox).
7. **Problem codes (1 day), when CI users ask.** An additive `issues` list. Then `doctor --json`.
8. **Get it found.** Once the repo is public, mention the install lines in launch posts and the README. Posting is the owner's call.

Not doing: a paid-only plugin, `.mcpb`, cloud-agent support (needs a Linux installer first, see `docs/linux.md`).

---

## 5. Licence angle (trade-offs only; the model doesn't change)

**Free and public skills and MCP (recommended).**
- For: the skills are how-to text; they sell `run` and `export`, which stay paid. `check` is already free, so an agent that runs
  `check` and finds a German screen in English is the best ad we have. Public repos get found through `gh skill search`, skills.sh and
  marketplace browsing. The program, with the skills inside, is already a free download, so hiding the repo protects nothing.
- Against: competitors can read how we explain the tool (they already can, from the free download). Two copies to keep in sync
  (the publish step solves it).

**Skills for paying users only.**
- For: one more line to list at checkout.
- Against: nothing to protect (the free download has them); gating needs a token server Gumroad doesn't give us; agents that can't
  load the skill guess commands and fail, and the buyer blames shotfleet. Every peer I found (Maestro, RevenueCat, the fastlane
  community) gives the agent layer away and charges for the product or the account.

**How the key works with an agent (measured from code and `skill/shotfleet/references/licence.md`):**
- Laptop: the user runs `shotfleet activate <key>` once in their own terminal. After that, CLI calls from any agent and the MCP server
  are licensed, because they read the same `licence.json`. The skills already forbid asking for the key, reading `licence.json`, or
  activating with a key pasted into chat. Up to 3 Macs per key.
- CI: `SHOTFLEET_KEY` from the secret store, checked online each run, no activation used. It fails open when Gumroad is unreachable.
- An agent in CI (for example the Claude Code GitHub Action or the Copilot coding agent on a macOS runner): the same `SHOTFLEET_KEY`
  secret. Cloud agents on Linux can't run shotfleet's capture at all.
- One gap worth a doc line: don't pass the key to the MCP server with `claude mcp add --env`; it would sit in plain text in
  `~/.claude.json`. Activate the Mac instead.
- Seats: "per developer" means an agent is not a seat; it acts for the developer who owns the licence. Worth one sentence in the
  terms or an FAQ if anyone asks (INFERENCE; the owner decides).

---

## 6. Sentences the site could use

Plain and short. Pick a few.

- Works with your AI coding agent. Claude Code, Cursor, Codex, Copilot, Gemini CLI: if it can run a terminal command, it can run shotfleet.
- One command teaches your agent how to use it: `shotfleet skill install`.
- Ask "are my German screenshots actually in German?" and your agent runs the check and tells you which screens to fix.
- Your agent gets a plain list back: which language, which screen, what's wrong, and whether to fix the app or the flow.
- The skills are free. So is `check`. You pay for capturing every language and exporting to fastlane.
- Your licence key stays on your Mac. The agent never needs it, and we tell it not to ask.
- Same in CI: exit 0 means every screenshot passed, 1 means it found problems, and `--json` gives you the list.
- Using Claude Code? `/plugin marketplace add noloman/shotfleet-skills` (only once step 4 exists).
- Prefer MCP? `claude mcp add shotfleet -- shotfleet mcp` gives your agent `check`, `run` and `doctor`.
- shotfleet never uploads anything to the App Store or Google Play, so your agent can't either through it.

---

## Sources

- Agent Skills overview and clients: https://agentskills.io
- Agent Skills specification: https://agentskills.io/specification
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Create a marketplace: https://code.claude.com/docs/en/plugin-marketplaces
- Marketplace reference (sources, `command`, `archive`): https://code.claude.com/docs/en/plugins/marketplace-reference
- Host a marketplace (URL hosting, auto-update, headersHelper): https://code.claude.com/docs/en/plugins/host-marketplace
- Claude Code MCP (timeouts, output limits, scopes): https://code.claude.com/docs/en/mcp
- Claude Code memory (AGENTS.md): https://code.claude.com/docs/en/memory
- Cursor skills: https://cursor.com/docs/context/skills
- Codex skills: https://learn.chatgpt.com/docs/build-skills (redirected from https://developers.openai.com/codex/skills/)
- GitHub Copilot skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- `gh skill`: https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/
- Gemini CLI skills: https://geminicli.com/docs/cli/skills/
- skills.sh: https://dev.to/stevengonsalvez/skillssh-npm-for-agent-skills-35jc
- MCP tools spec: https://modelcontextprotocol.io/specification/latest/server/tools
- MCP 2026-07-28 changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog
- MCPB: https://www.anthropic.com/engineering/desktop-extensions and https://blog.modelcontextprotocol.io/posts/2025-11-20-adopting-mcpb/
- AGENTS.md: https://agents.md/
- llms.txt: https://llmstxt.org/
- Maestro MCP: https://maestro.dev/mcp
- AppScreenshotStudio MCP: https://appscreenshotstudio.com/docs/mcp
- fastlane community MCP: https://github.com/lyderdev/fastlane-mcp-server
- Screenshot generator roundup: https://www.applaunchflow.com/blog/best-app-store-screenshot-generators-2026
