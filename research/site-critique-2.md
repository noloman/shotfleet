# shotfleet.com live site critique, round 2

Reviewed 2026-10-02 on the live site: `/`, `/alternatives`, `/terms`, `/privacy` (and the 404). No form was submitted, no Buy link was clicked, nothing was edited or deployed. Forms were tested client-side only, with `x` and `notanemail` and with an empty message. Tools were Claude in Chrome (own tab, closed afterwards) plus curl.

## How this was measured, and the limits

- The Chrome window could not be resized. `resize_window` succeeded, but `innerWidth` stayed at 1800 with DPR 2 and OS dark mode. To get the three widths I rendered each page's HTML in a same-origin `srcdoc` iframe of exactly 375, 820 or 1440 CSS px (media queries then evaluate against the iframe width). Light theme was forced with the site's own `data-theme="light"` hook. Dark was the real OS preference.
- Contrast ratios are WCAG 2.x. They were computed from `getComputedStyle` colours, composited over the real ancestor backgrounds (via canvas, so `color-mix()` values are handled), for every text node on all four pages in both themes. Transitions were disabled before measuring so mid-transition colours did not skew the numbers.
- The tab was `visibilityState: hidden`, so the scroll-reveal fade was slow in some screenshots. I did not count that as a defect. I confirmed `.reveal.in` and opacity 1 are reached on intersection.
- Not covered: Safari, Firefox, real touch hardware, a screen reader, an Android browser. The Return key on the header anchor did not register in this harness, so I did not test where that anchor lands focus.
- A screenshot taken while the zoom dialog was open came back blank. I verified the dialog by DOM state instead (open, focus, image size).

---

## P0: broken or misleading

### P0-1. The "shotfleet" brand link is dead on /terms, /privacy and the 404, and it floats over the text while scrolling

- **Where:** `header.top > .wrap > a.brand` on the text pages. The home page and `/alternatives` use `nav.pill`, which resets this, so they are fine.
- **Evidence:**
  - `.top { pointer-events: none }` is inherited by `.brand`. Computed `pointer-events` on the brand is `none`, and `document.elementFromPoint` over it returns `BODY`. The link cannot be clicked with a mouse. Keyboard works.
  - `.top` is `position: sticky; z-index: 20` with a transparent background, so the brand text sticks at the top and overlaps headings as you scroll. A screenshot of /privacy shows "shotfleet" printed over the "What I use it for" heading.
  - /terms has no footer or nav at all, so its only way home is the dead brand link.
- **Fix:** give the text pages the same pill as the other pages (preferred), or make the minimal repair:
```css
.top .brand { pointer-events: auto; }
.top:not(:has(.pill)) { position: static; }   /* text pages: no floating, unbacked brand */
```
  Also add the footer (Home · Licence and refunds · Privacy) to /terms.

### P0-2. Hero and meta copy read as a product you can use today, but nothing can be bought or installed. The price card makes this worse.

- **Where:** hero `h1` and `.sub`, `meta[name=description]`, `#price .plan.main`, `/alternatives` table price cell, `/terms` h1 "What you get when you buy shotfleet".
- **Evidence:**
  - "shotfleet isn't released yet" appears only in the `#price` paragraph, about 5,300 px down at 1800 wide. The hero says "shotfleet captures them all and checks every screenshot", in present tense.
  - The only CTA is "Get early access".
  - The price card shows "$29 launch price, first 100 buyers · Then $49" directly above a "Join the list" button. A reader can take that as "joining reserves $29". The page never says whether it does.
  - /alternatives states "$49 once ($29 for the first 100 buyers)" as if on sale, and /terms promises a 14-day refund "after buying". Both are fine as pre-announcements but have no "not on sale yet" note.
- **Fix, copy only:**
  - Under the hero form: `Not released yet. Join the waitlist for one launch email.`
  - Rename the button "Join the waitlist".
  - In the price card: `Launch price, not reserved by joining the list` (or "reserved for list members", whichever is true).
  - Add a one-line "Not on sale yet" note to /alternatives and /terms.
  - Make the meta description future-tense: "shotfleet will run…".

---

## P1: clear UX or accessibility defects

### P1-1. Dark theme: two "dark" cards turn near-white and their yellow text becomes unreadable
- **Where:** `.cell.you dt` ("YOUR FLOW"), `.bento .a span.y` ("MyApp.app"), `.bento .a span.dim` ("shotfleet.toml").
- **Evidence:** in dark, `--ink` becomes `#eaf0f7`, and these cards use `background: var(--ink)` with fixed yellow text. Measured ratios:

| Element | Ratio | Needed |
|---|---|---|
| `dt` "Your flow" | 1.45:1 | 4.5 |
| `span.y` "MyApp.app" | 1.46:1 | 4.5 |
| `span.dim` "shotfleet.toml" | 4.02:1 | 4.5 |

  The screenshot confirms it: the YOUR FLOW label and the config value are barely visible. The big off-white bento card also glares against the dark page. Light theme has no failures; its minimum is 4.75.
- **Fix:** stop using `--ink` as a card background. Add tokens that stay dark in both themes:
```css
:root { --card-dark:#0d1b2a; --card-dark-text:#f3f5f8; }
:root[data-theme="dark"], /* and the prefers-color-scheme block */ { --card-dark:#16263a; }
.bento .a, .cell.you { background:var(--card-dark); color:var(--card-dark-text); }
.bento .a p { color:color-mix(in srgb,var(--card-dark-text) 72%,transparent); }
.bento pre  { color:var(--card-dark-text); }
```
  The yellow on `#16263a` is about 9:1.

### P1-2. The price and the product state are not in the first screen, so the 5-second test fails on price
- **Evidence:** at 1440×900 (and 1800 dark) the first screen has the H1, the sub, an email field and a language strip. There is no price, no "waitlist" word, no platform requirement. The price first appears in the last section. The header "Pricing" link exists, but it lands on a section headed "Early access" whose first text is a 70-word paragraph of requirements and caveats.
- **What works:** product comprehension is good. "Store screenshots in every language your app ships" plus the strip of seven localized screens is clear in about 3 seconds. "Maestro" is unexplained jargon for anyone who has not used it.
- **Fix:** add one muted line under the hero form, for example `Mac command-line tool for Apple silicon · $29 launch price (first 100 buyers), then $49 once · not released yet`. Link "Maestro" to maestro.dev on first use, or write "Maestro (UI-flow tool)".

### P1-3. The hero language strip hides 35% of itself and cannot be scrolled with a mouse
- **Where:** `.fleet:not(.small)` (the home hero strip).
- **Evidence:** at 1440, `scrollWidth` is 2198 against `clientWidth` 1440, so 758 px is off-screen. That includes DE and the "+11 more languages" card. `scrollbar-width: none` plus `::-webkit-scrollbar { display:none }` removes every affordance. Plain-wheel mouse users cannot scroll horizontally. Trackpad, touch and keyboard (the group is `tabindex=0`) can. The "+11" card carries the "18 languages" message and is the one most likely to be missed.
- **Fix:** show a thin scrollbar for fine pointers and add two buttons:
```css
@media (hover:hover) and (pointer:fine){
  .fleet{ scrollbar-width:thin; scrollbar-color:var(--line) transparent; }
  .fleet::-webkit-scrollbar{ display:block; height:8px }
  .fleet::-webkit-scrollbar-thumb{ background:var(--line); border-radius:8px }
}
```
  At ≥1100 px it is also reasonable to wrap the strip or shrink `--ship` so all 8 items fit.

### P1-4. /alternatives, the highest-intent page, has no conversion path
- **Evidence:** the header has the three anchor links but no CTA button. The page body has no form or link to join. The footer has none either. It ends on "The story".
- **Fix:** add the same `Join the waitlist` pill to the header on /alternatives, and one block at the end of the page.

### P1-5. /alternatives comparison table: scrolls sideways with no cue, is not keyboard-reachable, and has no header semantics
- **Where:** `.tablewrap > table` (`min-width:760px`).
- **Evidence:** at 375 the table is 760 px inside a 327 px wrapper, so more than half is hidden. There is no shadow or fade cue. `.tablewrap` has `tabindex=-1`, so keyboard users cannot scroll it. The table has no `<caption>` and all six `<th>` have no `scope`.
- **Fix:**
```html
<div class="tablewrap" role="region" aria-labelledby="cmp-h" tabindex="0">
<table><caption class="sr">Feature comparison of shotfleet and four other tools</caption>
<thead><tr><th scope="col">Tool</th>…
<tbody><tr><th scope="row">shotfleet</th>…
```
```css
.tablewrap { background:
  linear-gradient(90deg,var(--surface) 30%,transparent) left/40px 100% no-repeat local,
  linear-gradient(270deg,var(--surface) 30%,transparent) right/40px 100% no-repeat local,
  linear-gradient(90deg,rgba(0,0,0,.12),transparent) left/12px 100% no-repeat scroll,
  linear-gradient(270deg,rgba(0,0,0,.12),transparent) right/12px 100% no-repeat scroll; }
```
  Also make the first column sticky on small screens.

### P1-6. Tap targets under 44 px, and secondary text under 16 px
- **Targets, measured at 375 (the 820 and 1440 results are the same except the header links are visible):**

| Control | Size | Note |
|---|---|---|
| Header CTA `.btn.sm` | 183×40 | |
| Header text links ("A real run" etc., ≥641 px) | 92×42, 84×42, 74×42 | |
| `.brand` | 105×22 | |
| Footer links | 17 px tall (47–147 px wide) | |
| Inline "How it compares…" / "Licence and refunds" | 39 / 19 px tall | |
| Zoom viewer "Close" button | 75×34 | |

  Hero form buttons are 48 px, form fields 52 px and gallery tabs 47 px, which is good. No document overflow at any width on any page (`scrollWidth` equals the viewport).
- **Text under 16 px (body is 17px/27px, which is good):**

| Text | Size |
|---|---|
| Figcaptions (the only visible language name per screenshot) | 13.6 px |
| `.fleet-note` (the key proof sentence: "Seven of 72 screenshots…") | 14.1 px |
| `.small` | 14.1 px |
| Flow-row `dd` | 14.7 px |
| Plan `li` | 15.5 px |
| Table | 15.2 px |
| Table notes | 13.6 px |
| Tab sub-labels "Android" / "iPad" at ≤520 | 12.5 px |

- **Fix:**
```css
.btn.sm{min-height:44px} .pill .links a{padding:12px 14px}
footer a{display:inline-block;padding:13px 6px}
.brand{padding-block:11px}
.zoom-close{padding:14px 20px}
.ship figcaption{font-size:1rem}
.fleet-note,.small{font-size:1rem}
.tabs button span{font-size:.875rem}
```

### P1-7. The terminal block cuts its own result line on phones
- **Where:** `.terminal pre` (`white-space: pre; overflow-x:auto`) inside `role="img"`.
- **Evidence:** at 375, "capturing 18 locales on 4 simulators…" and "captured 18/18 locales in 534s on 4 simulators" run past the 327 px box. The final line, which is the proof, is clipped. It sits in an unfocusable scroller, so keyboard users cannot reach it.
- **Fix:**
```css
@media (max-width:520px){ .terminal pre{ white-space:pre-wrap; overflow-wrap:anywhere; font-size:.8rem } }
```

### P1-8. Honesty: the Flutter/React Native caveat is buried, and the proof gallery is not proof
- **Evidence:**
  - "iOS and Android" in the hero is stated for "your app". The caveat "not yet run on a real Flutter or React Native app" sits in the final section's paragraph and in the "Not for you" list only by omission. Developers on those stacks will assume support.
  - The `#apps` gallery (Stressi, Cairn) is captioned "real store screenshots, not shotfleet output". It is honest, but placed under the heading "The same screen, in the languages of my other apps", it reads as capability proof when it proves nothing about the tool. It is also the only zoomable imagery, while the real output (the hero strip and the Chinese bug image) cannot be enlarged.
- **Fix:**
  - Add to `.fleet-note`: `Verified on native iOS, native Android and Compose Multiplatform; Flutter and React Native untested on a real app.`
  - Retitle the gallery, for example "My other apps, localized by hand: what store screenshots in 5 languages look like", or drop it.
  - Make the hero images zoomable using the same `button.zoom` pattern.

---

## P2: polish

1. **Hero note misaligned.** `p.wrap.fleet-note` (`max-width:760px` plus the `.wrap` auto margins) is centred, so its left edge sits at x=457 while every other block starts at x=432 at 820 wide. It is also 150 px off the heading at 1440. Fix: `.fleet-note{max-width:1120px; padding-inline-end:360px} @media(max-width:1120px){.fleet-note{padding-inline-end:24px}}`.
2. **Dead space in bento card A.** `min-height:340px` with `align-content:space-between` leaves about 160 px empty between its text and the config block at desktop. Use `align-content:start` and a smaller min-height.
3. **Other-script captions have no `lang`.** `日本語`, `العربية`, `Русский`, `한국어` and so on sit in an `lang="en"` page, so screen readers read them with an English voice. Fix: `<figcaption lang="ja">日本語`, and `lang="ar" dir="rtl"` for Arabic.
4. **Form errors are not associated with the field.** The `p.form-error[role=alert]` announces itself, which is fine. The input has `aria-invalid="true"` (correctly) but no `aria-describedby`. Add `aria-describedby="signup-top-error"` and remove it on success. Error text is 14.7 px, in red at 4.71:1 light and 6.73:1 dark, which passes.
5. **Forms without JS or with `forms.js` blocked.** `form#signup-top`, `#signup` and `#stack-*` have no `method`/`action`. Without the script a submit becomes `GET /?email=…&contact_pref=` and puts the address in the URL and in Cloudflare logs. Add `method="post" action="/api/signup"`, or render the forms with `hidden` and unhide them from JS.
6. **No skip link.** There are five tab stops (brand, 3 links, CTA) before the hero input. Add `<a class="sr" href="#main">Skip to content</a>` with an `:focus` reveal.
7. **Print is blank below the fold.** `html.js-reveal .reveal{opacity:0}` is only released by `IntersectionObserver`. Add `@media print{.reveal{opacity:1!important;transform:none!important;filter:none!important}}`. Consider cutting the reveal from 0.9 s with blur to about 0.5 s.
8. **Placeholder contrast.** The UA placeholder is `rgb(117,117,117)`, which is 4.6:1 on the white hero field in light but only about 3.7:1 on the dark surface. Set `::placeholder{color:var(--muted)}` (7.3:1 in dark).
9. **Zoom viewer.** It works (see below) but has no previous/next, so you cannot compare languages without closing and reopening, and Close is 34 px tall (see P1-6). Click-outside and click-image close are good.
10. **Number strip wording.** "108 problems … in 120 store screenshots" does not say whether 108 screenshots failed or 108 individual issues. Use "108 of 120 screenshots flagged" or "108 issues across N screenshots".
11. **Story attribution.** "The first run found a button nobody could reach" does not say whether the run or `check` found it. One clause fixes that.
12. **/alternatives voice and time-bound text.** "Very new: no stars when I looked" ages immediately and reads as a dig. Remove it or date it. The "Checked on 2026-10-02" stamp is good. Keep it.
13. **Metadata on the sub-pages.** `/terms` and `/privacy` have no canonical. None of the three sub-pages has `og:*` or `twitter:*`, so shared links to the comparison page are bare. `www.shotfleet.com` serves 200 with the same ETag (canonical points to the apex, so SEO is safe). A 301 to the apex would be cleaner.
14. **Contact address.** `/terms` and `/privacy` expose `manulorenzop@gmail.com`. Switch to a `hello@shotfleet.com` mailto once that routing is live.
15. **`llms.txt` freshness.** The live file says "Text typed into fields by the flow is not translated", but the repo HEAD commit is "typed text per language". Check that the deployed site matches the build.
16. **Spelling.** "Licence" (British noun) is used throughout the site, but US "license" is the term developers search for. Pick one deliberately.
17. **Security headers (curl, apex and www).**
    - Missing: `Strict-Transport-Security`. Add `max-age=31536000; includeSubDomains` in Cloudflare (SSL/TLS > Edge Certificates).
    - Also absent: `Cross-Origin-Opener-Policy`. `Referrer-Policy`, `Permissions-Policy`, `X-Content-Type-Options` and the CSP are present.
    - CSP is `default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`. No violations or console errors on any page. The only console line was a browser-extension debug message. `'unsafe-inline'` exists only for about 40 `style="--i:N"` / `--d:N` attributes. Replace them with `.ship:nth-child(n){--i:n}` and `.cell:nth-child(n){--d:n}` rules, then drop it.
18. **Caching.** CSS and JS return `max-age=0, must-revalidate`. Images return `max-age=604800`. Fingerprinting file names would allow `immutable` (not urgent at 7 KB CSS).
19. **Scroll region semantics.** The `.fleet` strips are `role="group" tabindex="0"`, which is acceptable for a scroll container. Add a one-line hint for AT: `aria-roledescription="carousel"` is not needed, but `aria-label` already tells the content. No change required.

---

## Measured reference data

**Redirects and status**
- `http://shotfleet.com/` → 301 → https. `http://www.shotfleet.com/` → 301 → `https://www.shotfleet.com/` → 200 (no redirect to the apex).
- `/alternatives/` → 307 → `/alternatives`. `/nope` → 404 with a proper `noindex` page that carries the CSP. `/robots.txt`, `/sitemap.xml` (4 URLs), `/llms.txt` and `/install.sh` → 200.
- All outbound links resolve: manulorenzo.me (→ www), polar.sh/legal/privacy (→ `/privacy-policy`), og.jpg 200.

**Weight and requests**
- First paint set: 11 requests, 171 KB (document 6 KB br, CSS 7 KB br, 5 small scripts, 4 hero images of 35–42 KB each). DCL 432 ms, load 547 ms.
- Everything on the page (hero 7 + bug 1 + Stressi 5 + Cairn 5 = 18 images, 911 KB of JPEG), plus document, CSS and 5 scripts: about 25 requests, roughly 0.93 MB. Cairn (477 KB) loads only after its tab is opened. Full-size zoom images are fetched on click (Cairn 250 KB, Stressi 40 KB).
- Image sizes are right for display. `width`/`height` are set on every image, so there is no layout shift. Images below the hero are `loading="lazy"`.

**Contrast, light then dark**

| Pair | Light | Dark |
|---|---|---|
| Muted text on paper | 5.54 | 7.32 |
| Muted text on surface | 6.05 | 6.68 |
| Link/blue text on paper | 6.80 | 6.91 |
| Button text on blue | 7.43 (hover 9.22) | 7.02 (hover 8.74) |
| `.flag.b` pennant | 7.43 | 7.02 |
| `.flag.r` ("zh · Next is off-screen") | 5.14 | 6.73 |
| Yellow code on dark ribbon `.flag.k b` | 10.48 | 6.50 |
| Error red on paper | 4.71 | 6.73 |
| "Pass" green on its tint | 5.89 | 7.85 |
| Gallery tab selected / unselected | 15.93 / 17.39 | 16.40 / 14.96 |
| Tab sub-label | 6.05 | 6.68 |
| Field border vs paper (needs 3) | 4.15 | 3.82 (vs surface 3.48) |
| Focus ring (blue) vs paper | 6.80 | 6.91 |
| Lowest text on any page | 4.75 (arrow icon on button) | 1.45 (see P1-1) |

All text on /alternatives, /terms and /privacy passes in both themes (lowest 5.54 light, 6.1 dark, including `.yes` green and `.no` grey in the table).

**Heading order and landmarks**
- Home: `h1`, then `h2`×9 (three of them are the bento card titles), then `h3`×2 under "Early access". No skipped levels. Landmarks are `header`, `nav[aria-label=Main]`, `main`, `footer`; groups and regions are labelled. No duplicate IDs.
- /terms has no footer or nav landmark. /privacy has a footer. /alternatives has `h1`, `h2`, `h3` in order.

**Keyboard**
- Focus ring is `:focus-visible` 3 px solid blue, offset 3 px. It was visible on the header CTA. The hero field uses a `:focus-within` 2 px ring on its wrapper.
- Gallery tabs: ArrowRight moved focus and selection to Cairn, with `aria-selected` and `hidden` updated correctly. Tab then goes to the scroll group, then the zoom buttons.
- Zoom viewer: Enter opens a native `<dialog>`, focus lands on Close, the alt text is copied to the enlarged image (1600×1200 natural, 1169×877 shown at 953 px viewport height), and Esc closes it. Focus returns to the same thumbnail ("Enlarge: Cairn on iPad in Japanese").

**Forms (validation only, nothing submitted)**
- Hero field with `notanemail`: message "That doesn't look like an email address. Check it and try again.", `role=alert`, `aria-invalid=true`, focus stays in the field.
- /privacy delete field with `x`: same message and behaviour. Contact form with an empty message: "Write a message first.", focus moves to the textarea.
- Labels are real (`<label for>`; the hero one is visually hidden), `autocomplete="email"` is set, and the honeypot has `tabindex=-1` and is off-screen.

**Reduced motion (CSS read)**
- Entrance animations (`.hero > *`, `.ship .stamp`, `.ship .ribbon`, `.fleet .ship img`) exist only under `prefers-reduced-motion: no-preference`.
- Under `reduce`: `scroll-behavior:auto`, `.reveal` forced visible with no transition, and the zoom animation is off. `reveal.js` also does not add `js-reveal` at all.
- Remaining motion under `reduce`: 0.4 s hover transitions and the button arrow nudge. Both are acceptable.

---

## What is already good (do not undo)

- **Copy discipline.** "Measured on my own apps", "Not for you if…", "Not stated" in the comparison table, "tested on real translation files; not yet run on a real Flutter or React Native app", the Turkish "Next/Advanced" collision example, and the 9 and 15 minute figures with the hardware named. None of this reads as hype.
- **Specific first headline.** "Store screenshots in every language your app ships." plus a strip of real output tells a developer the product in about 3 seconds.
- **The honest bug story with a real screenshot** (Chinese onboarding, red outline, "Next is off-screen" pennant, descriptive alt).
- **Contrast.** Light theme passes everywhere, and dark passes except the three inverted-card items in P1-1. Link, button, pennant, ribbon, tab and error colours all clear AA with margin (table above).
- **Light and dark done properly.** `color-scheme`, per-theme `theme-color` meta, and a `data-theme` override hook that made this audit possible.
- **Native, correct widgets.** Real ARIA tabs with arrow keys, native `<dialog>` with focus return, labelled forms, `role=alert` / `role=status` plus a focusable success box, `[hidden]` honoured.
- **Reduced-motion handling** (above), and nothing hidden without JS.
- **Responsive layout.** No horizontal overflow on any page at 375, 820 or 1440. The mobile hero is clean: stacked field and full-width 48 px button, and the strip peeks to signal scroll.
- **Performance.** 171 KB and 11 requests for the first view, explicit image dimensions, lazy loading below the fold, brotli, no third-party requests, system fonts only.
- **Strict CSP with no violations**, and a 301 from http plus a correct `noindex` 404.
- **Page structure.** Landmarks, heading order, `lang`, canonical and OG on the home page, `llms.txt`, sitemap and robots.
- **Privacy page.** Plain and complete, and it matches what the scripts do (first-party counters, no cookies).
