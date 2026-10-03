# GA4 setup for shotfleet.com

What to do in Google Analytics once the property exists, so the site and the privacy page stay true. The code side is `site/public/ga.js`; nothing loads from Google until a visitor presses Accept analytics, and nothing at all while `GA_ID` is the placeholder.

## 1. The Measurement ID in the code (done: `G-6NY43DB3F4`)

The property is created and the ID is already in `ga.js`; the steps below are how to change it. Setting `GA_ID` back to `G-XXXXXXXXXX` switches everything off again (no banner, nothing from Google).

1. GA4 > Admin > Data streams > the web stream > copy the Measurement ID (`G-` and 10 characters).
2. In `site/public/ga.js` replace the single line `const GA_ID = "G-XXXXXXXXXX";`. Nothing else in the repo contains the ID (a test checks this).
3. `python3 -m unittest discover -s tests`, then deploy. Until the commit with the real ID is deployed, the live site has no banner and loads nothing from Google.

## 2. Property and data stream

- Create a property (GA4, not Universal), reporting time zone and currency as you like.
- Data stream: Web, URL `https://shotfleet.com`, stream name `shotfleet.com`. Only one stream; do not add `shotfleet.manulorenzop.workers.dev`.
- Do not link Google Ads, Search Ads 360, BigQuery or any other product, and do not accept the optional "benchmarking" and "technical support" sharing settings you do not need: the privacy page says Google signals and the advertising features are off and Google acts only as processor.

## 3. Admin settings the privacy page depends on

Admin > Data collection and modification > Data collection:
- Google signals data collection: OFF (leave it off; `ga.js` also sets `allow_google_signals: false`).
- Granular location and device data collection: leave at the default or turn off for the regions you do not need; not required by the page.
- Advanced settings to allow for ads personalization: off for all regions.

Admin > Data collection and modification > Data retention:
- Event data retention: 14 months (the longest standard GA4 offers; the privacy page says "up to 14 months").
- Reset user data on new activity: off (so the 14 months run from collection, not from the visitor's last visit).

Admin > Data collection and modification > Data deletion requests: nothing to set; this is where a deletion request for a specific visitor would go.

Admin > Product links: nothing linked.

Admin > Data settings > Data sharing settings: untick every box you can (Google products and services, modeling contributions, technical support, account specialists). The privacy page does not promise this explicitly, but "no advertising use" is easier to defend with all sharing off.

## 4. Data stream settings (Admin > Data streams > the stream > Enhanced measurement)

`ga.js` sends `page_view` itself (GA4 sends it on config). Everything else is chosen per feature:

| Feature | Setting | Why |
|---|---|---|
| Page views | on (always) | the baseline |
| Scrolls | off | `pricing_view` and `runs_view` already say which sections were reached |
| Outbound clicks | on | the checkout link goes to polar.sh; it shows how many left for checkout |
| Site search | off | there is no search |
| Video engagement | off | no embedded video |
| File downloads | off | nothing is downloaded from the site through a link; installs use `curl` |
| Form interactions | off | it would register the waitlist and contact forms as events and risks noise; `signup` is sent explicitly |
| Page changes based on browser history events | off | the site is static pages |

Configure tag settings (same screen) > Define internal traffic: add a rule for your own IP address in the GA admin only. Do not write your IP into this repository or `ga.js`. Then Admin > Data filters > Internal traffic: switch the filter from Testing to Active after you have confirmed it works.

Configure tag settings > List unwanted referrals: add `polar.sh` (the checkout hands visitors back to the site and would otherwise start a new session from the referral).

## 5. Events the site sends

All sent only after consent, from `site/public/ga.js`:

| Event | When | Parameters |
|---|---|---|
| `page_view` | on load (automatic) | |
| `cta_click` | a click on a `.btn` link or button (same selector as the first-party counter in `analytics.js`; the contact and delete-my-email form buttons are excluded) | `cta_text`: the first 40 characters of the label |
| `pricing_view` | the `#price` section is 25 percent visible, once per page view | |
| `runs_view` | the `#run` section is 25 percent visible, once per page view | |
| `signup` | the waitlist signup succeeded: `forms.js` dispatches the DOM event `shotfleet:signup`, `ga.js` listens | none: no email, no stack answer |

Events appear in Admin > Data display > Events within a day (Realtime within seconds). Add a custom definition for `cta_text`: Admin > Data display > Custom definitions > Create custom dimension: Scope Event, name `CTA text`, event parameter `cta_text`.

## 6. Key events (formerly "conversions")

Admin > Data display > Key events > New key event:
- `cta_click` (marked: this is the funnel step of intent)
- `pricing_view` (marked)
- `signup` (marked: the waitlist signup, the conversion while the product is not yet on sale)
- Leave `runs_view` unmarked: it is an engagement signal, not a goal.

Events show in the list only after they have arrived once. Test them first (section 7), then mark them.

When the site goes live with the Polar checkout link instead of the waitlist, `signup` stops firing (the form is gone). The real purchase happens on polar.sh, outside this site, so GA cannot see it; `cta_click` on the Buy button and Outbound clicks are the nearest signal.

## 7. Test it, with consent in mind

1. Deploy with the real ID. In Chrome with a fresh profile or a private window open https://shotfleet.com: the banner shows, DevTools > Network shows no request to a google host and Application > Cookies shows no `_ga`.
2. Press Decline: still nothing; reload: no banner and nothing from Google.
3. Footer > Analytics settings > Accept analytics: now `gtag/js?id=G-...` loads, `g/collect` requests go to `*.google-analytics.com`, cookies `_ga` and `_ga_<id>` appear. GA4 > Admin > DebugView or Reports > Realtime shows you.
4. Footer > Analytics settings > Decline: the two cookies are deleted and further events stop.
5. If a request is blocked, the browser console names the CSP directive; the allowed hosts are exactly the ones in `site/public/_headers`. Do not widen them to fix a blocked region: Google serves collection from `region1.google-analytics.com` and `region1.analytics.google.com`, which the existing wildcards cover.

## 8. Keep the claims true

- Privacy page says: cookies `_ga` and `_ga_<id>` lasting up to 13 months (set in `ga.js` as `cookie_expires`), Google signals and ad features off, event data kept up to 14 months. If you change any of these in GA or in `ga.js`, change `site/public/privacy.html` and `tests/claims.json` (C076, C118) in the same commit; `tests/test_consent.py` pins the numbers.
- Today the Cloudflare dashboard (Web Analytics, Bot Fight Mode) could still add a beacon or cookie without a deploy; keep those off, as the register notes under C076.
