"""The three places that name the released version agree, and the tool that guards the minimum macOS is still there.
A release that disagrees with itself (0.1.1 had one such mismatch) is caught here, before packaging/publish.sh refuses it.

Run: python3 -m unittest tests.test_release_consistency
"""
import importlib.util, re, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class VersionAgrees(unittest.TestCase):
    def versions(self):
        py = re.search(r'^VERSION = "(\d+\.\d+\.\d+)"', (ROOT / "shotfleet.py").read_text(), re.M).group(1)
        changelog = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(), re.M).group(1)  # "## Unreleased" does not match
        docs = re.search(r"Last checked against version (\d+\.\d+\.\d+) on", (ROOT / "site/public/docs.html").read_text()).group(1)
        return py, changelog, docs

    def test_shotfleet_py_changelog_and_docs_page_name_the_same_version(self):
        py, changelog, docs = self.versions()
        self.assertEqual((changelog, docs), (py, py), f"shotfleet.py {py}, top CHANGELOG release heading {changelog}, docs 'Last checked' line {docs}")


class MachoMinosGuard(unittest.TestCase):
    TOOL = ROOT / "tools/macho-minos.py"

    def test_tool_exists_with_a_max_option(self):
        self.assertTrue(self.TOOL.is_file())
        self.assertIn('"--max"', self.TOOL.read_text())

    def test_max_fails_a_build_that_needs_a_newer_macos(self):
        spec = importlib.util.spec_from_file_location("macho_minos", self.TOOL)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        text = "Load command 9\n      cmd LC_BUILD_VERSION\n  cmdsize 32\n platform MACOS\n    minos 14.0\n      sdk 27.0\n"
        self.assertEqual(mod.minos(text), (14, 0))
        folder = Path(tempfile.mkdtemp())
        self.assertEqual(subprocess.run([sys.executable, str(self.TOOL), str(folder), "--max", "13"], capture_output=True).returncode, 0)  # nothing to scan
        # a real Mach-O: this interpreter. Its minimum is whatever it is; the limit decides the exit code.
        exe = Path(sys.executable).resolve()
        if "Mach-O" in subprocess.run(["file", "-b", str(exe)], capture_output=True, text=True).stdout:
            (folder / "py").write_bytes(exe.read_bytes())
            top = max(m for _, m in mod.scan(folder) if m)
            below = ".".join(map(str, (top[0] - 1,)))
            self.assertEqual(subprocess.run([sys.executable, str(self.TOOL), str(folder), "--max", below], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run([sys.executable, str(self.TOOL), str(folder), "--max", str(top[0] + 1)], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
