import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "live-qualification.yml"


class LiveQualificationWorkflowTests(unittest.TestCase):
    def test_live_workflow_is_manual_only_and_bounded(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        triggers = data.get("on", data.get(True))
        self.assertIsInstance(triggers, dict)
        self.assertEqual(set(triggers), {"workflow_dispatch"})
        self.assertNotIn("push", triggers)
        self.assertNotIn("pull_request", triggers)

        concurrency = data["concurrency"]
        self.assertEqual(concurrency["group"], "live-provider-qualification")
        self.assertFalse(concurrency["cancel-in-progress"])

        job = data["jobs"]["qualify"]
        self.assertEqual(job["environment"], "live-provider-qualification")
        self.assertEqual(job["timeout-minutes"], 10)
        self.assertEqual(data["permissions"], {"contents": "read"})

    def test_live_workflow_does_not_define_literal_api_keys(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY"):
            self.assertIn("secrets." + name, text)


if __name__ == "__main__":
    unittest.main()
