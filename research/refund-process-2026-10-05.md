# Refunds: how they work, what shotfleet does, what the law says (2026-10-05)

Research, not legal or tax advice. Every statement is marked **VERIFIED** (primary source, URL, read 2026-10-05) or **INFERENCE** (my reading, or something only a live test settles). Nothing was bought, refunded or changed in Gumroad: the only Gumroad calls were public GETs of help pages, the terms and the public product page.

Sources used, short names:
- **H47, H51, H335, H190, H134, H76, H268, H269, H13, H10, H62, H66** = `gumroad.com/help/article/<number>`: 47 Issuing a refund, 51 Gumroad's refund policy, 335 Custom refund policy, 190 How do I get a refund, 134 Chargebacks, 76 License keys, 268 Sales dashboard, 269 Payouts dashboard, 13 Getting paid, 10 EU and UK VAT, 62 Testing a purchase, 66 Fees.
- **GT** = `gumroad.com/terms` (Last Updated 14 September 2026). **SRC** = Gumroad's open source code, `antiwork/gumroad` on main (the code Gumroad publishes; I could not confirm what runs in production today).
- **BW6, BW3** = Burgerlijk Wetboek boek 6 and 3 on `wetten.overheid.nl`, consulted 05-10-2026 (BW6 "geldend van 16-07-2026"). **ACM** = `acm.nl/nl/verkoop-aan-consumenten/klantenservice/bedenktijd`. **PAGE** = the live product page `8954369651852.gumroad.com/l/shotfleet`.

## 1. Summary

1. A full refund is a Gumroad dashboard action. Gumroad returns its own fee and keeps the card fee, so a refund costs about $1.14 (at $29) to $1.72 (at $49) plus the sale (INFERENCE from H47 and the fee table in `research/gumroad-setup.md`).
2. **New and unrecorded in the repo:** Gumroad's code disables the licence key on a full refund (commit "Disable license keys when a purchase is fully refunded", 2026-08-19, `app/modules/purchase/refundable.rb`). The repo's notes say Gumroad does not (`research/gumroad-setup.md:47`). Both outcomes are refused by shotfleet; only the message differs. Not yet seen on a live key.
3. A refunded Mac stops unlocking at its next due check: 0 to 7 days after the refund when online, up to 30 days after its last good check when offline. A CI key stops at the next CI run if the runner can reach Gumroad. Nothing is deleted.
4. The site promised "if shotfleet doesn't work for your app ... no questions asked". Gumroad's live policy says "You do not have to explain". Fixed in `terms.html`.
5. The repo's plan to prove refunds ("buy with your own card" in `STATUS.md:25`, "refund the sale" of a 100% code in `LAUNCH.md:106`) conflicts with Gumroad's rules: do not pay for your own product with a card (H62, H13), and a $0 sale cannot be refunded (SRC). Use a second person, see section 7.

## 2. (A) Gumroad mechanics

| Question | Answer | Label, source |
|---|---|---|
| How does the seller refund? | Sales dashboard, click the sale to open the customer drawer, scroll down, **Refund fully**. Partial: type an amount in the Refund box, **Issue partial refund**. Only from the dashboard, not from Stripe or PayPal. | VERIFIED H47, H268. Button names from help text; the live dashboard was not opened |
| Partial refunds | The buyer keeps access. In code a partial refund leaves `refunded` false, so the shotfleet key keeps working. A series of partial refunds that adds up to the full price counts as full and disables the key. | VERIFIED H47; SRC `refund_partial_purchase!`, `as_json_for_license` |
| Time limit for the seller | None stated for card sales. PayPal sales can expire (`paypal_refund_expired?` exists, length not read). Irrelevant inside 14 days. | VERIFIED H47 says none; SRC for the PayPal flag |
| Seller must have the balance | "Refunds can only be processed if your balance is able to cover the transaction amount ... make additional sales until the refund can be issued." | VERIFIED H47 |
| Negative balance | H269 says a balance that goes negative from refunds or chargebacks may be debited from the bank account. GT 11.3(a) lets Gumroad suspend an account with a negative balance. The two help pages disagree on whether the refund is blocked or the balance goes negative. | VERIFIED H269, GT; the disagreement is mine to flag |
| Refund after a payout | The money has left, so see the two rows above. Payouts wait 7 days after a sale and need $100 (weekly, monthly or quarterly schedule), so early on a 14-day-old sale is usually still in the balance. A monthly or quarterly schedule keeps a buffer. | VERIFIED H13, H269; the conclusion is INFERENCE |
| What the buyer sees | An email confirming the refund. Card money in 5 to 10 business days, PayPal immediately. They lose access to the content and updates, and their rating is deleted. Refunds are in the charged currency. | VERIFIED H47 |
| Fees on a refund | Gumroad's own fee on the refunded part is returned; the payment-processing part is kept. | VERIFIED H47, H66 |
| VAT on a refund | A refund includes the sale amount plus the VAT. Partial refund, proportional VAT. Gumroad is merchant of record and collects and remits VAT, so the seller does no VAT step. A buyer with a VAT ID can also get VAT back through an invoice. | VERIFIED H10, H121 (`gumroad.com/help/article/121-sales-tax-on-gumroad`), H200 |
| $0 orders | Cannot be refunded: the refund action only finds sales with a price above 0 (`seller.sales.paid`). Use disable key or revoke access instead. `STATUS.md` agrees: the creator test purchase "cannot be refunded". | VERIFIED SRC `process_refund.rb`; consistent with STATUS |
| Refund policy shown to buyers | Set per product. PAGE shows "14-day money back guarantee", fine print: "Email hello@shotfleet.com within 14 days of buying and you get your money back. You do not have to explain. The free tier keeps working either way." (updated 2026-10-03). So the 14-day editor option exists. | VERIFIED PAGE; H335 |
| Who refunds, Gumroad or me | Gumroad "allows creators to set their own refund policies and issue their own refunds". Gumroad refunds on its own only for fraud, duplicate charges, Brazil's 7-day withdrawal, within 90 days to prevent a chargeback, or when a seller is silent for 30 days after the buyer wrote. Buyers are told to reply to the receipt, which goes to the seller's support email. | VERIFIED H190, H51, H204 |
| Chargeback: who pays | The seller covers the refunded amount and the processing fees; Gumroad returns its platform fee. It shows up to the seller as a full refund. Gumroad blocks that buyer from buying again, emails the buyer to cancel, gives the seller 72 hours (120 over a weekend) to add evidence once, and a win comes back as a balance credit, sometimes months later. | VERIFIED H134, H269 |
| Account limits | Payouts pause above a 1% chargeback rate. Above 1% disputing customers a refund policy is enforced account-wide. A refund rate above 15% lets Gumroad hold 25% of funds for 90 days; above 25% the account may be suspended. With few sales one refund can cross 15%. | VERIFIED H134, H51, GT 11.3(b); the small-numbers point is INFERENCE |
| Licence API fields | `refunded` is true only for a full refund. `chargebacked` is true from a chargeback until it is reversed. `disputed` is true from the chargeback on and stays true after a win. `dispute_won` is true after a win. | VERIFIED H76 names them; SRC `as_json_for_license`, `payload_for_ping_notification` give the meaning |
| Is the key still valid after a refund? | Per the source since 2026-08-19: no, Gumroad disables it, and verify answers 404 `This license key has been disabled.` Before that, or if the change is not live: `success:true` with `refunded:true`. After a chargeback the key stays enabled and only the flags change. | VERIFIED in SRC (commit 5bf874a, #7326); production state INFERENCE; H76 predates this |
| Disable, reset, use count | Dashboard: Sales, the sale, **Manage license keys**: disable the key, and on the Uses row use minus, plus, Edit or Reset. The seller can also revoke access to a purchase (not offered on refunded ones). API: disable, enable, rotate and decrement need an OAuth token with `edit_products`, which cannot ship in a program. | VERIFIED H268, H76, SRC `licenses_controller.rb`, `purchase_policy.rb`; exact button labels not seen |
| The Gumroad terms | Gumroad is reseller and merchant of record, handles refund requests "in Gumroad's sole discretion", and the supplier reimburses (GT 6.2(d), 7.1(a)). The product is "licensed by you through Gumroad to the relevant Buyer" with your end-user terms (6.7). Sellers may not suggest buyer terms that reduce the refund and chargeback section (GT, user conduct). | VERIFIED GT |
| Founder code and refunds | A refunded FOUNDER29 sale probably still counts as one of the 100 uses (the use count does not exclude refunded sales in the code). | INFERENCE from SRC `offer_code.rb`, `purchase.rb` |

## 3. (B) What shotfleet does on a refund

### Timeline (refund on day R, key activated day 0, `checked` set at activation)

| When | Gumroad | shotfleet on the buyer's Mac | Label |
|---|---|---|---|
| Day R | Owner refunds. Buyer emailed. Key disabled (new code) and `refunded` true. | Nothing yet: the Mac only asks Gumroad when its last good check is 7 days old (`shotfleet.py:3752`, `require_licence`). | VERIFIED code |
| Day R to the check | Money returns 5 to 10 business days (card). | Everything still unlocks: all languages and `export`. This is the unavoidable lag. | VERIFIED |
| First `run` or `export` at 7 days or more since the last check, online | Verify answers 404 disabled, or 200 with `refunded:true`. | Refused. `export`: `shotfleet: this licence is no longer valid (the key was disabled, as Gumroad does after a full refund). https://shotfleet.com/#price`, exit 2. `run`: the same as a `note:` on stderr, then `free tier: capturing 2 of N languages`. | VERIFIED, tests `GumroadLicence` |
| Same, offline or Gumroad down (5xx) | No answer. | Works until 30 days after the last good check, then `couldn't reach the licence server for 30 days`. | VERIFIED test |
| Idle Mac | No background job. | No check happens until the next `run` or `export`. | VERIFIED code |
| Second activated Mac | Same key. | Own `checked` clock, so it locks at its own next check (activated day 5, rechecked day 12). | VERIFIED code |
| CI with `SHOTFLEET_KEY` | Same key. | Checked on every `run` or `export`, no weekly cache, no activation used. Refused at the next CI run. If the runner cannot reach Gumroad it passes (fails open, with no 30-day limit). | VERIFIED code (`shotfleet.py:3844-3851`) |
| Buyer tries `activate` again | Same answer. | `that key didn't activate: the key was disabled ...`, no activation spent. | VERIFIED test |
| Buyer buys again | New purchase, new key, `uses` 0. Nothing blocks a re-buy after a refund (only after a chargeback). | Works as a new licence. | VERIFIED H134 (block is for chargebacks); INFERENCE for the rest |

Worst case online: refund just after a check, so 7 days of lag. Typical: activation day 0, refund day 3, daily user locks on day 7 (4 days). Refund on day 13 with the last check on day 7 locks on day 14.

**Nothing is deleted.** `licence.json` stays (only `deactivate` removes it), and no screenshots, run folders, configs or exported fastlane folders are touched (`require_licence` raises before any work). The free tier keeps `check`, `doctor`, `init`, `activate` and `run` for the first 2 languages. This matches the Gumroad fine print "The free tier keeps working either way".

### Cost of a shorter recheck
- Calls: weekly is 52 per Mac per year, daily 365. For 150 Macs that is 7,800 against 55,000 a year, each one small POST. I found no per-call fee and no licence-specific rate limit in Gumroad's `rack_attack.rb`, but I did not read the generic limits (INFERENCE). CI keys are the real volume: one call per CI run.
- Lockout: the 30-day grace covers outages and offline use at any recheck rate, so a shorter interval adds no lockout risk from outages. The risk is a wrong **verdict**, which has no grace: a 404 for a valid key (product deleted or recreated, a key disabled by mistake) locks every Mac at its next due check. Daily means a bad day hits everyone within a day, weekly spreads it over a week.
- Benefit: only the days between refund and lock, about 3.5 days on average at weekly. The buyer already got the 14 days. **Keep 7 days.**

### Abuse cases
| Case | What happens | Cost to me |
|---|---|---|
| Buy, `run` every language, `export`, refund | Buyer keeps all screenshots and exports forever. Nothing in code can take them back. | The card fee ($1.14 to $1.72) and a founder slot (INFERENCE). |
| Repeat the cycle with a new email | New key each time. Gumroad does not block it. | Same per cycle. Visible as one buyer with several sales in the Sales search. |
| Key shared before refund | At most 3 Macs; CI keys use no activation, so many machines are possible. The refund kills all of them at their next check (CI: next run). | None extra. |
| Key leaked publicly, no refund | Disable it in the dashboard. That also locks the real buyer, who must be given a new one (a new sale at $0 or an API rotate). | Support time. |
| Buyer edits `checked` in `licence.json`, or blocks `api.gumroad.com` | A refunded buyer keeps the unlocked state. There is no signature on the file. | Accepted: this is an honesty system for a $29 to $49 tool, and a code change is not proposed. |

## 4. (C) Policy and law

**The promise.** Site and PAGE both say 14 days from buying. Gumroad enforces nothing by itself: the seller refunds by hand. Gumroad adds its own 90-day discretionary refunds and Brazil's 7-day right (`terms.html:55` says so, and H51 and H190 confirm it).

**EU and Dutch 14-day withdrawal right (consumers only).**
- VERIFIED BW6 6:230o lid 1 sub c: for digital content not on a tangible medium the 14 days run from the day the contract is made, and need no reason (lid 1, "zonder opgave van redenen"). Same on Your Europe (`europa.eu/youreurope/citizens/consumers/shopping/returns`).
- VERIFIED BW6 6:230p sub g: the right is lost only if performance began with the consumer's prior express consent, the consumer declared they lose the right, **and** the trader sent the confirmation on a durable medium (6:230t lid 2 or 230v lid 7). ACM lists the same steps (inform, get consent, add it to the confirmation, give access only after the consumer starts it).
- VERIFIED BW6 6:230o lid 2: if the withdrawal information (conditions, term, how to exercise, model form, 6:230m lid 1 sub h) was not given, the 14 days extend, at most 12 months. ACM says the same.
- VERIFIED BW6 6:230oa: a trader who sells through an online interface must offer a withdrawal function (a clearly visible button, two steps, a confirmation on a durable medium). This is Directive 2023/2673, applying from 19 June 2026 (date from law firm summaries, not EUR-Lex, which blocked my fetch).
- INFERENCE: the 14-day promise gives consumers what the statute gives in time, but not in form: a consumer may withdraw by any clear statement, not only by emailing `hello@`; the old "if it doesn't work" condition contradicted "without giving reasons"; and the site gives none of the withdrawal information, so the 12-month extension could apply. I found nothing in Gumroad's help that captures the consent and acknowledgement in 6:230p g, so do not rely on that exception to refuse a refund.
- INFERENCE: it applies to consumers. Many shotfleet buyers will be businesses (a VAT ID at checkout is the visible signal). Who counts as the trader here, you or Gumroad as reseller and merchant of record, is open: GT 6.2 and 6.7 point both ways. Question for a lawyer.

**What the law asks sellers to state.** VERIFIED BW6 6:230m lid 1: identity and trade name, geographic address, phone and email, the withdrawal conditions, term and model form (sub h) or the fact that there is none and when it is lost (sub k), functionality and interoperability of digital content (r, s), and a reminder of the statutory conformity rights for digital content (w). VERIFIED BW3 3:15d: any online service must make identity, **address of establishment** and email easily and permanently reachable, plus the KvK number only if registered. The site shows a name and `hello@` only (`terms.html:60`, footer, privacy page): no address. A private seller without KvK still has the address duty on its face (INFERENCE; ask).

**Wording and Gumroad's terms.** `terms.html` was consistent with Gumroad on the 90 days and Brazil, but said "Refunds go through Gumroad too" without saying who starts a refund. Gumroad's own help tells buyers to reply to the receipt, which goes to the support email in your Gumroad settings (H204, `gumroad.com/help/article/352-supporting-your-customers`). Whether that setting is `hello@shotfleet.com` I could not see. Not in conflict with GT (the site does not limit the buyer's rights), but GT forbids suggesting such terms, so do not add "no refund after 14 days".

**After 14 days.** Legally you owe nothing in time for a business buyer, and for a consumer only the cases above and the statutory conformity rights if the program is defective (INFERENCE, Directive 2019/770, not verified here). Practically: a refund costs the card fee; a chargeback costs the sale, the processing fee and counts against the 1% and 15% limits. Reply within two business days, ask what failed, and refund up to about 30 days by default. The runbook has the template.

## 5. (D) Owner runbook
`docs/refund-runbook.md`. Every Gumroad screen step there is marked: none was seen live, so all button names come from help text.

## 6. (E) Gaps found

| Where | What contradicts what I verified | Fix |
|---|---|---|
| `site/public/terms.html:51` (before) | "If shotfleet doesn't work for your app ... no questions asked" against PAGE "You do not have to explain" | **Applied.** "You can ask for a refund within 14 days of buying and you'll get it, no questions asked, and you don't have to say why." |
| `terms.html:52` (new) | The page never said a refund ends the licence | **Applied**, with C047 quoting it |
| `terms.html:55` | No refund timing or VAT detail | **Applied**: money including VAT, card 5 to 10 business days |
| `STATUS.md:25`, `STATUS.md:77` | "buy with your own card" contradicts H62, H13 (can suspend the account), and `research/gumroad-setup.md:128` | Replace with: "Have another person buy at full price with their own card; refund it in Gumroad; set `checked` back 8 days; expect `the key was disabled` or `the purchase was refunded`." |
| `LAUNCH.md:106-108`, `research/gumroad-setup.md:126` | Refunds a 100%-off test sale; $0 sales cannot be refunded | "A 100%-off sale cannot be refunded: disable its key in Manage license keys and expect `the key was disabled`. Only a paid sale tests the `refunded` flag." |
| `research/gumroad-setup.md:15,47,92` and `tests/claims.json` C047 proof | "Gumroad does not turn a key off on refund" is outdated per SRC | Say: a full refund disables the key (404), a chargeback only sets flags. C047 note **added**; setup file text left for the owner |
| `shotfleet.py:3778` docstring | Same outdated claim | **Applied** (one line) |
| `marketing/launch-email.md:22` | "If it doesn't work for your app, reply within 14 days and I'll refund you." Conditional, quoted by C054; not published | "Reply within 14 days and I'll refund you, no questions asked." (and update C054 text) |
| `terms.html:57-58` "No warranty ... limited to what you paid" | Consumers' statutory conformity rights cannot be waived (INFERENCE) | Add: "If you are a consumer, nothing here limits the rights the law gives you." Lawyer to confirm |
| `terms.html:60`, footer, privacy | No postal address (BW3 3:15d, BW6 6:230m) | Owner decision, see section 9 |
| `terms.html` (missing) | No withdrawal information or function (BW6 6:230m h, 230oa) | Lawyer; draft: "If you are a consumer in the EU you can also withdraw within 14 days by emailing hello@shotfleet.com with a clear statement; no reason needed." |
| `shotfleet.py:3786` | A 200 answer that is not JSON (hotel Wi-Fi login page) raises a cryptic `Expecting value` error from `run` and `export` instead of using the 30-day grace; only the HTTP error path converts it | **Not applied** (outside the refund theme). Fix: `except ValueError: raise OSError("the licence server's answer was unreadable")` around `json.loads`; add a test. It makes a captive portal behave like offline, which is already allowed for 30 days |
| `skill/shotfleet/references/troubleshooting.md:106,109` | Does not list `the key was disabled` | Add the text to both rows (refunded or disabled) |

## 7. Recommendations, ranked

1. **Do not buy your own product with your card** (H62, H13). Prove the refunded path with one paid sale by a second person, then refund it. For the `disabled` path use the 100%-off test sale and disable its key. Fix `STATUS.md:25`, `LAUNCH.md:106`.
2. Check Gumroad Settings, Support email is `hello@shotfleet.com` (or forwards to it), so replies to the receipt reach you. Answer refund emails within two business days (H190: silence for 30 days lets Gumroad refund and flags you).
3. Keep the unconditional 14 days. Offer 30 days by default, case by case, for anyone who cannot get it working: a refund is cheaper than a chargeback.
4. Keep a buffer so a refund never hits an empty balance (monthly payouts at the start, GT 11.3(a), H47). Watch the refund rate in the first sales: one refund in six sales is over 15%.
5. Keep the 7-day recheck and 30-day grace. Do not delete or recreate the Gumroad product (every Mac would get a 404 verdict).
6. Fix the non-JSON answer error (section 6) and the troubleshooting rows.
7. Take the consumer-law questions to a lawyer before more consumers buy (section 8), and decide the address question.

## 8. Open questions for an accountant or lawyer

Accountant: (1) how to book a refunded sale when Gumroad is reseller and merchant of record: turnover is what Gumroad pays you, so does a refund reduce it and in which period; (2) the processing fee Gumroad keeps on a refund, a deductible cost?; (3) chargebacks and a negative balance, same; (4) do refunds change the KOR turnover line (EUR 20,000); (5) which Gumroad report is the record: Sales CSV (H268) and payout CSVs (H269).

Lawyer: (1) is the seller or Gumroad the "handelaar" for an EU consumer; (2) must the site carry the withdrawal information, model form and the withdrawal function, and does Gumroad's checkout already; (3) do the "no warranty" and liability lines survive against consumers; (4) is a postal address required for a private seller without KvK; (5) can the 6:230p g consent route be built into Gumroad's checkout at all; (6) are the 12-month extension and the statutory conformity rights a reason to refund consumers after 14 days.

## 9. Owner decisions
- Who makes the paid test sale, and when (blocks the "refunded key" proof).
- Postal address on the site, or a business address once the KvK exists.
- Default policy after 14 days (30 days case by case, or stay strict).
- Whether to ask Gumroad support (support@gumroad.com) if the full-refund licence disabling is live in production.
