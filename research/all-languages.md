# Supporting all languages and localization setups

Research date 2026-10-01. Nothing here was run against a simulator, emulator, Maestro flow, Gradle or xcodebuild, and nothing was installed.
Evidence tags: **[measured]** = run on this Mac (macOS 27) in the scratchpad; **[docs]** = from a linked page; **[source]** = read from the Maestro 2.0.10 jars in `~/.maestro/lib`; **[unverified]** = from general knowledge, needs a test before relying on it.

Experiments live in `/private/tmp/claude-501/.../scratchpad/limits/` (`jobs.json` + `el.png`...: rendered test screens, `vr.swift`: Vision language lists, `vk.swift`: VisionKit ImageAnalyzer, `vo.swift`: Vision options, `fmt.py`: format-string to regex prototype with asserts).

## Summary of the plan (priority order)

| # | Work | Limit | Effort | Why first |
|---|------|-------|--------|-----------|
| 1 | Make the check **diacritic- and digit-tolerant** (`norm()` on both sides: NFC, strip bidi marks, NBSP/NNBSP to space, native digits to ASCII, Persian yeh/kaf, accent-folded fuzzy match) and stop trusting Vision's language guess for unreadable scripts | A, D | S | Fixes false failures today (Hungarian, Persian, French) with ~40 lines |
| 2 | **Generic "strings from files" loader** (`strings = [...]` globs: ARB, i18next/JSON, .po, XLIFF, .resx, CSV, Android `strings.xml`, `.xcstrings`, `.stringsdict`, plurals), keyed by locale from filename/content | B, C, D | M | One feature unlocks Flutter, RN, Capacitor, NativeScript, MAUI, Unity-export, KMP-moko, Lokalise/Crowdin; builds are optional |
| 3 | **Format/plural engine**: parse printf, `{name}`, ICU plural/select, `.stringsdict`, `<plurals>`; produce (a) a regex per target string and (b) a re-render from arguments extracted out of the English selector | C | M | Required by #2 and by existing native apps (CrossfitTracker already ships `.stringsdict` that `load_strings` ignores) |
| 4 | **Base-language and region-only support**: `base = "de"` config, `--base-from-selectors`, locale fallback chain (en-GB -> en -> Base) | D | S | Removes the "English only" assumption in `translate_flow` and `shipped_locales` |
| 5 | **UI-hierarchy evidence** captured at each `takeScreenshot` (iOS XCTest `/viewHierarchy`, Android `uiautomator dump`), used as the primary language proof, OCR as fallback | A | M-L | Covers every script, exact Unicode, no OCR language limit |
| 6 | Optional **second OCR engine** (Tesseract script models, user-installed) only for screens with no hierarchy text (games, Canvas, Unity) | A | M | Last resort; heavy install, mediocre quality on UI text |
| 7 | Static-bundle readers (Hermes string table, MAUI satellite assemblies, Unity asset bundles) | B | L | Only if users demand "no config" support; source files are far cheaper |

Not recommended: cloud OCR as a default (privacy and per-image cost; screenshots of unreleased apps), ML Kit (Android in-app SDK, not a Mac tool), glyph-coverage heuristics (nothing credible; see A3).

---

## A. OCR limit (Vision reads 33 languages)

### What macOS 27 really does [measured]

`VNRecognizeTextRequest.supportedRecognitionLanguages()` per revision on this Mac:

- revision 3, `.accurate`: 33 codes (the list in the task). revision 2 `.accurate`: 8. `.fast`: 6 (en fr it de es pt). Only revision 3 `.accurate` is worth using; `ocr.swift` already does.
- **VisionKit `ImageAnalyzer` (Live Text) gives identical output** on the same test images (Greek: `PuOuíozIŞ`, Hebrew/Georgian: empty, Hungarian: `Beallitasok`). It is the same engine, so it is not a way to more languages. [measured: `vk.swift`]

Rendered 3 short UI lines per script (system font, 46 px) and ran `.build/ocr`:

| Script | Result | Consequence |
|---|---|---|
| Greek | Latin garbage, `lang=hu` | Looks like text but is wrong; the check must not treat it as evidence |
| Hebrew, Georgian, Burmese | empty string | `chars == 0` -> "no text found" problem for a healthy screen |
| Armenian | Latin-ish garbage, `lang=tr` | wrong-script output |
| Tamil, Telugu, Khmer | Thai-script garbage, `lang=th` | a Tamil screenshot would be "provably Thai" |
| Bengali | Devanagari garbage, `lang=hi` | same |
| Amharic | `tch`, `lang=cs` | same |
| Hungarian | `Beallitasok`, `Elözmények ööüü` | **diacritics lost**: `ő`->`ö`, `ű`->`ü`, `á`->`a`, `í`->`i` on a Latin-script language that is not in the list |
| Croatian | `Cšždć` (case drift, but `Čšžđć` mostly kept) | mostly OK |
| Persian | `تنظيمات`, digits `٢` `١٢` (Arabic-Indic, not Persian `۲`), `ی`->`ي` | Arabic model reads Persian with letter and digit substitutions |
| Arabic | exact, digits `٢` `١٢` | fine |

One bug follows in `judge_screen` today: for **Hebrew** and **Burmese** (and Georgian) Vision returns nothing, so `if not ocr.get("chars")` fires "no text found (blank or still loading?)" **before** the `readable_languages()` test; a healthy screen is reported as a problem. Fix: test readability first. Second, garbage in another script (Tamil read as Thai) is not caught as wrong-language only because `want` is unreadable and `lang != "en"`; keep that branch, and never let the script-detection regexes in `SCRIPTS` credit garbage. [source: `shotfleet.py` lines ~694-720]

### A1. Read text from the UI hierarchy instead of pixels (recommended)

**What exists in Maestro 2.x**

- `maestro hierarchy [--compact] [--[no-]ansi]` prints the current screen's hierarchy of the connected device. `--compact` = CSV `element_num,depth,attributes,parent_num`. As of 2.6.0 the output is pure JSON (our installed CLI is 2.0.10, where the output may still carry headers). [docs: Maestro 2.6.0 blog https://maestro.dev/blog/maestro-cli-v2-6-0, `maestro hierarchy --help` run locally]
- Per element attributes (`text`, `accessibilityText`, `hintText`, `resource-id`, `bounds`, `clickable`, `focused`, `checked`, `selected`, `enabled`, `class`). iOS: from XCTest `AXElement` = `identifier, frame, value, title, label, elementType, enabled, selected, hasFocus, placeholderValue, children` and Maestro maps `label/value/title` into `text`/`accessibilityText`. [source: AXElement fields in `maestro-ios-driver.jar`; docs search result]
- **In-flow capture does not exist.** `maestro test` writes the view hierarchy (`screen-hierarchy/*.json`) **only for failing steps**. [docs: https://docs.maestro.dev/maestro-flows/workspace-management/test-reports-and-artifacts] So there is no flag that dumps one per `takeScreenshot`.

**Ways to get one per screenshot (cost estimates are [unverified]; measure when the Mac is free)**

1. **Barrier via the flow's own HTTP call (best).** Maestro's GraalJS `http.get/post` can call a local server. shotfleet already rewrites `takeScreenshot`; add a line after each one:
   ```yaml
   - takeScreenshot: ...
   - runScript:
       file: snap.js       # http.get('http://127.0.0.1:PORT/snap?locale=de&name=01_home&dev=<udid>')
   ```
   shotfleet runs a tiny `http.server` thread. The handler dumps the hierarchy and answers only when finished, so Maestro does not execute the next tap until the dump is saved: **no race**. (Without a barrier, polling the shots folder and dumping when a PNG appears races the next tap.) `snap.js` is generated per run, like the existing flow rewrite. Check `runScript` + `http` is available in 2.0.10 (it is documented in Maestro's JavaScript docs; verify).
2. **Segmenting** the flow at each `takeScreenshot` into separate `maestro test` runs and calling `maestro hierarchy` between them. Deterministic but pays Maestro JVM start + driver handshake per segment (several seconds on iOS), and app state must survive between runs (no `launchApp` in later segments). Not recommended.
3. **Direct dump without Maestro.**
   - **iOS simulator:** Maestro's XCTest runner is an HTTP server on `localhost:22087`: `POST /viewHierarchy` with body `{"appIds":["com.example.app"],"excludeKeyboardElements":false}` returns the `AXElement` tree JSON; `GET /status`, `GET /deviceInfo`, `GET /screenshot` also exist. [docs: https://deepwiki.com/mobile-dev-inc/Maestro/4.1-ios-driver-architecture; request class `ViewHierarchyRequest(appIds, excludeKeyboardElements)` [source]]. **Port caveat:** issue https://github.com/mobile-dev-inc/Maestro/issues/3611 says every simulator session uses 22087 by default, so with shotfleet's parallel simulators the port per device must be discovered (`lsof -iTCP -sTCP:LISTEN -P | grep xctest`, or the driver-host-port Maestro assigns under `--shard-split`) before posting. Test with 2 sims.
   - **Android:** `adb -s <serial> exec-out uiautomator dump /dev/tty` prints XML (`<node text="" content-desc="" resource-id="" bounds="[..]" ...>`) to stdout; typically 0.5 to 2 s. **Risk:** Maestro's Android driver is itself an instrumentation (`dev.mobile.maestro`) holding a UiAutomation connection; a second `uiautomator` process can fail ("UiAutomation not connected" / already registered) on some API levels. [unverified: test]. Fallback if it conflicts: ask the device's Maestro driver through the same gRPC (`MaestroDriver.viewHierarchy`, port 7001 forwarded by dadb) from the barrier server, which is more work, or run `maestro --udid <id> hierarchy` from the barrier (a second CLI JVM; test whether Maestro allows two clients).
4. `maestro mcp` exposes hierarchy tools, but it is a second server on the same devices; same port problem as #3 (issue 3611). Skip.

**Output format to store:** keep a normalized list per screenshot `[{"text": ..., "label": ..., "value": ..., "hint": ..., "id": ..., "bounds": [l,t,r,b], "visible": bool}]` in `raw/<locale>/<name>.hier.json`; discard nodes outside the screen rectangle and nodes with zero size.

**Blind spots (what the hierarchy cannot prove)**

- Text drawn as image, Canvas, OpenGL/Unity, Lottie, custom `draw()`: **absent** (Compose `Canvas.drawText`, Flutter `CustomPainter`, game UIs). Fallback to OCR for those screens.
- Text that exists but is not shown: off-screen rows, `alpha 0`, covered by a modal (iOS driver explicitly "disables snapshotKeyHonorModalViews to make elements behind modals visible" [source]), collapsed accordions. Filter by bounds and ignore `visible=false`; the iOS driver has no hidden flag, so intersect with the screen frame.
- **Hierarchy proves the app asked for the string, not that it rendered**: missing glyphs (tofu on Khmer/Burmese/Amharic when the emulator image lacks a font), clipped or truncated text, overlapping elements, white-on-white. Pair with a cheap pixel check (A3).
- Truncation `...`: the accessibility label/`text` holds the **full** string even when the screen shows "Start work..." (iOS `label`, Android `text`). So the hierarchy cannot detect truncation; OCR still can (look for `…` at line end).
- Labels vs visible text: SwiftUI `.accessibilityLabel("Close")` replaces the visible text in `label`; `Image` + `Text` buttons merge into one element with label "Close, button"-style content; Compose `contentDescription` and `mergeDescendants=true` (parent shows empty `text`, children keep theirs; Maestro issue https://github.com/mobile-dev-inc/maestro/issues/2704). Match against `text`, `label`, `value`, `hint` and `title` (any), as Maestro itself does for selectors.
- iOS `value` vs `label`: text fields give the typed text in `value`, the field name in `label`, placeholder in `placeholderValue`. Dynamic type, `%@` user data and masked password fields contribute arguments that need a wildcard (see C).
- Flutter: semantics tree is merged (several lines joined with newlines in one node) and exists only if accessibility is on; Maestro works with Flutter apps but text of widgets wrapped in `ExcludeSemantics` is invisible. WebView: Android WebView content does appear in the tree when accessibility is enabled (and Maestro handles it), iOS WKWebView does too; canvas-based web UIs do not. [unverified for each framework; test on one sample]
- Cost summary: one extra HTTP call per screenshot (about 1-2 s iOS, 0.5-2 s Android [unverified]); a 5-screen flow in 18 locales adds roughly 2-3 min of CPU spread across parallel devices.

**How to use it in `judge_screen`:** score each locale by number of hierarchy strings exactly equal to its table (same as the OCR line match, but exact Unicode, so diacritics, Hebrew, Greek, Khmer, Burmese all work). Treat hierarchy text as `lines`, keep OCR only if the hierarchy has fewer than N text nodes or the language is readable and the screen is mostly Canvas.

**Effort: M** for Android+iOS + barrier + judge change, **L** if the Android UiAutomation conflict needs the gRPC fallback. Also unblocks `shotfleet check` of already-made screenshots only partially: there is no hierarchy for old PNGs, so OCR remains the path for `check` (see A2/A3).

### A2. Other OCR engines usable on a Mac

| Engine | Languages | Quality on short UI text | License | Install | Speed | Verdict |
|---|---|---|---|---|---|---|
| **Vision / Live Text** (current) | 33 (above); same set in VisionKit [measured] | good, but loses diacritics outside list | OS | none | ~0.3-1 s per image | keep |
| **Tesseract 5** + `tessdata_best` | 100+ languages and 37 scripts incl. Greek, Hebrew, Armenian, Georgian, Bengali, Tamil, Telugu, Kannada, Malayalam, Sinhala, Khmer, Lao, Burmese, Amharic, Devanagari, Gujarati, Punjabi, Odia [docs: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html, https://github.com/tesseract-ocr/tessdata_best] | designed for scanned pages; UI text with icons, gradients and small sizes needs preprocessing (upscale 2x, grayscale, `--psm 6/11`); expect gaps on Indic conjuncts and Burmese [unverified] | Apache-2.0 | `brew install tesseract tesseract-lang` (tesseract-lang is roughly 600 MB with all packs; `tessdata_best` per language 15-30 MB, script models like `Devanagari`, `Greek`, `Hebrew` 10-30 MB) | 0.5-3 s per screen | best free fallback; user installs it |
| **PaddleOCR PP-OCRv5** | 106 languages via multilingual rec models incl. Greek, Thai, Tamil, Telugu; Hebrew not listed [docs: https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md] | strongest on Chinese/Latin; Indic and Hebrew coverage thin | Apache-2.0 | `pip install paddlepaddle paddleocr` (~1-2 GB with deps, Python 3.14 wheels uncertain) | 0.3-1 s CPU | skip: heavy, partial |
| **EasyOCR** | 80+ languages incl. Bengali, Tamil, Telugu, Kannada, Thai, Hebrew-less [unverified] | okay | Apache-2.0 | pip + PyTorch (~1-2 GB), models downloaded at first use | 1-3 s | skip |
| **Surya OCR 2** | 91 languages incl. Arabic, Hindi, Greek, Hebrew [docs: https://pypi.org/project/surya-ocr/] | best among local open models for scripts (VLM-based) | code GPL; weights modified AI Pubs Open RAIL-M (free under about $2M revenue/funding) [docs, check current terms] | pip + torch/llama.cpp, multi-GB | seconds per page on Metal | license mismatch for a paid tool shipped to developers; skip |
| **docTR** | mainly Latin + some Cyrillic/Greek/Arabic, no Indic [unverified] | good on documents | Apache-2.0 | pip + torch | ~1 s | skip |
| **Google ML Kit text recognition v2** | 5 scripts: Latin, Chinese, Devanagari, Japanese, Korean [docs: https://developers.google.com/ml-kit/vision/text-recognition/v2/languages] | good | free SDK, proprietary | Android/iOS in-app SDK; not a Mac CLI | n/a | useless: fewer scripts than Vision and not usable from Python |
| **Google Cloud Vision / Azure Read / AWS Textract** | 100+ languages incl. all scripts above | best | paid per image (Google about $1.50 per 1000 images after the first 1000 each month [unverified]) | API key | 1 s round trip | uploads unreleased product screens to a third party; offer only as opt-in `ocr = "cloud:google"`, never default |
| macOS `Vision` custom words / `recognitionLanguages` | n/a | trying `usesLanguageCorrection=false` and pinning `pl/cs/tr/ro` for Hungarian: see "Experiment result" below | OS | none | none | cheap tuning |

**Recommendation:** do not bundle any engine. Add an optional `ocr_command = "tesseract {png} - -l ell+eng --psm 6"` hook: if the expected locale is not in `readable_languages()` and the user configured a command, run it and match with the same normalized comparison. Document `brew install tesseract tesseract-lang` (Homebrew formula pulls roughly 700 MB with all languages; each script model is separate). **Effort S for the hook, M if shotfleet picks the language packs per locale automatically** (map `el -> ell`, `he -> heb`, `hy -> hye`, `ka -> kat`, `bn -> ben`, `ta -> tam`, `te -> tel`, `kn -> kan`, `ml -> mal`, `gu -> guj`, `pa -> pan`, `or -> ori`, `si -> sin`, `km -> khm`, `lo -> lao`, `my -> mya`, `am -> amh`; codes per Tesseract naming). Keep it opt-in because quality on UI text is unproven here; test with a rendered Greek/Hebrew screen once installed.

Hungarian, Croatian and other Latin-script languages outside Vision's list: **fix the comparison, not the engine** (A4 below).

### A3. Pixel-free fallbacks

- **Unicode script detection of the screenshot** is impossible without OCR. Nothing credible exists for "this PNG contains Tamil" short of recognizing it.
- **Glyph-coverage / reference render** (render the expected string with a system font and compare to the crop): fragile because app font, size, weight, shaping, Dynamic Type and Android's fallback fonts differ; SSIM or template matching on non-aligned text is unreliable. It works only if we know the node bounds (hierarchy) and then only as "ink exists here" (crop has high-contrast pixels in the text bounds), which catches blank, clipped-to-nothing or off-screen text but not wrong text. Cheap to build with bounds from A1: **S** once A1 exists.
- **Reference-diff against another locale:** screenshot of locale X must differ from the base-language screenshot in at least the text regions (cheap perceptual hash per region); catches "localized app but English shown". Already half-done by the sha-256 copy check; extend to a perceptual hash so re-encodings are caught: **S**.
- **Tofu detection:** repeated identical box glyphs. A heuristic scan for many identical connected components in a text line is feasible but noisy; I would not ship it without a test set. **M, optional.**
- Honest conclusion: for scripts Vision cannot read, **hierarchy (A1) is the only credible automated proof**; OCR via an installed engine is the second; for apps with neither (games), say "not provable" (current behavior) and show the screenshot for manual review.

### A4. Make comparison tolerant (applies even with Vision)

Normalize both sides before comparing OCR/hierarchy lines with strings (prototype in `fmt.py`, asserts pass [measured]):

- NFC; casefold; collapse whitespace; U+00A0/U+202F/U+2009/U+2007 -> space.
- strip U+200E/200F/202A-202E/2066-2069/061C.
- digits: Arabic-Indic U+0660-0669, Persian U+06F0-06F9, Devanagari U+0966-096F, Bengali U+09E6-09EF -> ASCII.
- Persian `ی` U+06CC -> `ي` U+064A, `ک` U+06A9 -> `ك` U+0643 (Vision reads Persian as Arabic).
- For Latin-script languages Vision does not list (hu, hr, sk, sl, lt, lv, et, is, ca, eu, fil, sw...): compare **accent-folded** (NFKD, drop combining marks) with a similarity threshold (e.g. `difflib.SequenceMatcher` ratio >= 0.85) instead of exact line equality.
- Do not use `NLLanguageRecognizer` for UI text on non-listed languages; it labeled Tamil as Thai and Greek garbage as Hungarian [measured].

### Experiment result: Vision options on Hungarian

On the rendered Hungarian screen, pinning `recognitionLanguages` to `en-US`, `pl-PL`, `cs-CZ`, `ro-RO`, `tr-TR` or all four, with `usesLanguageCorrection` on or off, produced **identical** output (`Beallitasok | Edzés indítása | Elözmények ööüü`) [measured: `vo.swift`]. So Vision's options cannot recover `ő/ű/á/í`; accent-folded fuzzy comparison (A4) is the fix, not engine tuning.

---

## B. Frameworks: where translations live

Principle: for most frameworks the **source files** are the stable, format-documented place; compiled forms are compressed, code-embedded or per-version. Recommend a generic **`strings = [globs]`** option (B9), with built-in readers for the native formats shotfleet already handles. Confidence tags are on the claims.

| Framework | In the BUILT app | In SOURCE | Recommendation | Config the user gives |
|---|---|---|---|---|
| **Native iOS** | `.lproj/*.strings`, compiled String Catalogs become `.strings`/`.stringsdict` per lproj [docs/known] | `.xcstrings` JSON, `.strings`, `.stringsdict` | build (current); add `.stringsdict` (ignored today) | none |
| **Native Android** | `resources.arsc` via aapt2 (current) | `res/values-*/strings.xml`, `plurals`, `string-array` | build; add plurals and arrays from `aapt2 dump resources` | none |
| **Flutter** | **No ARB in the app.** `flutter gen-l10n` turns `lib/l10n/app_*.arb` into Dart (`app_localizations_de.dart`, a `String get x => '...'` class per locale), compiled into `libapp.so` (Android release, AOT) / `App.framework` (iOS) or the kernel blob (debug: `flutter_assets/kernel_blob.bin`). Strings are in the binary as UTF-16/UTF-8 string objects but with no keys and no structure [unverified, inspect an APK]. `flutter_assets/` holds fonts/assets, not ARB, unless the app lists ARB as an asset. Package `intl` with `Intl.message` is also code. | `lib/l10n/app_<locale>.arb` (JSON, `@key` metadata with placeholders, ICU `{n, plural, =0{..} one{..} other{..}}`); config in `l10n.yaml` (`arb-dir`, `template-arb-file`) | **source**: parse `l10n.yaml`'s `arb-dir` or glob | `strings = "lib/l10n/*.arb"` (locale from filename `app_de.arb` or the `@@locale` key) |
| **React Native / Expo** | i18next/react-intl JSON is `require`d, so it ends up **inside the JS bundle**: `main.jsbundle` (iOS) / `assets/index.android.bundle`. Release builds use **Hermes bytecode (`.hbc`)** by default in RN 0.70+: strings are in a string table (not human-readable as JSON, but extractable with hermes-dec / hermes_rs `strings`). [docs: https://github.com/P1sec/hermes-dec, https://github.com/Pilfer/hermes_rs] Debug builds served by Metro are plain JS. Expo OTA bundles are the same. | `locales/en/translation.json`, `i18n/*.json` (nested keys, i18next `{{name}}`, `_one/_other` plural suffixes or ICU) | **source**: JSON parser with key flattening; i18next v4 plural suffixes `_zero/_one/_two/_few/_many/_other` | `strings = "src/locales/*/translation.json"` (locale from folder or file name) |
| **.NET MAUI / Xamarin** | `.resx` -> compiled `*.resources` inside **satellite assemblies** `fr/MyApp.resources.dll` (iOS `.app` folder; on Android inside the APK's `assemblies/` blob, often XALZ-compressed, `assemblies.blob`) [docs: https://learn.microsoft.com/dotnet/maui/fundamentals/localization] | `Resources/Strings/AppResources.fr.resx` (XML `<data name><value>`) | **source** (`.resx` is trivial XML). Reading satellite DLLs needs a .NET reader; skip | `strings = "Resources/**/AppResources*.resx"`; locale from the middle suffix; neutral file = base |
| **Unity** | Localization package: String Tables are ScriptableObject assets in **Addressables / AssetBundles** (binary, serialized), or `StringTableCollection` assets; not readable without UnityPy [unverified] | Editor exports **CSV, XLIFF** (Localization package has built-in CSV and XLIFF export/import) [docs: https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/CSV.html] | **source**: CSV/XLIFF export | `strings = "Localization/export/*.csv"` (first column key, then per-locale columns) |
| **Kotlin Multiplatform moko-resources** | Android: normal `strings.xml` in `resources.arsc`; iOS: `.strings` in the framework's `MR` bundle, inside `Frameworks/<shared>.framework/*.bundle/<locale>.lproj` (shotfleet already scans lproj under frameworks) [unverified path details] | `shared/src/commonMain/moko-resources/<locale>/strings.xml` (Android format; plurals as `<plurals>`) | works from the build today; source option for speed | `strings = "shared/src/commonMain/moko-resources/*/strings.xml"` |
| **Compose Multiplatform resources** | `.cvr` (already supported) | `composeResources/values-<q>/strings.xml` | build (done) | none |
| **Lyricist** | **No resource files**: strings are Kotlin `object`s / data classes (`val Strings = mapOf(Locales.EN to EnStrings, ...)`); compiled into code | `.kt` | cannot read from build; parse Kotlin is out of scope. Offer CSV/JSON export or ask the user for a dump; or use A1 hierarchy with **zero string tables** (see D "no-table mode") | none feasible |
| **Capacitor / Ionic / Cordova** | web assets bundled as files: iOS `App.app/public/` (Capacitor) or `www/`; Android APK `assets/public/`. i18n JSON (ngx-translate `assets/i18n/de.json`, i18next) are plain files there, readable directly [unverified paths] | `src/assets/i18n/*.json` | **build** works (unzip APK, read `assets/public/**.json`) or source | `strings = "src/assets/i18n/*.json"` |
| **NativeScript** | bundled JS (webpack) + `app/i18n/*.json` copied under `app/` inside the APK/`.app` [unverified] | `app/i18n/*.json` or `.po` | source | `strings = "app/i18n/*.json"` |
| **Web / PWA wrappers** (Cordova, Tauri, Electron) | like Capacitor | JSON/PO | source | same |

### B9. Generic "strings from files" (recommended core of B)

Config: `strings = ["glob", ...]` (+ optional `base_locale`, `locale_from = "filename|dir|key|column"`), producing the same `{locale: {key: value}}` structure `load_strings` returns, with a per-file locale extractor. Formats, ordered by value:

| Format | Locale source | Plurals/placeholders | Notes |
|---|---|---|---|
| **Android `strings.xml`** | `values-de/`, `values-b+sr+Latn/` (existing `android_locale`) | `<plurals><item quantity>`, `<string-array>`; `%1$s`, `%1$d` | `\'`, `\n`, `\u`, `@string/` refs |
| **ARB** (Flutter) | `@@locale` or `app_<loc>.arb` | ICU in value; placeholders in `@key.placeholders` | JSON |
| **i18next / generic nested JSON** | folder or filename | `{{x}}`, `_one/_other` suffix, `$t(key)` nesting | flatten with `.` |
| **Lokalise / Crowdin / Phrase exports** | file or folder per locale; "JSON (flat)" or nested; Android XML / iOS strings / XLIFF also offered | same as above | treat as nested JSON / XLIFF; Lokalise "ICU" plural option; Crowdin `%name%`-style placeholders in some configs |
| **XLIFF 1.2 / 2.0** | `<file target-language>` / `trgLang` | `<x id>`/`<ph>` inline tags; Xcode `.xcloc` is XLIFF 1.2 | one file can hold many locales |
| **gettext `.po`** | `Language:` header or `locale/<lang>/LC_MESSAGES/*.po` | `msgid_plural` + `msgstr[n]` using the header `Plural-Forms:`; printf or `{}` | key is the msgid (English) which is convenient: base text *is* the key |
| **`.resx`** | filename suffix | `{0}` `{1}` | trivial XML |
| **CSV/TSV** | header row (`key,en,de,fr`) | per cell | Unity, spreadsheets, Lokalise "CSV" |
| **`.xcstrings`** (source) | JSON `strings.<key>.localizations.<loc>.stringUnit.value`, `variations.plural.<cat>`, `variations.device.<iphone|ipad|mac|...>` | `%lld`, `%@`; `substitutions` with `argNum` | `sourceLanguage` field = base (see D) |
| **`.stringsdict`** | folder lproj | `NSStringLocalizedFormatKey` = `%#@var@`, `NSStringFormatSpecTypeKey`, categories zero/one/two/few/many/other | `plutil -convert json` already works [measured on CrossfitTracker `ar.lproj/Localizable.stringsdict`: 6 Arabic categories] |
| **Java `.properties`** | `_de` suffix | `{0}` MessageFormat | cheap |

Implementation sketch: one `readers.py`-style table `{ext: reader(path) -> {locale: {key: value}}}` of about 150 lines; every reader returns plural forms as a dict `{ "one": ..., "other": ... }` for C. **Effort M.** Do not parse source code (Dart, Kotlin, Swift): a `strings` file is always required for Lyricist and similar.

### No-table mode (fallback)

If no strings are available, selectors cannot be translated. Provide `shotfleet run --no-translate`: run the English flow with only `AppleLanguages` changed and require **id-based selectors** (`id:` / accessibilityIdentifier / `resource-id`), which are language independent. The existing translator already leaves untranslated selectors "as-is"; document that using `id:` selectors is the universal fallback for frameworks nobody reads (Lyricist, Unity). **S, docs only.**

---

## C. Plurals and format strings

### C1. What the sources look like

- **iOS**: `.stringsdict` (above), `.xcstrings` `variations.plural` with CLDR categories `zero|one|two|few|many|other` and `variations.device` (`iphone`, `ipad`, `applewatch`, `appletv`, `applevision`, `mac`, `ipod`, `other`); compiled by Xcode into `Localizable.strings` + `.stringsdict` per lproj, so reading the **built `.app`** needs `.stringsdict` added to `load_strings` (it only reads `*.strings` today; CrossfitTracker's plural strings like `%d exercises` are therefore invisible) [source: `load_strings`]. For device variations the built `.strings` file holds a key suffix such as `key` plus `key~iphone`? [unverified; check on a compiled catalog].
- **Android**: `<plurals name="x"><item quantity="one">%d exercise</item>...</plurals>` and `<string-array>`. `aapt2 dump resources` prints them as `resource 0x... plurals/x` with `(config) ... [one] "..."` blocks and `array/x` entries; `load_strings_apk` matches only `string/` today [source]. Add `plurals/` and `array/` parsing.
- **ICU MessageFormat** (Flutter ARB, i18next-icu, formatjs/react-intl, Lokalise ICU): `{count, plural, =0 {No items} one {# item} other {# items}}`, `{gender, select, male{...} other{...}}`, nested, `{n, number}`, `{d, date, short}`.
- **gettext**: `msgid_plural` + `msgstr[0..n]` with `Plural-Forms: nplurals=3; plural=...`.

### C2. Format string -> regex

Prototype `fmt.py` (asserts pass [measured]):

- Tokenize with one regex covering printf (`%@ %d %i %u %f %s %ld %lld %1$d %2$@ %%`, flags, width, precision) and braces (`{name}`, `{0}`, `{{name}}`, `%(name)s`, `%name%`).
- Numeric specifiers -> `(?P<a1>-?[\d.,  ]+?)` (also match grouping separators and native digits after `norm()`); `%@` / `%s` -> lazy `.+?`.
- Literal text between tokens is `re.escape`d; for matching OCR/hierarchy text, **normalize both the pattern's literal parts and the candidate line with `norm()`** (A4). The prototype escapes raw literals; production code should `norm()` the literal parts first so NBSP and bidi marks cannot break equality.
- Repeated named/positional placeholders become back-references. `%%` -> `%`.
- Compile per (locale, key) once; for an N-key table, prefilter by the longest literal substring to avoid N regexes per line.
- **Plurals**: build the union of all forms. For `{count, plural, one {# item} other {# items}}` produce one regex per category with `#` -> `(\d+)`. The number selects the category via CLDR rules (use the explicit tables for the locales that matter: Arabic zero/one/two/few/many/other, Russian/Polish/Czech one/few/many/other, Japanese/Chinese/Korean `other` only). Matching a screen line needs only "any form" (alternation); no rule evaluation.
- Android's `%1$s` / iOS `%1$@` positions let translations **reorder** arguments (Arabic example in the prototype: `الجولة %2$d من %1$d`); name groups by position, not order.

### C3. Translating a selector with arguments

Flow selector `Round 2 of 12` (English) -> German `Runde 2 von 12`:

1. Build the English regex from every base string containing placeholders (`Round %1$d of %2$d`) and match the selector text against them; a match gives the key and the arguments `{1: "2", 2: "12"}`. Exact (non-placeholder) strings still use the existing `by_text` dict first.
2. Take the target locale's format for the same key, and **render** with the arguments (`render()` in `fmt.py`). For plurals select the category by the **target** locale's rule for the numeric argument (`2` in Arabic -> `two`; `5` in Russian -> `many`), not the English category. Because the CLDR rules matter only for the target, ship a small table or use Python `babel` if present (`babel.plural`) with a hard-coded fallback for about 40 locales. **Do not require babel**: it is a dependency; a 40-locale rule table is about 60 lines.
3. Apply `norm()`-tolerant matching in the produced Maestro regex: Maestro matches the whole text with Java regex, so emit `Runde\s2\svon\s12` with `[   ]` for spaces and `[0-9٠-٩۰-۹]` for digits when the locale's number system is not Latin (check by rendering one number with `NumberFormatter` or by seeing which digits the locale's strings use).
4. For `%@` arguments (user names, dynamic data) in the selector, keep the English text of the argument as-is.
5. Selectors that are substrings (`Round`) work today through the exact-match dict only; add `contains`-style translation for partial matches only if requested (**not** now).

### C4. Platform specifics that bite

- iOS `%d` vs `%lld`: both are numeric; `%ld`, `%lu`, `%@` handled; `%1$@` positional.
- Android escaping `\'`, `\"`, `\@`, `\?`, `\n`, `\uXXXX`; `<b>` spans in HTML-in-resource strings give plain text on screen but markup in the table (`aapt2` prints plain text of `<string>` with spans stripped? [unverified]); strip tags when comparing.
- ICU quoting: `'{'` literal braces, `''` apostrophe.
- Digits shown in `ar`/`fa`/`hi`/`bn`/`mr` follow the locale's number system on iOS if `AppleLocale` is set (shotfleet sets it), so `%d` renders `٢`. The arguments in selectors are ASCII; normalize before comparing [measured: Vision reads `ٍ٢ من ١٢` for Arabic].

**Effort: M** for a tested `formats.py` (tokenizer, regex, plural rules, render) plus wiring in `translate_flow` and the check.

---

## D. Non-English base language, region-only locales, RTL, special characters

### D1. Base language is not English

Current assumptions [source: `translate_flow`, `load_strings`, `add_cvr`, `load_strings_apk`, `shipped_locales`]: `base = "en"` default for Android (`load_strings_apk(base="en")`: default-config strings are assumed English), `CVR` default is `en`, selector text in the flow is looked up in the base table's values, and `shipped_locales` computes coverage relative to `strings[base]`.

Design: add `base = "de"` (or `"ja"`, `"pt-BR"`) to `shotfleet.toml`; default detected from the project: iOS `CFBundleDevelopmentRegion` in Info.plist or `.xcstrings` `sourceLanguage` (String Catalog); Android: the default `values/` is the **default locale**, whose language is unknown from the APK -> detect with a small language heuristic over the default strings (script ranges plus the existing `NLLanguageRecognizer`) or ask in `init` ("default language of values/ is de?"). Pass `base` through every loader (`load_strings_apk`, `add_cvr`, `.lproj/Base.lproj`). The flow is then written in that base language and `translate_flow` works unchanged because it keys on the base table values. For the base locale itself, the run is identity (selectors stay). **Effort S.** Test with a base-`de` fixture.

Also: **the English flow is not required** for translating when the selector text is from any locale; support `selectors_in = "ja"` as a synonym of base. **Included in the same S.**

### D2. Region-only localizations (`en-GB` but no `en`, `pt-PT` but no `pt`, `es-419`)

- Locale resolution chain: `de-AT -> de -> base`, `en-GB -> en -> Base`, `zh-HK -> zh-Hant -> zh`. iOS `AppleLanguages = ("en-GB")` with only `en-GB.lproj`: works; with only `en.lproj`, iOS also resolves `en-GB -> en`. If the app has only region lprojs (`pt-BR.lproj`, `pt-PT.lproj`), the language code `pt` alone fails: shotfleet must pass the full code and never invent the short one. `canon_lproj`/`store_code` need a region-aware table (a few lines); `shipped_locales` should treat regions as separate locales and avoid collapsing to the language.
- Android: `values-en-rGB`, `values-b+es+419`; `android_locale()` already handles `rXX` and `b+` forms [source]. Missing: fallback chain when base is absent: use `base` config (D1).
- Store codes: App Store `en-GB`, `pt-PT`, `es-MX`, `fr-CA`, `zh-Hans/Hant`; Play `en-GB`, `pt-PT`, `es-419`, `zh-CN`, `zh-TW`, `zh-HK` (existing `store_code`). Test the matrix with fixtures; **S**.
- iOS: `en_GB` lproj names (underscore) handled by `canon_lproj`.

### D3. RTL (ar, he, fa, ur, also yi, ps, ckb)

- **Flow**: Maestro `tapOn` coordinates (`point:`/percentages) and `swipe` directions are physical, not logical; in RTL layouts "swipe left to go next" flips. Selectors by text/id are unaffected. Document that `swipe: direction:` in RTL may need `rtl_swipes = "flip"` option (flip LEFT/RIGHT when the target is RTL and the app mirrors). **S**; keep as opt-in since not all apps mirror.
- **Hierarchy order**: element order in RTL screens is right-to-left; do not rely on index order (`index:` selectors).
- **Strings**: values contain bidi controls: U+200F RLM, U+200E LRM, U+202A-202E embeddings, U+2066-2069 isolates (iOS/Android insert FSI/PDI U+2068/U+2069 around `%@` arguments when `NSLocalizedString` + `String(format:)` is used with bidi-aware formatting; Android `BidiFormatter` adds LRM/RLM and U+202A-202C or isolates). They are invisible on screen, so OCR never sees them and Maestro's Android text match fails if the pattern includes them. **Strip them from both the table values and the emitted regex** (and in `norm()`), or make them optional `[‎‏‪-‮⁦-⁩]*` around tokens. [A4]
- **Digits**: `ar` shows Arabic-Indic `٠١٢٣٤٥٦٧٨٩` (U+0660) or Latin depending on the locale/region (`ar_EG` vs `ar_AE`/`ar-u-nu-latn`); `fa`/`ur`/`ps` show Persian/Urdu forms U+06F0; Vision outputs Arabic-Indic for Persian digits too [measured: `۲` read as `٢`]. Map all to ASCII before comparing; when producing selector regexes use `[0-9٠-٩۰-۹]`.
- **Letter variants**: Persian `ی`/`ک` vs Arabic `ي`/`ك` [measured]; Arabic presentation forms (U+FB50-FDFF, U+FE70-FEFF) from some OCR/PDF text: NFKC them. Hebrew has niqqud/final forms; Vision cannot read Hebrew at all: hierarchy only.
- **Mirrored punctuation/brackets** and reordered runs: OCR returns visual-order lines sometimes (`ar` with embedded Latin words, e.g. `Maestro 2 الجولة`). Compare **sets of words**, not whole lines, when a string mixes scripts. In `judge_screen` use the longest-common-words ratio for mixed-script strings (**S**).
- **Screenshot export:** no change.

### D4. French and other spacing characters

- French uses U+00A0 before `: ; ! ?` and U+202F (NNBSP) before `: ; ! ?` in newer iOS/CLDR (`« mot »` with NNBSP); `50 %` uses NNBSP (U+202F) in CLDR since 34 and NBSP before units in Android `%1$d min`. Vision and `adb` output turn these into normal spaces or drop them; Maestro regex needs `[\s  ]`. Fix by `norm()` on text and by emitting `\s` for every U+0020/U+00A0/U+202F/U+2009 in the pattern (note Java `\s` does not match NBSP unless `(?U)` flag; use an explicit class). [A4/C3]
- German thousands: `1.000`, French `1 000` (NNBSP), Swiss `1’000` (U+2019) and Arabic `٬` (U+066C) group separator, `٫` decimal separator (U+066B): accept `[.,’٬٫   ]` in numeric tokens.
- Turkish dotted/dotless I: `casefold()` maps `İ` -> `i̇`; use `locale`-aware lower for `tr` or compare NFKD-folded without marks.
- Thai/Khmer/Lao/Burmese have no spaces between words: OCR line comparison with word sets fails; match whole-line or use substring containment with a normalized needle (length >= 4 graphemes).
- CJK full-width digits/punctuation (`！`, `１２`): NFKC fold.

### D5. Locale/launch correctness for odd locales [unverified]

- `AppleLanguages` with `AppleLocale` formatted `ar_SA` vs `ar_EG` changes digits; `shotfleet.localize_flow` derives the locale from the store code; for `fa` (Persian) iOS `fa_IR`, Android emulator system locale set via `adb shell cmd locale set-app-locales` (API 33+) or `setprop`/`-prop persist.sys.locale`; verify the emulator image has fonts (Noto ships most scripts; Burmese/Khmer/Amharic may render as tofu on some system images: **that is exactly the hierarchy blind spot**).
- Numbering-system override `-u-nu-latn` only if the app wants it.

**Effort for D: S for base/region/norm, S for RTL swipe flag and word-set matching, nothing structural.**

---

## E. Per-limit recommendations and effort

| Limit | Recommendation | Effort |
|---|---|---|
| A. OCR | (1) normalization + accent-fold fuzzy match; move the "unreadable script" test before the "no text" test; (2) hierarchy capture per screenshot via the flow HTTP barrier as primary proof; (3) opt-in `ocr_command` hook for Tesseract; (4) perceptual-hash differing from base for non-readable scripts; ignore ML Kit, VisionKit, cloud by default | S / M-L / S / S |
| B. Frameworks | generic `strings = [globs]` with readers (Android XML, ARB, i18next JSON, .po, XLIFF, .resx, CSV, .xcstrings, .stringsdict, .properties); Flutter/RN/Capacitor/NativeScript/MAUI/Unity/Lyricist handled through source files or exports; `id:` selectors as the universal fallback; do not read Hermes/DLL/asset bundles | M |
| C. Plurals/formats | `formats.py`: tokenizer, regex, ICU plural, `.stringsdict`/`<plurals>`/xcstrings variations, CLDR category rules for about 40 locales, render with extracted args | M |
| D. Base/region/RTL | `base` config + region fallback chain + bidi/digit/space normalization + `rtl_swipes` flag | S |

## F. Open questions to settle with one short test each when the Mac is free

1. Does `runScript` with `http.get` work in Maestro 2.0.10 on both platforms, and does Maestro pause until the call returns? (One run of a two-line flow.)
2. iOS: which port does each simulator's XCTest runner listen on under `--shard-split` with 4 simulators? (`lsof` while running.)
3. Android: does `adb exec-out uiautomator dump` succeed while Maestro's driver instrumentation is attached? If not, test `maestro --udid X hierarchy` concurrently.
4. Flutter and Compose samples: do `text` attributes carry the visible strings (merged semantics)?
5. Does a compiled `.xcstrings` with device variations appear as `key~iphone` entries in the built `.strings`? (Check `Remoti` app already mentioned in PLAN.md.)
6. Install Tesseract in a throwaway prefix and OCR the rendered Greek/Hebrew screens from `jobs.json`; record accuracy (the test fixtures already exist).
