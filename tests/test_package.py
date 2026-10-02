import tempfile
import unittest
from pathlib import Path

from publishing_qa.package import build_review_documents, source_digest


class PackageTests(unittest.TestCase):
    def test_digest_is_stable_and_changes_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            p = root / "docs/01.md"
            p.write_text("# One\n", encoding="utf-8")
            first = build_review_documents(root, ["docs"], "en")
            d1 = source_digest(first)
            d2 = source_digest(first)
            self.assertEqual(d1, d2)
            p.write_text("# Two\n", encoding="utf-8")
            second = build_review_documents(root, ["docs"], "en")
            self.assertNotEqual(d1, source_digest(second))

    def test_source_digest_changes_with_content(self):
        from publishing_qa.review import ReviewDocument
        a=(ReviewDocument("docs/a.md","same","en"),)
        b=(ReviewDocument("docs/a.md","changed","en"),)
        self.assertEqual(source_digest(a), source_digest(a))
        self.assertNotEqual(source_digest(a), source_digest(b))


if __name__ == "__main__":
    unittest.main()
