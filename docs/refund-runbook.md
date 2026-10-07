# Refund runbook (for the owner)

Written 2026-10-05 from Gumroad's help pages, its terms and its published source; background and sources in `research/refund-process-2026-10-05.md`. **No step below was run in the live Gumroad dashboard.** Button and menu names come from help text, so each Gumroad screen step is tagged:

- **[help]** the step is described in a Gumroad help article, but the live screen was not seen. Names may differ a little.
- **[unverified]** inferred; look for the nearest menu entry and trust the screen over this page.

Never: refund from Stripe or PayPal directly (Gumroad does not support it), buy shotfleet with your own card (Gumroad treats it as card testing and can suspend the account), or paste a buyer's key or email into a chat or a repo.

## 1. A request comes in

1. It reaches you by email: either `hello@shotfleet.com` or a reply to the Gumroad receipt (which goes to the support email in Gumroad Settings, Support section **[help]**; check that it is `hello@shotfleet.com` or forwards there **[unverified]**).
2. Reply within two business days. If a buyer has written and you stay silent for 30 days, Gumroad may refund them itself and tell you **[help: gumroad.com/help/article/190]**.
3. Day count: 14 days from the purchase date in the Gumroad sale. Inside 14 days: refund, no questions. After 14 days: section 7.

## 2. Refund the sale

1. gumroad.com, sign in, **Sales** (called the Sales or customer dashboard) **[help: article 47, 268]**.
2. Search the buyer's email, click the sale to open the customer drawer **[help]**.
3. Scroll down and click **Refund fully** **[help]**. For a goodwill part-refund type an amount in the Refund box and click **Issue partial refund**: the buyer keeps the key and keeps access, so use it only if you want that **[help]**.
4. A $0 sale (a 100%-off code) has no refund button: the sale is not refundable **[from Gumroad's source, not seen live]**. Use section 5 instead.
5. If Gumroad says the balance is too low, the refund waits until more sales come in **[help: article 47]**, or the balance goes negative and Gumroad can debit your bank account and may suspend the account **[help: article 269, terms 11.3(a)]**. Tell the buyer the refund is on its way and ask Gumroad support (support@gumroad.com) what to do.
6. What happens: the buyer gets an email; card money arrives in 5 to 10 business days, PayPal at once; VAT is refunded too; Gumroad returns its own fee and keeps the card processing part, so expect to lose about $1.14 (at $29) or $1.72 (at $49) **[help]**.

## 3. Reply to the buyer

Template A, refund done (inside 14 days):

> Subject: Your shotfleet refund
>
> Hi NAME,
> I've refunded your shotfleet purchase in full, including any VAT. Gumroad sends you a confirmation, and on a card the money usually shows up in 5 to 10 business days.
> Your key stops unlocking every language and export the next time shotfleet checks it (about once a week). `shotfleet check` and 2 languages in `run` stay free, and nothing you already made is deleted.
> If you tell me what didn't work I'll try to fix it, but you don't have to.
> Manu

Template B, request after 14 days (pick one of the two middle paragraphs):

> Subject: Re: your shotfleet refund request
>
> Hi NAME,
> Thanks for writing. The 14-day refund window has passed, so this is my call, not a rule.
> OPTION 1: I'm happy to refund you, and I've done it. Gumroad will email you.
> OPTION 2: Before I do: can you send me the output of `shotfleet doctor` and say which step failed? If I can't get it working for you within 3 days, I'll refund you.
> Manu

Do not mention chargebacks or argue about whose fault it is.

## 4. Check afterwards

1. In the sale drawer the sale should show as refunded **[help]**.
2. Optional, licence API (read only, uses nothing). You need the product ID (`GUMROAD_PRODUCT_ID` in `shotfleet.py`) and the buyer's key from the sale drawer. **Always send `increment_uses_count=false`**, or the call counts as an activation (default is true):

   `curl -s https://api.gumroad.com/v2/licenses/verify -d "product_id=PRODUCT_ID" -d "license_key=KEY" -d "increment_uses_count=false"`

   Do not paste the answer anywhere: it contains the buyer's email.
3. Read the answer:

| Answer | Meaning | shotfleet says |
|---|---|---|
| 404 `This license key has been disabled.` | Expected for a full refund (Gumroad source, 2026-08-19). Also what a manual disable gives. | `the key was disabled, as Gumroad does after a full refund` |
| 200 with `"refunded": true` | The older behaviour, or the disable did not run. Still refused. | `the purchase was refunded` |
| 200, `"refunded": false` | The refund did not go through, or it was partial. The key still works. | nothing |
| 404 `That license does not exist for the provided product.` | Wrong product ID or key. Do not conclude anything. | |

4. The Mac locks at its next check, up to 7 days after the refund (30 if offline). A CI key (`SHOTFLEET_KEY`) is checked on every run, so it locks at the first run that reaches Gumroad after the refund; while Gumroad is unreachable it keeps working only on machines where it passed a check in the last 30 days. To see it sooner on your own test Mac, set `checked` in `licence.json` back 8 days and run `shotfleet export`. Details: `research/refund-process-2026-10-05.md`, section 3.

## 5. Reset or disable a key

In **Sales**, the sale, **Manage license keys** **[help: article 268]**:
- **Uses row**: minus, plus, Edit (type a number) or Reset to zero. Use it when a buyer runs out of activations (5 per key): reset to 0 or set it to the number of Macs they still use, then the buyer runs `shotfleet activate KEY` on the new Mac **[help]**.
- **Disable the key** (a leaked key, a $0 sale you want dead): the key answers 404 disabled, so every Mac and CI run is refused at its next check **[help; button label unverified]**. It also stops the real owner: tell them and give a new sale or code.
- **Revoke access** to a purchase is a second way, not offered for refunded sales **[from Gumroad's source; label unverified]**.
- Re-enabling a key is possible in the same place **[unverified]**.
- Never delete or recreate the Gumroad product: every key answers 404 and every Mac locks within a week.

## 6. A chargeback or dispute

1. Gumroad emails you the buyer's email and a link; it shows in Sales as a full refund, and in the customer export under Disputed **[help: article 134]**.
2. Reply to the buyer politely and ask them to cancel the dispute. Do not refund as well without asking Gumroad support first: its terms say a buyer's refund request is declined once they have a dispute open (terms 7.2(b)), and I could not find what a seller's own refund does then.
3. In the email, **Submit Additional Information** within 72 hours (120 hours if a weekend falls inside); you can submit once. Upload: the order email, `terms.html` and the refund policy as shown on the product page, your emails, and what the buyer did with the program if you know. If you stay silent, Gumroad submits without you **[help]**.
4. Cost: the sale amount and the processing fees; Gumroad returns its own fee. The buyer cannot buy again through Gumroad **[help]**.
5. shotfleet: the key (`chargebacked` true) is refused at the next check. If you win, `chargebacked` goes false and `dispute_won` true, and the next check accepts the key again by itself. The win can take months and shows as a balance credit.
6. Watch the numbers: chargeback rate above 1% pauses payouts, above 1% disputing customers a policy is forced on the account, and a refund rate above 15% lets Gumroad hold 25% of your funds for 90 days **[help; terms 11.3(b)]**. With few sales one case can cross a limit.

## 7. A request after 14 days

Not owed by the promise on the site. Default: ask what failed (Template B, option 2), refund up to about 30 days if it cannot be fixed, and decline later ones kindly. A refund costs about $1.14 to $1.72; a chargeback costs the whole sale plus fees and counts against the limits above. If the buyer says they are a consumer in the EU, or complains that they never got the withdrawal information, refund and note it for the lawyer: the statutory right can run up to 12 months when the information is missing (`research/refund-process-2026-10-05.md`, section 4).

## 8. What to record for the accountant

Keep one line per refund, plus Gumroad's own exports (Sales CSV from the Sales page, and the CSV of each payout from Payouts **[help: article 268, 269]**):

- Gumroad order number or sale ID, sale date and refund date;
- gross price, the VAT Gumroad collected, Gumroad fee, card fee kept, net you received;
- amount refunded, VAT refunded, fee returned by Gumroad, net cost to you;
- the payout (date and period) the sale and the refund fell into, and a negative balance if any;
- for chargebacks: the dispute date, outcome, any credit when won;
- buyer country and whether a VAT ID was given (business or consumer);
- your reply and its date (proof you answered within two days).

Do not store the licence key or card details. Open questions on how to book these: `research/refund-process-2026-10-05.md`, section 8.

## 9. Steps not verified in the live dashboard

Sales menu name; the Refund fully and Issue partial refund buttons; Manage license keys and its Disable, Reset and Edit labels; Revoke access; whether Settings, Support email is `hello@shotfleet.com`; whether the sale shows a "refunded" badge; whether a refunded FOUNDER29 sale still counts as one of the 100 uses. The first real refund settles all of them: write down what you saw next to each line here.
