# Should the shotfleet website be localized?

Researched 2026-10-02. Short answer: **later, not now, never "never".** Ship nothing new this week except one data-collection line. Localize when a measured trigger fires, and then do Japanese and Korean first.

How the evidence was gathered: live fetches of ~60 sites (hreflang tags, `<html lang>`, locale paths, localized pricing/docs/blog pages, run with curl on 2026-10-02), plus web searches. "No data found" means exactly that. I could not use Ahrefs or Similarweb (both need sign-in), so there are **no keyword volumes** in this file, only autocomplete and content-presence signals.

---

## 1. Do developer-tool sites get localized in practice?

Yes, but almost only the big or well-funded ones, and rarely the whole site. The closest peers (screenshot tools) are English-only.

### Checked, localized (what I verified)

| Site | Languages | How deep | Source |
|---|---|---|---|
| RevenueCat | ja (at /jp), ko, ca | Home and /jp/pricing only; blog and docs stay English; /ko/pricing is 404 | https://www.revenuecat.com/ (hreflang), https://www.revenuecat.com/jp/pricing, https://www.revenuecat.com/docs/ja (404) |
| Adapty (subscription SDK for mobile apps) | de, es, fr, ja, ko, pl, pt-pt, ru, tr, uk, zh-hans | Home, pricing, blog **and docs** (docs/ja exists) | https://adapty.io/ (hreflang), https://adapty.io/ja/pricing/, https://adapty.io/docs/ja/ |
| AppTweak (ASO) | fr, ja, ko, zh-cn | Home, pricing, blog | https://www.apptweak.com/ja , /ja/pricing, /ja/aso-blog |
| Sensor Tower (app intelligence) | zh-CN, ja, ko | Home at least | https://sensortower.com/ (locales list in page data) |
| Cursor | de, es, fr, hi, ja, ko, pt-BR, zh, zh-Hant | Home, pricing and docs | https://cursor.com/ (hreflang), https://cursor.com/ja/docs |
| JetBrains | de, es, fr, ja, ko, pt-BR, ru, zh (own .cn site) | Whole site | https://www.jetbrains.com/ (hreflang) |
| Figma | de, es (many regions), fr, ja; ko and pt-br paths also resolve (hreflang list was truncated in my check) | Whole site | https://www.figma.com/ (hreflang) |
| Phrase / Crowdin (localization vendors) | de, es, fr, ja, zh (+ more for Crowdin) | Home | https://phrase.com , https://crowdin.com |
| Tuist (Apple build tool) | docs: ko, ja, ru, zh, es, pt (+ Cantonese and Traditional Chinese listed) | **Docs**; added because of a "strong presence in countries like South Korea and Japan", and only "as we see contributors willing to help maintain them" | https://community.tuist.dev/t/help-tuists-documentation-speak-japanese-and-korean/115 , https://docs.tuist.dev/en/contributors/translate (search snippet) |

### Checked, English only (no hreflang, `lang="en"`, locale paths 404 or fall back to English)

fastlane (site and docs), Maestro (site and docs), Bitrise, Sentry, Linear, Raycast, Expo (site and docs), Flutter docs, Codemagic, Polar, Lokalise, BrowserStack, Emerge Tools, Runway, Apphud, AppFollow, MobileAction, SplitMetrics, AppRadar, **and every screenshot tool I could load: AppScreens, Screenshots Pro, AppLaunchpad, ButterKit, LaunchShots, AppMockUp, ScreenshotWhale** (Previewed and Shotbot did not give a usable `lang` or loaded poorly; treat as unverified).

Caveats: this is the homepage HTML as served to curl. A JavaScript-only language switch would not show up. Vercel's `/ja` returned a page with `lang="en-US"`, so I counted it as not localized. Linear and Raycast gave no sign of localized marketing pages.

### What the pattern says

- **The two things shotfleet is closest to are both English-only.** AppScreens (80+ languages of screenshot translation) has 277 URLs in its sitemap and none with a locale prefix (https://appscreens.com/sitemap.xml). AppLaunchpad sells "AI bulk localization to 80+ languages" and has an English site. An English-only site next to a localization product is normal in this niche, not a red flag buyers punish (no evidence either way on punishment; see section 5).
- **Where localization exists, the language order is remarkably consistent.** Tally across the nine localizers in the table above (hreflang as I read it; Figma's list was truncated in my check): Japanese 9 of 9, French about 7, Chinese 7, Korean 6-7 (not Phrase or Crowdin), German 6, Spanish 6, Portuguese 3 (one of them pt-PT), Russian 2 (Adapty, JetBrains), Turkish 1 (Adapty).
- **Depth is shallow.** Typical is home + pricing (RevenueCat, AppTweak), sometimes blog. Docs only for the big ones (Adapty, Cursor, JetBrains) or a community effort (Tuist).
- **Mobile-adjacent tools pick ja and ko first.** RevenueCat's only non-Catalan localizations are Japanese and Korean.

---

## 2. English proficiency and where indie mobile developers are

### Proficiency (general population, not developers)

EF English Proficiency Index 2025 (Wikipedia mirror of the EF table; 123 countries, score bands: very high 600+, high 550-599, moderate 500-549, low 450-499, very low under 450):

| Country | EF EPI 2025 | Band |
|---|---|---|
| Netherlands | 624 | very high |
| Germany | 615 | very high |
| Portugal | 612 | very high |
| South Korea | 522 | moderate (rank 48) |
| Russia | 521 | moderate |
| Spain | 540 | moderate |
| France | 539 | moderate |
| Turkey | 488 | low |
| Brazil | 482 | low |
| China | 464 | low (rank 86) |
| Japan | 446 | very low (rank 96, lowest ever, 11th straight yearly fall) |
| Mexico | 440 | very low |

Sources: https://en.wikipedia.org/wiki/EF_English_Proficiency_Index , https://www.nippon.com/en/japan-data/h02620/ , https://www.ef.edu/epi/regions/asia/japan/ . A second aggregator (worldpopulationreview.com) shows different numbers (probably an older edition), so treat scores as approximate. Important caveat from the same sources: the index "suffers from self-selection bias" (people who chose to take EF's online test).

**What this does and does not tell us.** I found **no credible data on English proficiency of mobile developers specifically.** Developers read English documentation far more than the general population (Apple, Maestro, fastlane and Xcode docs are English-first), so the national numbers overstate the gap. The reliable inference is only relative: Japan and China have the largest gap, Germany and the Netherlands the smallest, so localization helps Germans least. One unverified anecdote: IT staff in Brazil score well above the national average (https://blog.nextideatech.com/latam-countries-with-highest-english-proficiency-for-software-developers/, low-quality source).

### Where the developers are

- **Stack Overflow Developer Survey 2025** (49,000+ responses, 177 countries): US 20.4%, Germany 8.6%, India 7.2%, Brazil 2.3%, China 0.7%, Japan 0.5%. Not mobile-specific, and heavily skewed to English-reading users (Japan and China are badly under-represented because their developers use local platforms). Sources: https://survey.stackoverflow.co/2025/developers and search summary of the country table.
- **New small App Store developers by region (Apple small-developer report, 2022):** Europe ~25%, China ~23%, US ~14%, other ~35% (Korea, India, Brazil are in "other"); a search summary of the Apple report also gave Japan ~4%, which I could not confirm on the Statista page. Source: https://www.statista.com/statistics/1311950/distribution-new-small-app-developers-apple-app-store-by-region (quoting the Apple small-developer report, https://www.apple.com/newsroom/2023/05/small-developers-on-the-app-store-grew-revenue-by-71-percent-from-2020-2022/). This is the only developer-by-country figure I found; it is old and coarse. I found nothing on iOS developers by country for 2024-2026, nor on Google Play developers by country.
- **Japan:** very active native-language developer culture. Qiita has about 1.5 million members and 3 million monthly users (https://note.com/unikoukokun/n/n7d55668f12c3?hl=en), Zenn 150,000+ (same). iOSDC Japan is the country's largest iOS conference (2,685 in-person attendees in 2024, 10th edition in 2025 with 110 speakers: https://iosdc.jp/2025/). Many Japanese Qiita posts exist on exactly shotfleet's competitor: "fastlane snapshot" multi-language screenshot automation (e.g. https://qiita.com/ytyng/items/71b4c2f3a9615d3ff8f6, https://qiita.com/tarappo/items/ba8aad5d9a9b2f9d3a86). So there is a Japanese audience that looks for this in Japanese, and writes about it.
- **China:** large and mostly separate ecosystem. The GitHub list https://github.com/1c7/chinese-independent-developer has 61,600 stars (fastlane itself has about 42,000). CSDN has many Chinese how-tos for fastlane snapshot multi-language screenshots (https://blog.csdn.net/gitblog_00072/article/details/136980945). Reach and payment caveats in section 5.
- **Korea:** active iOS communities (Swift Korea Facebook group fell from 50,000+ to about 10,000 members; a KakaoTalk "iOS Developers KR" room; "let us: Go!" conference), but I found no solid headcount (a "500,000 iOS developers" claim appeared in one search summary and I could not source it, so do not use it). Apple runs a Developer Academy in Korea (https://www.apple.com/newsroom/2026/06/app-store-ecosystem-reaches-1-point-4-trillion-usd-as-developers-thrive-globally/).
- **Brazil:** Cocoaheads Brasil exists; no headcount found. Non-gaming app spend is growing fast (+31%, RevenueCat: https://www.revenuecat.com/blog/growth/is-localization-the-next-great-growth-opportunity-for-subscription-apps), which concerns the buyers' apps, not the buyers' site language.
- **Germany, France, Spain, Turkey, Russia:** no developer-community numbers found. Germany is the third-largest respondent country in Stack Overflow's survey and has the best English; France/Spain are moderate. Russia is moot (see section 5, Polar does not sell to Russia).

**Do not confuse two different language questions.** The app languages shotfleet captures (ja, ar, ko, de...) are about the buyer's *users*. The website language is about the *buyer's own* reading comfort. A German developer localizing an app into Japanese is happy with an English site; a Japanese developer localizing into English may not be.

---

## 3. Conversion effect of localized pages for B2B / dev tools

**No credible data found.** I searched for A/B tests or case studies of translated landing pages for developer tools and found none; only generic SaaS CRO posts and vendor claims.

What does exist, and why it does not transfer:
- CSA Research "Can't Read, Won't Buy": 2014 survey of 3,002 consumers in 10 countries (Brazil, China, Egypt, France, Germany, Indonesia, Japan, Russia, Spain, Turkey) found 75% prefer to buy in their language and 60% rarely or never buy from English-only sites (https://csa-research.com/l/media/survey-of-3000-online-shoppers-across-10-countries-finds-that-60-rarely-or-never-buy-from-english-only-websites). The 2020 edition (8,709 consumers, 29 countries) reports 76% and 40% (https://www.tcworld.info/news/cant-read-wont-buy-499 and https://thepaypers.com/payments/news/non-anglophone-customers-avoid-buying-from-english-only-websites-report). These are **consumers shopping for goods, self-reported**, from a firm that sells localization research. Not developers, not a $49 CLI.
- Vendor blog stats such as "+128% downloads after localizing an app" (https://appscreens.com/blog/what-languages-should-i-localize-my-app-into) are about app store listings (the buyers' apps), not a developer-tool landing page.
- Indirect behavioural evidence only: companies that do measure (Adapty, RevenueCat, AppTweak, Sensor Tower, Cursor) keep investing in ja/ko/zh/de pages. That says it pays for them, at their traffic, with their sales motion. It does not size the effect for a solo, pre-launch, $49 product.

---

## 4. SEO angle

Keyword volumes: **not found** (no Ahrefs/Similarweb access). What I could measure:

- Google autocomplete (US, `client=firefox`, run 2026-10-02): "fastlane snapshot" produces the **same English suggestions in en, ja, zh-CN, ko, de, pt and ru** ("fastlane snapshot", "fastlane snapshot ios", "fastlane snapshot frameit"). Developers search by tool name in English everywhere.
- Native-language descriptive queries ("App Store スクリーンショット 自動", "App Store 截图 多语言", "App Store 스크린샷 자동화", "App Store Screenshots automatisieren", "скриншоты app store автоматизация", and es/fr/pt/tr equivalents) returned **no suggestions at all**, which suggests low volume. Autocomplete is not a volume measure and can be geo-biased, so this is a weak signal, but it points one way.
- English "app store screenshots automation" also returned no suggestions; "localize app store screenshots" did. The category is small even in English.
- Local-language content exists (Qiita, CSDN, a few Korean posts) for fastlane snapshot. That is how-to demand for the incumbent, not proof anyone searches for a paid alternative.
- Practical blocker: the site lives on `shotfleet.manulorenzop.workers.dev`. A fresh workers.dev subdomain has no authority, so localized pages would not rank in any language until there is a custom domain. Also, workers.dev is reported as DNS-poisoned or reset in mainland China (https://community.cloudflare.com/t/cloudflare-workers-suspected-of-being-blocked-in-china/382155, https://community.cloudflare.com/t/worker-is-not-available-in-china/497419), so a Chinese page on this domain would often be unreachable for the very audience it targets.
- Google's rules for localized pages are simple and cheap: separate URLs per language, reciprocal self-referencing `hreflang` with absolute URLs, an `x-default` (https://developers.google.com/search/docs/specialty/international/localized-versions). Machine translation published **without human review** is named as auto-generated spam; since 2025 Google says it judges translated content by value, "docs-only change, no change in behavior" (https://www.searchenginejournal.com/google-removes-robots-txt-guidance-for-blocking-auto-translated-pages/548870/). So a reviewed translation is fine, an unreviewed one is a risk.

Conclusion: localized pages would help a Japanese or Chinese **launch post** (a Zenn/Qiita/Juejin article needs a landing page to link to) far more than they would help organic search.

---

## 5. Credibility, cost and risk

### Credibility: the inconsistency is real but mild

- For: the pitch is "your app, every language". A visitor in Tokyo who lands on an English-only page can fairly think "this person doesn't practice it". The page already shows localized outputs (ja, ko, de, ar, zh in the screenshot gallery and OG image), which carries most of the proof.
- Against: the tool, README, flow format, terminal output, error messages and support are all English. The whole toolchain it plugs into (Maestro, fastlane, Xcode, Android Studio) is English. A localized page that leads to an English product is a *new* inconsistency, unless it says so up front ("the site is in Japanese; the tool, docs and support are in English"). Every competitor in the screenshot niche is English-only (section 1).
- Net: not a conversion blocker on today's evidence; a nice-to-have that matters most in Japan and China.

### Cost and maintenance for a solo founder

- Size: `index.html` is ~900 visible words plus a handful of form/JS strings; privacy and terms are another ~630 words. Per language the first translation is cheap (LLM draft in minutes); the cost is review and drift.
- **Every copy change multiplies by N**, and this site has a claims register (`tests/claims.json`, 85 KB, each claim tied to exact English `where_text` in `site/public/index.html`, with status like "partial"). Honest-copy discipline means each translated sentence is a claim that can drift from the audited English. Rule: only translate claims whose register status is proven; mirror the English structure sentence for sentence; never add claims in translation; run the claims check against the English source of truth and add a test that every key exists in every locale.
- Translation quality is the real risk. A wrong or odd Japanese sentence on a trust-sensitive pitch ("checks every screenshot") hurts more than English. Use a native reviewer for wave 1 (a paid reviewer or a developer from the waitlist). I have no price data for this; get a quote.
- **Legal pages stay English.** Terms and privacy are the binding texts; machine translations of legal text create ambiguity and, for privacy, a duty to keep them equal. Link from the localized page: "Terms and privacy are in English and are the version that applies." I did not check consumer-law specifics per country; EU/Japan consumer rules about language of terms are an open question to settle with whoever reviews the legal pages before wave 2 in the EU.
- **Merchant of record (Polar):** Polar is seller of record and the buyer agreement is Delaware-law English (https://polar.sh/legal/checkout-buyer-terms). Polar localizes the checkout page to en, nl, es, fr, sv, de, hu, it, pt-BR, pt-PT, **ko, ja**, tr, pl (https://polar.sh/docs/features/checkout/localization), chosen by browser or `?locale=`. During beta, error messages and **receipts/transactional emails stay English** and there is no language switch on the page. **Chinese and Russian are not supported**, and Polar does not take payments from Russia (https://polar.sh/docs/merchant-of-record/supported-countries). Implication: a ja/ko/de/fr/es/pt page can pass `?locale=` to the checkout and stay coherent until the receipt; zh pages end in an English checkout; ru pages are pointless.
- **Support:** Polar expects the merchant to answer customer threads within 48 hours (https://polar.sh/docs/merchant-of-record/account-reviews). Support in every language is a promise; say "support is in English" on the localized pages and do not offer anything else.
- Analytics cost is nil: the signup record already stores `country`, and `/api/hit` already counts page views by day, source and first three letters of the browser language.

---

## 6. Recommendation

**Verdict: LATER, gated by data. Do not translate now.** Reasons in one paragraph: no traffic yet to test on; no evidence that language is the limiting factor for English-reading $49 CLI buyers; competitors in the exact niche are English-only; the product, docs and support are English; the domain is a workers.dev subdomain with no SEO authority; and each language multiplies claim-accuracy and review work for a solo founder. The upside is real but concentrated: Japan, Korea and China, and only if the audience actually shows up.

### Do now (about 30 minutes, no new surface)

1. Read the existing data first: `./signups.sh --details` (country per signup) and `./signups.sh --visits` (language per visit). If the waitlist is small, this already answers whether wave 1 is needed.
2. Add the missing field: in `site/worker.js` `/api/signup`, store the browser language next to `country`, reusing the same slug logic as `/api/hit` (`lang: (request.headers.get("accept-language")||"").split(/[-,;]/)[0].slice(0,3) || null`). Do not store the full header. The privacy page already lists country; add "and your browser's language" to the signup sentence at privacy.html line 29. Accept-Language is a weak signal for developers (many run an English OS in Japan or China), so **read it together with country, never alone**.
3. Keep using the Japanese/Korean/Chinese screenshots in the gallery and OG image as the "we practice it" proof (already done).

### Trigger for wave 1 (any one)

- 15 or more waitlist signups, or 100+ visits, with `country` = JP or KR in a rolling 30 days, or any single non-English country above ~20% of signups once there are 50+ signups.
- A non-English launch post is planned (Zenn/Qiita, a Korean community) and wants a landing page to link to.
- Two or more unprompted requests in the contact form or email for another language.
- Also required before wave 1: a custom domain (hreflang and ranking mean little on workers.dev), and a native reviewer lined up.

### Ranked languages (for a developer landing page, buyer's reading language)

| # | Language | One-line justification |
|---|---|---|
| 1 | Japanese (ja) | Lowest English proficiency of any big market (EF 446, rank 96), biggest native-language iOS developer culture found (Qiita 1.5M, iOSDC), local how-tos for the exact competitor tool, in every peer's language list, Polar checkout supports it. |
| 2 | Korean (ko) | In every mobile-tool peer's list (RevenueCat, AppTweak, Sensor Tower, Adapty), strong iOS communities, Polar checkout supports it; English is moderate (522), so the lift is smaller than Japan and I have no headcount. |
| 3 | Portuguese, Brazil (pt-BR) | Low-band English (482), large and fast-growing app market, Polar checkout supports it; but price sensitivity at $49 and no developer headcount found, so it is a test, not a sure thing. |
| 4 | Simplified Chinese (zh-Hans) | Largest developer pool (23% of new small App Store developers, a 61,600-star indie list) and low English (464), but: Polar checkout is English only, workers.dev is blocked in China, and Chinese devs write for CSDN/Juejin. Only after a custom domain and a checked buying path. |
| 5 | German (de) | Best English among all candidates (EF 615): lowest conversion lift. Worth it for trust and for EU buyers who expect German privacy text, not for comprehension. |
| 6 | French (fr) | Moderate English (539), appears in 5 peer lists, little evidence of need. |
| 7 | Spanish (es) | Moderate English (540), same logic as French. |
| 8 | Turkish (tr) | Low-band English (488) but low purchasing power at $49; checkout supported. |
| - | Russian (ru) | Skip: Polar cannot take payments from Russia. |

### Phasing

- **Wave 0 (now):** the data steps above. No new pages.
- **Wave 1 (after trigger): ja and ko.** One template, two JSON files. They share a CJK font stack, the Polar `?locale=` path and the same banner mechanism, so the second language is nearly free. Japanese first if only one is affordable. Run for 60 days.
- **Wave 2 (only if wave 1 moves a number): pt-BR, then zh-Hans if the custom domain and buying path are verified, then de.** French, Spanish and Turkish only if signups from those countries show up on their own.

### What to measure to decide wave 2

All from data the site already has plus one field:
- Signups and visits by country and by language, before and after wave 1 (`signups.sh --details` and `--visits`).
- Wave 1 pages: visits, signup rate (signups / visits) per locale versus the English page for the same country mix; also bounce proxy: visits with no signup and no scroll (not tracked; skip unless it matters).
- Source tags: use distinct `utm_source` for each community post (already supported) so a Zenn post is not confused with organic.
- Decision rule (suggested, adjust to real traffic): extend to a language only if the localized page's signup rate is at least 1.5x the English rate for that country over at least 100 visits, **or** it brings 10+ signups a month that English did not. With traffic this small, expect to decide on signups and replies, not on statistics. State plainly in any write-up that the sample was small.
- Support load: count non-English emails in a month; if they are under a few, English-only support is fine.

### Implementation recommendation (fits the stack, CSP stays `script-src 'self'`)

- **Source of truth:** keep English `site/public/index.html` as the template, replace visible strings with `{{key}}` tokens (about 80-100 keys for ~900 words), `site/i18n/en.json`, `site/i18n/ja.json`, ... A `site/tools/build-i18n.mjs` of roughly 60-80 lines (Node, no dependencies; the repo already runs `.mjs` tests) writes `public/ja/index.html`, `public/ko/index.html`, plus `public/index.html` from `en.json`. Commit the generated files (static assets, no build step on deploy), same as today.
- **Per page:** `<html lang="ja">`, `<link rel="canonical">` to itself, and a reciprocal block on every page: `hreflang="en"`, `"ja"`, `"ko"`, `"x-default"` pointing to the English page, all absolute URLs, each page listing itself. Add `/sitemap.xml` (robots.txt currently has no Sitemap line).
- **No auto-redirect.** A small external `lang-banner.js` (CSP-safe) on the English page: if `navigator.language` starts with `ja`/`ko` and the visitor did not dismiss it, show one line in that language ("日本語版があります"). Dismissal in `localStorage` inside try/catch. A permanent footer switcher "English · 日本語 · 한국어" on every page. Google's guidance supports separate URLs plus a fallback and does not require redirects.
- **Form strings:** `forms.js` has about 10 English strings (errors, "Sending…"). Move them to `data-*` attributes on each form (defaults stay English in the JS); no inline script needed. Also send `locale: document.documentElement.lang` with the signup so the worker can store which page converted (allowlist it in the worker like `STACKS`).
- **Buy button:** append `?locale=ja` or `ko` to the Polar checkout link on those pages.
- **Terms and privacy:** not translated. Localized pages link to the English ones with a one-line note in the local language: "Terms and privacy: English version applies." Keep the localized footer text in the build JSON.
- **Gallery and OG:** keep the same images; add `og:locale` and a localized `og:title`/`og:description` per page. Reuse `og.jpg`.
- **Tests:** extend `site/worker.test.mjs` for the `lang` field, add a small build test that fails when a key is missing from any locale or when a token is left unreplaced, and point the claims registry at the English strings only (the build guarantees a 1:1 key mapping).
- **Effort (my estimate):** template extraction + build script + tests 3-4 h; forms.js/data attributes 1 h; banner + switcher + hreflang + sitemap 1-1.5 h; worker lang field + privacy sentence 0.5 h; per language: LLM draft + self-edit 1 h, native review (calendar time, not hours) a few days; ongoing: about 15 minutes per language per copy edit. First two languages end to end: roughly 1.5 working days plus reviewer wait. Adding a third is about 2 hours.

### Do-not-do list

- Do not redirect by IP or `Accept-Language`. Offer a banner and a switcher only.
- Do not publish unreviewed machine translation (quality risk and Google's spam policy on unreviewed auto-translation). One native check per language minimum.
- Do not translate terms or privacy, and do not claim the translated pages are legally authoritative.
- Do not promise non-English support, a non-English README, or "localized" tooling that is not. The site may say "site in Japanese; tool, docs and support in English".
- Do not add claims, numbers or comparisons in translation that the English page and `tests/claims.json` do not already support. No localized testimonials or "popular in Japan" claims without data.
- Do not translate into Russian (checkout excluded) or ship Chinese on the workers.dev domain (blocked or unreliable in China) or without a verified purchase path.
- Do not use country flags as language icons; use language names.
- Do not machine-translate the screenshots/OG for each locale; the multi-language gallery is the proof and is already language-neutral.
- Do not build a CMS, a framework, runtime i18n JS or a per-visitor language cookie; one template and a script is enough.
- Do not localize before there is a custom domain, a native reviewer and a trigger.
- Do not count Accept-Language alone as "demand": developers in Japan and China often browse in English. Combine with country.

---

## Sources (consolidated)

- Peer sites (fetched 2026-10-02): https://www.revenuecat.com/ , https://adapty.io/ , https://www.apptweak.com/ , https://sensortower.com/ , https://cursor.com/ , https://www.jetbrains.com/ , https://www.figma.com/ , https://phrase.com , https://crowdin.com , https://fastlane.tools , https://docs.fastlane.tools , https://maestro.dev , https://docs.maestro.dev , https://bitrise.io , https://sentry.io , https://linear.app , https://www.raycast.com , https://expo.dev , https://appscreens.com (+ /sitemap.xml), https://screenshots.pro , https://theapplaunchpad.com , https://butterkit.app , https://www.launchshots.com
- Tuist localization: https://community.tuist.dev/t/help-tuists-documentation-speak-japanese-and-korean/115 , https://docs.tuist.dev/en/contributors/translate
- English proficiency: https://en.wikipedia.org/wiki/EF_English_Proficiency_Index , https://www.nippon.com/en/japan-data/h02620/ , https://www.ef.edu/epi/regions/asia/japan/
- Developers by country: https://survey.stackoverflow.co/2025/developers , https://www.statista.com/statistics/1311950/distribution-new-small-app-developers-apple-app-store-by-region , https://www.apple.com/newsroom/2023/05/small-developers-on-the-app-store-grew-revenue-by-71-percent-from-2020-2022/
- Communities: https://note.com/unikoukokun/n/n7d55668f12c3?hl=en (Qiita/Zenn sizes), https://iosdc.jp/2025/ , https://github.com/1c7/chinese-independent-developer , https://qiita.com/ytyng/items/71b4c2f3a9615d3ff8f6 , https://blog.csdn.net/gitblog_00072/article/details/136980945
- Conversion/consumer language preference: https://csa-research.com/l/media/survey-of-3000-online-shoppers-across-10-countries-finds-that-60-rarely-or-never-buy-from-english-only-websites , https://www.tcworld.info/news/cant-read-wont-buy-499 , https://thepaypers.com/payments/news/non-anglophone-customers-avoid-buying-from-english-only-websites-report
- SEO: https://developers.google.com/search/docs/specialty/international/localized-versions , https://www.searchenginejournal.com/google-removes-robots-txt-guidance-for-blocking-auto-translated-pages/548870/ , https://community.cloudflare.com/t/cloudflare-workers-suspected-of-being-blocked-in-china/382155 , https://community.cloudflare.com/t/worker-is-not-available-in-china/497419
- Polar: https://polar.sh/docs/features/checkout/localization , https://polar.sh/docs/merchant-of-record/supported-countries , https://polar.sh/legal/checkout-buyer-terms , https://polar.sh/docs/merchant-of-record/account-reviews
- App-market context (about buyers' apps, not site language): https://www.revenuecat.com/blog/growth/is-localization-the-next-great-growth-opportunity-for-subscription-apps , https://appscreens.com/blog/what-languages-should-i-localize-my-app-into

## Gaps (what this file does not know)

No keyword volumes; no developer-specific English proficiency; no dev-tool localization A/B data; no iOS-developer headcount by country for 2024-2026; Korea and Brazil headcounts unsourced; Previewed and Shotbot not verified; Polar localization is in beta and may change; consumer-law rules on the language of terms per country not checked; the live waitlist KV was not queried (the country split of real signups is the single most useful missing input and costs nothing to read).
