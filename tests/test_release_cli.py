import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from publishing_qa.release_cli import release_main
from publishing_qa.validation import ArtifactValidationError


class ReleaseCLITests(unittest.TestCase):
    def fixture(self, human=True):
        td=tempfile.TemporaryDirectory()
        root=Path(td.name)
        cfg={
          "qa_version":1,
          "project":{"type":"course-book","primary_language":"nb","languages":["nb","en"]},
          "ai":{"reviewers":{"required":[{"id":"openai"},{"id":"anthropic"},{"id":"google"},{"id":"mistral"}]}},
          "release":{"max_blocker":0,"max_critical":0,"max_high":0,"require_deterministic_tests":True,"require_build":True,"require_human_approval":True},
        }
        (root/"publishing-qa.yml").write_text(yaml.safe_dump(cfg),encoding="utf-8")
        digest="a"*64
        (root/"det.json").write_text(json.dumps({"passed":True,"build_passed":True,"source_digest":digest}),encoding="utf-8")
        (root/"reviews.json").write_text(json.dumps({"format_version":1,"project":"course-book","source_digest":digest,"findings":[],"reviewers":[],"required_failures":[],"complete":True}),encoding="utf-8")
        q=[{"provider":p,"model":"test-model","qualified":True,"structured_output":True,"latency_ms":1,"error":None} for p in ("openai","anthropic","google","mistral")]
        (root/"qual.json").write_text(json.dumps(q),encoding="utf-8")
        args=["--config",str(root/"publishing-qa.yml"),"--deterministic",str(root/"det.json"),"--reviews",str(root/"reviews.json"),"--qualifications",str(root/"qual.json"),"--output",str(root/"qa-report.json")]
        if human: args.extend(["--human-approved","--human-approval-source-digest",digest])
        return td,root,args

    def test_pass_writes_report_and_returns_zero(self):
        td,root,args=self.fixture()
        try:
            self.assertEqual(release_main(args),0)
            report=json.loads((root/"qa-report.json").read_text())
            self.assertEqual(report["decision"],"PASS")
        finally: td.cleanup()

    def test_fail_returns_one_but_still_writes_report(self):
        td,root,args=self.fixture(human=False)
        try:
            self.assertEqual(release_main(args),1)
            report=json.loads((root/"qa-report.json").read_text())
            self.assertEqual(report["decision"],"FAIL")
            self.assertIn("human approval missing",report["release_gate"]["blocking_reasons"])
        finally: td.cleanup()

    def test_human_approval_digest_mismatch_fails(self):
        td,root,args=self.fixture()
        try:
            i=args.index("--human-approval-source-digest")
            args[i+1]="b"*64
            self.assertEqual(release_main(args),1)
            report=json.loads((root/"qa-report.json").read_text())
            self.assertEqual(report["decision"],"FAIL")
            self.assertIn("source identity mismatch", " ".join(report["release_gate"]["blocking_reasons"]))
        finally: td.cleanup()

    def test_malformed_review_run_is_rejected(self):
        td,root,args=self.fixture()
        try:
            (root/"reviews.json").write_text(json.dumps({"complete":True,"findings":[]}),encoding="utf-8")
            with patch("sys.stderr") as stderr:
                self.assertEqual(release_main(args),2)
            self.assertTrue(stderr.write.called)
            self.assertFalse((root/"qa-report.json").exists())
        finally: td.cleanup()

    def test_qualification_must_be_array(self):
        td,root,args=self.fixture()
        try:
            (root/"qual.json").write_text(json.dumps({"provider":"openai"}),encoding="utf-8")
            with patch("sys.stderr") as stderr:
                self.assertEqual(release_main(args),2)
            self.assertTrue(stderr.write.called)
        finally: td.cleanup()

    def test_bad_evidence_key_is_rejected(self):
        td,root,args=self.fixture()
        try:
            (root/"evidence.json").write_text(json.dumps({"anything":[]}),encoding="utf-8")
            args.extend(["--evidence",str(root/"evidence.json")])
            with patch("sys.stderr") as stderr:
                self.assertEqual(release_main(args),2)
            self.assertTrue(stderr.write.called)
        finally: td.cleanup()

    def test_invalid_config_returns_two(self):
        td,root,args=self.fixture()
        try:
            (root/"publishing-qa.yml").write_text("qa_version: 1\nproject: {}\n", encoding="utf-8")
            with patch("sys.stderr") as stderr:
                self.assertEqual(release_main(args),2)
            self.assertTrue(stderr.write.called)
        finally: td.cleanup()


if __name__=="__main__":
    unittest.main()
