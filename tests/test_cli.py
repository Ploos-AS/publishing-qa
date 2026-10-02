import json
import tempfile
import unittest
from pathlib import Path

from publishing_qa.cli import run


SCHEMA = Path("schema/finding.schema.json").resolve()


class DeterministicQATests(unittest.TestCase):
    def test_broken_local_link_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "publishing-qa.yml").write_text(
                "qa_version: 1\nproject:\n  primary_language: nb\n  languages: [nb, en]\n",
                encoding="utf-8",
            )
            (root / "chapter.md").write_text("[missing](nope.md)\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["severity"] == "high" and f["category"] == "reference" for f in findings))

    def test_empty_alt_text_is_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "publishing-qa.yml").write_text(
                "qa_version: 1\nproject:\n  primary_language: nb\n  languages: [nb]\n",
                encoding="utf-8",
            )
            (root / "image.png").write_bytes(b"x")
            (root / "chapter.md").write_text("![](image.png)\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "accessibility" for f in findings))


if __name__ == "__main__":
    unittest.main()
