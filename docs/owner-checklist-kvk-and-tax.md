# Owner checklist: KvK, tax and Gumroad (Netherlands)

For Manu. This is a checklist, not tax or legal advice. The sources and the parts that are not verified are in `research/tax-nl-2026-10.md`. Nothing here can be done by an agent: registering needs your identity, and some steps cost money.

## 1. Register with the KvK (do this first)

- **Why:** selling software for profit on an ongoing basis is running a business, so a sole trader (eenmanszaak) registers with the KvK. The KvK passes your details to the Belastingdienst, which then sends your VAT identification number and your tax number. Source and wording: `research/tax-nl-2026-10.md`, section 1.
- **When:** from the moment you are economically active. Shotfleet has been on sale since 2026-10-05, so do it now rather than later.
- **How:** kvk.nl, "Eenmanszaak inschrijven", online. You identify yourself with DigiD or at a KvK location. There is a one-off registration fee (check the current amount on the form before you pay).
- **What to enter:** your own name as the business name works; trade name `shotfleet` (check it is free in the KvK trade-name search); activity: developing and selling software (the form suggests an SBI code, confirm the one it offers); address: your home address is public in the register unless you ask the KvK to hide it where the rules allow, so read that section of the form.

## 2. Questions for an accountant (one short conversation)

1. Gumroad is the merchant of record and collects buyers' VAT. Are my sales to Gumroad (a US company) outside Dutch btw, reverse-charged, or something else, and do I still file btw returns?
2. Should I use the kleineondernemersregeling (KOR), and does my situation allow it?
3. How are Gumroad's payout statements (gross sales, fees, taxes, payouts in EUR) entered in my income tax return?
4. Which deductions apply to a starting sole trader (zelfstandigenaftrek, startersaftrek, MKB-winstvrijstelling) and what time-spent evidence do I need to keep?
5. The W-8BEN form Gumroad may ask for: which treaty rate applies to a Dutch individual, and how do I fill it in correctly?

Bring: `research/tax-nl-2026-10.md`, one Gumroad payout statement, and the price list ($49, $29 for the first 100).

## 3. Gumroad account items only you can do

- Complete any tax-information request in Gumroad Settings, Payments (a US tax form for non-US sellers). Do not guess the treaty rate; use the accountant's answer.
- The founder code FOUNDER29 stops being useful after 100 uses (limit set on the code). Check the count in Checkout, Discounts.
- Payouts: weekly, minimum 100 USD (already set).

## 4. Records to keep from day one

Gumroad sales and payout statements, the licence-key emails you send by hand (resets), refunds, and a simple time log of the hours spent on the product (helps with the self-employed deduction).

## 5. Afterwards

- Tell the person who updates the site if the legal text must change (terms and privacy name Gumroad as merchant of record).
- Revoke the app-specific password named `shotfleet-notary` at account.apple.com once releases no longer need to be notarized from this Mac; releases do need it.
