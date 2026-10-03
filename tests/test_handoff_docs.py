"""docs/handoff.md and docs/compat.md name files and commands; a path that no longer exists means the instructions have rotted."""
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("docs/handoff.md", "docs/compat.md", "docs/linux.md", "docs/agent-tasks/README.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs/agent-tasks").glob("0*.md")))
PATH = re.compile(r"`((?:tools|docs|research|packaging|tests|skill|site|\.github)/[\w./-]+\.(?:py|sh|md|yml|html|toml|json))`")


class DocsPointAtRealFiles(unittest.TestCase):
    def test_every_path_in_backticks_exists(self):
        for doc in DOCS:
            text = (ROOT / doc).read_text()
            for rel in sorted(set(PATH.findall(text))):
                with self.subTest(doc=doc, path=rel):
                    self.assertTrue((ROOT / rel).exists(), f"{doc} names {rel}, which does not exist")

    def test_the_promotion_checklist_names_strings_that_are_really_there(self):
        # item 1 of the hand-off says these places quote the tested version; if one stops doing so the list is wrong
        for rel, quote in (("README.md", "Maestro (tested with 2.0.10)"), ("skill/shotfleet/SKILL.md", "tested with 2.0.10"),
                           ("skill/shotfleet/references/troubleshooting.md", "tested with 2.0.10"), ("tests/test_agent_skills.py", "Maestro (tested with 2.0.10)"),
                           ("tests/test_doctor_versions.py", "MAESTRO_TESTED"), ("shotfleet.py", "MAESTRO_TESTED = ("), ("shotfleet.py", "MAESTRO_PIN = {")):
            with self.subTest(file=rel, quote=quote):
                self.assertIn(quote, (ROOT / rel).read_text())

    def test_the_handoff_has_the_pinned_checksum_of_2_11_0_that_the_research_recorded(self):
        sha = "5384593cb4e7a106489e75a821d157dd43f4e438df6bc308b72e82c685e1283a"
        self.assertIn(sha, (ROOT / "docs/handoff.md").read_text())
        self.assertIn(sha[:8], (ROOT / "research/maestro-2-11.md").read_text())


if __name__ == "__main__":
    unittest.main()
