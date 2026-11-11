"""Google Analytics consent, checked statically (no browser, no network): the site promises that nothing from Google loads and no cookie
is set unless the visitor presses Accept analytics, and the CSP, privacy page and footer links have to agree with ga.js.

Run: python3 -m unittest discover -s tests
"""
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "site/public"
GA = (PUB / "ga.js").read_text()
CSS = (PUB / "site.css").read_text()
PAGES = {p.name: p.read_text() for p in sorted(PUB.glob("*.html"))}
WITH_GA = {n: t for n, t in PAGES.items() if "/ga.js" in t}


def body(name, text=GA):
    """The text of one top-level function inside ga.js's closure (they are indented by two spaces)."""
    m = re.search(rf"\n  function {name}\([^)]*\) \{{(.*?)\n  \}}\n", text, flags=re.S)
    assert m, f"function {name} not found in ga.js"
    return m.group(1)


class Consent(unittest.TestCase):
    def test_the_measurement_id_is_one_constant_at_the_top(self):
        self.assertEqual(re.findall(r'\bGA_ID\s*=', GA), ["GA_ID ="])
        self.assertEqual(len(re.findall(r"""["']G-[A-Z0-9]+["']""", GA)), 1)
        code = [l for l in GA.splitlines() if l.strip() and not l.startswith("//")]
        self.assertRegex(code[0], r'^const GA_ID = "G-[A-Z0-9]{10}";$')  # the one line to change; the placeholder G-XXXXXXXXXX also matches and is then inert (next test)
        self.assertEqual(code[0], 'const GA_ID = "G-6NY43DB3F4";')  # shotfleet property, web stream shotfleet.com
        for name, text in PAGES.items(): self.assertNotRegex(text, r"G-[A-Z0-9]{8,}", f"{name} repeats the measurement id")

    def test_placeholder_id_loads_nothing(self):
        guard = re.search(r"\(function \(\) \{\n  if \(!(/.+/)\.test\(GA_ID\)\) return;\n", GA)
        self.assertTrue(guard, "the first statement of ga.js must be the placeholder guard")
        rx = re.compile(guard.group(1)[1:-1])
        for bad in ("G-XXXXXXXXXX", "G-XXXXXX", "", "UA-12345-1", "G-ab12cd34ef", "G-AB12CD34EF&x=1"): self.assertIsNone(rx.match(bad), bad)
        for good in ("G-AB12CD34EF", "G-1234567890"): self.assertTrue(rx.match(good), good)

    def test_nothing_calls_gtag_before_consent(self):
        # every gtag call and the injection of Google's script live in start(), event() or stop(); event() does nothing unless start() ran
        outside = GA
        for fn in ("start", "stop", "event"): outside = outside.replace(body(fn), "")
        self.assertNotRegex(re.sub(r"function gtag\(\) \{[^\n]*\n", "", outside), r"\bgtag\(", "gtag called outside start/stop/event")
        self.assertNotIn("googletagmanager.com", outside)
        self.assertIn("if (on)", body("event"))
        self.assertEqual(GA.count("googletagmanager.com/gtag/js?id="), 1)
        self.assertEqual(len(re.findall(r"\.src\s*=", GA)), 1, "the only script ever injected is Google's")
        # start() runs only after Accept, or later when "granted" was stored: two call sites, both on a "granted" check
        calls = [l for l in GA.splitlines() if re.search(r"\bstart\(\)", l) and "function start" not in l]
        self.assertEqual(len(calls), 2, calls)
        for l in calls: self.assertIn('"granted"', l)
        self.assertIn('if (saved === "granted") start();', GA)
        self.assertIn('if (value === "granted") start(); else stop();', GA)
        # first visit with nothing stored: only the banner, no call to Google
        self.assertIn("else if (saved === null && usable) ask(false);", GA)

    def test_consent_mode_v2_denies_everything_then_grants_analytics_only(self):
        s = body("start")
        default = re.search(r'gtag\("consent", "default", \{(.*?)\}\)', s).group(1)
        update = re.search(r'gtag\("consent", "update", \{(.*?)\}\)', s).group(1)
        for k in ("ad_storage", "ad_user_data", "ad_personalization", "analytics_storage"): self.assertIn(f'{k}: "denied"', default)
        self.assertEqual(update.strip(), 'analytics_storage: "granted"')
        self.assertLess(s.index('"default"'), s.rindex('"update"')); self.assertLess(s.rindex('"update"'), s.index('"config"'))
        self.assertIn("allow_google_signals: false", s); self.assertIn("allow_ad_personalization_signals: false", s)
        self.assertNotRegex(GA, r"(ad_storage|ad_user_data|ad_personalization)\s*:\s*\"granted\"")
        self.assertNotIn("send_page_view: false", GA)  # GA4 sends page_view on config

    def test_funnel_events_mirror_the_first_party_counter(self):
        first_party = (PUB / "analytics.js").read_text()
        self.assertIn('[["free", "pricing"], ["run", "runs"]]', first_party)
        self.assertIn('closest("a.btn, button.btn")', first_party)
        self.assertIn('[["free", "pricing_view"], ["run", "runs_view"]]', GA)  # same two section ids as analytics.js
        self.assertIn('closest("a.btn, button.btn")', GA)
        for ev in ("cta_click", "pricing_view", "runs_view", "signup"): self.assertIn(f'"{ev}"', GA)
        self.assertIn('document.addEventListener("shotfleet:signup"', GA)
        self.assertIn('new CustomEvent("shotfleet:signup")', (PUB / "forms.js").read_text())

    def test_csp_lines_are_exactly_what_ga4_needs(self):
        line = next(l for l in (PUB / "_headers").read_text().splitlines() if l.strip().startswith("Content-Security-Policy:"))
        csp = {d.split()[0]: d.split()[1:] for d in line.split(":", 1)[1].split(";") if d.strip()}
        self.assertEqual(csp["default-src"], ["'self'"])
        self.assertEqual(csp["script-src"], ["'self'", "https://www.googletagmanager.com"])
        self.assertEqual(csp["connect-src"], ["'self'", "https://*.google-analytics.com", "https://*.analytics.google.com", "https://*.googletagmanager.com"])
        self.assertEqual(csp["img-src"], ["'self'", "https://*.google-analytics.com", "https://*.googletagmanager.com"])
        self.assertEqual(csp["frame-ancestors"], ["'none'"])
        self.assertEqual(csp["base-uri"], ["'none'"]); self.assertEqual(csp["form-action"], ["'self'"])
        for d in ("style-src", "default-src", "frame-ancestors", "base-uri", "form-action"): self.assertFalse([h for h in csp[d] if "google" in h], d)
        allowed = {"https://www.googletagmanager.com", "https://*.google-analytics.com", "https://*.analytics.google.com", "https://*.googletagmanager.com"}
        for h in sum(csp.values(), []):
            if h.startswith("https://"): self.assertIn(h, allowed)  # no other wildcard or host
            self.assertFalse(h in ("*", "https:", "http:", "data:") or "unsafe-eval" in h or h.startswith("http://"), h)
        self.assertNotIn("unsafe-inline", csp["script-src"])
        self.assertNotIn("unsafe-eval", line)

    def test_privacy_page_is_honest_about_analytics(self):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", PAGES["privacy.html"]))
        self.assertIn('id="analytics"', PAGES["privacy.html"])
        for must in ("Analytics (only if you accept)", "_ga", "up to 13 months", "up to 14 months", "The legal basis is your consent",
                     "Analytics settings", "Decline", "Clearing this site's data", "Google acts as my processor",
                     "not linked to you and your IP address is not stored", "first-party counter", "sets no cookie", "Until you accept, nothing is loaded from Google"):
            self.assertIn(must, text)
        self.assertIn('href="https://policies.google.com/privacy"', PAGES["privacy.html"])
        self.assertNotIn("no tracking scripts", text); self.assertNotIn("This site has no cookies", text)  # no longer unconditionally true
        self.assertIn("cookie_expires: 34128000", GA)  # 395 days, the 13 months the page says

    def test_every_page_with_ga_has_the_settings_link_and_the_other_way_round(self):
        self.assertTrue({"index.html", "alternatives.html", "terms.html", "privacy.html"} <= set(WITH_GA))
        for name, text in PAGES.items():
            link = 'id="analytics-settings"' in text
            self.assertEqual(link, name in WITH_GA, f"{name}: ga.js and the footer link must come together")
            if link:
                self.assertIn('<a href="/privacy#analytics" id="analytics-settings">Analytics settings</a>', text, name)
                self.assertLess(text.index('id="analytics-settings"'), text.index("/ga.js"), name)
                self.assertRegex(text, r'<script src="/ga\.js" defer></script>')
        self.assertEqual(GA.count('getElementById("analytics-settings")'), 1)

    def test_the_banner_is_built_by_ga_js_with_two_equal_buttons(self):
        s = body("ask")
        self.assertEqual(len(re.findall(r'\bbutton\("', s)), 2)
        self.assertIn('button("Accept analytics")', s); self.assertIn('button("Decline")', s)
        self.assertEqual(len(re.findall(r'type: "button"', s)), 1)  # one helper makes both
        self.assertNotIn("checked", GA); self.assertNotIn('"Escape"', GA); self.assertNotIn("keydown", GA)  # no pre-ticked box, no way to dismiss without choosing
        self.assertEqual(len(re.findall(r"\.consent-btn\b", CSS)), 2)  # one rule and its hover: no primary/secondary variants
        self.assertRegex(CSS, r"\.consent-btn \{[^}]*min-height: 44px")
        self.assertRegex(CSS, r"\.consent-actions a \{[^}]*min-height: 44px")
        self.assertRegex(CSS, r"\.consent \{[^}]*var\(--surface\)[^}]*var\(--ink\)")  # theme tokens, so light and dark both work
        self.assertIn("localStorage.setItem", body("choose")); self.assertRegex(body("choose"), r"try \{ localStorage\.setItem\(KEY, value\); \} catch")
        self.assertIn("usable = false", GA)  # blocked storage: treated as declined, no forced banner

    def test_no_inline_script_or_handler_was_added(self):
        for name, text in WITH_GA.items():
            for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", re.sub(r"<!--.*?-->", "", text, flags=re.S), flags=re.S):
                if "ld+json" in m.group(1): continue
                self.assertIn("src=", m.group(1), f"{name}: inline script")
                self.assertEqual(m.group(2).strip(), "", name)
            self.assertNotRegex(re.sub(r"<!--.*?-->", "", text, flags=re.S), r"<[^>]+\son\w+\s*=", f"{name}: event handler attribute")
        for bad in (".innerHTML", "eval(", "new Function", "document.write", "setAttribute(\"on"): self.assertNotIn(bad, GA)


if __name__ == "__main__":
    unittest.main()
