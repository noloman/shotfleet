# Launch: your part (about 20 minutes, then Polar's review)

Everything else is done and scripted. Signing and notarization use your Developer ID and the `KeysiNotary` profile;
the program is served from the shotfleet site (no public repos); `packaging/go-live.sh` does the rest.

Payments are on **Polar** (merchant of record: it charges and pays the VAT; a personal account is allowed, so no KvK is
needed to open it). Lemon Squeezy asks for a company number, so it is not used. Prices: **$49** once, **$29 for the
first 100** (code `FOUNDER29`), a free tier (`check` plus 2 languages in `run`), 14-day refunds.

## Already done in Polar (organization "NullTwenty", id `16188b30-3a8a-4fdc-8282-d350ae6ec1bb`)

- A **License Key benefit**: prefix `SHOTFLEET`, never expires, up to 3 activations, customers can free an activation.
- The product **shotfleet**: one-time, 49 USD (and 49 EUR) with that benefit attached.
- The discount **FOUNDER29**: 20 USD / 20 EUR off, 100 redemptions, applies to shotfleet only.

Check them at https://polar.sh/dashboard/nulltwenty/products . Change the EUR price there if you prefer another number.

## 1. Finish the account review (only you can; Polar → Finance → Account Review)

1. **Verify your identity** (passport or ID card plus a selfie, through Stripe).
2. **Connect a payout account** (your bank; pick the Netherlands as the country).
3. **Set up checkout**, then **Submit for review**. Polar's review can take up to 14 days; nothing can be sold until it passes.
   Before you submit, ask the Belastingdienst or an accountant whether regular software sales need a KvK registration in your
   case. A merchant of record handles the sales VAT only, not your own tax or registration duties.

## 2. Make the checkout link

Polar → **Checkout Links → New link** → product shotfleet, add the discount `FOUNDER29` so the founder price applies
automatically. Copy the link.

## 3. Tell me the link

Paste the checkout link and I'll run:

```sh
POLAR_ORG_ID=16188b30-3a8a-4fdc-8282-d350ae6ec1bb packaging/go-live.sh <checkout link>
```

which sets the organization in the program, builds, signs, notarizes and uploads it to the site
(`curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh`), switches the site from the waitlist to "Buy
shotfleet" with install steps, deploys it, and prints the waitlist so you can send the email below.

## 4. Send the launch email (your account, your words; draft in marketing/launch-email.md)

Posting and emailing stay yours, as agreed.

The founder price ($29) is for the first 100 buyers, whoever buys first: `go-live.sh` puts the buy page live before the email
goes out, so the email does not promise the list an early window.

## 5. 30 days after the launch email: delete the waitlist (a promise on the privacy page)

```sh
site/signups.sh --purge-waitlist      # shows the count, asks you to type PURGE, then deletes every email: record
```

Contact-form messages (`msg:` records) are kept until answered and deleted on request: the visitor's own "delete my email"
button removes messages left with that reply address, and you can remove any other with
`cd site && npx wrangler kv key delete "<msg:...>" --binding WAITLIST --remote` (list them with `site/signups.sh`).
Put a reminder in your calendar the day you send the email.
