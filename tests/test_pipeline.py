import unittest
from publishing_qa.pipeline import run_pipeline


CONFIG={
 "ai":{"reviewers":{"required":[{"id":"openai"},{"id":"anthropic"},{"id":"google"},{"id":"mistral"}]}},
 "release":{"max_blocker":0,"max_critical":0,"max_high":0,"require_deterministic_tests":True,"require_build":True,"require_human_approval":True},
}
DIGEST="a"*64
QUAL=[{"provider":p,"qualified":True} for p in ("openai","anthropic","google","mistral")]


class PipelineTests(unittest.TestCase):
    def pipeline(self, **kw):
        args=dict(
          project="book",
          config=CONFIG,
          deterministic_report={"passed":True,"build_passed":True,"source_digest":DIGEST},
          review_run={"complete":True,"findings":[],"source_digest":DIGEST},
          qualifications=QUAL,
          human_approved=True,
          human_approval_source_digest=DIGEST,
        )
        args.update(kw)
        return run_pipeline(**args)

    def test_end_to_end_clean_pass(self):
        r=self.pipeline()
        self.assertEqual(r["decision"],"PASS")
        self.assertEqual(r["release_gate"]["decision"],"PASS")

    def test_deterministic_failure_blocks(self):
        r=self.pipeline(deterministic_report={"passed":False,"build_passed":True,"source_digest":DIGEST})
        self.assertEqual(r["decision"],"FAIL")

    def test_incomplete_ai_board_blocks(self):
        r=self.pipeline(review_run={"complete":False,"findings":[],"source_digest":DIGEST})
        self.assertEqual(r["decision"],"FAIL")

    def test_high_finding_blocks(self):
        f={"finding_id":"F-1","severity":"high","category":"language","file":"a.md","claim":None,"problem":"bad","suggested_fix":"fix","confidence":0.9,"requires_verification":False,"verification_status":"unverified","reviewer":"openai"}
        r=self.pipeline(review_run={"complete":True,"findings":[f],"source_digest":DIGEST})
        self.assertEqual(r["decision"],"FAIL")
        self.assertTrue(r["consensus"])
        self.assertTrue(r["judged_findings"])

    def test_evidence_can_confirm_consensus(self):
        f={"finding_id":"F-1","severity":"medium","category":"fact","file":"a.md","claim":"x","problem":"wrong","suggested_fix":"fix","confidence":0.9,"requires_verification":True,"verification_status":"unverified","reviewer":"openai"}
        r=self.pipeline(review_run={"complete":True,"findings":[f]}, evidence_by_consensus={"CON-0001":[{"type":"primary_source","supports":"confirm","ref":"datasheet"}]})
        self.assertEqual(r["consensus"][0]["verification_status"],"confirmed")

    def test_deterministic_source_mismatch_blocks(self):
        r=self.pipeline(deterministic_report={"passed":True,"build_passed":True,"source_digest":"b"*64})
        self.assertEqual(r["decision"],"FAIL")
        self.assertIn("source identity mismatch", " ".join(r["release_gate"]["blocking_reasons"]))

    def test_human_approval_source_mismatch_blocks(self):
        r=self.pipeline(human_approval_source_digest="b"*64)
        self.assertEqual(r["decision"],"FAIL")

    def test_evidence_source_mismatch_blocks(self):
        evidence={"CON-0001":[{"type":"primary_source","supports":"confirm","ref":"x","source_digest":"b"*64}]}
        f={"finding_id":"F-1","severity":"medium","category":"fact","file":"a.md","claim":"x","problem":"wrong","suggested_fix":"fix","confidence":0.9,"requires_verification":True,"verification_status":"unverified","reviewer":"openai"}
        r=self.pipeline(review_run={"complete":True,"findings":[f],"source_digest":DIGEST}, evidence_by_consensus=evidence)
        self.assertEqual(r["decision"],"FAIL")

    def test_evidence_without_source_digest_blocks(self):
        evidence={"CON-0001":[{"type":"primary_source","supports":"confirm","ref":"x"}]}
        f={"finding_id":"F-1","severity":"medium","category":"fact","file":"a.md","claim":"x","problem":"wrong","suggested_fix":"fix","confidence":0.9,"requires_verification":True,"verification_status":"unverified","reviewer":"openai"}
        r=self.pipeline(review_run={"complete":True,"findings":[f],"source_digest":DIGEST}, evidence_by_consensus=evidence)
        self.assertEqual(r["decision"],"FAIL")
        self.assertIn("source identity mismatch", " ".join(r["release_gate"]["blocking_reasons"]))

    def test_matching_evidence_source_digest_preserves_identity(self):
        evidence={"CON-0001":[{"type":"primary_source","supports":"confirm","ref":"x","source_digest":DIGEST}]}
        f={"finding_id":"F-1","severity":"medium","category":"fact","file":"a.md","claim":"x","problem":"wrong","suggested_fix":"fix","confidence":0.9,"requires_verification":True,"verification_status":"unverified","reviewer":"openai"}
        r=self.pipeline(review_run={"complete":True,"findings":[f],"source_digest":DIGEST}, evidence_by_consensus=evidence)
        self.assertNotIn("source identity mismatch", " ".join(r["release_gate"]["blocking_reasons"]))

    def test_human_approval_blocks(self):
        self.assertEqual(self.pipeline(human_approved=False)["decision"],"FAIL")


if __name__=="__main__":
    unittest.main()
