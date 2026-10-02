"""The go-live rehearsal: packaging/go-live.sh --dry-run and tools/golive/smoke.sh, against a local fake server.
Nothing here touches the network, Cloudflare, Polar, git remotes or the real PATH. Stdlib only.

Run: python3 -m unittest discover -s tests
"""
import hashlib, io, os, shutil, stat, subprocess, tarfile, tempfile, threading, unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "site/public"
GOLIVE = ROOT / "packaging/go-live.sh"
SMOKE = ROOT / "tools/golive/smoke.sh"
INSTALL = PUB / "install.sh"
LIVE = "<!-- WAITLIST -->" not in (PUB / "index.html").read_text()  # go-live.sh already ran for real
CHECKOUT = "https://polar.sh/checkout/test-link"
ORG = "16188b30-3a8a-4fdc-8282-d350ae6ec1bb"
ARCHIVE = "shotfleet-macos-arm64.tar.gz"
CLEAN = "/usr/bin:/bin:/usr/sbin:/sbin"
APPLE_SILICON = os.uname().sysname == "Darwin" and os.uname().machine == "arm64"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def csp():
    line = next(l for l in (PUB / "_headers").read_text().splitlines() if l.strip().startswith("Content-Security-Policy:"))
    return line.split(":", 1)[1].strip()


def fake_archive(version):
    """A tar.gz shaped like the release: shotfleet/shotfleet, a program that reports its version."""
    buf = io.BytesIO()
    body = f'#!/bin/sh\necho "shotfleet {version}"\n'.encode()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("shotfleet/shotfleet"); info.size = len(body); info.mode = 0o755
        tar.addfile(info, io.BytesIO(body))
    return buf.getvalue()


class Site:
    """A fake shotfleet.com: site/public plus /download, with the CSP header from _headers and Cloudflare's /terms -> terms.html."""
    def __init__(self, tmp, index_html, base_pub=PUB, version="9.9.9", file_version=None, sum_override=None, with_csp=True):
        self.root = Path(tmp) / "site"
        shutil.copytree(base_pub, self.root, ignore=shutil.ignore_patterns("download", "img", "*.jpg"))
        (self.root / "index.html").write_text(index_html)
        dl = self.root / "download"; dl.mkdir()
        data = fake_archive(file_version or version)
        (dl / ARCHIVE).write_bytes(data)
        (dl / (ARCHIVE + ".sha256")).write_text(f"{sum_override or hashlib.sha256(data).hexdigest()}  {ARCHIVE}\n")
        (dl / "VERSION").write_text(version + "\n")
        policy = csp() if with_csp else None

        class Handler(SimpleHTTPRequestHandler):
            def translate_path(self, path):
                p = super().translate_path(path)
                return p + ".html" if not os.path.exists(p) and os.path.exists(p + ".html") else p
            def end_headers(self):
                if policy: self.send_header("Content-Security-Policy", policy)
                super().end_headers()
            def log_message(self, *a): pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(self.root)))
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown(); self.server.server_close()


class Fixture(unittest.TestCase):
    """Shared: the transformed page (a dry run's copy, or the tree itself once the site is live)."""
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.sale_checkout = None if LIVE else CHECKOUT
        cls.sale_pub = PUB
        cls.dry = None
        if not LIVE:
            copy = cls.tmp / "copy"
            cls.dry = run(["sh", str(GOLIVE), "--dry-run", CHECKOUT], env={**os.environ, "POLAR_ORG_ID": ORG, "GOLIVE_DRYRUN_DIR": str(copy),
                          "GOLIVE_SKIP_TESTS": "1", "GOLIVE_SKIP_MACHINE_CHECKS": "1"})
            cls.sale_pub = copy / "site/public"
        cls.sale_html = (cls.sale_pub / "index.html").read_text()

    @classmethod
    def tearDownClass(cls): cls._tmp.cleanup()

    def site(self, index_html=None, **kw):
        d = tempfile.mkdtemp(dir=self.tmp)
        s = Site(d, self.sale_html if index_html is None else index_html, base_pub=self.sale_pub, **kw)
        self.addCleanup(s.close)
        return s

    def smoke(self, site, *args):
        return run(["env", "-i", f"HOME={self.tmp}", f"PATH={CLEAN}", "sh", str(SMOKE), site.url, *args])


@unittest.skipIf(LIVE, "the site is already live; there is nothing left to rehearse")
class DryRun(Fixture):
    def test_the_dry_run_passes_and_says_what_it_would_do(self):
        self.assertEqual(self.dry.returncode, 0, self.dry.stdout + self.dry.stderr)
        out = self.dry.stdout
        for line in ("dry run clean", "would: 1. sed POLAR_ORG_ID", "would: 3. packaging/release.sh", "would: 5. (cd site && npx wrangler deploy)",
                     "would: 6. commit \"Site: sale open\" and git push", "smoke.sh https://shotfleet.com"):
            self.assertIn(line, out)
        self.assertIn(f'+POLAR_ORG_ID = "{ORG}"', out)  # the diff summary shows the one-line change to the program
        self.assertIn("site/public/index.html", out)

    def test_the_copy_has_the_checkout_link_and_no_markers_and_the_static_founder_text(self):
        live = self.sale_html
        self.assertGreaterEqual(live.count(f'href="{CHECKOUT}"'), 3)
        for marker in ("WAITLIST", "SALE", "@CHECKOUT@", "@GUMROAD@", "data-signup", 'id="signup', "Early access"): self.assertNotIn(marker, live)
        self.assertIn("first 100 buyers", live)  # honest text: no counter number exists, nothing feeds one (LAUNCH.md open item)
        self.assertNotRegex(live.lower(), r"\d+ (of 100|left|remaining)|spots? left")
        self.assertIn(f'POLAR_ORG_ID = "{ORG}"', (self.sale_pub.parent.parent / "shotfleet.py").read_text())

    def test_the_real_tree_is_untouched_and_nothing_was_deployed_or_pushed(self):
        before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ("shotfleet.py", "site/public/index.html")}
        head = run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout
        bin_, log = self.tmp / "bin", self.tmp / "calls.log"; bin_.mkdir(exist_ok=True)
        for tool in ("npx", "xcrun", "codesign", "swiftc"):  # anything the real run would use for the outside world
            f = bin_ / tool; f.write_text(f'#!/bin/sh\necho "{tool} $*" >> "{log}"\n'); f.chmod(f.stat().st_mode | stat.S_IEXEC)
        r = run(["sh", str(GOLIVE), "--dry-run", CHECKOUT], env={**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "POLAR_ORG_ID": ORG,
                "GOLIVE_SKIP_TESTS": "1", "GOLIVE_SKIP_MACHINE_CHECKS": "1"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(log.exists(), log.read_text() if log.exists() else "")
        self.assertEqual(before, {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in before})
        self.assertEqual(head, run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout)

    def test_bad_inputs_fail_the_dry_run(self):
        env = {**os.environ, "GOLIVE_SKIP_TESTS": "1", "GOLIVE_SKIP_MACHINE_CHECKS": "1"}
        for args, org, want in ((["http://polar.sh/x"], ORG, "must start with https://"), ([CHECKOUT], "not-a-uuid", "not a UUID"),
                                ([CHECKOUT, "https://gumroad.com/l/x"], ORG, "needs the product ID")):
            with self.subTest(args=args, org=org):
                r = run(["sh", str(GOLIVE), "--dry-run", *args], env={**env, "POLAR_ORG_ID": org})
                self.assertEqual(r.returncode, 1, r.stdout); self.assertIn(want, r.stdout); self.assertIn("DRY RUN FOUND PROBLEMS", r.stdout)

    def test_a_missing_checkout_link_is_a_usage_error_in_both_modes(self):
        for args in ([], ["--dry-run"]):
            r = run(["sh", str(GOLIVE), *args]); self.assertNotEqual(r.returncode, 0); self.assertIn("usage", r.stderr)


class Smoke(Fixture):
    def test_a_good_site_passes_from_a_clean_environment(self):
        s = self.site(); r = self.smoke(s, *([self.sale_checkout] if self.sale_checkout else []))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for line in ("/ is 200", "/install.sh is 200", "/download/VERSION is 200", f"/download/{ARCHIVE}.sha256 is 200", "/robots.txt is 200",
                     "/sitemap.xml is 200", "CSP header present", "archive matches its .sha256", "install.sh's checksum logic accepts the served archive",
                     "SKIP  http to https redirect", "0 failed"):
            self.assertIn(line, r.stdout)
        if self.sale_checkout: self.assertIn(f"checkout link {CHECKOUT} in", r.stdout)
        if APPLE_SILICON: self.assertIn("unpacked program says 'shotfleet 9.9.9'", r.stdout)
        self.assertFalse((self.tmp / "Library").exists())  # nothing was installed under HOME either

    def assertFails(self, site, message, *args):
        r = self.smoke(site, *args)
        self.assertEqual(r.returncode, 1, r.stdout); self.assertIn("FAIL", r.stdout); self.assertIn(message, r.stdout)

    def test_a_wrong_checksum_file_fails(self):
        self.assertFails(self.site(sum_override="0" * 64), "does NOT match")

    def test_a_missing_csp_header_fails(self):
        self.assertFails(self.site(with_csp=False), "CSP header missing")

    def test_a_page_that_still_has_the_waitlist_fails(self):
        self.assertFails(self.site(self.sale_html.replace("<h1>", '<h1 data-signup>', 1)), "still contains: data-signup")

    def test_a_page_without_the_expected_checkout_link_fails(self):
        self.assertFails(self.site(), "checkout link https://polar.sh/checkout/other in 0 places", "https://polar.sh/checkout/other")

    def test_a_counter_number_that_nothing_feeds_fails(self):
        self.assertFails(self.site(self.sale_html.replace("first 100 buyers", "first 100 buyers (37 of 100 left)", 1)), "counter number")

    def test_a_missing_release_fails(self):
        s = self.site(); (s.root / "download" / "VERSION").unlink()
        self.assertFails(s, "/download/VERSION is 404")

    @unittest.skipUnless(APPLE_SILICON, "the program only runs on an Apple silicon Mac")
    def test_a_program_that_disagrees_with_VERSION_fails(self):
        self.assertFails(self.site(version="9.9.9", file_version="9.9.8"), "VERSION says 9.9.9")


@unittest.skipUnless(shutil.which("shasum"), "install.sh needs shasum")
class InstallScript(Fixture):
    """install.sh against the fake server. Every case here stops before anything is installed (checksum or machine refusal)."""
    def install(self, site, uname_s="Darwin", uname_m="arm64"):
        shim = self.tmp / f"shim-{uname_s}-{uname_m}"; shim.mkdir(exist_ok=True)
        (shim / "uname").write_text(f'#!/bin/sh\ncase "$1" in -s) echo {uname_s};; -m) echo {uname_m};; esac\n'); (shim / "uname").chmod(0o755)
        home = self.tmp / "home"; home.mkdir(exist_ok=True)
        return run(["env", "-i", f"HOME={home}", f"PATH={shim}:{CLEAN}", f"SHOTFLEET_BASE={site.url}/download", "sh", str(INSTALL)]), home

    def test_install_sh_refuses_a_wrong_checksum_and_installs_nothing(self):
        r, home = self.install(self.site(sum_override="0" * 64))
        self.assertEqual(r.returncode, 1); self.assertIn("checksum mismatch", r.stderr)
        self.assertFalse((home / "Library").exists())

    def test_install_sh_refuses_an_intel_mac(self):
        r, home = self.install(self.site(), uname_m="x86_64")
        self.assertEqual(r.returncode, 1); self.assertIn("Apple silicon", r.stderr)
        self.assertFalse((home / "Library").exists())

    def test_install_sh_refuses_linux(self):
        r, _ = self.install(self.site(), uname_s="Linux")
        self.assertEqual(r.returncode, 1); self.assertIn("macOS only", r.stderr)

    def test_smoke_relies_on_the_install_line_it_stops_at(self):
        self.assertRegex((INSTALL).read_text(), r"(?m)^tar -xzf ")  # tools/golive/smoke.sh runs install.sh up to this line


if __name__ == "__main__":
    unittest.main()
