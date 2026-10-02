import unittest
from publishing_qa.release_gate import evaluate_release_gate


BASE={"max_blocker":0,"max_critical":0,"max_high":0,"require_deterministic_tests":True,"require_build":True,"require_human_approval":True}
QUAL=[{"provider":p,"qualified":True} for p in ("openai","anthropic","google","mistral")]
REQ=["openai","anthropic","google","mistral"]


class ReleaseGateTests(unittest.TestCase):
    def evaluate(self, **kw):
        args=dict(release=BASE,deterministic_ok=True,build_ok=True,review_run={"complete":True},qualifications=QUAL,required_providers=REQ,judged_findings=[],human_approved=True)
        args.update(kw)
        return evaluate_release_gate(**args)

    def test_clean_release_passes(self):
        self.assertEqual(self.evaluate()["decision"],"PASS")

    def test_missing_required_provider_fails(self):
        r=self.evaluate(qualifications=QUAL[:-1])
        self.assertEqual(r["decision"],"FAIL")
        self.assertIn("mistral", " ".join(r["blocking_reasons"]))

    def test_required_reviewer_failure_fails(self):
        self.assertEqual(self.evaluate(review_run={"complete":False})["decision"],"FAIL")

    def test_confirmed_high_fails_default_threshold(self):
        f=[{"severity":"high","disposition":"confirmed"}]
        self.assertEqual(self.evaluate(judged_findings=f)["decision"],"FAIL")

    def test_judge_max_reported_severity_is_enforced(self):
        f=[{"max_reported_severity":"high","disposition":"likely"}]
        self.assertEqual(self.evaluate(judged_findings=f)["decision"],"FAIL")

    def test_false_positive_high_does_not_block(self):
        f=[{"severity":"high","disposition":"false_positive"}]
        self.assertEqual(self.evaluate(judged_findings=f)["decision"],"PASS")

    def test_human_approval_is_real_gate(self):
        self.assertEqual(self.evaluate(human_approved=False)["decision"],"FAIL")

    def test_optional_build_can_be_disabled(self):
        cfg={**BASE,"require_build":False}
        self.assertEqual(self.evaluate(release=cfg,build_ok=False)["decision"],"PASS")


if __name__=="__main__":
    unittest.main()
