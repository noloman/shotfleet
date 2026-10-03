"""tools/latest-maestro.py: pick the newest stable Maestro release, fetch it, screen it. A local HTTP server stands in for GitHub."""
import contextlib, hashlib, importlib.util, io, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE)]
import shotfleet as sf
from test_doctor_fix import Server, zip_bytes
from test_maestro_compat import fake_maestro, ALL_STRINGS

spec = importlib.util.spec_from_file_location("latest_maestro", ROOT / "tools/latest-maestro.py")
lm = importlib.util.module_from_spec(spec); spec.loader.exec_module(lm)


def release(tag, assets=("maestro.zip", "checksums_sha256.txt"), **kw):
    return {"tag_name": tag, "draft": False, "prerelease": False,
            "assets": [{"name": n, "browser_download_url": f"https://example.invalid/{tag}/{n}"} for n in assets], **kw}


class PickingTheNewest(unittest.TestCase):
    def test_the_highest_version_wins_not_the_first_or_the_alphabetical_one(self):
        rels = [release("cli-2.9.0"), release("cli-2.11.0"), release("cli-2.10.3"), release("cli-1.40.3")]
        self.assertEqual(lm.newest_cli_release(rels)[0], "2.11.0")

    def test_pre_releases_drafts_other_tags_and_releases_without_the_zip_are_skipped(self):
        rels = [release("cli-3.0.0", prerelease=True), release("cli-2.99.0", draft=True), release("v9.9.9"), release("cli-2.50.0-beta1"),
                release("cli-2.40.0", assets=("checksums_sha256.txt",)), release("cli-2.11.0")]
        self.assertEqual(lm.newest_cli_release(rels)[0], "2.11.0")

    def test_nothing_usable_is_none(self):
        self.assertIsNone(lm.newest_cli_release([])); self.assertIsNone(lm.newest_cli_release([release("v1.0.0")]))

    def test_the_checksum_is_read_from_the_listing(self):
        h = "a" * 64
        self.assertEqual(lm.checksum_for(f"{'b' * 64}  other.zip\n{h.upper()}  maestro.zip\n"), h)
        self.assertEqual(lm.checksum_for(f"{h} *dist/maestro.zip"), h)
        self.assertIsNone(lm.checksum_for("nothing here")); self.assertIsNone(lm.checksum_for(None)); self.assertIsNone(lm.checksum_for(f"short  maestro.zip"))

    def test_the_verdict_names_tested_newer_and_older(self):
        with mock.patch.object(sf, "MAESTRO_TESTED", ("2.0.10",)):
            self.assertIn("was tested with", lm.verdict("2.0.10"))
            self.assertIn("newer than anything", lm.verdict("2.11.0")); self.assertIn("real run", lm.verdict("2.11.0"))
            self.assertIn("older than", lm.verdict("1.40.3"))
            self.assertIn("newer than anything", lm.verdict("2.100.0"))  # numeric, not alphabetical


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.server = Server({}); self.addCleanup(self.server.close)

    def serve(self, version="2.99.0", strings=None, sums="good"):
        d = fake_maestro(version=version, strings=strings)
        files = {f"maestro/{p.relative_to(d)}": p.read_bytes() for p in d.rglob("*") if p.is_file()}
        zbytes = zip_bytes(files, {"maestro/bin/maestro": 0o755})
        sha = hashlib.sha256(zbytes).hexdigest() if sums == "good" else "0" * 64
        base = self.server.url
        self.server.files.update({"/maestro.zip": zbytes, "/sums.txt": f"{sha}  maestro.zip\n".encode(),
                                  "/releases": json.dumps([{"tag_name": f"cli-{version}", "draft": False, "prerelease": False, "assets": [
                                      {"name": "maestro.zip", "browser_download_url": base + "/maestro.zip"},
                                      {"name": "checksums_sha256.txt", "browser_download_url": base + "/sums.txt"}]}]).encode()})

    def run_main(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(lm, "RELEASES", self.server.url + "/releases"), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = lm.main()
        return code, out.getvalue(), err.getvalue()

    def test_a_compatible_newer_maestro_passes_and_says_it_needs_a_real_run(self):
        self.serve()
        code, out, err = self.run_main()
        self.assertEqual(code, 0, out + err)
        self.assertIn("newest Maestro release: 2.99.0", out); self.assertIn("0 failed", out); self.assertIn("real run", out)

    def test_a_maestro_that_lost_something_shotfleet_needs_fails(self):
        self.serve(strings=[s for s in ALL_STRINGS if s != "ExecutionPlan(flowsToRun="])
        code, out, _ = self.run_main()
        self.assertEqual(code, 1); self.assertIn("FAIL", out); self.assertIn("ExecutionPlan(flowsToRun=", out)

    def test_a_download_that_does_not_match_the_published_checksum_is_refused(self):
        self.serve(sums="bad")
        code, out, err = self.run_main()
        self.assertEqual(code, 2); self.assertIn("checksum", err)

    def test_an_unreachable_release_list_is_exit_2_not_a_pass(self):
        with mock.patch.object(lm, "RELEASES", "http://127.0.0.1:9/none"), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(lm.main(), 2)
        self.assertIn("can't read the release list", err.getvalue())

    def test_the_step_summary_is_written_when_github_asks_for_one(self):
        self.serve(); summary = Path(tempfile.mkdtemp()) / "summary.md"
        with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
            code, _, _ = self.run_main()
        self.assertEqual(code, 0); self.assertIn("Maestro 2.99.0: ", summary.read_text())


if __name__ == "__main__":
    unittest.main()
