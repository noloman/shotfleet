# Plan: prove that a refunded key locks (2026-10-08)

Why it is still open: Gumroad's seller test mode and a $0 sale have no Refund button (`docs/refund-runbook.md`, "Seen live on 2026-10-08"). Everything else of the sale-to-lock path was run live that day: purchase, receipt, activation, five-use limit, reset, resend receipt, disable and the shipped program's refusal. What remains is Gumroad's own "Refund fully" button, and whether a full refund disables the key by itself (Gumroad's published source says yes; the program also handles `refunded: true`).

Never use the owner's own card (Gumroad treats it as card testing and can suspend the account, which also holds Keysi). A different person buys with their own card.

## Cheapest version (about $1, needs one single-use code)

1. Owner approves creating a single-use fixed-amount discount code for the product that brings the price to the Gumroad minimum (about $0.99 plus VAT), valid for one day, shared only with the buyer; delete it afterwards.
2. The buyer opens `https://8954369651852.gumroad.com/l/shotfleet/<CODE>` and pays with their own card. They forward the receipt, or the owner reads the key from Sales (never paste it in chat).
3. Owner (or the agent, with the key in a chmod 600 file): `sh /Users/manu/Developer/shotfleet-rc-build/refund-proof/refund-proof.sh before KEYFILE` (installs the live release in a throwaway HOME, shows the API says valid, activates, shows a licensed command passes the gate).
4. Owner refunds: Gumroad, Sales, the sale, **Refund fully**. Write down every label and dialog next to `docs/refund-runbook.md` section 2 and 9.
5. `sh .../refund-proof.sh after KEYFILE` (shows the API answer, sets the weekly check back 8 days, shows the activated Mac, a new Mac and a CI key all refused).
6. Record the result in `docs/refund-runbook.md` section 9 and delete the code.

Full-price version: same without the code; the buyer pays about $35 (price $29 with FOUNDER29, plus 21% VAT in the Netherlands), the refund returns it, the owner loses about $1.72 in fees.

## Message to send to the buyer

> Hi NAME, I'm testing the refund path of shotfleet before a launch weekend. Could you buy it once with your own card (about $1 with a one-day code, or $35 at the normal price) and then forward me the receipt? I refund you right after, in full, including VAT, so you get it back in 5 to 10 business days on a card. You can ignore the app itself.

## What to watch

Gumroad may refuse a refund when the balance is too low (the refund waits for more sales, runbook section 2.5); a sale made today only counts as available after Gumroad's hold, so expect a "balance" message and write down exactly what the screen says.
