import tempfile
import unittest
from pathlib import Path

from publishing_qa.provenance import collect_artifact_evidence, collect_command_evidence


class ProvenanceTests(unittest.TestCase):
    def test_successful_command_confirms(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = collect_command_evidence(
                evidence_id="E-1", kind="executable_test",
                command="python -c \"print('PASS')\"", cwd=Path(tmp),
            )
        self.assertEqual(e["supports"], "confirm")
        self.assertEqual(e["provenance"]["exit_code"], 0)
        self.assertTrue(e["source_digest"])

    def test_failed_command_disputes(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = collect_command_evidence(
                evidence_id="E-2", kind="compiler",
                command="python -c \"raise SystemExit(2)\"", cwd=Path(tmp),
            )
        self.assertEqual(e["supports"], "dispute")
        self.assertEqual(e["provenance"]["exit_code"], 2)

    def test_failed_command_can_confirm_negative_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = collect_command_evidence(
                evidence_id="E-NEG", kind="executable_test",
                command="python -c \"raise SystemExit(1)\"", cwd=Path(tmp),
                supports_on_success="dispute",
                supports_on_failure="confirm",
            )
        self.assertEqual(e["supports"], "confirm")
        self.assertEqual(e["provenance"]["exit_code"], 1)

    def test_timeout_polarity_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = collect_command_evidence(
                evidence_id="E-TIME", kind="executable_test",
                command="python -c \"import time; time.sleep(1)\"", cwd=Path(tmp),
                supports_on_timeout="dispute", timeout=0.01,
            )
        self.assertEqual(e["supports"], "dispute")
        self.assertTrue(e["provenance"]["timed_out"])

    def test_artifact_is_digested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "book.pdf"
            p.write_bytes(b"pdf")
            e = collect_artifact_evidence(evidence_id="E-3", kind="executable_test", path=p, root=root)
        self.assertEqual(e["ref"], "book.pdf")
        self.assertTrue(e["source_digest"])


if __name__ == "__main__":
    unittest.main()
