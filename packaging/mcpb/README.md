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

## Publishing to the official MCP registry (done 2026-10-11 for 0.1.9)

The registry lists `com.shotfleet/shotfleet`. Its MCPB package has to be a GitHub or GitLab release asset, so the bundle lives in the public repo `noloman/shotfleet-skills` as the release `mcpb-v<version>`.

For each shotfleet release:

1. `sh build.sh <out>/shotfleet.mcpb`, then `gh release create mcpb-v<version> <out>/shotfleet.mcpb -R noloman/shotfleet-skills`.
2. Put the new version and the file's sha256 in `server.json` (`openssl dgst -sha256 shotfleet.mcpb`).
3. Log in with the domain key, not GitHub: `mcp-publisher login http --domain shotfleet.com --private-key <hex of the Ed25519 key>`. The matching public record is served at `https://shotfleet.com/.well-known/mcp-registry-auth`. The private key is kept outside git (`shotfleet-rc-build/mcpb-release/key.pem`, mode 600).
4. `mcp-publisher publish`.

Anthropic's own directory no longer takes MCPB bundles; a local server goes in as part of a plugin (the skills repo is one). Smithery takes a stdio MCPB release through its API or CLI and needs a Smithery account.
