"""The 2026-10-07 security review (shotfleet-rc-build/code-review-2026-10-07/security.md): each finding's proof, as a test.
Marker files only, in temp folders; no device, no network."""
import contextlib, io, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


def png(w=1080, h=1920):  # just enough of a PNG for the size rules
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\0\0\0"


def quiet(f, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): return f(*a, **k)


class McpRunRunsNoConfigCommandUnlessAsked(unittest.TestCase):
    """S1: `run` over MCP ran [capture].build (/bin/sh -c) although hooks were off."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()).resolve()
        self.marker = self.d / "MARKER"
        p = mock.patch.object(sf, "apply_free_tier"); p.start(); self.addCleanup(p.stop)

    def config(self, text):
        cfg = self.d / "shotfleet.toml"; cfg.write_text(text); return str(cfg)

    def test_a_capture_build_does_not_run_without_hooks_true(self):
        cfg = self.config(f'[ios]\n[capture]\nbuild = "touch {self.marker}; exit 1"\nxctestrun = "build/*.xctestrun"\n')
        text, err = quiet(sf.mcp_call, "run", {"config": cfg})
        self.assertTrue(err); self.assertFalse(self.marker.exists(), "the [capture] build ran over MCP without hooks: true")
        self.assertIn("[capture] build", text); self.assertIn("hooks: true", text)
        text, err = quiet(sf.mcp_call, "run", {"config": cfg, "hooks": True})  # asked for: it runs (and fails with exit 1, as written)
        self.assertTrue(self.marker.exists()); self.assertIn("the [capture] build failed", text)
        self.assertFalse(sf.NO_HOOKS); self.assertTrue(sf.CONFIG_COMMANDS)

    def test_simctl_and_shell_setup_commands_are_refused_without_hooks_true(self):
        for section in (f'[ios]\napp = "A.app"\nsimctl = ["spawn booted /usr/bin/touch {self.marker}"]\n',
                        f'[android]\napk = "a.apk"\nshell = ["touch /sdcard/x"]\n'):
            with self.subTest(section=section.split("]")[0]), mock.patch.object(sf, "cmd_run", side_effect=AssertionError("run started")):
                text, err = quiet(sf.mcp_call, "run", {"config": self.config(section)})
                self.assertTrue(err); self.assertIn("simctl" if "simctl" in section else "[android] shell", text)

    def test_hooks_alone_are_still_skipped_not_refused(self):  # unchanged since 0.1.4
        cfg = self.config(f'[ios]\napp = "A.app"\n[hooks]\nbefore_run = "touch {self.marker}"\n')
        with mock.patch.object(sf, "cmd_run", lambda c, l: sf.run_hook({"before_run": f"touch {self.marker}"}, "before_run", c, {})[0]):
            text, err = quiet(sf.mcp_call, "run", {"config": cfg})
        self.assertFalse(err, text); self.assertFalse(self.marker.exists())

    def test_the_last_guard_stops_setup_commands_and_the_build_even_past_mcp_call(self):
        dev = mock.Mock()
        with mock.patch.object(sf, "CONFIG_COMMANDS", False):
            with self.assertRaises(sf.Fail): sf.run_setup(dev, "simctl", ["spawn booted /usr/bin/true"])
            with self.assertRaises(sf.Fail): sf.run_setup(dev, "shell", ["true"])
            with self.assertRaises(sf.Fail): quiet(sf.capture_build, {"build": f"touch {self.marker}"}, str(self.d / "x.toml"), self.d / "out")
        dev.run.assert_not_called(); dev.adb.assert_not_called(); self.assertFalse(self.marker.exists())

    def test_the_tool_says_so(self):
        run = next(t for t in sf.MCP_TOOLS if t["name"] == "run")
        for words in ("[capture] build", "[ios] simctl", "[android] shell", "hooks: true"): self.assertIn(words, run["description"])
        self.assertIn("[capture] build", run["inputSchema"]["properties"]["hooks"]["description"])


class McpCheckRunsNoProgram(unittest.TestCase):
    """S2: `check` over MCP ran any program passed as ocr_command, under readOnlyHint: true."""
    def test_ocr_command_is_refused_and_never_runs(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d).resolve(); marker = d / "MARKER"
            for lp in ("en", "de"):
                (d / "shots" / lp).mkdir(parents=True); (d / "shots" / lp / "1.png").write_bytes(png())
                (d / f"{lp}.json").write_text(json.dumps({"next": "Next" if lp == "en" else "Weiter"}))
            with mock.patch.object(sf, "is_mac", lambda: False), mock.patch.object(sf, "vision_available", lambda: False):
                text, err = quiet(sf.mcp_call, "check", {"folder": str(d / "shots"), "strings": [str(d / "*.json")],
                                                         "report": str(d / "rep"), "ocr_command": f"/usr/bin/touch {marker}"})
            self.assertTrue(err); self.assertIn("--ocr-command", text)
            self.assertFalse(marker.exists(), "check ran the ocr_command passed over MCP")

    def test_annotations_match_what_each_tool_does(self):
        tools = {t["name"]: t for t in sf.MCP_TOOLS}
        self.assertIs(tools["doctor"]["annotations"]["readOnlyHint"], True)
        self.assertIs(tools["check"]["annotations"]["readOnlyHint"], False)  # it writes check.json and index.html
        self.assertNotIn("ocr_command", tools["check"]["inputSchema"]["properties"])
        for name in ("check", "run"): self.assertIs(tools[name]["inputSchema"]["additionalProperties"], False)

    def test_path_and_list_arguments_are_checked(self):
        for name, args in (("check", {"folder": 5}), ("check", {"folder": "x", "strings": [5]}),
                           ("run", {"config": "x.toml", "locales": "de"}), ("run", {"config": ["x"]})):
            with self.subTest(name=name, args=args):
                text, err = quiet(sf.mcp_call, name, args); self.assertTrue(err, text)


class LocalesAreNeverPaths(unittest.TestCase):
    """S3: a locale from a translation file became a folder name: run deleted <out>/raw/../../VICTIM."""
    def test_an_arb_locale_with_a_path_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "app_en.arb").write_text(json.dumps({"@@locale": "en", "next": "Next"}))
            (d / "app_xx.arb").write_text(json.dumps({"@@locale": "../../VICTIM", "next": "Weiter"}))
            strings = quiet(sf.load_strings_files, [str(d / "*.arb")])
        self.assertEqual(set(strings), {"en"})

    def test_a_run_never_deletes_outside_its_output_folder(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d).resolve()
            (d / "proj/l10n").mkdir(parents=True); (d / "proj/out/raw").mkdir(parents=True)  # an earlier run's output
            victim = d / "proj/VICTIM"; victim.mkdir(); (victim / "keep.txt").write_text("mine")  # <out>/raw/../../VICTIM
            (d / "proj/flow.yaml").write_text("appId: x\n---\n- launchApp\n- tapOn: \"Next\"\n- takeScreenshot: 01\n")
            (d / "proj/l10n/app_en.arb").write_text(json.dumps({"@@locale": "en", "next": "Next"}))
            (d / "proj/l10n/app_de.arb").write_text(json.dumps({"@@locale": "de", "next": "Weiter"}))
            (d / "proj/l10n/app_xx.arb").write_text(json.dumps({"@@locale": "../../VICTIM", "next": "Next!"}))
            cfg = {"apk": "a.apk", "package": "com.x", "flow": "flow.yaml", "strings": "l10n/*.arb", "base_locale": "en"}
            path = lambda p: d / "proj" / p
            stop = type("Stop", (Exception,), {})
            with mock.patch.object(sf, "framework_hint"), mock.patch.object(sf, "read_maestro_version", lambda: "2.11.0"), \
                 mock.patch.object(sf, "fit_parallel", side_effect=stop):
                with self.assertRaises(stop): quiet(sf.android_run_inner, cfg, path, d / "proj/out", None, None)
            self.assertTrue((victim / "keep.txt").exists(), "run deleted a folder outside its output folder")

    def test_bad_locales_are_refused_where_they_come_in(self):
        with self.assertRaises(sf.Fail) as e: sf.cmd_run("nothing.toml", ["de", "../x"])
        self.assertIn("not a language code", str(e.exception))
        with self.assertRaises(sf.Fail): sf.check_section({"locales": ["de/../../x"]}, "ios", "shotfleet.toml")
        with self.assertRaises(sf.Fail): sf.check_section({"base_locale": ".."}, "ios", "shotfleet.toml")
        with self.assertRaises(sf.Fail): sf.check_section({"package": "com.x; reboot"}, "android", "shotfleet.toml")
        with self.assertRaises(sf.Fail): sf.check_section({"avd": "../evil"}, "android", "shotfleet.toml")
        sf.check_section({"locales": ["de", "pt-BR", "zh-Hant-HK", "es-419", "en_GB"], "package": "com.example.app", "avd": "shotfleet_android"},
                         "android", "shotfleet.toml")
        text, err = quiet(sf.mcp_call, "run", {"config": "nothing.toml", "locales": ["../x"]})
        self.assertTrue(err); self.assertIn("not a language code", text)

    def test_the_last_guard_refuses_a_path_outside_the_folder(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sf.inside(d, "raw", "de"), Path(d, "raw", "de"))
            with self.assertRaises(sf.Fail): sf.inside(d, "raw", "../../x")


@mock.patch.object(sf, "USE_DEVICE_LOCK", True)
class LockFilesInTmp(unittest.TestCase):
    """S4: /tmp/shotfleet-<key>.lock was opened through a symlink with 0o666, so another user could make shotfleet overwrite a file."""
    def setUp(self):
        self.key = f"secrevtest-{os.getpid()}"
        self.lock = Path(f"/tmp/shotfleet-{self.key}.lock")
        self.lock.unlink(missing_ok=True); self.addCleanup(self.lock.unlink, missing_ok=True)
        self.d = Path(tempfile.mkdtemp())

    def test_a_symlinked_lock_is_not_followed(self):
        victim = self.d / "victim.txt"; victim.write_text("precious")
        self.lock.symlink_to(victim)
        with quiet(sf.device_lock, self.key): pass
        self.assertEqual(victim.read_text(), "precious")

    def test_the_warm_up_lock_does_not_follow_a_symlink_either(self):
        target = self.d / "made-by-shotfleet"
        self.lock.symlink_to(target)
        with mock.patch.object(sf, "OCR_LOCK", str(self.lock)): self.assertIsNone(quiet(sf.ocr_warmup_lock, 1))
        self.assertFalse(target.exists())

    def test_a_new_lock_file_is_only_readable_by_its_user(self):
        with sf.device_lock(self.key): self.assertEqual(self.lock.stat().st_mode & 0o777, 0o600)

    def test_a_fifo_in_its_place_is_left_alone(self):
        os.mkfifo(self.lock)
        with quiet(sf.device_lock, self.key): pass  # no hang, no lock, the run goes on


if __name__ == "__main__":
    unittest.main()
