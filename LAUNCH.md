# Launch: your part (about 20 minutes, then Polar's review)

Everything else is done and scripted. Signing and notarization use your Developer ID and the `KeysiNotary` profile;
the program is served from the shotfleet site (no public repos); `packaging/go-live.sh` does the rest.

Payments are on **Polar** (merchant of record: it charges and pays the VAT; a personal account is allowed, so no KvK is
needed to open it). Lemon Squeezy asks for a company number, so it is not used. Prices: **$49** once, **$29 for the
first 100** (code `FOUNDER29`), a free tier (`check` plus 2 languages in `run`), 14-day refunds.

## Already done in Polar (organization "NullTwenty", id `16188b30-3a8a-4fdc-8282-d350ae6ec1bb`)

- A **License Key benefit**: prefix `SHOTFLEET`, never expires, up to 3 activations, customers can free an activation.
- The product **shotfleet**: one-time, 49 EUR and 49 USD, with that benefit attached (price set 2026-10-02; before that it was Free).
- The discount **FOUNDER29** ("Founder price"): 20 USD / 20 EUR off, 100 redemptions, 1 per customer (created 2026-10-02).
- The launch checkout link (founder price preset, return to https://shotfleet.com/#price): `https://buy.polar.sh/polar_cl_8zeKCsIGKxzOSzqGWva0UdjhFmDg2vrt0NoBB3Coq7l`. Viewed 2026-10-02 as a Dutch buyer: 49 EUR, minus 20 Founder price, 29 EUR total, VAT included; Polar shows "payments are currently unavailable" until the review passes.
- Support email `hello@shotfleet.com` (forwarded by Cloudflare Email Routing) and website `https://shotfleet.com/`.
- Still to create: a **standard link** (the same product without a preset discount), to swap in after the 100th redemption. Until then the launch link would stop applying the discount, so check the redemption count (Polar, Discounts) as sales come in.

Check them at https://polar.sh/dashboard/nulltwenty/products .

## 1. Finish the account review (only you can; Polar → Finance → Account Review)

1. **Verify your identity** (passport or ID card plus a selfie, through Stripe).
2. **Connect a payout account** (your bank; pick the Netherlands as the country).
3. **Set up checkout**, then **Submit for review**. Polar's review can take up to 14 days; nothing can be sold until it passes.
   Before you submit, ask the Belastingdienst or an accountant whether regular software sales need a KvK registration in your
   case. A merchant of record handles the sales VAT only, not your own tax or registration duties.

## 2. The checkout link

The launch link above is ready: pass it to `go-live.sh`. After 100 redemptions create the standard link (Polar → Checkout Links → New link → product shotfleet, no preset discount) and switch the Buy buttons to it.

## 3. Check this Mac (once, before the rehearsal)

- **Domain:** `shotfleet.com` and `www.shotfleet.com` are already custom domains of the site Worker (`site/wrangler.toml`);
  nothing to buy or point.
- **Git:** `go-live.sh` ends with a plain `git push`. The branch you run it on needs an upstream, or the push fails
  AFTER the site is live. On `main` that is already true; on any other branch run `git push -u origin <branch>` once.
  The working tree must be clean and nothing staged (the build and the commits would include it).
- **Signing and notarization:** the Developer ID certificate is in the login keychain (`security find-identity -v -p
  codesigning` lists `Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)`), and the `KeysiNotary` notarytool
  profile still works: `xcrun notarytool history --keychain-profile KeysiNotary` lists past submissions (read only; it
  needs the network, which is why the rehearsal does not run it for you). If the profile is gone, recreate it with
  `xcrun notarytool store-credentials KeysiNotary`.
- **Cloudflare:** `cd site && npx wrangler whoami` shows the account that owns `shotfleet.com`.
- Tools: python3, swiftc, xcrun, codesign, node and npx on the PATH (the rehearsal checks these).

## 4. Rehearse (changes nothing; a few seconds, a few minutes with the claims check)

```sh
POLAR_ORG_ID=16188b30-3a8a-4fdc-8282-d350ae6ec1bb packaging/go-live.sh --dry-run <checkout link>
```

It copies the working tree to a temp folder and, there, runs the same `sed` on `shotfleet.py`, the same git commits and the
same page transform as the real run, then prints the diff, checks the page (checkout link in the nav, hero and price
card; no WAITLIST or SALE markers; no counter number; install line once), runs the claims check on the result, checks
this Mac (step 3's git and signing items) and lists what the real run would do. It never builds, notarizes, uploads,
deploys or pushes. It ends with `dry run clean`; any `FAIL` line means do not go on. Nothing in it needs the network.

## 5. Go live (the one-shot; tell me the link and I run it, or you do)

```sh
POLAR_ORG_ID=16188b30-3a8a-4fdc-8282-d350ae6ec1bb packaging/go-live.sh <checkout link>
```

In this order: sets the organization in `shotfleet.py` and commits it; `packaging/release.sh` (claims gate, build, sign,
notarize, copy to `site/public/download`, deploy: at this moment the waitlist page is still what visitors see, next to a
working `install.sh`); turns the page into "Buy shotfleet" with your checkout link; deploys; commits "Site: sale open"
and pushes; prints the waitlist emails. Deploys and the push cannot be undone by the script. If it stops halfway, do
not simply run it again: the second run's organization commit would fail with "nothing to commit" and stop. Look at the last line it printed, then run the
remaining steps by hand (`packaging/release.sh`, the page transform, `cd site && npx wrangler deploy`, commit, push);
the page transform is safe to repeat.

## 6. Smoke test the live site (read only, from a clean environment)

```sh
env -i sh tools/golive/smoke.sh https://shotfleet.com <checkout link>
```

Fetches `/`, `/install.sh`, `/download/VERSION`, the archive and its `.sha256`, `/robots.txt`, `/sitemap.xml` and the
other pages; checks the status codes, the checkout link (3 places), no waitlist form, no counter number, the CSP header
and the http to https redirect; verifies the archive against its checksum; runs `install.sh`'s own checksum lines
(stopped before it extracts anything, so nothing is installed on your PATH) and, on an Apple silicon Mac, unpacks the
program in a temp folder and compares `--version` with `/download/VERSION`. Any `FAIL` means: fix it before the email.
The script itself is tested offline against a fake server (`tests/test_golive.py`).

Still by hand after the smoke test: open the page in a browser and click the buy button (the link must open Polar's
checkout at $29), then do one real install on a clean Mac account (`curl -fsSL https://shotfleet.com/install.sh | sh`,
`shotfleet doctor`) and one real test purchase of your own with a refund.

## 7. Send the launch email (your account, your words; draft in marketing/launch-email.md)

Posting and emailing stay yours, as agreed.

The founder price ($29) is for the first 100 buyers, whoever buys first: `go-live.sh` puts the buy page live before the email
goes out, so the email does not promise the list an early window.

## 8. 30 days after the launch email: delete the waitlist (a promise on the privacy page)

```sh
site/signups.sh --purge-waitlist      # shows the count, asks you to type PURGE, then deletes every email: record
```

Contact-form messages (`msg:` records) are kept until answered and deleted on request: the visitor's own "delete my email"
button removes messages left with that reply address, and you can remove any other with
`cd site && npx wrangler kv key delete "<msg:...>" --binding WAITLIST --remote` (list them with `site/signups.sh`).
Put a reminder in your calendar the day you send the email.

## Open items (not done, because they need something only you can give)

- **A live "N of 100 left" counter is not built.** The buy page says "First 100 buyers: $29" as plain text and `go-live.sh`
  keeps it; it shows no number, because nothing true feeds one yet (the smoke test and the tests fail the page if a counter
  number appears). To make it live: create a Polar **organization access token** (Polar dashboard, organization settings,
  read access to discounts) and put it into the site Worker as a secret with `cd site && npx wrangler secret put
  POLAR_TOKEN`; then the Worker can read the redemptions of `FOUNDER29` and the page can show the real count. I have not
  verified which Polar endpoint reports redemptions, so that is the first thing to check against Polar's API reference.
  Until then do not write "only N left" anywhere (MARKETING.md rule).
- The notarization profile and Cloudflare login can only be checked on your Mac (step 3).
