import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from publishing_qa import qualification_cli


class QualificationCLITests(unittest.TestCase):
    def test_missing_model_writes_failure_artifact_and_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qualification.json"
            argv = ["ploos-qa-qualify", "--provider", "openai", "--output", str(output)]
            with patch.dict(os.environ, {}, clear=True), patch("sys.argv", argv), self.assertRaises(SystemExit) as exit:
                qualification_cli.main()
            self.assertEqual(exit.exception.code, 1)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["provider"], "openai")
            self.assertFalse(data[0]["qualified"])
            self.assertIn("OPENAI_MODEL", data[0]["error"])

    def test_selected_provider_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qualification.json"
            argv = ["ploos-qa-qualify", "--provider", "mistral", "--output", str(output)]
            with patch.dict(os.environ, {}, clear=True), patch("sys.argv", argv), self.assertRaises(SystemExit):
                qualification_cli.main()
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([item["provider"] for item in data], ["mistral"])

    def test_successful_qualification_exits_zero(self):
        result = {
            "provider": "openai", "model": "test-model", "qualified": True,
            "structured_output": True, "latency_ms": 1, "error": None,
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qualification.json"
            argv = ["ploos-qa-qualify", "--provider", "openai", "--output", str(output)]
            with patch.dict(os.environ, {"OPENAI_MODEL": "test-model"}, clear=True), \
                 patch("publishing_qa.qualification_cli.build_adapter", return_value=object()), \
                 patch("publishing_qa.qualification_cli.qualify_provider", return_value=result), \
                 patch("sys.argv", argv), self.assertRaises(SystemExit) as exit:
                qualification_cli.main()
            self.assertEqual(exit.exception.code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), [result])


if __name__ == "__main__":
    unittest.main()
