import unittest

from publishing_qa.qualification import qualification_complete, qualify_provider
from publishing_qa.review import ReviewResponse


class GoodAdapter:
    def review(self, request):
        return ReviewResponse(request.reviewer_id, "fake", "m", tuple(), "ok")


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

    def test_all_required_must_pass(self):
        self.assertFalse(qualification_complete([{"provider":"openai","qualified":True}],["openai","anthropic"]))
        self.assertTrue(qualification_complete([
            {"provider":"openai","qualified":True},{"provider":"anthropic","qualified":True}
        ],["openai","anthropic"]))


if __name__=="__main__":
    unittest.main()
