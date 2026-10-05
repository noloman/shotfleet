"""tools/macho-minos.py: which macOS a PyInstaller folder needs (Homebrew's Python made the 0.1.0 folder need macOS 27.0;
research/limits-platform-reach-2026-10-05.md). Parsing only, canned `otool -l` text: no binary is touched.

Run: python3 -m unittest tests.test_platform_reach
"""
import contextlib, importlib.util, io, sys, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("macho_minos", ROOT / "tools/macho-minos.py")
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)

BUILD = "Load command 11\n      cmd LC_BUILD_VERSION\n  cmdsize 32\n platform {p}\n    minos {v}\n      sdk 27.0\n   ntools 1\n"


class MachoMinos(unittest.TestCase):
    def test_reads_the_minimum_macos_of_a_build_version_command(self):
        self.assertEqual(tool.minos(BUILD.format(p=1, v="13.0")), (13, 0))
        self.assertEqual(tool.minos(BUILD.format(p="MACOS", v="26.4")), (26, 4))

    def test_an_ios_simulator_file_has_no_macos_minimum_and_old_files_use_the_old_command(self):
        self.assertIsNone(tool.minos(BUILD.format(p=7, v="14.0")))  # platform 7: iOS simulator; its minos is an iOS version
        self.assertEqual(tool.minos("      cmd LC_VERSION_MIN_MACOSX\n  cmdsize 16\n  version 10.9\n      sdk 12.0\n"), (10, 9))
        self.assertIsNone(tool.minos(""))

    def test_max_turns_a_too_new_file_into_exit_code_1_and_the_report_names_the_macos(self):
        found = {("arm64", (11, 0)): [Path("a")], ("arm64", (27, 0)): [Path("b"), Path("c")]}
        with mock.patch.object(tool, "scan", return_value=found):
            for argv, code in (([], 0), (["--max", "14"], 1), (["--max", "27"], 0)):
                out = io.StringIO()
                with contextlib.redirect_stdout(out): self.assertEqual(tool.main(["dist/x", *argv]), code, argv)
            self.assertIn("this build needs macOS 27.0 or newer", out.getvalue()); self.assertIn("2 file(s)", out.getvalue())


if __name__ == "__main__":
    unittest.main()
