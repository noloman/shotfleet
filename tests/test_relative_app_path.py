"""`init <app>`: an app inside the project folder is written relative to the config (so the config can be committed),
one outside it keeps its place on this Mac and init says so; `run` and `check` resolve a relative path from the
config's folder, and a config with an absolute path still works. No device: synthetic folders only.

Run: python3 -m unittest tests.test_relative_app_path
"""
import contextlib, io, os, sys, tempfile, tomllib, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
from tests.test_projects import sim_app

STRINGS = {"en": {"a": "A"}, "de": {"a": "B"}}


class AppPathInConfig(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.cwd = os.getcwd(); self.addCleanup(os.chdir, self.cwd)

    def init(self, project, app, dest="."):
        os.chdir(project)
        with mock.patch.object(sf, "load_strings", return_value=STRINGS), contextlib.redirect_stdout(io.StringIO()) as out:
            sf.cmd_init([str(app)], dest)
        return out.getvalue(), tomllib.loads((Path(project) / dest / "shotfleet.toml").read_text())

    def test_an_app_inside_the_project_is_written_relative_and_resolved_from_the_config_folder(self):
        proj = self.root / "proj"; proj.mkdir()
        app = sim_app(proj, "build/App.app")
        out, doc = self.init(proj, app)
        self.assertEqual(doc["ios"]["app"], "build/App.app")
        self.assertNotIn("note:", out)
        os.chdir(self.root)  # run/check may be started from anywhere
        _, cfg, _ = sf.load_config(proj / "shotfleet.toml", "ios")
        self.assertEqual(Path(cfg["app"]), app)

    def test_a_config_in_a_subfolder_is_relative_to_that_folder(self):
        proj = self.root / "proj"; proj.mkdir()
        app = sim_app(proj, "build/App.app")
        _, doc = self.init(proj, app, dest="ci")
        self.assertEqual(doc["ios"]["app"], "../build/App.app")
        _, cfg, _ = sf.load_config(proj / "ci/shotfleet.toml", "ios")
        self.assertEqual(Path(cfg["app"]), app)

    def test_an_app_far_outside_the_project_stays_absolute_and_init_says_it_cannot_be_committed(self):
        proj = self.root / "a/b/c/proj"; proj.mkdir(parents=True)
        app = sim_app(self.root, "elsewhere/App.app")
        out, doc = self.init(proj, app)
        self.assertEqual(doc["ios"]["app"], str(app))
        self.assertIn(f"note: App.app is outside this project folder, so shotfleet.toml names it as {app}", out)
        self.assertIn("before you commit the config", out)

    def test_an_old_config_with_an_absolute_path_still_works(self):
        proj = self.root / "proj"; proj.mkdir()
        app = sim_app(self.root, "elsewhere/App.app")
        (proj / "flow.yaml").write_text(sf.FLOW_TEMPLATE)
        (proj / "shotfleet.toml").write_text(f'[ios]\napp = "{app}"\n')
        os.chdir(self.root)
        _, cfg, _ = sf.load_config(proj / "shotfleet.toml", "ios")
        self.assertEqual(Path(cfg["app"]), app)


if __name__ == "__main__":
    unittest.main()
