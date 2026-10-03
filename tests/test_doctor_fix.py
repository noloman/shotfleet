"""`shotfleet doctor --fix`: fetch Maestro, a Java runtime and the Android command-line tools, checked against checksums, into one
folder. A local HTTP server stands in for GitHub, Adoptium and Google, so nothing here touches the network.

Run: python3 -m unittest tests.test_doctor_fix
"""
import contextlib, hashlib, http.server, io, json, os, subprocess, sys, tarfile, tempfile, threading, unittest, zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


def zip_bytes(files, modes=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            info = zipfile.ZipInfo(name); info.external_attr = ((modes or {}).get(name, 0o644) | 0o100000) << 16
            z.writestr(info, data)
    return buf.getvalue()

def tar_bytes(files, executable=()):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data in files.items():
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o755 if name in executable else 0o644
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()

MAESTRO_ZIP = zip_bytes({"maestro/bin/maestro": b"#!/bin/sh\necho 2.0.10\n", "maestro/lib/maestro-cli.jar": b"jar"},
                        {"maestro/bin/maestro": 0o755})
JRE_TAR = tar_bytes({"jdk-21.0.1+1-jre/bin/java": b"#!/bin/sh\necho 'openjdk version \"21.0.1\"' >&2\n", "jdk-21.0.1+1-jre/release": b"x"},
                    executable=("jdk-21.0.1+1-jre/bin/java",))
CMDLINE_ZIP = zip_bytes({"cmdline-tools/bin/sdkmanager": b"#!/bin/sh\nexit 0\n", "cmdline-tools/source.properties": b"x"},
                        {"cmdline-tools/bin/sdkmanager": 0o755})
REAL_WHICH = __import__("shutil").which
sha256 = lambda b: hashlib.sha256(b).hexdigest()
sha1 = lambda b: hashlib.sha1(b).hexdigest()


class Server:
    """Serves the fake release files; `files` maps a path to bytes and can be changed per test."""
    def __init__(self, files):
        self.files, outer = files, self
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                path = self.path.split("?")[0]
                data = outer.files.get(path)
                if data is None: self.send_response(404); self.end_headers(); return
                self.send_response(200); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            def log_message(self, *a): pass
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=lambda: self.httpd.serve_forever(poll_interval=0.01), daemon=True).start()
    def close(self): self.httpd.shutdown(); self.httpd.server_close()


class FixTestCase(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp()); self.sdk = Path(tempfile.mkdtemp())
        self.server = Server({})
        self.addCleanup(self.server.close)
        self.set_files()
        for p in (mock.patch.dict(os.environ, {"SHOTFLEET_HOME": str(self.home)}),
                  mock.patch.object(sf, "MAESTRO_PIN", {"version": "2.0.10", "size": len(MAESTRO_ZIP), "url": self.server.url + "/maestro.zip",
                                                        "sha256": sha256(MAESTRO_ZIP)}),
                  mock.patch.object(sf, "ADOPTIUM_ASSETS", self.server.url + "/assets"),
                  mock.patch.object(sf, "ANDROID_REPOSITORY", self.server.url + "/repo/"),
                  mock.patch.object(sf, "SDK", self.sdk), mock.patch.dict(os.environ, {"ANDROID_HOME": "", "ANDROID_SDK_ROOT": ""}),
                  mock.patch.object(sf, "certifi_path", lambda: None),
                  mock.patch.object(sf.shutil, "which", self.which_without_brew),  # a Mac with Homebrew takes the brew branch: tested below
                  mock.patch.object(sf, "latest_release", lambda: None)):  # doctor's version lookup is a network call too
            p.start(); self.addCleanup(p.stop)
        sf.java_env.cache_clear(); self.addCleanup(sf.java_env.cache_clear)

    @staticmethod
    def which_without_brew(cmd, *a, **k):
        return None if cmd == "brew" else REAL_WHICH(cmd, *a, **k)

    def set_files(self, **override):
        entry = lambda host, arch: (f'<archive><complete><size>{len(CMDLINE_ZIP)}</size><checksum type="sha1">{sha1(CMDLINE_ZIP)}</checksum>'
                                    f'<url>cmdline.zip</url></complete><host-os>{host}</host-os>' + (f'<host-arch>{arch}</host-arch>' if arch else "") + '</archive>')
        # every platform, so a test that pretends to be Linux (or a Mac) on the other kind of machine still finds its archive
        manifest = ('<remotePackage path="cmdline-tools;latest"><archives>' + entry("linux", None) + entry("macosx", "x64") + entry("macosx", "aarch64")
                    + '</archives></remotePackage>')
        assets = [{"binary": {"image_type": "jre", "package": {"name": "jre.tar.gz", "link": self.server.url + "/jre.tar.gz",
                                                                   "checksum": sha256(JRE_TAR), "size": len(JRE_TAR)}}}]
        self.server.files.update({"/maestro.zip": MAESTRO_ZIP, "/jre.tar.gz": JRE_TAR, "/assets": json.dumps(assets).encode(),
                                  "/repo/repository2-3.xml": manifest.encode(), "/repo/cmdline.zip": CMDLINE_ZIP})
        self.server.files.update(override)

    def quiet(self):
        return contextlib.redirect_stderr(io.StringIO())


class Installers(FixTestCase):
    def test_maestro_is_installed_executable_and_found(self):
        with self.quiet(): path = sf.install_maestro()
        self.assertEqual(path, self.home / "maestro/bin/maestro")
        self.assertTrue(os.access(path, os.X_OK))
        self.assertEqual(sf.maestro_cmd(), str(path))
        self.assertEqual(subprocess.run([str(path)], capture_output=True, text=True).stdout.strip(), "2.0.10")
        self.assertFalse(list(self.home.rglob("*.part")) + list((self.home / "downloads").glob("*.zip")), "no download left behind")

    def test_a_wrong_checksum_installs_nothing(self):
        self.server.files["/maestro.zip"] = MAESTRO_ZIP + b"tampered"
        with self.quiet(), self.assertRaisesRegex(sf.Fail, "does not match its checksum"): sf.install_maestro()
        self.assertFalse((self.home / "maestro").exists())
        self.assertFalse(list(self.home.rglob("*.part")))

    def test_a_zip_with_a_path_outside_its_folder_is_refused(self):
        evil = zip_bytes({"maestro/bin/maestro": b"x", "../../escaped.txt": b"x"})
        self.server.files["/maestro.zip"] = evil
        with mock.patch.object(sf, "MAESTRO_PIN", {**sf.MAESTRO_PIN, "sha256": sha256(evil)}), self.quiet(), self.assertRaisesRegex(sf.Fail, "outside its folder"):
            sf.install_maestro()
        self.assertFalse((self.home.parent / "escaped.txt").exists())

    def test_a_download_that_404s_is_a_clear_failure(self):
        self.server.files.pop("/maestro.zip")
        with self.quiet(), self.assertRaisesRegex(sf.Fail, "can't download"): sf.install_maestro()

    def test_installing_twice_replaces_the_old_copy(self):
        with self.quiet(): sf.install_maestro()
        (self.home / "maestro/stale").write_text("x")
        with self.quiet(): sf.install_maestro()
        self.assertFalse((self.home / "maestro/stale").exists())

    def test_jre_is_installed_and_find_java_uses_it(self):
        with mock.patch.object(sys, "platform", "linux"), mock.patch.object(sf.host_platform, "machine", lambda: "x86_64"), self.quiet():
            jre = sf.install_jre()
        self.assertEqual(jre, self.home / "jre")
        self.assertTrue(os.access(jre / "bin/java", os.X_OK))
        with mock.patch.dict(os.environ, {"JAVA_HOME": "", "PATH": "/nonexistent"}):
            self.assertEqual(sf.find_java(), (True, str(self.home / "jre")))

    def test_jre_checksum_comes_from_the_api_and_is_enforced(self):
        assets = json.loads(self.server.files["/assets"]); assets[0]["binary"]["package"]["checksum"] = "0" * 64
        self.server.files["/assets"] = json.dumps(assets).encode()
        with mock.patch.object(sys, "platform", "linux"), mock.patch.object(sf.host_platform, "machine", lambda: "x86_64"), \
                self.quiet(), self.assertRaisesRegex(sf.Fail, "does not match its checksum"):
            sf.install_jre()
        self.assertFalse((self.home / "jre").exists())

    def test_no_java_download_for_an_unknown_system(self):
        with self.assertRaisesRegex(sf.Fail, "no Java download for"): sf.adoptium_target("win32", "AMD64")

    def test_cmdline_tools_go_into_the_sdk_and_the_sha1_is_enforced(self):
        with self.quiet(): tool = sf.install_cmdline_tools()
        self.assertEqual(tool, self.sdk / "cmdline-tools/latest/bin/sdkmanager")
        self.assertTrue(os.access(tool, os.X_OK))
        self.server.files["/repo/cmdline.zip"] = CMDLINE_ZIP + b"x"
        with self.quiet(), self.assertRaisesRegex(sf.Fail, "does not match its checksum"): sf.install_cmdline_tools()

    def test_the_manifest_is_read_per_system(self):
        xml = ('<remotePackage path="cmdline-tools;latest"><archives>'
               '<archive><complete><size>1</size><checksum type="sha1">aa</checksum><url>linux.zip</url></complete><host-os>linux</host-os></archive>'
               '<archive><complete><size>2</size><checksum type="sha1">bb</checksum><url>mx.zip</url></complete><host-os>macosx</host-os><host-arch>x64</host-arch></archive>'
               '<archive><complete><size>3</size><checksum type="sha1">cc</checksum><url>ma.zip</url></complete><host-os>macosx</host-os><host-arch>aarch64</host-arch></archive>'
               '</archives></remotePackage>')
        pick = lambda sysname, machine: sf.android_cmdline_archive(xml, sysname, machine)
        self.assertEqual(pick("linux", "x86_64")[1:], ("aa", 1))
        self.assertEqual(pick("darwin", "arm64")[1:], ("cc", 3))
        self.assertEqual(pick("darwin", "x86_64")[1:], ("bb", 2))
        with self.assertRaises(sf.Fail): pick("win32", "AMD64")


class Where(FixTestCase):
    def test_the_install_folder_is_the_one_the_user_named_else_the_sdk_found(self):
        self.assertEqual(sf.fix_sdk_root(), self.sdk)
        with mock.patch.dict(os.environ, {"ANDROID_HOME": "/somewhere/Sdk"}): self.assertEqual(sf.fix_sdk_root(), Path("/somewhere/Sdk"))
        with mock.patch.dict(os.environ, {"ANDROID_HOME": "", "ANDROID_SDK_ROOT": "/other"}): self.assertEqual(sf.fix_sdk_root(), Path("/other"))

    def test_a_named_folder_gets_the_tools_even_when_another_sdk_exists(self):
        named = Path(tempfile.mkdtemp())
        with mock.patch.dict(os.environ, {"ANDROID_HOME": str(named)}):
            plan = sf.fix_plan(True, True, ["platform-tools"], False)
            self.assertIn(str(named), plan[0][0])
            with self.quiet(): plan[0][1]()
        self.assertTrue((named / "cmdline-tools/latest/bin/sdkmanager").is_file())
        self.assertFalse((self.sdk / "cmdline-tools").exists())

    def test_the_ca_bundle_the_environment_names_wins_over_the_bundled_one(self):
        bundle = self.home / "proxy-ca.pem"; bundle.write_text("not a certificate")
        with mock.patch.dict(os.environ, {"SSL_CERT_FILE": str(bundle)}), mock.patch.object(sf.ssl, "create_default_context") as ctx:
            sf.tls_context()
        ctx.assert_called_once_with(cafile=str(bundle))
        with mock.patch.dict(os.environ, {"SSL_CERT_FILE": "", "REQUESTS_CA_BUNDLE": "", "CURL_CA_BUNDLE": str(bundle)}), mock.patch.object(sf.ssl, "create_default_context") as ctx:
            sf.tls_context()
        ctx.assert_called_once_with(cafile=str(bundle))


class Plan(FixTestCase):
    def test_a_mac_with_homebrew_installs_the_android_tools_with_brew_a_mac_without_downloads_them(self):
        with mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf.shutil, "which", lambda c, *a, **k: "/opt/homebrew/bin/brew" if c == "brew" else REAL_WHICH(c)):
            titles = [t for t, _ in sf.fix_plan(True, True, ["emulator"], False)]
        self.assertEqual(titles[0], "brew install --cask android-commandlinetools")
        with mock.patch.object(sf, "is_mac", lambda: True):  # which_without_brew is still in force: no brew
            titles = [t for t, _ in sf.fix_plan(True, True, ["emulator"], False)]
        self.assertTrue(titles[0].startswith("download Google's Android command-line tools"), titles)

    def test_nothing_missing_means_no_steps(self):
        self.assertEqual(sf.fix_plan(True, True, [], True), [])

    def test_missing_things_become_steps_in_order_and_never_mention_sudo(self):
        plan = sf.fix_plan(False, False, ["platform-tools", "emulator"], False)
        titles = [t for t, _ in plan]
        self.assertTrue(titles[0].startswith("download Maestro 2.0.10"), titles)
        self.assertTrue(titles[1].startswith("download a Java 21 runtime"), titles)
        self.assertIn("accept the Android SDK licences", " ".join(titles))
        self.assertIn("sdkmanager platform-tools emulator", titles[-1])
        self.assertFalse(any("sudo" in t or ".zshrc" in t or ".bashrc" in t for t in titles), titles)

    def test_android_is_left_alone_when_the_sdk_is_complete(self):
        self.assertEqual([t for t, _ in sf.fix_plan(False, True, [], True)][0][:8], "download")
        self.assertEqual(len(sf.fix_plan(False, True, [], True)), 1)


class Consent(FixTestCase):
    def plan(self, calls, fail_at=None):
        def step(i):
            def run():
                calls.append(i)
                if i == fail_at: raise sf.Fail(f"step {i} broke")
            return run
        return [(f"do thing {i}", step(i)) for i in (1, 2, 3)]

    def run_plan(self, plan, yes=False, tty=True, answer="y"):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch("builtins.input", lambda prompt="": answer):
            code = sf.run_fix_plan(plan, yes=yes, stdin_is_tty=tty)
        return code, out.getvalue(), err.getvalue()

    def test_answering_yes_runs_every_step(self):
        calls = []; code, out, _ = self.run_plan(self.plan(calls))
        self.assertEqual((code, calls), (0, [1, 2, 3]))
        self.assertIn("1. do thing 1", out); self.assertIn("never sudo", out)

    def test_anything_but_yes_runs_nothing(self):
        for answer in ("", "n", "no", "maybe"):
            calls = []; code, out, _ = self.run_plan(self.plan(calls), answer=answer)
            self.assertEqual((code, calls), (2, []), answer)

    def test_without_a_terminal_it_prints_the_plan_and_runs_nothing(self):
        calls = []; code, out, _ = self.run_plan(self.plan(calls), tty=False)
        self.assertEqual((code, calls), (2, []))
        self.assertIn("add --yes", out)

    def test_yes_skips_the_question(self):
        calls = []
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch("builtins.input", side_effect=AssertionError("asked")):
            code = sf.run_fix_plan(self.plan(calls), yes=True, stdin_is_tty=False)
        self.assertEqual((code, calls), (0, [1, 2, 3]))

    def test_the_first_failure_stops_the_rest_and_names_what_is_left(self):
        calls = []; code, _, err = self.run_plan(self.plan(calls, fail_at=2), yes=True)
        self.assertEqual((code, calls), (1, [1, 2]))
        self.assertIn("stopped at step 2: step 2 broke", err)
        self.assertIn("not done: 3. do thing 3", err)

    def test_an_empty_plan_says_so(self):
        code, out, _ = self.run_plan([])
        self.assertEqual(code, 0); self.assertIn("nothing to fix", out)


class DoctorCommand(FixTestCase):
    def test_the_flags_exist(self):
        r = subprocess.run([sys.executable, str(Path(sf.__file__)), "doctor", "--help"], capture_output=True, text=True)
        self.assertIn("--fix", r.stdout); self.assertIn("--yes", r.stdout)

    def test_doctor_fix_without_a_terminal_prints_the_plan_and_changes_nothing(self):
        out = io.StringIO()
        with mock.patch.object(sf, "maestro_cmd", lambda: None), mock.patch.object(sf, "find_java", lambda: (False, None)), \
                mock.patch.object(sys.stdin, "isatty", lambda: False), contextlib.redirect_stdout(out):
            sf.cmd_doctor(fix=True, yes=False)
        text = out.getvalue()
        self.assertIn("doctor --fix would do", text); self.assertIn("download Maestro 2.0.10", text); self.assertIn("nothing was run", text)
        self.assertFalse((self.home / "maestro").exists())

    def test_doctor_fix_yes_installs_maestro_and_the_runtime(self):
        out = io.StringIO()
        with mock.patch.object(sf, "maestro_cmd", lambda: None), mock.patch.object(sf, "find_java", lambda: (False, None)), \
                mock.patch.object(sys, "platform", "linux"), mock.patch.object(sf.host_platform, "machine", lambda: "x86_64"), \
                mock.patch.object(sf, "run_sdkmanager", lambda *a, **k: None), \
                contextlib.redirect_stdout(out), self.quiet():
            sf.cmd_doctor(fix=True, yes=True)
        self.assertTrue((self.home / "maestro/bin/maestro").is_file())
        self.assertTrue((self.home / "jre/bin/java").is_file())
        self.assertTrue((self.sdk / "cmdline-tools/latest/bin/sdkmanager").is_file())


if __name__ == "__main__":
    unittest.main()


class LicenceCallsUseTheSameCaBundle(unittest.TestCase):
    """A buyer behind a proxy that re-signs HTTPS must be able to activate: the licence calls honour SSL_CERT_FILE like the downloads."""
    def test_licence_calls_ask_tls_context_at_call_time(self):
        seen = []
        class Resp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b"{}"
        def fake_urlopen(req, timeout=None, context=None): seen.append(context); return Resp()
        marker = object()
        with mock.patch.object(sf, "tls_context", lambda: marker), mock.patch.object(sf.urllib.request, "urlopen", fake_urlopen), \
                mock.patch.object(sf, "GUMROAD_PRODUCT_ID", "pid"):
            sf.gumroad_verify("k", False)
        self.assertEqual(len(seen), 1)
        self.assertTrue(all(c is marker for c in seen), seen)


class MaestroZipLayouts(FixTestCase):
    def test_a_zip_without_the_maestro_folder_installs_too(self):
        flat = zip_bytes({"bin/maestro": b"#!/bin/sh\necho 2.99.0\n", "lib/x.jar": b"j"}, {"bin/maestro": 0o755})
        self.server.files["/maestro.zip"] = flat
        with mock.patch.object(sf, "MAESTRO_PIN", {**sf.MAESTRO_PIN, "sha256": sha256(flat)}), self.quiet():
            path = sf.install_maestro()
        self.assertEqual(path, self.home / "maestro/bin/maestro")
        self.assertTrue(os.access(path, os.X_OK)); self.assertTrue((self.home / "maestro/lib/x.jar").is_file())

    def test_a_zip_with_no_maestro_binary_is_refused(self):
        odd = zip_bytes({"readme.txt": b"x"}); self.server.files["/maestro.zip"] = odd
        with mock.patch.object(sf, "MAESTRO_PIN", {**sf.MAESTRO_PIN, "sha256": sha256(odd)}), self.quiet(), self.assertRaisesRegex(sf.Fail, "no bin/maestro"):
            sf.install_maestro()
        self.assertFalse((self.home / "maestro").exists())


class SdkPathsAreClean(FixTestCase):
    """Google's Android CLI crashes on a destination like /work/app/../Android/Sdk (seen on a GitHub runner, 2026-10-03), so every SDK path shotfleet hands out is normalised."""
    def test_dots_tilde_and_relative_paths_are_folded_away(self):
        self.assertEqual(sf.clean_path("/work/app/../Android/Sdk"), Path("/work/Android/Sdk"))
        self.assertEqual(sf.clean_path("/a/./b//c"), Path("/a/b/c"))
        self.assertEqual(sf.clean_path("~/x/../y"), Path.home() / "y")
        self.assertEqual(sf.clean_path("sdk"), Path.cwd() / "sdk")

    def test_the_folder_doctor_fix_installs_into_has_no_dots(self):
        with mock.patch.dict(os.environ, {"ANDROID_HOME": "/work/app/../Android/Sdk"}):
            self.assertEqual(sf.fix_sdk_root(), Path("/work/Android/Sdk"))
        with mock.patch.dict(os.environ, {"ANDROID_HOME": "", "ANDROID_SDK_ROOT": "/x/y/../z"}):
            self.assertEqual(sf.fix_sdk_root(), Path("/x/z"))

    def test_the_sdk_that_find_sdk_names_has_no_dots_even_when_it_is_missing(self):
        home = Path(tempfile.mkdtemp())
        with mock.patch.object(sf, "SYSTEM_SDKS", ()), mock.patch.object(Path, "home", classmethod(lambda cls: home)):  # not this machine's SDKs
            env = {"ANDROID_HOME": "/nonexistent/app/../Android/Sdk", "PATH": ""}
            self.assertEqual(sf.find_sdk(env), Path("/nonexistent/Android/Sdk"))
            real = Path(tempfile.mkdtemp()); (real / "platform-tools").mkdir()
            self.assertEqual(sf.find_sdk({"ANDROID_HOME": f"{real}/sub/../", "PATH": ""}), real)


class SdkManagerInvocation(FixTestCase):
    """Google's new sdkmanager is a shim for the Android CLI, which reports usage unless `--no-metrics`; installs use the CLI when it is there."""
    def tool(self, with_android):
        d = Path(tempfile.mkdtemp()) / "cmdline-tools/latest/bin"; d.mkdir(parents=True)
        (d / "sdkmanager").write_text("#!/bin/sh\n")
        if with_android: (d / "android").write_text("#!/bin/sh\n")
        return d / "sdkmanager"

    def test_package_installs_go_through_the_android_cli_with_metrics_off(self):
        t = self.tool(True)
        self.assertEqual(sf.sdkmanager_invocation(t, Path("/sdk"), ["platform-tools", "build-tools;36.0.0"]),
                         [str(t.with_name("android")), "--no-metrics", "--sdk=/sdk", "sdk", "install", "platform-tools", "build-tools;36.0.0"])

    def test_licences_and_older_tools_use_plain_sdkmanager(self):
        t = self.tool(True)
        self.assertEqual(sf.sdkmanager_invocation(t, Path("/sdk"), ["--licenses"]), [str(t), "--sdk_root=/sdk", "--licenses"])
        old = self.tool(False)  # no android program next to it: an older command-line tools release
        self.assertEqual(sf.sdkmanager_invocation(old, Path("/sdk"), ["emulator"]), [str(old), "--sdk_root=/sdk", "emulator"])


class EmulatorBootFailures(unittest.TestCase):
    """E1 on a GitHub runner (2026-10-03): 'emulators did not boot in time' after 600 s with no clue why, because the emulator's output went to DEVNULL."""
    def emu(self, returncode=None, log="line one\n\nHW config error: no KVM\n"):
        d = Path(tempfile.mkdtemp()); (d / "e.log").write_text(log)
        proc = mock.Mock(returncode=returncode, log_path=d / "e.log"); proc.poll.return_value = returncode
        e = sf.Emu(5702); e.proc = proc; e.booted = lambda: False
        return e

    def test_a_dead_emulator_fails_at_once_with_its_exit_code_and_output(self):
        with mock.patch.object(sf.time, "sleep", side_effect=AssertionError("must not wait for a dead emulator")):
            with self.assertRaises(RuntimeError) as cm: sf.wait_booted([self.emu(returncode=1)], timeout=600)
        msg = str(cm.exception)
        self.assertIn("emulator-5702", msg); self.assertIn("exited with code 1", msg); self.assertIn("HW config error: no KVM", msg)

    def test_a_timeout_carries_the_log_tail_and_the_likely_cause(self):
        with mock.patch.object(sf.time, "sleep", lambda s: None), mock.patch.object(sf, "boot_failure_hint", lambda output="": "HINT"):
            with self.assertRaises(RuntimeError) as cm: sf.wait_booted([self.emu()], timeout=-1)
        msg = str(cm.exception)
        self.assertIn("emulators did not boot in time (-1 s)", msg); self.assertIn("HW config error: no KVM", msg); self.assertIn("HINT", msg)
        self.assertNotIn("\n\n\n", msg)  # blank lines of the log are dropped

    def test_the_hint_names_missing_kvm_on_linux_and_memory_otherwise(self):
        with mock.patch.object(sf.sys, "platform", "linux"), mock.patch.object(sf.os, "access", lambda p, m: False):
            self.assertIn("/dev/kvm", sf.boot_failure_hint())
        with mock.patch.object(sf.sys, "platform", "darwin"):
            self.assertIn("3 GB", sf.boot_failure_hint())

    def test_a_full_disk_is_named_with_its_fix(self):
        """The real FATAL line from a GitHub runner, 2026-10-03: the emulator died at once and shotfleet used to wait 600 s for it."""
        fatal = ("INFO | Increasing RAM size to 2560MB\nFATAL        | Not enough space to create userdata partition. "
                 "Available: 7322.37 MB at /home/runner/.android/avd/../avd/shotfleet_android.avd, need 12288.00 MB.\n")
        with self.assertRaises(RuntimeError) as cm: sf.wait_booted([self.emu(returncode=1, log=fatal)], timeout=600)
        msg = str(cm.exception)
        self.assertIn("Not enough space to create userdata partition", msg); self.assertIn("12 GB free", msg); self.assertIn("disk.dataPartition.size", msg)
        self.assertNotIn("KVM", msg)  # not blamed on virtualization

    def test_start_emu_keeps_the_emulators_output(self):
        d = Path(tempfile.mkdtemp())
        with mock.patch.object(sf, "EMU_LOG_DIR", d), mock.patch.object(sf.subprocess, "Popen") as popen:
            p = sf.start_emu("avd", 5702)
        self.assertEqual(p.log_path, d / "emulator-5702.log"); self.assertTrue(p.log_path.exists())
        self.assertIs(popen.call_args.kwargs["stderr"], sf.subprocess.STDOUT); self.assertNotEqual(popen.call_args.kwargs["stdout"], sf.subprocess.DEVNULL)

    def test_the_tail_is_empty_without_a_log(self):
        self.assertEqual(sf.emulator_log_tail(object()), ""); self.assertEqual(sf.emulator_log_tail(mock.Mock(log_path="/nonexistent/x.log")), "")
