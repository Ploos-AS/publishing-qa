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
          "project":{"type":"course-book"},
          "ai":{"reviewers":{"required":[{"id":"openai"},{"id":"anthropic"},{"id":"google"},{"id":"mistral"}]}},
          "release":{"max_blocker":0,"max_critical":0,"max_high":0,"require_deterministic_tests":True,"require_build":True,"require_human_approval":True},
        }
        (root/"publishing-qa.yml").write_text(yaml.safe_dump(cfg),encoding="utf-8")
        (root/"det.json").write_text(json.dumps({"passed":True,"build_passed":True}),encoding="utf-8")
        (root/"reviews.json").write_text(json.dumps({"format_version":1,"project":"course-book","findings":[],"reviewers":[],"required_failures":[],"complete":True}),encoding="utf-8")
        q=[{"provider":p,"qualified":True} for p in ("openai","anthropic","google","mistral")]
        (root/"qual.json").write_text(json.dumps(q),encoding="utf-8")
        args=["--config",str(root/"publishing-qa.yml"),"--deterministic",str(root/"det.json"),"--reviews",str(root/"reviews.json"),"--qualifications",str(root/"qual.json"),"--output",str(root/"qa-report.json")]
        if human: args.append("--human-approved")
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

    def test_malformed_review_run_is_rejected(self):
        td,root,args=self.fixture()
        try:
            (root/"reviews.json").write_text(json.dumps({"complete":True,"findings":[]}),encoding="utf-8")
            with self.assertRaises(ArtifactValidationError):
                release_main(args)
            self.assertFalse((root/"qa-report.json").exists())
        finally: td.cleanup()

    def test_qualification_must_be_array(self):
        td,root,args=self.fixture()
        try:
            (root/"qual.json").write_text(json.dumps({"provider":"openai"}),encoding="utf-8")
            with self.assertRaises(ArtifactValidationError):
                release_main(args)
        finally: td.cleanup()

    def test_bad_evidence_key_is_rejected(self):
        td,root,args=self.fixture()
        try:
            (root/"evidence.json").write_text(json.dumps({"anything":[]}),encoding="utf-8")
            args.extend(["--evidence",str(root/"evidence.json")])
            with self.assertRaises(ArtifactValidationError):
                release_main(args)
        finally: td.cleanup()


if __name__=="__main__":
    unittest.main()
