from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .pipeline import run_pipeline


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
    p.add_argument("--output", default="qa-report.json")
    args = p.parse_args(argv)

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    project = config.get("project", {}).get("name") or config.get("project", {}).get("type") or "publishing-project"
    evidence = _json(args.evidence) if args.evidence else {}

    report = run_pipeline(
        project=project,
        config=config,
        deterministic_report=_json(args.deterministic),
        review_run=_json(args.reviews),
        qualifications=_json(args.qualifications),
        evidence_by_consensus=evidence,
        human_approved=args.human_approved,
    )
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report["decision"])
    return 0 if report["decision"] == "PASS" else 1


def main():
    sys.exit(release_main())


if __name__ == "__main__":
    main()
