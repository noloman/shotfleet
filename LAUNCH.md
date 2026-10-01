# Launch: your part (about 20 minutes, 30 with Gumroad)

Everything else is done and scripted. Signing and notarization use your existing Developer ID and the `KeysiNotary`
profile; the program is served from the shotfleet site (no public repos); `packaging/go-live.sh` does the rest.

## 1. Lemon Squeezy product

1. Sign in at https://app.lemonsqueezy.com (or sign up and finish the store's identity check; Lemon Squeezy is the
   merchant of record, so it handles VAT and sales tax).
2. **Products → New product**
   - Name: `shotfleet`
   - Description (paste):
     > Store screenshots in every language your app ships. Write one English Maestro flow; shotfleet runs it in every
     > language in parallel on iOS simulators and Android emulators, checks every screenshot against your app's own
     > strings (wrong language, copies, missing screens, App Store and Google Play size rules), and puts them in
     > fastlane's folders. For macOS (Apple silicon). Licence for one developer, up to 3 Macs, unlimited apps, a year
     > of updates. 14-day refunds.
   - Pricing: **Single payment, $79**.
   - **Generate license keys: on**. Activation limit **3**. License length **Unlimited** (updates are a year, the
     program keeps working).
   - Save and publish.
3. **Discounts → New discount**
   - Name and code: `FOUNDER`. Amount: **$30 off** (so $49). **Limit to 100 redemptions**. Applies to: shotfleet.
4. **Settings → Emails**: make sure the receipt includes the licence key (it does by default).
5. Open the product → **Share** → copy the checkout link, then add `?checkout[discount_code]=FOUNDER` to the end so
   the founder price is applied automatically.

## 2. Gumroad product (optional second store, ~10 minutes)

1. https://gumroad.com → **Products → New product** → Digital product, name `shotfleet`, price **$79**, paste the same
   description. No file to upload: buyers install from the site (put the install line in the product's content:
   `curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh`, then `shotfleet activate <your key>`).
2. In the product's settings, turn on **Generate a unique license key per sale**. Copy the **product ID** shown with
   the license key setting (the program checks keys against it).
3. **Discounts → New discount**: code `FOUNDER`, **$30 off**, limit **100** uses, for shotfleet.
4. Publish and copy the product link; add `/FOUNDER` at the end so the founder price is applied.
   (Each store's FOUNDER code has its own limit of 100, so up to 200 people can get the founder price.)

## 3. Tell me the links

Paste the Lemon Squeezy checkout link (and, if you made it, the Gumroad link and product ID) and I'll run
`packaging/go-live.sh <lemon link> [<gumroad link> <gumroad product id>]`, which:
- builds, signs, notarizes and uploads the program to the site (`curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh`),
- switches the site from the waitlist to "Buy shotfleet" with install steps,
- prints the waitlist so you can send the email below.

## 4. Send the launch email (your account, your words; draft in marketing/launch-email.md)

Posting and emailing stay yours, as agreed.
