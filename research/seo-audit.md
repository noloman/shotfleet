# SEO and AI-search audit of shotfleet.com

Audited 2026-10-02. Live site fetched with curl (headers, rendered HTML, redirects, crawler user agents), compared byte for byte with `site/public/` (index, alternatives, robots, sitemap, llms.txt are identical to the repo). Read: README.md, MARKETING.md, `research/marketing-research.md` section 3, `marketing/articles/` (01 to 03 drafts, 04-ideas.md), `site/public/*`, `site/wrangler.toml`, `site/worker.js`, `packaging/go-live.sh`.

## How to read the numbers in this file

- **Verified** = I fetched it or ran it today and the output is above or in the table.
- **Unverified** = a statement about search volume, ranking chance, how Google or an AI engine treats something, or a limit I know from memory. No SEO connector (Ahrefs, Semrush, Search Console) is authorized, so there is **no keyword volume, difficulty, impression or ranking number anywhere in this file**. Where a "chance" or "intent" is quoted from research/marketing-research.md 3.3 it is that file's own reading of the search results, not something I re-checked.
- What I tried and could not use: PageSpeed Insights API (HTTP 429, quota exhausted, so there are **no Lighthouse or Core Web Vitals numbers**); an LCP reading in Chrome (my tab was in the background and did not paint, entry list came back empty); `site:shotfleet.com` in the web search tool (returned unrelated pages; that tool is not Google, so it says nothing about whether the site is indexed). Search Console is the only real source for "is it indexed".

## Summary of the state of the site

The technical base is better than most launch sites: static HTML that is complete without JavaScript, system fonts only, brotli, a real 404 status, http to https 301, a correct sitemap and canonical on the two main pages, a 1200x630 og image on an absolute shotfleet.com URL, an `llms.txt`, and no third-party scripts. The gaps are on-page vocabulary and structure, not plumbing:

1. `www.shotfleet.com` returns 200 with the same content (duplicate host).
2. The home page never says "App Store" or "Google Play" (0 occurrences in visible text), says "localized" once, and has no one-sentence definition of what shotfleet is.
3. `/alternatives` has a 26 character title and no og/twitter tags; `/terms` and `/privacy` have no canonical.
4. No structured data anywhere.
5. No `/guides` section, no internal links from the home page to the articles that are meant to bring the traffic, and the three finished drafts use slugs that differ from the structure proposed here.
6. No `Disallow: /api/`, no `lastmod`, no HSTS.

Everything below has an exact snippet.

---

## 1. Page-by-page facts (verified)

| Page | Status | Title (chars) | Description (chars) | Canonical | og / twitter | H1 |
|---|---|---|---|---|---|---|
| `/` | 200 | "shotfleet · localized store screenshots" (39) | 199 chars, too long, cut off in results (Google's cut is about 155 to 160 characters desktop, less on mobile: unverified exact) | `https://shotfleet.com/` | og:title, description, image (absolute, 1200x630, alt), url, type; `twitter:card=summary_large_image`. Missing: `og:site_name`, `og:locale`, twitter title/image (fall back to og) | "Store screenshots in every language your app ships." |
| `/alternatives` | 200 | "shotfleet and alternatives" (26) | 103 | `https://shotfleet.com/alternatives` | **none** | "shotfleet and the other tools" |
| `/terms` | 200 | "Licence and refunds · shotfleet" (31) | 64 | **none** | none | "What you get when you buy shotfleet." |
| `/privacy` | 200 | "Privacy · shotfleet" (19) | 72 | **none** | none | "What I keep, and how to delete it." |
| 404 | 404 | "Page not found · shotfleet" | none | none | none (has `noindex`) | "There's no page here." |

Titles and descriptions are all unique. Only the home page's description is a length problem. The alternatives title wastes the only page that matches a comparison intent.

Image check: `og.jpg` is a real 1200x630 JPEG, 121 KB, shows the headline and three phones, served `image/jpeg` from `https://shotfleet.com/og.jpg`. Good. It is served `cache-control: max-age=0, must-revalidate` (fine for scrapers).

Heading structure (verified from the HTML):
- `/`: one h1, then h2s in order: "Run it once. Read the result." / "The first run found a button nobody could reach." / "Your flow says Next. Each language gets its own word." / three h2s in the bento ("One flow, not eighteen." / "iOS, Android and the other sizes." / "Made to work with the rest.") / "The same screen, in the languages of my other apps." / "Not for you if…" / "Early access", with h3 "Licence" and "Free at launch" under it. No skipped levels. The bento h2s are really third-level points; harmless. The headings are brand voice, not descriptive: none contains "App Store", "Google Play", "Maestro" or "fastlane". Do not rewrite them all; fix the h1/sub and add the definition (section 7, fix 3).
- `/alternatives`: h1, h2 Feature comparison / What each tool does / When you should NOT buy shotfleet / The story, with h3 per tool. Clean.
- `/terms`, `/privacy`: h1 then h2s. Clean.

Vocabulary count in visible text of the home page (comments and scripts stripped): 896 words; "App Store" 0, "Google Play" 0, "Maestro" 3, "localized" 1, "fastlane" 6. Alternatives page: "App Store" 1, "Google Play" 0.

## 2. Canonical host, www, http, trailing slash, 404 (verified with curl)

| Request | Result |
|---|---|
| `http://shotfleet.com/` | 301 to `https://shotfleet.com/` |
| `http://www.shotfleet.com/` | 301 to `https://www.shotfleet.com/` (then 200, see next row) |
| `https://www.shotfleet.com/` | **200, identical body and ETag** to the bare domain; canonical tag inside points at the bare domain |
| `https://www.shotfleet.com/robots.txt` | 200, same file (its `Sitemap:` line names the bare domain) |
| `/alternatives.html`, `/index.html`, `/alternatives/` | 307 to `/alternatives`, `/`, `/alternatives` |
| `/nonexistent`, `/llms-full.txt`, `/favicon.ico`, `/apple-touch-icon.png`, `/.well-known/security.txt` | **404 status**, custom page, `noindex` meta. No soft-404. |
| `/?utm_source=x` | same page; the canonical (no query) absorbs it |

Findings:
- The canonical tag already covers the duplicate, so this is not an emergency, but two hostnames serving 200 split links and crawl budget and confuse analytics. A 301 is the clean fix.
- The 307 (temporary) on `/alternatives.html` is how Workers static assets handle `.html`; the canonical covers it. Do not link to `.html` URLs anywhere.
- `/favicon.ico` is a 404 on every crawler request. The `<link rel="icon" href="/favicon.svg">` is honoured by browsers, but Google's favicon crawler and some bots still ask for `/favicon.ico`. Cheap fix: add a 48x48 `favicon.ico` and `apple-touch-icon.png` (180x180) to `site/public/`.
- No `Strict-Transport-Security` header is sent (verified: absent in the response headers).

### Fix: www to bare, one Cloudflare Redirect Rule (nothing to change in the Worker)

`run_worker_first = ["/api/*"]` and static assets mean no Worker code runs for pages, and `_redirects` (Workers assets) matches on path only, not on host, so it cannot do this. A Cloudflare **Redirect Rule** runs at the edge before the Worker. Keep the `www.shotfleet.com` custom domain in `wrangler.toml` (it provides the DNS record and the certificate the redirect needs).

Dashboard: shotfleet.com zone, Rules, Redirect Rules, Create rule, "Custom filter expression":

```
When:   (http.host eq "www.shotfleet.com")
Then:   Dynamic redirect
        URL:    concat("https://shotfleet.com", http.request.uri.path)
        Status: 301
        Preserve query string: on
```

Same thing through the API (do not run before reading: `PUT` on an entrypoint **replaces all rules in that phase**; the zone currently has none that I can see, but check first with a `GET`):

```bash
curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/rulesets/phases/http_request_dynamic_redirect/entrypoint" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  --data '{"rules":[{"action":"redirect","description":"www to apex","expression":"http.host eq \"www.shotfleet.com\"","action_parameters":{"from_value":{"status_code":301,"preserve_query_string":true,"target_url":{"expression":"concat(\"https://shotfleet.com\", http.request.uri.path)"}}}}]}'
```

Verify afterwards (expected: `301` and `location: https://shotfleet.com/alternatives?x=1`):

```bash
curl -sI "https://www.shotfleet.com/alternatives?x=1" | grep -iE '^(HTTP|location)'
curl -sI "http://www.shotfleet.com/" | grep -iE '^(HTTP|location)'   # 301 to https://www..., then the rule: two hops, fine
```

Update the comment in `site/wrangler.toml` on the www route to "redirected to the bare domain by a Cloudflare Redirect Rule". The two-hop http://www case is acceptable; enabling "Always Use HTTPS" is already in effect (the http to https 301 is observed).

HSTS: SSL/TLS, Edge Certificates, HSTS. Start with max-age 6 months, no `includeSubDomains` (the zone has email routing records visible in the owner's dashboard, and other subdomains may exist), no preload. It is a security and trust item, not a ranking item (Google has said HTTPS is a minor signal: unverified current weight).

## 3. Structured data

Current: none (`grep ld+json` returns 0 on every page).

### CSP check (verified in Chrome)

`site/public/_headers` sets `script-src 'self'` with no `'unsafe-inline'`. A `<script type="application/ld+json">` is a **data block**, not executed, so script-src does not apply to it. I confirmed this in Claude in Chrome (my own tab, closed afterwards) against a local server that sends the exact CSP string from `_headers`: an inline `<script>document.title=...</script>` was blocked (title unchanged), a same-origin `<script src>` ran, and the page's ld+json block was present and `JSON.parse` of its text succeeded. So no CSP change is needed, and do not add `'unsafe-inline'` or a hash for it.

### What is true for this page, and what is not

- True and useful: `SoftwareApplication` with `operatingSystem` macOS, requirements, three offers (free tier, $29 launch price, $49 standard price), author.
- **Do not add** `aggregateRating` or `review` (none exist; Google's software-app rich result needs one of them, so expect **no rich result** from this block: unverified, it is for machine readability and entity clarity). Do not add `softwareVersion` (no released version yet) or `downloadUrl` (nothing to download until go-live).
- **No `FAQPage` on the home page or `/alternatives`**: neither has real question and answer pairs ("When you should NOT buy" is a list, not Q&A). FAQ rich results are also restricted to a narrow set of sites on Google as far as I know (unverified today). Add `FAQPage` to an article only if that article visibly has questions and answers, and mark it as data for AI engines, not as a rich-result play.
- No `HowTo` (Google dropped that rich result: unverified recollection) and no `Review`.
- `eligibleQuantity` is a per-order quantity, not a "first 100 buyers" cap, so the cap is stated in the offer `description` only.

### Ready JSON-LD for `index.html` `<head>` (fits the WAITLIST/SALE toggle in `packaging/go-live.sh`)

`go-live.sh` removes `    <!-- WAITLIST -->` to `<!-- /WAITLIST -->` blocks and uncomments `    <!-- SALE` to `    SALE -->` blocks (4-space indent, markers on their own lines, `@CHECKOUT@` replaced), then refuses if the page still contains the strings WAITLIST, SALE, `@CHECKOUT@`, "Early access" or "Join the list". The two markers must wrap the whole `<script>` element (an HTML comment inside a script would break the JSON). The text below avoids those strings. Paste both blocks into `<head>` after the canonical link; the descriptions reuse sentences from llms.txt and the README so `tools/check-claims.sh` has nothing new to object to (run it anyway).

```html
    <!-- WAITLIST -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "@id": "https://shotfleet.com/#software",
  "name": "shotfleet",
  "url": "https://shotfleet.com/",
  "image": "https://shotfleet.com/og.jpg",
  "description": "A macOS command-line tool that captures localized App Store and Google Play screenshots from one English Maestro flow, in every language an app ships, and checks that each screenshot is in the right language. It also checks screenshots made by other tools.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "macOS (Apple silicon)",
  "softwareRequirements": "Apple silicon Mac, Maestro 2.x, Java 17 or newer. Xcode for iOS (Debug simulator build), Android SDK with API 33+ emulators for Android.",
  "author": { "@type": "Person", "name": "Manuel Lorenzo Parejo", "url": "https://manulorenzo.me" },
  "offers": [
    { "@type": "Offer", "name": "Free tier", "price": "0", "priceCurrency": "USD",
      "description": "shotfleet check is free for everyone; run is free for up to 2 languages.",
      "availability": "https://schema.org/PreOrder" },
    { "@type": "Offer", "name": "Licence, launch price", "price": "29", "priceCurrency": "USD",
      "description": "Every language and export to fastlane. Launch price for the first 100 buyers, once per developer, a year of updates, 14-day refund.",
      "availability": "https://schema.org/PreOrder" },
    { "@type": "Offer", "name": "Licence, standard price", "price": "49", "priceCurrency": "USD",
      "description": "The price after the first 100 buyers: once per developer, a year of updates, 14-day refund.",
      "availability": "https://schema.org/PreOrder" }
  ]
}
</script>
    <!-- /WAITLIST -->
    <!-- SALE
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "@id": "https://shotfleet.com/#software",
  "name": "shotfleet",
  "url": "https://shotfleet.com/",
  "image": "https://shotfleet.com/og.jpg",
  "description": "A macOS command-line tool that captures localized App Store and Google Play screenshots from one English Maestro flow, in every language an app ships, and checks that each screenshot is in the right language. It also checks screenshots made by other tools.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "macOS (Apple silicon)",
  "softwareRequirements": "Apple silicon Mac, Maestro 2.x, Java 17 or newer. Xcode for iOS (Debug simulator build), Android SDK with API 33+ emulators for Android.",
  "installUrl": "https://shotfleet.com/install.sh",
  "author": { "@type": "Person", "name": "Manuel Lorenzo Parejo", "url": "https://manulorenzo.me" },
  "offers": [
    { "@type": "Offer", "name": "Free tier", "price": "0", "priceCurrency": "USD",
      "description": "shotfleet check is free for everyone; run is free for up to 2 languages.",
      "availability": "https://schema.org/InStock" },
    { "@type": "Offer", "name": "Licence, launch price", "price": "29", "priceCurrency": "USD", "url": "@CHECKOUT@",
      "description": "Every language and export to fastlane. Launch price for the first 100 buyers, once per developer, a year of updates, 14-day refund.",
      "availability": "https://schema.org/InStock" },
    { "@type": "Offer", "name": "Licence, standard price", "price": "49", "priceCurrency": "USD", "url": "@CHECKOUT@",
      "description": "The price after the first 100 buyers: once per developer, a year of updates, 14-day refund.",
      "availability": "https://schema.org/InStock" }
  ]
}
</script>
    SALE -->
```

Two truth caveats to keep: (1) the day the launch price ends, delete the $29 offer or the "launch" wording (stale price markup is a mismatch with the visible page); the home page text is the source of truth. (2) Do not claim the $49 offer is purchasable alongside $29; the description says it is the later price. If Manu prefers the stricter version, keep only the $29 offer while it is the one on sale and add $49 when it takes over.

Both blocks and the article template parse as valid JSON (checked with Python `json.loads`, with `@CHECKOUT@` replaced by a placeholder URL). Schema-level validation in Google's Rich Results Test or validator.schema.org is a web form and was not done; do it by hand after pasting.

### Ready JSON-LD for articles (template; fill the placeholders from the real article)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "TechArticle",
      "headline": "ARTICLE H1",
      "description": "SAME AS THE META DESCRIPTION",
      "mainEntityOfPage": "https://shotfleet.com/guides/SLUG",
      "image": "https://shotfleet.com/og.jpg",
      "datePublished": "YYYY-MM-DD",
      "dateModified": "YYYY-MM-DD",
      "author": { "@type": "Person", "name": "Manuel Lorenzo Parejo", "url": "https://manulorenzo.me" },
      "about": { "@id": "https://shotfleet.com/#software" }
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "shotfleet", "item": "https://shotfleet.com/" },
        { "@type": "ListItem", "position": 2, "name": "Guides", "item": "https://shotfleet.com/guides" },
        { "@type": "ListItem", "position": 3, "name": "ARTICLE SHORT NAME" }
      ]
    }
  ]
}
</script>
```

`datePublished` must be the real publish date and `dateModified` must change only when the text changes (the drafts say technical steps get re-run before publishing: put that date in).

## 4. robots.txt and sitemap.xml

Current `robots.txt` (66 bytes): `User-agent: *`, `Allow: /`, `Sitemap: https://shotfleet.com/sitemap.xml`. Valid. The sitemap lists the four pages with absolute https bare-domain URLs, no query strings, none of them redirecting or noindex. Correct. Notes:
- Research file 3.5 says the robots file has no `Sitemap:` line and there is no sitemap; that is out of date (both exist and are live).
- No `lastmod`. Google uses `lastmod` only if it is consistently accurate; add real dates (and update them only on real content changes).
- `/api/*` (the Worker) is not disallowed. GET on `/api/signup` returns a JSON 405 and nothing links there, so this is hygiene, not a bug.
- `/download/*` and `/install.sh` are crawlable plain files; harmless.
- No `<meta name="robots" content="max-image-preview:large">` (optional; allows large image previews in Google surfaces: unverified benefit here).

### Proposed `site/public/robots.txt`

```
# shotfleet.com: everything public is open to search engines and AI assistants.
User-agent: *
Allow: /
Disallow: /api/

# Named AI crawlers: same rules, written out so the intent is on record.
# A crawler that matches its own group ignores the "*" group, so Disallow is repeated.
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: GPTBot
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: ClaudeBot
User-agent: PerplexityBot
User-agent: Perplexity-User
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: CCBot
Allow: /
Disallow: /api/

Sitemap: https://shotfleet.com/sitemap.xml
```

The named group is optional (the default is already "allowed"); its value is documentation and protection if a Cloudflare setting later injects blocks. Product decision for Manu: GPTBot, ClaudeBot, CCBot, Google-Extended and Applebot-Extended are **training** crawlers, the others fetch pages to answer a user or build a search index. For a paid product that wants to be named by assistants, allowing all of them is the simpler position (a public marketing site has nothing to protect); if you would rather opt out of training only, change those five to `Disallow: /` and keep the search and user-agent bots allowed. Bots that ignore robots.txt (Bytespider is the usual example, unverified) are not worth a rule.

### Proposed `sitemap.xml` (with the future pages marked, add them only when the URL is live)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://shotfleet.com/</loc><lastmod>2026-10-02</lastmod></url>
  <url><loc>https://shotfleet.com/alternatives</loc><lastmod>2026-10-02</lastmod></url>
  <url><loc>https://shotfleet.com/guides</loc><lastmod>YYYY-MM-DD</lastmod></url>
  <url><loc>https://shotfleet.com/guides/fastlane-snapshot-stuck-in-english</loc><lastmod>YYYY-MM-DD</lastmod></url>
  <url><loc>https://shotfleet.com/terms</loc><lastmod>2026-10-02</lastmod></url>
  <url><loc>https://shotfleet.com/privacy</loc><lastmod>2026-10-02</lastmod></url>
</urlset>
```

Use the real last-edited date of each file (`git log -1 --format=%cs -- site/public/index.html`), not today's date by habit. Manu-only steps: verify the domain in Google Search Console (DNS TXT record at Cloudflare) and Bing Webmaster Tools, submit the sitemap in both. That is the only way to get real impressions, indexing and query data; it needs 2 to 4 weeks of data before it says anything (research 3.1 says the same). Bing's index also feeds some assistants (unverified which).

## 5. Internal linking

Verified from the HTML:
- Home links to `/alternatives` once in the body (the small note under "Numbers from real runs") and once in the footer. There is no link to any guide, because none exists.
- Home mentions "fastlane" 6 times as plain text, never as a link; "Not for you if…" says fastlane snapshot is free but does not link to the comparison.
- `/alternatives` links to the home page and legal pages in the footer, but has no call to action to the waitlist or price anchor; its nav has no "Get early access" button.
- Terms and privacy have no link back into the content pages other than home.
- 404 page links only to the home page.
- MARKETING.md phase 0 says the three articles are "linked from the site footer": that footer link is not there yet.

Fixes (all in `site/public`; edit when the articles go live, not before, so there are no links to 404s):
1. Footer on every page: `<a href="/guides">Guides</a> · <a href="/alternatives">Alternatives</a> · …`.
2. Home "Not for you if…": make "fastlane snapshot is free" a link to `/alternatives`; make the three tool chips in the "Made to work with the rest" bento cell link to the matching section anchors on `/alternatives` (add `id` attributes such as `fastlane`, `butterkit`, `appscreens` to its h3s).
3. Home, after the "button nobody could reach" section: one line "Read the story: <a href="/guides/the-button-nobody-could-reach">how I found it</a>".
4. Home, before the footer: a short "Guides" section with the first three article titles as links (plain list, no cards).
5. Each article: breadcrumb (Home > Guides > Title), a "Related" list of 2 siblings, the free next step (`shotfleet check`, linked to `/#price`), and one link to `/alternatives` where the text mentions other tools. Absolute-root links (`/guides/...`, `/img/...`), never `img/...` relative paths (the home page uses relative `img/` paths; copying its markup into a `/guides/x` page would break the images).
6. 404 page: add links to `/`, `/guides`, `/alternatives`.
7. Anchors: `#run` and `#price` exist; there is no `#install` or `#catch` id (the article draft notes already account for this; `#catch` mentioned in 01's link plan does not exist as an id).

Cannibalization to avoid: `/alternatives` (exists) and planned article 6 "fastlane snapshot alternatives" would both target "fastlane snapshot alternative". Use **one URL**: expand `/alternatives` into the article 6 content (keep the URL: it is already in the sitemap, `llms.txt` and the footers) and do not publish a second page. If Manu prefers a separate guide, `/alternatives` must retarget to brand-comparison queries ("shotfleet vs fastlane snapshot") and link to the guide as the full comparison. Also keep articles 1 and 4 apart (1 is the troubleshooting answer for "snapshot shows English", 4 is the generic checklist) and link 4 to 1, 2, 3 as items.

## 6. Proposed `/guides` structure for static assets plus Worker

Facts that decide it (Workers static assets, default `html_handling = "auto-trailing-slash"`; observed here on `/alternatives`): `public/alternatives.html` is served at `/alternatives` (200) and `/alternatives.html` and `/alternatives/` redirect (307) to it. By the documented behaviour of that mode, `public/guides.html` serves `/guides` and `public/guides/<slug>.html` serves `/guides/<slug>`; a folder `index.html` would instead serve at `/guides/` with `/guides` redirecting to the slash form. I did not deploy to test the nested case (not allowed); test it with `npx wrangler dev` before the first publish. Nothing about `run_worker_first = ["/api/*"]` changes: the Worker is not involved.

```
site/public/
  guides.html                                    -> /guides (hub: list of guides with one-line descriptions)
  guides/fastlane-snapshot-stuck-in-english.html -> /guides/fastlane-snapshot-stuck-in-english
  guides/maestro-one-flow-every-language.html
  guides/the-button-nobody-could-reach.html
  guides/localized-screenshots-qa-checklist.html
  guides/google-play-screenshots-every-language-emulators.html
  guides/ios-permission-alerts-stay-english-ui-tests.html
  guides/plural-forms-screenshot-flows.html
  alternatives.html                              -> /alternatives (expanded with article 6, no separate guide)
  docs.html                                      -> /docs (README as a plain page; see AI section)
```

- Hand-written HTML copied from the `alternatives.html` head and footer is enough for 8 pages (no static site generator; add one when there are more than about 15 pages). Convert the markdown drafts once with `pandoc -f gfm -t html` (check `which pandoc`) or a short Python script, then paste into the template. Keep `site.css`; the inline `<style>` in `alternatives.html` should move to `site.css` before copying it 8 times.
- The three drafts carry other slugs (`/fastlane-snapshot-screenshots-all-english`, `/maestro-one-flow-every-language`, `/the-button-nobody-could-reach`) and 04-ideas.md uses root-level slugs. Change them all to `/guides/...` before publishing; if any went live under an old slug, add a path-based 301 in `site/public/_redirects` (supported by Workers assets, host-independent): `/old-slug /guides/new-slug 301`.
- Do not put articles at `/blog`: the content is evergreen how-to, not dated posts; `/guides` also reads better in a title and breadcrumb. Dates appear on each page (published, last verified).
- Add the guides to `llms.txt` and `sitemap.xml` in the same commit that publishes them.
- Nothing publishes by itself: per MARKETING.md "Claude prepares, Manu posts", the articles stay drafts until each TO VERIFY item is ticked (the drafts say several snippets have not been run, and `/download/VERSION` was a 404 when last checked, so `shotfleet check` in the call to action only works after the first release; until then the call to action is the waitlist).

## 7. Performance (verified unless marked)

- Transfer sizes with brotli: home HTML 5.8 KB (25.4 KB raw), `site.css` 6.9 KB (24.9 KB raw), five small scripts about 3.5 KB together, `/alternatives` 3.1 KB. No web fonts (system stacks only, confirmed in `site.css`), no third-party requests, `connect-src 'self'`.
- Images: 4 eager JPEGs above the fold (`train_ja/fr/ar/ko`, 35 to 42 KB each, about 155 KB) plus lazy ones. If a visitor scrolls the whole page and opens the Cairn tab, images total about 0.9 MB (train x7 281 KB, bug 20 KB, stressi 122 KB, cairn 466 KB), plus 1.4 MB of `img/full/*` only on click. All have `width` and `height` attributes (no layout shift from images) and alt text.
- Sizing: the thumbnails are 360 px wide shown at 152 to 212 CSS px (adequate on 2x screens, slightly soft above that). The Cairn thumbnails are 900x675 shown at 250 to 340 CSS px: about 2.6x larger than needed, but they sit in a hidden tab with `loading="lazy"`, so they load only if the tab is opened.
- Formats: all JPEG. WebP or AVIF would likely save roughly a third (unverified; measure with `cwebp -q 80` on two files before committing to it). Low priority at this weight.
- Caching: HTML, CSS, JS, `og.jpg` use Workers' default `max-age=0, must-revalidate` with ETag (Cloudflare shows `cf-cache-status: HIT`, so repeat views are cheap 304s). `/img/*` is `max-age=604800` (7 days) but file names are not hashed, so a replaced screenshot can be stale for a week; the files are named by content (`train_ja.jpg`), so rename on change.
- Compression: brotli on HTML and CSS (verified `content-encoding: br`).
- LCP candidate: **not measured** (see top). Reading the CSS: the h1 is system-font text, so it paints with the first render. The fleet images use a `rise` animation (`opacity: 0` to 1, 1.1 s, delay 0.2 s + 0.08 s per image), and Chrome does not count an image as an LCP candidate while it is fully transparent. On a narrow phone, where the 152 px x 330 px phone images can be the largest element on screen, the LCP is therefore probably set by an image that is deliberately delayed by about 0.3 to 1.4 s. This is a hypothesis; confirm with PageSpeed Insights once its quota resets, or with CrUX / Search Console Core Web Vitals once there is traffic. If it holds, the fix is to drop the animation from the first two images or start it at `animation-delay: 0s` with a shorter duration, and add `fetchpriority="high"` to the first image.
- `reveal.js` is a synchronous `<script>` in the head (475 bytes, same origin). Keeping it synchronous is correct (it must add the `js-reveal` class before first paint); it is not a problem.
- Optional: hint the browser with early hints from `_headers` (Cloudflare turns `Link` headers into 103 Early Hints; unverified for Workers assets): under `/`, `Link: </site.css>; rel=preload; as=style`.

## 8. AI-search readiness

Verified:
- **No JavaScript needed.** The raw HTML contains all the content: the h1, definition-like sentences, the numbers section, the terminal result (inside `role="img" aria-label` with the full result text), the flow-rewrite table, the "Not for you if" list, the pricing ($29 launch price for the first 100 buyers, then $49, free tier, 14-day refund) and the requirements. JavaScript only adds the waitlist form behaviour, tabs (both app galleries show without it), zoom and a scroll fade (applied only when JS runs and motion is allowed). Forms need JS but crawlers do not use them.
- **Crawler access.** robots.txt allows everything. I requested `/` with the user agents GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, Claude-SearchBot, CCBot, Bytespider, Googlebot, Amazonbot, Applebot and curl: all returned 200. This is **not proof** that Cloudflare's AI bot features are off: those use verified-bot lists and fingerprints, and I was spoofing the string from one IP, so a real crawler could still be treated differently.
- `robots.txt` as served shows none of the lines Cloudflare's "Manage robots.txt" (Content Signals) feature would add, so that managed-robots.txt feature does not appear to be on for this zone.
- `/llms.txt` exists (2.6 KB, `text/plain`, ASCII only, identical to the repo), correct structure: H1, blockquote summary, "What it does", "Requirements", "Price and licence", "Links" with five absolute URLs. Content is accurate against README and the home page (price, Apple silicon only, Maestro 2.x, Java 17+, Xcode, Android API 33+, the Flutter and React Native caveat, "Text typed into fields is not translated" stated). `/llms-full.txt` is a 404. `Accept: text/markdown` returns HTML (no markdown negotiation).
- No structured data (section 3), no visible "what is shotfleet" definition sentence on the home page (only in llms.txt), and the home page copy lacks the words "App Store" and "Google Play".

Unverified (say so if quoting): whether any assistant reads `llms.txt` at all (major vendors had not confirmed it as of my knowledge), and whether on-site changes matter more than mentions on third-party sites that models and search indexes already cite (GitHub, Reddit, AlternativeTo, newsletters). The marketing plan already targets those; the on-site work is cheap hygiene.

### Cloudflare's managed AI settings on this zone (Manu to check; I did not open his Cloudflare tab)

From memory (unverified, the dashboard names move): Cloudflare began blocking AI crawlers by default on zones created after 1 July 2025 and shows the choice at onboarding, and the zone has settings under Security, Bots ("Block AI bots", and "AI Crawl Control" / "Manage robots.txt" with a Content Signals Policy). The domain is new, so check these three things and keep them aligned with the robots.txt decision in section 4:
1. Block AI bots: set to **off** (or "only on hostnames with ads", which is not the case here) if you want to be citable.
2. Managed robots.txt: leave **off**, since a hand-written file is already in the repo; if you switch it on, re-fetch `/robots.txt` and make sure it does not add `Disallow` for search bots.
3. Pay-per-crawl: off.
Re-test after any change: `curl -s https://shotfleet.com/robots.txt` and the user-agent loop above.

### Fixes for AI readability

1. Add a one-paragraph definition high on the home page (visible text, not just llms.txt), reusing the llms.txt sentence: "shotfleet is a macOS command-line tool that captures localized App Store and Google Play screenshots from one English Maestro flow, in every language an app ships, and checks that each screenshot is in the right language." Place it in the hero `.sub` or directly under the fleet note.
2. Add `/docs` (static `docs.html`): the README sections What it checks, Quickstart, Config, In CI, With AI agents, Limits as plain HTML. It is the single most useful addition: the site currently has no page that answers "how do I use it" (README is not on the site), so assistants can quote only the marketing page. Also publish it as `/llms-full.txt` (the same text as markdown) and link both from `llms.txt`.
3. Update `llms.txt` when guides and docs exist (snippet below). Add `Content-Type: text/plain; charset=utf-8` for it in `_headers` only if non-ASCII is added later; today it is ASCII.
4. Keep comparison facts as HTML text with dates (the alternatives table already is; "Checked on 2026-10-02" is a good freshness signal; update it when prices are re-read, and set `dateModified`).
5. In articles, put a two-sentence direct answer under the h1, and name versions and dates ("verified with Maestro 2.x on 2026-MM-DD"); assistants prefer quotable, dated, specific statements. Never put a claim that `tests/claims.json` does not back.

`llms.txt` additions (after the guides and docs are live):

```
## Docs and guides

- [Docs](https://shotfleet.com/docs): commands, config, CI, limits
- [Guides](https://shotfleet.com/guides): how-to articles on localized store screenshots, Maestro locales and fastlane
- [llms-full.txt](https://shotfleet.com/llms-full.txt): the docs as one markdown file
```

---

## 9. Prioritized fix list

### P0: before the sale opens or before any link building (small, mostly one file each)

1. **www to bare 301** (Redirect Rule, section 2). 2 minutes in the dashboard. Verify with curl.
2. **Home head**: replace the title and description; add `og:site_name`, `og:locale`; add the JSON-LD (section 3).
```html
<title>shotfleet · Localized store screenshots from one Maestro flow</title>
<meta name="description" content="A Mac command-line tool: write one Maestro flow in English, capture App Store and Google Play screenshots in every language you ship, and check each one.">
<meta property="og:title" content="shotfleet · Localized store screenshots from one Maestro flow">
<meta property="og:description" content="One English Maestro flow. Every language your app ships, in parallel, checked.">
<meta property="og:site_name" content="shotfleet">
<meta property="og:locale" content="en_US">
```
   (Title 61 chars, description 153 chars; both counted. The go-live script's forbidden strings are not used.) Keep `og:description` as is.
3. **Home copy**: add the definition sentence and the words "App Store" and "Google Play" once in visible text (hero sub or under the fleet note). Do not change the brand-voice h2s. Keep `tools/check-claims.sh` green.
4. **`/alternatives` head**: new title and description, canonical already there, add og/twitter.
```html
<title>fastlane snapshot alternatives, and when not to buy shotfleet</title>
<meta name="description" content="shotfleet vs fastlane snapshot, simshot, ButterKit and AppScreens for localized App Store and Play screenshots, with prices and who should skip shotfleet.">
<meta property="og:title" content="fastlane snapshot alternatives, and when not to buy shotfleet">
<meta property="og:description" content="An honest comparison, with the free options first and a list of who should not buy shotfleet.">
<meta property="og:image" content="https://shotfleet.com/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://shotfleet.com/alternatives">
<meta property="og:type" content="website">
<meta property="og:site_name" content="shotfleet">
<meta name="twitter:card" content="summary_large_image">
```
   (Title 61 chars, description 154.) Also change its h1 from "shotfleet and the other tools" to "fastlane snapshot alternatives, and when not to buy shotfleet" or keep the h1 and use the title only; either is fine as long as title and h1 say the same thing.
5. **Canonical on `/terms` and `/privacy`**: add `<link rel="canonical" href="https://shotfleet.com/terms">` and `.../privacy`. Optionally `<meta name="robots" content="noindex">` is not needed; keep them indexable (trust pages for the merchant of record and for people).
6. **robots.txt** (add `Disallow: /api/`, section 4) and **sitemap lastmod**.
7. **Search Console and Bing Webmaster**: Manu verifies the domain (DNS TXT) and submits the sitemap. Without this there is no data to decide anything.

### P1: with the first guide

8. `/guides` hub and `/guides/<slug>` pages (section 6), footer link `Guides`, home "Guides" section, 404 links, sitemap and `llms.txt` entries, article JSON-LD (section 3). Fix the drafts' slugs first.
9. Merge article 6 into `/alternatives` (section 5), no second URL.
10. `/docs` and `/llms-full.txt` (section 8).
11. `favicon.ico` (48x48) and `apple-touch-icon.png` (180x180) in `site/public/`.
12. HSTS at Cloudflare (section 2).

### P2: later, measure first

13. Run PageSpeed Insights (mobile) once the quota resets and read the LCP element; if it is a fleet image, shorten or remove its fade-in on the first two images (section 7) and add `fetchpriority="high"` to the first.
14. WebP or AVIF for the thumbnails; smaller Cairn thumbnails (about 680 px wide); move the `alternatives.html` inline style into `site.css`.
15. `_headers` `Link: </site.css>; rel=preload; as=style` for `/`.
16. Per-article og images (a plain 1200x630 with the article title) instead of the shared `og.jpg`.
17. `hreflang` only when the Japanese and Korean pages start (research/website-localization.md): use `/ja/` and `/ko/` folders with reciprocal hreflang and a self-referencing canonical each.

---

## 10. Keyword plan: the 8 articles

Source of the queries, intents and "who ranks" notes: `research/marketing-research.md` 3.3 and 3.4 and `marketing/articles/04-ideas.md`. I did not re-run those searches. **Every statement of volume, difficulty or ranking chance is unverified**; where the research file says "good" or "medium" chance, that is its judgement from the results it saw. Title tags are at most 56 characters (no brand suffix: the brand comes from `og:site_name` and the logo; adding " · shotfleet" would push most past 60), descriptions at most 156 characters; lengths were counted.

Rules for every article, in addition to the per-article lists: the first-person voice and no hype from the drafts; one direct-answer paragraph under the h1; "last verified" date and the tool versions used; code blocks that can be copied; the free next step (`shotfleet check`, or the waitlist link until the first release); a paragraph on what shotfleet cannot do; official sources linked (Apple, Google, Maestro, fastlane docs); a "Related" list; byline Manu with a link to manulorenzo.me; TechArticle and BreadcrumbList JSON-LD (template in section 3); `og:type` `article` with `article:published_time`. Every sentence about shotfleet backed by `tests/claims.json` or the code.

### 1. fastlane snapshot screenshots stuck in English (draft exists)

| Field | Value |
|---|---|
| Target query | fastlane snapshot wrong language; fastlane snapshot not changing language; fastlane screenshots all english |
| Intent | Informational, troubleshooting (a person with a failing setup wants the cause) |
| Slug | `/guides/fastlane-snapshot-stuck-in-english` |
| Title tag (54) | fastlane snapshot screenshots all in English: 5 causes |
| Meta description (153) | Every language folder shows English? Five causes to rule out in fastlane snapshot, plus a free command that checks each image against your app's strings. |
| H1 (draft) | Why your fastlane snapshot screenshots are all in English (and how to check every language) |
| On-page elements | Direct answer in the first paragraph (launch arguments vs simulator locale, `localize_simulator`); five numbered causes as h2s, each with a "how to confirm" command; the four or five GitHub issues cited with one line each and a note that they are from 2017 to 2018 and not proof the bug exists today; a `ls MyApp.app/*.lproj` check; the free `shotfleet check fastlane/ --app MyApp.app` block with sample output; an honest "when not to use shotfleet" paragraph; links to guide 2 and 4. Optional real FAQ section only if you write 3 real questions. |
| Notes | The research file says the results for this query are mostly GitHub issue threads (so a guide is differentiated: unverified, not re-checked). Draft TO VERIFY items 3 and 5 must be run first. |

### 2. One Maestro flow in every language (draft exists)

| Field | Value |
|---|---|
| Target query | maestro multiple languages; maestro locale; maestro screenshots different languages; maestro device-locale |
| Intent | Informational, how-to (tutorial) |
| Slug | `/guides/maestro-one-flow-every-language` |
| Title tag (54) | One Maestro flow in every language, on iOS and Android |
| Meta description (154) | Maestro cannot set the locale inside a flow. Run one flow in every language on iOS and Android, and avoid the four traps that give you English by mistake. |
| On-page elements | Direct answer + a minimal working flow; iOS (`-AppleLanguages`) and Android (per-app locale on API 33+) sections as h2s with the exact commands; a table "traps and symptoms" (port 7001 shared by parallel Android runs, the env-precedence trap in Maestro 2.10 with the cited PR, `--device-locale` limits, `clearState` resets); the Maestro version tested stated at the top (research roadmap R1: only 2.0.10 was run, 2.11 current: re-test and say which); link to Maestro's own docs; link to guide 5 and 7; the shotfleet section kept short and last. Careful: the marketing rules say never to quote "Maestro says one flow per locale" (the docs now recommend tags plus `--device-locale`). |
| Notes | Every snippet in the draft is unrun; do not publish until the TO VERIFY list is ticked. |

### 3. The button nobody could reach (draft exists, founder story)

| Field | Value |
|---|---|
| Target query | android button off screen translation; next button not visible small phone; text overflow localization android onboarding; jetpack compose verticalScroll long translations |
| Intent | Informational / story, long-tail troubleshooting, shareable for newsletters and Show HN |
| Slug | `/guides/the-button-nobody-could-reach` |
| Title tag (55) | A Next button nobody could reach in Japanese on Android |
| Meta description (151) | In Japanese, Korean, Chinese and Arabic the Next button sat below the screen on a small Android phone. How I found it, the fix, and how to test for it. |
| On-page elements | The `img/bug_zh.jpg` screenshot with the alt text from the draft ("Chinese onboarding page with four goal cards and no Next button") and explicit `width`/`height`; the review-grid image with red outlines once rendered; the Compose fix as a code block (the draft says an 8-line fix; the home page says two pages were made to scroll: make the article and home agree); "how to test for it" with the free check; an honest line that this is one app and one bug; link to guide 4 (item 9 of the checklist). Pinned to a commit and image, per the draft. |
| Notes | Highest shareability, so it is the article to submit to newsletters (MARKETING.md). If the long-tail query is the goal over the story, an alternative slug is `/guides/android-button-off-screen-long-translations`; keep the story slug as it is the one that gets linked. |

### 4. Localized app store screenshots QA checklist

| Field | Value |
|---|---|
| Target query | localized app store screenshots checklist; app store screenshot rejection 2.3.3; verify localized screenshots |
| Intent | Informational, checklist (people audit a listing before submitting); partly commercial investigation |
| Slug | `/guides/localized-screenshots-qa-checklist` |
| Title tag (54) | Localized app store screenshots checklist: 10 failures |
| Meta description (154) | Ten ways a localized App Store or Google Play listing is wrong, from English copied into every folder to an unreachable button, and how to check each one. |
| On-page elements | The ten items from 04-ideas.md as numbered h2s, each with "what it looks like", "find it by hand", "how `check` reports it" (real output from a planted failure), and the Apple or Google spec link; a summary table of the ten at the top (quotable); the limits paragraph (scripts macOS cannot read, very short screens, claims C003 and C030); links to guides 1 and 3 from items 1 and 9; Apple's screenshot specifications and Google Play preview assets pages re-read on the day (limits change). |
| Notes | Competitors' checklists are generic per the research (unverified); the value is real failures with real output, so wait for one real before and after with written permission, as the draft says. "Rejection 2.3.3" must not be implied as a rejection reason unless Apple's guideline text says so: quote the guideline once, with the link, after reading it that day. |

### 5. Google Play screenshots in every language with emulators

| Field | Value |
|---|---|
| Target query | google play screenshots every language automate; fastlane screengrab locale; android emulator screenshots multiple languages |
| Intent | Informational, how-to |
| Slug | `/guides/google-play-screenshots-every-language-emulators` |
| Title tag (56) | Google Play screenshots in every language with emulators |
| Meta description (156) | Automate Google Play screenshots in every language: per-app locales on Android 13+, emulators, the fastlane supply folder layout and what 18 languages cost. |
| On-page elements | A table of Play's rules (count, 320 to 3840 px per side) with the link to Google's page and the date read; the manual path with real adb commands (`cmd locale set-app-locales`, verified on an API 33+ emulator first); the folder layout `metadata/android/<locale>/images/phoneScreenshots/`; a timing box with the machine stated (18 languages by 4 screens, 15 min 24 s on one Mac with 4 emulators, claims C007; re-time and name the machine); the `fastlane supply` upload line run on a test track, screenshots only; link to guide 2. |
| Notes | The research file says Android is thinner than iOS on this topic and Google's own docs rank (unverified). Needs API 33+; no upload by shotfleet. |

### 6. fastlane snapshot alternatives in 2026 (merge into `/alternatives`)

| Field | Value |
|---|---|
| Target query | fastlane snapshot alternative |
| Intent | Commercial investigation (comparison) |
| Slug | **`/alternatives`** (do not create `/guides/fastlane-snapshot-alternatives`; one URL, see section 5) |
| Title tag (55 for the article variant; the page title used in P0 is 61) | fastlane snapshot alternatives in 2026: an honest table |
| Meta description (149) | Free options first: fastlane snapshot, screengrab, Maestro, simshot, then ButterKit and AppScreens. What each costs and who should not buy shotfleet. |
| On-page elements | Keep the existing text table (HTML, not an image) and extend it with Maestro `--device-locale`, StoreScreens CLI and the asc CLI; columns what it does, platforms, price, what it checks, who should not use it; "capture with anything, check with shotfleet"; dated facts ("checked on <date>") for every price (ButterKit Pro, AppScreens Pro and Scale, Maestro Cloud per device per month, simshot status; open the source on the day, do not copy numbers from the research file); the C094 reword ("runs your languages one after another on each simulator") and the `concurrent_simulators` check before the parallel row is published; `dateModified` in JSON-LD. |
| Notes | The research file rates this SERP as contested by vendors (unverified). If the head-to-head timing is not run, say nothing about relative speed. The published `/alternatives.html` and the unpublished `site/draft/alternatives.html` differ; reconcile before editing. |

### 7. iOS permission alerts stay English in UI tests

| Field | Value |
|---|---|
| Target query | maestro permission dialog localization; ios permission alert language ui test; maestro allow while using app german |
| Intent | Informational, troubleshooting (very narrow) |
| Slug | `/guides/ios-permission-alerts-stay-english-ui-tests` |
| Title tag (46) | iOS permission alerts stay English in UI tests |
| Meta description (152) | Your app is German but the iOS permission alert is English. What that does to Maestro and UI-test taps, one measurement, and the permissions workaround. |
| On-page elements | A screenshot of a German app with an English alert (alt text describing both); the measurement (what was run, iOS version, app) repeated on a second app; the open Maestro issue #2654 linked and re-read; the `launchApp: permissions: all: allow` block from the README; the Android half only if tested (the draft says it is untested: do not claim it); no claim of live permission-alert taps in shotfleet (claims C070 is partial). |
| Notes | Low effort, good for newsletters (draft). Volume for this query is unverified and probably small; value is as a link target. |

### 8. Plural forms in screenshot flows

| Field | Value |
|---|---|
| Target query | localized plural forms ui test; arabic plural forms android strings; cldr plural categories |
| Intent | Informational, reference; link bait for the localization audience |
| Slug | `/guides/plural-forms-screenshot-flows` |
| Title tag (54) | Plural forms in UI test flows: Arabic, Russian, Polish |
| Meta description (153) | A tap selector for "Round 2 of 12" has to match every CLDR plural form. How Arabic, Russian and Polish differ, and how to match them in screenshot flows. |
| On-page elements | A table of CLDR categories per language (Arabic six, Russian four, Polish four, Japanese one: confirm against the Unicode CLDR plural rules chart the day you publish and link it); what `.stringsdict` and Android `<plurals>` look like; one worked example per language with real generated selectors and the app's strings read by hand (README Limits, claims C015); a short "why a template alone cannot match" section with a code block. |
| Notes | Lowest priority, per the draft: write after the sale has data. Intent is niche; unverified volume. |

### Order and cannibalization check

Publish order stays 1, 2, 3, then 6 (as the `/alternatives` expansion, since it already exists), 5, 4, 7, 8, subject to each gate in 04-ideas.md. Distinct target queries: no two articles share a head query. Overlaps to manage with links, not merging: 1 and 4 (item 1 of 4 links to 1), 2 and 5 and 7 (all touch Maestro locale; 2 is the hub, 5 and 7 link up to it), 3 and 4 (item 9 of 4 links to 3). Do not write for the head terms the research marks as vendor territory ("app store screenshot sizes", "best screenshot tools", "screenshot generator").

## 11. What was not checked

- Indexing status, impressions, queries, backlinks: no Search Console or SEO connector authorized; the `site:` search returned nothing useful.
- Core Web Vitals and Lighthouse scores (PageSpeed quota exhausted; background-tab LCP empty).
- Cloudflare dashboard settings (AI bot block, managed robots.txt, HSTS, existing Redirect Rules): I did not touch the owner's open Cloudflare tab; verify by hand.
- Nested `/guides/<slug>` routing on Workers assets (documented, not deployed).
- Schema validation in Google's Rich Results Test and validator.schema.org (web forms; not submitted). JSON syntax and CSP behaviour were checked as described in section 3.
- Whether any SERP above still looks the way research/marketing-research.md describes.

Nothing on the site or in the repo was changed; this file is the only output. A temporary local test server and one browser tab were used and closed.
