"""tools/apple-specs-watch.py: notice when Apple's screenshot specification page and shotfleet's size table drift apart. A local server stands in for Apple."""
import contextlib, importlib.util, io, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE)]
import shotfleet as sf
from test_doctor_fix import Server

spec = importlib.util.spec_from_file_location("apple_watch", ROOT / "tools/apple-specs-watch.py")
aw = importlib.util.module_from_spec(spec); spec.loader.exec_module(aw)


def page_for(sizes, extra=(), script="var x = '9999 x 9999 pixels';"):
    """A page shaped like Apple's: a size and its landscape twin per cell, plus a script block that must be ignored."""
    cells = "".join(f"<td>{w} x {h} pixels</td><td>{h} x {w} pixels</td>" for w, h in list(sizes) + list(extra))
    return f"<html><script>{script}</script><body><table><tr>{cells}</tr></table><p>Screenshots must not include alpha.</p></body></html>"


TABLE = sorted({s for v in sf.APPLE_SIZES.values() for s in v})


class Parsing(unittest.TestCase):
    def test_sizes_are_read_in_either_orientation_and_markup_entities_are_handled(self):
        sizes, n = aw.page_sizes("<p>1,320&nbsp;x 2868 pixels</p> <b>1320 &times; 2868 pixels</b> <i>2868 x 1320 pixels</i> <td>422 × 514 pixels</td>")
        self.assertEqual(sizes, {(1320, 2868), (422, 514)})
        self.assertIn((422, 514), sizes); self.assertIn((1320, 2868), sizes)

    def test_script_and_style_blocks_are_ignored(self):
        sizes, _ = aw.page_sizes(page_for([(640, 920)], script="var big = '4321 x 8765 pixels';"))
        self.assertNotIn((4321, 8765), sizes); self.assertIn((640, 920), sizes)

    def test_shotfleets_table_agrees_with_a_page_built_from_it(self):
        sizes, n = aw.page_sizes(page_for(TABLE))
        self.assertEqual(aw.compare(sizes, aw.table_sizes()), ([], []))
        self.assertGreaterEqual(n, aw.MIN_SIZES)

    def test_a_new_size_and_a_dropped_size_are_each_reported(self):
        sizes, _ = aw.page_sizes(page_for(TABLE + [(1500, 3000)]))
        new, gone = aw.compare(sizes, aw.table_sizes()); self.assertEqual((new, gone), ([(1500, 3000)], []))
        sizes, _ = aw.page_sizes(page_for([s for s in TABLE if s != (1320, 2868)]))
        new, gone = aw.compare(sizes, aw.table_sizes()); self.assertEqual((new, gone), ([], [(1320, 2868)]))


class Running(unittest.TestCase):
    def setUp(self):
        self.server = Server({}); self.addCleanup(self.server.close)

    def run_main(self, body=None, url=None):
        if body is not None: self.server.files["/specs"] = body.encode()
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(aw, "URL", url or self.server.url + "/specs"), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = aw.main()
        return code, out.getvalue(), err.getvalue()

    def test_a_matching_page_exits_0(self):
        code, out, _ = self.run_main(page_for(TABLE)); self.assertEqual(code, 0); self.assertIn("matches", out)

    def test_drift_exits_1_and_names_the_size(self):
        code, out, _ = self.run_main(page_for(TABLE, extra=[(1500, 3000)]))
        self.assertEqual(code, 1); self.assertIn("1500x3000", out); self.assertIn("APPLE_SIZES", out)

    def test_a_page_that_stopped_looking_like_the_specification_is_exit_2_not_a_pass(self):
        code, _, err = self.run_main("<html><body>Please sign in to continue</body></html>")
        self.assertEqual(code, 2); self.assertIn("changed shape", err)

    def test_an_unreachable_page_is_exit_2(self):
        code, _, err = self.run_main(url="http://127.0.0.1:9/none"); self.assertEqual(code, 2); self.assertIn("can't read", err)

    def test_the_step_summary_is_written(self):
        summary = Path(tempfile.mkdtemp()) / "s.md"
        with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
            self.run_main(page_for(TABLE))
        self.assertIn("Apple screenshot sizes", summary.read_text())


class TableFacts(unittest.TestCase):
    def test_old_devices_landscape_sizes_are_accepted_as_apple_lists_them(self):
        for size, cls in (((960, 600), 'iPhone 3.5"'), ((1136, 600), 'iPhone 4"'), ((2048, 1496), 'iPad 9.7"'), ((1024, 748), 'iPad 9.7"')):
            self.assertEqual(sf.apple_class(size), cls, size)
        self.assertIsNone(sf.apple_class((959, 600)))
        # known and harmless: the rotation rule also lets the portrait twin of those landscape sizes through; nobody produces them

if __name__ == "__main__":
    unittest.main()
