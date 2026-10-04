# Overcoming three README limits: hierarchy text, typed text, launchApp options

Research date 2026-10-02. Nothing here was run on a simulator, emulator, or Maestro flow (other sessions were using them), nothing was installed, and no repo file was edited.

Evidence tags:
- **[source]** = read in Maestro source. Sources are `main` at commit a4ccea7 (2026-10-02, version 2.11.0) and tag `cli-2.0.10` (the Maestro installed on this Mac). Both were cloned shallow into the scratchpad.
- **[docs]** = from a linked page.
- **[repo]** = from this repo.
- **[inferred]** = my reasoning, not seen in a source or docs.
- **[unverified]** = needs an experiment.

Nothing about timing is **[measured]**.

Two facts frame all three limits:
- The Maestro on this Mac is **2.0.10**; upstream is **2.11.0**. Several things below need **Maestro >= 2.7.0** (release PR https://github.com/mobile-dev-inc/Maestro/pull/3432, merged 2026-07-20; changelog https://github.com/mobile-dev-inc/Maestro/blob/main/CHANGELOG.md). shotfleet's README says only "Maestro 2.x".
- Maestro's own `--debug-output` folder is already passed by shotfleet to every run, in both `ios_run` and `android_run` [repo: `shotfleet.py` ~875, ~1045].

---

## 1. Read the screen's text from the UI hierarchy instead of pixels

### Verdict: feasible now on Maestro >= 2.7.0; the one trick it rests on was run on 2.11.0 on 2026-10-04 and works (section 1f). Effort M. Not worth it on older Maestro.

### 1a. What exists (verified in source)

| Fact | Evidence |
|---|---|
| `maestro hierarchy` prints JSON (since 2.6.0; `--compact` gives CSV) of the **connected** device. It opens its own session. | [source] https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-cli/src/main/java/maestro/cli/command/PrintHierarchyCommand.kt ; [docs] https://maestro.dev/blog/maestro-cli-v2-6-0 |
| **iOS element -> Maestro attributes.** `accessibilityText` = AX **label**, `title`, `value`, `text` = `title` if non-empty else `value`, `hintText` = placeholder, `resource-id` = identifier, `bounds`. SwiftUI `Text("Hello")` has label `Hello` and empty value, so its text sits in **`accessibilityText`, not `text`**. | [source] https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-client/src/main/java/maestro/drivers/IOSDriver.kt (`mapViewHierarchy`, ~line 211) |
| **Android attributes.** `text` (with a hint fallback), `content-desc` -> `accessibilityText`, `hintText`, `resource-id`, `bounds`, `visible-to-user`, `error`. Invisible children are skipped. WebView content is kept even when reported invisible. | [source] https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-android/src/androidTest/java/dev/mobile/maestro/ViewHierarchy.kt ; AndroidDriver.kt ~1152 |
| The hierarchy is the **real** Unicode string. XML is UTF-8 on Android, JSON via Jackson on both. Only XML-illegal control characters are stripped. | [source] ViewHierarchy.kt `stripInvalidXMLChars` ; TestOutputWriter.kt (Jackson, no `ESCAPE_NON_ASCII` found) |
| **Maestro JS cannot read the screen.** The `maestro` JS object holds only `copiedText` and `platform`. `runScript`/`evalScript` can only call `http`, `json()`, `output`, `env`. So there is no "give me all text" call from a flow. | [source] https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-client/src/main/java/maestro/js/GraalJsEngine.kt lines 80, 154 ; [docs] https://docs.maestro.dev/maestro-flows/javascript/make-http-requests.md |
| `http.get/post` is a synchronous okhttp wrapper, so a flow step **blocks** until the server answers. This is what makes a "barrier" design race-free. | [docs] same page; [source] GraalJsHttp.kt |

### 1b. Three ways to capture per screenshot, ranked

**A. In-run marker step (recommended; no ports, no extra tool, no race).** [source, not run]

Maestro 2.7.0+ writes `screen-hierarchy/step-NNN-<cmd>.json` into the per-flow debug folder for any *visible* step that **fails or warns** (https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-orchestra/src/main/kotlin/maestro/orchestra/debug/ArtifactsGenerator.kt, `onCommandFinished`, `captureStepHierarchy`). That is not true on 2.0.10: `CommandDebugMetadata.hierarchy` is declared but never set, so no hierarchy file is written. I checked the tag's source and `cli-2.6.0` returns 404 for that file.

An `optional: true` step that fails is reported as `CommandOutcome.Warned`: the flow carries on and passes, and the hierarchy is saved (Orchestra.kt lines ~344-355). `assertTrue` supports `condition`, `label` and `optional` (YamlAssertTrue.kt), and a condition that evaluates to `false` fails immediately without a wait (Orchestra.kt `evaluateCondition`, script condition branch). So right after every `takeScreenshot`, shotfleet appends:

```yaml
- assertTrue:
    condition: ${false}
    label: "shotfleet:hier:01_home"
    optional: true
```

- Cost: Maestro's own comment says the hierarchy round trip is "~1s" (ArtifactsGenerator.kt header). A failing `assertTrue` fetches the hierarchy twice: once for the exception in `assertConditionCommand`, once for the artifact. That is about 2 s per screenshot, so about 16 s per locale for 8 shots. Spread over 4 parallel devices and 40 locales that is roughly +3 min. [source + inferred]
- Android's `viewHierarchy` first calls `uiDevice.waitForIdle(500)` and clears the accessibility cache [source: MaestroDriverService.kt ~200-250], so a busy screen can add up to 0.5 s.
- It also saves a PNG per warned step, which is harmless because `.work/debug` is scratch.
- Where the output lands: `<debug>/<flow name>[-shard-N][-2]/screen-hierarchy/`, with `commands.json` beside it listing every step with its `label`, `sequenceNumber` and `artifacts` [source: TestDebugReporter.createFlowDir, FlowDebugOutput.kt]. shotfleet already sets `name: <lproj>` in the flow header, so the folder is predictable. Pair by label from `commands.json`; fall back to the k-th marker equals the k-th screenshot.
- It works identically on iOS and Android because it lives in Orchestra, not in a driver.

**B. Out-of-process dump, timed by an HTTP barrier.** [source for the endpoints, rest inferred]

Add `- runScript: {file: snap.js, env: ...}` after each screenshot. `snap.js` calls `http.get('http://127.0.0.1:PORT/snap?...')`, and a tiny `http.server` thread in shotfleet dumps and only then answers.
- **iOS, direct to the runner.** Maestro's XCTest runner is an HTTP server on `127.0.0.1` with routes `viewHierarchy, screenshot, status, deviceInfo, inputText, launchApp, setPermissions, ...` (https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-ios-xctest-runner/maestro-driver-iosUITests/Routes/XCTestHTTPServer.swift ; CONTRIBUTING.md documents `curl localhost:22087/deviceInfo`).
  - The call is `POST /viewHierarchy` with `{"appIds":["<bundle>"],"excludeKeyboardElements":false}`.
  - The response is an `AXElement` tree (identifier, frame, value, title, label, elementType, placeholderValue, ...).
  - The port is **not fixed**. In 2.11 `maestro test` picks a random free port per shard (`ServerSocket(0)`, TestCommand.kt `selectPort`) and logs `[shard N] Selected device <udid> using port <port>`. shotfleet's `flow_devices()` already regex-parses that same log line, so the udid-to-port map is available.
  - Never use a bare `maestro --device X hierarchy` for this. It defaults to port 22087 and adopts **any** runner answering there, which can be another simulator's. See https://github.com/mobile-dev-inc/Maestro/issues/3611 (open, 2026-09-18). 2.6.0 added `--driver-host-port` and a per-device lock, which only partly mitigates it.
- **iOS via idb.** `idb ui describe-all --udid <U> --format complete` reads the accessibility tree without Maestro's runner. The `axbridge` backend is documented at about 30 ms on an idle screen and 1.6 s on a heavy tree, and returns exact `label` and `identifier` (https://github.com/facebook/idb/blob/main/website/docs/idb/accessibility.mdx). Costs:
  - Needs `brew install facebook/fb/idb`, macOS 15+ and Xcode 26+ (idb docs, installation.mdx), which is an extra buyer dependency.
  - It leaves the simulator's device-wide `AutomationEnabled` flag on, and mode-asserted reads are about 1.8x slower on large apps (same page).
  - idb is maintained (pushed 2026-10-01). `idb` is installed on this Mac, but its CLI errors on start-up and I did not run it.
- **Android.** `adb -s S exec-out uiautomator dump /dev/tty` (the same code path as Maestro's own dump). **It conflicts:** Android allows one UiAutomation client per device, and Maestro's driver instrumentation holds it for the whole run. A second dump then throws `UiAutomationService ... already registered` (reports: https://github.com/appium/appium/issues/1243 , https://github.com/appium/appium/issues/14763 ; Maestro's driver is `dev.mobile.maestro` instrumentation, MaestroDriverService.kt line ~94). So option B is **not usable on Android** except by speaking Maestro's gRPC `viewHierarchy` RPC (proto in `maestro_android.proto`). That is real work, so B is not viable for Android.
- Verdict for B: iOS-only, extra moving parts. It matters only as a fallback for Maestro < 2.7 on iOS.

**C. Segmenting the flow into separate `maestro test` runs with `maestro hierarchy` between them.** Rejected: it re-pays the driver start per segment, loses app state, and hits the port/lock problem above. [inferred]

`maestro mcp` is the same port problem (issue 3611). Skip.

### 1c. What the hierarchy text can and cannot prove

- **Exact Unicode.** Hebrew, Greek, Armenian, Georgian, Indic, Khmer, Burmese, Hungarian `ő/ű` all compare exactly, so no OCR language list applies. The logical order (not visual) also helps RTL matching. [source + inferred]
- **Covered:** UIKit, SwiftUI, Android Views, Compose `Text`, React Native, WebViews (Android source keeps WebView nodes; iOS 26 Safari view service is walked [source: ViewHierarchyHandler.swift]), and Flutter. For Flutter, `Text` and `TextField` are semantic by default; Flutter text lives in the semantics tree, which can merge several lines into one node, so **split on newlines** (https://docs.maestro.dev/get-started/supported-platform/flutter.md ; node merging is [inferred]).
- **Missing:** text drawn with Canvas/CustomPainter/`drawText`, OpenGL and Unity/Godot game UIs, Lottie, text baked into images, and `ExcludeSemantics`/`importantForAccessibility=no` widgets. For these the hierarchy is empty or sparse, so fall back to OCR for those screens. That includes the "not provable" case today.
- **Wrong but plausible:** the hierarchy proves the app asked for a string, not that it is visible. A truncated label keeps its full text; clipped, overlapped or tofu glyphs (Khmer, Burmese, Amharic with a missing emulator font) all pass. Pair it with a cheap pixel check: ink inside each node's bounds (S once bounds are stored), and keep OCR where it is readable. [inferred]
- **Accessibility labels differ from visible text.** SwiftUI `.accessibilityLabel`, Compose `contentDescription`, and merged parents (https://github.com/mobile-dev-inc/Maestro/issues/2704, open). Match any of `text`, `accessibilityText`, `value`, `title`, `hintText`. This is a known false-positive source if a developer renamed a label, but it still proves the language.
- **Status bar and keyboard.** The iOS runner adds the status bar and the keyboard as extra subtrees. Ignore them (strings like `9:41` match nothing anyway).
- **`check` on existing PNGs** (fastlane, other tools) has **no** hierarchy. It stays OCR-only, so for unreadable scripts the answer there is the Tesseract hook or "not provable". Say so in the README. This feature improves `run`, not `check`.

### 1d. Minimal design

1. `localize_flow()` and `android_flow()`: after every `takeScreenshot` step (scalar form is one line, map form ends after its `path:` line), append the marker above with `label: "shotfleet:hier:<name>"`. The hook sits next to `redirect_screenshot`.
2. Preflight: read `maestro --version`. If below 2.7.0, skip the markers and print "text read from pixels (Maestro < 2.7.0 has no per-step hierarchy)". shotfleet already runs `maestro --version` in doctor [repo: ~1405].
3. After the run: for each flow dir under `.work/debug/attemptN/`, read `commands.json`, find steps whose label starts with `shotfleet:hier:`, load the file under `artifacts`, flatten to `[{"t": str, "id": str, "b": [l,t,r,b]}]`. Drop nodes with zero or off-screen bounds and the status bar. Split text on `\n`. Write `raw/<lp>/<name>.hier.json`.
4. `cmd_check`: if `<name>.hier.json` sits next to the PNG, use it. `judge_screen(lp, ocr, tables, hier=None)`: `lines = {norm(s) for s in hier strings}`; score exactly as today (exact line plus format regex). If hierarchy has at least 3 text nodes it supersedes the `ocr["lang"]`/`SCRIPTS` branch; when `best < 2` and hierarchy is rich, return "not provable" instead of guessing from language detection. This also removes the Hebrew/Burmese `chars == 0` false alarm in the current code (the `no text found` branch fires before `readable_languages()`).
5. `check.json` and the HTML report: add `evidence: "hierarchy" | "ocr"` per screenshot, so the user sees how each language was proven.
6. Test: a canned `screen-hierarchy` JSON fixture (iOS and Android shape, Hebrew/Greek) plus the existing `tests/` style; no simulator needed.

### 1e. Failure modes

- `assertTrue` marker not warned-through (YAML shape, label with `:`, version quirk): no hierarchy files, so fall back to OCR and note it. **Experiment: 2-step flow on one sim, then `ls <debug>/<flow>/screen-hierarchy` and read `commands.json`.**
- Upgrading Maestro 2.0.10 to 2.7+ changes the debug-output layout (`logs/maestro.log` is now inside each flow dir; `flow_devices()` uses `rglob("maestro.log")` so it should survive), adds a PNG per step, and in 2.6.0 changed parallel iOS handling. Re-run the whole suite on the new version before shipping. [inferred from changelog]
- Hierarchy taken about 1 s after the screenshot can differ if the screen animates. A spinner or ticking timer shows up as a changed string; compare only table matches, not the whole tree.
- Large iOS trees: the runner has a recovery path for `kAXErrorIllegalArgument` and `kAXErrorInvalidUIElement` [source: ViewHierarchyHandler.swift], and idb truncates at depth 50 / 3000 nodes.

### 1f. Experiment result, 2026-10-04: yes, on one emulator with Maestro 2.11.0 (run, not source reading)

**Question** (handoff item 7): can the UI hierarchy be read during a sharded run without hanging it (2.0.10's `maestro hierarchy` broke sharded runs)?
**Answer: yes through the in-run marker (1b A); no through `maestro hierarchy` from outside.** Evidence is in `research/experiments-2026-10-04/A/`.

Setup: Maestro 2.11.0 (`cli-2.11.0` release zip, unpacked in a scratch folder, Java home pointed at scratch with `-Duser.home` so `~/.maestro` was not
touched: listing and mtime identical before and after). One read-only copy of the `shotfleet_android` AVD (Android 16, arm64) on port 5760, booted from
its snapshot. App: the fixture APK (`com.shotfleet.fixture`, `tools/fixture-app-android/build.sh`) with the app language set to Japanese by
`adb shell cmd locale set-app-locales com.shotfleet.fixture --locales ja`. Both runs used `maestro --device emulator-5760 test --shard-all 1
--debug-output <dir> <flow>`, so they were sharded runs of one shard on one device.

The flow (`A/flow-control.yaml`): `launchApp`, `takeScreenshot: shots-control/01_welcome`, the marker (`assertTrue: {condition: ${false}, label:
"shotfleet:hier:01_welcome", optional: true}`), `tapOn: "次へ"`, `takeScreenshot` again, the marker again.

| Run | What happened | Result |
|---|---|---|
| control (markers only) | both markers reported `WARNED`, the flow carried on | `rc=0`, 16 s. `screen-hierarchy/step-005-assertCondition.json` and `step-008-...json` written; `commands.json` lists each as a `SCREEN_HIERARCHY` artifact of the step labelled `shotfleet:hier:<name>`. Marker cost per `commands.json`: 1178 ms for the first, 77 ms for the second. |
| probe (a 40 s `extendedWaitUntil` step, `optional: true`, in the middle; `maestro --device emulator-5760 hierarchy` started 17 s into the run, while that step was waiting) | the sharded run was **not hung**: it finished with `rc=0` in 54 s, the tap, the second screenshot and the second marker all ran | `maestro hierarchy` itself failed fast with `rc=1`: `Device server died during 'deviceInfo' on emulator-5760 ... StatusRuntimeException: UNAVAILABLE` (`A/probe-hierarchy.err`). It ended before the 25 s check, so nothing had to be killed. It returned no hierarchy. |

One text file per screenshot (`A/extract.py` pairs each marker label with the `takeScreenshot` before it and flattens `text`, `accessibilityText`, `hintText`
of every node; `A/results/<run>/<name>.txt`). The Japanese is exact, not OCR:

```
01_welcome.txt   ようこそ / あなたのスクリーンショットを、すべての言語で。 / 次へ   (then the status bar: 2:40, "T-Mobile, three bars.", "Battery charging, 100 percent.")
02_settings.txt  設定 / アプリの見た目と音を選びます。 / 完了                       (same status-bar lines)
```

What this does not show: only one emulator and one shard (not two shards on two emulators at the same time), one app with two screens, one run of each.
The 2.0.10 hang was not re-run here (the claim about it stays the 2026-10-01 measurement noted in `android_flow`). Status-bar nodes (time, signal, battery) are in
the text and must be dropped before matching. The same mechanism also fired for the optional 40 s wait step (it ended `WARNED`, so it saved a hierarchy too),
which confirms any warned step saves one. Side finding for the Maestro 2.11 work: with `--debug-output` set, the relative `takeScreenshot` path ended up
under `<debug>/<flow>/takeScreenshot/shots-control/01_welcome.png`, not in the working directory.

**Not implemented in shotfleet.** `android_flow` still carries no markers and Android screenshots are still checked with OCR only; nothing in the README or the
site changes. Next step if wanted: section 1d, Effort M, now with the trick confirmed.

Effort: **M** (about 3 to 5 days with fixtures and the experiment).

---

## 2. Per-locale values for text typed with `inputText`

### Verdict: feasible now. Effort S. Android non-ASCII needs Maestro >= 2.7.0; iOS non-ASCII needs an experiment per script.

### 2a. Maestro side [source/docs]

- Flow header `env:` defines variables, and `${NAME}` substitutes them. A header `env:` block with `${...}` use is documented (https://docs.maestro.dev/maestro-flows/flow-control-and-logic/permissions.md , example with `env:` + `${CAMERA_PERMISSION_STATE}`), and `inputText` takes `${...}` (https://docs.maestro.dev/reference/commands-available/inputtext.md). `YamlConfig.env` exists (https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-orchestra/src/main/java/maestro/orchestra/yaml/YamlConfig.kt).
- Values are bound as **JS variables** (`GraalJsEngine.putEnv` -> `envBinding[key] = value`), not pasted into script text, so quotes or `${` in a value cannot break a flow. Names must be valid JS identifiers.
- `-e NAME=value` on the CLI cannot work for shotfleet: it runs **one** `maestro test` over many per-locale flows (`--shard-split`), so a CLI value would be the same for every flow. Put the values in each **per-locale flow's header**, which shotfleet already writes (`localize_flow`, `android_flow`).

### 2b. `inputText` and non-Latin text

| Platform | Behaviour | Evidence |
|---|---|---|
| iOS | Text goes through the XCTest runner as one synthesized text event (first character slow, rest at 30 cps). Unicode supported since January 2023 (`isUnicodeInputSupported() = true`), independent of the keyboard layout. | [source] https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-ios-xctest-runner/maestro-driver-iosUITests/Routes/Helpers/TextInputHelper.swift ; IOSDriver.kt ; PR https://github.com/mobile-dev-inc/Maestro/pull/603 ; issue https://github.com/mobile-dev-inc/Maestro/issues/146 (2023-01-30 comment) |
| Android, Maestro **< 2.7.0** (this Mac: 2.0.10) | **Hard error** `UnicodeNotSupportedError` for any non-ASCII text (`isUnicodeInputSupported() = false` plus the guard in `Orchestra.inputTextCommand`). | [source] tag `cli-2.0.10`, Orchestra.kt ~1027 ; the docs page still says "Unicode characters are not supported on Android" and is stale |
| Android, Maestro **>= 2.7.0** | First-party IME. For non-ASCII, `AndroidDriver` enables a Maestro-owned IME, commits Base64-encoded UTF-8 chunks by `am broadcast`, then restores your IME. PR tested Arabic, CJK, Hangul, emoji and mixed scripts into a native field. ASCII still goes character by character with a 75 ms sleep. | [source] AndroidDriver.kt `inputUnicodeText` ~1447 ; MaestroDriverService.kt `inputText` ; PR https://github.com/mobile-dev-inc/Maestro/pull/3211 (merged 2026-07-01) ; issue 146 closed 2026-07-01 |

Known rough edges (not fixed):
- Characters dropped or repeated on laggy apps: https://github.com/mobile-dev-inc/Maestro/issues/395 (closed), https://github.com/mobile-dev-inc/Maestro/issues/2005 (open).
- Slow on Android 16: https://github.com/mobile-dev-inc/Maestro/issues/2718.
- Texts over about 1600 chars time out: https://github.com/mobile-dev-inc/Maestro/issues/3638.
- Pasting is not available: https://github.com/mobile-dev-inc/Maestro/issues/3640.
- Text fields' own autocorrect, auto-capitalise and predictive text still apply, as with English demo text.

**[unverified]:** on an iOS simulator whether CJK, Arabic, Hebrew and emoji reach the field intact when the simulator's active keyboard is not that script; and on Android < 13 emulators (shotfleet needs API 33+ anyway, so fine). One 5-step flow per script would settle it.

### 2c. Design (about 40 lines)

Config (shared by iOS and Android, since the flow is shared):

```toml
[inputs]                 # default for every language
name = "Alex"
city = "Berlin"

[inputs.de]              # language, or a full code (pt-BR, zh-Hans)
name = "Jonas"
[inputs.ja]
name = "太郎"
city = "東京"
```

or the same in a file `inputs.toml` that translators can edit (`inputs = "inputs.toml"` in the section).

Flow: `- inputText: ${name}` and, to prove it in a check, `- assertVisible: "${name}"`.

Steps:
1. Resolve per locale: exact code, then language (`pt-BR` -> `pt`), then `[inputs]`. A variable used in the flow with no default is a **setup error** (message: variable `name` has no value for `de`).
2. Emit into the per-locale flow header as a `env:` block, quoting each value with `json.dumps(v, ensure_ascii=False)` (a valid YAML double-quoted scalar) and validating names against `^[A-Za-z_]\w*$`. Write flow files with `encoding="utf-8"` explicitly (today `write_text` uses the default; fine on macOS, but cheap to make explicit). [repo: ~869, ~1062]
3. `translate_flow` must **skip selector lines containing `${`**: today `tapOn: ${x}` or `assertVisible: "${name}"` is looked up as an English label and reported under "selectors not found in the app's strings". Likewise the map form `- inputText:\n    text: "..."` matches `SELECTOR_KEYS` (`text` is a key), so a typed demo string equal to an app string would get "translated". Skip lines whose parent step is `inputText`, or at minimum report-only. [repo: `SELECTOR_KEYS`, `SELECTOR_RE` ~156, ~495]
4. Preflight: on Android with a non-ASCII value and Maestro < 2.7.0, **fail early** with "typing non-Latin text on Android needs Maestro 2.7 or newer (you have 2.0.10)", instead of failing mid-run on 30 emulators.

Not worth building: auto-translating typed text from the app's own strings (no source for demo names/addresses). Treat typed text as the buyer's data.

Effort: **S** (half a day plus a fixture test for the env block, fallback chain and `${` skip).

---

## 3. `launchApp` options on iOS (`permissions`, `arguments`, `clearState`)

### Verdict: feasible now, safe, effort S. This is a pure flow-rewrite change; no Maestro experiment is needed beyond one smoke run.

### 3a. What Maestro does [source]

- A bare `- launchApp` runs `setPermissions(appId, all: allow)` then launches with launch arguments. "For testing convenience, default to allow all on app launch" (Orchestra.kt `launchAppCommand`, line ~1311). **So shotfleet's bare launch already grants every permission it can; `permissions:` is only needed to deny or leave unset.**
- Order inside `launchApp`: `clearKeychain` -> `clearState` -> `setPermissions` -> launch. On iOS Simulator, `clearState` is terminate + **reinstall** (LocalSimulatorUtils.kt `clearAppState`), then permissions are applied host-side by `applesimutils` and `xcrun simctl privacy` (SimctlIOSDevice.kt `setPermissions`). Neither touches the app's language, which is carried by the launch arguments `-AppleLanguages (xx)`, `-AppleLocale` (IOSLaunchArguments.kt makes them `-key value`). **So honouring `clearState: true` is safe on iOS**, unlike Android where it wipes the per-app locale and shotfleet deliberately strips it [repo: android_flow].
- Option names (https://docs.maestro.dev/reference/commands-available/launchapp.md): `appId`, `clearState`, `clearKeychain`, `stopApp`, `permissions`, `arguments`. Permission names and values: `all|camera|location|photos|notifications|...` with `allow|deny|unset` (https://docs.maestro.dev/maestro-flows/flow-control-and-logic/permissions.md).
- A top-level `- setPermissions:` step needs no special handling and already passes through `localize_flow` unchanged [repo]. A following bare `launchApp` resets everything to `all: allow`.

### 3b. Two gotchas

- **Notifications on iOS are never pre-granted silently** [docs permissions.md: "iOS does not grant notification permissions silently"]. Maestro's runner taps "Allow" itself only if the dialog text contains the **English** phrase "Would Like to Send You Notifications" (PermissionButtonFinder.swift `notificationsPermissionLabel`), and it looks for buttons labelled `allow`/`continue` or `don't allow`/`cancel` (lowercase English), with a positional fallback (second button) after that. In every other language the dialog is **not** recognised, so it can sit on top of the screenshot. shotfleet already translates system alert strings (`system_strings(root)`, `README` tip, `shotfleet.py` ~852), so the working recipe is an optional translated tap: `- tapOn: {text: "Allow", optional: true}`. [source + repo]
- `permissions:` values can contain variables (`${CAMERA}`) since 2.8.0, which can feed from the `[inputs]` table of section 2 for free.

### 3c. Design in `localize_flow` (about 30 lines)

Today any `- launchApp:` map form raises `ValueError`. Instead:
1. Parse the step's indented block (until the next `- ` at the same indent). Accept keys `clearState`, `clearKeychain`, `stopApp`, `permissions` (nested map, copy lines verbatim and re-indent) and `arguments` (nested map).
2. Emit shotfleet's own block first (`clearState: true` on the first launch, `arguments:` with `AppleLanguages`/`AppleLocale`), then merge. **shotfleet's `AppleLanguages`/`AppleLocale` win.** If the user sets those keys, say so ("launchApp arguments `AppleLanguages` conflict with `locales`"). User `clearState` overrides ours on later launches. User arguments are appended.
3. Reject a different `appId` (the header's `appId` is per-build, and shotfleet writes it).
4. Keep rejecting anything else with the key named, e.g. "launchApp: `foo` isn't supported".
5. Android `android_flow` already passes the map form through (it only strips `clearState:`), so the same flow works there. Only the first-launch rule differs.
6. Test: a pure-function test on `localize_flow` for 5 shapes (bare, `clearState` only, `permissions` all+camera deny, `arguments` merge, conflicting AppleLanguages). No simulator needed, plus one smoke run later.

README: delete the "On iOS, launchApp with options isn't supported yet" line and the matching `ValueError`.

Risks: `clearState: true` mid-flow reinstalls the app (about 2 to 5 s, resets data), which is what the user asked for; `clearKeychain` clears the whole simulator keychain, which is fine because shotfleet owns its simulators.

Effort: **S** (about half a day with tests).

---

## Verified versus inferred, in one list

**Verified by reading primary source (not run):**
- The per-step hierarchy files exist only from Maestro 2.7.0 and only for failed or warned steps.
- Optional failures are "Warned" and the flow passes.
- `assertTrue` supports `optional` and `label`.
- iOS and Android attribute mappings.
- The XCTest runner routes and request shape.
- The runner port is random per shard in 2.11 (it was already shuffled, 7001-7128 per shard, in 2.0.10).
- Maestro's JS has no screen access.
- `launchApp` defaults to `all: allow`.
- Order: `clearState` -> permissions -> launch.
- iOS `clearState` is a reinstall.
- Android non-ASCII is a hard error before 2.7.0 and an IME path after.
- The English-only notification auto-tap.
- idb's documented behaviour and costs.

**Inferred (needs the experiment):**
- Cost per call. The "~1 s" figure is Maestro's own code comment, not measured.
- That the marker pair produces exactly one file per screenshot and `commands.json` lists it under `artifacts`.
- Flutter node merging.
- Truncated labels carrying the full string.
- That an upgrade from Maestro 2.0.10 keeps shotfleet's other assumptions (debug layout, shard log line, JUnit) intact.

**Not checked at all:** iOS typing of CJK, Arabic, Hebrew and emoji on a simulator; Compose and Flutter apps' actual attribute content; a real Android run with the marker.

---

## Ranked recommendation (small paid CLI, buyers ship 10+ languages)

1. **Build #3 first (launchApp options on iOS), about half a day.** `- launchApp: {clearState: true}` is the most common Maestro idiom, and today shotfleet stops with an error on the very first run. That is onboarding friction for every iOS buyer, the fix is certain (pure rewrite, tested without a simulator), and it also unlocks `permissions: {all: deny}` for empty-state shots. Remove the README limit.
2. **Then #2 (per-locale `[inputs]`), about half a day.** It makes every store listing look native instead of "Alex" in Japanese, with a certain, low-risk design. Gate Android non-ASCII on a Maestro >= 2.7 preflight. Run one iOS script experiment (CJK/Arabic/emoji) before claiming support.
3. **Then #1 (hierarchy evidence), M, but run the 10-minute marker experiment this week** to de-risk it (needs Maestro upgraded to >= 2.7.0, which I could not do). It is the only fix that makes every script provable, so it is the differentiator for buyers with Greek, Hebrew, Georgian or Indic languages. But it needs a Maestro version bump with a re-validation of the whole suite, helps `run` and not `check`, and cannot see Canvas/game text. Do the cheap diacritic and digit normalisation from `research/all-languages.md` (A4) before this; it fixes Hungarian and Persian in about 40 lines and covers the most common non-listed Latin languages.
4. Not worth building now: Android `uiautomator dump` or an out-of-run iOS barrier (conflicts with Maestro's UiAutomation on Android; port discovery and an idb dependency on iOS), and auto-translating typed text.
