# Workarounds for the Maestro dependency and for a run's appetite for Mac resources (2026-10-05)

Branch `claude/workarounds-maestro-resources` (from `origin/main` 533299e). Device-free: no simulator, emulator or Maestro was started, nothing downloaded, no full test suite
run (only `tests.test_capacity_planner`, 17 tests, and `tests.test_docs`, 26 tests). The Mac was busy with someone else's 4-simulator run the whole time (load 824, 4 pool
simulators booted, `vm_stat`-available 6.9 to 9.5 GB of 32 GB, swap 6.2 GB): I read counters only and touched nothing.

Tags: **[R]** read in this repo. **[W]** read on the web today (2026-10-05); the pages were summarised by a small model through WebFetch, so quote nothing from here without
opening the URL. **[M]** measured today. **[I]** inference, mine.

## 1. Ranked recommendations

| # | What | Effort | Risk | Why now |
|---|---|---|---|---|
| 1 | **Run the quiet-Mac measurement (section 5), about 100 min of one device slot.** Every other decision (default Maestro version for iOS, whether the planner may change the device count, pre-warm, stagger) is a guess without it. | 0.5 day of attention, one quiet slot | none (own device names, hard limits) | The one hard fact we have says 2.0.10 beat 2.11.0 at 4 simulators (404 s, no retry, vs 826 s, 9 of 19 retried, both at low load) and `doctor --fix` installs 2.11.0. See decision D1. |
| 2 | **Wire the capacity planner warn-only** (`capacity = "warn"` default): print what the Mac showed and what to close, change nothing else. About 8 lines plus README and `skill/.../config.md` rows. Turn on `capacity = "adjust"` only after step 1 calibrates the per-device costs. | S (1 to 2 h) | low (a print) | Today a thrashing run is silent; the buyer sees 55 minutes of nothing. Prototype is on this branch, tested, not wired. |
| 3 | **Make the Maestro watch cheap and automatic, and add a deny list.** `tools/latest-maestro.py` downloads 315 MB every time; ask the releases API first and download only when the newest tag is not in `MAESTRO_TESTED` and not yet screened. Run it from a local weekly job (no Actions spend). Add `MAESTRO_BAD = {version: reason}` that `run` refuses (exit 2, one line) for known-broken versions, and keep today's warn-only for merely untested ones. | S to M | low | Maestro ships roughly monthly [W]; Xcode and iOS break its iOS driver on a different clock (section 4.2). |
| 4 | Adaptive retry: when attempt 1 loses at least half the languages, or two or more shards report nothing (the 2.11.0 pattern), run the retry on `n // 2` simulators and stagger the driver starts; keep one retry. | S to M, needs one device run to prove | low | Cheap protection against the 9-of-19 pattern without choosing a Maestro version. |
| 5 | Driver pre-warm (start each simulator's XCTest driver one at a time before the real Maestro call). Experiment first (section 5, case P); build only if it cuts time or retries. | M | medium: shotfleet kills drivers after every batch on purpose (`kill_stale_drivers`), pre-warm fights that | Only worth it if staggering shows a gain. |
| 6 | Fallback driver (plain XCUITest runner, Appium): **do not build** (section 4.5). Write down the triggers that would change that. | L to XL | high | Not a plan, a strategic note. |

### Decisions for the coordinator

- **D1 (most important).** `doctor --fix` pins Maestro 2.11.0 (`MAESTRO_PIN` [R]). On the one low-load comparison we have, 2.0.10 is the better iOS default at 4 simulators.
  2.11.0 is needed for Android non-Latin `inputText` (2.7.0+, `[inputs]`) [R]. Options: (a) keep 2.11.0 and ship recommendation 4 (retry on fewer devices); (b) pin 2.0.10 for
  iOS-only buyers until step 1 says otherwise (loses nothing on iOS, which has no `[inputs]` problem; Xcode 27 with 2.0.10 ran on iOS 26.4 simulators [R], but 2.1.0 broke on
  Xcode 26.2 [W #2932], so 2.0.10 on a future Xcode is a risk too); (c) wait for step 1. I recommend (c) with (a) as the fallback.
- **D2.** Enable the planner? Warn-only now (recommended); `adjust` after step 1. Not before: its memory costs are estimates and it was never run on a machine under 32 GB (section 2.4).
- **D3.** Whether `run` should refuse any Maestro. Recommended: only a deny list of versions proven bad, never "untested".

## 2. Capacity planner (prototype, `shotfleet.py`, tests in `tests/test_capacity_planner.py`)

### 2.1 What exists and what it adds

`fit_parallel(n)` [R] reads one number, macOS memory pressure (`kern.memorystatus_vm_pressure_level`): level 4 refuses ("Close some apps"), level 2 halves. `fit_emulators(n)` [R] is
Linux only (2 cores and 3 GB per emulator, from one 2-core runner). Neither reads swap, free memory, load, cores on macOS, or how many simulators are already up, and the
message is a generic hint printed *after* failures (`overload_note`). The prototype adds, without changing any of that:

- `plan_capacity(want, platform, reading) -> Plan(n, level, notes)`: **pure**, never below 1, never above `want`, never refuses (the caller keeps `fit_parallel`'s level-4 `Fail`,
  so exit codes cannot change). `level` is `ok`, `tight`, `short` or `critical`.
- `capacity_message(plan, want, reading)`: one paragraph naming the numbers seen and the fix ("Close Xcode, Android Studio and other simulators, run ./gradlew --stop ...").
  Empty string when all is well.
- `read_capacity(platform, prefix)`: the only impure part (`vm_stat`, `sysctl hw.memsize vm.swapusage`, `os.getloadavg`, `os.cpu_count`, `xcrun simctl list devices booted`).
  Every failed read stays `None` and that rule is skipped. Parsers (`parse_vm_stat`, `parse_swap_used_gb`, `parse_load1`, `count_booted`) are tested on this Mac's real text.

### 2.2 Rules (the fewest of these wins)

| Rule | Formula | Source |
|---|---|---|
| Cores | `cores // cores_per_device` (iOS 1, Android 2) | Android 2 is `fit_emulators` [R]; iOS 1 is [I], no evidence either way |
| Memory | `n <= (available_gb - 1.5 base - 2.0 headroom) // gb_per_device + already_booted_pool_devices`; `gb_per_device` iOS 2.0, Android 3.0 | Android 3 GB: `boot_failure_hint` [R]. iOS 2.0 and the 1.5 GB base (Maestro's JVM, helpers): **[I], not measured**; section 5 measures them |
| Swap | `swap_used >= 10 GB` **and** available memory below what the whole pool needs: run 1 device | 17 GB (gate start) and 21 GB crawled; 6 GB (gate end) finished [R]. 10 GB is the midpoint, not a measured knee |
| Pressure | level 2: `want // 2`; level 4: report `critical` (caller refuses as today) | `fit_parallel` [R] |
| Load | **not used for the number**; shown in the message only | see 2.3 |

`available_gb` = (free + inactive + speculative pages) times the page size from `vm_stat`. This Mac read 9.45 GB while `memory_pressure` said "free percentage 40%" (12.8 GB of 32):
the two scales differ, and the quiet check (`/tmp/shotfleet-quiet-check.sh`, 20% free) uses the second. The planner's costs are in the first scale and must be calibrated in it.

### 2.3 The evidence behind the thresholds (all 2026-10-04/05, from the repo)

| Run | Devices | Load / free % / swap | Result |
|---|---|---|---|
| Quiet re-measure, 2.0.10, CrossfitTracker 19 languages [R `docs/compat.md`, `docs/handoff.md`] | 4 iOS simulators, 4 Android emulators | quiet | 404 s iOS, 415 s Android, 0 problems, no retry |
| Release gate G3 start [R `release-0.1.1-evidence`] | 4 simulators | load 284, free 41%, **swap 16,969 of 18,432 MB**, 7 idle Gradle daemons (21 GB) | iPhone attempt 1 lost ar, de, ja, then tr; 54 m 57 s whole e2e |
| Release gate G3 end | | load 23, free 73%, swap 6,086 MB | fine |
| 2.11.0 iOS, 2026-10-04 clean rerun [R `research/maestro-2-11.md`] | 4 simulators | load 10, free 64%, level 1 | 826 s, **9 of 19 retried** (two of four drivers missed the 240 s start) |
| iOS 27 4-simulator e2e [R] | 4 | load 735, swap 21.6 GB | killed at 35 min, inconclusive |
| wger iOS 19 languages [R `research/real-apps-2026-10-05/`] | cut to 1 by `fit_parallel` (level 2) | level 2 | still "stopped" (hung) |
| Android fixture 2026-10-04 | 2 emulators | **load 765**, free 52%, level 1 | 148 s, passed |

What this says:
1. **Swap in use plus short memory is the signal, not load.** Load 765 (emulators inflate it) and 499 passed; load 284 with 17 GB of swap crawled. So load is shown, never decisive.
2. **Free percentage alone misleads**: the thrashing gate started at 41% free. Swap was the tell.
3. **Swap in use alone also misleads**: 6 GB at the gate end was a leftover, not thrash. Hence the AND with "memory below the pool's need".
4. **Low load does not make 2.11.0 safe**: the 9-of-19 retries happened at load 10, free 64%. That is a driver-start problem, not a memory one, so the planner cannot fix it (recommendation 4 can, section 4).
5. Something under the 10 GB swap figure is probably already slow; the figure is where I would stop trusting a run, not where thrash starts [I].

### 2.4 Estimates, and what is not known (honest)

- "4 simulators need about 11.5 GB available" = 1.5 + 4 x 2.0 + 2.0 headroom; "4 emulators about 15.5 GB". Both **[I]**: the 2 GB and 3 GB per device were never measured per process, and
  summing RSS double counts the shared dyld cache (I summed 53 GB of RSS for 4 simulators: meaningless). Section 5 case M measures the drop of available memory per booted device instead.
- The quiet gate only demanded 20% free (6.4 GB by `memory_pressure`) and 4 simulators passed, so **the planner is probably conservative**. On a 16 GB Mac with 5 GB available it would
  say 1 device where 4 may well work. That would be a 4x slowdown for a buyer; it is why the default is warn-only and `adjust` waits for calibration. I have no machine under 32 GB.
- Emulators are not counted as "already booted" (only simulators); `adb devices` on 57xx ports would add that (marked `ponytail:` in the code).
- Maestro's own JVM is one process per run for all shards [R], so the base cost does not grow with `n`.

### 2.5 Wiring, ready but not applied (few lines, coordinator's call)

In `ios_run_inner` after `n = fit_parallel(want)` (same two lines after `fit_emulators(...)` in `android_run_inner`):

```python
if cfg.get("capacity", "warn") != "off":
    r = read_capacity("ios", cfg.get("sim_prefix", "shotfleet")); plan = plan_capacity(want, "ios", r)
    if m := capacity_message(plan, want, r): print("warning: " + m, flush=True)
    if cfg.get("capacity") == "adjust": n = min(n, plan.n)
```

Also: `"capacity": str` in `KEYS["common"]`, a check that it is `off`, `warn` or `adjust`, a README row and a `skill/shotfleet/references/config.md` row (`tests/test_docs.py` and
`tests/test_agent_skills.py` read those), and `fit_parallel` stays first so level 4 still refuses. Override for the buyer: `capacity = "off"`, or `adjust` with an explicit lower `parallel`.
Not applied because I may not run the full suites here and a new config key touches the docs tests.

## 3. Why a run is hungry: the shape of the cost [R unless tagged]

One Maestro JVM per run drives all shards (`--shard-split k`); per device there is a booted simulator (or emulator), and on iOS an XCTest driver process per simulator. Every
`maestro` call starts a JVM (slow on a busy Mac), lists devices (3 times per test, including `xcrun devicectl` [W #3635]), and installs or starts each driver. After a failed
driver start Xcode 26+ may run a `simctl diagnose` of up to 10 minutes [W #3633]; shotfleet's watchdog already kills those. Other sessions' Gradle daemons, Android Studio and
Xcode are the usual competitors: 21 GB held by idle Gradle daemons caused the 55-minute run [R].

## 4. Maestro dependency risk

### 4.1 Cadence [W https://github.com/mobile-dev-inc/maestro/releases via the GitHub API, 2026-10-05]

Apache-2.0 [W api.github.com/repos/mobile-dev-inc/maestro], created 2022-03, about 15.9k stars, 520 open issues, pushed the same morning. CLI releases: 2.0.8 (2025-10-28), 2.0.9 (11-04),
**2.0.10 (2025-11-13)**, 2.1.0 (2026-01-12), 2.2.0 (02-20), 2.3.0 (03-10), three 2.3.1-dev prereleases, 2.4.0 (04-02), 2.5.0 (04-27), 2.5.1 (04-30), **2.6.0 (05-21)**, 2.6.1 (06-12),
**2.7.0 (07-20)**, 2.8.0 (07-31), 2.9.0 (08-26), 2.10.0 (08-31), **2.11.0 (09-29)**. That is ten minors in 10.5 months after a two-month gap; since February roughly monthly, with a
patch or a second minor now and then. Release notes on GitHub just point at `CHANGELOG.md` [W]. Six commits sat on main after 2.11.0 [W]; no 2.11.1 or 2.12 on 2026-10-05.
INFERENCE: expect about three new versions before the next shotfleet minor release; "tested with 2.0.10 and 2.11.0" will be stale within weeks.

### 4.2 What changed between 2.0.x and 2.11.x that touches shotfleet [W CHANGELOG.md, main, plus issues; cross-checked with `research/maestro-2-11.md` [R]]

| Area | Change | Version | Matters because |
|---|---|---|---|
| Java | Java 17 required, GraalJS replaces the old JS engine | 2.0.0 (before our range); Rhino removed 2.6.0 | `doctor --fix` installs Java; `runScript` flows |
| `--device` on `test` | `--platform`, `--device` added to `test`; `--device-os/--device-model` replace `--ios-version`; `list-devices` | 2.1.0, 2.4.0 | shotfleet uses the global `maestro --device A,B test`: unchanged, passes on both |
| iOS driver on new Xcode | Driver never listened on 7001 under Xcode 26.2; workaround longer startup timeout; fixed by PR #3166 [W #2932, opened 2026-01-16] | 2.1.0 broken; fix in a later release [I: first version not read] | The real dependency risk: Apple moves, Maestro follows within weeks, buyers wait |
| Parallel iOS | Per-device session keys, dynamic port instead of 7001, a file lock on `~/.maestro/sessions`, warm session reuse (about 15 to 8 s per device) [W PR #3138, merged 2026-05-12] | 2.6.0 (05-21) | Plausible [I] cause of the 2.11.0 start problem at 4 simulators (new locking and port code under 4 simultaneous starts); shotfleet's port-7001 comments are 2.0.10 lore |
| Driver death mid-suite | XCUITest driver dies silently, rest of the suite fails at once; asked for restart or `--restart-driver-between-flows` [W #3368, #3318], closed "not planned" | 2.6.0 | shotfleet's retry is the only protection |
| Hierarchy | `maestro hierarchy` prints JSON only; iOS hierarchy faster by direct snapshot traversal | 2.6.0, 2.7.0 | shotfleet reads text from Maestro's debug artifacts, not that command; `maestro-compat.py` checks the log strings |
| WebView | Android WebView: bounded devtools sockets, hierarchy as a serialized string | 2.9.0 | positive for WebView text; iOS WebView text: nothing found, **not verified** |
| Artifacts | New per-flow bundle, a screenshot before every step; `takeScreenshot` confined to the output folder | 2.7.0, 2.8.0 | Broke shotfleet's absolute paths on 2.11.0 (25 of 36 assertions) until relative names; fixed [R] |
| Errors | `launchApp`, `setPermissions`, `clearState` errors no longer swallowed | 2.7.0 | not seen in our runs [R] |
| Speed | Android direct ADB socket, about 41% faster | 2.5.0 | |
| Physical iPhones | not listed any more | 2.11.0 | none, simulators only |

**Known performance problems [W]:** driver start is slow and reinstalls the driver each run: an open PR claims 52 s to 10 s warm for one device and 54 to 15 s for three
(#3139, opened 2026-04-04, **still open**, not a release feature); device discovery has no timeouts so one unresponsive device stalls every run, even with `--device` (#3635, open,
affects 2.6.1 and 2.10.0); `xcodebuild` collects a diagnose on every driver failure on Xcode 26+ and 27 (#3633, open, 2.10.0, Xcode 27.0, iOS 27.0 runtime); Android adb calls with no
timeout (#3658, open); the dynamic work-stealing shard (`--shard-split-dynamic`, #3340) was closed "not planned". Open Xcode 27 items concern Studio/Viewer only (#3606, #3661): `maestro test` works.
Everything that fits shotfleet's own run at 4 simulators is in section 2.3 and `docs/handoff.md` item on 2.11.0 [R].

### 4.3 What shotfleet should do (cheap, in order)

1. **Tested-versions matrix**, one table in `docs/compat.md` (exists as prose; make it rows): version, date, iOS e2e (time, retries, load), Android e2e, `maestro-compat.py` result, Xcode and iOS runtime used.
   Today's rows: 2.0.10 pass (404 s, 0 retries), 2.11.0 pass (826 s, 9 retries), nothing else tested. Keep `MAESTRO_TESTED` as the code form of it.
2. **Weekly compatibility check without Actions.** `tools/watch-upstream.sh` and `tools/latest-maestro.py` [R] work but are manual and download 315 MB each time. Make `latest-maestro.py`
   read the releases list first and exit 0 "nothing new" when the newest tag was screened last time (a one-line state file). A weekly launchd or Claude scheduled task on the owner's Mac
   can run it; the existing `maestro-latest.yml` stays manual (spend). A pass still means "worth a real run", never "supported".
3. **Untested versions: warn (as `doctor` and `run` already do), refuse only a deny list.** `maestro_warning` prints "not the version shotfleet was tested with" and continues [R]; a refusal of
   merely untested versions would strand buyers for weeks after each Maestro release. A `MAESTRO_BAD` entry (with the reason and the fix) is the one case worth a hard stop.
4. **Static check additions** to `MAESTRO_INTERFACE`: the "resolves outside this run's" string (the check that would have caught 2.11.0 on day one, noted in `research/maestro-2-11.md`),
   and `-collect-test-diagnostics` presence for #3633 [I].
5. **Driver pre-warm**: possible because per-device sessions are reused in 2.6+ (#3138) [W], but unproven for how long a driver outlives the Maestro call, and shotfleet kills drivers after
   every batch. Test as case P below before building. Cheaper first: **stagger** (start shard drivers 20 to 30 s apart) is not possible through one `--shard-split` call, so it means one
   Maestro call per simulator started in sequence, which loses Maestro's sharding; so only pre-warm (a no-op flow on each simulator in turn, then the real call) is a realistic form [I].
6. **Adaptive retry/backoff** (recommendation 4): the retry already waits for `healthy_installs`; add "fewer devices when the first attempt lost half or two silent shards".
   Backoff in time buys little: the failure is a driver that never came up, not a transient.

### 4.4 `MAESTRO_DRIVER_STARTUP_TIMEOUT`

shotfleet sets 240000. The 2.11.0 failure message says "consider increasing timeout" even then [R]. A bigger value (the #2932 reporter used 300000) only helps a slow driver, not a
dead one [I]; the cost of a bigger value is that a truly dead start now takes 5 minutes before the retry. Test 300000 as a variable in case S, not as a default.

### 4.5 Fallback driver: realistic? (strategic note; effort and risk are INFERENCE, not a plan)

What shotfleet takes from Maestro [R, `MAESTRO_INTERFACE`]: a flow interpreter (13 command families: `launchApp` with arguments and `permissions`, `clearState`, `tapOn` with
relative anchors, `assertVisible`, `scrollUntilVisible`, `extendedWaitUntil`, `inputText`, `runScript`, `repeat`, `takeScreenshot`, `waitForAnimationToEnd`), device sharding,
a JUnit report, the screen-text dump, and the iOS XCTest runner and Android driver underneath. Users write `flow.yaml` in Maestro's language, so a fallback must run those flows.

| Option | What you build | Effort | Risk |
|---|---|---|---|
| **A. Keep Maestro's iOS driver, drop its CLI**: vendor the Apache-2.0 XCTest runner (arm64+x86_64 in both versions [R]), talk to it from Python over HTTP, write the interpreter (above) | interpreter for the flows people actually use, a driver client, reports | 4 to 8 weeks | medium: the driver's HTTP protocol is internal and changed with 2.6 and 2.7; removes the JVM (memory, 3-per-test discovery, startup) and the CLI regressions, keeps driver regressions |
| **B. Plain XCUITest runner of our own** (a Swift UI-test bundle that drives another app by bundle id) | the runner, a protocol, the interpreter, hierarchy dump; Android through UiAutomator or `adb` | 8 to 14 weeks, plus Xcode-version upkeep | high: reinvents the part Maestro maintains against every Xcode, which is where Maestro itself broke (#2932) |
| **C. Appium** (XCUITest driver + UiAutomator2) | a flow-to-WebDriver translator, Node and Appium installation in `doctor --fix`, session and port management per simulator | 6 to 10 weeks | high: heavier (Node, WebDriverAgent builds; preinstalled WDA needs iOS 17+ and extra setup [W appium docs]), another large upstream on its own Xcode treadmill, and no evidence it uses less memory per simulator |

Honest conclusion: the dependency is real but its measured costs so far were **version-specific and fixable at our end** (the screenshot path, the retry), and the structural fix is
option A, not B or C. Do not start any. Revisit if: (1) a new Xcode breaks the pinned Maestro and upstream takes more than about 8 weeks to ship a fix (#2932 opened 2026-01-16; 2.2.0 came
2026-02-20 and 2.4.0 2026-04-02, first fixed version not read [I]); (2) mobile-dev-inc changes the licence or archives the repo (Apache-2.0 today [W]; the commercial product is Maestro Cloud, so
priorities for the local CLI may drift [I]); (3) the measurements in section 5 show the JVM and driver overhead is the main memory or time cost. The cheapest insurance is already
in place: `doctor --fix` installs a pinned, checksummed Maestro [R], so a buyer is never on a moving version unless they chose it.

## 5. Measurement plan (a QUIET Mac; nothing here was run)

**Preconditions, every case:** take the lock `mkdir /tmp/shotfleet-devices.lock && echo "<session> | capacity measurement | <HH:MM> | est. 100 min" > /tmp/shotfleet-devices.lock/holder`
(release with `rm -rf` at the end); `sh /tmp/shotfleet-quiet-check.sh` must print `quiet:` (it stops the case if not, no waiting); close Android Studio and run `./gradlew --stop`
in projects you own only; no emulators on 57xx; iOS runtime pinned in the config to an installed 26.x (not 27). Record per case: Maestro version, `sw_vers`, Xcode version, `sysctl hw.memsize hw.ncpu`.
Every shotfleet step gets a hard kill: `perl -e 'alarm shift; exec @ARGV' <seconds> <cmd>` (macOS has no `timeout`), plus the config's `stall_s = 300` and `timeout_s = 300`.

**Sampler (leave running in a second shell, one file per case, kill by its own PID; replace `SHOTFLEET_REPO` with the checkout path and set `CASE`):**

```sh
sample() { out=$1; echo "t,avail_gb,swap_gb,load1,pressure,sims_booted,maestro_jvm_gb" > "$out"
  while :; do python3 - "$out" <<'PY'
import sys, time, subprocess
sys.path.insert(0, "SHOTFLEET_REPO"); import shotfleet as sf
r = sf.read_capacity("ios"); ps = subprocess.run(["ps", "-axo", "rss,command"], capture_output=True, text=True).stdout
jvm = sum(int(l.split()[0]) for l in ps.splitlines() if "maestro/lib" in l and "java" in l) / 2**20
open(sys.argv[1], "a").write(f"{time.time():.0f},{r.avail_gb:.2f},{r.swap_used_gb:.2f},{r.load1:.0f},{r.pressure},{r.booted_ours + r.booted_other},{jvm:.2f}\n")
PY
  sleep 10; done; }
sample /tmp/cap-$CASE.csv & SAMPLER=$!   # at the end: kill $SAMPLER
```

**Case M, memory per booted device (about 12 min, no Maestro).** Create four throwaway simulators `shotfleet-memtest-1..4` (`xcrun simctl create`, iOS 26.x, the config's device type),
record the baseline (sampler 60 s), boot one, wait for `bootstatus`, wait 60 s, record; repeat to 4; then install and launch the app on each and record again; delete the four.
Result: `gb_per_simulator = (avail_before - avail_after) / k` for idle and with-app, and swap change. Same for Android: `emulator -avd shotfleet_android -port 5702 -read-only` ... 1 then 2 emulators
(about 10 min). These replace the 2.0 and 3.0 constants.

**Case matrix, iOS (Maestro x devices).** Config `examples/crossfittracker/shotfleet.toml` with `stall_s = 300`, `timeout_s = 300`; out dir fresh per case; `--locales` as listed:

| Case | Maestro | `--parallel` | Languages | Reps | Est. time each | Hard kill |
|---|---|---|---|---|---|---|
| A4 | 2.0.10 | 4 | all 19 | 2 | 7 min + 3 boot | 20 min |
| A2 | 2.0.10 | 2 | first 8 | 2 | 7 min + 2 boot | 15 min |
| A1 | 2.0.10 | 1 | first 8 | 1 | 13 min + 1 boot | 25 min |
| B4, B2, B1 | 2.11.0 | 4, 2, 1 | 19, 8, 8 | 2, 2, 1 | same as above | same |

(Estimate: 404 s for 19 languages on 4 simulators is about 85 s of simulator time per language [I].) Order: A4, B4, A4, B4 (interleaved, so drift cancels), then A2, B2, A2, B2, then A1, B1. Total about
2 x (23 + 18 + 14) = 110 min with boots; cut A1/B1 if the slot is short.

```sh
# per case; MAESTRO_HOME is ~/.maestro (2.0.10) or ~/.maestro-tests/2.11.0/maestro
export PATH=$MAESTRO_HOME/bin:$PATH; maestro --version | tee -a /tmp/cap-$CASE.log
sh /tmp/shotfleet-quiet-check.sh || exit 1
perl -e 'alarm shift; exec @ARGV' $KILL python3 shotfleet.py run examples/crossfittracker/shotfleet.toml --parallel $N --locales "$LANGS" 2>&1 | tee /tmp/cap-$CASE.log
echo "exit=$?"; python3 - <<'PY'
import json, glob
r = json.load(open(glob.glob("out/*/run.json")[0]))
print("wall", r["wall_seconds"], "sims", r["simulators"], "retried", sum(1 for v in r["locales"].values() if v.get("attempts", 1) > 1), "failed", sum(1 for v in r["locales"].values() if not v.get("ok")))
PY
```

**Record per case:** exit code; `wall_seconds`, `simulators`, languages retried and failed (above); time from "capturing N locales" to the first screenshot of each shard (first PNG mtimes in
`out/.work/debug/attempt1`) = driver start time per shard; the line `iOS driver not ready in time` in `maestro1.log` (count and which shard); the CSV (peak swap, minimum available GB, maximum
JVM GB, pressure changes); whether `simctl diagnose` ever ran (`pgrep -fl "simctl diagnose"` sampled with the CSV). A case is **void**, not failed, if the quiet check fails at its start or another
session starts a device job (note it, discard it).

**Case S (longer driver timeout, 2.11.0, 4 simulators, 19 languages, about 8 min, only if B4 retried):** shotfleet sets `MAESTRO_DRIVER_STARTUP_TIMEOUT=240000` itself (`shotfleet.py`, `ios_run_inner`), so
exporting 300000 in the shell does nothing; run from a scratch copy of the repo with that number changed to 300000 and compare retries and time to first screenshot with B4. A stagger through one
`--shard-split` call is not possible, so staggering is case P.

**Case P (pre-warm, 2.11.0, 4 simulators, about 10 min):** boot the pool by hand (names `shotfleet-iphone-17-pro-max-1..4`, the pool prefix), install the app, then for each simulator in turn run
`maestro --device <udid> test warm.yaml` (a flow with only `launchApp` and `waitForAnimationToEnd`) with `MAESTRO_DRIVER_STARTUP_TIMEOUT=240000`, noting how long each takes; **without** running `kill_stale_drivers`,
start the real 4-device run via `shotfleet run` and record time to first screenshot per shard and retries against B4. Check whether the drivers are still alive between calls (`pgrep -fl maestro-driver`, the
port in `~/.maestro/sessions`). If shotfleet's own `kill_stale_drivers()` at the start of `ios_run_inner` kills them anyway (it does [R]), record that: the experiment then needs a scratch edit, which is the finding.

**Android (about 25 min):** same matrix with `shotfleet.py run examples/crossfittracker/android.toml --parallel N` on 2.0.10 and 2.11.0, N = 1, 2, 4 on 19 languages (A4 about 7 min, N=1 about 25 min: skip N=1
unless time), sampler as above (add `qemu-system-aarch64` RSS with `ps -axo rss,command | grep "[q]emu-system" | awk '{s+=$1} END {print s/1048576}'`; RSS double counts, treat as an upper bound).

**Decision rules once the numbers exist:** (1) set `gb` per device from case M, then check the planner against the CSVs: it should have said 4 on every quiet A4/B4 start and fewer on a start with a deliberately
held memory hog (`memory_pressure -l warn` probably needs sudo [I]; use `python3 -c "x=bytearray(14*2**30); input()"` to hold 14 GB, kill by PID); (2) if B4 retries again at load under 20 and A4 does not, decide D1 for iOS;
(3) if S/P cut B4 to under 500 s with no retries, build recommendation 5 or 4 in that form.

## 5a. Measurement (2026-10-05)

Run by the coordinator's device-slot runner under the device lock, 16:40 to 18:26 [M]. Mac: 10 cores, 32 GB, macOS 27.0 (26A428), Xcode 27.0 (27A266a),
runtime pinned to `com.apple.CoreSimulator.SimRuntime.iOS-26-4`, device type iPhone 17 Pro Max, pool `shotfleet-1..4`. **App: the repo's fixture**
(`tools/fixture-app`, 5 languages en/de/ja/ar/tr, one flow with 2 screenshots), not CrossfitTracker: so a case is 10 screenshots, not 19 languages, and the
times below are mostly boot and driver start, not flow time. Config per case: `stall_s = 300`, `timeout_s = 300`, fresh `out`, `--locales en,de,ja,ar,tr`;
Maestro chosen with `SHOTFLEET_MAESTRO` (2.0.10 = `~/.maestro`, 2.11.0 = `~/.maestro-tests/2.11.0`). Every case: quiet check at its start (all passed),
hard kill (`perl alarm`), sampler every 10 s (`read_capacity`, Maestro JVM RSS). Scripts and raw data (not in the repo):
`/Users/manu/Developer/shotfleet-rc-build/device-slots/job3/` (`results.jsonl`, `cap-<case>.csv`, `cases/<case>/run.log`).

**The Mac was not quiet in the plan's sense.** The quiet check (load under 300, free memory 20 %+) passed at every case start, but swap in use was 10.4 to
14.3 GB from 16:52 on (6.1 GB before my first boots; it never came back down), and 4 booted iOS 26.4 simulators alone keep load1 at 400 to 1000 here.

### Case matrix (iOS, fixture, in run order)

| Case | Maestro | Sims | Result | Wall (s) | Setup before capture (s) | Capture (s, `run.json`) | Retried | Peak load | Peak swap GB | Min avail GB (`vm_stat`) | Max JVM GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A4_1 | 2.0.10 | 4 (pool created fresh) | **killed at 900 s** | 900 | 204 | none | 4 of 5 retried, then killed | 999 | 12.6 | 4.7 | 0.41 |
| B4_1 | 2.11.0 | 4 | **killed at 900 s** | 900 | 187 | none | all 5 retried, then killed | 1021 | 14.3 | 4.9 | 1.28 |
| A2_1 | 2.0.10 | 2 -> 1 | pass 5/5 | 406 | 336 | 63 | 0 | 319 | 14.0 | 9.4 | 0.53 |
| B2_1 | 2.11.0 | 2 | pass 5/5 | 210 | 37 | 166 | 0 | 414 | 13.6 | 7.7 | 0.53 |
| A2_2 | 2.0.10 | 2 | pass 5/5 | 196 | 87 | 103 | 0 | 348 | 13.3 | 6.3 | 0.76 |
| B2_2 | 2.11.0 | 2 | pass 5/5 | 201 | 63 | 131 | 0 | 361 | 12.4 | 7.5 | 0.53 |
| A1_1 | 2.0.10 | 1 | pass 5/5 | 138 | 23 | 112 | 0 | 260 | 12.4 | 8.5 | 0.59 |
| B1_1 | 2.11.0 | 1 | pass 5/5 | 147 | 41 | 102 | 0 | 175 | 10.9 | 7.5 | 1.03 |
| A4_2 | 2.0.10 | 4 | pass 5/5 | 280 | 93 | 173 | 0 | 844 | 10.8 | 5.3 | 0.51 |
| B4_2 | 2.11.0 | 4 | pass 5/5 | 301 | 237 | 50 | 0 | 735 | 11.3 | 5.1 | 1.47 |
| A4_3 | 2.0.10 | 4 | pass 5/5 | 325 | 268 | 44 | 0 | 690 | 11.9 | 4.7 | 0.86 |
| B4_3 | 2.11.0 | 4 | pass 5/5 | 281 | 117 | 150 | 0 | 633 | 11.8 | 5.8 | 0.51 |

"Setup before capture" = seconds from `shotfleet run` to its "capturing" line (pool boot, `bootstatus`, status bar, install). Memory pressure level was 1 or 2
(never 4) in every case; no "Unknown error" or "Unable to clear state" anywhere.

**What stopped answering:**
- A4_1 (pool created in this case, i.e. four first boots at once): 3 of 4 shards hit "iOS driver not ready in time" (the 240 s
  `MAESTRO_DRIVER_STARTUP_TIMEOUT`), one shard passed `en` in 19 s; on the retry `shotfleet-1` stopped answering (`simctl terminate` did not return in 300 s,
  shotfleet carried on without it) and the hard kill came at 900 s. That simulator stayed broken: in A2_1 the same `terminate` hung 300 s again, and
  shotfleet ran on 1 simulator (5/5, so the carry-on works). I deleted and recreated it between cases (a single first boot then took 32 s at load ~180).
- B4_1: all 4 shards sat at "Waiting for flows to complete" with no screenshot for 300 s (stall stop), the retry of all 5 gave no result before the kill at 900 s. No
  "driver not ready" line. After the kill, its orphaned Maestro driver (`xcodebuild test-without-building` for `shotfleet-1`) ran `simctl diagnose` for a
  few seconds and then ended by itself.
- Driver start time per shard (first screenshot per shard) was **not recorded**: shotfleet removes `.work` after collecting, and my sampler looked there.

### Case M, memory per booted simulator

- **M (fresh, created for the test, `shotfleet-memtest-1..4`):** baseline 10.2 GB available (`vm_stat`), swap 6.1 GB, load 7. 1 booted: 7.4 GB (-2.8 GB),
  load 264. 2 booted: 5.8 GB (-2.2 GB per simulator), load 512. **The 3rd first boot did not finish `bootstatus` in 400 s** (load ~900, `ps` and `simctl`
  calls took over 60 s); case aborted, the four test simulators deleted. A first boot is far heavier than a later boot.
- **M2 (the warm pool `shotfleet-1..4`, booted one after another, 60 s settle each):** baseline 11.65 GB, swap 11.5 GB, load 109. After 1/2/3/4 booted:
  9.70 / 9.99 / 8.29 / 8.01 GB, load 154 / 252 / 351 / 437. With the fixture installed and launched on all four: 6.38 GB, load 518, pressure level 2.
  **Per simulator: about 0.9 GB idle (3.6 GB for 4) and 1.3 GB with the app (5.3 GB for 4)**; swap fell 1.1 GB meanwhile (macOS paging back in), so
  the `vm_stat` figure is noisy at this swap level. The planner's 2.0 GB per iOS simulator is an upper bound for a warm pool and too low for first boots
  (2.2 to 2.8 GB each, and they stall at three).
- **Load, not memory, is what 4 simulators cost here:** 4 idle booted simulators = load ~440, which alone fails the quiet check (case P below).

### Case P, pre-warm (2.11.0)

Pool booted by `make_pool` (4), fixture installed, then `maestro --device <udid> test warm.yaml` (`launchApp`, `waitForAnimationToEnd`,
`MAESTRO_DRIVER_STARTUP_TIMEOUT=240000`) one simulator at a time:
- Simulator 1: **235 s** to warm (with the other 3 booted, load ~400), exit 0, and **0 driver processes alive after the call** (`pgrep` for
  `xcodebuild test-without-building` and `maestro-driver`). Maestro 2.11.0 stops its XCTest driver at the end of each call, so a pre-warmed driver cannot
  survive into shotfleet's run even before `kill_stale_drivers` runs. I stopped the warm-up after simulator 2 had started (the finding was settled and the
  slot was finite).
- The real run on the pre-booted pool (P_run) was **void**: the quiet check failed at its start (load 400 with the 4 idle simulators booted).

Not run: case S (only if B4 retried for driver start; the B4 failure was a stall, not "driver not ready"); the Android matrix; the 14 GB memory-hog check.

### Reading and recommendation

- **No evidence that 2.11.0 is worse than 2.0.10 on iOS with this app.** At 4 simulators each version had one failed case (A4_1 cold pool, B4_1 stall)
  and two clean passes (capture 2.0.10: 173 and 44 s; 2.11.0: 50 and 150 s); at 2 and 1 simulators both always passed with no retries and similar times
  (at 2: 2.11.0 166 and 131 s, 2.0.10 103 s plus 63 s in A2_1, which ran on 1 simulator; at 1: 102 against 112 s). The spread between repeats of the same case (44 to 173 s)
  is larger than any version difference. "iOS driver not ready" appeared only on 2.0.10 (A4_1, first boots).
- **What decides a 4-simulator run on this Mac is load and swap, not the Maestro version:** both failures happened with peak load ~1000 and swap 12.6 to
  14.3 GB; every pass at 4 had peak load 633 to 844. Setup before capture (93 to 268 s) is larger than capture itself for a short flow.
- **Recommendation: keep 2.11.0 as the one default (no iOS pin to 2.0.10, no per-platform split)**, so D1 option (a): keep 2.11.0 and ship
  recommendation 4 (retry on fewer simulators when attempt 1 loses half the languages), plus D2 with real numbers: count about 1.3 GB per warm iOS
  simulator with the app and treat first boots (a fresh pool) as at least 2.5 GB each and never more than two at once. Pre-warm (recommendation 5): **drop
  it**, 2.11.0 does not keep a driver between calls. Caveat: the fixture flow is short; the earlier CrossfitTracker data point (19 languages, 2.0.10 404 s
  against 2.11.0 826 s with 9 retried) is not contradicted for long flows. Repeat A4/B4 with CrossfitTracker on a Mac with swap under 8 GB before
  pinning anything.

## 6. What I could not verify

- The per-device memory costs (iOS 2.0 GB, Android 3.0 GB, 1.5 GB base) and the 10 GB swap knee: estimates; case M and the CSVs settle them. No machine under 32 GB was available to test the planner's output on a small Mac.
- Which Maestro release first fixed the Xcode 26.2 driver problem (#2932 closed by PR #3166; I did not read the release it landed in), and whether 2.6.0's parallel work really causes the 2.11.0 start problem (inference from the timing of PR #3138 and our 4-simulator results).
- Whether an XCTest driver survives the end of a Maestro call in 2.6+ (needed for pre-warm); 2.0.10 left drivers behind on port 7001 [R], which is why `kill_stale_drivers` exists.
- iOS WebView text on any Maestro version; the full changelog (I read a model's summary of `CHANGELOG.md`, and the release pages themselves only say "see CHANGELOG.md"); the GitHub issue summaries are of the pages as fetched today.
- Effort figures in 4.5 are my estimates, not measured against any code.
- Nothing about Xcode 27's `DeviceHub.app` rename affecting `simctl` or shotfleet (reported for Maestro Studio only, #3606).
- The wiring in 2.5 was written, not applied or run; only the pure function, parsers and message are tested (17 tests, `python3 -m unittest tests.test_capacity_planner`).
