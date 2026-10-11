# shotfleet engineering documentation

Written 2026-10-08 for engineers who know Python, shell and git, have heard of Maestro and fastlane, and know nothing about shotfleet, its business or its internals. After reading these files you should be able to build, change, test, release and support the product.

**Snapshot.** Branch `claude/app-launch-readiness-d770fd`; `main` is at `7e5176c`; `VERSION = "0.1.7"` in `shotfleet.py:28`. The live site (`shotfleet.com/download/VERSION`) served 0.1.6 when these docs were written; 0.1.7 is committed, built and notarized (2026-10-08, from `b41ac94`) but its device gate and publish step had not run. `origin/main` has moved on from this worktree (it holds at least `b41ac94`, `802e2fd` and `b5dd971`, which adds claims C281 to C287); this folder describes `7e5176c`, where the highest claim id is C280. The code has moved on since: the live version is 0.1.9 (2026-10-11), and 0.1.8 and 0.1.9 changed behaviour this folder does not describe (see `CHANGELOG.md`). `shotfleet.py` is 5,705 lines and 398,850 bytes. Every `shotfleet.py:LINE` anchor in this folder is for that commit. Line numbers drift with every edit; function and constant names are the stable handle (grep for the name). Where a fact could not be verified, the text says "not verified" and names the file that is the only source.

**Source of truth.** The code wins over any document, including this one. Older documents that overlap with this folder: [../ARCHITECTURE.md](../ARCHITECTURE.md) and [../architecture/](../architecture/01-code-layout.md) (written at 0.1.6, still useful, line anchors stale), [../handoff.md](../handoff.md), `STATUS.md`, `CHANGELOG.md`. Their stale statements are collected in [Documentation corrections](#documentation-corrections) below instead of being edited.

## Contents and reading order

| File | What is in it | Read it when |
|---|---|---|
| this file | the product on one page, the index, a glossary, documentation corrections | first |
| [01-runtime-architecture.md](01-runtime-architecture.md) | how `shotfleet.py` is organised; every command; config format; how a run flows end to end; output files and JSON shapes; conventions, exit codes, global state, environment variables | before touching any code |
| [02-capture-and-devices.md](02-capture-and-devices.md) | reading the app's strings; rewriting the flow per language; locale injection on iOS and Android; simulator and emulator pools; Maestro under watchdogs; capacity planner and overload advisor; retries and `--retry-failed`; locks; bring-your-own XCUITest capture | before touching `run` |
| [03-check-ocr-export.md](03-check-ocr-export.md) | `check` and its rules; the OCR stack (Swift helper, Vision, Tesseract) and the `ANECompilerService` slow-first-run issue; store rules; coverage matrix; `check --compare`; `export` and `--print-upload` | before touching `check` or `export` |
| [04-setup-mcp-skills.md](04-setup-mcp-skills.md) | `doctor` and `doctor --fix`; `init` and project detection; the MCP server; the agent skills; external-command plugins; the Linux Docker image | before touching setup or agent integration |
| [05-licence-and-money.md](05-licence-and-money.md) | how shotfleet is sold; Gumroad licence keys, activations, weekly re-check, offline grace, refunds, CI key, update window; known limits | before touching anything licence, pricing or refund related |
| [06-packaging-and-release.md](06-packaging-and-release.md) | standalone Python build, signing, notarization, the release gate, the claims register, `tools/check-claims.sh`, version bump checklist, release and rollback runbooks | before building or releasing |
| [07-website-and-backend.md](07-website-and-backend.md) | `site/`: pages, the Cloudflare Worker and KV, `install.sh`, CSP, analytics, deploy, domain and mail | before touching the site |
| [08-testing.md](08-testing.md) | test layers, every test module, fixture apps and device scripts, Maestro compatibility matrix, shared-Mac device protocol, KVM notes, flaky tests | before writing tests or running device jobs |
| [09-operations-and-support.md](09-operations-and-support.md) | support, refunds and key resets, the weekend watchdog, a troubleshooting table | when something breaks or a buyer writes |
| [10-contributing.md](10-contributing.md) | standing rules, claims discipline, branches and claim ids, recipes, what not to do, a first-week checklist | before your first change |
| [11-history-and-decisions.md](11-history-and-decisions.md) | timeline, decision log, incidents and lessons, known limitations, open work | to understand why things are as they are |
| [12-function-map.md](12-function-map.md) | every top-level function and class of `shotfleet.py` with line numbers (generated from the file) | as a lookup table |

Suggested orders:

- **New engineer, general**: this README, 01, 10, 11, then 02 and 03, then 05, 08.
- **Fixing a bug in `run`**: 01, 02, 08, 09 (troubleshooting table).
- **Fixing a bug in `check`**: 01, 03, 08.
- **Cutting a release**: 06, 08, 09, 05 (the licence checks in the gate), 07 (deploy).
- **Answering support**: 09, 05, `docs/refund-runbook.md`.
- **Working on the site or a claim**: 07, 10 (claims discipline), 06 (claims register).

## What shotfleet is, on one page

**Product.** A command-line program for macOS (Apple silicon, macOS 13 or later; `check` also runs on Linux) that produces and verifies localized App Store and Google Play screenshots. You write **one English [Maestro](https://maestro.mobile.dev) flow** (YAML that taps buttons by their visible text). shotfleet reads the translations compiled into your app build, rewrites every text selector in the flow into each language the app ships, boots N iOS simulators or Android emulators, runs one language per device in parallel, and then **checks every screenshot** against the app's own strings: wrong language, copies of another language's image, missing screens, blank frames, system dialogs over the app, and the stores' size, count and transparency rules. Screenshots that pass can be copied into fastlane's `deliver` and `supply` folder layouts with `export`. shotfleet never uploads to a store; fastlane does that.

**The problem it removes.** Localized screenshots are often the English set copied into every language folder, because the script that drives the app taps English buttons and cannot run in German or Japanese without a copy per language. Nobody checks the result, and Android and iOS need separate tooling.

**Who buys it.** Indie developers and small teams shipping a **native iOS and/or Android app in many languages (10 or more)** who already use fastlane or Maestro. Flutter, React Native, Expo, MAUI, Capacitor and Kotlin Multiplatform apps work when their translations can be found (build or source files). It is not for games (Unity draws its own UI) and not for people who want frames and captions (other tools do that; shotfleet only reads captions to explain a wrong-language verdict). Positioning and competitors: `STRATEGY.md`.

**How it is sold.** One Gumroad product. $49 once per developer, $29 for the first 100 buyers (the offer code `FOUNDER29`, applied automatically), a year of updates, a 14-day refund, before VAT or sales tax. Gumroad is the merchant of record. The buyer receives a licence key by email and runs `shotfleet activate <key>`. No account, no server of ours. Support is one person at `hello@shotfleet.com`. The program is closed source (private repo); the installable program is a signed, notarized build served from `shotfleet.com` (`curl -fsSL https://shotfleet.com/install.sh | sh`, a `.pkg`, or a Homebrew cask). The three agent skills are public. Live since 2026-10-05. Details: [05](05-licence-and-money.md).

**Free versus licensed.**

| | Without a key | With a key |
|---|---|---|
| `check`, `doctor`, `init`, `skill`, `mcp`, `activate`, `deactivate` | yes, always | yes |
| `run` | the first 2 languages (a cap per run, both platforms, every device size) | every language |
| `export` | refused | yes |
| versions | all that you have | every version released within a year of the purchase; later ones run as the free tier |

**How it works (the whole pipeline).**

```text
shotfleet.toml + flow.yaml + app build (.app or .apk)
  -> read the build's strings (or Flutter/RN/... translation files)        [02]
  -> languages the app really ships (not libraries' strings)               [02]
  -> translate_flow: English selectors -> that language's text             [02]
  -> language injection: iOS launch arguments in each flow;                [02]
     Android per-app locale on each emulator
  -> N devices, one Maestro process (--shard-split), one language each     [02]
  -> screenshots + the app's own screen text (texts.json)                  [02]
  -> check: app text > macOS Vision OCR > Tesseract; language, copies,     [03]
     missing, blank, dialogs, [expect], store rules, coverage matrix
  -> run.json, check.json, index.html
  -> export: only languages that passed -> fastlane deliver/supply folders [03]
```

**Technology.** Python 3.11+ standard library in a single file (`shotfleet.py`), one 56-line Swift helper (`ocr.swift`) around macOS Vision and NaturalLanguage, Maestro (a Java program, tested with 2.0.10 and 2.11.0) as the device driver, `xcrun simctl` / `xcodebuild` / `adb` / `emulator` / `aapt2` as tools. Packaging: PyInstaller one-folder build from a standalone Python, Developer ID signed, notarized. Website: static files plus one Cloudflare Worker with Workers KV. Tests: `unittest` and one Node file; the gate is `tools/check-claims.sh`, run locally.

**Repository map.**

| Path | What it is |
|---|---|
| `shotfleet.py`, `ocr.swift` | the program |
| `skill/` | three agent skills (`shotfleet`, `shotfleet-ci`, `shotfleet-review`), shipped inside the program |
| `packaging/` | build, sign, notarize, publish and go-live scripts, pinned build inputs |
| `tools/` | developer tools: fixture apps, device e2e scripts, release-candidate and verify scripts, upstream watchers, `check-claims.sh`, `status.sh` |
| `site/` | the website (`public/`), the Worker (`worker.js`), wrangler configs, tests |
| `tests/` | 51 `test_*.py` modules, `claims.json` (the claims register), `browser_site.cjs`, `fixtures/` |
| `docs/` | buyer-adjacent and internal docs (`compat.md`, `linux.md`, `refund-runbook.md`, `device-queue.md`, `handoff.md`, ...) and this folder |
| `research/` | dated research notes: the "why" behind decisions; `research/README.md` is the index |
| `marketing/` | launch material and article sources for the guides |
| `examples/crossfittracker/` | a real app's config and flows |
| `README.md`, `CHANGELOG.md`, `STATUS.md`, `PLAN.md`, `STRATEGY.md`, `ROADMAP.md`, `DISTRIBUTION.md`, `LAUNCH.md`, `TESTING.md`, `Dockerfile` | buyer README (tested), release notes (the release scripts read its top heading), project state, plans |

Outside the repo (the owner's Mac): `/Users/manu/Developer/shotfleet-rc-build/` is the durable folder for release builds, worktrees, logs, the release archive and the weekend watchdog (see [06](06-packaging-and-release.md) and [09](09-operations-and-support.md)).

## Glossary

| Term | Meaning |
|---|---|
| **Activation** | one count on a Gumroad key's lifetime `uses` counter, made by `shotfleet activate` on a Mac that did not already hold the key. A key allows 5 (`MAX_MACS`): "3 Macs and 2 spare for reinstalls". Not a count of Macs. [05](05-licence-and-money.md) |
| **ANECompilerService** | the root macOS service that compiles Vision's text-recognition model for the Neural Engine on first use; while it compiles, text recognition does not answer. The cause of "text recognition isn't answering". Not a hang; do not reboot. [03](03-check-ocr-export.md) |
| **App text / the app's own text** | the labels of the screen read from the running app (iOS: the Maestro driver's accessibility tree; Android: the hierarchy Maestro saves), stored as `<shot>.texts.json`. Exact, any script; `check` prefers it to OCR. In `check.json` it is `evidence: "hierarchy"` |
| **Base locale** | the language the flow is written in (default `en`); `base_locale` in the config |
| **Budget (OCR)** | the 480 seconds (`OCR_BUDGET_S`) that all of one `check`'s waiting on macOS text recognition shares |
| **BYOC** | bring your own capture: a `[capture]` table makes `run` build and run the team's XCUITest screenshot tests instead of a Maestro flow (iOS only) |
| **Capture** | everything up to the PNG files in `out/raw/<locale>/` |
| **Cask** | Homebrew's package type for proprietary binaries; `brew install noloman/tap/shotfleet` |
| **Claim / claims register / claim id** | a public promise and its proof: one row of `tests/claims.json`, id `C###`. Tests fail when the quoted words drift. [06](06-packaging-and-release.md), [10](10-contributing.md) |
| **Collision** | two different English labels that translate to the same word in one language, so a tap could hit the wrong element; reported before a run |
| **Coverage matrix** | the per-language by device-class table at the end of `check` (0.1.7): `ok`, `missing`, `too many`, `wrong size`, or `-` |
| **Device lock** | the `flock` on `/tmp/shotfleet-<key>.lock` inside the program that stops two shotfleet runs sharing devices. Not the same as the **device queue**, the human/agent convention in `docs/device-queue.md` (`mkdir /tmp/shotfleet-devices.lock`) |
| **Demo mode (Android)** | SystemUI demo mode applied to emulators: fixed clock 9:41, full battery and signal, no notifications |
| **Developer ID / hardened runtime / notarization / stapling** | Apple's signing identity for software outside the App Store; the runtime restrictions the notary requires; Apple's scan that must say "Accepted"; attaching the ticket to the package. [06](06-packaging-and-release.md) |
| **Evidence** | where a screenshot's text came from in `check.json` (`hierarchy` or `ocr`); also a claim status meaning "a dated record exists" |
| **Export** | copying passing languages into fastlane's `deliver` / `supply` folders; needs a licence |
| **Fail** | the exception class for user-facing errors; ends as one line `shotfleet: <message>` on stderr, exit 2 |
| **fastlane deliver / supply / snapshot / screengrab** | fastlane's App Store upload, Google Play upload, iOS screenshot (XCUITest) and Android screenshot (Espresso) tools. shotfleet's `export` writes the folders deliver and supply read; `check` accepts what snapshot and screengrab write |
| **Fixture app** | the small test apps in `tools/fixture-app` (iOS) and `tools/fixture-app-android` that the end-to-end device tests run against. [08](08-testing.md) |
| **Flow** | the Maestro YAML script |
| **Founder price** | $29 for the first 100 buyers via the Gumroad offer code `FOUNDER29` ($20 off, applied automatically); list price $49 |
| **Free tier** | `check` always; `run` capturing 2 languages without a valid licence |
| **Frozen** | a PyInstaller build (`sys.frozen` is true). The only place the licence is enforced; source runs are unlicensed |
| **Gate / G1 to G11** | the local pre-release checks numbered in `research/go-live-gate.md`: G1 final code and `tools/check-claims.sh`, G2 iOS fixture on both Maestros, **G3 device gate** (the signed release binary runs the fixture end to end on real simulators and emulators with a real licence), G4 artifacts built, G5 Gatekeeper accepts them, G6 licence against the real Gumroad API, G7 install paths, G8 real apps, G9 staging rehearsal, **G10 production smoke** (`tools/golive/smoke.sh` right after the deploy), G11 rollback written. [06](06-packaging-and-release.md) |
| **Go-live** | the one-time switch on 2026-10-05 from a waitlist page to a sale page (`packaging/go-live.sh`: set the Gumroad product id, transform the page, deploy). Later releases use build, gate and `packaging/publish.sh` |
| **Gumroad** | the store and merchant of record. Key facts: product id (public, `GUMROAD_PRODUCT_ID`), licence key shape (four groups of 8 hex characters), `uses` counter, refunds disable the key |
| **Hierarchy marker** | the optional, always-warning `assertTrue` step after each Android `takeScreenshot` that makes Maestro 2.7.0+ save the screen hierarchy |
| **Hook** | a user command in `[hooks]` (`before_run`, `after_run`, `before_export`, `after_export`), run by `/bin/sh` in the config's folder |
| **Infra error** | a failed language whose error looks like the device or Maestro broke (`INFRA_ERRORS`); only these are retried automatically (0.1.7) |
| **KvK** | the Dutch Chamber of Commerce registration. Polar and Lemon Squeezy end in a Stripe check that asks for it; the owner has none, so Gumroad was chosen |
| **KV (Workers KV)** | Cloudflare's key-value store used by the Worker (binding `WAITLIST`): visit counts and contact messages. [07](07-website-and-backend.md) |
| **lproj / locale** | a language code as the app spells it (`de`, `pt-BR`, `zh-Hans`); `.lproj` is the iOS folder; `canon()` normalises spellings |
| **Maestro** | the open-source mobile UI test runner shotfleet drives; a Java program (Java 17+). `--shard-split` runs several devices from one process. **Tested** versions: 2.0.10 and 2.11.0 |
| **MAESTRO_TESTED / PIN / BAD** | the tested pair; the version `doctor --fix` installs (2.11.0, checksum pinned); the deny list (empty: a version goes there only with a reproduced failure) |
| **Manifest** | the file `publish.sh --make-manifest` writes with the version and the SHA-256 of the tested tarball and package; `publish.sh` refuses files that do not match it |
| **MCP** | Model Context Protocol; `shotfleet mcp` is a server with tools `check`, `run`, `doctor`. [04](04-setup-mcp-skills.md) |
| **minos** | a Mach-O file's minimum macOS version, read by `tools/macho-minos.py`; the declared minimum of the build is macOS 13 |
| **Not verified / unverified** | a screenshot nobody could read because macOS text recognition was busy and no other reader existed; listed in `check.json` `unverified`, not a failure unless `--strict`. In these docs, "not verified" also marks a statement that could not be checked |
| **Notary profile** | the `notarytool` keychain profile (`ShotfleetNotary`); it only works while the Mac's screen is unlocked ("No Keychain password item found" means locked, not lost) |
| **OCR / Vision / Tesseract** | optical text recognition: Apple Vision on a Mac (through `ocr.swift`), Tesseract elsewhere or as a fallback |
| **Override / inputs / expect** | config tables: `[overrides.<locale>]` (what to tap for an English text), `[inputs]` (text to type per language), `[expect.<shot>]` (texts that must or must not be on a screen) |
| **Plugin (external command)** | `shotfleet foo` runs `shotfleet-foo` from the PATH |
| **Pool** | the simulators named `shotfleet-<device>-N` or the emulators on ports 5702, 5704, ... that a run uses |
| **ponytail** | a code comment prefix marking a deliberate shortcut and its ceiling |
| **Problem / note** | a failing line versus an informational line in `check.json` |
| **RC build / `shotfleet-rc-build`** | "release candidate". `tools/release-candidate.sh` builds a signed-style test build with a TEST Gumroad product id (starting `RCTEST`) and runs the licence through it against a fake server. The folder `/Users/manu/Developer/shotfleet-rc-build/` is the durable working area for release work (per-version folders, worktrees, logs, the release archive); it is outside the repo and survives reboots, unlike `/tmp` |
| **Release archive / release dir** | `SHOTFLEET_RELEASE_DIR`: a durable folder with `archive/<version>/` (the shipped bytes) and `state/` (rollback records) used by `publish.sh` |
| **Retry** | one automatic second attempt of languages that failed with an infra error; `run --retry-failed` reruns the languages that failed in `run.json` |
| **Rollback id / Cloudflare version** | the id of the live Worker/asset version recorded before a deploy; `wrangler rollback <id>` returns to it |
| **Round (Android)** | one pass in which each emulator captures one language |
| **Shard** | Maestro's way (`--shard-split`) to spread flows over several devices from one process; it hands any flow to any device |
| **Shipped locales** | the languages the app itself translates, excluding libraries' (`shipped_locales`) |
| **Skill** | an agent skill (`SKILL.md` plus references) that tells an AI coding agent how to use shotfleet |
| **Smoke test** | `tools/golive/smoke.sh`: read-only checks of the live site and release right after a deploy (G10) |
| **Snapshot (emulator)** | the saved `shotfleet` boot state read-only emulator copies start from |
| **SnapshotHelper** | fastlane's Swift helper that writes screenshots to `~/Library/Caches/tools.fastlane/screenshots` |
| **Stall watchdog** | kills Maestro when no new screenshot appears for `stall_s` seconds (default 900) |
| **Store code** | a listing folder name used by fastlane (`de-DE`, `zh-Hans`, `es-419`) |
| **Table** | in `check`, a locale's normalised strings plus one regex for its format strings |
| **texts.json** | `<shot>.texts.json`, the app's own text for one screenshot |
| **Twins** | language pairs detection cannot separate (`ms`/`id`, `hr`/`sl`) |
| **Update window** | "a year of updates", enforced: a build covers a purchase when its baked-in release date is on or before the same calendar date a year after Gumroad's sale date |
| **Versioned downloads** | permanent, immutable `https://shotfleet.com/download/<version>/` files |
| **Waitlist** | the pre-sale landing page; its code remnants are still in the repo (dead routes and KV keys, [07](07-website-and-backend.md)) |
| **Weekend watchdog** | the owner's launchd job that probes the live sale and install path every 30 minutes. [09](09-operations-and-support.md) |
| **Worktree** | a `git worktree` checkout. Every agent session works in its own; release work lives under `shotfleet-rc-build/`, not `/tmp` |
| **XCUITest / xctestrun** | Apple's UI test framework / the file describing a prebuilt test run |

## Not verified (summary)

Each chapter ends with, or contains, its own list; the main open points:

- **Never run for this task (by instruction):** any simulator, emulator or device job, `publish.sh`, `wrangler`, GitHub Actions, notarization. Everything about device behaviour is from reading the code and the dated records in `research/` and `STATUS.md`. [08 section 8.20](08-testing.md#820-not-verified) lists what the testing author could not check; [06 section 6.16](06-packaging-and-release.md#616-not-verified) and the last section of [07](07-website-and-backend.md) do the same.
- **Money path:** a refunded real key being refused has never been proven against a real paid sale ([05 section 5.7](05-licence-and-money.md#57-how-a-refund-reaches-the-program)).
- **External state:** Cloudflare, DNS and Email Routing settings, GA4 admin settings, whether the Docker image is on ghcr.io, the Homebrew tap and the public skills repo. They are described from repo files only.
- **Provisional numbers:** the capacity planner and overload thresholds, the emulator "2 cores and 3 GB" figure and `OCR_STUCK_CPU_MIN` are labelled provisional or INFERENCE in the code comments.
- **Live version:** `0.1.6` is taken from the weekend watchdog's log of 2026-10-08 06:45 and the release archive's state records, not from a fresh fetch.
- **A stray file:** `docs/weekend-support.md` was present as an untracked file in this working tree while these docs were written (written by another session, not by this task); it is not part of the commit that adds `docs/engineering/`.

## Documentation corrections

Statements in existing documents that are stale or wrong against the code at `7e5176c`. They were found while writing this folder and are **not** fixed in place (documentation-only task; the owner reviews). Severity: low unless marked. The code wins in every case.

**Fixed on branch `claude/018-docs` (2026-10-08):** rows 3 and 27 (the CHANGELOG 0.1.5 line and `docs/linux.md` now say the image and the Action are built, not published), row 5 (`docs/ARCHITECTURE.md` and `docs/architecture/*` no longer quote line numbers; the function map has them), row 13 and the first part of row 34 (`STATUS.md`, `docs/handoff.md` and `LAUNCH.md` point to the CHANGELOG instead of naming versions) and the 0.1.7 row of row 24 (`docs/compat.md`). The other rows are still open. The tables below are left as written.

### Found in the program's own text and the buyer docs

| # | Where | Says | The code does |
|---|---|---|---|
| 1 | `README.md:27`, `site/public/docs.html:249`, `skill/shotfleet/references/troubleshooting.md:121`, comments at `shotfleet.py:4579` and `:4962-4965` | a blank screenshot makes `run` "capture that language again once, then report it" | since 0.1.7 only infrastructure failures are retried (`INFRA_ERRORS`, `shotfleet.py:1658`); a blank-screenshot error is not one, so the language is reported without a second try. Verified by calling `is_infra_error` on the real `blank_note` text (False). **Medium**: public text and a tested skill table promise a retry that does not happen |
| 2 | `shotfleet.py:4-8` (module docstring) | lists five commands | `COMMANDS` (`:5041`) has nine: also `mcp`, `skill`, `activate`, `deactivate` |
| 3 | `CHANGELOG.md` 0.1.5 (the Docker bullet) | `ghcr.io/noloman/shotfleet-check` and the Action `noloman/shotfleet-check-action` are described as shipped | the image and the Action are built, but public pages hold their text back (`site/draft/docker-pending.txt`, `site/DOCKER_PUBLISHED` absent, test `DockerPending`); whether the image is actually pushed to ghcr is **not verified** |
| 4 | `Dockerfile` header | example `--build-arg VERSION=0.1.4` | `packaging/docker-check.sh` defaults the tag to `VERSION` in `shotfleet.py`; the comment is only an example |

### `docs/ARCHITECTURE.md` and `docs/architecture/*` (written at 0.1.6, `285e099`)

| # | Where | Says | Now |
|---|---|---|---|
| 5 | all `shotfleet.py:LINE` anchors, "5,143 lines, about 347 KB" (`01-code-layout.md`), "5,400 lines" | numbers for 0.1.6 | 5,705 lines, 398,850 bytes; every anchor has shifted by up to about 560 lines (for example `cmd_check` `:3329` is now `:3572`, `COMMANDS` `:4745` is now `:5041`). Use [12-function-map.md](12-function-map.md) |
| 6 | `ARCHITECTURE.md` and `02-capture.md`/`03-check.md`/`04-export-and-store-rules.md` | no mention of 0.1.7 features | missing: store coverage matrix (`coverage_matrix`), `check --compare`, `export --print-upload`, `run --retry-failed`, infra-only retry (`is_infra_error`), `BAD_IOS_RUNTIMES` (iOS 27.0 skipped), the overload advisor (`busy_warn`), bounded `simctl list/create/delete` calls (`simctl_sh`), MCP `note` for the free tier. Covered in [02](02-capture-and-devices.md), [03](03-check-ocr-export.md) |
| 7 | `architecture/13-mismatches.md` row 9 | export hooks see an empty `SHOTFLEET_PLATFORM` on iOS runs | fixed in 0.1.7: `ios_run_inner` writes `report["platform"] = "ios"` (`shotfleet.py:2205`) |
| 8 | `architecture/13-mismatches.md` row 20 | the Linux build and the Docker image do not bake a release date and warn on every start | fixed in 0.1.7 (CHANGELOG): the `Dockerfile` writes `build/_release.py` |
| 9 | `architecture/13-mismatches.md` row 10 and `architecture/08-website.md` | the worker serves `POST /api/signup`; alert email via `send_email`/`ALERT_TO` | removed on 2026-10-07 (`6443039`): `site/worker.js` routes are `/api/hit`, `/api/contact`, `/api/forget` only; the signup code left in `site/public/forms.js` and `ga.js` is dead. See [07](07-website-and-backend.md) |
| 10 | `architecture/13-mismatches.md` row 4 | "1,184 tests plus 59 worker checks" | on 2026-10-08 `sh tools/check-claims.sh` at `7e5176c` (plus these docs) printed `check-claims: ok (python: Ran 1244 tests in 70s OK (skipped=20) ; worker: 37 checks ok)`, exit 0 |
| 11 | `architecture/05-licensing.md` | the release-candidate result "92 checks for the 0.1.5 run" | 92 of 92 is the first full run of 2026-10-02 (`research/release-candidate.md`); later runs have more checks |
| 12 | `architecture/11-security-and-privacy.md` | `latest_release` at `shotfleet.py:3603` | `:3864` |

### Project state documents

| # | Where | Says | Now |
|---|---|---|---|
| 13 | `STATUS.md`, `docs/handoff.md` (section 17 is the last state section) | state through the 0.1.4 build; header says 0.1.6 "at the time of writing" | 0.1.7 is committed and awaiting its release build; there are no "state after" sections for 0.1.5 to 0.1.7 (history is in `CHANGELOG.md` and `shotfleet-rc-build/<version>/`) |
| 14 | `STATUS.md` gate 8 | doctor "needs Maestro 2.x (`shotfleet.py:1875`)" | `doctor` shows `MAESTRO_TESTED` and `doctor --fix` installs 2.11.0; line 1875 is in `config_commands` |
| 15 | `STATUS.md` (Gumroad bullet) | "licence-key block with 3 activations per key" | the program enforces `MAX_MACS = 5` (`shotfleet.py:5289`); Gumroad itself only stores the counter. Terms, site and README say "3 Macs, spare activations for reinstalls" |
| 16 | `STATUS.md` risk R6 and gate 11 | 131 claims, "47 not green" | `tests/claims.json` has 273 rows (proven 120, evidence 103, fixed 22, partial 20, removed 3, policy 3, unverifiable 2) |
| 17 | `PLAN.md` ("Phase 1b") | docs checked by `tests/test_docs_vs_code.py` | that file does not exist; docs and site are checked by `tests/test_docs.py`, `test_handoff_docs.py`, `test_screenshot_mode_doc.py`, `test_site.py`, `test_claims*.py`, `test_cli_claims.py` |
| 18 | `marketing/kit/directories.md:141` | "follow what CONTRIBUTING.md says" | there is no `CONTRIBUTING.md` in the repo; see [10](10-contributing.md) |
| 19 | `docs/handoff.md` and `STATUS.md` | cite `shotfleet.py` line numbers and "waiting" branches as current | lines drift; several `claude/015-*` branches listed as waiting are merged |

### Found while writing the testing and website chapters

Full tables are in [08 section 8.19](08-testing.md#819-differences-from-docsarchitecture09-testingmd-and-other-existing-docs) and the last sections of [07](07-website-and-backend.md) and [06](06-packaging-and-release.md); the main items:

| # | Where | Says | Now |
|---|---|---|---|
| 20 | `docs/architecture/09-testing.md` | 49 modules, 1,173 tests; Android fixture is 29 assertions | 51 modules and 1,230 `def test_` at `7e5176c` (the gate run reported 1,244 tests; the difference from the static count is not investigated); Android is 30 when hierarchy markers are recorded (Maestro 2.7.0+). The 161 s / 197 s timings it quotes appear in no file (not verified) |
| 21 | `tools/fixture-app/README.md` | "Android is skipped: there is no Android fixture yet" | `tools/fixture-app-android/` exists; `tools/fixture-e2e.sh --android` runs it |
| 22 | `docs/linux.md` lines 14, 55-58, 97, 128-132 | Android `run` on Linux "never run" / "untried"; "do not run E1 again" | it passed with one emulator on a 2-core runner (`docs/linux.md:101-126`, `docs/handoff.md:68`); two emulators need 4 or more cores. `docs/agent-tasks/README.md` row 05 and `05-e1-android-on-linux-kvm.md` "Context" repeat the old state |
| 23 | `docs/agent-tasks/01-maestro-2-11.md` | `MAESTRO_TESTED` "is still `("2.0.10",)`" | `("2.0.10", "2.11.0")` since 2026-10-04 |
| 24 | `docs/compat.md` | Python 3.14.0rc2 is the latest tested; iOS 27 line has no mention of the 2026-10-07 boot freezes or of the 0.1.7 default skip of 27.0; no 0.1.7 row; says a unit test fails if the Maestro interface list stops matching `shotfleet.py` | 3.14.8 runs on the dev Mac; `BAD_IOS_RUNTIMES` (`shotfleet.py:4764`); the test checks one direction only (`tests/test_maestro_compat.py:85-89`) |
| 25 | `docs/handoff.md:53-61` (Maestro promotion checklist) | a short list of files to update | also `docs/compat.md`, `docs/linux.md:69`, `tests/test_claims_site.py:75-76`, `tests/test_handoff_docs.py:23-25` and four claim rows that quote the pair (see [08 section 8.12](08-testing.md#812-the-maestro-compatibility-matrix)) |
| 26 | `docs/device-queue.md` | quiet check: free memory 20%, load under 300 | later rules are stricter (memory pressure level 1, no busy Gradle daemon, swap not growing; [08 section 8.13](08-testing.md#813-the-device-queue-and-the-two-locks)); it does not mention the program's own `flock` |
| 27 | `docs/linux.md:5` | the `ghcr.io/noloman/shotfleet-check` image is described as existing | public pages hold it back (`site/DOCKER_PUBLISHED` absent); whether it was pushed is not verified |
| 28 | `.github/workflows/e1-android-kvm.yml` header | "five runs" | `docs/linux.md` records six in the first series plus seven in the second |
| 29 | `docs/architecture/08-website.md` | DOCKER-PENDING markers in `docs.html` and `llms.txt`, CLIP markers in `demo.html`, a test forbidding `<!--` in all public pages, 250 claim rows | the held-back text is in `site/draft/docker-pending.txt`; no CLIP markers remain; only `docs.html` is tested for comments; 273 rows |
| 30 | `research/ga-setup.md` | names Polar (lines 44, 53, 79); expects a `signup` event; recommends 14-month event retention | Polar is gone; the signup event can no longer fire; the 2026-10-05 investigation found 2 months set (`research/ga4-investigation-2026-10-05.md`) |
| 31 | comments in `site/signups.sh` (header), `site/public/forms.js` (line 1), `site/tools/og.swift` | waitlist wording; writes `og.png` | no signup form or route exists; the site serves `og.jpg`; how it is produced today is not documented |

### Found while writing the packaging chapter

Full table: [06 section 6.15](06-packaging-and-release.md#615-differences-from-docsarchitecture07-packaging-and-releasemd-and-other-existing-docs).

| # | Where | Says | Now |
|---|---|---|---|
| 32 | `docs/architecture/07-packaging-and-release.md` | `publish.sh` verifies the `immutable` header; `fixture-e2e.sh` "has a hard limit"; gate runs take "about 37 to 55 minutes" | `publish.sh` only warns about it (`:305-306`); `fixture-e2e.sh` has no hard limit (the per-release waiter outside the repo does); 0.1.6's passing re-run took 24 min 58 s |
| 33 | the same lead, and `docs/architecture/10-making-changes.md` | between releases the CHANGELOG heading is `## X.Y.Z (<!-- RELEASE_DATE -->)` | between releases it is `## Unreleased` (invisible to the version-consistency regex); `publish.sh:144` still refuses the placeholder form |
| 34 | `STATUS.md` ("How to release again"), `LAUNCH.md:3` | `go-live.sh` was the 0.1.0 and 0.1.1 way; sections 4 to 6 of LAUNCH.md are the template for the next release | `release.sh` was used once, by `go-live.sh`; 0.1.1 was published by hand; 0.1.2 onward use build, gate and `packaging/publish.sh`. 0.1.5 and 0.1.6 are published (`shotfleet-rc-build/release-archive/state/published-*`), not "waiting" |
| 35 | `tools/status.sh:3`, `docs/architecture/13-mismatches.md` row 4 | the tests take about 30 s / 15 s | `tools/check-claims.sh` took 51 to 69 s on 2026-10-07 (`TESTING.md:3`) |
| 36 | `tools/release-candidate.sh:3` | "roadmap gates 5 and 6" | rows 5 and 6 of `STATUS.md`'s 16-row table, not G5 and G6 of `research/go-live-gate.md`. Three gate numbering schemes exist ([06 section 6.5.0](06-packaging-and-release.md#650-which-gate-three-numbering-schemes)) |
| 37 | `packaging/entitlements.plist:4`, `packaging/build.sh:51-52` | comments about a one-file build and Homebrew's Python framework | the product is a one-folder build from a standalone Python; the comments are leftovers |
| 38 | `DISTRIBUTION.md` table | the tap `noloman/homebrew-shotfleet` | `noloman/homebrew-tap` (its own Status section says so) |
| 39 | `docs/weekend-support.md:38` | "live is 0.1.6" | true now; stale the day 0.1.7 is published (also `EXPECT_VERSION` in `watch.sh`) |
| 40 | version bump | `site/public/index.html` "New in X.Y.Z" section | no test or script checks it (06 section 6.11, row 6): it can lag silently |

### Operations note (not a documentation error)

The weekend watchdog (outside the repo) expects live version `0.1.6` by default (`EXPECT_VERSION` in `watch.sh`); it will report a problem when 0.1.7 is published unless that default is changed ([09](09-operations-and-support.md)).
