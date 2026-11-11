"""tools/golive/smoke.sh (the live-site check run after every deploy) and site/public/install.sh, against a local fake server.
Nothing here touches the network, Cloudflare, git remotes or the real PATH. Stdlib only.

Run: python3 -m unittest discover -s tests
"""
import hashlib, io, os, shutil, stat, subprocess, tarfile, tempfile, threading, unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "site/public"
SMOKE = ROOT / "tools/golive/smoke.sh"
INSTALL = PUB / "install.sh"
ARCHIVE = "shotfleet-macos-arm64.tar.gz"
CLEAN = "/usr/bin:/bin:/usr/sbin:/sbin"
APPLE_SILICON = os.uname().sysname == "Darwin" and os.uname().machine == "arm64"
needs_mac = unittest.skipUnless(os.uname().sysname == "Darwin", "the release scripts use macOS tools (BSD sed -i, shasum)")


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
    """Shared: the site tree being served."""
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.sale_pub = PUB
        cls.sale_html = (PUB / "index.html").read_text()

    @classmethod
    def tearDownClass(cls): cls._tmp.cleanup()

    def site(self, index_html=None, **kw):
        d = tempfile.mkdtemp(dir=self.tmp)
        s = Site(d, self.sale_html if index_html is None else index_html, base_pub=self.sale_pub, **kw)
        self.addCleanup(s.close)
        return s

    def smoke(self, site, *args):
        return run(["env", "-i", f"HOME={self.tmp}", f"PATH={CLEAN}", "sh", str(SMOKE), site.url, *args])


class Smoke(Fixture):
    @needs_mac
    def test_a_good_site_passes_from_a_clean_environment(self):
        s = self.site(); r = self.smoke(s)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for line in ("/ is 200", "/install.sh is 200", "/download/VERSION is 200", f"/download/{ARCHIVE}.sha256 is 200", "/robots.txt is 200",
                     "/sitemap.xml is 200", "CSP header present", "archive matches its .sha256", "install.sh's checksum logic accepts the served archive",
                     "SKIP  http to https redirect", "0 failed"):
            self.assertIn(line, r.stdout)
        self.assertIn("home page links to GitHub Sponsors", r.stdout)
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

    def test_a_page_that_sells_something_again_fails(self):
        self.assertFails(self.site(self.sale_html.replace("<h1>", '<a href="https://example.gumroad.com/l/x">Buy shotfleet</a><h1>', 1)), "still contains: gumroad.com")

    def test_a_page_without_the_sponsors_link_fails(self):
        self.assertFails(self.site(self.sale_html.replace("https://github.com/sponsors/noloman", "https://example.com")), "no link to https://github.com/sponsors/noloman")

    def test_a_missing_release_fails(self):
        s = self.site(); (s.root / "download" / "VERSION").unlink()
        self.assertFails(s, "/download/VERSION is 404")

    @unittest.skipUnless(APPLE_SILICON, "the program only runs on an Apple silicon Mac")
    def test_a_program_that_disagrees_with_VERSION_fails(self):
        self.assertFails(self.site(version="9.9.9", file_version="9.9.8"), "VERSION says 9.9.9")


class InstallScript(Fixture):
    """install.sh against the fake server. The refusal cases stop before anything is installed; the link cases install the fake program into a temp HOME."""
    def install(self, site, uname_s="Darwin", uname_m="arm64", home_name="home"):
        shim = self.tmp / f"shim-{uname_s}-{uname_m}"; shim.mkdir(exist_ok=True)
        (shim / "uname").write_text(f'#!/bin/sh\ncase "$1" in -s) echo {uname_s};; -m) echo {uname_m};; esac\n'); (shim / "uname").chmod(0o755)
        home = self.tmp / home_name; home.mkdir(exist_ok=True)
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

    def test_a_test_install_with_another_home_links_only_inside_that_home(self):
        """2026-10-06: a temp-HOME install overwrote /opt/homebrew/bin/shotfleet for the real user. Now it stays in $HOME/.local/bin."""
        brew = Path("/opt/homebrew/bin/shotfleet")
        before = os.readlink(brew) if brew.is_symlink() else None
        try:
            r, home = self.install(self.site(), home_name="home-link")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((home / ".local/bin/shotfleet").is_symlink(), r.stdout)
            self.assertIn(f"to {home}/.local/bin", r.stdout)
            self.assertEqual(os.readlink(brew) if brew.is_symlink() else None, before)
        finally:  # never leave the real Homebrew link changed, whatever happened above
            now = os.readlink(brew) if brew.is_symlink() else None
            if now != before and now and str(self.tmp) in now:
                brew.unlink()
                if before: brew.symlink_to(before)

    def test_shotfleet_bin_dir_picks_the_link_folder(self):
        site = self.site(); shim = self.tmp / "shim-Darwin-arm64"; shim.mkdir(exist_ok=True)
        (shim / "uname").write_text('#!/bin/sh\ncase "$1" in -s) echo Darwin;; -m) echo arm64;; esac\n'); (shim / "uname").chmod(0o755)
        home = self.tmp / "home2"; home.mkdir(exist_ok=True); bindir = self.tmp / "mybin"
        r = run(["env", "-i", f"HOME={home}", f"PATH={shim}:{CLEAN}", f"SHOTFLEET_BASE={site.url}/download", f"SHOTFLEET_BIN_DIR={bindir}", "sh", str(INSTALL)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((bindir / "shotfleet").is_symlink())

    def test_smoke_relies_on_the_install_line_it_stops_at(self):
        self.assertRegex((INSTALL).read_text(), r"(?m)^tar -xzf ")  # tools/golive/smoke.sh runs install.sh up to this line


if __name__ == "__main__":
    unittest.main()
