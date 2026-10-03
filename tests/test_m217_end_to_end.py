import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from publishing_qa.cli import main as deterministic_main
from publishing_qa.orchestrator import run_reviews
from publishing_qa.package import build_review_documents
from publishing_qa.release_cli import release_main
from publishing_qa.review import AdapterRegistry, ReviewResponse


class Clean:
    provider = "clean"
    def review(self, request):
        return ReviewResponse(
            reviewer_id=request.reviewer_id,
            provider=self.provider,
            model="test",
            findings=(),
        )


class M217EndToEndTests(unittest.TestCase):
    def test_real_artifact_chain_passes_and_stale_deterministic_report_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            chapter = root / "docs/01.md"
            chapter.write_text("# Chapter\n", encoding="utf-8")
            config = {
                "qa_version": 1,
                "project": {"type": "course-book", "primary_language": "nb", "languages": ["nb"]},
                "source": {"paths": ["docs"]},
                "ai": {"reviewers": {"required": [
                    {"id": "openai", "provider": "clean", "roles": ["technical"]},
                    {"id": "anthropic", "provider": "clean", "roles": ["pedagogy"]},
                    {"id": "google", "provider": "clean", "roles": ["fact_check"]},
                    {"id": "mistral", "provider": "clean", "roles": ["independent"]},
                ], "supplemental": []}},
                "release": {"max_blocker": 0, "max_critical": 0, "max_high": 0,
                            "require_deterministic_tests": True, "require_build": True,
                            "require_human_approval": True},
            }
            cfg = root / "publishing-qa.yml"
            cfg.write_text(yaml.safe_dump(config), encoding="utf-8")
            det = root / "det.json"
            finding_schema = Path(__file__).resolve().parents[1] / "schema/finding.schema.json"
            with patch("sys.argv", ["publishing-qa", str(root), "--schema", str(finding_schema), "--output", str(det)]), self.assertRaises(SystemExit) as exit:
                deterministic_main()
            self.assertEqual(exit.exception.code, 0)
            deterministic = json.loads(det.read_text(encoding="utf-8"))

            registry = AdapterRegistry()
            registry.register("clean", Clean)
            reviews = run_reviews(
                project="course-book",
                config=config,
                documents=build_review_documents(root, ["docs"], "nb"),
                registry=registry,
                schema_path=finding_schema,
            )
            reviews_path = root / "reviews.json"
            reviews_path.write_text(json.dumps(reviews), encoding="utf-8")
            qualifications = [
                {"provider": p, "model": "test", "qualified": True, "structured_output": True, "latency_ms": 1, "error": None}
                for p in ("openai", "anthropic", "google", "mistral")
            ]
            qual_path = root / "qual.json"
            qual_path.write_text(json.dumps(qualifications), encoding="utf-8")
            report_path = root / "release.json"
            args = ["--config", str(cfg), "--deterministic", str(det), "--reviews", str(reviews_path),
                    "--qualifications", str(qual_path), "--human-approved",
                    "--human-approval-source-digest", reviews["source_digest"], "--output", str(report_path)]
            self.assertEqual(release_main(args), 0)
            self.assertEqual(json.loads(report_path.read_text())["decision"], "PASS")
            self.assertEqual(deterministic["source_digest"], reviews["source_digest"])

            chapter.write_text("# Changed chapter\n", encoding="utf-8")
            changed_reviews = run_reviews(
                project="course-book", config=config,
                documents=build_review_documents(root, ["docs"], "nb"),
                registry=registry, schema_path=finding_schema,
            )
            reviews_path.write_text(json.dumps(changed_reviews), encoding="utf-8")
            args[args.index("--human-approval-source-digest") + 1] = changed_reviews["source_digest"]
            self.assertEqual(release_main(args), 1)
            failed = json.loads(report_path.read_text())
            self.assertEqual(failed["decision"], "FAIL")
            self.assertIn("source identity mismatch", " ".join(failed["release_gate"]["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
