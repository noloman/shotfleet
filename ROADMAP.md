# shotfleet roadmap

Built from: research/audit.md (code audit), research/first-run.md (cold user test), research/market-2026.md
(competitors, store rules), research/all-languages.md (language and format limits), research/real-apps.md
(trials on other apps). Effort: S < 1 day, M 1–3 days, L > 3 days.

## Done (2026-10-01)
- Every audit finding fixed (export data loss, wrong-language passes, untranslated anchors, leaks, tracebacks).
- First-run fixes (Python 3.9 message, wrong build types, platform mismatch, quieter check without --app, init paths).
- All 50 App Store and 87 Play listing codes; 85-language measurement (tools/langmatrix.py).
- 1.1 tolerant matching; 1.2 plurals (.stringsdict, <plurals>, Compose) and format strings (matching + translating
  'Round 2 of 12' into every plural form); 1.4 base language and region fallback; real-app defects (English-keyed
  String Catalogs, multi-line Android strings, YAML quoting, non-language folders).
- 1.3 translations from source files (Flutter ARB, i18next, .xcstrings, XLIFF, .resx, .po, .properties, CSV).
- 2.2 store-rule linter (sizes per Apple display class, Play limits, alpha, counts, recommendation eligibility).
- 1.6 --ocr-command (e.g. Tesseract) for scripts macOS can't read; 2.3 caption vs app language (message only: caption
  language alone is too unreliable to fail on); 2.5 MCP server (`shotfleet mcp`); 2.6 fastlane upload recipes.
- System dialogs: measured that iOS draws them in the device language (English), so their taps stay English-matchable;
  iOS launchApp options (permissions: {all: allow}) supported.
- Emulator benchmark written up (android-emulator-bench/RESULTS.md).
- Headless emulators (Manu's idea), measured 2026-10-01: shotfleet already ran headless (`-no-window`). Snapshot boots
  are now used: read-only copies boot in 4-5 s instead of 21-23 s cold (2 rounds each); verified end to end (de+ja,
  4/4 screenshots). The ATD image is NOT usable for store screenshots: apps launch faster (2.5-4.4 s vs 7.5 s), but
  every screen capture is black (tried default, swiftshader and host GPU). Also fixed: the status bar showed "3G".

## Done 2026-10-02
- 2.4 iPad and Android tablets from one flow: `device_types` (iOS) and `devices` (Android). Verified: remoti iPhone 6.9" +
  iPad 13" (2064x2752); CrossfitTracker phone 1080x1920 + tablet 1440x2560, exported to phoneScreenshots/tenInchScreenshots.
- MCP `check` on real screenshots: 72 screenshots, 18 languages, 0 problems, 29 s (after the Mac restart fixed OCR).
- 1.5 on Android: not possible with Maestro 2.0.10 (`maestro hierarchy` breaks sharded runs); iOS reads app text exactly.

- macOS text recognition: doctor and check warm it up once, check runs at most 4 in parallel, falls back to Tesseract
  when it's stuck (72 real screenshots, 0 false problems) and uses installed Tesseract for scripts macOS can't read
  (84/85 languages verified by reading, was 66).

## Still open
- A clean 8-emulator benchmark round on an idle Mac.
- Confirm on a freshly restarted Mac how long macOS's first text-recognition compile takes (needs Manu's restart). Without a
  restart, verified 2026-10-03: the release-candidate build's `check` matches source on real screenshots (72 iOS + 72 Android
  clean, planted set exactly its 2 mistakes); with recognition stuck, `check` switches to Tesseract after 90 s (137 s total).

## 1. Every language, every localization setup (no buyer turned away)
| # | What | Why | Effort |
|---|---|---|---|
| 1.1 | Tolerant comparison: NFC, bidi marks stripped, NBSP/NNBSP, native digits (Arabic-Indic, Persian, Devanagari) to ASCII, accent-folded matching for Latin languages outside macOS OCR (hu, sk, hr, ca, …) | Hungarian ő reads as ö; Persian digits; French NBSP. Cheap and removes false alarms | S |
| 1.2 | Format strings and plurals: `.stringsdict`, String Catalog variations, Android `<plurals>`, printf/ICU → regex; translate "Round 2 of 12" selectors with the same numbers | Many real labels contain numbers; plural-only strings are invisible today | M |
| 1.3 | `strings = [globs]` from source files: ARB (Flutter), i18next/JSON (React Native, Expo), `.po`, XLIFF, `.resx` (MAUI), `.xcstrings`, `strings.xml`, CSV (Unity), `.properties` | Opens Flutter/RN/MAUI/Capacitor buyers; translations aren't readable in those builds | M |
| 1.4 | Base language other than English; region fallback (en-GB → en → base) | Apps developed in German/Japanese | S |
| 1.5 | Read on-screen text from the UI hierarchy during `run` (exact Unicode in every script), OCR as fallback | Removes the OCR limit for runs entirely. Needs 4 experiments first (all-languages.md §F) | M–L |
| 1.6 | Optional `ocr_command` hook (e.g. Tesseract) for `check` on scripts macOS can't read | For buyers who want full verification of Greek/Hebrew/Indic listings | S |

## 2. Beat the competition
| # | What | Evidence | Effort | Paid? |
|---|---|---|---|---|
| 2.1 | Localized system dialogs: permission alerts, notifications prompt, ATT, in every language | Maestro's permission helper is English-only (maestro#2654, open) | M | yes, core |
| 2.2 | Store-rule linter in `check`: sizes/counts per device class, no alpha, Play phone 2–8 / tablet 4+, promo eligibility, locales without a set | Developers trip on these; only dimension checks exist elsewhere | S–M | free funnel |
| 2.3 | Caption vs UI language check for framed images (ButterKit, AppScreens, AI localizers) | Translated caption over English UI is the classic failure; nobody checks it | M | yes |
| 2.4 | iPad / tablet from the same flow (shipped as `device_types` for iOS and `devices` for Android, see Done 2026-10-02) | iPad 13" required if the app runs on iPad; Play tablets need 4+ | L | yes |
| 2.5 | MCP server next to the Claude Code skill | ButterKit and StoreScreens ship MCP | S–M | indirect |
| 2.6 | Hand-off recipes: `asc screenshots upload`, fastlane deliver/supply | Removes the last manual step | S | no |
| 2.7 | Variant sets for custom product pages / Play experiments | Unproven demand; AppScreens sells it | M | maybe |

## 3. Sell it
DISTRIBUTION.md: bundled signed binary, Homebrew tap, Gumroad licence, `check` free. Needed by the founder sale (STRATEGY.md week 4).

## Order
1.1 → 1.4 → 1.2 → 1.3 → 2.2 → 2.1 → (experiments for 1.5 on a quiet Mac) → 1.5 → 2.3 → 3 → 2.4.
Each item ships with tests and is re-measured with tools/langmatrix.py and the CrossfitTracker regression.
