from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .pipeline import run_pipeline
from .validation import ArtifactValidationError, load_schema, validate


def _json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def release_main(argv=None):
    p = argparse.ArgumentParser(prog="ploos-qa release")
    p.add_argument("--config", default="publishing-qa.yml")
    p.add_argument("--deterministic", required=True)
    p.add_argument("--reviews", required=True)
    p.add_argument("--qualifications", required=True)
    p.add_argument("--evidence")
    p.add_argument("--human-approved", action="store_true")
    p.add_argument("--human-approval-source-digest")
    p.add_argument("--output", default="qa-report.json")
    args = p.parse_args(argv)

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    schema_dir = Path(__file__).resolve().parent / "schemas"
    validate(config, load_schema(schema_dir / "config.schema.json"), "QA config")
    deterministic = _json(args.deterministic)
    reviews = _json(args.reviews)
    qualifications = _json(args.qualifications)
    evidence = _json(args.evidence) if args.evidence else {}

    validate(deterministic, load_schema(schema_dir / "deterministic-report.schema.json"), "deterministic report")
    validate(reviews, load_schema(schema_dir / "review-run.schema.json"), "review run")
    qschema = load_schema(schema_dir / "provider-qualification.schema.json")
    if not isinstance(qualifications, list):
        raise ArtifactValidationError("qualifications: <root>: must be an array")
    for i, item in enumerate(qualifications):
        validate(item, qschema, f"qualification[{i}]")
    validate(evidence, load_schema(schema_dir / "evidence-map.schema.json"), "evidence map")

    project = config.get("project", {}).get("name") or config.get("project", {}).get("type") or "publishing-project"

    report = run_pipeline(
        project=project,
        config=config,
        deterministic_report=deterministic,
        review_run=reviews,
        qualifications=qualifications,
        evidence_by_consensus=evidence,
        human_approved=args.human_approved,
        human_approval_source_digest=args.human_approval_source_digest,
    )
    validate(report, load_schema(schema_dir / "pipeline-report.schema.json"), "pipeline report")
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report["decision"])
    return 0 if report["decision"] == "PASS" else 1


def main():
    sys.exit(release_main())


if __name__ == "__main__":
    main()
