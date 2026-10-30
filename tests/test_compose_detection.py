"""#97: a Compose APK whose screens expose no resource id gets a note, at init and after a run."""
import sys, tempfile, unittest, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


def apk(d, names=(), dex=b""):
    p = Path(d) / "a.apk"
    with zipfile.ZipFile(p, "w") as z:
        for n in names: z.writestr(n, "1.0")
        if dex: z.writestr("classes.dex", dex)
    return p


class Compose(unittest.TestCase):
    def test_detected_from_the_library_version_file_or_the_dex(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(sf.compose_apk(apk(d, ["META-INF/androidx.compose.runtime_runtime.version"])))
            self.assertTrue(sf.compose_apk(apk(d, dex=b"xx Landroidx/compose/runtime/Composer; yy")))
            self.assertFalse(sf.compose_apk(apk(d, ["META-INF/other.version"], b"nothing here")))
            self.assertFalse(sf.compose_apk(Path(d) / "missing.apk"))

    def test_app_resource_ids_are_told_from_the_systems(self):
        sys_only = {"attributes": {"resource-id": "com.android.systemui:id/clock"}, "children": [{"attributes": {"resource-id": "android:id/content"}}]}
        self.assertFalse(sf.has_app_resource_id(sys_only))
        self.assertTrue(sf.has_app_resource_id({"attributes": {}, "children": [sys_only, {"attributes": {"resource-id": "view_week"}}]}))
        self.assertFalse(sf.has_app_resource_id(None))


if __name__ == "__main__":
    unittest.main()
