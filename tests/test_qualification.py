import unittest

from publishing_qa.qualification import qualification_complete, qualify_provider
from publishing_qa.review import ReviewResponse


class GoodAdapter:
    def review(self, request):
        return ReviewResponse(request.reviewer_id, "fake", "m", tuple(), "ok")


class InvalidAdapter:
    def review(self, request):
        return ReviewResponse(request.reviewer_id, "fake", "m", ({"severity":"impossible","problem":"bad"},), "bad")


class SecretAdapter:
    def review(self, request):
        raise RuntimeError("Authorization: Bearer super-secret-token API_KEY=sk-abcdefgh12345678")


class BadAdapter:
    def review(self, request):
        raise RuntimeError("offline")


class QualificationTests(unittest.TestCase):
    def test_success(self):
        r=qualify_provider(provider="openai",adapter=GoodAdapter(),model="m")
        self.assertTrue(r["qualified"])
        self.assertIsNone(r["error"])

    def test_failure_is_reported_not_raised(self):
        r=qualify_provider(provider="openai",adapter=BadAdapter(),model="m")
        self.assertFalse(r["qualified"])
        self.assertIn("RuntimeError",r["error"])

    def test_invalid_structured_finding_does_not_qualify(self):
        r=qualify_provider(provider="openai",adapter=InvalidAdapter(),model="m")
        self.assertFalse(r["qualified"])
        self.assertFalse(r["structured_output"])
        self.assertIn("ValueError", r["error"])

    def test_error_is_sanitized(self):
        r=qualify_provider(provider="openai",adapter=SecretAdapter(),model="m")
        self.assertFalse(r["qualified"])
        self.assertNotIn("super-secret-token", r["error"])
        self.assertNotIn("sk-abcdefgh12345678", r["error"])
        self.assertIn("[REDACTED]", r["error"])

    def test_all_required_must_pass(self):
        self.assertFalse(qualification_complete([{"provider":"openai","qualified":True}],["openai","anthropic"]))
        self.assertTrue(qualification_complete([
            {"provider":"openai","qualified":True},{"provider":"anthropic","qualified":True}
        ],["openai","anthropic"]))


if __name__=="__main__":
    unittest.main()
