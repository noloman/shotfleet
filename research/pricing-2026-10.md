# Functionality, competitors and price (researched 2026-10-02)

Method: three research agents plus my own fetches. Prices below are marked **V** (read on the vendor's own page today by me) or **A** (reported by an agent, not re-checked). Agent claims about what shotfleet does were wrong in places (frames, RTL, "auto-framed") and were discarded.

## 1. What shotfleet really offers

| Capability | Status |
|---|---|
| One English Maestro flow -> every language the app ships, selectors rewritten from the app's own strings | **Proven** (CrossfitTracker iOS 18/18 and Android 18/18; Kuokka iOS+iPad; HackerNewsKMP APK) |
| Parallel capture on simulators and emulators, both platforms from one config and one flow | **Proven** (9 min iOS, 15 min Android for 18 languages x 4 screens; both-platform run on Kuokka + HackerNewsKMP) |
| Checks: wrong language, copies, missing, store size rules, iPad rule | **Proven** (one real bug found in CrossfitTracker; planted errors caught) |
| Export to fastlane deliver/supply, iPhone + iPad sets together | **Proven** |
| 13" iPad pass from the same flow | **Proven** (Kuokka, de + ja) |
| Flutter / React Native / MAUI / Unity via translation files | **Sample files only**, no real app |
| iOS permission alerts | They are drawn in the device language, which stays English (measured on `main` with Maps); taps on them keep their English text |
| Tesseract alternative reader | Proven, English-only data on this Mac |
| Signed one-file binary, licence check | Binary builds and signs; **never notarized, licence server never called** |
| Frames, captions, backgrounds, AI translation of marketing text, upload to the stores, Android tablets, Watch/Mac/TV | **Not offered** |

Friction a buyer pays: macOS only; Xcode and a debug simulator build; Maestro installed; writing a Maestro flow; typed text isn't translated; first `check` compiles an OCR model once (30 s to minutes).

## 2. Competitors and their prices

| Tool | Price | What it is |
|---|---|---|
| ButterKit | **V** Free (watermarked exports, unlimited on-device translation, 50 languages); Pro **$99 one-time** (was $149), free updates, 5 Macs, 14-day refund; Supporter $39/yr | Frames/captions from Simulator capture, AI translation, ASC upload, MCP. Apple platforms, limited Android |
| AppScreens | **V** Free (no localizations); Pro **$99/yr** (10 languages, store upload); Scale $180/yr (80+) | Web editor: mockups from uploaded screenshots, iOS + Android |
| Maestro Cloud | **V** $250 per device per month; local CLI free | Hosted devices; no per-flow locale |
| simshot | **V** Free, MIT, iOS only, 0 stars, needs ~3 lines added to your app | Per-language capture by launch arguments |
| fastlane snapshot / screengrab | free (A) | The default; UI-test code per platform |
| StoreScreens CLI, asc CLI | free (A) | Capture/upload helpers; asc is large (A: 7.6k stars) |
| Screenshots.pro, AppLaunchpad, ScreenshotWhale, LocalizeShots, Previewed, Rotato, Shotlingo... | A: roughly $5-20/month or $50-180/yr | Mockups from uploaded images; none verifies the language |

Nothing found captures the real app in every language from one flow on both platforms and checks it. Those tools make marketing images; shotfleet makes the raw, correct captures that go inside them.

## 3. Price

Comparables (A): DevUtils $29-99, Transmit $45, Charles $50, Proxyman $89, Nova $99 one-time. Lemon Squeezy fee 5% + $0.50 (A). Net per sale: $29 -> $27.05, $49 -> $46.05, $79 -> $74.55.

Not supported by evidence (agents asserted them): "10-30 hours saved per release", "75% of devs skip localization", "$79 is underpriced". Nobody has paid yet and the waitlist has 0 signups, so there is no demand data at any price.

What does hold:
- The audience that matters compares us with free capture (fastlane, simshot, Maestro) and with ButterKit's free tier. Our difference (real localized captures from one flow, plus verification) is real, but setup takes an hour or more, so the buyer pays in friction as well as money.
- Both direct competitors have a free tier that shows value before paying; we don't (check is free, capture is not).
- We offer less than ButterKit's $99 (no frames, no upload) and have no track record.

## 4. Recommendation

- Standard $49 one-time (a year of updates, then keeps working); launch price $29 for the first 100.
- Free tier that shows the product: `run` unlocked for up to 2 languages, plus free `check`. Paid unlocks all languages.
- Team/CI licence later (about $149).
- Raise the price as proof arrives (first case studies, notarized release, real Flutter/RN run). Keep the 14-day refund.
- Decision rule in sales count, not revenue: 50 sales at $29 within 60 days.

## Addendum 2026-10-02: net per sale on Gumroad (replaces the Lemon Squeezy arithmetic in section 3)

Polar and Lemon Squeezy are out (a Dutch KvK would be asked for); the sale is on Gumroad. Fees read from gumroad.com/pricing and help article 66 today: 10% + $0.50, plus card processing 2.9% + $0.30 (not included in the 10%); Discover sales 30%. Net per sale (assuming the percentages run on the list price, not on VAT added on top): $29 -> $24.46 (15.7% in fees), $49 -> $41.88 (14.5%). Against the old figures that is $2.59 and $4.17 less per sale. The $29/$49 decision stands; the page must say prices are before VAT where it applies, because Gumroad cannot show a VAT-inclusive digital price. The 50-sales rule is now $1,223 net at $29. Details, sources and the unverified points: research/gumroad-setup.md.
