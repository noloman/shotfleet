# Launch: your part (about 30 minutes in Gumroad, then Gumroad's first-payout review)

> **Status, 2026-10-05:** go-live ran 2026-10-05 (5fa4f7c, 5bbec86). Sections 4 to 6 are the record and the template for the next release. Section 8 (purge the waitlist 30 days after the launch email) is still live and is a promise on the privacy page.

> **2026-10-02: Polar was dropped.** Polar pays out through Stripe, and Stripe will ask a Dutch resident for a KvK number.
> The sale moves to **Gumroad**, which you already use for Keysi (Individual account, EUR bank payout, no KvK entered).
> Everything about Polar below this note is gone; the Polar organization, product, discount and checkout links are no
> longer used and can be deleted or left. Why Gumroad, what it costs and what is still unverified:
> `research/gumroad-setup.md`. Its last section is the click-by-click checklist for the Gumroad product.

Everything else is done and scripted. Signing and notarization use your Developer ID and the `KeysiNotary` profile;
the program is served from the shotfleet site (no public source repo; the empty public repo `noloman/shotfleet-releases` is kept for a later Action, tap and fastlane plugin, see DISTRIBUTION.md); `packaging/go-live.sh` does the rest.

Payments are on **Gumroad** (merchant of record since 2025-01-01: it charges and pays the VAT and sales tax worldwide; an
Individual account needs no business registration). Lemon Squeezy and Polar are not used: both end in a Stripe check that
asks for a KvK. Prices: **$49** once, **$29 for the first 100** (code `FOUNDER29`, applied automatically),
a free tier (`check` plus 2 languages in `run`), 14-day refunds. Gumroad cannot show a VAT-inclusive price, so the page says prices
are before VAT where it applies. Fees: 10% + $0.50 plus card processing 2.9% + $0.30, so about $24.46 net at $29 and
$41.88 at $49.

## 1. Create the product in Gumroad (only you can: sign-in, identity, bank, terms)

Follow section 6 of `research/gumroad-setup.md` (a Claude-in-Chrome session can do the clicks; it stops at every step
marked MANU ONLY). In short: one product `shotfleet` at $49, **License key block inserted on the Content page** (the step
that was missed on Keysi: without it buyers get no key), a 14-day refund policy on the product, the code `FOUNDER29`
($20 off, limit 100 uses, applied automatically), no file upload (the installer is public; Gumroad sells only the key).
You hand back two things: the **product URL** (`https://<account>.gumroad.com/l/<permalink>`) and the **product ID**
(22 characters ending in `==`, shown in the License key block while you edit).

Before you publish the product:

1. Check the payout status on Settings, Payments. If Stripe asks for a KvK or company document anywhere, stop and tell me.
   The honest unknown is the check Stripe runs after the first sales; Keysi has not reached it yet (see the research file).
2. Ask the Belastingdienst or an accountant whether regular software sales need a KvK registration for income tax. A
   merchant of record handles the sales VAT only, not your own tax or registration duties. This is separate from Stripe.

## 2. The checkout link

The product URL is the link on every Buy button (`go-live.sh` puts it in the page). The founder price needs no second
link: the code is applied automatically for the first 100 buyers, and the 101st pays $49 by itself. Check the code's use
count in Gumroad (Checkout, Discounts) as sales come in, and read the research file's two open points (what the page shows
after the 100th use; whether a test purchase uses one).

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

## 4. Check the live product, then rehearse (read only)

```sh
tools/golive/storefront.sh <product URL> <product ID> 49
packaging/go-live.sh --dry-run <product URL> <product ID>
```

`storefront.sh` reads the Gumroad product page and fails on the three silent ways to lose a sale: the product is
unpublished, licence keys are off, no refund policy (or one that is not 14 days); it also checks the product ID is on the
page, the list price, and that `licenses/verify` answers (a made-up key is rejected; nothing is counted). It needs the
network and is tested offline against a fake page (`tests/test_golive.py`).

The dry run copies the working tree to a temp folder and, there, runs the same `sed` on `shotfleet.py` (it sets
`GUMROAD_PRODUCT_ID`), the same git commit and the same page transform as the real run, then prints the diff, checks the
page (product link in the nav, hero and price card; no WAITLIST or SALE markers; no counter number; install line once),
runs the claims check on the result, checks this Mac (step 3's git and signing items) and lists what the real run would do.
It never builds, notarizes, uploads, deploys or pushes. It ends with `dry run clean`; any `FAIL` line means do not go on.
A product URL that is not `gumroad.com/l/<permalink>` or an ID that is not 22 characters and `==` is a warning, not a stop.

## 5. Go live (the one-shot; tell me the URL and ID and I run it, or you do)

```sh
packaging/go-live.sh <product URL> <product ID>
```

In this order: sets the product ID in `shotfleet.py` and commits it; `packaging/release.sh` (claims gate, build, sign,
notarize, copy to `site/public/download`, deploy: at this moment the waitlist page is still what visitors see, next to a
working `install.sh`); turns the page into "Buy shotfleet" with your product URL; deploys; commits "Site: sale open"
and pushes; prints the waitlist emails. Deploys and the push cannot be undone by the script. If it stops halfway, look at
the last line it printed, then run the remaining steps by hand (`packaging/release.sh`, the page transform,
`cd site && npx wrangler deploy`, commit, push); the page transform is safe to repeat, and the product-ID commit is skipped
when the ID is already there.

## 6. Smoke test the live site (read only, from a clean environment)

```sh
env -i sh tools/golive/smoke.sh https://shotfleet.com <product URL>
```

Fetches `/`, `/install.sh`, `/download/VERSION`, the archive and its `.sha256`, `/robots.txt`, `/sitemap.xml` and the
other pages; checks the status codes, the product link (3 places), no waitlist form, no counter number, the CSP header
and the http to https redirect; verifies the archive against its checksum; runs `install.sh`'s own checksum lines
(stopped before it extracts anything, so nothing is installed on your PATH) and, on an Apple silicon Mac, unpacks the
program in a temp folder and compares `--version` with `/download/VERSION`. Any `FAIL` means: fix it before the email.
The script itself is tested offline against a fake server (`tests/test_golive.py`).

Still by hand after the smoke test: open the page in a browser and click the buy button (the link must open Gumroad's
product page showing $49 crossed out and $29), then do one real install on a clean Mac account
(`curl -fsSL https://shotfleet.com/install.sh | sh`, `shotfleet doctor`) and one test purchase: Gumroad's own "Test card"
checkout while logged in, or a single-use 100%-off code (never your own card; Gumroad can suspend the account for that).
Activate the key it issues, activate again (counts nothing). A 100%-off sale cannot be refunded (no refund action on a $0
sale): disable its key under Manage license keys instead and check the next weekly check refuses it (`the key was disabled`).
Only a paid sale by another person tests the refund itself (`docs/refund-runbook.md`).

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

## 9. Support: moving a key to another Mac

A key has 3 activations; Gumroad has no per-Mac record and the program cannot give one back (that needs your Gumroad
token). When a buyer writes for a fourth Mac: Gumroad, Sales, the sale, License key section, Uses row, minus or Reset. That
is the whole job. The terms say exactly this.

## Open items (not done, because they need something only you can give)

- **A live "N of 100 left" counter is not built.** The buy page says "First 100 buyers: $29" as plain text and `go-live.sh`
  keeps it; it shows no number, because nothing true feeds one (the smoke test and the tests fail the page if a counter
  number appears). Gumroad shows a discount code's use count in your dashboard; reading it by API would need your Gumroad token
  (unverified), which must not go into the site, so no live counter is planned. Until then do not write "only N left" anywhere
  (MARKETING.md rule).
- The 14-day refund option in Gumroad's editor, the page after 100 uses, what Stripe asks after the first sales and the card-fee
  base when VAT is added are unverified: the list is at the end of `research/gumroad-setup.md`.
- The notarization profile and Cloudflare login can only be checked on your Mac (step 3).
