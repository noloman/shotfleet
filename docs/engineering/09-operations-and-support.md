# 9. Operations and support

Scope: how to run the business side as an engineer once shotfleet is on sale: who answers support, where refunds, key resets and chargebacks are handled, how to see whether the live site and the install path are healthy, what the weekend watchdog probes, and a troubleshooting table for the four things that go wrong most (install, text recognition, device overload, licence checks). Nothing here changes any account; every Gumroad or Cloudflare action named is the owner's to take.

**Who is allowed to do what.** The owner (Manu) is the only person with the Gumroad, Cloudflare, Apple Developer and GitHub accounts. An engineer or agent reads, diagnoses and drafts; it does not refund, reset a key, deploy, publish or post unless the owner approves that exact action (see [10](10-contributing.md)). Never paste a licence key, a buyer's email address or a card detail into a chat, an issue or the repo.

## 9.1 Support

- **Channel.** `hello@shotfleet.com`. Mail to that address is forwarded by Cloudflare Email Routing to the owner's own inbox (`site/public/privacy.html`; `STATUS.md` gate 13 records that forwarding was verified and suggests a test mail once a month). One person answers. Replies go out within two business days (the promise in the refund runbook; Gumroad may refund by itself after 30 days of silence).
- **Gumroad receipt replies** reach the support email set in Gumroad Settings; the runbook asks to check that it is `hello@shotfleet.com` or forwards there (unverified).
- **What buyers write about** and where the answer is:

| Request | Handling | Where |
|---|---|---|
| Refund inside 14 days | Gumroad, Sales, the sale, Refund fully; reply with template A | [../refund-runbook.md](../refund-runbook.md) sections 1 to 3 |
| Refund after 14 days | The site's promise does not cover it; ask what failed, refund up to about 30 days if unfixable | runbook section 7 |
| Key rejected or "used all 5 activations" | In Sales, Manage license keys, reset Uses (to 0, or to the number of Macs still in use); the buyer runs `shotfleet activate KEY` again | runbook section 5; [05](05-licence-and-money.md) |
| "I lost my key" | The key is in the Gumroad receipt email; check spam; the buyer can use Gumroad's "Get your download link" or the owner resends the receipt from Sales (unverified) | runbook, `docs/weekend-support.md` (see the note below) |
| Chargeback or dispute | Reply in Gumroad within 72 hours (120 if a weekend falls inside); do not also refund without asking Gumroad support | runbook section 6 |
| Leaked key | Disable the key in Manage license keys (every Mac and CI run is refused at its next check); give the real owner a new sale or code | runbook section 5 |
| Free licence for a maintainer or student | A 100%-off Gumroad code (a $0 sale has no refund button) | `docs/weekend-support.md` |
| "It does not install / run" | Ask for `shotfleet --version`, `shotfleet doctor` output and the failing command; use the table in 9.4 | below |

- **Never**: refund from Stripe or PayPal directly (Gumroad does not support it); buy shotfleet with your own card (Gumroad treats it as card testing and can suspend the account); delete or recreate the Gumroad product (every key would answer 404 and every Mac would lock within a week).
- **What to record for the accountant**: runbook section 8 lists one line per refund and the exports to keep.
- A support sheet written for the launch weekend, `docs/weekend-support.md`, existed as an untracked file in this working tree when this chapter was written (not part of the commit that adds these docs); check `git log -- docs/weekend-support.md` before relying on it.

## 9.2 Is the product up? Read-only checks an engineer can run

None of these changes anything. They are what the owner's watchdog runs (9.3) and what the post-deploy smoke test runs.

```bash
curl -s https://shotfleet.com/download/VERSION                       # the live version; compare with CHANGELOG.md top heading
curl -sI https://shotfleet.com/install.sh | head -1                  # 200
cd <repo> && sh tools/golive/smoke.sh https://shotfleet.com          # about 36 checks in recent runs, on the live site and release; read-only, installs nothing
sh tools/golive/storefront.sh <the Gumroad product URL>              # published, licence keys on, product id matches, $49 list, 14-day refund
tools/status.sh --quick                                              # the numbers STATUS.md quotes, from the repo and the live site, no tests
env -i HOME=$(mktemp -d) PATH=/usr/bin:/bin <installed shotfleet> --version   # clean-environment start; catches import-time crashes
```

The `env -i` check is not optional after a release: a `NameError` at import crashed `shotfleet --version` on a Mac with no Android SDK (fixed before 0.1.0 shipped, PR #42) and was found only by running the post-deploy smoke against a staging copy that way (`STATUS.md`, "Bugs the release gate caught").

Release mechanics (publish, rollback, the Cloudflare version ids) are in [06](06-packaging-and-release.md); the site and worker in [07](07-website-and-backend.md).

## 9.3 The weekend watchdog

A launchd job on the owner's Mac, **outside the repository** (so it is not versioned and a new machine will not have it):

| Item | Value |
|---|---|
| Script | `/Users/manu/Developer/shotfleet-rc-build/weekend-watch/watch.sh` (POSIX sh, 2 KB) |
| Scheduler | `~/Library/LaunchAgents/com.shotfleet.weekendwatch.plist`, label `com.shotfleet.weekendwatch`, `StartInterval` 1800 s (every 30 minutes), `RunAtLoad` |
| Log and state | `watch.log` (one line per run: `ok` or `FAIL; ...`), `state` (the last failure text, used to avoid repeating a notification), `launchd.err`, all in the same folder |
| Notification | `osascript` macOS notification titled "shotfleet watch: PROBLEM" on a **new** failure, and "recovered" when probes pass again; nothing is sent over a network |
| Stop | `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.shotfleet.weekendwatch.plist` |

What it probes (all read-only; the timeouts are 25 s, 120 s for the download):

1. `https://shotfleet.com` paths `/`, `/install.sh`, `/terms`, `/privacy`, `/download/VERSION` each return HTTP 200.
2. The live version (`/download/VERSION`) equals `EXPECT_VERSION`. **The default in the script is `0.1.6`**; the variable can override it. When the next version goes live the owner (or whoever promotes it) must change that default, or the watchdog reports a problem for a healthy release. (The log shows a test run on 2026-10-08 with `9.9.9` as the expected value, which is how the failure path was exercised.)
3. The download `shotfleet-macos-arm64.tar.gz` is fetched and its SHA-256 equals the published `.sha256` file.
4. The Gumroad product page still contains `"price":49` (catches unpublish or a price change).
5. The Gumroad licence API answers a made-up key with the JSON "does not exist" message, sent with `increment_uses_count=false` so it never counts an activation. This proves the licence endpoint is reachable and the product id is accepted.

It does not log in anywhere, does not check Cloudflare's dashboard, and does not run the program. A green watchdog therefore says "the storefront, the installer path and the licence API answer", not "the program works".

## 9.4 Troubleshooting table

Start with `shotfleet --version` and `shotfleet doctor`. Errors that stop a command print `shotfleet: <message>` on stderr and exit 2; the message names the fix. `skill/shotfleet/references/troubleshooting.md` is a tested table of message fragments (a test requires every fragment to exist in the program); this table is the engineer-level view with where to look.

### Install and first run

| Symptom | Likely cause | Look at | Fix or answer |
|---|---|---|---|
| `shotfleet runs on macOS only` / `needs an Apple silicon Mac` | Linux, or an Intel Mac | `site/public/install.sh` lines 5-6 | Not supported; offer the refund. `check` runs on Linux via the Docker image only once that image is published ([04](04-setup-mcp-skills.md#46-the-linux-check-image)) |
| `download is corrupt (checksum mismatch)` | truncated download, a proxy rewriting bytes, or a bad publish | the watchdog's probe 3; `tools/golive/smoke.sh` | Retry; if it repeats on several networks, alert the owner (a bad publish: roll back, [06](06-packaging-and-release.md)) |
| `shotfleet: command not found` after install | the link folder is not on PATH | the installer prints the exact `export PATH` line | open a new Terminal window after adding it |
| "Apple could not verify ..." (Gatekeeper) on a browser-downloaded copy | the quarantine flag on a download; `curl \| sh` sets none | README Quickstart (pkg paragraph) | use the `curl` line or the signed, notarized `.pkg`; an unnotarized build would hang then be killed (`STATUS.md` gate 6) |
| macOS older than 13 | not supported | `tools/macho-minos.py` output in the release folder | refund |
| `doctor` shows MISSING emulator / avdmanager / aapt2 / system image | Android SDK pieces | the `sdkmanager` lines `doctor` prints | iOS-only users can ignore; otherwise `shotfleet doctor --fix` |
| `Maestro isn't installed` | no Maestro | `maestro_cmd` order in [04](04-setup-mcp-skills.md#41-doctor) | `shotfleet doctor --fix` (installs the pinned 2.11.0) |
| a run behaves differently on a machine with an iOS 27 runtime | the newest runtime is the default | `BAD_IOS_RUNTIMES`, [02](02-capture-and-devices.md#24-devices) | 0.1.7 prefers another runtime when iOS 27.0 is not the only one; live 0.1.6 does not: pin `runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"` |

### Text recognition stuck or "not verified"

| Symptom | Likely cause | Look at | Fix or answer |
|---|---|---|---|
| `doctor` prints `note: text recognition: slow to start`; `check` says "macOS is preparing its text recognition" | the first compile of Vision's model by `ANECompilerService` (30 s on a quiet Mac, minutes on a busy one, once about 40 minutes) | `ps aux \| grep ANECompiler` (CPU use), [03](03-check-ocr-export.md#35-the-slow-first-run-anecompilerservice) | wait and run again; **do not reboot**; install Tesseract for a fallback (`brew install tesseract`) |
| `N screenshot(s) not verified, because macOS text recognition was busy` | the check's 8-minute budget ran out and no other reader exists | the `unverified` list in `check.json`; the NOT VERIFIED block in `index.html` | run `check` again later (the compile result is cached), or `--strict` to make it fail CI; exit code 0 otherwise |
| `ANECompilerService ... has used N hours of CPU and looks stuck` | a service above `OCR_STUCK_CPU_MIN` (120 min), an inference-based threshold | `ane_state` in the code; `research/workarounds-text-recognition-2026-10-05.md` | Tesseract fallback; if truly stuck the service is root's, so an owner decision |
| `another shotfleet is preparing macOS text recognition; waiting` | two checks warming up at once | `/tmp/shotfleet-ocr-warmup.lock` | nothing; they take turns and the wait counts against the budget |
| a language Vision cannot read (Hebrew, Greek, Georgian, Indic) is only partly checked | Vision has no model | `readable_languages`; note lines in `check.json` | install Tesseract with that language data; those screens are otherwise checked for copies and missing screens only |

### Device overload, hangs and failed languages

| Symptom | Likely cause | Look at | Fix or answer |
|---|---|---|---|
| `warning: this Mac is very busy (swap is 90% full; ...); simulators may stop answering` | the overload advisor | [02](02-capture-and-devices.md#26-the-capacity-planner-and-the-overload-advisor) | close Xcode, Android Studio, other simulators; `./gradlew --stop`; rerun with `--parallel` half as many; `capacity = "off"` silences it |
| `simctl <cmd> did not answer within N s` / `no simulator answers any more` | CoreSimulator wedged under load | `~/.shotfleet/hung-simulators/`, the message's own `xcrun simctl shutdown <udid>` | shut down shotfleet's simulators (yours stay untouched), rerun; the next run replaces the ones that stopped answering |
| `failed flows with 'Unknown error' or 'Unable to clear state'` | a slow simulator, not the app | `out/maestro1.log`; the overload note | `shotfleet run <config> --retry-failed` after freeing memory |
| `maestro made no new screenshot for 900 s and was stopped` | hung simulator or flow (stall watchdog) | `out/.work/debug/`, `maestro1.log` | usually load; raise `stall_s` only if a flow really takes longer between screenshots |
| `another shotfleet run is using these devices` | the `flock` is held | `/tmp/shotfleet-ios-shotfleet.lock` (or `-ios-shotfleet-<device-slug>.lock`), `/tmp/shotfleet-android-emulators.lock` (holder pid inside) | wait or stop the other run; the OS drops the lock if it died |
| FAIL line, "not retrying: the flow or the app failed" | the failure is deterministic | the `failed step:` / `on screen:` lines under FAIL | fix the flow, then `--retry-failed` |
| `blank screenshot(s)` | the app paints its first frame after the flow's wait | README Tips | add `extendedWaitUntil: visible: "<text>"` before `takeScreenshot`. Note: docs say `run` retries blank once; 0.1.7 does not (see the README corrections) |
| Android: `the emulator exited with code N before it booted` / `emulators did not boot in time` | no KVM on Linux, small disk (12 GB userdata), not enough memory or cores | the emulator log tail in the message (`$TMPDIR/shotfleet-emulator-logs/`), `boot_failure_hint` | see `docs/linux.md`; one emulator on a 2-core machine, two need 4 or more cores |
| Android: `... is Android API 31; ... needs API 33` | per-app languages need Android 13 | `require_api33` | install an API 33+ image (the message prints the command) |
| shared Mac: runs void each other | two device jobs at once | `docs/device-queue.md` | take the agent-level lock first; never kill what you did not create |

### Licence

| Message (fragment) | Meaning | Fix or answer |
|---|---|---|
| `need a licence: shotfleet activate <key>` | `export` or `run` past 2 languages with no valid licence | the buyer runs `shotfleet activate <key>` |
| `that key didn't activate: ...` | refused key (wrong, `the key was disabled`, `the purchase was refunded`, charged back, disputed) | check the sale in Gumroad; runbook section 4 shows the read-only `curl` |
| `this key has used all 5 activations` | the lifetime counter reached `MAX_MACS` | the owner resets Uses in Gumroad ([05](05-licence-and-money.md)) |
| `nothing was activated and no activation was used: your licence covers every shotfleet version released until <date>` | the build is newer than the buyer's year | older versions keep working (`/download/<version>/`); renewal is not on sale: owner decision |
| `can't reach the licence server (...)` on `activate` | offline, a captive portal, a proxy | the activation may have been counted; the Mac remembers (`pending`); run `activate` again online, it will not count twice |
| `activating on this Mac didn't finish` | an interrupted activation left `pending: true` | `shotfleet activate <key>` again |
| `this licence is no longer valid (...)` | the weekly check refused it; the refusal is remembered | the reason is in the parentheses; `shotfleet activate <key>` checks again if it changed |
| `couldn't reach the licence server for 30 days` | offline grace over | connect once |
| `SHOTFLEET_KEY couldn't be checked` | CI key, Gumroad unreachable, key never passed a check on this machine in 30 days | rerun when Gumroad is reachable; cache `ci-checked.json` between hosted jobs |
| `the saved licence on this Mac is unreadable` | corrupt `licence.json` | `shotfleet activate <key>` (no extra activation) |
| the licence works from source but not in the release | by design: source runs unlicensed, only frozen builds enforce | n/a |

### Release or site problems

| Symptom | Look at |
|---|---|
| Live version and CHANGELOG disagree | `/download/VERSION` versus the top heading of `CHANGELOG.md`; `tools/status.sh --quick`; [06](06-packaging-and-release.md) |
| Notarization step says "No Keychain password item found" | the screen is locked (macOS locks that keychain about 5 minutes after the screen locks); it is not a lost profile; unlock, keep the Mac awake, retry (`research/notary-profile-2026-10-06.md`, `packaging/notary-check.sh`) |
| A deploy went wrong | roll back to the recorded Cloudflare version ([06](06-packaging-and-release.md)); the owner approves any production deploy |
| GA4 shows no data | expected until real traffic and consent: `research/ga4-investigation-2026-10-05.md` ([07](07-website-and-backend.md)) |

## 9.5 Operating habits that came from incidents

These are written down because each cost real time; the evidence is in [11](11-history-and-decisions.md).

- One device job at a time, with a hard time limit on every waiter (`docs/device-queue.md`).
- Keep release work in `/Users/manu/Developer/shotfleet-rc-build/`, never `/tmp`, which a reboot wipes.
- Check the exit code of the real command (`sh tools/check-claims.sh > log 2>&1; echo rc=$?`), never through a pipe.
- Do not release on a loaded Mac: memory pressure level 1, no stray emulators, `./gradlew --stop`.
- Prove who owns a process or folder before killing or deleting it.
