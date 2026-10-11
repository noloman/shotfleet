# shotfleet MCP bundle

An [MCPB](https://github.com/anthropics/mcpb) bundle (`shotfleet.mcpb`) for the shotfleet MCP server, for Claude
Desktop, Smithery and the MCP registry. It has the tools `check`, `doctor` and `run`.

The bundle does not contain shotfleet. It holds `manifest.json` and one small script, `server/shotfleet-mcp`, that runs
`shotfleet mcp` from the copy you installed. Install that first (macOS, Apple silicon only):

```bash
curl -fsSL https://shotfleet.com/install.sh | sh
```

Why a script and not the plain command: apps started from the Dock have a short PATH, and the installer links
shotfleet into Homebrew's bin, `/usr/local/bin` or `~/.local/bin`. The script looks in those and in
`~/Library/Application Support/shotfleet/app`. If it finds nothing it prints the install line and exits.

The spec has no CPU field, so the manifest says `darwin` and the description and the script say Apple silicon.

Your licence key never goes in the bundle or an MCP setting. Run `shotfleet activate <key>` once in Terminal.

Build (local, publishes nothing): `sh build.sh`, which validates and packs with the pinned official `mcpb` package.
Bump `version` in `manifest.json` with each shotfleet release; `build.sh` refuses a mismatch with `shotfleet.py`.
