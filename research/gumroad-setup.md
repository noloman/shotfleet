# Gumroad: how shotfleet sells and licenses through it

Written 2026-10-02. Polar was dropped the same day because its payout provider (Stripe) will ask a Dutch person for a KvK. Gumroad is what Manu already uses for Keysi. Keysi is read-only reference: nothing there was changed.

Marks: **V** = read on an official Gumroad page on 2026-10-02 (the help pages are pages of gumroad.com/help/article/<id>, quoted by id). **K** = how Keysi does it (file reference). **U** = unverified: only Manu's dashboard or a live purchase can settle it.

## 1. What Keysi does (K)

All paths under `/Users/manu/Developer/Keysi/`.

- **Account and payout.** Individual account, Netherlands, EUR bank payout, USD 100 minimum, no KvK entered; "cleared as an individual" on 2026-09-10 (`AGENTS.md` ~l.609-640, `Keysi/Core/LicenseConfig.swift` l.50-70). Gumroad offers no PayPal payout there; "PayPal Connect" is a buyer payment method (`marketing/DISTRIBUTION-OPTIONS.md`, correction of 2026-09-10). Caveat that matters here: as of 2026-09-12 Keysi had zero purchases (`marketing/STRATEGY.md` l.84), so nobody has seen what Stripe asks *after* sales accrue (section 2, payout).
- **Product.** One product, license keys on, no uploaded file: the buyer gets a key and downloads the free app from the site (`AGENTS.md` step 3; `marketing/copy/10-gumroad-product-page.md` sec. 7 is the receipt text). Refund policy is set per product (30 days), because the account-level control is managed by Gumroad (`AGENTS.md` step 6; `scripts/storefront-check.sh` l.140-160).
- **Checkout link.** A plain link, no overlay, no webhook, no ping: `https://8954369651852.gumroad.com/l/mdyvqv` with UTM parameters tagged per surface (`LicenseConfig.swift` l.71, `checkoutURL(source:)` l.127; site Buy button in `site/index.html` l.371). Gumroad keeps `utm_source` and `utm_campaign` and filters on them.
- **Key check.** `POST https://api.gumroad.com/v2/licenses/verify` with `product_id`, `license_key`, `increment_uses_count` (`Keysi/Core/LicenseGateway.swift` l.114-334). Activation sends `true`; the 7-day revalidation and everything else sends `false`. Offline grace 30 days (`LicenseConfig.swift` l.11-12).
- **Refund, chargeback, dispute.** Gumroad answers `success:true` for such a purchase; the app reads `purchase.refunded`, `.chargebacked`, `.disputed` and rejects (`LicenseGateway.swift` l.228, 267-271, 292-310). A `success:false` without a flag is "could not confirm", not a revocation, because a wrong `product_id` returns the same 404 as a bad key.
- **Seats.** Keysi promises 3 Macs and enforces it as a warning only: `uses > 3` shows a message and the key keeps working; `deactivate` makes no request, because `decrement_uses_count` needs an OAuth token with `edit_products` scope that must not ship in an app (`LicenseGateway.swift` l.60-110; `LicenseConfig.swift` l.20).
- **Tax and support wording.** Terms: price "plus any applicable VAT, handled at checkout"; Gumroad "acts as the merchant of record, handles payment processing, and remits VAT/sales tax"; refund by replying to the Gumroad receipt or by email; Gumroad may refund within 90 days on its own and honours Brazil's 7-day withdrawal (`site/terms.html` l.55-125). Privacy: Gumroad processes the licence check and the purchase (`site/privacy.html` l.88-94). Thanks page: "Your license key is on its way to your email from Gumroad" (`site/thanks.html` l.29).
- **Pitfalls Keysi documented (AGENTS.md step 6, `marketing/LAUNCH-READINESS.md` sec. 1).** Found only by a real $0 purchase: (1) licence keys were off (the Content tab showed the seller's own text, not a licence block); (2) the product was Unpublished; (3) no refund policy was set. Their check script read `is_published`, `is_licensed`, `refund_policy` and the product id out of the product page's embedded JSON because the page is rendered client side (`scripts/storefront-check.sh`). The test purchase used a single-use, product-scoped 100%-off code (`1LZTFLP`, spent). Never buy your own product with a card: Gumroad treats it like card testing and can suspend the account (V, 62).

shotfleet's `tools/golive/storefront.sh` is that check, adapted.

## 2. Verified facts (V)

| Question | Answer | Source |
|---|---|---|
| Fee, direct sales | **10% + $0.50** per transaction, "+ sales tax"; no monthly fee | gumroad.com/pricing; help 66 |
| Card processing | **Not included**: extra **2.9% + $0.30**; PayPal fees extra | help 66 (lists both as "does not include"). Keysi saw the same 12.9% + $0.80 in its payout settings |
| Discover (Gumroad marketplace) sales | **30% flat**, processing included | help 66, pricing |
| Volume discount | 5% + $0.50 after $20,000 paid sales in a month. Irrelevant here | help 66 |
| On a refund | Gumroad's own fee on the refunded part **is returned**; only the processing part is kept | help 66, 47. (Keysi's notes say the platform fee is not returned: that is older; the help pages now say otherwise) |
| On a chargeback | Seller covers the refunded amount and processing fees; Gumroad returns its platform fee | help 134 |
| Merchant of record | Yes, **for all sales since 2025-01-01**: Gumroad collects and remits sales tax and VAT worldwide; nothing for the seller to register or file. Seller still reports own income tax | pricing, help 121, 10; terms ("reseller and merchant of record", "you shall not issue any invoice") |
| VAT on the price | **Added on top.** A seller cannot make a digital price VAT-inclusive ("Can I choose not to charge VAT ... or make it inclusive? No"). So $29 is $29 before VAT for EU buyers | help 10 |
| Business buyers | An EU/UK buyer with a VAT ID can enter it at checkout or later on the invoice to get the VAT refunded | help 10 |
| Payout provider | Gumroad uses **Stripe** for card payments and **bank payouts**. Identity checks are Stripe's: date of birth, legal name, phone, address, a government ID number and photo ID, proof of address, and "Company Tax ID and business registration document (if applicable)". Account type **Individual** is for "do not have business registration documents" | help 260 |
| When Stripe asks | "after a certain amount of time has passed and sales accrued", and in rare cases rejects an account; a rejected account's balance of $1 or more is paid out | help 13 |
| Payout from the Netherlands | Bank, **EUR**, standard minimum **$100**; weekly/monthly/quarterly, sales wait **7 days**; Euro accounts are paid on Wednesdays; PayPal payout only where banks are unsupported. Every account is reviewed before the first payout (1-3 weeks, typically 3-4 sales with a balance above $100) | help 13, 160 |
| Gumroad's own seller terms | May hold funds on elevated refund/chargeback rates (reserve at 15% refunds), pending identity checks or an open review; may ask for a taxpayer ID | gumroad.com/terms |
| Chargeback limits | Payouts pause above 1% chargeback rate; above 1% disputing customers Gumroad forces a 30-day refund policy account-wide | help 134, 51 |
| Refund policy | Seller sets it **per product** (Product tab, Settings, "Specify a refund policy for this product"), with optional fine print; Gumroad Support then refunds on the seller's behalf and includes the policy in card disputes. Gumroad may refund within 90 days to prevent chargebacks; Brazilian consumers get 7 days regardless | help 335, 51 |
| Refund periods offered | The help pages mention policies "of 7 days or more" and 30 days. A **14-day** option is **U** (the editor lists the choices) | help 51, 335 |
| Licence keys | Turned on by **Content page, Insert, License key**; one block per product, only on one content page. Keys are issued to earlier buyers too once the block is added. Key format: four groups of 8 hex characters (sample `A1B2C3D4-E5F60718-9ABCDEF0-1234ABCD`) | help 76 |
| Per-key use limit | **No setting.** "License key enforcement is completely up to the creator ... Gumroad performs no additional license key verification." The `uses` counter is the only seat tool; the seller can fix it in the dashboard (Sales, the sale, License key section, Uses row: minus, plus, Edit, Reset) | help 76 |
| `verify` call | `POST https://api.gumroad.com/v2/licenses/verify`, no token. `product_id` (required for products made after 2023-01-09, shown in the License key block while editing), `license_key`, `increment_uses_count` ("true"/"false", **default true**). "Checking for a valid license on each launch will increment the usage count unless you set increment_uses_count to false" | help 76 |
| `verify` answer | 200 `{success, uses, purchase{...}}`; unknown key or wrong product: **404** with `{"success":false,"message":"That license does not exist for the provided product."}` (also measured live today with Keysi's product id and a zeroed key; Python's default User-Agent is not blocked) | help 76; live POST |
| Purchase fields | `refunded`, `disputed`, `dispute_won`, `chargebacked` (booleans), `email`, `price`, `currency`, `quantity`, `sale_timestamp`, `license_key`, `is_multiseat_license`, `variants`, `subscription_*` (`subscription_ended_at`, `_cancelled_at`, `_failed_at`, memberships only; ignore) | help 76 |
| Revocation | Gumroad does not turn a key off on refund or chargeback: the response stays `success:true`. "You can also check if a purchase has been refunded or disputed by checking the refunded/disputed fields". The seller can also **disable** a key by API (needs a token) | help 76 |
| Releasing a seat | `decrement_uses_count` needs an OAuth token of the seller: cannot ship in the program (K, `LicenseGateway.swift`) | Keysi; API page is client-rendered and could not be fetched as text, so this part is Keysi's measurement |
| Offer codes (Gumroad calls them discount codes) | Amount **or percentage** off; letters and digits only; **Limit quantity** caps total uses; each item bought counts one use; validity period; min amount; per product. Only one code per product, never stacked. Link form: `<product url>/<CODE>`. A code can be set to **apply automatically**: the page shows the original price crossed out beside the discounted one | help 128 |
| Code limit reached | Not stated. For an automatic code, only "validity period ends" is documented to bring back the full price. **U** whether reaching the quantity limit does the same | help 128 |
| Prices per currency | **No separate price per currency.** One price; the seller chooses a display currency; at checkout card buyers may pay in 32 local currencies at real-time rates with USD price endings kept (so $29 shows as roughly 26 EUR with a nice ending). Optional purchasing-power discounts of 20-60% by country, off unless switched on | help 46, 327 |
| Payout currency | EUR for a Dutch bank, converted at the rate of the sale | help 46, 13 |
| Test purchase | Logged into the seller account, the checkout offers "Test card"; no card, no real sale. A 100%-off code also works | help 62 |
| Direct to checkout | `?wanted=true` on the product URL opens the payment form; a code goes at the end of the path; UTM parameters are kept (K) | help 144, 270, 128 |
| Overlay | Exists (a Gumroad script on the page); shotfleet does not use it: it would need a third-party script in a CSP that allows only `'self'`. A plain link, as Keysi does | K; help 144 |
| Webhooks | Gumroad offers sale pings (**U**: not read today); neither Keysi nor shotfleet uses any webhook. Not needed: the program asks the licence API itself | K |
| Several accounts | Allowed; shotfleet's product goes in the **same account as Keysi** (one payout setup). Product id and permalink are per product | help 252 |
| Stripe sign-up flag | Gumroad's own page data carries `disable_stripe_signup: true` (seller-side Stripe Connect sign-up is off). Not about payouts through Gumroad | page data |

Payout and KvK, plainly: **V** that Gumroad's Individual type asks for no business registration, and that Keysi's account (same person, same country, same bank) was accepted as Individual with no KvK. **U** whether Stripe asks for a KvK later, when sales accrue and the review runs: Gumroad itself says Stripe may ask for more "after a certain amount of time has passed and sales accrued". A third-party help page claims Stripe now requires a KvK for Dutch accounts; I could not confirm that from Stripe. Keysi has not yet reached that stage. Keep payouts small and frequent until the first one lands, and read the answer in Gumroad's Payouts page after the first $100.

Not legal or tax advice: whether recurring income needs a KvK for Dutch income tax is a separate question (Keysi's `DISTRIBUTION-OPTIONS.md` makes the same point) and sits with an accountant. It was already an open item in LAUNCH.md.

## 3. Fee arithmetic (V fees, assumption flagged)

Fee = 10% + $0.50 (Gumroad) + 2.9% + $0.30 (card). Assumed: the percentages apply to the list price, not to VAT added on top (**U**; Gumroad's help says the fee is "+ sales tax" and does not say on which base the card fee runs). PayPal buyers: PayPal's own fee instead of the card fee (**U** amount).

| List price | Gumroad fee | Card fee | Net to Manu | Effective rate | Net on the old Lemon Squeezy / Polar figure (5% + $0.50) | Difference |
|---|---|---|---|---|---|---|
| $29 | $3.40 | $1.14 | **$24.46** | 15.7% | $27.05 | -$2.59 |
| $49 | $5.40 | $1.72 | **$41.88** | 14.5% | $46.05 | -$4.17 |
| $39 (reference) | $4.40 | $1.43 | $33.17 | 14.9% | | |

Discover sales (30% flat) would net $20.30 at $29. Do not opt in. Refunds return Gumroad's part of the fee, keep the card part (about $1.14 on $29).

## 4. Price and the founder offer

**$29 for the first 100, $49 after: still holds.** The loss against the research figure is $2.59 and $4.17 a sale, 10% of net, not a reason to move a price whose evidence is willingness to pay (research/pricing-2026-10.md). The decision rule (50 sales at $29 within 60 days) is $1,223 net, not $1,353. What does change:

1. **The page must say "plus VAT where it applies".** A Dutch buyer of the founder price pays $29 plus 21% VAT, about $35 (Polar showed VAT inside the 29). Gumroad cannot show a VAT-inclusive digital price. So "$29" is honest only with that line next to it.
2. A $19 or $39 tier would not change the picture: the fixed $0.80 weighs more at low prices (Keysi's argument, `marketing/STRATEGY.md` l.119).

**Founder price, simplest honest option:** list the product at **$49** and create the code **FOUNDER29**, **$20 off** (an amount, so the result is exactly $29), **Limit quantity 100**, no expiry, on this product only, and switch on **Automatically apply discount code** for it. The buyer sees $49 crossed out and $29 with no code to type and no way to miss it; the 101st buyer pays $49 with no action from Manu. This is the Polar setup (`FOUNDER29`, -20, 100 redemptions) carried over. Why not the other: a $29 product that Manu raises to $49 by hand after sale 100 sells at $29 until he looks, and one racing hour can sell sales 101 to 110 at the wrong price.

Two **U** points to settle in the first test: (a) whether the page still looks right once all 100 uses are spent (Gumroad documents only validity-period expiry as returning to full price; if that is the only way, add an end date to the code as a backup and check the code's use count after sale 90); (b) whether a test purchase or a 100%-off test code uses up one of the 100. Use a **separate** 100%-off, single-use code for testing, as Keysi did, and delete it afterwards.

**What the page states:** "$29 launch price for the first 100 buyers, then $49. One time, per developer. Prices are before VAT where it applies. 14-day refund." The site text must not carry a live "N of 100 left" number: nothing feeds it (the Polar redemption-count idea is gone; Gumroad's code use count is visible in the dashboard only). `tests/claims.json` C110 already says this.

## 5. What the code enforces (shotfleet.py, Gumroad path)

- Keys: four groups of 8 hex characters. Polar keys start with `SHOTFLEET-`, Lemon Squeezy keys are UUIDs 8-4-4-4-12: no collision (tested).
- Refunded, charged-back or disputed purchase: invalid at activation and at the weekly check; a **won** dispute (`dispute_won`) keeps the licence. A 5xx from Gumroad is an outage and falls under the 30 days offline grace, never a revocation. A 404 `success:false` means "no such key for this product" and does invalidate: a seller who disables a key must stop it (the cost: a wrong product id would also invalidate; go-live checks the id against the live product page first).
- **Use count.** The promise is "3 activations". Activation looks first with `increment_uses_count=false`; if `uses` is already 3 it refuses without spending another; otherwise one counted call. Re-running `activate` with the key a Mac already holds counts nothing. The weekly check, `SHOTFLEET_KEY` in CI and everything else send `false`: exactly one counted call per new activation (tested). `deactivate` cannot give an activation back (needs a token), so it says so; moving to a 4th Mac means an email, and Manu resets or lowers the count in the Gumroad dashboard (Uses row). The terms say exactly this. Ceiling: two activations at the same instant can pass 3, and a deactivate-then-activate on one Mac counts twice; both are fixed by hand.
- `GUMROAD_PRODUCT_ID` empty (a build that skipped go-live) fails loudly instead of sending an empty product id.
- TLS goes through certifi's bundle like Polar's did (the frozen build may not trust the Mac's).
- Polar and Lemon Squeezy code paths stay, tested, for keys that already exist. Nothing sells them. `POLAR_ORG_ID` is no longer set by go-live.

## 6. Manual checklist for Manu in Gumroad

Written so a Claude-in-Chrome session can follow it. Rule for that session: **stop and hand over at every step marked MANU ONLY** (identity, bank, accepting terms, anything with a password or code). Never buy with a real card. Never enter payment details.

Where: https://gumroad.com, logged in as Manu (the Keysi account). Dashboard menu names can change: if a name below is missing, look for the nearest one and say so.

1. **Check the account is ready (MANU ONLY if anything is missing).** Settings, Payments: account type Individual, country Netherlands, payout method Bank account in EUR, status not "under review". Do not change country (it clears payout details and forfeits unpaid balances: help 260). If Stripe asks for a KvK or company document anywhere here, **stop and tell the developer**; do not enter anything.
2. **New product.** Products, New product, type **Digital product**, name `shotfleet`, price **$49** (USD). Do not tick pay-what-you-want. Create.
3. **Product tab.**
   - Name: `shotfleet - localized App Store and Google Play screenshots`. Keep "shotfleet" first.
   - Custom permalink: `shotfleet` (so the link is `https://<account>.gumroad.com/l/shotfleet`; Gumroad may pick another if taken: note it).
   - Summary: `Capture real localized screenshots in every language from one Maestro flow, and check each one is in the right language. One licence per developer, a year of updates.`
   - Description: copy the "Price and licence" and "What it does" bullets from `site/public/llms.txt`, then add: `The program is a free download at https://shotfleet.com. This purchase is the licence key: it unlocks every language and export. Needs an Apple silicon Mac, Maestro and Java 17+.` Add this line: `Prices are before VAT where it applies.` State the licence limit exactly: `One key can be activated 3 times (up to 3 of your own Macs, plus CI). To move to a 4th Mac, email hello@shotfleet.com.`
   - Cover image and thumbnail (600 x 600): use `site/public/og.jpg` for the cover; a plain square with the name for the thumbnail. Optional.
   - Refund: toggle **Specify a refund policy for this product**, choose **14 days** (if the editor offers no 14-day option, stop and tell the developer: the site says 14 and its tests demand it), fine print: `Email hello@shotfleet.com within 14 days of buying and you get your money back. You do not have to explain. The free tier keeps working either way.`
   - Leave the checkout button text at the default ("I want this!" or "Buy this": Gumroad's choice).
   - Do not mark it as an e-publication (it is software; reduced VAT would be wrong).
4. **Content tab: licence keys (the step Keysi missed).** Open the Content tab, **Insert, License key**. Leave "Allow customers to choose number of seats" **off**. Under the block write: `Your key is above. Install: curl -fsSL https://shotfleet.com/install.sh | sh, then shotfleet activate <your key>. Up to 3 activations per key; to move to another Mac email hello@shotfleet.com.` Do **not** upload a file: the installer is public, Gumroad sells only the key. Copy the **product ID** shown in the License key block (22 characters ending `==`): it is not secret and goes into `packaging/go-live.sh`. Keep this ID in the chat to the developer.
5. **Checkout settings.** Checkout, Discounts tab: **New discount**.
   - Code `FOUNDER29`, this product only, **amount off $20** (not a percentage), **Limit quantity 100**, no minimum, no end date unless point (a) in section 4 says otherwise.
   - Then on the product's page (Product tab, pricing section) switch on **Automatically apply discount code** and pick `FOUNDER29`. The page must show $49 crossed out and $29.
   - Checkout form tab: show the discount-code box **only if a discount is available**.
   - Second code for testing: `SHOTFLEETTEST`, 100% off, **Limit quantity 1**, this product only. Delete it after step 8.
   - Settings, Purchasing power parity: leave it **off** (it would discount by country, 20-60%, and Gumroad applies the larger of PPP and a code). If it is already on from Keysi, tell the developer before changing it: it is account-wide.
6. **Tax.** Nothing to set: Gumroad is the merchant of record for all sales and collects VAT and sales tax itself (help 121, 10). Do not enter any VAT number as a seller. Just check that Settings, Payments shows no tax form request (a W-8BEN may be requested for non-US sellers: **MANU ONLY**, he signs it).
7. **Payout (MANU ONLY).** Settings, Payments: legal name, address (no PO box), bank account IBAN in EUR, identity documents if Stripe asks. Choose payout frequency (weekly is fine). The $100 minimum and the 7-day hold apply. If a KvK is demanded: stop (see step 1).
8. **Publish and test.**
   - Keep the product **unpublished** until step 8 passes in preview. Test purchase while logged in: Gumroad's "Test card" checkout (help 62), then a purchase with `SHOTFLEETTEST` and a throw-away email (MANU ONLY to receive the email). Confirm: the receipt contains a licence key; the key verifies with `tools/golive/storefront.sh <product URL> <product id> 49` (all lines ok); on the developer's Mac `shotfleet activate <key>` prints "activated", running it again counts nothing, a refund from the Sales dashboard makes the next weekly check fail (refund the test sale and wait, or set `checked` back in `licence.json` by hand).
   - Then **Publish**. Re-run `tools/golive/storefront.sh`.
   - Never pay with a real card and never buy it from the same account with a card.
9. **Accept terms (MANU ONLY).** If Gumroad shows a terms or seller-agreement prompt, the developer reads and accepts it himself.
10. **Hand back to the repo.** Give the developer: the product URL and the product ID. Then: `packaging/go-live.sh --dry-run <product URL> <product ID>`, `tools/golive/storefront.sh <product URL> <product ID> 49`, and the real run only when both are clean (LAUNCH.md).
11. **After the first sale.** Sales dashboard: confirm the order, its fee (expect about 15.7% at $29), the licence key and `uses = 1` after the first activation. After the first $100 balance, read the Payouts page for Stripe's verdict (section 2). To reset a Mac count: Sales, the sale, License key, Uses row, Reset or minus.

Open and unverified after this file: the 14-day refund option, what the founder page does after 100 uses, whether test purchases consume a code use, what Stripe asks after the first sales, the card-fee base when VAT is added, and PayPal buyers' fee.
