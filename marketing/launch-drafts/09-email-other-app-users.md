# Email to users of my other apps: only if you have consent

**Status: don't send. As far as I can find, there is no list you're allowed to email about shotfleet.**

## What I checked (2026-10-06)

- **The repo:** no mailing list, subscriber export or newsletter for users of WOD Tracker, Stressi, Cairn, Keysi or AnywhereRoles. The only email list in the shotfleet project is the shotfleet **waitlist** (Cloudflare KV).
- **The waitlist's own promise:** the privacy page says I send one email when shotfleet is available, don't share or sell the list, don't add people to any other list, and delete it 30 days after the launch email (claims C080, C081). That one email is `marketing/launch-email.md`. The waitlist was last known at 0 signups (STATUS.md R8), and it can't be used for anything else.
- **App users:** App Store and Google Play don't give you your users' email addresses. Emails you might have from support requests or a sign-in were given for that purpose, not for marketing a different product.
- **The law, in short (not legal advice):** you're in the Netherlands, so the GDPR and the Dutch Telecommunicatiewet apply. Marketing email needs prior consent, with one exception for your own *existing customers* about *your own similar products*, and only if they could opt out when you collected the address. Users of a workout app or a keyboard-shortcut app aren't buying "similar products" to a developer tool, so that exception doesn't cover this.

## If you do have a list with consent

Send only if the people on it signed up for news about your apps or tools in general (for example a newsletter of yours that says "news about my apps"). Then:

**Subject options:**
- `I made a tool for developers: shotfleet`
- `Something different from me this time: a developer tool`

**Preview text:** `Store screenshots in every language, checked. Only interesting if you make apps.`

**Body:**

> Hi,
>
> You're getting this because you signed up for news about my apps. This one is different: it's a tool for people who make apps, so if that's not you, you can skip it.
>
> It's called shotfleet. It makes App Store and Google Play screenshots in every language your app has, from one flow you write once in English, and it checks every screenshot is really in the right language. I built it because my own store screenshots were wrong in ways I hadn't noticed: on one app, the captions were translated but the app under them was still in English.
>
> The check is free, and it works on screenshots you already have: https://shotfleet.com/?utm_source=app-newsletter
>
> It runs on Apple silicon Macs. Every language costs $29 for the first 100 buyers, then $49, one-time.
>
> If you know someone who makes apps in a few languages, feel free to forward this.
>
> Manu
>
> [Unsubscribe link, required, and your postal address if your mail service needs it]

**Best time:** a Tuesday or Wednesday morning in your readers' main time zone.

**Rule to respect:** one email, a working unsubscribe link, and don't email the shotfleet waitlist with it.
