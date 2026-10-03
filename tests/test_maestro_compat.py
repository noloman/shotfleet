"""tools/maestro-compat.py: a Maestro that has everything shotfleet relies on passes, one that lost a flag, a log line or a flow key fails.
A fake Maestro (a shell script plus a small jar) stands in; no Java and no real Maestro needed."""
import importlib.util, io, os, stat, sys, tempfile, unittest, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf
spec = importlib.util.spec_from_file_location("maestro_compat", ROOT / "tools/maestro-compat.py")
mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)

ALL_STRINGS = [n for group in sf.MAESTRO_INTERFACE["class_strings"].values() for n in group]


def fake_maestro(version="2.5.0", flags=None, strings=None, extra_strings=()):
    """A Maestro folder: bin/maestro answers --version/--help, lib/maestro-fake.jar holds the given class strings."""
    d = Path(tempfile.mkdtemp())
    flags = sf.MAESTRO_INTERFACE["cli"]["maestro test"] + ["JUNIT"] if flags is None else flags
    (d / "bin").mkdir(); (d / "lib").mkdir()
    script = d / "bin/maestro"
    script.write_text(f'''#!/bin/sh
case "$*" in
  *--version*) echo {version} ;;
  *test*--help*) echo "Usage: maestro test {' '.join(flags)}" ;;
  *--help*) echo "Usage: maestro --device <id> {{test}}" ;;
esac
''')
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    with zipfile.ZipFile(d / "lib/maestro-fake.jar", "w") as z:
        z.writestr("a/B.class", b"\xca\xfe" + " ".join((ALL_STRINGS if strings is None else strings) + list(extra_strings)).encode())
    return d


def run_check(d):
    lines = []
    passed, failed, version = mc.check(d / "bin/maestro", d / "lib", out=lines.append)
    return passed, failed, version, lines


class Compat(unittest.TestCase):
    def test_a_complete_maestro_passes_every_check(self):
        passed, failed, version, lines = run_check(fake_maestro())
        self.assertEqual((failed, version), (0, "2.5.0"), [l for l in lines if l.startswith("FAIL")])
        self.assertGreater(passed, 20)

    def test_a_lost_flag_is_a_failure_that_names_it(self):
        flags = [f for f in sf.MAESTRO_INTERFACE["cli"]["maestro test"] if f != "--shard-split"] + ["JUNIT"]
        _, failed, _, lines = run_check(fake_maestro(flags=flags))
        self.assertEqual(failed, 1); self.assertTrue(any(l.startswith("FAIL") and "--shard-split" in l for l in lines), lines)

    def test_flag_names_are_matched_whole_not_as_prefixes(self):
        flags = ["--shard-splitter", "--format", "--output", "--debug-output-dir", "JUNIT"]  # lookalikes only
        _, failed, _, lines = run_check(fake_maestro(flags=flags))
        self.assertEqual(failed, 2, [l for l in lines if l.startswith("FAIL")])

    def test_a_vanished_log_line_is_a_failure(self):
        strings = [s for s in ALL_STRINGS if s != "ExecutionPlan(flowsToRun="]
        _, failed, _, lines = run_check(fake_maestro(strings=strings))
        self.assertEqual(failed, 1); self.assertTrue(any("ExecutionPlan(flowsToRun=" in l and l.startswith("FAIL") for l in lines))

    def test_the_device_udid_is_only_information(self):
        _, failed, _, lines = run_check(fake_maestro())
        self.assertEqual(failed, 0); self.assertTrue(any("MAESTRO_DEVICE_UDID: not defined" in l for l in lines))
        _, failed, _, lines = run_check(fake_maestro(extra_strings=["MAESTRO_DEVICE_UDID"]))
        self.assertEqual(failed, 0); self.assertTrue(any("MAESTRO_DEVICE_UDID: defined" in l for l in lines))

    def test_maestro_1_is_not_enough(self):
        _, failed, _, lines = run_check(fake_maestro(version="1.40.3"))
        self.assertTrue(any(l.startswith("FAIL") and "Maestro 2 or newer" in l for l in lines), lines)

    def test_shotfleets_view_of_the_version_is_shown(self):
        _, _, _, lines = run_check(fake_maestro(version=sf.MAESTRO_TESTED[0]))
        self.assertTrue(any("tested version" in l for l in lines), lines)
        _, _, _, lines = run_check(fake_maestro(version="2.99.0"))
        self.assertTrue(any("not the version shotfleet was tested with" in l for l in lines), lines)

    def test_it_finds_the_folder_the_binary_or_the_wrapper(self):
        d = fake_maestro()
        for arg in (d, d / "bin/maestro"):
            maestro, lib = mc.find_maestro(str(arg)); self.assertEqual(maestro, (d / "bin/maestro").resolve())
        wrapper = Path(tempfile.mkdtemp()); (wrapper / "maestro").symlink_to(d)
        self.assertEqual(mc.find_maestro(str(wrapper))[0], (d / "bin/maestro").resolve())
        self.assertEqual(mc.find_maestro("/nonexistent"), (None, None))

    def test_the_interface_covers_what_the_program_passes_to_maestro(self):
        src = (ROOT / "shotfleet.py").read_text()
        for flag in sf.MAESTRO_INTERFACE["cli"]["maestro test"]: self.assertIn(f'"{flag}"', src, flag)
        self.assertIn('"--device"', src)
        for var in sf.MAESTRO_INTERFACE["class_strings"]["env"]: self.assertIn(var, src, var)


if __name__ == "__main__":
    unittest.main()
