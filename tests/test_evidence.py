import tempfile
import unittest
from pathlib import Path

from publishing_qa.evidence import Evidence, digest_file, verification_from_evidence


class EvidenceTests(unittest.TestCase):
    def test_primary_source_can_confirm(self):
        status = verification_from_evidence([{"type":"primary_source","supports":"confirm"}])
        self.assertEqual(status, "confirmed")

    def test_executable_test_can_confirm(self):
        status = verification_from_evidence([{"type":"executable_test","supports":"confirm"}])
        self.assertEqual(status, "confirmed")

    def test_secondary_source_alone_is_only_likely(self):
        status = verification_from_evidence([{"type":"secondary_source","supports":"confirm"}])
        self.assertEqual(status, "likely")

    def test_conflicting_evidence_is_disputed(self):
        status = verification_from_evidence([
            {"type":"primary_source","supports":"confirm"},
            {"type":"compiler","supports":"dispute"},
        ])
        self.assertEqual(status, "disputed")

    def test_strong_dispute_marks_false_positive(self):
        status = verification_from_evidence([{"type":"standard","supports":"dispute"}])
        self.assertEqual(status, "false_positive")

    def test_file_digest_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "result.txt"
            p.write_text("PASS", encoding="utf-8")
            a = digest_file(p)
            p.write_text("FAIL", encoding="utf-8")
            self.assertNotEqual(a, digest_file(p))

    def test_evidence_record_gets_timestamp(self):
        record = Evidence("E-1","compiler","build.log","confirm").record()
        self.assertTrue(record["collected_at"])


if __name__ == "__main__":
    unittest.main()
