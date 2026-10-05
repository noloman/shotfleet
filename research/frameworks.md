# shotfleet and app frameworks: who can we serve, and what has to change

Research date 2026-10-02, against branch `claude/integrate-on-main` (shotfleet.py 2130 lines, includes the uncommitted working-tree edits of another session).
No simulator, emulator or Maestro was run, nothing was installed or cloned. I downloaded single files (docs, translation files) into the scratchpad and ran shotfleet's own readers on them.

Tags: **[V]** verified in a primary source this session (URL in Sources), **[R]** I ran shotfleet's code on real or synthetic files, **[I]** inference, not verified: check it in the validation plan.

## 0. Findings that matter before the per-framework sections

What exists on this branch that touches frameworks (read in shotfleet.py):

- `strings = "glob"` (config) and `check --strings` feed `load_strings_files` -> `read_translation_file` (.arb .json .xcstrings .strings .stringsdict .xml .xlf .resx .po .properties .csv). Locale comes from `@@locale`, the file name or the folder (`locale_from_path`).
- iOS language is set per flow by `localize_flow` as `launchApp: arguments: AppleLanguages "(lp)", AppleLocale`. User `launchApp` options (permissions...) are now merged. Android: `pm clear` then `cmd locale set-app-locales <pkg> --locales <lp>` (`android_run`).
- New: iOS runs read each screen's text from the Maestro iOS driver's accessibility tree (`ios_screen_texts`, `capture_texts`, saved as `<shot>.texts.json`); `check` prefers it to OCR (`screen_text`). Android still uses OCR only (comment in `android_flow`).
- No framework detection anywhere. `cmd_init` on a Flutter/RN build prints "0 languages ()" or a few native languages with no hint to use `strings`.

Real-file test of the readers (downloaded real translation files from GitHub, ran `load_strings_files` + `translate_flow`) **[R]**:

| Source | Files | Result |
|---|---|---|
| wger Flutter app, `lib/l10n/app_{en,de,ar,ja,pt_BR}.arb` | 5 ARB, 573 keys en | all loaded; "Log in" -> "Anmelden" / Arabic; ICU plurals ok. `ja` has 174/573 keys so `shipped_locales` silently drops it (50% rule) |
| Bluesky social-app, Lingui `src/locale/locales/{en,de,ja}/messages.po` (Crowdin) | 3 PO, ~3,290 msgs | loaded (locale from folder); "Sign in" -> "Einloggen" / "サインイン" |
| Rocket.Chat RN `app/i18n/locales/{en,de,ja}.json` | flat i18next-style JSON, 1,086 keys | loaded; "Settings" -> "Einstellungen". "Cancel" became `(Abbrechen|Cancel)` because de.json has an untranslated "Cancel" |
| obytes Expo template `src/translations/{en,ar}.json` | 25 keys | loaded |
| .NET MAUI official sample `LocalizationDemo` `.resx` (neutral, de, ja, zh-Hans, pt) | 3 keys x 5 | loaded |
| Unity Localization CSV export (docs' format: `Key,Id,English(en),French(fr)`, also the "with comments" variant) | synthetic from docs | loaded, Id and Comments columns ignored correctly |

Bugs found by running it **[R]** (all reproduced on this branch):

1. **i18next namespaces collide.** `locales/en/common.json` + `locales/en/settings.json` both with key `title`: the later file overwrites (`load_strings_files` does `out[lp].update(t)` with bare keys). A flow tapping "Home" (from common.json) is reported untranslated.
2. **A 2-3 letter namespace file name is read as a locale.** `locales/en/app.json` -> `locale_from_path` returns `app` (the `ok(stem)` check accepts any 2-3 letter stem), so a locale called "app" appears and `app.json` strings never reach `en`. Same for `ui.json`, `nav.json`, `faq.json`.
3. **gettext `.po`:** the `Language:` header is ignored and `msgstr[n]` plurals are dropped. A `messages.po` with no locale in its path (the usual `locale/de/LC_MESSAGES` layout is fine) is stored as the **base** language, so German text lands in `en`. Silent.
4. **Empty accessibility tree gives a false problem.** `screen_text()` returns a result as soon as `<shot>.texts.json` exists, even for `[]`. `judge_screen` then reports "no text found (blank or still loading?)" instead of falling back to OCR. This hits every app whose text is not in the iOS accessibility tree: Unity and other games, Flutter text drawn outside semantics, WebViews without accessibility, RN views with `accessible={false}` parents. Reproduced with an empty `.texts.json`.
5. **Partial native tables mask a missing JS table.** If a Flutter/RN/MAUI/Expo build has any native strings (Expo `locales` in app.json writes `InfoPlist.strings`, and `Localizable.strings` from SDK 55; MAUI's `Platforms/Android/Resources/values-*/Strings.xml` holds only the app name), the default path (no `strings`) loads those few strings, `shipped_locales` looks fine, and nothing in the flow translates. [I] for the Expo/MAUI cases (the mechanism is read in `ios_run`/`android_run`; the bundle contents are from the docs).
6. `shipped_locales` drops partially translated languages with no message (wger `ja` 30%).
7. `check --app X.app` on a Flutter/RN build fails with "contains no translations shotfleet can read (no .lproj strings, String Catalogs or resources)": true, but it does not say "use --strings".

Cross-cutting facts used below:

- **The language mechanism shotfleet uses works without app cooperation on Android.** AOSP `LocaleManagerService.setApplicationLocales` has no `android:localeConfig` check; only the caller (shell has `CHANGE_CONFIGURATION`) is checked **[V]**. `android:localeConfig` only gates the system Settings UI; Google says omitting it signals users should not be able to set the language in Settings **[V]**. `resourceConfigurations`/`resConfigs` strip resources for other languages from the APK, so natively resolved strings (Compose resources compiled to `resources.arsc`, `strings.xml`, MAUI native strings) fall back to default for a stripped language **[V]** (Google's text says exactly that purpose). Apps whose strings are in JS/Dart/.NET assemblies are not affected by stripping. Whether an app locale with no resources still reaches `Configuration.getLocales()` is [I]; confirm in the plan.
- **iOS:** `AppleLanguages` as a launch argument changes `NSLocale.preferredLanguages`, which Flutter's engine (`FlutterEngine.mm` `onLocaleUpdated`, line ~1571) and react-native-localize (`RNLocalize.mm` lines 89/107) read **[V]**. It is not filtered by the bundle's `CFBundleLocalizations` (Flutter issue 177386: unsupported OS language is returned as is) **[V]**.
- **An in-app language picker that persists the choice overrides the OS language** (obytes: `lng: getLanguage() || getLocales()[0]`, wger: `userLocale` setting) **[V]**. shotfleet clears state per language, which usually resets it; apps that read a stored default from a bundled config will not follow.
- **Maestro** is black-box over the OS accessibility tree for every framework (docs) **[V]**. `launchApp: arguments` exist on iOS and Android **[V]**.
- Debug vs release matters per framework (below); shotfleet's inputs are "a simulator `.app` and an APK that run on their own".

## 1. React Native (bare)

1. **Build.** iOS: `xcodebuild -workspace ios/App.xcworkspace -scheme App -configuration Release -sdk iphonesimulator -derivedDataPath build` -> `build/Build/Products/Release-iphonesimulator/App.app`. Android: `cd android && ./gradlew assembleRelease` -> `android/app/build/outputs/apk/release/app-release.apk` (the RN template signs release with the debug keystore, so it installs) **[V]**. `npm run ios` / `assembleDebug` build debug apps, and RN's gradle plugin skips bundling the JS for debuggable variants **[V]** (template comment), so a Debug app needs Metro and shows a red screen when started alone [I for iOS: same design]. **Not unchanged: Debug builds do not work as inputs; Release builds do.** Hermes compiles the JS and the JSON translations into the bundle, so strings can't be read from the build.
2. **Language.** iOS: libraries read `preferredLanguages` -> follows the launch argument **[V]**. The RN template Info.plist has `CFBundleDevelopmentRegion` but no `CFBundleLocalizations` **[V]**; react-native-localize's README says to list locales there and set `android:localeConfig` **[V]**, mainly for native pieces and RTL. `i18next-react-native-language-detector` (npm 1.0.2, 27 stars, last push 2017-03-28) is a thin wrapper over `react-native-locale-detector` and is effectively abandoned **[V]**; real apps use `expo-localization` (3.3M npm downloads/week) or `react-native-localize` (0.68M/week) **[V]**. Android: `getLocales()` and `Locale.getDefault()` come from the process configuration, which carries the per-app locale [I].
3. **Maestro sees it.** Official support, `testID` maps to `id`, text selectors work on `Text`/`Button` **[V]**. Known: on iOS, an `accessibilityLabel` replaces the visible text in the tree so `tapOn: "Click me!"` fails (issue 1409 open since 2023, PR 3165 open) **[V]**; nested touchables swallow taps unless the outer one is `accessible={false}` (Maestro docs) **[V]**. This also shrinks `.texts.json` for shotfleet's check [I].
4. **Translations.** Typical: `locales/<lng>/<ns>.json` or `locales/<lng>.json` (i18next), Lingui `.po`, react-intl JSON, i18n-js JSON or TS objects, Ignite's `app/i18n/en.ts`. Read today: flat and nested JSON, `_one/_other` -> `#one/#other`, ICU in values, `.po` by folder. Missing: namespaces (bugs 1-2), TS/JS object files (Ignite, many vue-i18n/i18n-js setups: `.ts` is not a supported extension and raises "don't know how to read"), `.po` header/plurals (bug 3), runtime-fetched or OTA translations (Phrase OTA, CodePush, Expo Updates bundles), strings assembled in code (`t('a') + ' ' + t('b')`), i18next `$t()` nesting and `_context` suffixes (not resolved; selectors on such text stay untranslated, reported as such).
5. **Verdict: works today** for Release builds with i18next JSON or Lingui/gettext files. **Small work** for namespaces and a TS-object reader.
   Code: `read_translation_file` + `locale_from_path` (namespace prefix, directory beats stem) S; `.po` header and `msgstr[n]` S; TS/JS reader via `node -e` dump M; framework hint (section 11) S.

## 2. React Native with Expo and EAS

1. **Build.** Local: `npx expo run:ios --configuration Release` and `npx expo run:android --variant release`; `-o/--output <dir>` copies the binary, `--no-bundler` skips Metro **[V]** (Expo CLI docs). EAS: `eas.json` profile with `"ios": {"simulator": true}` then `eas build -p ios --profile preview` (cloud) or `eas build --local`; Android profile `"android": {"buildType": "apk"}` **[V]**. `eas build:run -p ios --latest` installs on a simulator **[V]**. The EAS iOS simulator artifact is an archive that has to be unpacked to get the `.app` [I]; `WRONG_BUILD` has no hint for it. **Not usable:** development-client builds (`developmentClient: true`, they need `npx expo start`, docs say so) and Expo Go (runs inside Expo's container; Maestro docs: use `openLink` there, shotfleet needs your own bundle id) **[V]**. `debugOptimized` is still a debug variant: no embedded JS [I].
2. **Language.** `expo-localization`'s config plugin takes `supportedLocales` (per platform) and that is what makes the app declare its languages to iOS and Android **[V]**. On iOS `getLocales()` stays fixed while the app runs (fine: shotfleet sets the language at launch); on Android it can change at runtime, so apps re-read on foreground **[V]**. From SDK 58 (docs describe it), RTL on iOS applies only if the device language is one of the declared `supportedLocales` **[V]**: Arabic/Hebrew runs need that plugin option. App name and permission strings are localized with `locales` in app.json (InfoPlist.strings; `Localizable.strings` from SDK 55) **[V]**, which feeds bug 5.
3. **Maestro:** same as RN; Maestro docs call Expo/EAS fully supported, including EAS Workflows **[V]**.
4. **Translations:** same as RN. `app.json` `locales/<lng>.json` is native metadata only. Expo's own guide uses `i18n-js` with in-code objects (TS), which is the unsupported reader case.
5. **Verdict: works today** with Release/EAS-preview builds. Expo is the majority of RN: npm `expo` 11.2M/week vs `react-native` 16.0M/week **[V]**. Code: as RN plus `.gz`/`.tar.gz` hint in `WRONG_BUILD`/`build_hint` S.

## 3. Flutter

1. **Build.** iOS: `flutter build ios --simulator --debug` -> `build/ios/iphonesimulator/Runner.app` [I path]. Android: `flutter build apk --debug` -> `build/app/outputs/flutter-apk/app-debug.apk` [I path]. Flutter docs: simulator and emulator run only debug mode, release is not supported there **[V]**. So the iOS input is always a debug (JIT) build, and **the DEBUG banner appears in every screenshot** unless the app sets `debugShowCheckedModeBanner: false` (default on in debug) **[V]**. Debug builds run standalone on the simulator. Gotcha: wger's debug build has `applicationIdSuffix ".debug"`, so the package is `de.wger.flutter.debug`; `init` reads it from the APK, so it is fine unless a user hardcodes the package **[V]** (read from build.gradle).
2. **Language.** iOS: engine uses `[NSLocale preferredLanguages]` -> launch argument works; `CFBundleLocalizations` is not needed for Dart strings but Flutter's docs say to add languages in Xcode (they create empty `.strings` files) for the App Store **[V]**. Android: engine reads `getResources().getConfiguration().getLocales()` **[V]** and a Flutter maintainer thread says `platformDispatcher.locales` and `didChangeLocales` take per-app languages into account (issue 109842 is open only for official docs/support) **[V]**. Flutter then resolves the OS list against `supportedLocales` (exact, language, else the first supported locale), unless the app has `locale:` or a `localeResolutionCallback` **[V]**. wger has `android:localeConfig` and `userLocale` (null by default) **[V]**.
3. **Maestro sees it** through the Semantics tree: `Text`/`TextField` are implicit; icons need `semanticLabel`; `Semantics(identifier:)` since Flutter 3.19; Keys are invisible; Flutter web needs `ensureSemantics()`; Flutter desktop unsupported **[V]**.
4. **Translations.** `lib/l10n/app_<locale>.arb` + `l10n.yaml` (`arb-dir`, `template-arb-file`) **[V]** (docs). Read today: ARB, `@@locale`, `app_zh_Hans`, `intl_en.arb`, metadata `@key` ignored, ICU plural/select expanded per form (`items#one`, `=0`), placeholders `{name}` [R]. Real wger files worked [R]. Also common: `easy_localization` JSON (`assets/translations/*.json`; 293k pub.dev downloads/30d) and `slang` (301k) vs `intl` (11.3M, i.e. gen_l10n dominates) **[V]**. Missing: auto-find of the ARB folder from `l10n.yaml`, Dart-code translations (GetX `Map<String, Map<String,String>>`), nested ICU (`icu_forms` handles the first plural/select block only, per its own `ponytail:` comment), runtime-downloaded translations.
5. **Verdict: works today** (the single most uniform source format). **Small work:** debug-banner warning, empty-tree fallback (bug 4), `l10n.yaml` auto-detect, silent 50% rule (bug 6).
   Code: `screen_text` S; `cmd_init`/`detect_framework` S-M; `shipped_locales` report S.

## 4. Kotlin Multiplatform / Compose Multiplatform

1. **Build.** iOS: Xcode project of the shared app, e.g. `xcodebuild -project app/iosApp/KotlinConf.xcodeproj -scheme KotlinConfAppScheme -configuration Debug -sdk iphonesimulator -derivedDataPath build build` (scheme name from the app's README **[V]**; Xcode runs the Gradle embed task). Android: `./gradlew :app:androidApp:assembleDebug` (module exists in kotlinconf-app **[V]**; older wizard apps use `:composeApp:assembleDebug`) -> `.../build/outputs/apk/debug/*.apk`. Both are normal native artifacts: **work unchanged.** Previous work already ran two KMP apps through the loaders (research/real-apps.md: Kuokka, Stressi).
2. **Language.** CMP resources on iOS use the first of the preferred locales (PR 5180 "Use first of preferred locales instead of current") **[V]** -> launch argument works. Android: `stringResource` responds to locale overrides; iOS in-app switching is the open issue (CMP-8376) **[V]** (irrelevant to shotfleet). Resource folders: a script-less `values-zh` must exist next to `values-b+zh+Hans` or Chinese can't resolve **[V]**. Android `resourceConfigurations` should not strip CMP languages, because CMP resources are packaged as assets (`.cvr`), not in `resources.arsc` [I].
3. **Maestro:** Android Compose via accessibility **[V]**. iOS: the Compose accessibility tree loads lazily on the first request from the iOS accessibility engine since 2025-01 (PR 1780); before, apps needed `AccessibilitySyncOptions.Always` for VoiceOver/XCUITest (issue 4401) **[V]**. Old CMP (< ~1.8) apps may show an empty tree to Maestro [I on version].
4. **Translations:** `.cvr` (iOS bundle and APK assets), `strings.xml`, `.xcstrings`, `.strings` all read from the build; `check` and `run` need no `strings`. Missing: `<string-array>` (not read), code-defined strings (Lyricist-style), the `.cvr` plural encoding is "inferred from the writer, not seen in a real app" per `add_cvr`'s own comment: validate on kotlinconf-app. moko-resources compiles to native files (covered).
5. **Verdict: works today** (best covered). Needs one real-app run to retire the `.cvr` plural risk. Code: none required; S for `<string-array>`.

## 5. .NET MAUI

1. **Build.** iOS simulator: `dotnet build -f net10.0-ios -c Debug -p:RuntimeIdentifier=iossimulator-arm64` -> `bin/Debug/net10.0-ios/iossimulator-arm64/<App>.app` [I: docs show `dotnet build -t:Run -f net8.0-ios`; the official sample targets `net10.0-*` **[V]**]. Android: **Debug uses Fast Deployment, which installs assemblies outside the APK**, so an adb-installed debug APK will not start by itself; set `-p:EmbedAssembliesIntoApk=true` or build Release **[V]** (dotnet/android build-properties docs). `dotnet build -f net10.0-android -c Debug -p:EmbedAssembliesIntoApk=true` -> `bin/Debug/net10.0-android/<ApplicationId>-Signed.apk` [I path]. Needs `dotnet workload install maui`.
2. **Language.** .NET `CurrentUICulture`. MAUI docs: on iOS/Mac Catalyst declare every language under `CFBundleLocalizations` and set `CFBundleDevelopmentRegion` so MAUI controls localize **[V]**. Android culture from the process locale [I]; `.resx` culture assemblies are satellite assemblies inside the APK/app, so stripping by `SatelliteResourceLanguages` could drop languages [I, check in plan].
3. **Maestro:** native controls (UILabel/TextView) so text is in the tree [I]; Maestro has no MAUI page of its own (its Windows/WinUI issues are unrelated).
4. **Translations:** `Resources/Strings/AppResources.resx` + `.de.resx` **[V]**. Read today: `.resx`, culture from file name, neutral = base. Real sample worked [R]. Missing: nothing structural. Pitfall: bug 5 (native `values-*/Strings.xml` holding only the app name gets read by `load_strings_apk` when no `strings` is set).
5. **Verdict: works today with `strings = "Resources/Strings/*.resx"`.** **Small work:** hint. Effort S.

6. **Result of the run, 2026-10-04: passed.** Evidence in `research/experiments-2026-10-04/C/`. `dotnet/maui-samples` `10.0/Fundamentals/Localization/LocalizationDemo` (sparse checkout), .NET SDK 10.0.401 in a scratch folder,
   `dotnet workload install maui` (MAUI SDK 10.0.110, iOS SDK 27.0; 101 packages, 2.07 GB download, **6.90 GB unpacked, over the task's 5 GB limit: run anyway with the owner's go-ahead**), Xcode 27.0.
   `dotnet build -f net10.0-ios -c Debug -p:RuntimeIdentifier=iossimulator-arm64` -> `LocalizationDemo.app` (`rc=0`, 415 s). `shotfleet init` on the `.app` found 9 languages (de, en, es, fr, ja, pt, pt-PT, zh-Hans, zh-Hant) and printed the MAUI hint;
   the config added `strings = "<...>/Resources/Strings/*.resx"` and `locales = ["de", "ja"]`. The flow (en): launch, `assertVisible: "Notes:"`, `assertVisible: "Add Note"`, `takeScreenshot: 01_home`.
   `shotfleet run --locales de,ja --parallel 1` with Maestro 2.0.10 (shotfleet's tested version): `rc=0`, `captured 2/2 locales in 394s on 1 simulators` (iPhone 17 Pro Max, iOS 26.4), `untranslated_selectors: []` for both languages,
   the selectors became `'Hinweise:'` / `'Neues Element hinzufügen'` (de) and `'注釈：'` / `'新しい項目を追加'` (ja) and their `assertVisible` steps passed, `shotfleet check`: `checked 2 screenshots in 2 languages: 0 problem(s)`.
   The German screenshot shows the German labels and the sample's own German flag image, which only appears when the OS locale reached the app. **0 untranslated selectors on a 2-language run: C passes.**
   What this does not show: Android (not built), the native `values-*` trap (bug 5; the iOS bundle has none), more than two languages or one screen, Release builds, or any MAUI app that is not this sample. The run was not on a quiet Mac: job #10's Android emulator
   (port 5702) was running and the load was 480 to 640, with the queue owner's agreement for this iOS-only run; the language and selector results do not depend on timing, but the 394 s is not a speed figure.

## 6. Unity

1. **Build.** Unity exports an Xcode project for iOS: build it with `xcodebuild -project Unity-iPhone.xcodeproj -scheme Unity-iPhone -configuration Debug -sdk iphonesimulator`, after setting Player Settings > Target SDK = Simulator SDK [I, Unity manual not fetched]. Android: Build Settings with "Build App Bundle" off, or `Unity -batchmode -quit -buildTarget Android -executeMethod <your build method>` -> `.apk` [I]. Both produce installable artifacts.
2. **Language.** Games read `Application.systemLanguage`, which "might not appear immediately... on some platforms updates only after you restart" **[V]**; the Localization package's `SystemLocaleSelector` is built on it [I]. Whether iOS's `-AppleLanguages` launch argument reaches it is closed-source: unknown, needs an experiment. Android per-app locale probably reaches `Locale.getDefault()` [I].
3. **Maestro does not see the text.** Unity draws to a GL/Metal/Vulkan surface. Since Unity 2023.2/6 there is an `AssistiveSupport` / `AccessibilityHierarchy` API for TalkBack/VoiceOver (iOS 13+, API 26+), but nodes exist only if the game creates them **[V]**. Text selectors are therefore mostly unusable; flows must tap `point: "x%,y%"`.
4. **Translations:** Localization String Tables are ScriptableObjects in Addressables (not readable from the build); the package exports CSV/XLIFF **[V]** (CSV columns `Key, Id, English(en)...`, handled [R]). I2 Localization and custom JSON also exist.
5. **Verdict: not realistic for the product's core promise** (rewrite text selectors). A reduced use is feasible: run a point-driven flow per language, capture, and run `check` (OCR). That needs bug 4 fixed first. Effort S (fix) + docs; do not market it.

## 7. Capacitor / Ionic

1. **Build.** `npm run build && npx cap sync`; Android `cd android && ./gradlew assembleDebug` -> `android/app/build/outputs/apk/debug/app-debug.apk`; iOS `xcodebuild ... -sdk iphonesimulator` on the generated `ios/App` project **[V]** (HybridMob guide for Android/iOS shape; exact iOS project name varies by Capacitor version [I]). Debug builds embed the web assets, so **they work unchanged**.
2. **Language.** The UI is JS, so the language is whatever the web layer reads. Android: `navigator.language` and the Device plugin follow `AppCompatDelegate` locales (Capawesome plugin docs; it only changes natively rendered strings) **[V]**. **iOS: an Apple Developer Forums post reports WKWebView's `navigator.language` uses the system language, not the per-app language, since iOS 17.4** (unanswered single thread) **[V as a report]**; if true, `AppleLanguages` launch arguments don't reach web apps that use `navigator.language`, while apps using `@capacitor/device` (native `preferredLanguages`) would follow [I]. One 20-minute experiment settles it on iOS 26.
3. **Maestro:** iOS reads WebView content through accessibility, and an element's `id` becomes the accessibility id (HybridMob guide) **[V]**. Android WebView is the weak side: known issues 2293 (ids), 3497 (WebView 150+ text inputs unmatchable), 3646 (`androidWebViewHierarchy: devtools` fails on System WebView 148+, opened 2026-09-30), and the documented workaround `androidWebViewHierarchy: devtools` **[V]**.
4. **Translations:** ngx-translate/Transloco/i18next/vue-i18n JSON and Angular `$localize` XLIFF: read today (JSON, `.xlf`). Missing: `.xmb`, TS locale objects (common in vue-i18n), remote-loaded JSON.
5. **Verdict: needs real work or at least an experiment:** feasible if the app follows the native locale (Android yes; iOS unverified). Otherwise per-language means a URL/localStorage bridge that is app-specific (not generic). Effort M, uncertain.

6. **Result of the iOS experiment, 2026-10-04 (run on a simulator): yes, the language reaches the webview.** Evidence in `research/experiments-2026-10-04/B/`.
   Throwaway app `dev.shotfleet.capdemo`: Capacitor 8.5.2 (`@capacitor/core`, `@capacitor/ios`) with `@capacitor/device` 8.0.3, Debug build for the iOS Simulator SDK with Xcode 27.0,
   web assets embedded. Two buttons, the first labelled with `navigator.language`, the second from a string table (`en: Hello`, `de: Hallo`, picked by the first two letters of
   `navigator.language`), plus a text line from `Device.getLanguageCode()`. Run on a new iPhone 17 Pro simulator, iOS 26.4, launched with `xcrun simctl launch ... dev.shotfleet.capdemo <args>`;
   the text was read back through Maestro 2.11.0 `hierarchy` (which also shows that Maestro on iOS sees WKWebView text) and one screenshot of each state was taken:

   | Launch | `navigator.language` | String-table button | `Device.getLanguageCode()` |
   |---|---|---|---|
   | no argument | `en-GB` | Hello | `en` |
   | `-AppleLanguages "(de)"` | `de-DE` | **Hallo** | `de` |
   | `-AppleLanguages "(ja)"` | `ja` | Hello (no `ja` in the table, falls back) | `ja` |
   | `-AppleLanguages "(de)" -AppleLocale de_DE` | `de-DE` | Hallo | `de` |
   | system language set to German on the simulator, then rebooted | `de-DE` | Hallo | `de` |

   So on iOS 26.4 `-AppleLanguages` alone is enough, and `navigator.language` follows it; the forum report (iOS 17.4 and later, `navigator.language` stays on the system language) was **not reproduced**.
   What this does not show: a real device (simulator only), any iOS version other than 26.4, an app that sets its own language in code, and Android (the Android side stays [V]/[I] above).
   The verdict changes from "iOS unverified" to: per-language capture of a Capacitor app works on iOS 26.4 with the launch argument, for apps that read `navigator.language` or `@capacitor/device`.

7. **Round 2, 2026-10-05: iOS 18.6 and the Android WebView.** Evidence in `research/experiments-2026-10-04/B2/` (same throwaway app, rebuilt: Capacitor 8.x, Debug builds, web assets embedded; Maestro 2.11.0 `hierarchy` plus a screenshot per case; `run.sh` has a hard 30 min limit and removes only its own devices).
   **iOS 18.6 simulator** (iPhone 16 Pro, created for the run and deleted afterwards), the version family the Apple forum report is about (17.4 and later):

   | Launch | `navigator.language` | String-table button | `Device.getLanguageCode()` |
   |---|---|---|---|
   | no argument | `en-GB` | Hello | `en` |
   | `-AppleLanguages "(de)"` | `de-DE` | Hallo | `de` |
   | `-AppleLanguages "(ja)"` | `ja` | Hello (no `ja` in the table) | `ja` |
   | `-AppleLanguages "(de)" -AppleLocale de_DE` | `de-DE` | Hallo | `de` |
   | system language German, rebooted | `de-DE` | Hallo | `de` |

   **So the forum report is not reproduced on iOS 18.6 either**: `-AppleLanguages` alone reaches the webview on 18.6 and on 26.4. (The default row is read from the screenshot, `ios18-1-default.png`: Maestro's first hierarchy call after a boot returned nothing.)
   **Android 16 emulator (API 36, `shotfleet_android`), WebView `com.google.android.webview` 133.0.6943.137**, per-app language set with `adb shell cmd locale set-app-locales dev.shotfleet.capdemo --locales <tag>`:
   no setting `navigator.language=en-US`, Hello, `device=en`; `de`: `navigator.language=de`, **Hallo**, `device=de`; `ja`: `navigator.language=ja`, Hello (no `ja` in the table), `device=ja` (read from the screenshots in `B2/`). So on Android the per-app locale reaches the WebView, as the note above expected.
   **Maestro on the Android WebView is the weak side, as noted:** `hierarchy` returned only the status bar (and for `de` also "capdemo" and the first button) and nothing for the default and `ja` launches, although the screen was fully rendered; the iOS WebView text was read every time except the first call after boot. So language capture works; reading WebView text on Android through Maestro does not (issues 2293, 3497, 3646 above).
   What this still does not show: a real device, an app that sets its own language in code, Android older than 16 / other WebView versions, or Ionic-specific plugins.

## 8. NativeScript

1. **Build.** `ns build ios` (simulator build lands in `platforms/ios/build/Debug-iphonesimulator/`) and `ns build android` (APK in `platforms/android/app/build/outputs/apk/debug/`) [I, from CLI docs summaries; the doc page URL returned 404].
2. **Language.** Native views; the common plugin `@nativescript/localize` **converts `app/i18n/*.json` into native `values-*/strings.xml` and `*.lproj/Localizable.strings` at build time** (read in the plugin's `converter.ts` hook) **[V]**, so the OS locale mechanism applies directly.
3. **Maestro:** native views [I].
4. **Translations:** read straight from the build by the existing native readers (`load_strings`, `load_strings_apk`); keys are encoded but both languages encode alike [I]. `@nativescript-community/l` (4 stars) keeps a local JSON first, then native.
5. **Verdict: works today (probably)**, tiny audience (npm `@nativescript/core` 31k/week vs 16M for react-native) **[V]**. No code needed. Validate once if cheap.

## 9. Native web views (a native shell around a web page)

Same as section 7 for the Android/iOS language question, plus: for a remote site the translations are server-side (no files for shotfleet), `Accept-Language` follows the WebView's language, not the app's (the iOS 17.4 report above), and selectors can't be rewritten without the source strings. **Not realistic** unless the pages are bundled (then it is Capacitor).

## 10. Games and other engines

Godot 4.5 added AccessKit screen reader support for `Control` nodes on desktop; mobile support is shown for the 4.8 dev snapshots (news summary, not the release notes) **[I/V weak]**. Unreal has no accessibility tree for in-game UI [I]. Unity: section 6. **Not realistic for text selectors**; reduced mode as in section 6.

## 11. Consolidated code changes (function level)

| # | Change | Where | Effort | Why |
|---|---|---|---|---|
| 1 | `screen_text` returns None when the tree text is empty or under ~3 lines so OCR runs; today an empty tree gives a false "no text found" | `screen_text` (and tests) | S | bug 4, all non-accessible apps |
| 2 | i18next namespaces: prefix keys with the namespace when several JSON files share a locale folder; prefer the folder locale over a 2-3 letter file stem | `read_translation_file` (.json), `locale_from_path` | S | bugs 1-2, RN/Expo/Capacitor |
| 3 | `.po`: use the `Language:` header when the path has none; read `msgid_plural`/`msgstr[n]` | `read_translation_file` (.po) | S | bug 3, Lingui/gettext/Unity |
| 4 | `detect_framework(path)` from bundle markers (Flutter `flutter_assets`, RN `main.jsbundle`/`index.android.bundle`, Unity `UnityFramework`/`libunity.so`, MAUI `Microsoft.Maui` assemblies, Capacitor `public/` + `capacitor.config.json`) [I: markers are standard, confirm on real builds]. Use it in `cmd_init` (print the matching `strings = "..."` default glob and "0 languages" warning), in the `cmd_check` "no translations" error, and in `ios_run`/`android_run` when every selector is untranslated | new fn + `cmd_init`, `cmd_check`, `ios_run`, `android_run` | M | bugs 5, 7; also yields the framework for the signup question |
| 5 | Warn on RN Debug builds (no `main.jsbundle`) and on Flutter debug (DEBUG banner) | inside `detect_framework` consumers | S | sections 1, 3 |
| 6 | Print which languages `shipped_locales` dropped and why (e.g. "ja 30% translated; set locales to force") | `shipped_locales` callers | S | bug 6 |
| 7 | `.gz`/`.tar.gz`/`.tgz` hint for EAS simulator archives | `WRONG_BUILD`, `build_hint` | S | Expo/EAS |
| 8 | Read `.ts`/`.js` translation objects by dumping them with `node -e` when Node exists | `read_translation_file` | M | Ignite, vue-i18n, i18n-js, Expo guide |
| 9 | `l10n.yaml` / `i18next` config auto-discovery for the glob | `cmd_init`, `config_strings` | S-M | zero-config Flutter/RN |
| 10 | Android `<string-array>` in `load_strings_apk`/`strings.xml` reader | readers | S | KMP/native |

Nothing in `localize_flow`, `android_run`, or the language mechanism needs to change for any framework above except the verification experiments (Capacitor iOS, Unity iOS).

## 12. Validation plans (do not run; the owner approves downloads)

Common to all: `shotfleet doctor`; `shotfleet init <build>`; try `--locales en`, then 2 languages, then all; compare loaded strings with the source files; `shotfleet check`. Times are wall-clock on an Apple-silicon Mac including a first build, excluding toolchain installs (Flutter SDK ~1.5 GB, Unity ~10 GB, .NET MAUI workload ~several GB).

| Framework | Candidate (stars verified via GitHub API 2026-10-02) | Why | Build commands | What to check | Time |
|---|---|---|---|---|---|
| Flutter | [wger-project/flutter](https://github.com/wger-project/flutter) 977 stars, AGPL, 39 ARB locales, `integration_test/make_screenshots_test.dart` | real Weblate-translated app, partial languages (ja 30%), RTL (ar, fa, he), `localeConfig`, `.debug` suffix; also a ready screenshot test to compare against | `git clone --depth 1`, `flutter pub get`, `flutter build ios --simulator --debug`, `flutter build apk --debug`; config `strings = "lib/l10n/app_*.arb"`, `locales = ["de","ar","pt-BR","ja"]` | flow translates login/register labels with 0 untranslated; screenshots really in German/Arabic (RTL); DEBUG banner present; package `de.wger.flutter.debug`; ja falls back to English for 70% | 2-3 h |
| Flutter (alt.) | [flutter/samples](https://github.com/flutter/samples) 19,270 stars | has gen_l10n samples; tiny; but few real translations | same | reader only | 1 h |
| React Native / Expo | [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) 4,349 stars: Expo, i18next + expo-localization, `.maestro/` flows, `src/translations/{en,ar}.json` | smallest real Expo+i18next app with Maestro already wired; en+ar = exactly the 2-language free tier, plus RTL | `pnpm install`; `npx expo prebuild`; `npx expo run:ios --configuration Release --no-bundler -o ./out-ios` (build first without `--no-bundler` if needed); `npx expo run:android --variant release`; `strings = "src/translations/*.json"`; the template reads an `APP_ENV` variable, check its README | persisted `getLanguage()` empty on a fresh install so the launch argument wins; ar RTL (needs `supportedLocales` or RTL flips only on Android); Release has embedded JS; flows from `.maestro/` translate | 2-3 h |
| RN (large) | [bluesky-social/social-app](https://github.com/bluesky-social/social-app) 18,315 stars, Lingui, 53 `messages.po` locales | stress test of the `.po` reader (already ran 3 locales OK) | heavy native build, 30+ min | `.po` plurals, 3,000-string tables, `strings = "src/locale/locales/*/messages.po"` | 4 h |
| RN (bare) | [RocketChat/Rocket.Chat.ReactNative](https://github.com/RocketChat/Rocket.Chat.ReactNative) 2,415 stars, 67 locale JSONs; or [infinitered/ignite](https://github.com/infinitered/ignite) 19,940 stars (TS-object translations) | Rocket.Chat: flat JSON at scale; Ignite: proves the TS reader need | `yarn`, Release xcodebuild/`assembleRelease` | login screen needs no server | 3 h |
| KMP/CMP | [JetBrains/kotlinconf-app](https://github.com/JetBrains/kotlinconf-app) 3,564 stars, CMP, `values` + `values-de` (118 strings each) | official CMP app on iOS+Android, real translations | `xcodebuild -project app/iosApp/KotlinConf.xcodeproj -scheme KotlinConfAppScheme -configuration Debug -sdk iphonesimulator -derivedDataPath build build`; `./gradlew :app:androidApp:assembleDebug` | `.cvr` plural encoding; iOS accessibility tree non-empty (CMP version); en vs de on both platforms; whether the screens need network data | 2-3 h |
| .NET MAUI | [dotnet/maui-samples](https://github.com/dotnet/maui-samples) 3,655 stars, `10.0/Fundamentals/Localization/LocalizationDemo` (7 strings, de/es/fr/ja/pt/zh-Hans/zh-Hant, `CFBundleLocalizations` set, per-locale flag images) | official, tiny, flag image per locale proves the OS locale reached the app | sparse checkout of that folder; `dotnet workload install maui`; `dotnet build -f net10.0-ios -c Debug -p:RuntimeIdentifier=iossimulator-arm64`; `dotnet build -f net10.0-android -c Debug -p:EmbedAssembliesIntoApk=true`; `strings = "Resources/Strings/*.resx"` | labels translate; the native `values-*/Strings.xml` trap (bug 5); Debug APK installs and starts alone | 2 h (workload install separate) |
| Capacitor / Ionic | none found: searched GitHub topics (capacitor, ionic, i18n, ngx-translate, i18next); [aeharding/voyager](https://github.com/aeharding/voyager) 1,817 stars has no translations; [ionic-conference-app](https://github.com/ionic-team/ionic-conference-app) 3,587 stars has none. Build a throwaway app: `npm init @capacitor/app`, add i18next with `en.json`/`de.json`, two buttons | the one question that matters is whether `navigator.language` follows the launch argument on iOS 26 and Android per-app locale | `npm run build && npx cap sync`; `gradlew assembleDebug`; `xcodebuild ... -sdk iphonesimulator` | the displayed language in iOS and Android; Maestro text visibility in WKWebView and Android WebView | 1-1.5 h |
| NativeScript | [NativeScript/plugins](https://github.com/NativeScript/plugins) 205 stars, `apps/demo/src/i18n/{en,fr,fr-CA}.json` with `@nativescript/localize` (framework repo [NativeScript/NativeScript](https://github.com/NativeScript/NativeScript) 25,663 stars) | confirms the native-file path | `ns build ios`, `ns build android`; run `shotfleet init` on the outputs | init lists en, fr, fr-CA with no `strings` | 1.5 h |
| Unity / games | none verified; throwaway project: Unity 6, Localization package, 2 locales, a UI Toolkit button | answers three unknowns: `systemLanguage` under `-AppleLanguages`, empty Maestro tree, point-based flow plus `check` | Unity iOS Simulator SDK build + `xcodebuild`; Android APK | language reaches the game; `.texts.json` empty; with fix #1 `check` falls back to OCR | 3-4 h plus 10 GB install |

Order to run: wger, obytes, kotlinconf, MAUI sample, Capacitor throwaway; Unity last (and only if the owner wants the game segment).

## 13. (b) Signup form: "You ship on" today is iOS / Android / both

Keep it, and add one required single-choice question, **"Your app is built with"** (7 options, each maps to a reader and build command, and "Other" has a free-text field so NativeScript and Godot still show up):

1. Swift or Kotlin (native)
2. Flutter
3. React Native or Expo
4. Kotlin or Compose Multiplatform
5. .NET MAUI or Xamarin
6. Capacitor, Ionic or another web view
7. Unity, a game engine or other

Why: it mirrors section 11's `detect_framework`, so form answers and tool detection use the same categories; the split RN/Expo is not needed at signup (Expo is the majority of RN, `expo` 11.2M vs `react-native` 16.0M npm downloads/week). Optional second free-text field "Where do your translations live? (Lokalise, Crowdin, Phrase, files in the repo, other)": it tells us whether the `strings` glob or an export is the path.

## 14. (c) Which frameworks to support first

Market numbers I could verify:

- Statista 2023 (n=29,269): Flutter 46%, React Native 35%, Cordova 10%, Ionic 9%, Xamarin 8%, Kotlin Multiplatform 4% of cross-platform mobile developers.
- Stack Overflow Developer Survey 2024 (all respondents, "other frameworks and libraries"): Flutter 9.4%, React Native 8.4%, SwiftUI 4.3%, .NET MAUI 3.1%, Xamarin 2.9%, Ionic 2.5%, Cordova 2.2%, Capacitor 1.8%; other tools: Unity 3D 5.9%, Godot 4.4%, Unreal 3.0%. Among professionals Flutter 9.4%, React Native 9.0%. **The 2025 survey's technology page has no mobile-framework list** (languages, databases, cloud, web frameworks, IDEs, AI only), so 2024 is the latest.
- JetBrains Developer Ecosystem: Kotlin Multiplatform use 7% (2024) -> 18% (2025) (stated on kotlinlang.org).
- npm downloads, week 2026-09-24..30: react-native 16.0M, expo 11.2M, @capacitor/core 5.5M, @ionic/core 0.55M, @nativescript/core 31k; i18next 26.8M, react-i18next 19.9M, expo-localization 3.3M, react-native-localize 0.68M, @lingui/core 1.8M. pub.dev 30 days: intl 11.3M, easy_localization 293k, slang 301k. NuGet Microsoft.Maui.Controls 26.7M all-time. These count CI and transitive installs; use as relative sizes only.

Ranking = developers x ease (my 1-5 scores: size x ease). Ease means "works with today's code, needs the least hand-holding":

| Rank | Framework | Size | Ease | Score | Note |
|---|---|---|---|---|---|
| 1 | Flutter | 5 | 4 | 20 | one standard source format (ARB), real files pass; debug-only simulator builds (banner) are the cost |
| 2 | React Native + Expo | 5 | 3 | 15 | largest audience, fragmented i18n (JSON, Lingui, TS objects) and a Release-build requirement |
| 2 | Kotlin / Compose Multiplatform | 3 | 5 | 15 | zero config today; fastest to prove with kotlinconf-app |
| 4 | Capacitor / Ionic | 3 | 2 | 6 | build is easy; the language path is unverified on iOS |
| 4 | .NET MAUI | 2 | 3 | 6 | works with `strings`; small, enterprise-leaning |
| 6 | NativeScript | 1 | 4 | 4 | works through native files, tiny |
| 6 | Unity / games | 4 | 1 | 4 | big audience, no text in the accessibility tree; do not target |

Do first: fixes 1-4 of section 11 (a day of work total), then wger and obytes real runs, publish "Flutter, React Native/Expo and Compose Multiplatform" as tested only after those pass (the README admits sample-only today).

## 15. Real runs on a Mac, 2026-10-03

First runs of the plans in section 12 on a device. Mac: Apple silicon, Xcode 27.0 (iOS 26.4 simulator), Android SDK with the `shotfleet_android` AVD, Maestro 2.0.10, Flutter 3.47.6 (`brew install --cask flutter`), Node 26. Apps were shallow clones in a scratch folder. Screenshots (resized), flows, configs, `run.log` and `check` output: `research/real-apps-2026-10-03/<app>-<platform>/`. Today's date is the date of every number below; one run per cell unless it says otherwise.

**What passed**

| App (framework, build) | Platform | `init` with no arguments | Languages run | Result |
|---|---|---|---|---|
| wger-project/flutter (Flutter, debug) | iOS | found `build/ios/iphonesimulator/Runner.app`, wrote `strings = "lib/l10n/*.arb"` (19 languages shipped, 37 files), printed the DEBUG-banner hint | de, ja | de 3/3 in German; ja 3/3 but mostly English (see below). Capture 48 s, whole run 82 s |
| wger | Android | found `build/app/outputs/flutter-apk/app-debug.apk` (`de.wger.flutter.debug`; the iOS id is `de.wger.flutter.community`, one flow serves both) | de, ja | same; capture 61 s |
| obytes template (Expo + i18next, Release) | iOS | found `ios/build/Build/Products/Release-iphonesimulator/ObytesApp.app`, wrote `strings = "src/translations/*.json"` (ar, en) | en, ar | en 3/3, ar 3/3; Arabic and right-to-left on the Settings screen. Capture 74 s |
| obytes | Android | found `android/app/build/outputs/apk/release/app-release.apk`, same line | en, ar | same, tab bar flipped too. Capture 100 s |
| JetBrains/kotlinconf-app (Compose Multiplatform, Debug) | iOS | found the DerivedData `KotlinConf.app`; no `strings` needed, read de and en from the build | de, en | 6/6, `check` 0 problems. Capture 56 s |
| kotlinconf-app | Android | found `androidApp-debug.apk` | de, en | 6/6, `check` 0 problems. Capture 56 s |

Flows (3 screenshots each): wger login, the Advanced sheet, its Self-hosted option; obytes onboarding, login, Settings; KotlinConf privacy notice, notifications, Info. I looked at the German, Arabic and Japanese images by eye: the text is in those languages.

**What did not pass, or passed with a caveat**

| What | Detail |
|---|---|
| wger ja | The app's Japanese is about 30% done: Flutter falls back to English per string. `check` flags it both ways: in the run ("shows en strings (6 lines) more than ja (0)") and, with `--strings`, "the app has no ja translation, so this listing shows another language". Correct behaviour, but a Japanese listing from wger is not usable. |
| obytes onboarding and login | Hard-coded English in the template (only Settings uses i18next). The flow's three selectors for them (`Obytes Starter`, `Let's Get Started`, `Not Now`) are reported as untranslated, and `check` flags `ar/01_onboarding` and `ar/02_login` ("text looks like 'en', expected 'ar'"). Right again; they are the app's, not shotfleet's. The tab bar is also hard-coded English on iOS. |
| DEBUG banner | Appears on every wger screenshot on iOS (expected) and also on Android (the Android build is a debug APK too). No React Native red box (Release builds), no Metro. |
| `expo run:ios` as written | Fails after the 11-minute `pod install`: Xcode 27 has no Simulator.app, so Expo cannot "open the Simulator". Built with `xcodebuild -workspace ios/ObytesApp.xcworkspace -scheme ObytesApp -configuration Release -sdk iphonesimulator -derivedDataPath build IPHONEOS_DEPLOYMENT_TARGET=15.1` instead (Xcode 27 rejects the pods' deployment targets of 9.0 and 12.4 without that override). `npx expo run:android` needs a running emulator; used `npx expo prebuild --platform android` then `./gradlew assembleRelease`, which failed twice in `react-native-reanimated` (it looks for `react-native-worklets/android/build/intermediates/cmake/release/obj/...so`, which AGP wrote under `cxx/RelWithDebInfo`) and passed on the third run (3 min 44 s) once those files were copied to the expected folder. |
| kotlinconf-app iOS build | The documented `xcodebuild` fails on Xcode 27 with "Xcode Requested Architecture Not Configured in Gradle: ios_x64"; `ARCHS=arm64 ONLY_ACTIVE_ARCH=YES` fixes it. The Android build needs `sdk.dir` in `local.properties` (or `ANDROID_HOME`). |
| wger Android build | 1005 s on the first build because Gradle downloaded NDK r28c and CMake 3.22.1; the iOS build took 89 s. |
| kotlinconf-app has no `ja` | Only `values` and `values-de`; so de and en were run (a `ja` run would have been English). |

**The four questions**

1. *Does the language reach the app?* Yes, everywhere: iOS `-AppleLanguages` reached Flutter, the Expo/Hermes app (i18next `lng` from `expo-localization`, nothing persisted on a fresh install) and Compose Multiplatform; Android `cmd locale set-app-locales` reached all three. Arabic right-to-left reached both platforms of the Expo app. No code change was needed for this.
2. *Does Maestro see the text?* Flutter: yes, through implicit `Semantics`; no `Semantics` code was added to wger. Gotcha found: Flutter merges a row's texts into one label with a newline (`Selbst gehostet\nMit deiner eigenen Instanz verbinden`, and `New to wger? Register` is one label), so `tapOn: "Self-hosted"` finds nothing even in English. `tapOn: "Self-hosted.*"` matches. shotfleet used to leave such a selector untranslated (so German failed); it now translates the text inside a leading or trailing `.*` (code change below). Expo: `id:` selectors (`testID`) worked for all inputs, the tab and the button; text selectors worked on Settings. No `accessibilityLabel` was involved, so issue 1409 was not met. Compose: iOS tree non-empty with a current Compose (text selectors worked); Android fine.
3. *Untranslated selectors in the run output?* wger 0 (after the `.*` change), kotlinconf 0, obytes 3 (the app's own English, above).
4. *DEBUG banner or red box?* Banner yes (wger, both platforms); red box no.

**Other findings from the runs**

- **A blank first screenshot, and `check` did not flag it.** wger on Android (a Flutter debug build is slow to draw its first frame on a fresh emulator): `01_login.png` was a white screen with only the status bar; and KotlinConf on iOS (Compose has the text in the accessibility tree before it paints): the first image was white. Both were caught only by luck (a second language with the same white image: "identical image in 2 languages"). A single-language run would have passed. Fixes in the flows: `extendedWaitUntil: visible: "Log in", timeout: 60000` (wger) and a 3 s pause (`extendedWaitUntil: notVisible: id: "no-such-id", timeout: 3000`) after the wait (KotlinConf). Candidate for shotfleet: `check` could flag a screenshot with no content (hand-off item below).
- **A first Android launch of a Flutter debug app can take longer than Maestro's default wait**: the first attempt with a plain `assertVisible: "Log in"` failed on both shards, shotfleet's retry then passed. The long `extendedWaitUntil` avoids the retry (61 s instead of 87 s).
- **iOS Arabic keyboard in a secure field:** `inputText: "password123"` typed only 3 characters (`•••`) in the Arabic run, nothing at all when split into chunks, while `123456` typed fine; English was fine. The flow uses digits. Not a shotfleet problem; worth a line in Tips.
- **A "Save Password?" system sheet** appears after the Expo login form on iOS and swallowed the next tap in the Arabic run; `tapOn: {text: "Not Now", optional: true}` handles it. `Not Now` is now a known system button (kept in English, no "untranslated" report).
- Memory pressure on a busy Mac: shotfleet used 1 simulator or emulator instead of 2 (it says so), which is why the capture times above are one-device times.
- `shotfleet check <out>` run on its own, without `--strings`, does not know the app's translations: wger iOS said 0 problems although the Japanese is English; with `--strings 'lib/l10n/*.arb'` it says what is true. `run` passes the strings itself.

**Code changes made for this** (with tests in `tests/test_shotfleet.py`): `translate_flow` translates the text inside `.*Text` and `Text.*` selectors; `Not Now` joins the system buttons.

**Not run:** bare React Native, other Flutter and Expo apps, Capacitor, MAUI, Unity, Maestro 2.11, iPad and tablet sets, the full 37 (wger) languages, a real Flutter *release* build on Android.

## 16. Device window, 2026-10-04 (13:21-14:05): checking the fixes of section 15

Same Mac (Apple silicon, Xcode 27, iOS 26.4 simulator, Maestro 2.0.10), run inside the shared device queue. Evidence: `research/real-apps-2026-10-04/` (logs, `check.json`, `run.json`, resized screenshots; `window.log` has load, free memory and disk before each step).

**Correction to section 15.** In the last KotlinConf iOS run of 2026-10-03 the English first screenshot (`01_privacy`) was a blank white frame and `check` passed it; the evidence image in `research/real-apps-2026-10-03/kotlinconf-ios/en-01_privacy.png` is that blank frame, and "6/6, 0 problems" for KotlinConf iOS was wrong for that image. `blank_screenshot()` flags it. A clean pair needs a longer wait than the 3 s pause used then (see below).

| Check | Result |
|---|---|
| Blank frame found by `check` and `run` (KotlinConf iOS, flow without any wait before the first screenshot) | The first capture of both languages was blank; `run` printed `retrying 2: de, en`; the second capture was blank again, so both ended `FAIL ... blank screenshot(s): 01_privacy.png (the app had not drawn its first frame ...)` and `check` said `blank: nothing is drawn on it yet` plus `identical image in 2 languages`. So the capture-again step does **not** heal a deterministic blank (Compose paints after the text is readable every time); it only helps a transient one. The fix is in the flow: wait for text, then pause. Before this change that run would have passed `run` with the white frames. |
| Same flow on KotlinConf Android | 2/2 languages ok, 6 screenshots, `check` 0 problems, 105 s, so Android does not need the pause. |
| Flutter **release** APK on Android (wger, de + ja) | 2/2 languages ok in 69 s on 1 emulator; German, no DEBUG banner, first screenshot not blank; `check` flags ja like the debug build (27% translated). The `init` hint "on Android use flutter build apk --release" is right. Build: a release APK needs a signing key (wger reads `fastlane/metadata/envfiles/key.properties`); a throwaway `keytool -genkeypair` key works for a local build. |
| Warning before the run for a half-translated language | Printed for real: `warning ja: only 27% of the app's own strings are translated, so the ja screenshots will mostly show en` (wger) and `warning ar: only 26% ...` (Rocket.Chat). |
| wger Android, all 19 shipped languages | 19/19 captured, 3 screenshots each, **822 s on 1 emulator** (memory pressure cut 2 to 1; the first ~13 min ran under a load of 135 to 150 from another session's emulator, so this is not a clean timing). `check`: 60 screenshots in 20 languages (a stale `ja` folder from the earlier run was still in the output folder), 20 problems, all of the kind "shows en strings": **ca, it, nl, pl, pt, pt-PT, ro and zh-Hant show the English text on the Advanced screens** although they pass the 50% rule, because the Advanced sheet is newer than their translations. The 50% rule counts the whole app, not the screens in the flow; `check` is what catches it. |
| wger iOS, all 19 languages | **Not run**: the simulator never finished booting (`simctl bootstatus did not answer within 900 s`), under the same load. To repeat. |
| Arabic password typing on iOS (Expo app) | Letters typed into a secure field are dropped when the app runs in Arabic: `abcdef` typed nothing, six single letters nothing, `abc123` typed only `123` (3 dots), and earlier `123456` typed all six. Name and e-mail fields take letters. Not shotfleet's doing; documented in README Tips and `troubleshooting.md`. |
| Rocket.Chat (bare React Native, 67 locale files) | Builds: Android release APK 214 MB (Gradle, 3 attempts' worth of setup: needs `-PKEYSTORE...` for the release signing), iOS Release needs `-destination 'generic/platform=iOS Simulator'` instead of `-sdk iphonesimulator` (its Watch app target fails with "no such module WatchKit"), `ARCHS=arm64`, `IPHONEOS_DEPLOYMENT_TARGET=16.4`; pods 11 min. `init` after the fix: React Native, `app/i18n/locales/*.json`, 25 languages, 16 shipped. First screens (en, de, ar on both platforms, 3/3): only the splash (red, logo) was captured because the starter flow's 5 s wait is shorter than the Release JS boot; the accessibility tree held only the app name. `ar` is 26% translated (warning printed). A real flow is still to be written. |
| First try of the KotlinConf step | `no simulator app at .../DerivedData/...`: another session had cleaned DerivedData; the app was rebuilt into the scratch folder. |

**Code changes after this window:** none beyond the README/troubleshooting lines; the blank check, the retry, the half-translated warning and the `init` fixes behaved as designed.

## 17. Follow-up window, 2026-10-04 22:45 to 2026-10-05 07:00: nothing usable, one product fix

The follow-up of section 16 (clean KotlinConf iOS pair, wger Android and iOS in 19 languages, Rocket.Chat exploration) held the device lock for **8 h 15 min** and produced no screenshots. Logs in `research/real-apps-2026-10-05/`; load, memory and disk per step in `research/real-apps-2026-10-04/window.log`.

| Step | What happened |
|---|---|
| KotlinConf iOS, 6 s pause | `captured 0/2 locales in 4425s`, `no result (see maestro log)`, whole command 6285 s. The Mac was at load 135 to 340 (the release-gate rerun and other sessions' jobs), and the simulator never answered. |
| wger Android, 19 languages (clean timing for E1) | Refused to start in 926 s: `each emulator wants about 3 GB of free memory and 2 CPU cores` (the emulator's setup log is printed with it). Not a timing. |
| wger iOS, 19 languages | Hung for **6 h 14 min with 0 screenshots**: Maestro (5 h 33 min old) against my `shotfleet-1` simulator, which had never finished booting. shotfleet had no way to notice: its only time limit is `timeout_s` x languages (600 s x 19 = 3 h per batch, then a retry batch). I killed my own process chain by exact PID, shut the simulators down and released the lock. |

My waiter script had no maximum run time either, so I held the lock for 8 h without noticing; the next waiters (small experiments, the Play screenshots job) lost that time.

**Product fix (this branch):** `run_guarded` watches progress: when no new screenshot appears for `stall_s` seconds (default 900, config key `stall_s`), Maestro and its drivers are killed and the run takes the existing retry path, printing `maestro made no new screenshot for N s and was stopped`. Unit-tested (`StalledRun.*`, claim C130). Not yet seen on a device (the situation that triggers it needs a hung simulator).

**Still not run on a device:** a clean wger Android 19-language timing (needs a quiet Mac with 3 GB per emulator free), wger iOS in 19 languages, Rocket.Chat with a real flow, a clean KotlinConf iOS pair with a longer wait.

## Six-line summary

1. Works today: Kotlin/Compose Multiplatform (native readers), Flutter (ARB, real wger files read fine) and RN/Expo (i18next JSON, Lingui `.po`) with Release builds, MAUI via `.resx`, NativeScript via native files (probable).
2. Real bugs I reproduced: i18next namespaces collide and 3-letter file names read as locales, `.po` ignores the Language header and plurals, and an empty accessibility tree gives a false "no text found" instead of falling back to OCR.
3. Build traps: RN/Expo need Release (Debug needs Metro; dev clients and Expo Go unusable), Flutter simulator builds are debug-only (DEBUG banner), MAUI Debug APK needs `EmbedAssembliesIntoApk=true`.
4. Hard cases: Capacitor on iOS (WKWebView language may ignore the per-app language since iOS 17.4, unverified) and Unity/games (no text in the tree: not realistic for selector rewriting).
5. Add `detect_framework` (hints, "use strings=" default globs, signup categories) plus the S-size reader fixes; validation order wger, obytes, kotlinconf-app, MAUI LocalizationDemo, a throwaway Capacitor app.
6. Support order by developers x ease: Flutter, then RN/Expo and KMP/CMP, then MAUI and Capacitor/Ionic, then NativeScript, last Unity/games; signup gets a 7-option "Your app is built with" question.

## Sources

Primary docs and code (fetched 2026-10-02):
- Maestro docs: [React Native](https://docs.maestro.dev/get-started/supported-platform/react-native.md), [Flutter](https://docs.maestro.dev/get-started/supported-platform/flutter.md), [Jetpack Compose](https://docs.maestro.dev/get-started/supported-platform/android/jetpack.md), [launchApp](https://docs.maestro.dev/reference/commands-available/launchapp.md), [known issues](https://docs.maestro.dev/extra-materials/troubleshooting/known-issues.md). Issues: [1409](https://github.com/mobile-dev-inc/maestro/issues/1409), [3056](https://github.com/mobile-dev-inc/maestro/issues/3056), PR [3165](https://github.com/mobile-dev-inc/Maestro/pull/3165), [2293](https://github.com/mobile-dev-inc/Maestro/issues/2293), [3497](https://github.com/mobile-dev-inc/Maestro/issues/3497), [3646](https://github.com/mobile-dev-inc/Maestro/issues/3646), PR [3384](https://github.com/mobile-dev-inc/Maestro/pull/3384).
- Android: [per-app language preferences](https://developer.android.com/guide/topics/resources/app-languages); AOSP [LocaleManagerService.java](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/locales/LocaleManagerService.java).
- Flutter: [i18n docs](https://docs.flutter.dev/ui/internationalization), [build modes](https://docs.flutter.dev/testing/build-modes), [debugShowCheckedModeBanner](https://api.flutter.dev/flutter/material/MaterialApp/debugShowCheckedModeBanner.html), engine [FlutterEngine.mm](https://github.com/flutter/flutter/blob/master/engine/src/flutter/shell/platform/darwin/ios/framework/Source/FlutterEngine.mm), [LocalizationPlugin.java](https://github.com/flutter/flutter/blob/master/engine/src/flutter/shell/platform/android/io/flutter/plugin/localization/LocalizationPlugin.java), issues [109842](https://github.com/flutter/flutter/issues/109842), [177386](https://github.com/flutter/flutter/issues/177386).
- Expo: [localization SDK](https://docs.expo.dev/versions/latest/sdk/localization/), [localization guide](https://docs.expo.dev/guides/localization/), [simulator builds](https://docs.expo.dev/build-reference/simulators/), [APK builds](https://docs.expo.dev/build-reference/apk/), [Expo CLI compiling](https://docs.expo.dev/more/expo-cli/).
- React Native: [template build.gradle](https://github.com/react-native-community/template/blob/main/template/android/app/build.gradle), [template Info.plist](https://github.com/react-native-community/template/blob/main/template/ios/HelloWorld/Info.plist), [react-native-localize](https://github.com/zoontek/react-native-localize) (README, `RNLocalize.mm`), [i18next-react-native-language-detector](https://github.com/DylanVann/i18next-react-native-language-detector).
- Compose Multiplatform: [localize strings](https://kotlinlang.org/docs/multiplatform/compose-localize-strings.html), PR [5180](https://github.com/JetBrains/compose-multiplatform/pull/5180), [CMP-8376](https://youtrack.jetbrains.com/issue/CMP-8376), core PR [1780](https://github.com/JetBrains/compose-multiplatform-core/pull/1780), issue [4401](https://github.com/JetBrains/compose-multiplatform/issues/4401), [kotlinconf-app](https://github.com/JetBrains/kotlinconf-app), [KMP reasons](https://kotlinlang.org/docs/multiplatform/multiplatform-reasons-to-try.html).
- .NET: MAUI [localization](https://github.com/dotnet/docs-maui/blob/main/docs/fundamentals/localization.md), [dotnet/android build properties](https://learn.microsoft.com/en-us/dotnet/android/building-apps/build-properties), [LocalizationDemo](https://github.com/dotnet/maui-samples/tree/main/10.0/Fundamentals/Localization/LocalizationDemo).
- Capacitor: [HybridMob guide](https://hybridmob.com/tutorials/e2e-testing-ionic-capacitor-playwright-maestro), [Capawesome app-language](https://capawesome.io/docs/sdks/capacitor/app-language/), Apple Developer Forums [thread 750119](https://developer.apple.com/forums/thread/750119).
- NativeScript: [@nativescript/localize hooks](https://github.com/NativeScript/plugins/tree/main/packages/localize/hooks), [nativescript-community/l](https://github.com/nativescript-community/l).
- Unity: [Application.systemLanguage](https://docs.unity3d.com/ScriptReference/Application-systemLanguage.html), [Localization CSV](https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/CSV.html), [mobile screen reader](https://unity.com/blog/engine-platform/mobile-screen-reader-support-in-unity). Godot: [4.5 release](https://godotengine.org/releases/4.5/).
- Market: [Statista 2023](https://www.statista.com/statistics/869224/worldwide-software-developer-working-hours/) (page title "Cross-platform mobile frameworks used by global developers 2023"), [SO survey 2024 technology](https://survey.stackoverflow.co/2024/technology), [SO survey 2025 technology](https://survey.stackoverflow.co/2025/technology), npm registry download API, pub.dev score API, NuGet search API.
- Repo stars from `gh api repos/<owner>/<repo>` on 2026-10-02.
- Local: `research/real-apps.md`, `shotfleet.py` functions named above; my test files are in the session scratchpad (`t/`, `real/`).
