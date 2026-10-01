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
| 2.4 | iPad / tablet from the same flow (`devices = ["iphone-6.9", "ipad-13"]`) | iPad 13" required if the app runs on iPad; Play tablets need 4+ | L | yes |
| 2.5 | MCP server next to the Claude Code skill | ButterKit and StoreScreens ship MCP | S–M | indirect |
| 2.6 | Hand-off recipes: `asc screenshots upload`, fastlane deliver/supply | Removes the last manual step | S | no |
| 2.7 | Variant sets for custom product pages / Play experiments | Unproven demand; AppScreens sells it | M | maybe |

## 3. Sell it
DISTRIBUTION.md: bundled signed binary, Homebrew tap, Lemon Squeezy licence, `check` free. Needed by the founder sale (STRATEGY.md week 4).

## Order
1.1 → 1.4 → 1.2 → 1.3 → 2.2 → 2.1 → (experiments for 1.5 on a quiet Mac) → 1.5 → 2.3 → 3 → 2.4.
Each item ships with tests and is re-measured with tools/langmatrix.py and the CrossfitTracker regression.
