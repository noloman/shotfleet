"""What the site and README say the program prints and accepts, checked against the program itself.

Run: python3 -m unittest discover -s tests
"""
import contextlib, io, json, os, re, shlex, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

INDEX = (ROOT / "site/public/index.html").read_text()
README = (ROOT / "README.md").read_text()
SOURCE = (ROOT / "shotfleet.py").read_text()


def png(w=1320, h=2868):
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2]) + b"\0" * 8 + b"IDAT"


def shape(line):
    return re.sub(r"\d+", "N", line)


EN = {"a": "Next", "b": "Settings", "c": "Start Training"}
EL = {"a": "Επόμενο", "b": "Ρυθμίσεις", "c": "Έναρξη προπόνησης"}
STRINGS = {"en": EN, "el": EL}


def fake_vision():
    """macOS text recognition stubbed to read each screenshot's .txt sidecar, like the `cat {image}.txt` OCR command. The real one
    waits on macOS's model compile: 139 s and 214 s for one test each on a loaded Mac (research/speed-2026-10-05.md)."""
    def read(ocr, png, timeout=120):
        t = Path(f"{png}.txt").read_text() if Path(f"{png}.txt").exists() else ""
        return {"text": t, "chars": len(t), "lang": None, "langs": {}, "lines": []}
    stack = contextlib.ExitStack()
    for name, fake in (("warm_up_ocr", lambda *a, **k: True), ("read_text", read)):  # ocr_tool and its --langs list stay real: no model compile
        stack.enter_context(mock.patch.object(sf, name, side_effect=fake))
    return stack


def fixture(d):
    """Two languages from translation files: el/1.png shows Greek (fine), el/2.png shows English (a problem). OCR is `cat`."""
    en, el = EN, EL
    shots = d / "shots"
    for lp, words in (("el", el), ("en", en)):
        (shots / lp).mkdir(parents=True)
        (shots / lp / "1.png").write_bytes(png()); (shots / lp / "1.png.txt").write_text("\n".join(words.values()))
    (shots / "el" / "2.png").write_bytes(png()); (shots / "el" / "2.png.txt").write_text("\n".join(en.values()))
    for lp, words in (("en", en), ("el", el)):
        (d / "locales" / lp).mkdir(parents=True)
        (d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
    return shots


def run_main(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sf.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TerminalSample(unittest.TestCase):
    """The sample run on the site and in the README is the program's real output format."""
    SAMPLES = {"index.html": INDEX, "README.md": README}

    def lines(self, text):
        text = re.sub(r"<[^>]+>", "", text)
        return [l.strip() for l in text.splitlines()]

    def test_check_summary_line_matches_what_cmd_check_prints(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            with fake_vision(), contextlib.redirect_stdout(io.StringIO()) as out:
                sf.cmd_check(shots, strings=STRINGS, report_dir=d / "rep", ocr_command="cat {image}.txt")
        printed = [l for l in out.getvalue().splitlines() if l.startswith("checked ")]
        self.assertEqual(len(printed), 1, out.getvalue())
        for name, text in self.SAMPLES.items():
            sample = [l for l in self.lines(text) if l.startswith("checked ")]
            self.assertEqual([shape(l) for l in sample], [shape(printed[0])], name)

    def test_run_lines_match_the_format_strings_in_the_code(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            sf.print_result("ar", {"ok": True, "screenshots": 4}, 4)
        printed = out.getvalue().rstrip("\n")
        templates = {kind: re.sub(r"\{[^}]*\}", "N", m) for kind, m in
                     (("captured", re.search(r'f"(captured .*? simulators)"', SOURCE).group(1)),
                      ("capturing", re.search(r'f"(capturing .*? simulators\.\.\.)"', SOURCE).group(1)))}
        for name, text in self.SAMPLES.items():
            lines = self.lines(text)
            self.assertIn(printed, lines, name)  # "ok   ar       4/4 screenshots", spaces and all
            for kind, template in templates.items():
                sample = [l for l in lines if l.startswith(kind + " ")]
                self.assertEqual([shape(l) for l in sample], [template], (name, kind))

    def test_sample_numbers_agree(self):
        for name, text in self.SAMPLES.items():
            t = "\n".join(self.lines(text))
            self.assertRegex(t, r"captured 18/18 locales in \d+s on 4 simulators", name)
            self.assertIn("capturing 18 locales on 4 simulators...", t, name)
            self.assertIn("checked 72 screenshots in 18 languages: 0 problem(s)", t, name)  # 18 x 4 = 72


class DocumentedCommands(unittest.TestCase):
    """Every `shotfleet ...` command the README and the site show parses with the real argument parser."""
    def commands(self):
        found = []
        for block in re.findall(r"```(?:bash|sh)?\n(.*?)```", README, flags=re.S):
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("shotfleet ") and "<" not in line and "|" not in line and "..." not in line:
                    found.append(line)
        found += [c for c in re.findall(r"`(shotfleet [^`]+)`", README) if "<" not in c and "..." not in c and "|" not in c
                  and c.split()[1] in sf.COMMANDS and (len(c.split()) > 2 or c.split()[1] in ("run", "doctor"))]
        found += [l.strip().removeprefix("$ ") for l in re.findall(r'<p class="cmd"[^>]*><span>\$</span>([^<]*)</p>', INDEX)]
        return found

    def test_the_documented_commands_parse(self):
        cmds = self.commands()
        self.assertGreaterEqual(len(cmds), 6)
        for cmd in cmds:
            argv = shlex.split(cmd, comments=True)[1:]
            with self.subTest(cmd=cmd), mock.patch.object(sf, "main_cmd", side_effect=lambda a: a), \
                 mock.patch.object(sf.shutil, "which", return_value=None):
                self.assertTrue(hasattr(sf.main(argv), "cmd"))

    def test_ci_recipe_uses_the_installed_command_and_a_json_flag_that_exists(self):
        recipe = README.split("# .github/workflows/screenshots.yml")[1].split("```")[0]
        self.assertNotIn("shotfleet.py", recipe)
        self.assertIn("install.sh | sh", recipe)
        line = next(l for l in recipe.splitlines() if "shotfleet check" in l).split("run:")[1].split(">")[0]
        seen = []
        with mock.patch.object(sf, "main_cmd", side_effect=lambda a: seen.append(a) or 0), mock.patch.object(sf, "LAST_REPORT", None):
            with contextlib.redirect_stdout(io.StringIO()):
                sf.main(shlex.split(line)[1:])
        self.assertEqual((seen[0].cmd, seen[0].json), ("check", True))

    def test_json_flag_is_on_run_check_and_export(self):
        for argv in (["run", "--json"], ["check", "x", "--json"], ["export", "x", "--fastlane", "y", "--json"]):
            with self.subTest(argv=argv), mock.patch.object(sf, "main_cmd", return_value=0), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sf.main(argv), 0)
        self.assertTrue("`run`, `check` and `export` take `--json`" in README)


class JsonReports(unittest.TestCase):
    def test_check_json_is_valid_json_with_the_documented_keys_and_nothing_else_on_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            with fake_vision(): code, out, err = run_main("check", str(shots), "--strings", str(d / "locales/*/translation.json"),
                                                       "--ocr-command", "cat {image}.txt", "--report", str(d / "rep"), "--json")
        report = json.loads(out)
        self.assertEqual(code, 1, err)
        self.assertEqual(report["exit"], 1)
        self.assertIsInstance(report["problems"], list); self.assertTrue(report["problems"])
        self.assertEqual(len(report["screenshots"]), 3)
        self.assertIn("checked 3 screenshots in 2 languages", err)  # progress goes to stderr

    def test_export_json_reports_what_was_written_and_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            for lp in ("de", "ja"):
                (out / "raw" / lp).mkdir(parents=True); (out / "raw" / lp / "01.png").write_bytes(b"x")
            (out / "run.json").write_text(json.dumps({"platform": "ios"}))
            (out / "check.json").write_text(json.dumps({"problems": ["ja/01.png: shows en strings"]}))
            code, stdout, err = run_main("export", str(out), "--fastlane", str(Path(d) / "fl"), "--json")
        self.assertEqual(json.loads(stdout), {"exit": 1, "exported": ["de-DE"], "skipped": ["ja"]})
        self.assertIn("exported 1 listings", err)


class CheckPromises(unittest.TestCase):
    def test_check_writes_its_report_to_shotfleet_check_and_leaves_the_folder_alone(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            before = sorted(str(p.relative_to(shots)) for p in shots.rglob("*"))
            cwd = os.getcwd(); os.chdir(d)
            try:
                with fake_vision(), contextlib.redirect_stdout(io.StringIO()):
                    sf.cmd_check(shots, strings=STRINGS, ocr_command="cat {image}.txt")
            finally: os.chdir(cwd)
            self.assertEqual(sorted(str(p.relative_to(shots)) for p in shots.rglob("*")), before)
            self.assertTrue((d / "shotfleet-check/check.json").is_file()); self.assertTrue((d / "shotfleet-check/index.html").is_file())

    def test_index_is_a_grid_with_a_row_per_language_a_column_per_screen_and_problems_outlined(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            with fake_vision(), contextlib.redirect_stdout(io.StringIO()):
                sf.cmd_check(shots, strings=STRINGS, report_dir=d / "rep", ocr_command="cat {image}.txt")
            page = (d / "rep/index.html").read_text()
        self.assertEqual(page.count("<tr>"), 3)  # header + el + en
        self.assertEqual(len(re.findall(r"<th>[^<]+</th>", page.split("</tr>")[0])), 2)
        self.assertIn("img.bad{border-color:#d33}", page)
        self.assertRegex(page, r'el/2\.png"><img [^>]*class="bad"')  # the English screenshot in the Greek row
        self.assertNotRegex(page, r'el/1\.png"><img [^>]*class="bad"')
        self.assertIn('<td class="missing">missing</td>', page)  # and a missing screen is a red cell

    def test_check_needs_no_licence_in_the_released_build(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf.sys, "frozen", True, create=True), \
             mock.patch.object(sf, "LICENCE_FILE", Path(d) / "none.json"), \
             mock.patch.object(sf, "require_licence", side_effect=AssertionError("check must not ask for a licence")), \
             mock.patch.object(sf, "cmd_check", return_value=0), mock.patch.object(sf, "cmd_doctor", return_value=0), \
             mock.patch.object(sf, "cmd_init", return_value=0):
            self.assertEqual(sf.main(["check", d]), 0)
            self.assertEqual(sf.main(["doctor"]), 0)
            self.assertEqual(sf.main(["init", "My.app"]), 0)


class Versions(unittest.TestCase):
    def test_version_makes_no_network_call(self):
        with mock.patch.object(sf.urllib.request, "urlopen", side_effect=AssertionError("no network for --version")):
            with self.assertRaises(SystemExit) as e, contextlib.redirect_stdout(io.StringIO()) as out: sf.main(["--version"])
        self.assertEqual(e.exception.code, 0); self.assertEqual(out.getvalue().strip(), f"shotfleet {sf.VERSION}")

    def test_doctor_announces_a_newer_release_from_the_sites_version_file(self):
        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False
        seen = []
        def fake(url, timeout):
            seen.append(url); return Resp(b"9.9.9\n")
        with mock.patch.object(sf.urllib.request, "urlopen", fake):
            self.assertEqual(sf.latest_release(), "9.9.9")
        self.assertEqual(seen, ["https://shotfleet.com/download/VERSION"])
        with mock.patch.object(sf.urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertIsNone(sf.latest_release())  # silent when offline


class NothingIsUploaded(unittest.TestCase):
    def test_the_program_only_names_the_servers_it_talks_to(self):
        hosts = set(re.findall(r"https?://([A-Za-z0-9.-]+)", SOURCE))
        allowed = {"shotfleet.com",  # install hint, /download/VERSION
                   "api.gumroad.com",  # licence checks
                   "127.0.0.1",  # local test servers
                   "get.maestro.mobile.dev",  # text of an install hint
                   "developer.android.com",  # text of an install hint (Linux: where the Android command-line tools come from)
                   # `doctor --fix` only, after the user agreed to the plan (test_downloads_are_only_reachable_from_doctor_fix):
                   "github.com",  # the pinned Maestro release
                   "api.adoptium.net", "adoptium.net",  # the Java runtime and its checksum
                   "dl.google.com"}  # Google's Android command-line tools and their manifest
        self.assertEqual(hosts - allowed, set())


if __name__ == "__main__":
    unittest.main()


class McpCheckDoesNotTouchTheFolder(unittest.TestCase):
    def test_the_mcp_check_tool_writes_its_report_elsewhere_and_config_accepts_avd_tablet(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as cwd:
            d = Path(d); shots = fixture(d)
            before = sorted(p.relative_to(shots).as_posix() for p in shots.rglob("*"))
            old = os.getcwd(); os.chdir(cwd)
            try:
                real = sf.cmd_check  # the fake reader stands in for macOS OCR, which compiles a model on first use
                with fake_vision(), mock.patch.object(sf, "cmd_check", lambda *a, **k: real(*a, **{**k, "ocr_command": "cat {image}.txt"})):
                    text, err = sf.mcp_call("check", {"folder": str(shots), "strings": str(d / "locales/*/translation.json")})
            finally:
                os.chdir(old)
            after = sorted(p.relative_to(shots).as_posix() for p in shots.rglob("*"))
            self.assertFalse(err, text)
            self.assertEqual(before, after)  # nothing was written into the checked folder
            self.assertTrue((Path(cwd) / "shotfleet-check" / "index.html").exists())
        self.assertIn("avd_tablet", sf.KEYS["android"])



def word_png(rows, scale=12):
    """A real grayscale PNG of black pixel-font letters on white: '1' is ink. Vision reads it (the fixture PNGs are header-only)."""
    import struct, zlib
    w, h = (len(rows[0]) + 4) * scale, (len(rows) + 4) * scale
    ink = lambda x, y: 0 <= y // scale - 2 < len(rows) and 0 <= x // scale - 2 < len(rows[0]) and rows[y // scale - 2][x // scale - 2] == "1"
    raw = b"".join(b"\0" + bytes(0 if ink(x, y) else 255 for x in range(w)) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


@unittest.skipUnless(sf.vision_available(), "macOS text recognition exists only on a Mac")
class RealVisionSmoke(unittest.TestCase):
    """The one test that runs the real macOS text recognition; every other test stubs it (fake_vision), because a cold model
    compile takes minutes. Builds the helper, warms it up (it draws and reads "Ready") and reads a real picture of "EEE".
    Skipped, not failed, when macOS's recognition itself doesn't answer: a busy or freshly restarted Mac, not a shotfleet bug."""
    def test_real_macos_text_recognition_warms_up_and_reads_a_word(self):
        ocr = sf.ocr_tool()
        if not sf.warm_up_ocr(ocr, timeout=90):  # macOS's state, not shotfleet's (check falls back then): seen at load 800, an e5rt error
            self.skipTest("macOS text recognition did not answer in 90 s: " + sf.ocr_not_answering())
        e = ["11111", "10000", "10000", "11110", "10000", "10000", "11111"]
        with tempfile.TemporaryDirectory() as d:
            png = Path(d, "word.png"); png.write_bytes(word_png([a + "0" + b + "0" + c for a, b, c in zip(e, e, e)]))
            r = sf.read_text(ocr, png)
        self.assertIn("EEE", r["text"], r)
