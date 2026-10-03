#!/usr/bin/env python3
"""Run one test module as if on an Apple-silicon Mac, to catch Mac-only failures before CI does: tools/pretend-mac.py test_doctor_fix

Flips sys.platform to darwin (after the imports, which need the real one) and the CPU to arm64. That is all it does: it has no
Xcode, no Homebrew, no Vision, no plutil. Tests that really need those still skip or fail here, so this is a screen for the kind of
mistake where a test assumes the machine it was written on (it found two in the doctor --fix tests that the macOS CI job found too).
It does not replace a run on a Mac.
"""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import shotfleet as sf, urllib.request, tarfile, zipfile, subprocess  # noqa: E401,F401 -- imported while still on the real platform

if len(sys.argv) < 2:
    sys.exit(__doc__)
sys.platform = "darwin"
sf.host_platform.machine = lambda: "arm64"
module = __import__(sys.argv[1])
result = unittest.TextTestRunner(verbosity=1 if "-v" in sys.argv else 0).run(unittest.defaultTestLoader.loadTestsFromModule(module))
sys.exit(not result.wasSuccessful())
