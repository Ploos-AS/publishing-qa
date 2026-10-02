import unittest

from publishing_qa.providers import JSONReviewerAdapter, register_builtin_providers
from publishing_qa.review import AdapterRegistry, ReviewDocument, ReviewRequest


class FakeTransport:
    def __init__(self):
        self.calls = []
    def generate_json(self, **kwargs):
        self.calls.append(kwargs)
        return {"findings":[{"severity":"low","category":"language","problem":"Wording"}],"notes":"ok"}


class ProviderTests(unittest.TestCase):
    def test_generic_adapter_uses_structured_transport(self):
        t = FakeTransport()
        a = JSONReviewerAdapter(transport=t, model="x", output_schema={"type":"object"})
        r = a.review(ReviewRequest("p","r",("editorial",),(ReviewDocument("a.md","text"),)))
        self.assertEqual(len(r.findings), 1)
        self.assertEqual(t.calls[0]["model"], "x")

    def test_builtin_registry_is_provider_neutral(self):
        transports = {x:FakeTransport() for x in ("openai","anthropic","google","mistral")}
        registry = AdapterRegistry()
        register_builtin_providers(registry, transports, {x:"model" for x in transports}, {"type":"object"})
        self.assertEqual(registry.providers, ("anthropic","google","mistral","openai"))
        self.assertEqual(registry.create("openai").provider, "openai")

    def test_prompt_does_not_contain_other_reviewer_findings(self):
        t = FakeTransport()
        a = JSONReviewerAdapter(transport=t, model="x", output_schema={})
        a.review(ReviewRequest("p","r",("technical",),(ReviewDocument("a.md","source"),), context={"release":"rc1"}))
        self.assertNotIn("other reviewer", t.calls[0]["prompt"].lower())


if __name__ == "__main__":
    unittest.main()
