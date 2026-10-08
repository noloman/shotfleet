"""The claims register (tests/claims.json): every promise on the site, the docs and the launch texts, with its status and proof.

These tests keep the register honest: the words it quotes are still where it says, no known-false claim is left published,
and a claim marked proven names a test that exists.

Run: python3 -m unittest discover -s tests
"""
import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = json.loads((ROOT / "tests/claims.json").read_text())
STATUSES = {"proven", "partial", "evidence", "untested", "unverifiable", "fixed", "removed", "policy"}  # policy: the owner's decision, nothing to test
KEYS = {"id", "claim", "where", "where_text", "status", "proof", "layer", "assertion", "fix"}
LAYERS = {"unit", "site", "fixture", "device", "legal"}
TESTS = "\n".join(p.read_text() for p in sorted((ROOT / "tests").glob("test_*.py")))


def text_of(rel):
    return (ROOT / rel).read_text()


class Register(unittest.TestCase):
    def test_schema(self):
        self.assertGreaterEqual(len(CLAIMS), 100)
        ids = [c["id"] for c in CLAIMS]
        self.assertEqual(len(ids), len(set(ids)), "duplicate id")
        for c in CLAIMS:
            with self.subTest(id=c["id"]):
                self.assertRegex(c["id"], r"^C\d{3}$")
                self.assertTrue(KEYS <= set(c), KEYS - set(c))
                self.assertIn(c["status"], STATUSES)
                self.assertIn(c["layer"], LAYERS)
                self.assertTrue(c["claim"].strip() and c["where"] and c["where_text"] and c["proof"].strip())

    def test_where_files_exist_and_quoted_words_are_still_there(self):
        for c in CLAIMS:
            if c["status"] == "removed": continue
            for rel in c["where"]: self.assertTrue((ROOT / rel).is_file(), f"{c['id']}: {rel} is missing")
            for i, quote in enumerate(c["where_text"]):
                files = [c["where"][i]] if len(c["where"]) == len(c["where_text"]) else c["where"]
                with self.subTest(id=c["id"], quote=quote[:60]):
                    self.assertTrue(any(quote in text_of(f) for f in files), f"{c['id']}: {quote!r} is no longer in {files}")

    def test_removed_claims_are_really_gone(self):
        for c in CLAIMS:
            if c["status"] != "removed": continue
            for rel in c["where"]:
                if (ROOT / rel).is_file():
                    for quote in c["where_text"]: self.assertNotIn(quote, text_of(rel), f"{c['id']}: {quote!r} is back in {rel}")

    def test_no_claim_is_still_false(self):
        self.assertEqual([c["id"] for c in CLAIMS if c["status"] == "false"], [])  # fixed ones say so: status "fixed"

    def test_fixed_and_removed_say_how_and_why(self):
        for c in CLAIMS:
            if c["status"] in ("fixed", "removed") or "fixed_by" in c:
                with self.subTest(id=c["id"]):
                    self.assertIn(c.get("fixed_by"), ("code", "wording", "removed"))
                    self.assertGreater(len(c.get("fixed", "")), 20, "say what changed and why this route")
                    if c["fixed_by"] == "code": self.assertTrue(c.get("test"), "a fix in code names its test")

    def test_proven_claims_record_a_test_that_exists(self):
        proven = [c for c in CLAIMS if c["status"] == "proven"]
        self.assertTrue(proven)
        for c in CLAIMS:
            named = re.findall(r"\b([A-Z]\w+)\.(test_\w+)", c["proof"] + " " + c.get("test", ""))
            if c["status"] == "proven": self.assertTrue(c.get("test") or named, f"{c['id']} is proven but names no test")
            for cls, name in named:
                with self.subTest(id=c["id"], test=f"{cls}.{name}"):
                    self.assertRegex(TESTS, rf"class {cls}\b(?s:.*?)def {name}", f"{c['id']}: {cls}.{name} does not exist")

    def test_the_audit_counts_add_up(self):
        by = {s: sum(c["status"] == s for c in CLAIMS) for s in STATUSES}
        self.assertEqual(sum(by.values()), len(CLAIMS))


if __name__ == "__main__":
    unittest.main()
