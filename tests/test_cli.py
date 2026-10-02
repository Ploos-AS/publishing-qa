import tempfile
import unittest
from pathlib import Path

from publishing_qa.cli import run

SCHEMA = Path("schema/finding.schema.json").resolve()


def config(root, extra=""):
    (root / "publishing-qa.yml").write_text(
        "qa_version: 1\nproject:\n  primary_language: nb\n  languages: [nb, en]\n" + extra,
        encoding="utf-8",
    )


class DeterministicQATests(unittest.TestCase):
    def test_broken_local_link_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config(root)
            (root / "chapter.md").write_text("[missing](nope.md)\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["severity"] == "high" and f["category"] == "reference" for f in findings))

    def test_empty_alt_text_is_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config(root)
            (root / "image.png").write_bytes(b"x")
            (root / "chapter.md").write_text("![](image.png)\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "accessibility" for f in findings))

    def test_language_counterpart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "parity:\n  enabled: true\n  language_dirs:\n    nb: docs/nb\n    en: docs/en\n")
            (root / "docs/nb").mkdir(parents=True); (root / "docs/en").mkdir(parents=True)
            (root / "docs/nb/01.md").write_text("# Hei\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "translation" and f["severity"] == "high" for f in findings))

    def test_exercise_requires_solution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "exercises:\n  enabled: true\n  exercise_dir: exercises\n  solution_dir: solutions\n")
            (root / "exercises").mkdir()
            (root / "exercises/01.md").write_text("# Oppgave\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "solution" and f["severity"] == "high" for f in findings))

    def test_unbalanced_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config(root)
            (root / "chapter.md").write_text("```python\nprint('x')\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "build" and f["severity"] == "high" for f in findings))


if __name__ == "__main__":
    unittest.main()
