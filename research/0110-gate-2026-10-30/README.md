# 0.1.10 release gate, 2026-10-30

The signed and notarized build from d3fe008, run through the full fixture e2e (iPhone, iPad, Android, iOS 26.4) on Maestro 2.0.10. One run, PASS, all 65 assertions, 16:12-16:33. The Android output assertions ran (no "needs Python" in the log).

- g3-0110-gate-PASS.log: the gate log
- sha256.txt: the hashes of the two files that were gated
- verify.out: tools/verify-release.sh on the build, 10 checks, 0 failed

Not covered: the 0.1.10 features (clock/root, custom sizes and landscape, waitForExpected, runFlow when defined, Compose and foldables) are not exercised by this gate. They were tested with fakes and unit tests only.
