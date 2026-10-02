from __future__ import annotations

import json
from typing import Any

from .credentials import credential_for
from .http import HTTPJSONClient


class BaseHTTPTransport:
    provider = ""
    def __init__(self, *, api_key: str | None = None, client=None):
        self.api_key = api_key or credential_for(self.provider)
        self.client = client or HTTPJSONClient()


class OpenAITransport(BaseHTTPTransport):
    provider = "openai"
    url = "https://api.openai.com/v1/responses"

    def generate_json(self, *, model, system, prompt, schema):
        payload = {
            "model": model,
            "instructions": system,
            "input": prompt,
            "store": False,
            "text": {"format":{"type":"json_schema","name":"publishing_qa_review","schema":schema,"strict":True}},
        }
        data = self.client.post(self.url, headers={"Authorization":f"Bearer {self.api_key}"}, payload=payload)
        text = data.get("output_text")
        if not text:
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        text = content.get("text")
                        break
        if not text:
            raise ValueError("OpenAI response contained no output text")
        return json.loads(text)


class GeminiTransport(BaseHTTPTransport):
    provider = "google"
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def generate_json(self, *, model, system, prompt, schema):
        payload = {
            "model": model,
            "input": system + "\n\n" + prompt,
            "response_format":{"type":"text","mime_type":"application/json","schema":schema},
        }
        data = self.client.post(self.url, headers={"x-goog-api-key":self.api_key}, payload=payload)
        text = data.get("output_text")
        if not text:
            for step in data.get("steps", []):
                for content in step.get("content", []):
                    if content.get("type") == "text":
                        text = content.get("text")
                        break
        if not text:
            raise ValueError("Gemini response contained no output text")
        return json.loads(text)


class MistralTransport(BaseHTTPTransport):
    provider = "mistral"
    url = "https://api.mistral.ai/v1/chat/completions"

    def generate_json(self, *, model, system, prompt, schema):
        payload = {
            "model":model,
            "messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
            "response_format":{"type":"json_schema","json_schema":{"name":"publishing_qa_review","schema":schema,"strict":True}},
        }
        data = self.client.post(self.url, headers={"Authorization":f"Bearer {self.api_key}"}, payload=payload)
        text = data["choices"][0]["message"]["content"]
        return json.loads(text)


class AnthropicTransport(BaseHTTPTransport):
    provider = "anthropic"
    url = "https://api.anthropic.com/v1/messages"

    def generate_json(self, *, model, system, prompt, schema):
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role":"user","content":prompt}],
            "output_config":{"format":{"type":"json_schema","schema":schema}},
        }
        data = self.client.post(
            self.url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload=payload,
        )
        text = None
        for block in data.get("content", []):
            if block.get("type") == "text":
                text = block.get("text")
                break
        if not text:
            raise ValueError("Anthropic response contained no text block")
        return json.loads(text)
