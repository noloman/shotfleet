# shotfleet landing page: design and conversion critique (2026-10-02)

Reviewed: the "signal flag" redesign (commit 8b64be3, identical to branch tip 19a0884 apart from og.jpg), at 1440x900, 768 and 375x812, light and dark. Source read: `site/public/index.html`, `site.css`, `forms.js`, `privacy.html`, `404.html`, `terms.html`, `site/worker.js`, `site/draft/alternatives.html`.

Method notes. The worktree was switched to `claude/integrate-on-main` mid-review, which serves the OLD design and has no `site/draft/`. I finished the visual review from a `git archive` of the redesign branch. Live DOM, form and focus tests ran on localhost:8799 before the switch. Headless-Chrome full-page shots were used for the tablet and desktop sections. Phone behaviour was checked only in the real 375 emulation, because headless Chrome will not go below about 500px. The valid-email submit and the success state were NOT exercised, as instructed. The success state is judged from the code only.

## 1. Verdict

1. First impression 8/10. The look is distinctive and clean: pennants, flat colour, one blue. It reads as made by a person with taste, not a template.
2. Clarity 7/10. The headline says what it produces, but not that it is a Mac command-line tool for developers. Someone could mistake it for a caption or mockup service like AppScreens or ButterKit.
3. Trust 6/10. The real bug story, real numbers, plain pricing and refund, and the privacy page are strong. Missing: any way to install or try it, a link to the real app, the hardware behind "9 minutes", and a discoverable licence page.
4. Conversion path 5/10. The only action is an email at the very bottom, about 3,100px down on desktop. "Free to try" is offered for a product that isn't released. The paid and free cards are confusingly ordered.
5. Polish 7.5/10. Spacing, dark mode and the fleet strip are good. Defects: collapsed word spaces in the 800-weight headings, an underlined 404 button, a clipped command, an undefined `--soft` variable on the draft page.
6. Accessibility 7/10. Landmarks, headings, focus rings (3px blue), alt text, reduced motion and the terminal `role="img"` are done well. Weak points: pennant text announced as bare "ja/fr", small tap targets, dark-mode white-on-coral at 2.79:1, an error message that is not tied to its field.
7. Overall: 6.5/10. Visual identity is ahead of the conversion mechanics. The fixes below are mostly small.
8. Biggest lever: let the first screen end in an email field and an honest "what's available now" line.
9. Biggest risk: contradictory claims. The home page says Flutter and React Native work. The draft comparison page says that is untested.
10. Second risk: the home page promises a 14-day refund but the licence terms page is not linked from anywhere.

Scores: first impression 8, clarity 7, trust 6, conversion path 5, polish 7.5, accessibility 7.

## 2. Findings in detail

### First five seconds
- Desktop 1440x900: the H1 is 80px/800, then two lines of subcopy and two buttons. The right half of the hero is empty. The pennants start at y=715, so only about 185px of phone screenshots show above the fold. The signature is visible but the proof (the phones) is not.
- Phone 375x812: the H1, subcopy and two stacked CTAs fill the screen, with the first pennant and phone at the bottom edge. Good.
- The subcopy uses "Maestro flow" before the visitor knows it is a CLI. Skeptical engineers know Maestro, but the page never says "command-line tool for macOS" in the hero.
- "For iOS and Android · by Manuel Lorenzo Parejo" is the only audience line. It does not say "indie developers", "CLI" or "Mac".

### Hierarchy and rhythm
- The type scale is good: H1 clamp(2.5rem, 6.4vw, 5rem), H2 clamp(1.7rem, 3.4vw, 2.5rem), body 17px/1.6, measure 46ch. Sections alternate text left, image right and then flip, with generous padding.
- Heading word spacing: `letter-spacing:-0.04em` at weight 800 eats the word space. "What I keep" reads as "What Ikeep" on the privacy page, and "vs. other" reads as "vs.other" on the comparison page. The H2 "Run it once." is tight too.
- The three split sections look alike. The "Your flow says Next" code card breaks the pattern nicely, then the three-point row feels like a template footer. It is fine, but it is the weakest block.
- The pricing section: the free card is shorter and top-aligned. The paid card form is capped at 460px inside a roughly 610px card, so the right 150px is empty. The command line in the free card is clipped (`--app MyApp.ap`) at 1440.

### Colour and contrast (computed from the CSS, WCAG 2.x)

| Pair | Light | Dark |
|---|---|---|
| ink on paper | 16.1 | 16.4 |
| muted on paper | 5.49 | 7.32 |
| muted on surface | 5.95 | 6.68 |
| blue link on paper | 6.86 | 6.91 |
| button text on blue | 7.43 | 7.02 |
| pass green on pass bg | 5.89 | 7.85 |
| error red on paper | 4.75 | 6.73 |
| terminal text / dim on terminal | 13.8 / 5.5 | 15.5 / 6.2 |
| placeholder (#757575) on paper | 4.25 FAIL | 4.08 FAIL |
| form field border on paper (needs 3:1) | 2.90 FAIL (marginal) | 3.82 |
| yellow pennant, dark text | 10.5 | 10.5 |
| red pennant, white text | 5.14 | **2.79 FAIL** |
| blue pennant text | 7.43 | 7.02 |
| black "k" pennant (`.flag.k`) vs page | 16.1 | **1.08, shape vanishes** |
| yellow pennant shape vs paper | 1.53 (text carries it) | 11.3 |
| terminal block edge vs paper | 16.1 | 1.04 (only a faint border) |

- Dark mode problems: the white "ja" / "ru" / "ZH · STUCK" labels on the coral red (#ff6b5e) fail, and the "fr" / "de" pennants (#0d1b2a) disappear into the #0a121c page, leaving only floating text. The red `outline` on the bug phone and the blue stamps work fine in dark.
- Light mode is clean. The yellow pennant is the only low-contrast shape, but its dark text is readable.
- Body copy in muted grey on paper is legible but a little pale for 17px/400. It passes, so leave it.

### The fleet strip
- It communicates well: the same screen, seven scripts, checkmark stamps, and a "+11" tail card. The staggered offset and the hoist animation feel alive, and animation is gated on `prefers-reduced-motion: no-preference`.
- Touch: it scrolls natively (overflow-x with scroll-snap proximity, hidden scrollbar). The half-cut phone at the right edge is the only affordance, and it is enough. No overflow on the page at 375 (scrollWidth 375).
- Keyboard: Chrome makes the scroller focusable (Tab went brand, nav, CTAs, byline link, then the scroller). Safari does not, so keyboard users there cannot scroll the strip. Add `tabindex="0"`.
- The stamps all look identical, so they claim "checked" without showing anything checked. The one failure (red outline) is a screen later, which is a good contrast, but the link between the two is not drawn.
- Images are 360px wide displayed at 212px CSS, so about 1.7x. That is soft on 2x screens, and the in-screenshot text is unreadable anyway. Total weight is about 330KB, which is fine. Width and height attributes are set, so no layout shift. The last three images are lazy-loaded, correctly.
- The pennant font stack leads with "DIN Condensed" (macOS and iOS only). On Android and Windows it falls back to a non-condensed system font, which weakens the signature on phones. The pennants stretch to the full width of each phone, which looks intentional.

### Trust for a solo, pre-release product
Works: first-person voice; a specific bug with a specific cause and a two-line fix; real figures (534s, 72 screenshots); an honest "isn't released yet"; refund; the free tier; the privacy page that says "I run this on my own"; the comparison draft's "When you should NOT buy" section.

Missing or weak:
- No way to try or inspect it. The "Free to try" card shows a command for a tool nobody can install yet. That is contradictory ("isn't released yet" next to "Free to try").
- No link to the real app (WOD Tracker on the App Store / Play), which would prove the demo is real. The comparison draft calls the same app "CrossfitTracker", which is inconsistent.
- "9 minutes on iOS, 15 on Android, on one Mac": engineers will ask which Mac (chip, RAM) and how many simulators.
- The licence terms page exists (`terms.html`: one licence per developer, CI use, weekly online licence check that works offline 30 days, 14-day refund, Polar as merchant of record) but nothing links to it. The home page footer has only "Privacy". The refund and the weekly phone-home are exactly what a skeptic wants to see before paying.
- No release date or rough ETA, no changelog, no repository or docs link, no "does it upload my app or screenshots anywhere?" answer. If true (the checks run on-device), it is the strongest one-liner available.
- "First 100 people on the list" is unverifiable scarcity. Show a counter or drop the number if the list is small.

### Copy (vague or untrue-sounding)
- "checks every screenshot" in the hero does not say what is checked. The body explains it, but "a copy" ("a wrong language, a copy, or a missing screen") is jargon for "a duplicate".
- "Each image is read back" is vague. If it is OCR, say "read by OCR".
- "Built for native apps; Flutter and React Native work from your translation files (new)." The "(new)" is meaningless, and this conflicts with the comparison draft ("has not been tested on a real app yet"). Pick the true version. Skeptics will also ask about Kotlin Multiplatform and Compose Multiplatform.
- "Made to work with the rest" is a vague heading.
- "Nothing in the app was changed to get them." The next section says there was a two-line fix, which reads as a contradiction. Say "Nothing was added to the app to capture them".
- "$29 for the first 100 people on the list": does joining lock the price? Say it.
- Strong lines, keep as is: "The first run found a button nobody could reach." "It was a two-line fix in my app." "the version you have keeps working".

### Pricing and signup block
- What you get is clear: $49 once, per developer; every language, both platforms, iPad, export; unlimited apps; a year of updates; 14-day refund.
- Emphasis: $49 is huge and the $29 founder price is a 30px pennant. For someone joining the list today, $29 is the offer. Make it primary.
- On tablet and phone the free card comes first, so the signup is pushed down. Put the paid card first on narrow screens.
- The paid card is titled just "shotfleet", which says nothing. Use "Licence" or "Full".
- Tested on the local page:
  - Empty email: the message "That doesn't look like an email address. Check it and try again." is the wrong text for empty. It should say "Enter your email address".
  - Invalid email ("not-an-email"): the same message appears, focus moves to the field, `aria-invalid="true"` is set. That works.
  - The error renders BELOW the button, not next to the field. On a phone it sits under the fold of the card. The input has no `aria-describedby`, and `aria-invalid` is never cleared while the user types.
  - The red field border and the blue focus ring clash.
- Success state (code only): the form hides and a green box takes focus ("You're on the list. I'll email you once, when it's ready."). This is fine for screen readers, but it has no next step, no mention of a confirmation email, and the card collapses (layout shift). Use it to ask for the framework (see section 4).
- Platform select: one more tap for a field that is not needed for launch email. The worker accepts `ios|android|both` and stores anything else as `unknown`.
- Honeypot field named `website`: password managers sometimes fill it, which silently drops a real signup because the worker answers "ok" and discards it. Rename it to something unguessable, with `autocomplete="off"` kept.

### Accessibility
- Landmarks (banner, nav, main, contentinfo) and headings are fine: one H1, then H2 sections, with H3 for the plan titles. The three "point" cards use H2, so they sit at the same level as the section titles. Use H3 under an H2.
- No skip link. The first Tab stop is the brand. It matters little on a one-screen header, so it is optional.
- Pennants: `<span class="flag">ja</span>` is read as the letters "ja". The phone image carries the language in its alt, so the pennant is redundant. Hide it with `aria-hidden="true"` and make the alt say "Japanese", or turn the figure into a `figcaption`.
- Terminal: `role="img"` with a full aria-label and the `pre` hidden is a good pattern. The label and the output agree.
- Tap targets at 375: the nav links are 24px tall, the brand 22px, the byline link 17px, the footer links 17 to 23px. The WCAG 2.2 minimum of 24px is met only just. Buttons (50px) and inputs (48px) are fine. Pad the links to 44px.
- Small text: labels 13.6px/600, `.small` 13.6px, the phone terminal 12.2px. Raise the caption and label to 14px or more.
- Focus: `:focus-visible` is a 3px blue outline with a 3px offset on every control. Good.
- Reduced motion: stamps and pennant animations and smooth scroll are all disabled. Good.
- The alt texts are specific ("WOD Tracker's Train screen in Japanese"). Good.

### Performance
- No third-party requests, no web fonts (zero `document.fonts`), CSS 14KB, JS 3KB deferred, about 330KB of images in total, strict CSP in `_headers`. Excellent for the audience.
- LCP is the H1 text. No CLS from images.
- `og.jpg` is 127KB. Fine.

### Cross-page consistency
- Privacy: coherent and warm, with the same pennant label and the same buttons. The H1 at 80px is heavy for a text page, and the label ("PRIVACY") repeats the page title. The footer says "Home" but has no link to licence terms.
- 404: on-brand. The button text is underlined (`p a` underline rule beats `.btn`) and the page has no footer. In dark it is a periwinkle button with underlined dark text.
- Comparison draft (`site/draft/alternatives.html`): an inline `<style>` block redeclares `.yes/.no/.note` and uses an undefined `var(--soft)`, so the "when not to buy" box has no background and the table header background is missing in that block. The H1 loses the space in "vs. other". "CrossfitTracker" vs "WOD Tracker". Otherwise this page has the best trust copy on the site.
- The old design lives on `claude/integrate-on-main` (no pennants). Make sure the right branch is deployed.

## 3. Prioritised changes (at most 15)

1. [must] Do not promise things that contradict. In `index.html`, the Early access paragraph: replace "Flutter and React Native work from your translation files (new)." with the verified truth. If untested: "Built and tested on native apps. Flutter and React Native read your translation files but are untested on a real app. Kotlin and Compose Multiplatform too." Keep the draft page consistent.
2. [must] Fix "Free to try" vs "isn't released yet". Rename the card "Free at launch" with the copy "Checking screenshots (`shotfleet check`) and capturing 2 languages will stay free. Install instructions arrive with the launch email." Or ship `install.sh` (it exists on the other branch) and show the real install line.
3. [must] Link the terms page and state the phone-home. Footer: `<a href="/terms">Licence and refunds</a> · <a href="/privacy">Privacy</a>`. In the price card add under the list: "One licence check a week, works offline for 30 days. [Terms]".
4. [must] Move the email form into the hero. Replace the two hero buttons with: `<form class="hero-form">` containing an email input and "Get early access", with the microcopy "$29 for the first 100. One email at launch, nothing else." under it. Keep "See a real run" as a text link. This removes the 3,100px scroll to the only goal.
5. [must] Fix the dark-mode pennants in `site.css`. In the dark block add `.flag.r{background:#ff6b5e;color:#1a0b09}` (contrast about 7:1) and make `.flag.k` visible: `.flag.k{background:#ffffff;color:#0d1b2a}` for dark only, or give every pennant `box-shadow: inset 0 0 0 1.5px var(--line)`. The terminal edge in dark is nearly invisible too: use `border-color: #2d4258`.
6. [must] Make the headline say what it is. Add a pennant above the H1: `<p class="label">CLI for macOS · iOS + Android</p>` (the `.label` class already exists) and change the subcopy to "A Mac command-line tool. Write one Maestro flow in English; it runs in every language you ship, in parallel, and checks each screenshot before it reaches the stores."
7. [must] Error and empty-state microcopy in `forms.js`. If the field is empty: "Enter your email address." If invalid: "That email address looks wrong. Check it and try again." Render the error directly under the input (move `<p class="form-error">` inside the `.field` before the select) and add `aria-describedby="signup-error"` with a matching id. Remove `aria-invalid` on the next `input` event. Rename the honeypot from `website` to e.g. `contact_url`, or stop the autofill by also using `autocomplete="off"` plus `data-lpignore`.
8. [should] Fix heading word spacing in `site.css`: `h1{letter-spacing:-0.03em;word-spacing:0.06em}` and `h2{letter-spacing:-0.025em;word-spacing:0.05em}`. This restores "vs. other" and "What I keep".
9. [should] Promote the founder price: in `.amount` show `$29` large with "founder price, first 100" and `<s>$49</s>` beside it, then "then $49". Make the paid card first on mobile with `.plans .main{order:-1}` under 820px. Rename the card from "shotfleet" to "Licence".
10. [should] Add proof under the numbers. In the "Run it once" copy: "on one MacBook Pro (M-series, N GB)". Link "my app, WOD Tracker" to its store page. Add one line near the hero: "Runs on your Mac. Your app and screenshots are not uploaded" if that is true (check the licence call and the OCR path first).
11. [should] Pennants for assistive tech and a11y basics. Add `aria-hidden="true"` to every `.flag` in the fleet and make the alts say "Japanese". Add `tabindex="0"` to `.fleet`. Raise tap targets: `.top nav a,.brand,footer a,.by a{display:inline-block;padding-block:10px}`. Raise `.small,label{font-size:0.875rem}`. Placeholder: `::placeholder{color:var(--muted)}`. Field border `--field:#7a8ba0` (3.4:1).
12. [should] Replace the "Platform" select with a one-tap stack question (see section 4).
13. [nice] 404 fix: `.page .btn{text-decoration:none}` (or use `p a:not(.btn)` in the underline rule) and add the footer. On the draft page, delete the inline style block, or define `--soft: color-mix(in srgb,var(--ink) 5%,transparent)`.
14. [nice] Hero balance on wide screens: shrink the top padding (`clamp(24px,4vw,56px)`) so the phones reach the fold at 1440x900, or place the first three phones in a hero right column. Serve the phone images at 480px wide for sharper retina. Add `font-stretch:condensed` to `.flag` so Android keeps a narrow pennant label where "DIN Condensed" is missing.
15. [nice] Add a short "Who this is not for" box on the home page, lifted from the comparison draft (no Mac, no Maestro, already happy with fastlane snapshot). It is the single most credible block you have. Also add a release estimate ("aiming for November") and a link to the comparison page when it is published.

## 4. Signup: platform and framework in one short question

The select "iOS and Android / iOS only / Android only" adds a tap and answers a question the launch email does not need. Replace it with one optional question that captures both platform and framework:

```html
<div class="field">
  <label for="stack">You build with <span class="opt">(optional)</span></label>
  <select id="stack" name="stack">
    <option value="">Choose one</option>
    <option value="native-both">Swift and Kotlin (two native apps)</option>
    <option value="native-ios">Swift / SwiftUI, iOS only</option>
    <option value="native-android">Kotlin / Compose, Android only</option>
    <option value="react-native">React Native</option>
    <option value="flutter">Flutter</option>
    <option value="kmp">Kotlin Multiplatform / Compose Multiplatform</option>
    <option value="maui">.NET MAUI</option>
    <option value="unity">Unity</option>
    <option value="other">Other</option>
  </select>
</div>
```

- One tap, nine honest options, and the platform is derived from the choice. Cross-platform frameworks default to both. Native split three ways because it matters for the Android emulator work.
- Alternative if you prefer no dropdown: pill buttons (radio-style `<input type="radio">` styled as chips, 44px high, in a `fieldset` with `legend`). They show all options at once and need no click to open, so they convert better on a phone.
- Make the whole thing a second step after the email is accepted. Show the success box first ("You're on the list."), then the same box asks "One more thing, optional: what do you build with?" and PATCHes the entry. This puts zero extra friction in front of the email and still collects the data from the people who care. It needs a small worker route (`/api/signup/stack`) keyed by the email.
- Backend: the worker's `platform` allow-list is `["ios","android","both"]`. Add `stack` to the body and store `stack` plus a derived `platform`. Update the privacy page's list item "Which stores you said you ship on" to "What you said you build with".

## 5. Already the best: do not touch

1. The pennant system: the swallowtail labels above each phone, the same shape reused for list bullets, the `$29` tag, the page labels and the "ZH · STUCK" flag on the broken screenshot. It is the one memorable idea on the page and it is consistent across pages. Keep the flat colours and the single blue. (Only fix the dark-mode contrast, change 5.)
2. The "first run found a button nobody could reach" section: the real Chinese Android screenshot with a red outline and a red flag, the specific cause, and "It was a two-line fix in my app." This is the page's most convincing proof and its best contrast with the blue "checked" stamps. Do not smooth or shorten it.
3. The honest, plain voice and the zero-third-party stance: "shotfleet isn't released yet", "the version you have keeps working", no cookies or analytics, system fonts, strict CSP, 330KB total, dark theme that follows the system. For skeptical engineers this restraint is the brand. Do not add a web font, tracker, chat widget, countdown timer or testimonials carousel.
