import tempfile
import json
from unittest.mock import patch
import unittest
from pathlib import Path

from publishing_qa.cli import run, main
from publishing_qa.package import build_review_documents, source_digest

SCHEMA = Path("schema/finding.schema.json").resolve()


def config(root, extra=""):
    (root / "publishing-qa.yml").write_text(
        "qa_version: 1\nproject:\n  primary_language: nb\n  languages: [nb, en]\n" + extra,
        encoding="utf-8",
    )


class DeterministicQATests(unittest.TestCase):
    def test_cli_report_matches_release_deterministic_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config(root)
            (root / "chapter.md").write_text("# Hello\n", encoding="utf-8")
            output = root / "det.json"
            argv=["publishing-qa",str(root),"--schema",str(SCHEMA),"--output",str(output)]
            with patch("sys.argv", argv), self.assertRaises(SystemExit) as exit:
                main()
            self.assertEqual(exit.exception.code, 0)
            report=json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertTrue(report["build_passed"])
            self.assertRegex(report["source_digest"], r"^[0-9a-f]{64}$")

    def test_cli_digest_matches_review_document_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "source:\n  paths: [docs]\n")
            (root / "docs").mkdir()
            (root / "docs/chapter.md").write_text("# Hello\n", encoding="utf-8")
            output = root / "det.json"
            argv=["publishing-qa",str(root),"--schema",str(SCHEMA),"--output",str(output)]
            with patch("sys.argv", argv), self.assertRaises(SystemExit):
                main()
            report=json.loads(output.read_text(encoding="utf-8"))
            expected=source_digest(build_review_documents(root, ["docs"], "nb"))
            self.assertEqual(report["source_digest"], expected)

    def test_duplicate_evidence_producer_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config(root, "evidence:\n  producers:\n    - {id: test, type: executable_test, command: 'true'}\n    - {id: test, type: executable_test, command: 'true'}\n")
            with self.assertRaisesRegex(ValueError, "duplicates producer id"):
                run(root, root/"publishing-qa.yml", SCHEMA)

    def test_evidence_binding_unknown_producer_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config(root, "evidence:\n  producers: []\n  bindings:\n    - match: {category: fact}\n      producers: [missing]\n")
            with self.assertRaisesRegex(ValueError, "unknown producer"):
                run(root, root/"publishing-qa.yml", SCHEMA)

    def test_invalid_evidence_polarity_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config(root, "evidence:\n  producers:\n    - {id: test, type: executable_test, command: 'true', supports_on_success: maybe}\n")
            with self.assertRaisesRegex(ValueError, "supports_on_success"):
                run(root, root/"publishing-qa.yml", SCHEMA)

    def test_cli_invalid_config_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"publishing-qa.yml").write_text("qa_version: 1\nproject: {}\n", encoding="utf-8")
            argv=["publishing-qa",str(root),"--schema",str(SCHEMA),"--output",str(root/"det.json")]
            with patch("sys.argv", argv), patch("sys.stderr"), self.assertRaises(SystemExit) as exit:
                main()
            self.assertEqual(exit.exception.code, 2)
            self.assertFalse((root/"det.json").exists())

    def test_cli_semantic_evidence_error_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config(root, "evidence:\n  producers:\n    - {id: x, type: executable_test, command: 'true', supports_on_success: invalid}\n")
            argv=["publishing-qa",str(root),"--schema",str(SCHEMA),"--output",str(root/"det.json")]
            with patch("sys.argv", argv), patch("sys.stderr"), self.assertRaises(SystemExit) as exit:
                main()
            self.assertEqual(exit.exception.code, 2)

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


    def test_publication_metadata_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "publication:\n  enabled: true\n  metadata_file: publication.yml\n  required_metadata: [title, author, publisher, license]\n  required_artifacts: [dist/book.epub]\n")
            (root / "publication.yml").write_text("title: Test\nauthor: Author\npublisher: Ploos AS\nlicense: CC-BY-4.0\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any("artifact is missing" in f["problem"] for f in findings))

    def test_required_artifact_generated_by_hook_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "publication:\n  enabled: true\n  metadata_file: publication.yml\n  required_artifacts: [dist/book.epub]\nhooks:\n  - name: build\n    command: mkdir -p dist && printf epub > dist/book.epub\n")
            (root / "publication.yml").write_text("title: Test\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertFalse(any("artifact is missing" in f["problem"] for f in findings))

    def test_failed_hook_keeps_required_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "publication:\n  enabled: true\n  metadata_file: publication.yml\n  required_artifacts: [dist/book.epub]\nhooks:\n  - name: build\n    command: exit 1\n")
            (root / "publication.yml").write_text("title: Test\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any("Hook failed: build" in f["problem"] for f in findings))
            self.assertTrue(any("artifact is missing" in f["problem"] for f in findings))

    def test_duplicate_isbn_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "publication:\n  enabled: true\n  metadata_file: publication.yml\n")
            (root / "publication.yml").write_text("isbn:\n  epub: '9781234567897'\n  pdf: '9781234567897'\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any("ISBN is reused" in f["problem"] and f["severity"] == "high" for f in findings))

    def test_chapter_manifest_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "chapter_order:\n  enabled: true\n  manifest: chapters.yml\n")
            (root / "chapters.yml").write_text("chapters:\n  - docs/01.md\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any(f["category"] == "reference" and "does not exist" in f["problem"] for f in findings))


    def test_structure_parity_detects_heading_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "parity:\n  enabled: true\n  structure: true\n  language_dirs:\n    nb: docs/nb\n    en: docs/en\n")
            (root / "docs/nb").mkdir(parents=True); (root / "docs/en").mkdir(parents=True)
            (root / "docs/nb/01.md").write_text("# Tittel\n## Del\n", encoding="utf-8")
            (root / "docs/en/01.md").write_text("# Title\n### Part\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any("Heading structure differs" in f["problem"] for f in findings))

    def test_structure_parity_detects_code_language_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config(root, "parity:\n  enabled: true\n  structure: true\n  language_dirs:\n    nb: docs/nb\n    en: docs/en\n")
            (root / "docs/nb").mkdir(parents=True); (root / "docs/en").mkdir(parents=True)
            (root / "docs/nb/01.md").write_text("# Tittel\n```python\nprint(1)\n```\n", encoding="utf-8")
            (root / "docs/en/01.md").write_text("# Title\n```text\nprint(1)\n```\n", encoding="utf-8")
            findings = run(root, root / "publishing-qa.yml", SCHEMA)
            self.assertTrue(any("Code-block language structure differs" in f["problem"] for f in findings))


if __name__ == "__main__":
    unittest.main()
