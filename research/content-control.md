# Content control: can shotfleet decide WHAT the app shows?

Research date 2026-10-02. Read-only: no simulator, emulator or Maestro was run, nothing was installed, no repo was edited, nothing committed. The owner's other apps were only read.

Evidence tags:
- **[repo]** = read in shotfleet (file:line on branch `claude/integrate-on-main`).
- **[app]** = read in one of the owner's apps (path given).
- **[docs]** = from a page I fetched this session (URL given; some pages were read through a summarizer, flagged "summarized").
- **[source]** = read in Maestro `main` on GitHub (the Mac has Maestro 2.0.10, `main` is newer; behaviour on 2.0.10 is unverified).
- **[inferred]** = my reasoning. **[unverified]** = needs an experiment or a source I did not reach.

## 0. The answer in ten lines

1. shotfleet today controls the language, the status bar, permissions, fresh state, typed text (iOS only) and the launch arguments of the app. It does **not** control data: it cannot seed a database, return fixture JSON, change a backend, set the date, or log in.
2. Every real indie app in this repo's neighbourhood solves "what is on screen" **inside the app**, behind a DEBUG-only switch: Remoti's `-UITEST_SEED_DEMO_CONTENT` (iOS) and `debug.remoti.demo` system property (Android), Cairn's `CAIRN_DEMO_SEED` env var, Stressi's `debug_screenshot_mode` default and system property. That is also what fastlane snapshot and simshot assume.
3. So the right design for shotfleet is not "seed the data for you" but "make the app's own screenshot mode easy to drive, in every language, on both platforms, and prove it worked". The app owns the data; shotfleet owns the matrix (language x device x state) and the verification.
4. iOS already works for that today, with no code change, through `launchApp: arguments:` (merged by `localize_flow`, shotfleet.py:771-778). Two traps: Maestro drops the dash for YAML booleans, and Maestro cannot pass launch **environment** variables (Cairn's style).
5. Android is the gap: there is no way to run a shell command on each emulator after boot or after shotfleet's `pm clear` (shotfleet.py:1373-1375), and the app-side switches the owner uses on Android are system properties or SharedPreferences, which Maestro launch arguments (intent extras) cannot set in time.
6. Cheapest high-value fixes: (a) a documented "screenshot mode contract" plus recipes, (b) `[android] shell` / `[ios] simctl` setup commands per device with `$SHOTFLEET_SERIAL` / `$SHOTFLEET_UDID`, (c) per-device values through a generated JS map keyed by `MAESTRO_DEVICE_UDID` (fixes the Android `[inputs.<locale>]` limit), (d) `[expect]`, a content check that fails when the seeded content is missing (empty-state screenshots are the real risk of any seeding scheme).
7. Heavier ideas (a local mock server, container file seeding on iOS, AI-generated fixtures) are possible but each needs the app to cooperate anyway; build them only when buyers ask.
8. AnywhereRoles (the `remoti` repo): iOS works with shotfleet today, with zero shotfleet changes, using his existing `-UITEST_*` flags; Android needs feature (b). It would give him real localized UI instead of "English app + translated caption", which is what his pipeline ships now. It is not better than his setup for English-only screenshots.
9. Product: content control makes shotfleet more credible, not obviously more profitable. It widens who can succeed with the product, and the check (`[expect]`) is a differentiator nobody has. Recommendation: build the contract doc + Android/iOS setup commands + `[expect]` next (about 4 days), the rest later or never.
10. My earlier advice to the owner ("do not use shotfleet for AnywhereRoles, the UI tests already seed the data") was too strong. The seeding lives in the app, not in the UI tests. See section 5.

---

## 1. What shotfleet controls today

### 1.1 Table

| Control | What it does | Where | Platforms |
|---|---|---|---|
| Maestro flow steps | The user's flow is passed through. Only lines using selector keys (`tapOn`, `assertVisible`, ...) are rewritten to match any translation; everything else (`inputText`, `scroll`, `openLink`, `runScript`, `runFlow`, `setLocation`, `addMedia`, ...) is passed through verbatim | `SELECTOR_KEYS` shotfleet.py:189, `SELECTOR_RE` :590, `translate_flow` :627 | both |
| `launchApp:` options | A block under `- launchApp:` is parsed: `clearState`, `permissions`, `arguments` and other keys are kept. shotfleet adds `clearState: true` to the first launch and appends its own `AppleLanguages` / `AppleLocale` under `arguments:`. User arguments are kept. Inline `{ ... }` is refused | `localize_flow` :760-803, `launch()` :771-778; test `test_launch_app_options_are_kept_and_merged` tests/test_shotfleet.py:87 | iOS |
| Same on Android | `android_flow` keeps the flow, adds a bare `- launchApp` if the first step is not one, and **deletes every `clearState:` line**. Other options (arguments = intent extras, permissions) pass through | :1310-1323 | Android |
| Fresh state per language | iOS: Maestro `clearState` = uninstall and reinstall (Maestro source, see limits-text.md 3a), plus a host-side uninstall/install before each batch. Android: `adb shell pm clear <pkg>` per emulator per round | iOS :1096-1100; Android :1373 | both |
| Language | iOS: launch arguments `-AppleLanguages (xx)` and `-AppleLocale <store locale, e.g. de_DE, zh_CN>` so number and date formats follow the store locale. Android: `cmd locale set-app-locales <pkg> --locales <lp>` after `pm clear` | iOS :765-769; Android :1374 | both |
| Permissions | iOS: whatever the user wrote under `permissions:`; a bare Maestro `launchApp` already grants all (limits-text.md 3a, [source]). Android: `adb install -r -g` grants all at install | :1366 | both |
| `[inputs]` | `[inputs]` defaults and `[inputs.<locale>]` (exact code, then the language part) become `env:` entries in each per-locale flow header; the flow writes `inputText: ${name}`. The values are JSON-quoted | `inputs_for` :742, `with_env` :750, call at :1084; validation :57-60 | iOS per language. **Android: defaults only**, with a printed note (:1344-1345, :1380) |
| `[overrides.<locale>]` | Replaces what shotfleet would tap for one language (label to literal or `re:` regex) | `check_tables` :61-63, passed to `translate_flow` at :1081, :1352 | both |
| Hooks | `before_run`, `after_run`, `before_export`, `after_export`, run by `/bin/sh` in the config's folder with `SHOTFLEET_EVENT/_VERSION/_CONFIG/_PLATFORM/_OUT/_BUNDLE_ID/_LOCALES`; `after_run` also `_EXIT/_PROBLEMS/_REPORT`. `before_run` runs **before** simulators or emulators boot (`run_platform` :1006-1012 calls the hook, then `capture_platform`) | `run_hook` :989-1003 | both |
| iOS status bar | After boot: `simctl status_bar <udid> override --time 9:41 --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100`. It is set once per simulator, not per language | `make_pool` :849-851 | iOS |
| Android demo mode | `DEMO_MODE` list: `sysui_demo_allowed 1`, then `am broadcast -a com.android.systemui.demo` commands for enter, clock 0941, battery 100 unplugged, wifi shown level 4, mobile hidden, notifications hidden. Applied after boot and again before every round "because SystemUI can drop it" | :1231-1239; applied :1308, :1375 | Android |
| Device size | `device_type(s)` / `devices` (phone, tablet) | README Config | both |
| Text reading | iOS: reads the screen's text from Maestro's runner during the run (`capture_texts` :882), saves `<shot>.texts.json`; `check` prefers it to OCR (`screen_text` :1629). Android: OCR only (comment in `android_flow`) | | |

### 1.2 What the table adds up to

- shotfleet **is** a launch-argument and flow-step driver plus a language matrix. Because user `arguments:` survive on iOS, an app that reads a launch argument for a screenshot mode (Remoti, Stressi, fastlane-style `-FASTLANE_SNAPSHOT`) works today.
- Everything that happens before the app launches on a device (seed files, `setprop`, `simctl ui appearance dark`, push, location, media) is outside shotfleet's reach: there is no per-device hook, and `before_run` is too early (devices do not exist yet) and `after_run` too late.
- State is wiped by shotfleet on purpose, which is good for reproducibility and bad for anything seeded earlier than the launch (Android `pm clear` at :1373 removes files you pushed before it).

### 1.3 Two Maestro facts that decide a lot

- **Argument encoding.** `toIOSLaunchArguments`: for a **Boolean** value the key is kept as written (no dash added); for any other value the key gets a `-` prefix if it has none; the result is `[key, value.toString()]` pairs. So `UITEST_MODE: true` produces the bare token `UITEST_MODE true`, not `-UITEST_MODE true`. Write `UITEST_MODE: "1"` (string, gets the dash) or `"-UITEST_MODE": true`. [source: https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-ios-driver/src/main/kotlin/util/IOSLaunchArguments.kt]. The apps read `ProcessInfo.processInfo.arguments.contains("-UITEST_MODE")` (Remoti, remotiApp.swift:973), so the dash matters. Whether 2.0.10 encodes the same way is [unverified].
- **No launch environment.** `YamlLaunchApp` has exactly `appId, clearState, clearKeychain, stopApp, permissions, arguments, label, optional` [source: https://github.com/mobile-dev-inc/Maestro/blob/main/maestro-orchestra/src/main/java/maestro/orchestra/yaml/YamlLaunchApp.kt]. The docs say iOS arguments land in `ProcessInfo.processInfo.arguments` and `UserDefaults`, Android arguments arrive in `intent.extras` [docs: https://docs.maestro.dev/reference/commands-available/launchapp.md]. A web search summary mentioned a `launchEnvironment` option, but that appears to belong to a third-party reimplementation (maestro-runner), and I could not load its changelog [unverified, do not rely on it].

---

## 2. How apps get their content for screenshots, and how common approaches seed it

For each: what it is, whether it works with shotfleet today, and a source.

### 2.1 App-side screenshot mode (the dominant pattern)

| Variant | Real example | Works with shotfleet today? |
|---|---|---|
| iOS launch arguments read from `ProcessInfo.arguments` / `UserDefaults` | Remoti: `-UITEST_MODE -UITEST_RESET_PERSISTENCE -UITEST_SKIP_ONBOARDING -UITEST_SEED_DEMO_CONTENT ...` [app: remoti/iosApp/remotiUITests/remotiUITests.swift:673-697, remoti/iosApp/remoti/remotiApp.swift:953-1034]. Stressi: `UserDefaults.standard.bool(forKey: "debug_screenshot_mode")` and `debug_screenshot_slide` [app: Stressi/iosApp/iosApp/ContentView.swift:13-18]. HackerNewsKMP: `-ui_testing -show_for_you_fixture` [app: HackerNewsKMP/iosApp/KuokkaUITests/KuokkaUITests.swift:48-95, 370]. fastlane itself adds `-FASTLANE_SNAPSHOT YES` and documents "launch arguments" in the Snapfile [docs: https://docs.fastlane.tools/actions/snapshot/]. | **Yes**, through `launchApp: arguments:` (use string values). |
| iOS **environment variables** | Cairn: `CAIRN_DEMO_SEED=1`, `CAIRN_DEMO_SCREEN=...`, set with `app.launchEnvironment` in UI tests and `SIMCTL_CHILD_CAIRN_DEMO_SEED=1 xcrun simctl launch ...` in its capture script [app: Cairn/UITests/FeatureTourTests.swift:17-21, Cairn/Scripts/capture-screenshots.sh:36-41, Cairn/Sources/App/DemoSeed.swift:17]. | **No.** Maestro cannot pass env (section 1.3). Fix on the app side: also accept `-CAIRN_DEMO_SEED 1` (one line). |
| Android system property read via reflection | Remoti: `adb shell setprop debug.remoti.demo 1` after `pm clear`, then start the activity; seeds Room and DataStore, swaps Koin bindings for fakes [app: remoti/androidApp/src/debug/java/me/manulorenzo/remoti/demo/DemoMode.kt, header comment]. Stressi: `debug.stressi.screenshot`, `debug.stressi.slide`, or SharedPreferences `stressi_debug` [app: Stressi/androidApp/src/main/java/me/manulorenzo/stressi/DebugMode.kt]. The release source set carries a no-op twin (remoti/androidApp/src/release/.../DemoMode.kt). | **No** (needs a per-device `setprop` that shotfleet cannot run). |
| Android intent extras | The only thing Maestro `arguments:` can send on Android [docs, above]. Koin/DI usually starts in `Application.onCreate`, before any intent is visible, which is why Remoti chose a system property (its own comment says so). | Only for apps that read extras in the Activity. |
| Compose/SwiftUI "screenshot mode" that renders marketing slides | Stressi's `ScreenshotShowcaseView` / `ScreenshotShowcaseScreen`: headline and subhead come from `NSLocalizedString`, so per-language text is free [app: Stressi/iosApp/iosApp/Views/ScreenshotShowcaseView.swift:1-40]. | Yes on iOS; Android needs the property. |
| Per-language demo data computed inside the app | Cairn `DemoSeed.pinnedArticle` picks a Wikipedia article by `Locale.preferredLanguages.first` ("Steinmaennchen" for de, "Moledro" for pt...) [app: Cairn/Sources/App/DemoSeed.swift:81-102]. | Yes: shotfleet's `-AppleLanguages` is exactly what that reads. This is the cleanest per-locale content story: **the app localizes its own demo data from the language it is launched in**. |

Compiled-out-of-release is the convention (`#if DEBUG`, `BuildConfig.DEBUG`, a release no-op twin). shotfleet already requires Debug simulator builds / debug APKs, so this is compatible [repo: README "init", load_config :144-147].

### 2.2 Deep links and URL schemes

- Maestro `openLink` takes `link`; Android has `autoVerify` and `browser`; **iOS may show a one-time security confirmation dialog the first time an app is opened from a deep link, a permanent choice per Simulator that survives clearing app state** [docs: https://docs.maestro.dev/reference/commands-available/openlink.md]. shotfleet's simulators are persistent and reused (`shotfleet-1..N`, make_pool :830-847), so the dialog appears once per simulator; a flow must tap it optionally.
- Good for "jump to screen X" and for apps that have a debug deep link to seed (`myapp://debug/seed?...`). Works today, no shotfleet change; `openLink` is not touched by `translate_flow`.
- Cairn's `CAIRN_OPEN_URL` hook and `CAIRN_DEMO_SCREEN` are the same idea through env [app: Cairn/Scripts/compat-pass.sh:41].

### 2.3 Maestro `runScript`, `evalScript`, `runFlow`, env

- `runScript` runs a JS file, takes `env:`, can set `output.x`; HTTP is available as `http.get/post/put/delete/request` [docs: https://docs.maestro.dev/reference/commands-available/runscript.md, https://docs.maestro.dev/maestro-flows/javascript/make-http-requests.md]. The JS cannot read the screen or run shell commands (limits-text.md 1a, [source]).
- Built-in variables include `MAESTRO_FILENAME`, `MAESTRO_DEVICE_UDID`, `MAESTRO_SHARD_ID`, `MAESTRO_SHARD_INDEX` [docs: https://docs.maestro.dev/maestro-flows/flow-control-and-logic/parameters-and-constants, summarized]. `MAESTRO_DEVICE_UDID` is the key to per-device content in a sharded run (section 4, F4). Which exact string it is on Android (adb serial?) and on 2.0.10 is [unverified].
- `runFlow` with `env:` runs a sub-flow with variables: useful for reusing a "log in with test account" snippet. Untouched by shotfleet.
- A synchronous `http.get` from a flow can call a local server on the Mac, which is how a flow could ask the host to do things (seed, reset) at an exact moment; blocking is [source] in limits-text.md 1a.

### 2.4 Preloaded container data

- iOS: `xcrun simctl get_app_container <udid> <bundle> data` prints the data container path [docs: `xcrun simctl help get_app_container`, run locally, read-only]. Copy files in while the app is not running, after install and before launch. `xcrun simctl spawn <udid> defaults write <bundle> key -bool YES` sets a UserDefaults key from outside (Cairn does this for `hasSeenWelcome`, Cairn/Scripts/capture-screenshots.sh:39).
- Android: `adb push` to `/data/local/tmp`, then `adb shell run-as <pkg> cp ...` into the app's private dir. `run-as` works only for debuggable apps [inferred from the Android docs; page not fetched this session: unverified]. shotfleet's `pm clear` at shotfleet.py:1373 must run **before** the push.
- Interposition problem on iOS: Maestro's `clearState` inside the flow reinstalls the app at flow time, and all locales run in **one** sharded `maestro test` process (shotfleet.py:1105-1112), so shotfleet cannot run host commands between "clear" and "launch" of a given locale. Only a flow-initiated host call (an HTTP barrier, section 4 F5) can. On Android shotfleet owns the rounds, so it can.
- Brittleness: copying a prebuilt SwiftData / Core Data / Room database ties the fixture to one schema version; every app migration breaks it. App-side seeding code (Remoti, Cairn) avoids this.

### 2.5 Seeded databases (SwiftData, Core Data, Room)

- Remoti seeds Room through its own bridge on launch under `-UITEST_SEED_DEMO_CONTENT` (remotiApp.swift:1114-1200) and Android seeds `JobsDao` once into an empty catalog (hence `pm clear`) [app: DemoMode.kt `seed`]. Cairn "wipes whatever is there and writes the demo state" with SwiftData at launch [app: DemoSeed.swift:104-106].
- Rule of thumb for shotfleet: **never** seed the database from outside; trigger the app's own seeding.

### 2.6 Mock servers, network stubbing, proxies

- Local HTTP mock (WireMock, `python -m http.server`, Prism): the app needs a configurable base URL. iOS simulator shares the Mac's network stack, so `http://localhost:PORT` reaches the host. Android emulator reaches the host at `10.0.2.2`; `127.0.0.1` is the emulator itself [docs: https://developer.android.com/studio/run/emulator-networking, summarized: the alias table itself did not load; this is the well-known behaviour].
- Cleartext: apps targeting Android 9+ block plain HTTP by default [docs: https://developer.android.com/privacy-and-security/security-config]; iOS ATS applies to localhost too and `NSAllowsLocalNetworking` exempts local networking [docs: https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nsallowslocalnetworking, summarized, thin page]. So a debug build must opt in on both platforms.
- Per-locale mock: all emulators hit the same host, so the server cannot tell which language is asking unless the URL carries it (iOS: a per-locale launch argument; Android: a per-emulator `adb reverse` to a per-locale host port, [inferred, `adb reverse` not verified this session]).
- Proxy approaches (mitmproxy/Charles map-local): need a system proxy and, for HTTPS, a trusted CA. iOS simulator follows the Mac's system proxy [inferred], which means changing the user's Mac network settings: against shotfleet's "no surprises" philosophy. Android emulators accept `-http-proxy` [inferred] and a user CA is not trusted by apps targeting Android 7+ unless the debug build says so (the `debug-overrides` page above shows the mechanism). Not recommended as a shotfleet feature.
- Firebase emulators: a `before_run` hook can start `firebase emulators:start` and the app needs a debug switch pointing at host/localhost (`10.0.2.2` on Android). [unverified: I did not read Firebase docs.] Data is global, not per language.
- fastlane ecosystem equivalent: none built in; people use launch arguments plus an in-app fixture repository (HackerNewsKMP `-show_for_you_fixture`).

### 2.7 Test accounts, `clearState`, keychain

- Logged-in state is either (a) a debug flag that bypasses auth (Remoti `-UITEST_SKIP_ONBOARDING`, Android `DemoAuthRepository` [app: DemoMode.kt `demoModule`]), (b) real credentials typed by the flow (`inputText` with `[inputs]` or `-e`), or (c) HackerNewsKMP style fixture credentials from the environment (`HNProtectedFlowFixture.fromEnvironment()`).
- Interaction with shotfleet's "fresh state per language": every language starts from a clean install, so a login must be part of every flow or flag. That is correct for screenshots but slow if login is a network call. Keychain: `clearKeychain` is iOS-only [docs: https://docs.maestro.dev/reference/commands-available/clearkeychain.md]; `simctl keychain reset` exists [docs: `xcrun simctl help keychain`].
- Credentials in a flow file end up in the repo: use `[inputs]` from the environment or a gitignored config. Never print them (shotfleet's hook output goes to stderr).

### 2.8 Feature flags

Remoti's `-UITEST_FORCED_FREE_PRO_FEATURES SALARY_INSIGHTS,ADVANCED_FILTERS` stands in for a Remote Config value [app: remoti/iosApp/remoti/Utilities/RemoteFeatureFlags.swift:43-48]. Same mechanism as 2.1; works as a launch argument with a string value.

### 2.9 StoreKit, billing, subscriptions, paywall

- Real paywall prices on a simulator need StoreKit testing; a StoreKit configuration file is selected in an Xcode scheme, which a plain `maestro test` run does not use [inferred, not verified this session]. Remoti avoids it with `-UITEST_GRANT_PRO` and `-UITEST_SHOW_PAYWALL` (remotiApp.swift:1034, :1014) and on Android with `DemoProBillingRepository`. Play Billing has no emulator test mode that shotfleet could switch on.
- Conclusion: monetization screens need an app-side flag. shotfleet can only pass it.

### 2.10 Push notifications and permission states

- `xcrun simctl push <udid> <bundle> payload.json` simulates a remote push (4096 byte limit, needs an `aps` key) [docs: `xcrun simctl help push`]. A hook could use it, but timing against a banner is fragile.
- Permission states: Maestro `permissions:` and `setPermissions` [docs: https://docs.maestro.dev/maestro-flows/flow-control-and-logic/permissions.md, via limits-text.md]; `simctl privacy grant|revoke|reset <service> <bundle>` [docs: `xcrun simctl help privacy`]. iOS notification prompts are not granted silently (limits-text.md 3b).

### 2.11 Date and time

- iOS: `status_bar --time` changes only what the status bar shows; if given an ISO date string "it will also set the date on relevant devices" (display, e.g. iPad) [docs: `xcrun simctl help status_bar`]. The simulator's clock is the Mac's clock; I found no `simctl` command that sets it [unverified, full command list not read]. Content like "Posted 3h ago" is computed by the app from `Date()`, so seed relative to now (Remoti does: `now.addingTimeInterval(-10_800)`, remotiApp.swift:1160-1200).
- Android: SystemUI demo mode supports `clock` with `hhmm` or `millis` only, no date [docs: https://android.googlesource.com/platform/frameworks/base/+/master/packages/SystemUI/docs/demo_mode.md, summarized]. Setting the real device date needs root; `google_apis` (non-Play) images allow `adb root` [inferred, unverified]. shotfleet's `DEMO_MODE` sets 09:41 for display (:1231-1239).
- Maestro's docs list a `travel` command described as a GPS route simulation and, per a summarized page, also a system-clock adjustment; the page gave no platform support [docs: https://docs.maestro.dev/reference/commands-available/travel.md, **unverified, treat as GPS only**]. `setLocation` needs Android API 31+ and affects coordinates only, not IP geolocation [docs: https://docs.maestro.dev/reference/commands-available/setlocation.md]. `addMedia` takes png/jpeg/jpg/gif/mp4 from the workspace on both platforms [docs: https://docs.maestro.dev/reference/commands-available/addmedia.md]. `setAirplaneMode` works on Android only; on iOS it passes and does nothing [docs: https://docs.maestro.dev/reference/commands-available/setairplanemode.md]. `simctl location set|start|run`, `simctl addmedia`, `simctl ui appearance|content_size|increase_contrast` exist [docs: local `xcrun simctl help`].

### 2.12 Locale-dependent content

- Strings: handled by shotfleet (translated selectors).
- Demo text typed by the user or shown from fixtures: stays the same in every language unless the app localizes it (Cairn) or `[inputs.<locale>]` provides it (iOS only). README says this plainly (README line 264).
- RTL: `-AppleLanguages (ar)` flips layout on iOS; Android per-app locale flips layout. Numbers and dates follow `-AppleLocale` from the store code (shotfleet.py:765-768); on Android `set-app-locales` carries both [inferred].
- Names, addresses, currencies, units: nothing in shotfleet or in any competitor localizes these. Apps that need it (fitness, finance, travel) must carry per-locale demo data; the Cairn pattern (a dictionary keyed by language, inside the app) is the working example.

### 2.13 Dynamic, ML and AI content

- Cairn's screenshots depend on live Wikipedia pages and on-device AI answers; its capture script waits 55-62 s per shot "the answer streams in after the sheet opens" [app: Cairn/Scripts/capture-screenshots.sh:55-62]. In a Maestro flow the equivalent is `extendedWaitUntil` on an expected string with a long timeout; that already works. The result is not reproducible across languages or days, which is why `[expect]` (section 4 F9) is the honest tool: assert the thing arrived rather than assume it.
- AI-generated fixtures (translated names, notes, messages) are possible (section 4 F10) but the generated text becomes part of a public listing: label as generated, review each language.

### 2.14 What competitors do about content

| Tool | Content story | Source |
|---|---|---|
| fastlane snapshot | `launch_arguments`, `-FASTLANE_SNAPSHOT YES`, status bar override (`override_status_bar`: 9:41, full battery); everything else is the developer's UI test code | https://docs.fastlane.tools/actions/snapshot/ |
| simshot (free, MIT, iOS only) | The app reads one launch argument (`--state-arg`, default `uiState`) from `UserDefaults`; "three lines" in the app; sweeps `--langs x --states`; no status bar override, no seeded data, no Android | https://github.com/FreakLee/simshot (summarized) |
| ButterKit | Captures what is on the simulator, does not drive or seed it; frames and exports | https://butterkit.app/docs/capture/xcode/capturing-from-xcode/ (search summary) |
| AppScreens | "Does not capture directly from apps"; imports finished screenshots | https://appscreens.com/blog/appscreens-vs-fastlane (summarized) |
| Maestro | Flow steps plus `launchApp` arguments, `setLocation`, `addMedia`, `runScript` HTTP; no seeding | docs above |

So **nobody** controls content for you; the field's answer is "the app has a screenshot mode, the tool passes an argument". shotfleet is already at parity with simshot on iOS and ahead on Android and checking; it is behind fastlane only in that fastlane's users already have UI test code that does the seeding.

---

## 3. What shotfleet cannot do today, and why

Each item has the evidence and whether it is a real limit or a design choice.

| # | Limit | Evidence | Real or by design |
|---|---|---|---|
| L1 | Cannot change what a backend returns, cannot stub the network | No network code anywhere in shotfleet.py; `[inputs]`, `[overrides]` and `[hooks]` are the only extension tables (TABLES :38) | By design so far; needs app cooperation anyway (2.6) |
| L2 | Does not know the app's data model, so it cannot seed a database | Only strings are read from the build (README "How it works") | Fundamental; seeding must be app-side (2.5) |
| L3 | No per-device or per-round setup commands: no `setprop`, no `settings put`, no `simctl ui appearance dark`, no `simctl location set`, no `simctl addmedia`, no `simctl privacy`, no `simctl push` | Hooks are run-level only (:989-1018); `make_pool` and `android_pool` hard-code the status bar and demo mode (:849, :1308) | **Real gap**, small to fix |
| L4 | Android per-app switch cannot be set in time. Remoti and Stressi use system properties; Maestro arguments are intent extras read after `Application.onCreate` | Remoti DemoMode.kt comment; Maestro docs | Real gap on Android |
| L5 | No launch environment on iOS (Cairn style) | Maestro `YamlLaunchApp` fields (1.3) | Maestro limit; app-side workaround is one line |
| L6 | `[inputs.<locale>]` is ignored on Android (defaults only) | shotfleet.py:1344-1345, :1380; README line 219-221 | Real; solvable (F4) without a server |
| L7 | Typed text is not auto-translated and no per-locale fixture files exist | README line 264 | By design (buyer's data); F4/F5 give a channel |
| L8 | Android flows cannot carry per-locale values at all: all flows of a round are identical and Maestro hands any flow to any emulator | android_run :1377-1380; the round's `lang` map is only known to the host (:1371-1376) | Real; `MAESTRO_DEVICE_UDID` (2.3) is the escape [unverified] |
| L9 | iOS: no host-side step between a locale's clear and its launch, because all locales share one sharded Maestro process | ios_run :1105-1112 | Structural; HTTP barrier would fix (F5) |
| L10 | Android `clearState` is deleted on purpose, `pm clear` is shotfleet's | android_flow :1321 | Correct (clearState erases the per-app language) |
| L11 | Cannot set the date or clock (only the displayed status bar time) | 2.11 | OS limit on iOS; root-only on Android |
| L12 | No check that seeded content actually appeared. A silently failed seed produces an empty-state set in every language that passes every current check (the checks compare language, copies, missing, store rules) | judge_screen :1531, README "What it checks" | **Real and the most dangerous gap**: the owner's own committed demo images (Train tab with built-in content) hide that Log/Progress would be empty |
| L13 | Content that is not text (images, avatars, charts) cannot be judged | OCR/hierarchy compare strings only | Out of scope |
| L14 | No login or account concept | none in repo | By design; use app flags or `runFlow` with env |
| L15 | StoreKit / billing states cannot be set | 2.9 | App-side flag only |
| L16 | The public claim "Nothing in the app was changed to get them" is true for the WOD Tracker run, but that run only visits tabs whose content is built in (see examples/crossfittracker/ios.yaml: onboarding, then Train, Log, Progress, Profile with no seeded data) | site/public/index.html:222, examples/crossfittracker/ios.yaml | Wording risk, see section 6 |

One more observation about the existing example: examples/crossfittracker/ios.yaml gets to its screens by tapping through the real onboarding, so state is created by the flow. That is the third seeding method (flow-driven), valid for apps whose state is created by a short UI path, and it is free. It breaks down when the state needs 20 taps or a server.

---

## 4. How to overcome each limit: feature designs, ranked

Ranking = value to a paying indie/mobile developer, divided by effort for a solo founder. "Test without a device" says what unit tests can cover (shotfleet's tests are stdlib only, tests/test_shotfleet.py).

### F1. The "screenshot mode contract" (documentation + recipes + flow snippets). Rank 1.

- **Solves:** L1, L2, L4, L5 by telling the developer exactly what to add, in 10 lines per platform. Turns the three real-world patterns (launch args, env, Android property) into one recommendation.
- **How:** a docs page and a skill section: (1) iOS: read `-SCREENSHOT_MODE`, `-SCREENSHOT_SCENE <name>` from `ProcessInfo.arguments` / `UserDefaults`, compiled out of Release; seed in the app from `Locale.preferredLanguages` like Cairn; (2) Android: read the same from intent extras in the Activity **and** from a `debug.<app>.*` system property (and SharedPreferences) in `Application.onCreate`; (3) seed relative to `Date()`; (4) never seed from outside; (5) flow snippets: `launchApp: arguments:` with string values and the dash rule, `openLink`, `extendedWaitUntil` for slow content. Also a recipe for the Cairn style: "accept the env var name as an argument too".
- **Risks:** none technical. It must not promise that every app can do this in 10 minutes (Remoti's seeding is 950 lines on Android: DemoContent.kt 478, DemoFakes.kt 271, DemoMode.kt 203).
- **Effort:** 0.5 to 1 day. **Test without a device:** a docs test that the snippets parse as a flow and survive `localize_flow` (cheap: tests/test_shotfleet.py:87 pattern). **Paid?** No, it is the funnel and the SEO page ("fastlane snapshot launch arguments alternative").

### F2. Per-device setup commands: `[android] shell` and `[ios] simctl` (and a per-round hook). Rank 2.

- **Solves:** L3, L4, L11 (partly), enables dark mode / content size / location / media / privacy / push per device.
- **Design:**
  ```toml
  [android]
  shell = ["setprop debug.remoti.demo 1", "settings put system font_scale 1.0"]   # once per emulator after boot
  after_clear = ["run-as $SHOTFLEET_PACKAGE ..."]                                 # per round, after pm clear, before the flow (optional, later)

  [ios]
  simctl = ["ui $UDID appearance dark", "location $UDID set 52.3676,4.9041"]       # once per simulator after boot
  ```
  Android: run each string through `adb -s <serial> shell` right after the `DEMO_MODE` loop (shotfleet.py:1308) and again after `pm clear` and `set-app-locales` (:1373-1375) for `after_clear`, with `SHOTFLEET_SERIAL`, `SHOTFLEET_LOCALE`, `SHOTFLEET_PACKAGE` in the environment of a host-side `after_boot` hook variant. iOS: `xcrun simctl <args>` with the udid substituted, after `make_pool`'s `status_bar` call (:849).
- **Validation:** refuse unknown keys through `KEYS` (:34-36) like every other setting; a failing command is a setup error (exit 2) with the command printed.
- **Risk:** `setprop` of `debug.*` from the shell user is expected to work [unverified, no emulator booted]; the read-only snapshot boots (shotfleet.py:1253-1258) discard properties on each boot, so set it **after** boot every run (that is what the design does). On iOS, per-locale commands are impossible (one shared Maestro process, L9).
- **Effort:** 1 day (2 with `after_clear`). **Test without a device:** unit-test command construction and substitution with a fake `sh`; a fake `Emu.adb`. **Paid?** Core feature, part of `run` (paid beyond 2 languages).
- **Why it matters most:** it is the one change that lets the owner's Android DemoMode (and Stressi's) run under shotfleet.

### F3. `[ios] env` for apps that read launch environment (Cairn style). Rank 6.

- **Idea:** `xcrun simctl spawn <udid> launchctl setenv KEY VALUE` per simulator before the flow, so apps launched afterwards might inherit it [unverified: whether apps started by the XCTest runner inherit launchd env on iOS 26 is exactly the experiment to run].
- **Effort:** 0.5 day plus a 30 minute experiment. **Verdict:** do not build unless the experiment passes and a buyer needs it; the one-line app change (accept `-CAIRN_DEMO_SEED 1`) is simpler, safer and works under every tool.

### F4. Per-device values without a server: a generated JS map keyed by `MAESTRO_DEVICE_UDID`. Rank 3.

- **Solves:** L6, L8, L7 (Android half). Finishes the already-advertised `[inputs]` on Android.
- **How:** shotfleet knows serial to locale before it writes the round's flows (`lang[e.serial] = lp`, shotfleet.py:1376). Write `shotfleet_vars.js` next to the flows:
  ```js
  const byDevice = { "emulator-5702": {name: "Jonas"}, "emulator-5704": {name: "Taro"} };
  output.v = byDevice[MAESTRO_DEVICE_UDID] || {};
  ```
  and make the flow start with `- runScript: shotfleet_vars.js`, then `inputText: ${output.v.name}`. On iOS the same file works (map of every pool udid), or keep the existing header `env:` path (:750).
- **Risks:** [unverified] that `MAESTRO_DEVICE_UDID` is the adb serial on Android and exists on Maestro 2.0.10 (docs list it, version unknown); whether `runScript` inside a sharded run sees it. Non-ASCII typing on Android needs Maestro >= 2.7.0 (limits-text.md 2b); add the preflight described there.
- **Effort:** 1 to 1.5 days incl. a 15 minute device experiment. **Test without a device:** generation of the JS and map; run the JS under Node with a fake `MAESTRO_DEVICE_UDID`. **Paid?** Yes, part of `run`; it removes a documented limit.

### F5. HTTP barrier for host actions at flow time (seed per locale on iOS). Rank 7.

- **Idea:** the flow calls `runScript` with `http.get("http://127.0.0.1:PORT/seed?udid=${MAESTRO_DEVICE_UDID}&locale=de")`; a tiny stdlib `http.server` thread in shotfleet (as designed for hierarchy capture in limits-text.md 1b-B) does the host work (terminate, reinstall, copy files into `get_app_container ... data`, `defaults write`) and only then answers, because Maestro's HTTP call is synchronous. The flow continues with `launchApp` without `clearState`.
- **Solves:** L9 (iOS per-locale container seeding), also lets Android do `after_clear` from inside a flow.
- **Risks:** high. Copying a database file couples to schema version (2.4); a first launch after a file copy may trigger migration; ports; Maestro must have `MAESTRO_DEVICE_UDID`; the server is more moving parts to explain; a failure mode is "silently seeded stale data". It also needs `[seed]` fixtures the buyer must author per language.
- **Effort:** 3 to 4 days plus device experiments. **Test without a device:** server handlers against a fake simctl. **Paid?** Maybe, as a Pro tier. **Verdict:** only for apps that ship fixture files and cannot add a debug seed; rare among indie developers who already wrote their own seeding.

### F6. `[mock]`: built-in tiny mock server with per-locale JSON. Rank 8.

- **How:** `[mock] "GET /api/jobs" = "fixtures/jobs.{locale}.json"`; shotfleet serves them on `127.0.0.1:PORT`; iOS gets a per-locale launch argument `-API_BASE http://localhost:PORT/<locale>`, Android gets `adb reverse tcp:8080 tcp:<PORT_for_locale>` per emulator and the app uses `http://localhost:8080`.
- **Requirements the buyer must meet:** a base-URL switch in a debug build, cleartext allowed for localhost (2.6), and mock JSON in the exact shape of their API. That is the same "app cooperation" cost as an in-app fake, with more config.
- **Effort:** 3 to 5 days, +1 per platform experiment. **Test without a device:** server and route matching fully testable. **Paid?** If ever, paid. **Verdict:** later or never; WireMock or a 20-line Python server in a `before_run` hook (F7) already does it, with no shotfleet code.

### F7. Hook recipe library. Rank 4.

- **What:** a docs page of `[hooks]` and `[ios] simctl` recipes: start Firebase emulators in `before_run` and stop in `after_run`; start `python3 -m http.server` / WireMock; `simctl privacy`; `simctl push`; Android `settings put`; "seed SwiftData" by pointing at the app's own seed argument (not by touching the store).
- **Effort:** 1 day. **Test:** the recipes are text; check TOML validity. **Paid?** No, SEO and trust. (Firebase emulator specifics are [unverified]; write them against the Firebase docs when doing it.)

### F8. `shotfleet doctor --content`: a checklist for the screenshot-mode contract. Rank 5.

- **What it can honestly check from a build:** Android: debuggable flag (`aapt2 dump badging` has `application-debuggable`) so `run-as` and debug props make sense; presence of `INTERNET` and `usesCleartextTraffic`/network config; iOS: Debug build (`device_build`, `build_hint` already exist :1924-1935), `NSAppTransportSecurity` in Info.plist; plus a **string probe** of the main binary for tokens like `UITEST`, `FASTLANE_SNAPSHOT`, `SCREENSHOT`, `DEMO_SEED`, `debug.` that hints a screenshot mode exists. It prints "found `-UITEST_MODE` in the binary: pass it with `launchApp: arguments:`" or "no screenshot-mode switch found: screenshots will show whatever a fresh install shows (empty states). See the contract."
- **Risks:** heuristic. It must say "hint", never "your app has a screenshot mode". Stripped or obfuscated release builds are out of scope (Debug builds only).
- **Effort:** 1 day. **Test without a device:** run against the existing fixture app (tools/fixture-app) and the owner's builds. **Paid?** No (free onboarding).

### F9. `[expect]` and `check --content`: prove the seeded content is on screen, per language. Rank 2 (equal with F2 by value; highest value per day).

- **Solves:** L12. A seed that silently fails is the failure mode of every approach above; today nothing would flag it.
- **Design:**
  ```toml
  [expect.01_home]                  # screenshot name
  any = ["Senior iOS Engineer"]     # at least one visible (any language)
  [expect.01_home.de]
  all = ["Steinmaennchen"]           # per-language strings (app-localized demo data like Cairn's)
  [expect.03_log]
  not = ["No workouts yet", "Keine Workouts"]   # the empty state must NOT show
  ```
  Reuse `screen_text()` (:1629) and the normalisation used by `judge_screen`; on iOS the text is exact from the accessibility tree (`.texts.json`), on Android it is OCR (so Android expectations in unreadable scripts report "could not verify", never "pass"). `not` checks use the app's own strings: shotfleet already has the translated tables, so `empty_state = "app.empty_log"` could look up every language's text for free (later).
- **Also cheap:** an "identical-content" heuristic: a screenshot whose text equals the same screenshot in the fresh-install flow is probably an empty state; skip, too fuzzy.
- **Effort:** 1.5 to 2 days. **Test without a device:** entirely (PNG fixtures + `.texts.json`, same as the existing Evidence and JudgeScreen tests, tests/test_shotfleet.py:231, :669). **Paid?** Free in `check` (it is the funnel and consistent with STRATEGY "check is free"); `run` uses it automatically.

### F10. AI-assisted fixture generation per language. Rank 9.

- **What:** `shotfleet fixtures translate fixtures/en.json --to de,ja,...` using the buyer's own API key (Claude, OpenAI) to produce `[inputs.<locale>]` values or fixture files; output flagged "machine generated, review before shipping".
- **Value:** moderate for apps with user-generated content (names, notes, messages). Weak for apps where content is catalog or built-in.
- **Risks:** quality across 40 languages is unverified; a network call and a key inside a "runs locally" tool changes the privacy story (README and site say nothing is uploaded; keep it off by default and say what is sent); store reviewers expect screenshots to represent the app.
- **Effort:** 2 days. **Test without a device:** mock the API. **Paid?** Optional paid extra, or leave to the agent skill (the Claude Code skill can already do it with the user's own agent, at zero shotfleet code).

### Ranked summary

| Rank | Feature | Days | Value | Paid |
|---|---|---|---|---|
| 1 | F1 contract doc + recipes + snippets | 0.5-1 | High (unblocks every new user, SEO) | no |
| 2 | F9 `[expect]` / `check --content` | 1.5-2 | High, unique, testable offline | free in check |
| 2 | F2 `[android] shell`, `[ios] simctl` (+`after_clear`) | 1-2 | High for Android apps with a debug switch | yes (run) |
| 3 | F4 device-keyed values (Android `[inputs]`) | 1-1.5 | Medium, removes a documented limit | yes |
| 4 | F7 hook recipes | 1 | Medium | no |
| 5 | F8 `doctor --content` | 1 | Medium (onboarding) | no |
| 6 | F3 `[ios] env` | 0.5 + experiment | Low (app-side fix is simpler) | maybe |
| 7 | F5 HTTP barrier / `[seed]` files | 3-4 | Low-medium, high risk | maybe |
| 8 | F6 `[mock]` | 3-5 | Low (hooks do it) | maybe |
| 9 | F10 AI fixtures | 2 | Low-medium | optional |

Maestro commands that already help without any shotfleet code (document them in F1): `openLink` (deep links), `setLocation` (iOS and Android 31+), `addMedia` (png/jpg/gif/mp4, both), `setPermissions`/`permissions:`, `clearKeychain` (iOS), `setAirplaneMode` (Android only), `runScript` with HTTP, `runFlow` with `env:`, `extendedWaitUntil`. Do not promise `setLocation` or `addMedia` results until run (not run here).

---

## 5. The AnywhereRoles case

AnywhereRoles is the `remoti` repo (`/Users/manu/Developer/remoti`): iOS app `iosApp/remoti` (bundle name remoti), Android `androidApp` (package `me.manulorenzo.remoti`, flavors `dev` and `prod`), shared Kotlin Multiplatform code. The App Store brand is AnywhereRoles (strings, scripts named `upload_app_store_anywhereroles_*`). There is no repo called anywhereroles; `anywhereroles-mcp.json` files and `noloman.github.io/anywhereroles` are web assets.

### 5.1 How he seeds data today

iOS (XCUITest, 956 lines in `iosApp/remotiUITests/remotiUITests.swift`):
- `storeScreenshotApp()` (line 673) launches the app with `-UITEST_MODE -UITEST_RESET_PERSISTENCE -UITEST_SKIP_ONBOARDING -UITEST_COMPACT_TAB_BAR -UITEST_HIDE_ENGAGEMENT_CARDS -UITEST_SEED_DEMO_CONTENT -AppleLanguages (en) -AppleLocale en_US`, plus per-shot extras: `-UITEST_GRANT_PRO` (insights), `-UITEST_SHOW_PAYWALL`, `-UITEST_DELAY_CATALOG`, `-UITEST_FORCED_FREE_PRO_FEATURES <list>`. It also forces orientation (iPad landscape).
- The **data** is in the app, `#if DEBUG`, in `iosApp/remoti/remotiApp.swift`: `resetUITestPersistentStateIfNeeded` (:953, deletes UserDefaults and the `remoti.db` files), `configureLaunchDefaults` (:973-1025, sets onboarding done, hides engagement cards, writes the "last sync" timestamps), `uiTestCatalog` (:1040), `seedUITestContentIfNeeded` (:1114-1200, inserts categories and four jobs with relative timestamps through `JobsBridge`). Pro and paywall flags in `SubscriptionStore.swift:292` and `RemoteFeatureFlags.swift:43-48`.
- The test steps: type "Senior iOS Engineer" in the search field (data, English in every language because it is a job title from the fixture), tap the first job, tap "Why this fits", scroll, `XCTAttachment` screenshot, tab by accessibility identifier, etc. English labels; the app is forced to English.
- Localization is done **after** capture: raw English captures in `fastlane/screenshots/_source/{ios,android}/`, then `scripts/compose_store_screenshots.py` burns localized headings from `fastlane/screenshot-headings.json` onto them for 20 locales [app: remoti/ASO_ROADMAP.md:239-246]. The UI inside the phone stays English in every listing. That is exactly the case shotfleet's check flagged on his committed set: 108 problems, all "shows en strings", true positives, viewed in two images [repo: research/real-apps.md "shotfleet check on committed screenshots"].

Android:
- `androidApp/src/debug/java/me/manulorenzo/remoti/demo/DemoMode.kt` (203 lines), `DemoContent.kt` (478), `DemoFakes.kt` (271): debug-only; enabled by `adb shell pm clear me.manulorenzo.remoti; adb shell setprop debug.remoti.demo 1; adb shell am start ...`. It seeds Room and DataStore into an empty catalog, replaces Koin bindings for billing, auth, alerts, categories, jobs remote and all-jobs repository with fakes, and hides the source badge. The release source set carries a no-op twin. How the Android screenshots are then captured I could not find (no UI test; manual adb is likely) [unverified].

### 5.2 What shotfleet needs so he can use it

iOS: **nothing new.** Concretely:
1. Build a Debug simulator app (the flags are `#if DEBUG`).
2. A Maestro flow with launches that carry his flags as **string** values (see the dash rule in 1.3):
   ```yaml
   - launchApp:
       arguments:
         UITEST_MODE: "1"
         UITEST_RESET_PERSISTENCE: "1"
         UITEST_SKIP_ONBOARDING: "1"
         UITEST_COMPACT_TAB_BAR: "1"
         UITEST_HIDE_ENGAGEMENT_CARDS: "1"
         UITEST_SEED_DEMO_CONTENT: "1"
   ```
   shotfleet adds `clearState: true` on the first launch and its own `AppleLanguages`/`AppleLocale` (shotfleet.py:771-778). His own `-AppleLanguages (en)` line must not be copied (shotfleet's wins and reports conflicts per limits-text.md 3c).
3. Typing "Senior iOS Engineer" is data, the same in every language: `inputText: "Senior iOS Engineer"`. No `[inputs]` needed. `tapOn: "Why this fits"` is translated by shotfleet from the app's `.strings` (the string exists in `Localizable.strings`; whether every promoted label is a key is [unverified]).
4. Tab taps: he uses accessibility identifiers (`tabButton("saved")`); Maestro `tapOn: {id: "..."}` passes through untouched.
5. Pro and paywall shots need a **relaunch with different flags** (`UITEST_GRANT_PRO`, `UITEST_SHOW_PAYWALL`): a second `- launchApp:` block with `clearState: false`... note `UITEST_RESET_PERSISTENCE` already clears data on launch, so state is reset anyway. shotfleet supports several `launchApp` steps (later ones keep their options, :790-793).
6. Keyboard: his test types `"...\n"`; in Maestro use `hideKeyboard` or `pressKey: Enter`.
7. iPad landscape: Maestro has `setOrientation` [docs list, https://docs.maestro.dev/reference/commands-available]; whether the capture is 2752x2064 with no black band is [unverified] (his own comment says XCTest's `app.screenshot()` had such a band, but Maestro screenshots use the runner, not XCUIScreen; the band risk must be tested).
8. Output goes to `_source/ios/<locale>/` instead of one `_source/ios/`; `compose_store_screenshots.py` currently takes one source set and a heading per locale, so it needs a small change to read per-locale raw captures and drop the English-only assumption. That change is in his repo, not shotfleet.

Android: needs **F2**. Without it nothing sets `debug.remoti.demo` on shotfleet's emulators, because shotfleet boots them itself after `before_run`, and `pm clear` (shotfleet.py:1373) runs per round. With F2 (`[android] shell = ["setprop debug.remoti.demo 1"]`, once per emulator after boot) his flow would be: bare `launchApp` (shotfleet adds it), wait for the first screen, tap, screenshot. Because DemoMode seeds only into an empty catalog and shotfleet clears data each round, the seed would run every round, which is correct. He needs a `dev` or `prod` **debug** APK (`assembleDevDebug`; the package then has `.dev`, which `init` reads from the APK).

### 5.3 Would it then be better than his current setup? Honest answer

- **Real localized UI in 17 languages: yes, clearly better.** His current store images show English UI under translated captions. Apple's guideline 2.3.3 problem is reported by vendor blogs, which are marketing sources [repo: research/market-2026.md line 48]; the visible downside is a localized listing that shows English product. shotfleet would fix that and would verify it.
- **Data quality: equal.** shotfleet reuses his seeding unchanged; it adds no data of its own.
- **Maintenance: roughly equal, different.** He would maintain one Maestro flow (English labels) per story instead of Swift XCUITest code for screenshots. His 956-line XCUITest file is mostly **regression tests**, not screenshots (roughly four store-screenshot tests), and stays regardless.
- **Cost today:** a day to write the flow and adapt `compose_store_screenshots.py`; Android blocked until F2.
- **Where shotfleet is not better:** English-only screenshots (his UI tests already do that, with exact timing control, `waitForExistence`, accessibility identifiers and XCTest attachments); the app-specific states with complex gestures; anything needing XCUITest APIs.
- **Verdict:** my earlier advice "don't use shotfleet, the UI tests already seed the data" was wrong on the reason. The seeding is in the app and shotfleet can drive it on iOS today. The correct advice: **use shotfleet for AnywhereRoles iOS if he wants the localized listings to show localized UI; wait for F2 for Android.** If he decides English UI under translated captions is acceptable for his markets, then no, shotfleet adds little beyond `check`.

---

## 6. The product angle

### 6.1 Does content control make shotfleet more valuable and profitable?

- **More valuable: yes, in one specific way.** The promise "one English flow, every language, checked" is only as good as the content the flow reaches. Empty states in 18 languages are 18 wasted screenshots. Developers evaluating shotfleet will ask "how do I get my demo data in?" within the first hour; today the honest answer is "your app's debug switch, via launch arguments" and README does not say it. (README mentions `launchApp` arguments only in passing, Tips section.)
- **More profitable: not directly.** Nobody pays for "pass an argument" (fastlane and simshot do it for free). They pay for time saved and for a result they can trust. Content features that pay: F2 (unblocks Android apps with debug switches), F4 (removes a documented limit), F9 (trust). Heavy features (F5, F6) serve a small number of buyers and add support load.
- **Who would pay:** (a) an indie with a debug-seeded app and no desire to maintain UI test code for 40 languages (Remoti, Cairn, Stressi are three of the owner's own examples of that profile); (b) a developer whose UI tests exist only in English and who ships English UI under translated captions (the real-apps finding, 108 of 120 images); (c) teams wanting the CI check. Not the buyer: apps whose content is server-driven and unmockable, games (research/frameworks.md section 6), apps whose demo needs real accounts.
- **Competitors:** none controls content (2.14). simshot's "states" matrix (languages x states from one argument) is the same idea shotfleet already has; shotfleet's differentiators stay Android, checking and the one-flow promise. Content control by itself is not a moat; verified content (`[expect]`) is.

### 6.2 Recommendation

| Item | When |
|---|---|
| F1 contract doc, F9 `[expect]` + `check --content`, F2 per-device commands | **Build now** (about 4 days total; ahead of or alongside the launch because all three remove first-hour failures and are testable without a device) |
| F4 device-keyed values, F8 `doctor --content`, F7 recipes | **Next** (2 to 3 days) |
| F3 `[ios] env`, F5 `[seed]`/barrier, F10 AI fixtures | **Later**, only on buyer request, after the 30 minute experiments |
| F6 built-in `[mock]` server, proxy-based interception | **Never** as built-ins; recipes via hooks instead (WireMock or a Python server in `before_run`) |

**Smallest first step that is honest and testable:** F9 with only `any` and `not` lists, applied to the iOS `.texts.json` data that already exists (shotfleet.py:882-899, :1629), plus the F1 page with the iOS argument recipe and the dash rule. No device is needed to build or test it, it fixes the largest silent failure (L12), and it adds no claim beyond "we check that the strings you list are on screen". Do the one experiment that matters next time the Mac is free: a 3-step flow on one simulator with `launchApp: arguments: { UITEST_MODE: "1" }` against a build that prints its arguments, to confirm the dash and boolean behaviour on Maestro 2.0.10 (and on the Maestro version shotfleet will require).

### 6.3 Claims that must stay carefully worded

- Website, hero note, site/public/index.html:222: "Nothing in the app was changed to get them." True for that run, but those screens are built-in content visited via the real onboarding (examples/crossfittracker/ios.yaml). Keep it tied to that run and add "your app's own demo data and screenshot switch still apply" nearby. Do not generalise it to "no app changes needed".
- Website "Not for you if... your UI tests already run in every language" (index.html:381) and alternatives.html:77 "If you don't want test code in your app": shotfleet does not remove the need for app-side demo data. Reword to "no UI-test code; your app still needs a way to show demo data if empty screens are not what you want to ship".
- README "Why": "a separate copy per language" is about taps; do not imply shotfleet creates content.
- README line 264 and the `[inputs]` section already say Android defaults only; keep that until F4 ships and is run on a device. The values are "tested as flow text, not yet run on a device".
- Any mention of `launchApp` arguments must show **string** values and the dash rule until verified on the supported Maestro; the Android sentence must say they arrive as intent extras and cannot enable a system-property switch.
- Do not claim support for seeding, mocking, StoreKit, push, date/time or login. "Passes your launch arguments, sets language, status bar, permissions and fresh state" is the full honest list today.
- Status bar claim: iOS sets 9:41 and full bars; Android demo mode shows 09:41 (`hhmm 0941`), not the date; "Tuesday January 9th" (fastlane's override) is not what shotfleet does.
- Android "every permission granted" (`install -g`) is a statement about install; `pm clear` before each round may reset runtime grants [unverified]; do not state permissions are retained until tested.
- `check` caveat: it verifies language and strings, not that data is meaningful. After F9, say "checks that the strings you list are present", nothing about "looks good".

---

## 7. What I did not verify (one list)

- Everything about device behaviour: Maestro argument encoding on 2.0.10, `MAESTRO_DEVICE_UDID` value on Android, `setprop debug.*` from adb shell on the snapshot-booted emulators, `run-as` and `adb reverse` behaviour, `launchctl setenv` inheritance, iPad landscape captures through Maestro, StoreKit on a plain Maestro run.
- ATS and emulator network facts came through a page summarizer; the Apple page was thin.
- That a Maestro-run Debug build of Remoti reaches its seeded state exactly as XCUITest does (it should, the flags are plain launch arguments, but the first launch with `clearState` reinstall plus `-UITEST_RESET_PERSISTENCE` was not run).
- How the Android store screenshots of AnywhereRoles are produced today.
- Effort figures are estimates, not measurements.
