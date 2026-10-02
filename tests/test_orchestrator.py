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


class SecretBroken:
    provider = "secret-broken"
    def review(self, request):
        raise RuntimeError("Authorization: Bearer super-secret-token API_KEY=sk-abcdefgh12345678 " + "x"*1000)


class OrchestratorTests(unittest.TestCase):
    def registry(self):
        r = AdapterRegistry()
        r.register("good", Good)
        r.register("broken", Broken)
        r.register("secret-broken", SecretBroken)
        return r

    def test_required_failure_marks_run_incomplete(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"broken","roles":["fact_check"]}],"supplemental":[]}}}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA)
        self.assertFalse(result["complete"])
        self.assertEqual(result["required_failures"], ["r1"])

    def test_failure_audit_sanitizes_secrets_and_limits_error_size(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"secret-broken","roles":["technical"]}]}}}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA)
        error = result["reviewers"][0]["error"]
        self.assertNotIn("super-secret-token", error)
        self.assertNotIn("sk-abcdefgh12345678", error)
        self.assertIn("[REDACTED]", error)
        self.assertLessEqual(len(error), 260)

    def test_supplemental_failure_does_not_block(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"good","roles":["technical"]}],"supplemental":[{"id":"extra","provider":"broken","roles":["specialist"]}]}}}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA)
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["reviewers"][1]["status"], "failed")

    def test_default_audit_does_not_store_document_content_or_notes(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"good","roles":["technical"]}]}}}
        secret = "private manuscript sentence"
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md",secret,"en"),), registry=self.registry(), schema_path=SCHEMA)
        audit = result["reviewers"][0]
        self.assertNotIn(secret, str(audit))
        self.assertNotIn("content", audit["request"]["documents"][0])
        self.assertEqual(audit["request"]["documents"][0]["size_bytes"], len(secret.encode("utf-8")))
        self.assertEqual(audit["request"]["source_digest"], result["source_digest"])
        self.assertNotIn("notes", audit["response"])

    def test_full_audit_content_requires_explicit_opt_in(self):
        config = {"ai":{"reviewers":{"required":[{"id":"r1","provider":"good","roles":["technical"]}]}}}
        secret = "debug manuscript"
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md",secret,"en"),), registry=self.registry(), schema_path=SCHEMA, audit_full_content=True)
        self.assertEqual(result["reviewers"][0]["request"]["documents"][0]["content"], secret)
        self.assertIn("notes", result["reviewers"][0]["response"])

    def test_reviewers_receive_independent_context_copies(self):
        config = {"ai":{"reviewers":{"required":[{"id":"a","provider":"good","roles":["technical"]},{"id":"b","provider":"good","roles":["pedagogy"]}]}}}
        context = {"release":"rc1"}
        result = run_reviews(project="x", config=config, documents=(ReviewDocument("a.md","x"),), registry=self.registry(), schema_path=SCHEMA, context=context)
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["reviewers"]), 2)
        self.assertNotIn("findings", result["reviewers"][1]["request"]["context"])


if __name__ == "__main__":
    unittest.main()
