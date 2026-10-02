import unittest
from pathlib import Path

from publishing_qa.normalize import normalize_and_validate
from publishing_qa.review import AdapterRegistry, ReviewDocument, ReviewRequest, ReviewResponse


SCHEMA = Path("schema/finding.schema.json")


class FakeAdapter:
    provider = "fake"

    def __init__(self, model="fake-1"):
        self.model = model

    def review(self, request):
        return ReviewResponse(
            reviewer_id=request.reviewer_id,
            provider=self.provider,
            model=self.model,
            findings=({"severity": "warning", "category": "factual", "problem": "Check claim"},),
        )


class ReviewContractTests(unittest.TestCase):
    def test_registry_is_extensible(self):
        registry = AdapterRegistry()
        registry.register("fake", FakeAdapter)
        adapter = registry.create("fake", model="fake-2")
        self.assertEqual(adapter.model, "fake-2")

    def test_independent_request_contract(self):
        request = ReviewRequest(
            project="book",
            reviewer_id="reviewer-a",
            roles=("fact_check",),
            documents=(ReviewDocument("docs/01.md", "# Chapter", "en"),),
        )
        response = FakeAdapter().review(request)
        self.assertEqual(response.reviewer_id, "reviewer-a")
        self.assertEqual(len(response.findings), 1)

    def test_normalization_maps_aliases_and_validates(self):
        normalized = normalize_and_validate(
            [{"severity": "warning", "category": "factual", "problem": "Check claim"}],
            "reviewer-a",
            SCHEMA,
        )
        self.assertEqual(normalized[0]["severity"], "medium")
        self.assertEqual(normalized[0]["category"], "fact")
        self.assertTrue(normalized[0]["requires_verification"])


if __name__ == "__main__":
    unittest.main()
