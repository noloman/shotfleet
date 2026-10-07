"""The release build installs exact, hashed inputs (packaging/requirements-build.txt) and nothing else; no unpinned install is left."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packaging"


def requirements():
    """{name: (version, [sha256, ...])} from the requirements file; a continuation line starts with whitespace."""
    text = (PKG / "requirements-build.txt").read_text().replace("\\\n", " ")
    found = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"([A-Za-z0-9._-]+)==([0-9][A-Za-z0-9.]*)((?: --hash=sha256:[0-9a-f]{64})+)", re.sub(r"\s+", " ", line))
        assert m, "not an exact pin with sha256 hashes: %r" % line
        found[m.group(1).lower()] = (m.group(2), re.findall(r"[0-9a-f]{64}", m.group(3)))
    return found


class PinnedBuildInputs(unittest.TestCase):
    def test_file_parses_and_every_requirement_is_pinned_with_a_hash(self):
        reqs = requirements()
        for name in ("pyinstaller", "pyinstaller-hooks-contrib", "certifi", "altgraph", "macholib", "packaging", "setuptools"):
            self.assertIn(name, reqs)
        self.assertEqual(reqs["pyinstaller"][0], "6.22.3")  # what 0.1.1 shipped with
        self.assertEqual(reqs["certifi"][0], "2026.6.17")
        for name, (version, hashes) in reqs.items():
            self.assertTrue(hashes, name)

    def test_no_option_that_turns_hash_checking_off_or_floats_versions(self):
        text = (PKG / "requirements-build.txt").read_text()
        for bad in ("--index-url", "--extra-index-url", "--find-links", ">=", "<=", "~=", "--no-deps"):
            self.assertNotIn(bad, "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#")))

    def test_build_installs_only_from_the_file_with_hashes_and_the_recorded_python(self):
        s = (PKG / "build.sh").read_text()
        self.assertRegex(s, r"pip install .*--require-hashes -r packaging/requirements-build\.txt")
        self.assertIn('PINNED_PYTHON=${PINNED_PYTHON:-3.14.2}', s)
        self.assertIn('"$PYTHON" -m venv build/venv', s)
        self.assertIn("uv python find", s)
        self.assertNotIn("python3 -m venv", s)
        self.assertLess(s.index("PINNED_PYTHON="), s.index("swiftc"))  # a wrong Python is refused before anything is built

    def test_every_build_freezes_the_release_date(self):
        # a frozen build without the _release module prints "no usable release date" on every start
        for name, text in (("build.sh", (PKG / "build.sh").read_text()), ("build-linux.sh", (PKG / "build-linux.sh").read_text()),
                           ("Dockerfile", (PKG.parent / "Dockerfile").read_text())):
            self.assertIn("RELEASE_DATE = ", text, name)
            self.assertIn("--hidden-import _release", text, name)
            self.assertIn("--paths", text, name)

    def test_no_unpinned_pip_install_left_in_packaging(self):
        for f in sorted(PKG.glob("*.sh")):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if line.lstrip().startswith("#") or "pip" not in line:
                    continue
                self.assertNotIn("--upgrade", line, "%s:%d" % (f.name, n))
                if re.search(r"pip install", line):
                    self.assertTrue("--require-hashes" in line or re.search(r"==\d", line), "%s:%d installs unpinned: %s" % (f.name, n, line))

    def test_build_refuses_a_python_that_is_not_the_recorded_version(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "python"
            fake.write_text('#!/bin/sh\necho 3.99.0\n')
            fake.chmod(0o755)
            r = subprocess.run(["sh", str(PKG / "build.sh")], env={"PATH": "/usr/bin:/bin", "PYTHON": str(fake)}, capture_output=True, text=True, cwd=d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("recorded build Python is 3.14.2", r.stderr)


if __name__ == "__main__":
    unittest.main()
