# shotfleet on real apps (not CrossfitTracker)

Status: PARTIAL. Strings loading, flow translation and checks were done for the builds that exist. Not finished: Maestro/emulator runs (forbidden), IceCubesApp/CrossFit-WOD-Logger/subscrifi-iOS (no usable build), Stressi/HackerNewsKMP/subscrifi screenshot checks only partly done.
All work read-only; scripts and caches are in scratchpad `.../scratchpad/apps/` (load.py, harness.py, roundtrip.py, andcmp.py, fl_*.py, rep/).

## Builds found
| project | build used | note |
|---|---|---|
| remoti | DerivedData remoti-cbzw...app (iOS sim) | native SwiftUI iOS + Android (no APK, only .aab) |
| HackerNewsKMP (Kuokka) | iosApp/Kuokka.xcarchive, composeApp/build/outputs/apk/release/composeApp-release.apk | Compose resources (.cvr) |
| Stressi | Stressi.xcarchive, androidApp-debug.apk | |
| Cairn | build/Cairn.xcarchive | String Catalog, xcarchive older than the catalog |
| Subscribi-iOS | build/Subscribi.xcarchive | String Catalog |
| Keysi | build/Release/Keysi.xcarchive (macOS app) | String Catalog; build/Debug app is stale (nl only) |
| Launchi | build/Release/Launchi.app (macOS) | build is empty: only Metadata.appintents, no lproj, load_strings returns {} |
| subscrifi | androidApp-debug.apk | iOS builds contain no strings |
| IceCubesApp, CrossFit-WOD-Logger | none (CrossFit has an .ipa only) | IceCubes: ran load_strings on source `IceCubesApp/Resources/Localization` instead |

## Locale/string comparison (loaded vs repo)
- remoti iOS: loaded 18 shipped locales = 18 lproj in repo (de es fr hi id it ja ko nl pl pt-BR ro ru sv tr uk zh-Hans + en). Own keys 1194 per locale == repo .strings exactly (0 missing/extra, all 18). Extra 36 loaded locales (ar, az, es-MX, nb...) are SPM bundle strings (RevenueCat, Firebase, GoogleSignIn); shipped_locales correctly ignores them.
- Kuokka iOS: 11 shipped (de es fr id it ja ko pt-BR tr zh-Hans + en) = repo lproj. APK: 11, zh is `zh-CN` (iOS `zh-Hans`), matches composeResources values-zh-rCN. APK is older than the sources (83 keys of 1406 missing in APK) so not a loader fault.
- Stressi: iOS 9 = repo (en de es fr it ja ko pt-BR zh-Hans). APK: shipped `pt`, `zh` = repo values-pt / values-zh. OK. APK stale: 43 repo strings not in APK.
- Cairn: 11 = catalog langs (en es fr de it pt-BR nl ja ko zh-Hans sv). Counts 1404 vs 702 own because the PlugIn embeds the same table (duplicates, harmless).
- Subscribi: en, es = catalog. Dev language is en in every Info.plist (CFBundleDevelopmentRegion) and every catalog; no non-English-source app available to test.
- subscrifi APK: shipped 8 = repo values-* (de es fr it ja ko pt-BR + en).
- IceCubes source: 18 lproj loaded = 18 in repo (plus en). Keys 441/locale.
- Launchi: loads nothing from an incomplete build (no diagnostics, see D8).

## Defects

### D1 (HIGH). String Catalogs without explicit English values: base table is empty, nothing translates, shipped_locales wrong
Repro: Keysi (`~/Developer/Keysi/build/Release/Keysi.xcarchive/Products/Applications/Keysi.app`; catalog has `en` localizations for only 6 of 606 keys).
```
s = sf.load_strings(app); len(s['en']) -> 16 (Sparkle/InfoPlist), len(s['de']) -> 666
sf.shipped_locales(s) -> ['de','en','es','fr','it','ja','ko','pt-BR']   # zh-Hans (601 strings) dropped
sf.translate_flow('- tapOn: "Add Shortcut"\n', s['en'], s['de'])  -> untranslated
```
Cause: Xcode does not emit `en.lproj/Localizable.strings` when the source value equals the key (en.lproj only has .stringsdict + InfoPlist.strings). English text is the key. shipped_locales measures coverage against the near-empty en key set, so zh-Hans (601/666) fails the 50% test.
Fix: when base lacks a key that other locales have, use the key itself as the English value (for catalog apps), and compute shipped coverage over the union of keys of non-base locales. With base := keys the 8-label flow translated fine (de `Kurzbefehl hinzufügen`, `Kopieren`).
Note: Cairn/Subscribi/remoti have explicit en so they work; the bug appears only for key-as-text catalogs (very common: IceCubes-style code uses identifier keys, Keysi uses text keys).

### D2 (HIGH). .stringsdict plurals are never loaded
remoti en.lproj/Localizable.stringsdict has 6 keys (`FilterView.Button.ShowCount` "Show %d jobs", `Paywall.Trial.Days`...), Cairn 5 (`%lld tabs`, `%lld days left`), Keysi 6 (`%lld results`, `Trial — %lld days left`), Launchi ships stringsdict too. `load_strings` only reads *.strings, so `- tapOn: "Show 3 jobs"` is reported untranslated. Fix: parse .stringsdict (plutil json) and expose each variant (one/other/few...) as a candidate, see D3.

### D3 (MEDIUM). Strings containing format specifiers/interpolation can never match
Visible text is the formatted result ("Day 3 of ~15", "12 comments", "3 tabs", "Recovery: 85%"), the table has `Day %d of ~15`, `%1$d comments`, `Recovery: %1$d%%`. All reported as untranslated (Stressi, Kuokka, Cairn, remoti flows). Fix: convert each format string to a regex (`%d %lld %@ %1$s` -> `.+`, `%%` -> `%`) and match the English selector against it, then emit the translated pattern with the same wildcards; Android `%1$s`/`%d` also.

### D4 (MEDIUM). Android multi-line values are dropped by load_strings_apk
`aapt2 dump resources` prints a newline inside the quotes as a real line break; the line regex `\(([^)]*)\) "(.*)"\s*$` requires the closing quote on the same line.
Repro: `~/Developer/subscrifi/androidApp/build/outputs/apk/debug/androidApp-debug.apk`, `share_subscription_text` ("%1$s - %2$s/%3$s\nNext renewal: %4$s") missing in all 8 locales. Stressi debug APK: `learn_stress_content`, `learn_hrv_content`, ... 8 strings missing in all locales. Fix: accumulate continuation lines until a line ending in `"` and join with "\n".
Also not loaded: Android `<plurals>` and `<string-array>` (aapt2 prints them in different format), same as D2.

### D5 (MEDIUM). Selector parsing does not unescape YAML or strip comments
Using remoti (de table):
- `- tapOn: 'What''s your experience level?'` -> reported untranslated (`''` not unescaped; the same text in double quotes translates).
- `- tapOn: "Say \"hi\""` -> text kept as `Say \"hi\"`, untranslated (Kuokka has `No results found for "%1$@"`).
- `- tapOn: What's your experience level? # note` (unquoted + comment) -> untranslated; with quotes it works.
- `- tapOn: { text: "Skip" }` flow-map form is skipped silently and not reported as untranslated (silent English left in the flow).
Fix: parse the scalar with a YAML loader (or implement '' and \" \\ \n unescape, strip ` #` comment for plain scalars) and report skipped flow-maps.
Also SELECTOR_KEYS lacks relative selectors (`below:`, `above:`, `leftOf`, `rightOf`, `containsChild`, `childOf` with nested `text:`) - minor.

### D6 (LOW/noise). Collision warnings are mostly false positives
Round trip over all own labels x shipped locales (remoti 1093 labels x 17: 602 collision lines of 18581 runs; Cairn 124/7010; Stressi 61/3824; Kuokka 368/11960). No pattern failures: every generated regex fully matches its target string, all outputs parse as YAML, no regex errors. Typical false positives: singular vs plural (`Bookmarks`/`Bookmark`, ko `Get Started`/`Getting Started`), case/punctuation variants (`Asia Pacific`/`Asia-Pacific`, `Add Comment`/`Add a comment`), fr `Back`->`Retour` "also means `Feedback`" (Kuokka key `feedback` = "Retour"), `Delete`/`Clear`/`Erase`. Real ones are rare (`Next`/`Continue` -> `Weiter` in Stressi de, which can sit on the same onboarding screen). Suggest: only warn when both labels appear in the same flow or normalise (casefold, strip punctuation, singularise) before comparing.

### D7 (LOW). Unions of homonymous keys widen the pattern
One English text mapping to several keys becomes `(a|b)`: IceCubes ja `Reply` -> `(リプライ|返信)` (one is a notification-menu title), Subscribi es `Add Subscription` -> `(Agregar Suscripción|Añadir suscripción)` (two catalog keys, only one on screen), `Settings` -> `(Ajustes|Configuración)`. Works, but can match the wrong element. Acceptable; maybe prefer keys referenced in the same key family.

### D8 (LOW). Empty/odd inputs fail silently
- Launchi's incomplete Release build yields `{}` and cmd_check with such an app would have no tables so `tables and not app_locale(...)` skips every locale check: it should say "app has no strings".
- macOS .app bundles (Keysi, Launchi): all keys get the prefix `Contents/Resources/Localizable:` and Sparkle nib strings (`SUUpdateAlert:170.title`) are loaded as base strings; `check --app` refuses (needs Info.plist at root). Out of scope for iOS/Android but flows built on macOS will not match.
- `check --app foo.apk` against an iOS screenshot folder gives a clear error (good); against a different app's strings (subscrifi vs Subscribi names) nothing warns.
- Incidental, not shotfleet: Kuokka iOS `ios_weekly_digest_share_top_story` = `Top story: %@\\n%@` (literal backslash-n in .strings; likely an app bug), and Kuokka KMP .cvr values from the iOS archive carry real newlines while the XML source has `\n` escapes (fine).

## translate_flow results per app (5-8 step flows with real labels)
- Subscribi (es): all 8 labels translated; two ambiguous ones became alternations. OK.
- remoti: onboarding labels translate in all 17 locales; `'What''s ...'` fails (D5); plural "Show 12 jobs", "5 selected" untranslated (D2/D3).
- Cairn: `Unlock Cairn`, `Rename…` (de `Umbenennen …` with space - correct), `Copy Address`, `The site's own`, `Cancel`, `Delete`, `What are the main points?` all translate; `3 tabs` untranslated (D2).
- Stressi: onboarding/tab labels OK, `Los geht's` quoted correctly (`''`), `?` escaped. `Day 3 of ~15`, `Recovery: 85%` untranslated (D3).
- Kuokka: iOS and cmp: keys both fine (emoji `📱 Available offline` -> `📱 Offline verfügbar` OK, quotes OK when double-quoted); `12 comments`, `No results found for "swift"` untranslated (D3).
- IceCubes (source tables): `Timeline Local Reply Notifications` translate in ja/zh-Hans; `Option 2`, `Mastodon.social users` untranslated (D3).
- Keysi: nothing translates (D1); with base := keys everything but the plural works; `(untitled)` correctly escaped to `\(unbenannt\)`.

## shotfleet check on committed screenshots
- Cairn `~/Developer/Cairn/fastlane/screenshots` (55 images, 11 languages) vs xcarchive: 0 problems. Plausible; not exhaustively reviewed (store-frame folder `screenshots-store` not run).
- remoti `~/Developer/remoti/fastlane/screenshots` vs the iOS sim build: 120 screenshots in 20 languages, 108 problems, all "shows en strings (N lines) more than <lang> (0..3)". I viewed `de-DE/iphone-16-02-fit-trust.png` (German caption "Sieh, warum es passt", app UI in English: "Why this fits", "Was this useful?", "Helpful") and `ja/iphone-16-01-jobs-list.png` (Japanese caption, English UI "1 job", "Newest first", "Posted just now"). TRUE positives: the committed localized listings have localized captions over an English app. The 12 unflagged are en-*. No false positive seen in the two images viewed (others not individually viewed).
- Stressi `~/Developer/Stressi/screenshots` (junk working folder): 1 problem, `ipad_only: the app has no ipad_only translation`. FALSE positive: a device subfolder name is treated as a locale. Suggest: ignore folder names that are not locale-like (ipad*, iphone*, `ipad_only`, `.generated`) or only treat locale-shaped names as languages. Proper store folders (`fastlane/.generated/store_variants`, metadata/ios) not run.
- subscrifi Android `androidApp/fastlane/screenshots/<locale>` with the debug APK: error `holds Android screenshots but --app is an APK` although that folder is named fastlane/screenshots/<locale> (deliver layout) while it belongs to the Android app; suggest relaxing or clarifying the message (the folder is Android's, the platform guess came from the path). Not run further.
- HackerNewsKMP, subscrifi iOS screenshots: not run (no suitable build/time).

## Summary of suggested fixes (priority)
1. D1: key-as-English fallback + coverage over union of keys. 2. D2/D3: stringsdict + format-string matching. 3. D4: multi-line aapt2 values (+ plurals). 4. D5: YAML scalar parsing. 5. check: ignore non-locale folder names; error on empty strings tables. 6. Reduce collision noise.
