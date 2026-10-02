import unittest
from pathlib import Path

from publishing_qa.orchestrator import run_reviews
from publishing_qa.review import AdapterRegistry, ReviewDocument, ReviewResponse

SCHEMA = Path("schema/finding.schema.json")


class Good:
    provider = "good"
    def review(self, request):
        return ReviewResponse(
            reviewer_id=request.reviewer_id, provider=self.provider, model="test",
            findings=({"severity":"low","category":"language","problem":"Minor wording"},),
        )


class Broken:
    provider = "broken"
    def review(self, request):
        raise RuntimeError("provider unavailable")


class OrchestratorTests(unittest.TestCase):
    def registry(self):
        r = AdapterRegistry()
        r.register("good", Good)
        r.register("broken", Broken)
        return r

    def test_required_failure_marks_run_incomplete(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"broken","roles":["fact_check"]}],"supplemental":[]}}}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA)
        self.assertFalse(result["complete"])
        self.assertEqual(result["required_failures"], ["r1"])

    def test_supplemental_failure_does_not_block(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"good","roles":["technical"]}],"supplemental":[{"id":"extra","provider":"broken","roles":["specialist"]}]}}}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA)
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["reviewers"][1]["status"], "failed")

    def test_reviewers_receive_independent_context_copies(self):
        config = {"ai":{"reviewers":{"required":[{"id":"a","provider":"good","roles":["technical"]},{"id":"b","provider":"good","roles":["pedagogy"]}]}}}
        context = {"release":"rc1"}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA, context=context)
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["reviewers"]), 2)
        self.assertNotIn("findings", result["reviewers"][1]["request"]["context"])


if __name__ == "__main__":
    unittest.main()
