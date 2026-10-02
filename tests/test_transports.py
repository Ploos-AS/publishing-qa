import unittest

from publishing_qa.providers.transports import AnthropicTransport, GeminiTransport, MistralTransport, OpenAITransport


class FakeClient:
    def __init__(self, response):
        self.response=response; self.calls=[]
    def post(self, url, **kwargs):
        self.calls.append((url,kwargs)); return self.response


SCHEMA={"type":"object","properties":{"findings":{"type":"array"}},"required":["findings"]}


class TransportTests(unittest.TestCase):
    def test_openai_uses_responses_structured_output_and_no_store(self):
        c=FakeClient({"output_text":"{\"findings\":[]}"})
        t=OpenAITransport(api_key="x",client=c)
        self.assertEqual(t.generate_json(model="m",system="s",prompt="p",schema=SCHEMA),{"findings":[]})
        payload=c.calls[0][1]["payload"]
        self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"],"json_schema")

    def test_gemini_uses_interactions_response_format(self):
        c=FakeClient({"output_text":"{\"findings\":[]}"})
        t=GeminiTransport(api_key="x",client=c)
        t.generate_json(model="m",system="s",prompt="p",schema=SCHEMA)
        self.assertEqual(c.calls[0][1]["payload"]["response_format"]["mime_type"],"application/json")

    def test_mistral_uses_json_schema_mode(self):
        c=FakeClient({"choices":[{"message":{"content":"{\"findings\":[]}"}}]})
        t=MistralTransport(api_key="x",client=c)
        t.generate_json(model="m",system="s",prompt="p",schema=SCHEMA)
        self.assertEqual(c.calls[0][1]["payload"]["response_format"]["type"],"json_schema")

    def test_anthropic_uses_output_config_format(self):
        c=FakeClient({"content":[{"type":"text","text":"{\\\"findings\\\":[]}"}]})
        t=AnthropicTransport(api_key="x",client=c)
        t.generate_json(model="m",system="s",prompt="p",schema=SCHEMA)
        payload=c.calls[0][1]["payload"]
        self.assertEqual(payload["output_config"]["format"]["type"],"json_schema")


if __name__=="__main__":
    unittest.main()
