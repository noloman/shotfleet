"""0.1.7 reliability: a runtime guard, bounded simulator calls, an overload warning, and retries that only cover device failures
(`--retry-failed`). Fakes only: no simulator, emulator, Maestro or network."""
import contextlib, io, json, os, plistlib, re, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

needs_mac = unittest.skipUnless(sys.platform == "darwin", "iOS run path is macOS only")


def rt(version, available=True):
    return {"identifier": f"com.apple.CoreSimulator.SimRuntime.iOS-{version.replace('.', '-')}", "name": f"iOS {version}", "version": version,
            "platform": "iOS", "isAvailable": available}


class RuntimeGuard(unittest.TestCase):
    def test_the_newest_runtime_that_is_not_known_to_hang_wins_and_one_line_says_why(self):
        ident, note = sf.pick_ios_runtime([rt("26.4"), rt("27.0"), rt("26.0")])
        self.assertEqual(ident, rt("26.4")["identifier"])
        self.assertEqual(note.count("\n"), 0)
        self.assertIn("using iOS 26.4", note); self.assertIn("iOS 27.0", note); self.assertIn("freeze at boot", note)
        self.assertIn('runtime = "com.apple.CoreSimulator.SimRuntime.iOS-27-0"', note)  # how to use it anyway

    def test_the_order_simctl_lists_them_in_does_not_matter(self):
        self.assertEqual(sf.pick_ios_runtime([rt("26.4"), rt("26.10"), rt("26.9")])[0], rt("26.10")["identifier"])  # 26.10 is newer than 26.9

    def test_a_good_runtime_alone_is_picked_with_no_note(self):
        self.assertEqual(sf.pick_ios_runtime([rt("26.4")]), (rt("26.4")["identifier"], ""))
        self.assertEqual(sf.pick_ios_runtime([rt("27.1"), rt("26.4")])[1], "")  # 27.1 is not on the list

    def test_when_only_a_bad_runtime_is_installed_it_is_used_with_a_warning(self):
        ident, note = sf.pick_ios_runtime([rt("27.0")])
        self.assertEqual(ident, rt("27.0")["identifier"])
        self.assertIn("warning", note); self.assertIn("only iOS runtime installed", note); self.assertIn("runtime = ", note)

    def test_the_list_is_data(self):
        ident, note = sf.pick_ios_runtime([rt("26.4"), rt("26.5")], bad={"26.5": "it crashes"})
        self.assertEqual(ident, rt("26.4")["identifier"]); self.assertIn("it crashes", note)
        self.assertEqual(sf.BAD_IOS_RUNTIMES.keys(), {"27.0"})

    def test_run_prints_the_choice_and_a_runtime_in_the_config_is_never_second_guessed(self):
        listed = json.dumps({"runtimes": [rt("26.4"), rt("27.0"), rt("26.2", available=False)]})
        with mock.patch.object(sf, "simctl_sh", return_value=subprocess.CompletedProcess([], 0, listed, "")), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sf.latest_ios_runtime(), rt("26.4")["identifier"])
        self.assertIn("using iOS 26.4", out.getvalue())
        # a config with runtime = ... never reaches latest_ios_runtime (ios_run_inner asks only when it is missing)
        self.assertIn('if "runtime" not in cfg: cfg["runtime"] = latest_ios_runtime()', (ROOT / "shotfleet.py").read_text())

    def doctor(self, names):
        d = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, d, True)
        out = io.StringIO()
        ok = lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "Ready\n" if "--warmup" in cmd else '{"runtimes": []}', "")
        with mock.patch.object(sf, "SDK", d / "sdk"), mock.patch.object(sf, "BREW", d / "brew"), mock.patch.object(sf.Path, "home", return_value=d / "home"), \
                mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()), \
                mock.patch.object(sf.shutil, "which", lambda c, **k: f"/usr/bin/{c}" if c in ("xcrun", "swiftc") else None), \
                mock.patch.object(sf, "find_java", return_value=(True, None)), mock.patch.object(sf, "java_env", return_value={}), \
                mock.patch.object(sf, "sh", ok), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", lambda: None), \
                mock.patch.object(sf, "ios_runtimes", lambda: names), mock.patch.object(sf, "maestro_cmd", lambda: "/m"), \
                mock.patch.object(sf, "read_maestro_version", return_value="2.11.0"), contextlib.redirect_stdout(out):
            sf.cmd_doctor()
        return out.getvalue()

    def test_doctor_warns_when_the_only_runtime_is_a_known_bad_one_and_explains_runtime(self):
        out = self.doctor(["iOS 27.0"])
        self.assertRegex(out, r"WARNING iOS Simulator runtime iOS 27\.0: .*freeze at boot")
        self.assertIn("runtime =", out); self.assertIn("xcrun simctl list runtimes", out)

    def test_doctor_stays_quiet_when_a_good_runtime_is_there(self):
        self.assertNotIn("WARNING iOS Simulator runtime", self.doctor(["iOS 26.4", "iOS 27.0"]))
        self.assertNotIn("WARNING iOS Simulator runtime", self.doctor(["iOS 26.4"]))


class BoundedCalls(unittest.TestCase):
    def test_every_simctl_and_adb_call_in_the_program_has_a_timeout(self):
        calls = [(n, l.strip()) for n, l in enumerate((ROOT / "shotfleet.py").read_text().splitlines(), 1)
                 if re.search(r'\bsh\(\[(?:"xcrun"|adb_cmd\(\)|str\(SDK / "platform-tools/adb"\))', l) and "timeout" not in l]
        self.assertEqual(calls, [])

    def test_a_simctl_call_that_never_answers_ends_with_a_plain_message_not_a_hang(self):
        def hang(cmd, **kw): raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        with mock.patch.object(sf, "sh", hang), self.assertRaisesRegex(RuntimeError, r"simctl list did not answer within 120 s.*too busy.*fewer parallel devices"):
            sf.simctl_sh("list", "devices", "-j")

    def test_listing_creating_and_deleting_simulators_all_go_through_the_bounded_call(self):
        def hang(cmd, **kw): raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        with mock.patch.object(sf, "sh", hang), self.assertRaisesRegex(RuntimeError, "too busy"):
            sf.make_pool(1, "dt", "rt")
        with mock.patch.object(sf, "sh", hang), self.assertRaisesRegex(sf.Fail, "too busy"):
            sf.latest_ios_runtime()
        with mock.patch.object(sf, "sh", hang), self.assertRaisesRegex(sf.Fail, "too busy"):
            sf.device_type_id("iPad Pro 13-inch (M5)")
        with mock.patch.object(sf, "sh", hang):
            self.assertIsNone(sf.ios_runtimes())  # doctor: "can't say", not a hang


R = sf.Reading


class OverloadAdvisor(unittest.TestCase):
    def setUp(self):
        sf.BUSY_STATE["warned"] = False; self.addCleanup(sf.BUSY_STATE.update, warned=False)

    def test_the_state_that_lost_the_ipad_pool_is_called_very_busy(self):  # 2026-10-07: load 500-800 on 10 cores, swap nearly full
        r = R(avail_gb=3, swap_used_gb=17.5, swap_total_gb=18, load1=620, cores=10, pressure="2")
        m = sf.busy_message(r, using=4)
        self.assertIn("very busy", m); self.assertIn("simulators may stop answering", m)
        self.assertIn("Close other builds or use fewer parallel devices", m); self.assertIn("--parallel 2", m)
        self.assertIn("swap is 97% full", m); self.assertIn("load 620 on 10 cores", m)

    def test_each_danger_sign_alone_is_enough_and_a_quiet_mac_gets_nothing(self):
        self.assertTrue(sf.busy_reasons(R(swap_used_gb=16.5, swap_total_gb=18)))                 # 92 %
        self.assertTrue(sf.busy_reasons(R(pressure="4")))
        self.assertTrue(sf.busy_reasons(R(load1=120, cores=10)))
        self.assertEqual(sf.busy_reasons(R(swap_used_gb=6.0, swap_total_gb=7.0, load1=40, cores=10, pressure="2")), [])  # 86 % swap, load 4 per core, elevated pressure: busy, not dangerous
        self.assertEqual(sf.busy_reasons(R(swap_used_gb=5, swap_total_gb=7, load1=3, cores=10, pressure="1")), [])
        self.assertEqual(sf.busy_message(R()), "")  # nothing readable: say nothing, never refuse

    def test_one_device_gets_no_parallel_advice(self):
        self.assertNotIn("--parallel", sf.busy_message(R(pressure="4"), using=1))

    def test_it_warns_once_per_run_and_capacity_off_silences_it(self):
        r = R(pressure="4")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertTrue(sf.busy_warn({}, "ios", 4, r)); self.assertFalse(sf.busy_warn({}, "ios", 4, r))
        self.assertEqual(out.getvalue().count("very busy"), 1)
        sf.BUSY_STATE["warned"] = False
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertFalse(sf.busy_warn({"capacity": "off"}, "ios", 4, r))
        self.assertEqual(out.getvalue(), "")

    def test_at_the_start_of_a_run_the_busy_warning_replaces_the_memory_one_and_nothing_is_refused(self):
        r = R(avail_gb=3, swap_used_gb=17.5, swap_total_gb=18, load1=620, cores=10, pressure="2")
        with mock.patch.object(sf, "read_capacity", return_value=r), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertIsNone(sf.capacity_warn({}, 4, "ios", 1))
        self.assertEqual(out.getvalue().count("warning:"), 1); self.assertIn("very busy", out.getvalue())
        # a Mac that is only short of memory still gets the old message
        sf.BUSY_STATE["warned"] = False
        with mock.patch.object(sf, "read_capacity", return_value=R(avail_gb=4, cores=10, pressure="1")), contextlib.redirect_stdout(io.StringIO()) as out:
            sf.capacity_warn({}, 4, "ios", 4)
        self.assertIn("short of memory", out.getvalue()); self.assertNotIn("very busy", out.getvalue())

    def test_swap_size_is_read_from_the_same_sysctl_line(self):
        line = "total = 7168.00M  used = 6783.19M  free = 384.81M  (encrypted)"
        self.assertAlmostEqual(sf.parse_swap_used_gb(line, "total"), 7.0)
        self.assertAlmostEqual(sf.parse_swap_used_gb(line), 6.62, places=2)


class InfraErrors(unittest.TestCase):
    def test_device_failures_are_told_apart_from_flow_failures(self):
        for e in ("Unknown error", "Unable to clear state", "no result (see maestro log)", "flow never ran (see maestro log)",
                  "no progress for 300 s, stopped (a hung simulator or test; log: x)", "simctl uninstall did not answer within 60 s: simulator U is not responding",
                  "adb: device offline", "emulators did not boot in time (300 s)"):
            self.assertTrue(sf.is_infra_error(e), e)
        for e in (None, "", "Element not found: Text matching regex: Weiter", "flow passed but took 2 of 3 screenshots",
                  "screenshot 02.png is blank (all one colour)", "xcodebuild failed (exit 65; log: x)", "Assertion is false: 'Weiter' is visible"):
            self.assertFalse(sf.is_infra_error(e), e)

    def test_only_failures_that_look_like_the_device_are_chosen_for_the_retry(self):
        final = {"de": {"ok": False, "error": "Unknown error"}, "fr": {"ok": False, "error": "Element not found"}, "ja": {"ok": True, "error": None}}
        self.assertEqual(sf.retry_choice(final), (["de"], ["fr"]))

    def test_keep_earlier_restores_passed_languages_in_order_and_adds_the_tries(self):
        prev = {"locales": {"de": {"ok": False, "attempts": 2}, "fr": {"ok": True, "attempts": 1, "screenshots": 3}, "ja": {"ok": False, "retried": True}}}
        report = {"locales": {"ja": {"ok": True, "attempts": 1}, "de": {"ok": True, "attempts": 1}}}
        self.assertEqual(sf.keep_earlier(report, prev), 1)
        self.assertEqual(list(report["locales"]), ["de", "fr", "ja"])
        self.assertEqual([report["locales"][k]["attempts"] for k in ("de", "fr", "ja")], [3, 1, 3])  # 2+1, kept, 2 (retried flag) + 1
        self.assertEqual(sf.keep_earlier({"locales": {}}, None), 0)


@needs_mac
class IosRetries(unittest.TestCase):
    """The iOS run on fakes: a Maestro that fails, per language and per call, the way the test says."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, self.d, True)
        app = self.d / "My.app"
        for lp, word in (("en", "Next"), ("de", "Weiter"), ("fr", "Suivant")):
            (app / f"{lp}.lproj").mkdir(parents=True)
            (app / f"{lp}.lproj" / "Localizable.strings").write_text(f'"next" = "{word}";\n')
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "x.y", "CFBundleLocalizations": ["en", "de", "fr"]}))
        (self.d / "flow.yaml").write_text('- launchApp\n- takeScreenshot: 01\n')
        (self.d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\nlocales = ["de", "fr"]\n')
        self.maestro_calls, self.outcomes = [], {}  # outcomes[lp] = list of "ok" or a failure message, one per Maestro call that includes lp
        p = mock.patch.dict(os.environ, {"SHOTFLEET_HOME": str(self.d / "home")}); p.start(); self.addCleanup(p.stop)
        sf.BUSY_STATE["warned"] = False

    def fake_maestro(self, cmd, env=None, timeout=None, cwd=None, **kw):
        flows = Path(cmd[cmd.index("test") + 1])
        lps = sorted(f.stem for f in flows.glob("*.yaml")); self.maestro_calls.append(lps)
        cases = []
        for lp in lps:
            plan = self.outcomes.get(lp, ["ok"]); res = plan.pop(0) if len(plan) > 1 else plan[0]
            if res == "ok":
                (Path(cwd) / lp).mkdir(parents=True, exist_ok=True); (Path(cwd) / lp / "01.png").write_bytes(b"x")
            cases.append(f'<testcase name="{lp}" time="2">{"" if res == "ok" else f"<failure>{res}</failure>"}</testcase>')
        Path(cmd[cmd.index("--output") + 1]).write_text(f"<testsuites><testsuite>{''.join(cases)}</testsuite></testsuites>")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def run_it(self, **kw):
        class S:
            udid = "U1"
            def run(self, *a, check=True): return ""
        real = sf.sh
        def sh(cmd, **k): return subprocess.CompletedProcess(cmd, 0, "1", "") if cmd[0] == "sysctl" else real(cmd, **k)
        with mock.patch.object(sf, "make_pool", return_value=[S()]), mock.patch.object(sf, "run_guarded", self.fake_maestro), \
             mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
             mock.patch.object(sf, "latest_ios_runtime", return_value="rt"), mock.patch.object(sf, "kill_stale_drivers"), \
             mock.patch.object(sf, "cmd_check", return_value=0), mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "sh", sh), \
             mock.patch.object(sf, "read_capacity", return_value=R()), contextlib.redirect_stdout(io.StringIO()) as out:
            code = sf.cmd_run(str(self.d / "shotfleet.toml"), **kw)
        return code, out.getvalue()

    def run_json(self): return json.loads((self.d / "out/run.json").read_text())["locales"]

    def test_a_flow_failure_is_not_retried_and_run_json_says_one_try(self):
        self.outcomes = {"de": ["Element not found: Text matching regex: Weiter"]}
        code, out = self.run_it()
        self.assertEqual(code, 1, out); self.assertEqual(len(self.maestro_calls), 1)
        self.assertIn("not retrying de", out); self.assertNotIn("retrying 1", out)
        self.assertEqual((self.run_json()["de"]["ok"], self.run_json()["de"]["attempts"], self.run_json()["fr"]["attempts"]), (False, 1, 1))

    def test_a_device_failure_is_retried_once_and_the_try_is_counted(self):
        self.outcomes = {"de": ["Unknown error", "ok"]}
        code, out = self.run_it()
        self.assertEqual(code, 0, out); self.assertEqual(self.maestro_calls, [["de", "fr"], ["de"]])
        self.assertIn("retrying 1: de", out); self.assertIn("(retried)", out)
        self.assertEqual((self.run_json()["de"]["attempts"], self.run_json()["fr"]["attempts"]), (2, 1))

    def test_a_device_failure_that_stays_is_tried_twice_only(self):
        self.outcomes = {"de": ["Unknown error"]}
        code, out = self.run_it()
        self.assertEqual(code, 1); self.assertEqual(len(self.maestro_calls), 2); self.assertEqual(self.run_json()["de"]["attempts"], 2)

    def test_retry_failed_reruns_only_the_failed_languages_and_keeps_the_good_ones(self):
        self.outcomes = {"de": ["Element not found"]}
        self.assertEqual(self.run_it()[0], 1)
        good_shot = self.d / "out/raw/fr/01.png"; self.assertTrue(good_shot.is_file())
        self.outcomes = {"de": ["ok"]}; self.maestro_calls.clear()
        code, out = self.run_it(retry_failed=True)
        self.assertEqual(code, 0, out); self.assertEqual(self.maestro_calls, [["de"]])
        self.assertIn("retrying the languages that failed in the last run: de", out); self.assertIn("kept the other 1 language", out)
        runs = self.run_json()
        self.assertEqual(list(runs), ["de", "fr"]); self.assertTrue(runs["de"]["ok"] and runs["fr"]["ok"])
        self.assertEqual((runs["de"]["attempts"], runs["fr"]["attempts"]), (2, 1))  # de: the failed run plus this one
        self.assertTrue(good_shot.is_file())
        self.maestro_calls.clear()
        code, out = self.run_it(retry_failed=True)  # everything passed now
        self.assertEqual((code, self.maestro_calls), (0, [])); self.assertIn("nothing to retry", out)

    def test_attempts_add_up_across_a_failed_retry_and_a_retry_failed_run(self):
        self.outcomes = {"de": ["Unknown error"]}  # tried twice in the first run
        self.assertEqual(self.run_it()[0], 1)
        self.outcomes = {"de": ["ok"]}
        self.assertEqual(self.run_it(retry_failed=True)[0], 0)
        self.assertEqual(self.run_json()["de"]["attempts"], 3)

    def test_retry_failed_without_an_earlier_run_says_so(self):
        with self.assertRaisesRegex(sf.Fail, "--retry-failed needs the last run's .*run.json"):
            self.run_it(retry_failed=True)

    def test_retry_failed_refuses_a_run_json_from_another_config(self):
        self.assertEqual(self.run_it()[0], 0)
        f = self.d / "out/run.json"; j = json.loads(f.read_text()); j["config"] = "/elsewhere/other.toml"; j["locales"]["de"]["ok"] = False
        f.write_text(json.dumps(j))
        with self.assertRaisesRegex(sf.Fail, "another config"):
            self.run_it(retry_failed=True)

    def test_the_flag_and_locales_do_not_mix(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sf.main(["run", "x.toml", "--retry-failed", "--locales", "de"])

    def test_the_overload_warning_is_checked_again_before_the_retry(self):
        self.outcomes = {"de": ["Unknown error", "ok"]}
        busy = R(pressure="4")
        seen = []
        def reading(*a, **k): seen.append(1); return R() if len(seen) == 1 else busy  # quiet at the start, bad by the retry
        with mock.patch.object(sf, "fit_parallel", lambda n: n):
            with mock.patch.object(sf, "read_capacity", side_effect=reading):
                class S:
                    udid = "U1"
                    def run(self, *a, check=True): return ""
                with mock.patch.object(sf, "make_pool", return_value=[S()]), mock.patch.object(sf, "run_guarded", self.fake_maestro), \
                     mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), mock.patch.object(sf, "latest_ios_runtime", return_value="rt"), \
                     mock.patch.object(sf, "kill_stale_drivers"), mock.patch.object(sf, "cmd_check", return_value=0), mock.patch.object(sf, "java_env", return_value={}), \
                     contextlib.redirect_stdout(io.StringIO()) as out:
                    sf.cmd_run(str(self.d / "shotfleet.toml"))
        self.assertEqual(out.getvalue().count("very busy"), 1)
        self.assertLess(out.getvalue().index("very busy"), out.getvalue().index("retrying 1"))


if __name__ == "__main__":
    unittest.main()
