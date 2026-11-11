"""packaging/publish.sh, packaging/preflight.sh and tools/verify-release.sh against fake artifacts in a temp dir. No network except 127.0.0.1,
no Cloudflare (a fake wrangler records its calls), nothing signed. The real deploy is never run by these tests.

Run: python3 -m unittest tests.test_release_scripts
"""
import hashlib, os, shutil, subprocess, sys, tempfile, threading, unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISH, PREFLIGHT, VERIFY = ROOT / "packaging/publish.sh", ROOT / "packaging/preflight.sh", ROOT / "tools/verify-release.sh"
OLD, NEW = "11111111-2222-3333-4444-555555555555", "99999999-8888-7777-6666-555555555555"

FAKE_WRANGLER = r"""#!/bin/sh
# fake wrangler: state in $FAKE_DIR, every call logged in $FAKE_DIR/calls. deploy publishes ./public/download and install.sh into $FAKE_DIR/serve.
echo "$*" >> "$FAKE_DIR/calls"
[ -f "$FAKE_DIR/live" ] || echo "$OLD" > "$FAKE_DIR/live"
case "$1" in
  deployments) echo "Created:     now"; echo "Version(s):  (100%) $(cat "$FAKE_DIR/live")" ;;
  deploy) echo "$NEW" > "$FAKE_DIR/live"; rm -rf "$FAKE_DIR/serve"; mkdir -p "$FAKE_DIR/serve"; cp -R public/download "$FAKE_DIR/serve/download"; cp public/install.sh "$FAKE_DIR/serve/"
          [ -z "$FAKE_CORRUPT" ] || echo corrupt >> "$FAKE_DIR/serve/download/shotfleet-macos-arm64.tar.gz"
          [ -z "$FAKE_CORRUPT_OLD" ] || echo corrupt >> "$FAKE_DIR/serve/download/9.9.8/shotfleet-macos-arm64.tar.gz"
          echo "Current Version ID: $NEW" ;;
  rollback) echo "$2" > "$FAKE_DIR/live"; echo "rolled back" ;;
esac
"""


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(cmd, env=None, cwd=None, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, cwd=cwd, timeout=120, env={**os.environ, **(env or {})}, **kw)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tree, self.art, self.fake, self.rel = (self.tmp / n for n in ("tree", "art", "fake", "release"))
        for d in (self.tree / "site/public", self.tree / "tools/golive", self.art, self.fake):
            d.mkdir(parents=True)
        (self.tree / "shotfleet.py").write_text('VERSION = "9.9.9"\n')
        (self.tree / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n- x\n\n## 9.9.9 (2026-01-01)\n- y\n")
        (self.tree / "site/public/docs.html").write_text("<p>Last checked against version 9.9.9 on 2026-01-01.</p>\n")
        (self.tree / "site/wrangler.toml").write_text('name = "fake"\n')
        shutil.copy(ROOT / "site/wrangler.staging.toml", self.tree / "site/wrangler.staging.toml")
        shutil.copy(ROOT / "site/public/install.sh", self.tree / "site/public/install.sh")
        shutil.copy(ROOT / "tools/golive/smoke.sh", self.tree / "tools/golive/smoke.sh")
        for c in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"]):
            subprocess.run(["/usr/bin/git", "-C", str(self.tree), *c], check=True, capture_output=True)
        pkg = self.tmp / "build/shotfleet"; pkg.mkdir(parents=True)
        (pkg / "shotfleet").write_text("#!/bin/sh\necho shotfleet 9.9.9\n"); (pkg / "shotfleet").chmod(0o755)
        self.tar, self.pkg = self.art / "shotfleet-9.9.9-macos-arm64.tar.gz", self.art / "shotfleet-9.9.9-macos-arm64.pkg"
        subprocess.run(["tar", "-C", str(self.tmp / "build"), "-czf", str(self.tar), "shotfleet"], check=True)
        self.pkg.write_bytes(os.urandom(2048))
        self.manifest = self.tmp / "manifest.txt"
        self.manifest.write_text(run(["sh", PUBLISH, "--make-manifest", "9.9.9", self.tar, self.pkg]).stdout)
        (self.fake / "wrangler.sh").write_text(FAKE_WRANGLER)
        self.env = {"WRANGLER": f"sh {self.fake}/wrangler.sh", "FAKE_DIR": str(self.fake), "OLD": OLD, "NEW": NEW, "PUBLISH_ALLOW_BRANCH": "1",
                    "SHOTFLEET_RELEASE_DIR": str(self.rel), "SHOTFLEET_ALLOW_TMP_DIR": "1", "PUBLISH_BASE": "http://127.0.0.1:9",
                    "PUBLISH_SETTLE": "0", "PUBLISH_RETRY": "0", "PUBLISH_SMOKE": "/usr/bin/true"}

    def publish(self, *extra, env=None, manifest=None):
        return run(["sh", PUBLISH, *extra, "--manifest", manifest or self.manifest, "--artifacts", self.art, "--tree", self.tree], env={**self.env, **(env or {})})

    def calls(self):
        f = self.fake / "calls"
        return f.read_text().splitlines() if f.exists() else []

    def serve(self):
        (self.fake / "serve").mkdir(exist_ok=True)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Quiet, directory=str(self.fake / "serve")))
        # the server reads whatever directory exists now; the fake deploy replaces it, so serve from a path that is re-resolved on each request
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.env["PUBLISH_BASE"] = f"http://127.0.0.1:{srv.server_address[1]}"


class Syntax(unittest.TestCase):
    def test_sh_n_and_help(self):
        for s in (PUBLISH, PREFLIGHT, VERIFY):
            with self.subTest(script=s.name):
                self.assertEqual(run(["sh", "-n", s]).returncode, 0)
                r = run(["sh", s, "--help"])
                self.assertEqual(r.returncode, 0)
                self.assertTrue(r.stdout.strip(), "--help prints something")
                self.assertNotIn("set -eu", r.stdout)  # the help stops at the end of the header comment

    def test_unknown_argument_and_missing_arguments_are_usage_errors(self):
        for s in (PUBLISH, PREFLIGHT, VERIFY):
            self.assertEqual(run(["sh", s, "--bogus"]).returncode, 2)
        self.assertEqual(run(["sh", PUBLISH]).returncode, 2)
        self.assertEqual(run(["sh", VERIFY]).returncode, 2)


class DryRun(Fixture):
    def test_dry_run_passes_checks_prints_the_plan_and_touches_nothing(self):
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for line in ("manifest version 9.9.9", "VERSION agrees", f"rollback target): {OLD}", "would: rm -rf", "would: archive the staged bytes", "would: write the rollback id",
                     "deploy", "would, on any failure:", "dry run clean"):
            self.assertIn(line, r.stdout)
        self.assertFalse((self.tree / "site/public/download").exists())
        self.assertFalse(self.rel.exists())
        self.assertEqual(self.calls(), ["deployments list"])  # read-only: no deploy, no rollback

    def test_real_tree_version_extractors_work_on_the_real_files(self):
        # the three places publish.sh reads, on this repo itself: only the checks that read the files, with a manifest of the right version
        version = [l.split('"')[1] for l in (ROOT / "shotfleet.py").read_text().splitlines() if l.startswith("VERSION = ")][0]
        art = self.tmp / "real"; art.mkdir()
        for n in (f"shotfleet-{version}-macos-arm64.tar.gz", f"shotfleet-{version}-macos-arm64.pkg"):
            (art / n).write_bytes(n.encode())
        m = self.tmp / "real.txt"; m.write_text(run(["sh", PUBLISH, "--make-manifest", version, *sorted(art.iterdir())]).stdout)
        r = run(["sh", PUBLISH, "--dry-run", "--manifest", m, "--artifacts", art, "--tree", ROOT], env=self.env)
        self.assertIn(f"all say {version}", r.stdout)

    def test_refuses_a_file_that_is_not_the_tested_one(self):
        good = self.tar.read_bytes()
        self.tar.write_bytes(good + b"x")
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("bytes, the manifest says", r.stdout)
        self.tar.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))  # same size again, wrong content
        self.assertIn("does not match its manifest sha256", self.publish("--dry-run").stdout)

    def test_refuses_a_manifest_version_that_is_not_strictly_digits(self):  # security review S7 (2026-10-07): the case glob let `9.9.9;x` through
        for bad in ("9.9.9;touch${IFS}x", "9.9.9$(id)", "9.9.9.1", "9..9"):
            with self.subTest(version=bad):
                m = self.tmp / "bad-manifest.txt"
                m.write_text(self.manifest.read_text().replace("version 9.9.9", f"version {bad}", 1))
                r = self.publish("--dry-run", manifest=m)
                self.assertEqual(r.returncode, 1)
                self.assertIn("manifest has no 'version X.Y.Z' line", r.stdout)
                self.assertNotIn(f"manifest version {bad}", r.stdout)

    def test_refuses_a_version_that_disagrees(self):
        (self.tree / "shotfleet.py").write_text('VERSION = "9.9.8"\n')
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "y"], check=True)
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("VERSION disagrees", r.stdout)
        self.assertIn("shotfleet.py '9.9.8'", r.stdout)

    def test_refuses_a_changelog_or_docs_page_with_another_version(self):
        (self.tree / "site/public/docs.html").write_text("<p>Last checked against version 9.9.8 on 2026-01-01.</p>\n")
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "y"], check=True)
        self.assertIn("docs page '9.9.8'", self.publish("--dry-run").stdout)

    def test_refuses_a_changelog_whose_top_release_heading_is_still_the_placeholder(self):
        (self.tree / "CHANGELOG.md").write_text("# Changelog\n\n## 9.9.9 (<!-- RELEASE_DATE -->)\n- x\n\n## 9.9.8 (2026-01-01)\n- y\n")
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "y"], check=True)
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1); self.assertIn("top release heading still has <!-- RELEASE_DATE -->", r.stdout)
        self.assertIn("VERSION agrees", r.stdout)  # the placeholder heading still names the version

    def test_refuses_a_whats_new_page_whose_release_date_is_still_the_placeholder(self):
        page = self.tree / "site/public/whats-new.html"
        page.write_text("<h2 id=\"v9-9-9\">9.9.9, <!-- RELEASE_DATE --></h2>\n")
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "add", "-A"], check=True)
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "y"], check=True)
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1); self.assertIn("still has <!-- RELEASE_DATE -->", r.stdout)
        page.write_text("<h2 id=\"v9-9-9\">9.9.9, 2026-01-01</h2>\n")
        subprocess.run(["/usr/bin/git", "-C", str(self.tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "z"], check=True)
        self.assertEqual(self.publish("--dry-run").returncode, 0)

    def test_refuses_a_dirty_tree_and_resume_md(self):
        (self.tree / "shotfleet.py").write_text('VERSION = "9.9.9"\n# dirty\n')
        (self.tree / "RESUME.md").write_text("x")
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("git tree is not clean", r.stdout)
        self.assertIn("RESUME.md is in the tree", r.stdout)

    def test_refuses_without_origin_main_unless_allowed(self):
        r = self.publish("--dry-run", env={"PUBLISH_ALLOW_BRANCH": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("HEAD is not origin/main", r.stdout)

    def test_refuses_without_a_durable_directory(self):
        r = self.publish("--dry-run", env={"SHOTFLEET_RELEASE_DIR": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("SHOTFLEET_RELEASE_DIR is not set", r.stdout)
        r = self.publish("--dry-run", env={"SHOTFLEET_ALLOW_TMP_DIR": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("under a temporary directory", r.stdout)

    def test_refuses_when_the_live_version_id_cannot_be_read_in_a_real_run(self):
        r = self.publish(env={"WRANGLER": "false"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("refusing to deploy without a rollback target", r.stdout)
        self.assertFalse((self.tree / "site/public/download").exists())

    def test_manifest_needs_both_files(self):
        m = self.tmp / "one.txt"; m.write_text("\n".join(self.manifest.read_text().splitlines()[:3]) + "\n")
        r = self.publish("--dry-run", manifest=m)
        self.assertEqual(r.returncode, 1)
        self.assertIn("exactly two files", r.stdout)


class RealRunWithFakes(Fixture):
    """The whole publish flow against a fake wrangler and a local web server that serves what the fake deploy 'uploaded'."""

    def test_success_stages_archives_records_deploys_and_verifies(self):
        self.serve()
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PUBLISHED 9.9.9", r.stdout)
        self.assertEqual([c for c in self.calls() if not c.startswith("deployments")], ["deploy"])  # no rollback
        d = self.tree / "site/public/download"
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["9.9.9", "VERSION", "shotfleet-macos-arm64.pkg", "shotfleet-macos-arm64.tar.gz", "shotfleet-macos-arm64.tar.gz.sha256"])
        self.assertEqual(sha(d / "shotfleet-macos-arm64.tar.gz"), sha(self.tar))
        arch = self.rel / "archive/9.9.9"
        self.assertEqual(sha(arch / "shotfleet-macos-arm64.pkg"), sha(self.pkg))
        self.assertIn(sha(self.tar), (arch / "SHA256SUMS").read_text())
        rollback_files = list((self.rel / "state").glob("rollback-9.9.9-*.txt"))
        self.assertEqual(len(rollback_files), 1)
        self.assertEqual(rollback_files[0].read_text().splitlines()[0], OLD)
        self.assertEqual(len(list((self.rel / "state").glob("published-9.9.9-*.txt"))), 1)

    def test_a_failed_verification_rolls_back_to_the_recorded_id(self):
        self.serve()
        r = self.publish(env={"FAKE_CORRUPT": "1"})
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("served tarball hash differs", r.stdout)
        self.assertIn("ROLLING BACK", r.stdout)
        self.assertIn(f"rollback {OLD}", " ".join(self.calls()))
        self.assertEqual((self.fake / "live").read_text().strip(), OLD)
        self.assertEqual(len(list((self.rel / "state").glob("published-*"))), 0)
        self.assertEqual(len(list((self.rel / "state").glob("rollback-9.9.9-*.txt"))), 1)  # the id was recorded before the deploy

    def test_a_failed_smoke_test_rolls_back(self):
        self.serve()
        r = self.publish(env={"PUBLISH_SMOKE": "/usr/bin/false"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("smoke test failed", r.stdout)
        self.assertEqual((self.fake / "live").read_text().strip(), OLD)

    def test_a_stopped_script_after_the_deploy_rolls_back(self):
        # the web server is not up: VERSION can never be verified, so the script gives up and must undo the deploy
        r = self.publish()
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"rollback {OLD}", " ".join(self.calls()))
        self.assertEqual((self.fake / "live").read_text().strip(), OLD)


class Versioned(Fixture):
    """/download/<version>/: the new release plus every archived one, re-staged on each deploy because a deploy replaces all static assets."""

    def archive(self, version, corrupt=False):
        a = self.rel / "archive" / version; a.mkdir(parents=True)
        tar, pkg = a / "shotfleet-macos-arm64.tar.gz", a / "shotfleet-macos-arm64.pkg"
        tar.write_bytes(version.encode() * 1000); pkg.write_bytes(os.urandom(512))
        (a / "SHA256SUMS").write_text(f"{sha(tar)}  {tar.name}\n{sha(pkg)}  {pkg.name}\n")
        (a / "manifest.txt").write_text(f"version {version}\nfile {sha(tar)} 1 shotfleet-{version}-macos-arm64.tar.gz\nfile {sha(pkg)} 1 shotfleet-{version}-macos-arm64.pkg\n")
        (self.rel / "archive/live-before-9.9.9").mkdir(exist_ok=True)  # a record folder, never staged
        if corrupt:
            tar.write_bytes(tar.read_bytes() + b"x")
        return sha(tar), sha(pkg)

    def test_two_versions_are_staged_served_and_verified(self):
        old_tar, old_pkg = self.archive("9.9.8")
        self.serve()
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for line in ("archive 9.9.8: 2 file(s) match their recorded sha256 and the kept manifest", "ok    /download/9.9.9/shotfleet-macos-arm64.pkg",
                     "ok    /download/9.9.8/shotfleet-macos-arm64.tar.gz", "versioned downloads verified: 9.9.8 9.9.9"):
            self.assertIn(line, r.stdout)
        served = self.fake / "serve/download"
        self.assertEqual(sha(served / "9.9.9/shotfleet-macos-arm64.tar.gz"), sha(self.tar))
        self.assertEqual(sha(served / "9.9.8/shotfleet-macos-arm64.pkg"), old_pkg)
        self.assertEqual((served / "9.9.8/shotfleet-macos-arm64.tar.gz.sha256").read_text(), f"{old_tar}  shotfleet-macos-arm64.tar.gz\n")
        self.assertEqual((served / "VERSION").read_text().strip(), "9.9.9")  # latest stays where it was
        self.assertEqual(sha(served / "shotfleet-macos-arm64.tar.gz"), sha(self.tar))
        self.assertFalse((served / "live-before-9.9.9").exists())
        self.assertEqual(sorted(p.name for p in (self.rel / "archive/9.9.9").iterdir()),  # the flat archive is unchanged by the versioned folders
                         ["SHA256SUMS", "VERSION", "manifest.txt", "shotfleet-macos-arm64.pkg", "shotfleet-macos-arm64.tar.gz", "shotfleet-macos-arm64.tar.gz.sha256"])

    def test_dry_run_prints_every_versioned_file(self):
        self.archive("9.9.8")
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout)
        for v, n in (("9.9.9", "tar.gz"), ("9.9.9", "pkg"), ("9.9.8", "tar.gz"), ("9.9.8", "pkg")):
            self.assertIn(f"would: stage /download/{v}/shotfleet-macos-arm64.{n}", r.stdout)
        self.assertIn(f"would: stage /download/9.9.8/shotfleet-macos-arm64.tar.gz (sha256 {sha(self.rel / 'archive/9.9.8/shotfleet-macos-arm64.tar.gz')[:12]}...) "
                      f"from {self.rel}/archive/9.9.8, plus shotfleet-macos-arm64.tar.gz.sha256\n", r.stdout)
        self.assertIn("would: stage /download/9.9.9/shotfleet-macos-arm64.pkg (sha256 ", r.stdout)
        self.assertIn("from the tested artifacts\n", r.stdout)
        self.assertEqual(r.stderr, "")
        self.assertFalse((self.tree / "site/public/download").exists())

    def test_a_corrupted_archived_file_refuses_before_anything_is_deployed(self):
        self.archive("9.9.8", corrupt=True)
        self.serve()
        r = self.publish()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("archive 9.9.8: shotfleet-macos-arm64.tar.gz does not match its recorded sha256", r.stdout)
        self.assertIn("REFUSED", r.stdout)
        self.assertEqual(self.calls(), ["deployments list"])
        self.assertFalse((self.tree / "site/public/download").exists())

    def test_sha256sums_rewritten_to_match_a_changed_file_is_caught_by_the_manifest(self):
        self.archive("9.9.8")
        a = self.rel / "archive/9.9.8"; t = a / "shotfleet-macos-arm64.tar.gz"
        t.write_bytes(b"other"); (a / "SHA256SUMS").write_text(f"{sha(t)}  {t.name}\n")
        r = self.publish("--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("SHA256SUMS and manifest.txt disagree on shotfleet-macos-arm64.tar.gz", r.stdout)

    def test_a_versioned_file_served_wrong_rolls_back(self):
        self.archive("9.9.8")
        self.serve()
        r = self.publish(env={"FAKE_CORRUPT_OLD": "1"})
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("served /download/9.9.8/shotfleet-macos-arm64.tar.gz has another sha256", r.stdout)
        self.assertEqual((self.fake / "live").read_text().strip(), OLD)

    def test_headers_make_versioned_files_immutable_and_latest_no_cache(self):
        h = (ROOT / "site/public/_headers").read_text()
        self.assertIn("/download/:file\n  Cache-Control: no-cache\n", h)
        self.assertIn("/download/:version/*\n  Cache-Control: public, max-age=31536000, immutable\n", h)
        self.assertNotIn("/download/*", h)  # it would also match the versioned files and join both Cache-Control values


class Staging(Fixture):
    """--staging: the throwaway worker only. Every wrangler call carries the staging config and name; anything that could resolve to production is refused."""
    ARGS = "--config wrangler.staging.toml --name shotfleet-staging"
    STG = "https://shotfleet-staging.acct.workers.dev"

    def staging(self, *extra, env=None):
        return self.publish("--staging", *extra, env=env)

    def set_config(self, text):
        (self.tree / "site/wrangler.staging.toml").write_text(text)

    def test_refuses_when_the_base_url_could_be_production_or_is_missing(self):
        for base, why in (("", "needs PUBLISH_BASE"), ("https://shotfleet.com", "is not https://shotfleet-staging"), ("https://www.shotfleet.com", "is not https://shotfleet-staging"),
                          ("https://shotfleet-staging.x.workers.dev.shotfleet.com", "production domain"), ("https://shotfleet-staging.evil.com/a.workers.dev", "bare origin"),
                          ("https://shotfleet.manulorenzop.workers.dev", "is not https://shotfleet-staging"), ("https://shotfleet-staging.a.workers.dev/x", "bare origin")):
            with self.subTest(base=base):
                r = self.staging("--dry-run", env={"PUBLISH_BASE": base})
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(why, r.stdout)
                self.assertIn("REFUSED: the staging target is not provably separate", r.stdout)
                self.assertEqual(self.calls(), [])  # refused before wrangler was even asked to read

    def test_refuses_a_staging_config_that_could_touch_production(self):
        good = (ROOT / "site/wrangler.staging.toml").read_text()
        for text, why in (('name = "shotfleet"\n', "names the worker 'shotfleet'"), ('name = "fake"\n', "names the worker 'fake'"),  # the fixture's production name is "fake"
                          (good + 'routes = [{ pattern = "x.example.com", custom_domain = true }]\n', "has a route"),
                          (good + '[[kv_namespaces]]\nbinding = "WAITLIST"\nid = "250f"\n', "tables other than [assets]"),
                          (good + '[[send_email]]\nname = "ALERT"\n', "tables other than [assets]"),
                          (good + '[env.production]\nname = "shotfleet"\n', "has a route"),
                          (good + 'route = "shotfleet.com/*"\n', "has a route")):
            with self.subTest(text=text[-60:]):
                self.set_config(text)
                r = self.staging("--dry-run", env={"PUBLISH_BASE": self.STG})
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(why, r.stdout)
                self.assertEqual(self.calls(), [])
        self.set_config(good.replace('"shotfleet-staging"', '"shotfleet-staging"  # not shotfleet.com'))  # a comment is fine
        self.assertNotIn("REFUSED: the staging target", self.staging("--dry-run", env={"PUBLISH_BASE": self.STG}).stdout)
        (self.tree / "site/wrangler.staging.toml").unlink()
        self.assertIn("does not exist", self.staging("--dry-run", env={"PUBLISH_BASE": self.STG}).stdout)

    def test_the_real_staging_config_passes_and_a_dry_run_reads_only_with_the_staging_target(self):
        r = self.staging("--dry-run", env={"PUBLISH_BASE": self.STG})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("staging target: worker shotfleet-staging", r.stdout)
        self.assertIn("[STAGING shotfleet-staging]", r.stdout)
        self.assertEqual(self.calls(), [f"deployments list {self.ARGS}"])
        self.assertFalse(self.rel.exists())

    def test_a_real_staging_run_uses_the_staging_target_in_every_call_and_keeps_its_state_apart(self):
        self.serve()
        (self.fake / "smoke.sh").write_text(f'echo "$SMOKE_SKIP_REDIRECT" > {self.fake}/smoke-env\n')
        r = self.staging(env={"PUBLISH_SMOKE": f"sh {self.fake}/smoke.sh", "PUBLISH_BASE": self.env["PUBLISH_BASE"]})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("WRANGLER WRITE target: worker=shotfleet-staging config=site/wrangler.staging.toml", r.stdout)
        self.assertEqual(self.calls(), [f"deployments list {self.ARGS}", f"deploy {self.ARGS}"])
        self.assertEqual((self.fake / "smoke-env").read_text().strip(), "1")
        self.assertEqual(len(list((self.rel / "staging/state").glob("published-9.9.9-*.txt"))), 1)
        self.assertFalse((self.rel / "state").exists())

    def test_a_failed_staging_run_rolls_back_on_staging_only(self):
        self.serve()
        r = self.staging(env={"FAKE_CORRUPT": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("WRANGLER WRITE target: worker=shotfleet-staging", r.stdout)
        rb = [c for c in self.calls() if c.startswith("rollback")]
        self.assertEqual(len(rb), 1)
        self.assertIn(f"rollback {OLD}", rb[0]); self.assertTrue(rb[0].endswith(self.ARGS))
        self.assertEqual((self.fake / "live").read_text().strip(), OLD)

    def test_production_mode_never_passes_the_staging_config(self):
        self.serve()
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WRANGLER WRITE target: PRODUCTION", r.stdout)
        self.assertFalse([c for c in self.calls() if "staging" in c])


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class VerifyRelease(Fixture):
    def test_manifest_mismatch_and_unsigned_files_fail(self):
        r = run(["sh", VERIFY, "--no-run", "--manifest", self.manifest, self.tar])
        self.assertEqual(r.returncode, 1)
        self.assertIn("matches the manifest", r.stdout)  # the hash is right ...
        self.assertIn("FAIL: ", r.stdout)  # ... and a fake, unsigned program is not a release
        self.tar.write_bytes(b"tampered")
        r = run(["sh", VERIFY, "--no-run", "--manifest", self.manifest, self.tar])
        self.assertIn("does NOT match the manifest", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_a_folder_and_a_missing_target(self):
        r = run(["sh", VERIFY, "--no-run", self.tmp / "build/shotfleet"])
        self.assertEqual(r.returncode, 1)
        r = run(["sh", VERIFY, self.tmp / "nope"])
        self.assertIn("no such file or folder", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_make_manifest_round_trips(self):
        text = self.manifest.read_text()
        self.assertIn("version 9.9.9", text)
        self.assertIn(f"file {sha(self.tar)} {self.tar.stat().st_size} {self.tar.name}", text)
        self.assertEqual(run(["sh", PUBLISH, "--make-manifest", "9.9.9", self.tmp / "missing"]).returncode, 2)


class Preflight(Fixture):
    def test_fails_with_a_reason_when_checks_fail(self):
        fakebin = self.tmp / "bin"; fakebin.mkdir()
        for n in ("security", "uv", "xcrun"):  # a fake xcrun: the real notarytool is never called
            (fakebin / n).write_text("#!/bin/sh\nexit 1\n"); (fakebin / n).chmod(0o755)
        r = run(["sh", PREFLIGHT], env={"PATH": f"{fakebin}:{os.environ['PATH']}", "NOTARY_PROFILE": "no-such-profile-xyz", "WRANGLER": "false", "MIN_FREE_GB": "99999999"})
        self.assertEqual(r.returncode, 1, r.stdout)
        for line in ("FAIL  Developer ID Application certificate", "FAIL  Developer ID Installer certificate", "FAIL  wrangler whoami", "FAIL  free disk", "FAIL  notarytool history failed", "FAIL  no uv-managed standalone Python"):
            self.assertIn(line, r.stdout)
        self.assertIn("preflight: ", r.stdout)


FAKE_XCRUN = '#!/bin/sh\n[ -z "$FAKE_XCRUN_ERR" ] && { echo "Successfully received submission history."; exit 0; }\necho "$FAKE_XCRUN_ERR$4" >&2; exit 69\n'
LOCKED = "Error: No Keychain password item found for profile: "


class NotaryCheck(Fixture):
    """A fake xcrun on the PATH stands in for notarytool; the real one is never called."""
    def check(self, err, profile=""):
        fakebin = self.tmp / "bin"; fakebin.mkdir(exist_ok=True)
        (fakebin / "xcrun").write_text(FAKE_XCRUN); (fakebin / "xcrun").chmod(0o755)
        return run(["sh", ROOT / "packaging/notary-check.sh"], env={"PATH": f"{fakebin}:{os.environ['PATH']}", "NOTARY_PROFILE": profile, "FAKE_XCRUN_ERR": err})

    def test_not_found_names_the_screen_lock_first_then_store_credentials(self):
        r = self.check(LOCKED)
        self.assertEqual(r.returncode, 1)
        self.assertIn(LOCKED + "ShotfleetNotary", r.stderr)  # the default, and notarytool's reason kept
        self.assertIn("macOS locks this keychain about 5 minutes after the screen locks. Unlock the Mac and run again.\n"
                      "Only if it still fails: xcrun notarytool store-credentials ShotfleetNotary --apple-id <your Apple ID> --team-id 2357A78TMR", r.stderr)

    def test_env_override_and_other_failures(self):
        r = self.check(LOCKED, profile="OtherProfile")
        self.assertIn("store-credentials OtherProfile ", r.stderr)
        r = self.check("Error: network unreachable ")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("screen locks", r.stderr); self.assertIn("No network", r.stderr)
        self.assertEqual(self.check("").returncode, 0)

    def test_scripts_check_first_and_right_before_each_submit(self):
        release = (ROOT / "packaging/release.sh").read_text()
        self.assertLess(release.index("packaging/notary-check.sh"), release.index("packaging/build.sh  #"))
        for f in ("build.sh", "pkg.sh"):
            code = (ROOT / "packaging" / f).read_text()
            submit = code.index("(set -o pipefail; xcrun notarytool submit")
            self.assertIn("packaging/notary-check.sh", code[code.rindex("\n", 0, code.rindex("\n", 0, submit)):submit])  # the line before
            self.assertNotIn("log <id>", code)

    def test_release_keeps_the_mac_awake_and_keeps_the_build_exit_status(self):
        t = self.tmp / "rel"
        for d in ("packaging", "tools", "bin"): (t / d).mkdir(parents=True)
        shutil.copy(ROOT / "packaging/release.sh", t / "packaging/release.sh")
        stubs = {"packaging/notary-check.sh": "exit 0", "tools/check-claims.sh": "exit 0",
                 "packaging/build.sh": 'echo "build out $NOTARY_PROFILE"; echo "build err" >&2; exit 7',
                 "bin/caffeinate": 'echo "caffeinate $*" >> "$(dirname "$0")/calls"; shift; exec "$@"'}
        for f, body in stubs.items():
            (t / f).write_text("#!/bin/sh\n" + body + "\n"); (t / f).chmod(0o755)
        r = run(["sh", t / "packaging/release.sh"], env={"PATH": f"{t / 'bin'}:{os.environ['PATH']}", "NOTARY_PROFILE": ""})
        self.assertEqual(r.returncode, 7)
        self.assertIn("build out ShotfleetNotary", r.stdout); self.assertIn("build err", r.stderr)
        self.assertEqual((t / "bin/calls").read_text(), "caffeinate -di packaging/build.sh\n")


if __name__ == "__main__":
    unittest.main()
