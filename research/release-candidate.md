# Release candidate: the frozen program, built locally and tested without the network accounts

Run 2026-10-02 on the dev Mac (Apple silicon, macOS 27.0, Python 3.14.8 from Homebrew, PyInstaller from pip). Covers STATUS.md gate 5 (licence) and gate 6 (release build) as far as they can be proven without Apple's notary, a Gumroad product or a clean Mac. Everything below was produced by one script, `SHOTFLEET_RC=1 tools/release-candidate.sh` (tests: `tests/test_release_candidate.py`). Outputs are trimmed; temp paths are shortened to `$W`.

Verdict: **92 checks passed, 0 failed** (the first full run that built it: 94 checks, 1 failed, a too-strict assertion in the script about the planted-problem list, fixed; then the same checks on the kept build: 92 of 92; earlier runs found two script bugs, listed in section 6). Not proven: Apple's notarization verdict, a real Gumroad key, Gatekeeper with a browser download of a notarized build, a clean Mac. Two findings need a decision (section 7).

Nothing was deployed, pushed, uploaded, notarized or submitted to Apple. No simulator or emulator was booted. One unintended call to the real Gumroad API happened (section 7, item 5).

## 1. What the script does

1. Copies `shotfleet.py`, `ocr.swift`, `skill/`, `packaging/` into a temp dir and sets `GUMROAD_PRODUCT_ID = "RCTESTPRODUCT0001abc=="` in the **copy only** (a `diff` check asserts the copy differs from the repo file in exactly one line; the repo file is never edited). With a product id the licence gate is on.
2. Runs that copy's `packaging/build.sh` (the real build) with `DEVELOPER_ID` set from `security find-identity -v -p codesigning` and `NOTARY_PROFILE` unset (`env -u`), so build.sh signs and never submits.
3. Tests the frozen `dist/shotfleet/shotfleet` in a clean environment (`env -i`, a temp `HOME` per simulated Mac, because the licence file is `~/Library/Application Support/shotfleet/licence.json`).
4. Starts a local fake Gumroad API (Python, 127.0.0.1, port chosen by the OS) and points the binary at it with `SHOTFLEET_GUMROAD_API`.
5. Tars the build like `packaging/release.sh`, serves it with `python3 -m http.server`, runs `site/public/install.sh` against it with a temp `HOME`, and runs `tools/golive/smoke.sh` against the same server.
6. Deletes its work dir when everything passed (`--keep` keeps it, `--reuse DIR` re-runs the checks on a kept build).

The script refuses to run without `SHOTFLEET_RC=1`, needs 3 GB free, and never touches `/opt/homebrew/bin`, `/usr/local/bin` or the real PATH (section 5).

## 2. Build

| | |
|---|---|
| Signing identity | `Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)` (one of 6 valid identities in the keychain) |
| Build time | 148 s on the first run, 75 s on the last (`packaging/build.sh`, includes `swiftc` for the OCR helper and `pip install` of pyinstaller and certifi) |
| Folder `dist/shotfleet/` | 22 MB, 70 files, 56 Mach-O files |
| Tarball | 9.2 to 9.4 MB (9,638,256 bytes), `shotfleet-0.1.0-macos-arm64.tar.gz` (the task expected hundreds of MB; it is not) |
| Disk | needs well under 1 GB for the build; the 3 GB pre-flight is slack |

```
$ file shotfleet           Mach-O 64-bit executable arm64
```

## 3. Bundle contents

| Check | Result |
|---|---|
| certifi's CA bundle is inside | `_internal/certifi/cacert.pem`, 240,216 bytes, SHA-256 identical to the one pip installed |
| Prebuilt OCR helper | `_internal/ocr` runs: `ocr --warmup` printed `Ready` in 1.1 s |
| Agent skills | `_internal/skill/{shotfleet,shotfleet-ci,shotfleet-review}/SKILL.md` |
| TLS actually verifies with it | `SHOTFLEET_GUMROAD_API=https://example.com/v2/licenses shotfleet activate <key>` printed `shotfleet: Gumroad answered 405`. A certificate failure would have said `can't reach the licence server (...CERTIFICATE_VERIFY_FAILED...)`. So the handshake with a public CA-signed host succeeds from the frozen program, and no licence file was written. |
| Gumroad and Polar code read `SHOTFLEET_KEY` | Gumroad path proven by behaviour (section 6, CI block). The Polar path (`SHOTFLEET_KEY=SHOTFLEET-...`) would call the real Polar API, so it was **not** run; it is covered by the unit tests only. |

## 4. Signature and Gatekeeper

```
$ codesign --verify --deep --strict --verbose=2 $W/src/dist/shotfleet/shotfleet
  valid on disk
  satisfies its Designated Requirement          [exit 0]
$ codesign -dvv ...
  Format=Mach-O thin (arm64)   flags=0x10000(runtime)
  Authority=Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)
  Authority=Developer ID Certification Authority / Apple Root CA
  Timestamp=2 Oct 2026 at 16:14:50   TeamIdentifier=2357A78TMR   Info.plist=not bound   Sealed Resources=none
$ codesign -d --entitlements - ...
  com.apple.security.cs.allow-unsigned-executable-memory = true
  com.apple.security.cs.disable-library-validation = true
$ spctl --assess --type execute -vv $W/src/dist/shotfleet/shotfleet
  rejected
  source=Unnotarized Developer ID
  origin=Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)       [exit 3]
```

- Every one of the 56 Mach-O files in the folder passes `codesign --verify --strict` (a loop in the script, because `--deep` on the executable alone does not walk a bare folder).
- Hardened runtime and a secure timestamp are present, the two things Apple's notary requires. This is not a notarization verdict.
- `spctl` rejects the build as "Unnotarized Developer ID", exactly as expected until Apple has accepted it. Apple accepted the 0.1.0 folder build once before (DISTRIBUTION.md, 2026-10-01); this build was not submitted.
- The signature survives `tar -czf` and extraction (`codesign --verify --deep --strict` on the extracted copy, and again on the copy `install.sh` installed).

**Quarantine test.** On a copy: `xattr -rw com.apple.quarantine "0081;00000000;Safari;" shotfleet/` (every file, as Archive Utility would after a browser download), then `shotfleet --version` from a shell:

```
$ shotfleet --version      (quarantined, signed, unnotarized)
  [hangs; killed by my 60 s / 90 s timeout (exit 143) in all four script runs]
  one run without a timeout: 5 min 15 s, then exit 137 (SIGKILL)
  a copy with the flag on the executable only: same, killed at 40 s
$ same bytes without the flag: shotfleet 0.1.0 in well under a second
```

So Gatekeeper does **not** let an unnotarized program run once the quarantine flag is on, even from a shell, here (macOS 27.0, while the machine had a load average of 400 to 900 from other sessions, which may explain the very long hang but not the refusal; it was never seen to run). The `curl | sh` install path sets no quarantine flag, so `install.sh` is unaffected (section 5). A tarball downloaded in a browser and unpacked WOULD be quarantined, so a notarized build is needed for that route. Gatekeeper for a *notarized* build run after a quarantined download is the one thing that still has to be tried (DISTRIBUTION.md records that the notarized 0.1.0 ran quarantined without a prompt). I did not find a clean control: a copy of `/bin/ls` with the flag is killed at once too (an Apple platform binary copied elsewhere loses its status), so that comparison proves nothing.

## 5. install.sh against the tarball (local server, temp HOME)

Same lines as `release.sh` produce the site's `download/` folder in a temp dir: the tarball under its install name, `shotfleet-macos-arm64.tar.gz.sha256` (`shasum -a 256 name > name.sha256`) and `VERSION`:

```
4d8d644cca06b191b72685ede97c3536852d5b560baf4b71fc33207d2380c131  shotfleet-macos-arm64.tar.gz
```

| Check | Result |
|---|---|
| Served archive matches the `.sha256` byte for byte | ok |
| `install.sh` with `SHOTFLEET_BASE=http://127.0.0.1:<port>/download`, variant A (first PATH candidate is a writable dir) | `installed shotfleet 0.1.0 to $HOME/fakebrew/bin`; the command is a link to `~/Library/Application Support/shotfleet/app/shotfleet`; `shotfleet --version` from the PATH prints `shotfleet 0.1.0`; installed copy still verifies; a second run (update) works |
| Variant B (no writable candidate) | `installed shotfleet 0.1.0 to $HOME/.local/bin` and `add it to your PATH: echo 'export PATH="...:$PATH"' >> ~/.zshrc`; works once on the PATH |
| A wrong `.sha256` | `download is corrupt (checksum mismatch); try again`, exit 1, nothing installed |
| Real PATH untouched | `ls -l /opt/homebrew/bin/shotfleet /usr/local/bin/shotfleet` identical before and after |
| `tools/golive/smoke.sh http://127.0.0.1:<port>` | 12 release lines ok (install.sh is a script and checks SHA-256, VERSION 0.1.0, archive non-empty (9,637,977 bytes), `.sha256` holds a hash and names the archive, archive matches it, install.sh's checksum logic accepts it, the unpacked program says `shotfleet 0.1.0`). Overall `smoke: 35 checks, 13 failed`: the 13 are the sale-page checks, which fail by design while the site is the waitlist. |

How the variants work: `install.sh` picks the first writable directory of `/opt/homebrew/bin`, `/usr/local/bin`, `~/.local/bin`, and this Mac has a writable Homebrew bin, so a plain run would have linked into the real PATH. The script therefore rewrites **only that one `for DIR in ...` line** into a temp copy (a `diff` check asserts exactly one line changed, and `tests/test_release_candidate.py` asserts the original line still exists). Variant A swaps the first two candidates for a dir inside the temp HOME (the "a Homebrew bin exists" branch), variant B removes them (the fallback). Not covered: the `/usr/local/bin` branch itself, which is the same code as the first.

## 6. The frozen program, free and licensed

Frozen program, no licence (HOME is empty):

```
$ shotfleet --version                                 shotfleet 0.1.0
$ shotfleet doctor                                    exit 0
    ok   maestro 2.0.10 / java 17+ / swiftc (OCR checks) / xcrun simctl / adb
    MISSING emulator, avdmanager, aapt2, system image (API 33+) (Android)  -> sdkmanager ...
    text recognition: ok ready in 0 s | in 3 of 5 runs under load: PROBLEM text recognition ready in 88 s (or 28 s, 37 s) but read ''
    iOS: ready   Android: not ready
$ shotfleet skill install --dir $W/run/skills         installed .../shotfleet, .../shotfleet-ci, .../shotfleet-review
$ SHOTFLEET_OCR='cat {image}.txt' shotfleet check fx/shots --strings 'fx/locales/*/translation.json' --report fx/rep --json
    checked 3 screenshots in 2 languages: 2 problem(s)       exit 1
      - el/2.png: shows en strings (3 lines) more than el (0)
      - en: missing 2.png
```

- `doctor` needs no `swiftc` in the frozen build (the OCR helper is bundled), does not crash, and exits 0. It took 17 s on a quiet Mac and 41 to 188 s when the machine was loaded (Maestro's JVM `--version` and the OCR warm-up). It also makes one plain GET of `https://shotfleet.com/download/VERSION` (currently 404; no way to turn that off, so it is the one network call in these tests that is not to 127.0.0.1 or example.com).
- The fixture is `tests/test_cli_claims.py`'s two-language one: el/2.png shows English (planted, found), en/2.png is missing (found). On an unloaded Mac macOS's own OCR also reports `en/1.png: no text found (blank or still loading?)` because the PNG is only a header; when macOS text recognition is stuck the program says so and uses `--ocr-command` for everything and that third line disappears. The script accepts both.

Free tier on the gate-ON build (no licence file), config with `locales = ["fr", "it", "pt"]` and an app that ships only el and en, so `run` can never reach a simulator:

```
$ shotfleet run ft/shotfleet.toml                                              exit 2
  note: `export` and every language in `run` need a licence: shotfleet activate <key> (buy one at https://shotfleet.com/#price; checkout is on Gumroad). `check` is free, and `run` captures up to 2 languages without one.
  free tier: capturing 2 of 3 languages (fr, it). `shotfleet activate <key>` unlocks every language (https://shotfleet.com/#price)
  skip fr: app has no fr.lproj
  skip it: app has no it.lproj
  shotfleet: none of those languages are in the app. It ships: el, en
$ shotfleet export ex/out --fastlane ex/fastlane                               exit 2
  shotfleet: `export` and every language in `run` need a licence: shotfleet activate <key> ...
$ (nothing was written to ex/fastlane; `export --json` printed {"exit": 2})
```

This proves the cap (2 of 3) and the refusal on the real frozen gate-ON build without a device: `cap_locales` runs before any simulator is created, and the all-unknown languages stop the run at "none of those languages are in the app" before `booting`. The output has no `booting` line. What it cannot prove: that the first two languages then actually capture. That needs a device (gate 9/10).

Licence against the local fake Gumroad API (contract = `gumroad_verify`: form POST `product_id`, `license_key`, `increment_uses_count`; 404 + `{success:false,message}` for an unknown key or another product; 200 + `{success, uses, purchase:{refunded, chargebacked, disputed, dispute_won}}`; `uses` counts every verify unless `increment_uses_count=false`; the same shape as the fake in `tests/test_shotfleet.py`). The fake is checked against `gumroad_verify` itself in `tests/test_release_candidate.py`.

| Step | Result |
|---|---|
| unknown key | `that key didn't activate: That license does not exist for the provided product.`, exit 2, no licence file |
| refunded key | `that key didn't activate: the purchase was refunded.`, exit 2, **uses stays 0** |
| `activate <good key>` | `activated on <host>. Thanks for buying shotfleet!`, uses = 1, `licence.json` has `store: gumroad` |
| `activate` again on the same Mac | ok, **uses still 1** |
| `run` with the licence | no `note:`, no `free tier:` line (all three languages go on, none is capped) |
| `export` with the licence | `exported 1 listings to ...: de-DE`, file in `fastlane/screenshots/de-DE` |
| licence 3 days old | no network call at all (re-checked at most weekly) |
| licence 8 days old | re-checked, `increment_uses_count=false`, uses unchanged, `checked` timestamp refreshed, export works |
| 8 days old and refunded since | `this licence is no longer valid (the purchase was refunded). https://shotfleet.com/#price`; `run` then prints that as a note and applies the 2-language cap |
| 10 days old, Gumroad answers 503 | not a verdict: export works |
| 10 and 29 days old, server DOWN (process killed, connection refused) | export works (30-day offline grace) |
| 31 days old, server DOWN | `couldn't reach the licence server for 30 days; connect once to keep using every language in `run``, exit 2; `run` falls back to the cap |
| 31 days old, server back | re-check passes, export works |
| `deactivate` | `removed from this Mac. Gumroad can't give the activation back from here: if all 3 are used, email hello@shotfleet.com and I'll reset the count`; licence file gone; `export` refused again |
| three Macs, then a fourth | Macs 2 and 3 activate (uses 2, 3 after the deactivated Mac 1 counted); the 4th: `this key has used all 3 activations. Email hello@shotfleet.com and I'll reset the count`, exit 2, **uses stays 3**, no licence file |
| a Mac that already holds the key, all 3 used | re-activates fine |
| CI: `SHOTFLEET_KEY=<good key>` | `export` works, no licence file written, uses unchanged |
| CI: refunded `SHOTFLEET_KEY` | `SHOTFLEET_KEY isn't a valid licence (the purchase was refunded)`, exit 2 |
| CI: `run` with `SHOTFLEET_KEY` | no cap |
| CI: Gumroad outage | does not fail the build |
| every request the fake received | carried this build's product id and only the three form fields |

Two script bugs found on the way, both fixed: killing the fake server killed only its wrapper shell (the 31-day offline case then passed because the server was still up), and a trailing slash in `$TMPDIR` made one message comparison fail. The last runs prove the offline cases with a really dead port.

## 7. Findings (reported, not fixed; I did not touch `shotfleet.py`)

1. **Quarantined, unnotarized builds do not run** (section 4). Not a bug, a requirement: a notarized build is needed for any browser download; the `curl | sh` route is unaffected. Re-run the quarantine step on the notarized build to close this.
2. **A truncated or corrupt `licence.json` is not handled** (`require_licence`, `cmd_deactivate`, `shotfleet.py` around lines 2473 and 2504). Reproduced on the frozen build with `{"key": "ABC`:
   ```
   $ shotfleet export ...   shotfleet: Unterminated string starting at: line 1 column 9 (char 8)   exit 2
   $ shotfleet run ...      same message, exit 2 (no free-tier fallback: apply_free_tier only catches NoLicence)
   $ shotfleet deactivate   same message, exit 2 (cannot remove the file)
   $ shotfleet activate <key>   works (cmd_activate already catches ValueError)
   ```
   `licence.json` is written with a plain `write_text` (not atomic), so a crash or full disk during the weekly refresh can leave it half written. A buyer would see a raw JSON error and have to find and delete the file. Suggested fix: treat unreadable JSON like a missing licence in `require_licence` and `cmd_deactivate` (raise `NoLicence` / delete the file), and write via a temp file and `os.replace`.
3. **`doctor` can print a false PROBLEM for text recognition** on a busy Mac: `ready in 37 s but read ''` (also 88 s and 28 s) in 3 of 6 frozen runs while the Mac's load average was 400 to 900 (other sessions building). The same helper binary prints `Ready` in 1 s when idle, and the next `doctor` said `ok ... ready in 0 s`. The helper's `--warmup` returned an empty result. It is a warning only (exit 0) and `check` falls back to `--ocr-command` when macOS's OCR is stuck, but a first-time buyer on a loaded Mac would see PROBLEM. Not shown to be frozen-specific.
4. **`doctor` takes 17 s on a quiet Mac and 40 to 190 s under load** (Maestro `--version` starts a JVM; the OCR warm-up). Fine, but it says nothing while it waits except the text-recognition line.
5. **Unintended real API call (mine, not a program bug).** While checking item 2 I ran `shotfleet activate ABCDEF12-34567890-ABCDEF12-34567890` on the frozen build WITHOUT `SHOTFLEET_GUMROAD_API` set, so it posted once to `https://api.gumroad.com/v2/licenses/verify` with the test product id `RCTESTPRODUCT0001abc==`, a made-up key and `increment_uses_count=false`. Gumroad answered that the licence does not exist for that product; nothing was created or changed there. It is the only real Gumroad call; the script always sets the fake's URL.
6. The `check` fixture's blank `en/1.png` depends on macOS OCR state (above); not a bug.

## 8. What could not be tested here

- **Apple's notarization verdict.** The build is signed with hardened runtime and a timestamp, but nothing was submitted. Needs `NOTARY_PROFILE=KeysiNotary packaging/release.sh` (Manu's go; `release.sh` also deploys, so run `packaging/build.sh` with `DEVELOPER_ID` and `NOTARY_PROFILE=KeysiNotary` set instead, which notarizes but does not deploy), then `spctl --assess` must say `accepted source=Notarized Developer ID`.
- **A real Gumroad key**: activation count semantics (does `uses` really include the verify that carries `increment_uses_count=true`? is the 404 body really that message? do `refunded`/`chargebacked` really flip?), the product id format, and the License key block. Only Manu's product and one purchase plus refund can settle this (gate 5 stays partial).
- **Polar and Lemon Squeezy paths** against their real APIs (would be real calls; unit-tested only).
- **Gatekeeper on a notarized, browser-downloaded build**, and a clean Mac or user (Maestro, Java, no Xcode CLT, no Homebrew): cold test 3.
- Whether the 2 free languages then really capture on devices (needs a simulator; gate 9 and 10).

## 9. Reproduce

```
SHOTFLEET_RC=1 tools/release-candidate.sh              # about 4 to 8 minutes; --no-sign to skip signing; --keep to keep the temp dir
python3 -m unittest tests.test_release_candidate       # syntax, refusal without SHOTFLEET_RC=1, fake server vs gumroad_verify, fixtures (5 s)
```
