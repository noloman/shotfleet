# 4. Setup commands, MCP server and agent skills

Scope: the commands a buyer runs before and around `run` (`doctor`, `doctor --fix`, `init`, `init --capture`), the MCP server (`shotfleet mcp`), the three agent skills (`shotfleet skill install`), the external-command plugin mechanism, and the Linux `check` Docker image. Anchors are `shotfleet.py:LINE` at `7e5176c` (0.1.7). A longer 0.1.6-era treatment of MCP and skills is [../architecture/06-mcp-and-skills.md](../architecture/06-mcp-and-skills.md).

## 4.1 `doctor`

`cmd_doctor(fix, yes, config)` (`:4196`) checks the tools shotfleet drives and prints, for each, `ok` or `MISSING` plus the exact fix. It changes nothing unless `--fix` is given. It is free and has no licence code.

What it checks (one row per tool, tagged with the platform that needs it, `both`, `iOS` or `Android`):

| Check | Source of truth |
|---|---|
| Maestro (shows the version and the tested versions) | `maestro_cmd` `:3960`: `$SHOTFLEET_MAESTRO`, else `~/.shotfleet/maestro/bin/maestro`, else `maestro` on the PATH; `read_maestro_version` `:3924`; needs 2.x |
| Java 17 or newer | `find_java` `:3878`: `$JAVA_HOME`, `java` on the PATH, `~/.shotfleet/jre`, `/usr/libexec/java_home`, Homebrew's keg-only openjdk, SDKMAN, `/Library/Java/...`, `/usr/lib/jvm`; `java_env` `:3893` hands the result to Maestro |
| `swiftc` on a Mac (not needed in a frozen build) or Tesseract elsewhere | `have("swiftc")` |
| `xcrun simctl` and an iOS Simulator runtime (Mac) | `simctl_works` `:4164` (timed, 120 s), `ios_runtimes` `:4169`; `xcode_hint` `:4177` names an installed-but-unselected Xcode |
| `/dev/kvm` (Linux only) | `os.access` |
| `adb`, `emulator`, `avdmanager`, `aapt2`, a system image of API 33 or newer | `find_sdk` `:2362` (order: `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `~/Library/Android/sdk`, `~/Android/Sdk`, `/usr/lib/android-sdk`, Homebrew's cmdline-tools, the folder above an `adb` on the PATH), `cmdline_tool` `:2380`, `find_image` `:2387` |
| macOS text recognition ready | runs `ocr --warmup`, waiting at most 60 s; "slow to start" is a note, not a failure ([03](03-check-ocr-export.md#35-the-slow-first-run-anecompilerservice)) |

Extras: a warning when the only installed iOS runtime is on `BAD_IOS_RUNTIMES` (iOS 27.0); a note when Maestro is not one of `MAESTRO_TESTED` (`("2.0.10", "2.11.0")`, `:3915`); with a `[capture]` config in the current folder (`capture_mode` `:4190`) iOS needs Xcode but not Maestro or Java; one line "shotfleet X is out (you have Y): <update command>" read from `https://shotfleet.com/download/VERSION` (`latest_release` `:3864`, 5 s timeout; `update_command` `:4185` says `brew upgrade --cask noloman/tap/shotfleet` for a Homebrew install, else the `curl | sh` line).

Result and exit code: `iOS: ready/not ready   Android: ready/not ready`; returns 0 when at least one platform is ready, **2** when neither is, 1 only when a `--fix` step failed. An iOS-only buyer is shown which lines block their platform only.

### `doctor --fix`

Rules (comment at `:3946`, from `research/setup-friction.md`): never sudo, never edit PATH or shell rc files, never install Xcode; everything fetched goes into one folder (`~/.shotfleet`, or `$SHOTFLEET_HOME`) or the Android SDK folder, over HTTPS, checked against a checksum **before unpacking**.

`fix_plan` (`:4119`) builds a numbered list of `(description, function)`; `run_fix_plan` (`:4141`) prints it, asks once (`[y/N]`, or takes `--yes`; refuses without a terminal unless `--yes`), runs the steps in order and stops at the first failure, listing what was not done. Exit codes: 0 done, 1 a step failed, 2 nobody agreed.

| Step | What it does |
|---|---|
| Maestro | `install_maestro` `:4026`: downloads the pinned `MAESTRO_PIN` (`:3951`: version 2.11.0, size, GitHub release URL, SHA-256) to `~/.shotfleet/downloads`, verifies, unzips with `extract_zip_safely` `:4014` (refuses members that escape the folder; keeps unix permissions) into `~/.shotfleet/maestro` |
| Java | `install_jre` `:4046`: asks Adoptium's API for the Temurin 21 JRE for this OS/arch, takes the link and SHA-256 from its answer, unpacks with the `data` tar filter into `~/.shotfleet/jre` |
| Android command-line tools | on a Mac with Homebrew `brew install --cask android-commandlinetools`; otherwise `install_cmdline_tools` `:4089` downloads Google's archive (SHA-1 from Google's repository manifest, `android_cmdline_archive` `:4069`) into `<sdk>/cmdline-tools/latest` |
| Android SDK licences | `sdkmanager --licenses` fed `y` (the plan says it accepts them, with the URL) |
| SDK packages | `sdkmanager platform-tools emulator build-tools;36.0.0 <system image> cmdline-tools;latest` for whatever is missing. `sdkmanager_invocation` `:4110` routes installs through `android --no-metrics sdk install` when Google's newer shim program is present, because that tool otherwise reports usage data to Google and shotfleet promises nothing leaves the machine except what you ask for |

`MAESTRO_PIN` changes only after a real device run passed on the new version (see [08](08-testing.md) and [10](10-contributing.md)). The proxy case: corporate proxies that re-sign HTTPS need `SSL_CERT_FILE` (`tls_context` `:3998`).

## 4.2 `init`

`cmd_init(builds, dest)` (`:4657`) writes `shotfleet.toml` and `flow.yaml` (`FLOW_TEMPLATE` `:4298`: write the flow in English, tap and assert by visible text, no `appId`). It never overwrites: an existing file is kept, with a note on whether it already points at the given build (`keep_note` `:4646`). It never builds or runs anything.

With no build argument it finds the newest ones (`find_builds` `:4593`):

- iOS: the newest `Debug-iphonesimulator` `.app` in Xcode's DerivedData (`~/Library/Developer/Xcode/DerivedData`) whose `info.plist` `WorkspacePath` is this folder, up to two folders below, or above (`derived_apps` `:4417`; worktree copies are other copies; test runners and device builds are skipped, `simulator_app_time` `:4439`).
- Android: the newest Gradle debug APK under `build/outputs/apk/**/debug` here or one or two levels down (`gradle_apks` `:4447`), dropping Wear OS APKs when several exist (`is_watch_apk`).
- A recognised framework project (`detect_project` `:4538`: Flutter, Capacitor, Expo / React Native, .NET MAUI, Kotlin Multiplatform, Unity) changes where builds are looked for, which `strings` glob is written into the config, which build commands are suggested, and which hints are printed; these paths are the frameworks' documented defaults, "not checked on every version of each toolchain" (the code's own `ponytail:` comment). Native Swift or Kotlin apps return None.
- Nothing found: a `Fail` with the exact `xcodebuild` / `./gradlew assembleDebug` / framework command to run, and the KMP XCFramework hint where it applies (`KMP_XCFRAMEWORK_HINT` `:4589`).
- Archives (`.tar.gz`, `.tgz`, `.zip`, as Expo EAS hands over) are unpacked first into `.shotfleet/builds` (`unpack_build` `:4332`, members escaping the folder refused). Wrong files get a specific hint (`.ipa`, `.aab`, `.xcarchive`, device builds: `WRONG_BUILD`, `build_hint`).
- Paths inside the project are written relative to the config; a build outside it keeps its absolute (or `~`) path and `init` prints a one-line note that it is only valid on this Mac (`config_path` `:4380`).

`init --capture` (`cmd_init_capture` `:4731`) writes only a `[capture]` config, with the project's own shared scheme that tests a `*UITest*` bundle (`ui_test_scheme` `:4721`, read from the scheme files, never from `xcodebuild -list`, which resolves Swift packages and once wrote 2.4 GB into DerivedData).

## 4.3 The MCP server

`shotfleet mcp` (`cmd_mcp` `:5251`) is a Model Context Protocol server on stdin/stdout, JSON-RPC 2.0, one message per line. It implements exactly: `initialize` (answers with the client's `protocolVersion` if it is in `MCP_VERSIONS = ("2025-11-25", "2025-06-18")`, else the newest; the comment explains why not 2025-03-26, which requires JSON-RPC batches, nor 2026-07-28, which has no `initialize`), `tools/list`, `tools/call`, `ping`, and progress notifications. Notifications from the client are ignored; a batch is rejected with -32600; unknown methods get -32601. Install line: `claude mcp add shotfleet -- shotfleet mcp`.

Three tools (`MCP_TOOLS` `:5134`):

| Tool | Arguments | Behaviour | Annotations |
|---|---|---|---|
| `check` | `folder` (required), `app`, `strings` (list of globs), `report`, `full` | runs `check_any`; writes `check.json` and `index.html` into the report folder (default `./shotfleet-check` in the server's working folder, never inside the checked folder, or the run's own folder for shotfleet output); `ocr_command` is refused ("it runs a program") | `readOnlyHint: false`, `destructiveHint: true` (it replaces those two files), `idempotentHint: true` |
| `doctor` | none | `cmd_doctor()` with no `--fix`; asks shotfleet.com once for the version | `readOnlyHint: true`, `openWorldHint: true` |
| `run` | `config` (required), `locales`, `full`, `hooks` | `apply_free_tier()` then `cmd_run`; same free-tier cap as the CLI | `destructiveHint: true`, `idempotentHint: false`, `openWorldHint: true` |

**Safety gate for config commands.** A `shotfleet.toml` from a cloned repo can hold shell commands: `[hooks]`, `[capture] build`, `[ios] simctl`, `[android] shell`. Over MCP none of them runs unless the caller passes `hooks: true`. `mcp_call` (`:5200`) checks `config_commands` first and, without the opt-in, returns an error naming the commands; it sets `NO_HOOKS`/`CONFIG_COMMANDS` for the duration of the call and restores them in a `finally`; `refuse_config_commands` (`:1878`) is the last guard inside the run code, even if the first check missed one. (Added in 0.1.6 after a review found `[capture] build` ran anyway.)

**Mechanics.** Each call redirects stdout and stderr into a `StringIO` and returns it (or, for `check` and `run`, a summary built by `mcp_summary` `:5178`; see [01](01-runtime-architecture.md#18-output-files) for the shape). `mcp_call` resets `LAST_REPORT`, `FREE_TIER_NOTE` and `REPORTS` at the start of every call because the process is long-lived. If the client sent a `progressToken`, a daemon thread sends a `notifications/progress` carrying the last log line every `MCP_HEARTBEAT_S = 30` seconds (Claude Code drops a stdio call that is silent for 30 minutes). Any exception in a call is caught and returned as `isError: true` so one bad call cannot kill the server. `run` can take an hour or more; a client with a short timeout will give up on it.

**Adding an MCP tool.** Add the dict to `MCP_TOOLS` (with honest annotations), a branch in `mcp_call`, decide the licence and free-tier behaviour (call `apply_free_tier()` for anything that captures), add to the tests in `tests/test_shotfleet.py` / `tests/test_agent_skills.py`, the README "What the MCP tools do", and the skills.

## 4.4 Agent skills

`skill/` holds three skills, each a folder with a `SKILL.md` (frontmatter `name` and `description`, short body) and, for the main one, `references/` (`troubleshooting.md`, `flow-writing.md`, `config.md`, `ci.md`, `licence.md`):

| Skill | Use |
|---|---|
| `shotfleet` | the main skill: decision tree, commands, exit codes, `--json`, flow writing, references (`SKILL.md` under 200 lines, enforced by a test) |
| `shotfleet-ci` | add `shotfleet check` to GitHub Actions or another CI |
| `shotfleet-review` | read a check report and turn it into a fix list (its table of problem messages is checked against fragments in the program) |

`shotfleet skill install` (`cmd_skill` `:5043`) copies them out of the program (`sys._MEIPASS/skill` in a frozen build, `skill/` next to the source otherwise; PyInstaller includes them with `--add-data skill:skill`) into `~/.claude/skills` (Claude Code, Cursor) and `~/.agents/skills` (Codex, Gemini CLI, Copilot, Cursor). `--project` uses `./.claude/skills` and `./.agents/skills`; `--dir` one folder. Skills already there are kept unless `--force`. `docs/AGENTS-snippet.md` is a paste-in block for `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`. The skills and the snippet are tested by parsing every documented `shotfleet ...` command with the real argparse parser (`tests/test_agent_skills.py`), so a documented flag that does not exist fails the suite.

The skills are also published, separately, as the public repo `noloman/shotfleet-skills`: `tools/sync-public-skills.sh <checkout>` copies `skill/*` there, sets its plugin version to `VERSION` and prints the diff; it never commits or pushes (a human reads the diff and pushes).

## 4.5 External commands (plugins)

`main()` (`:5068`): if the first argument is not an option, not a built-in command, and `shotfleet-<arg>` exists on the PATH, the process is replaced (`os.execv`) by that program with the remaining arguments. This is the same mechanism as `git foo`. README "Extending shotfleet" documents it for buyers. The built-ins always win.

## 4.6 The Linux `check` image

`Dockerfile` builds `ghcr.io/noloman/shotfleet-check:<version>`: a PyInstaller one-folder build of the same program in a Debian slim image with Tesseract (a language list in `ARG LANGS`), `aapt` (for `--app app.apk`) and `jq`. It contains the compiled program, never `shotfleet.py`. `SHOTFLEET_IMAGE=check` makes `run` and `export` refuse. It has the same pinned, hash-checked build inputs as the Mac build (`packaging/requirements-build.txt`, Python 3.14.2) and, since 0.1.7, bakes its build date the same way (`build/_release.py`), so the "no usable release date" warning no longer prints on every start. `packaging/docker-check.sh` builds and pushes it. **Not published yet (as of this repo state):** `site/draft/docker-pending.txt` holds the site and `llms.txt` text about the image and the GitHub Action `noloman/shotfleet-check-action` back "until the Linux check image and the GitHub Action are published" (`packaging/README.md` step 9); a site test (`DockerPending` in `tests/test_site.py`) guards that, and a flag file `site/DOCKER_PUBLISHED` is to be added when they are. Packaging details: [06](06-packaging-and-release.md).
