from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def finding(severity, category, problem, file=None, line=None):
    return {
        "finding_id": "",
        "severity": severity,
        "category": category,
        "file": file,
        "line": line,
        "claim": None,
        "problem": problem,
        "suggested_fix": None,
        "confidence": 1.0,
        "requires_verification": False,
        "verification_status": "confirmed",
        "reviewer": "deterministic",
    }


def scan_markdown(root: Path):
    findings = []
    md_files = sorted(root.rglob("*.md"))
    heading_ids = {}
    for path in md_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(finding("high", "build", "Markdown file is not valid UTF-8", str(path)))
            continue

        rel = str(path.relative_to(root))
        if "\t" in text:
            findings.append(finding("low", "consistency", "Tab character found in Markdown source", rel))

        headings = [m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.M)]
        heading_ids[rel] = headings

        for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", text):
            alt, target = match.groups()
            line = text.count("\n", 0, match.start()) + 1
            if not alt.strip():
                findings.append(finding("medium", "accessibility", "Image has empty alt text", rel, line))
            if not re.match(r"^[a-z]+://", target) and not target.startswith("#"):
                asset = (path.parent / target.split("#", 1)[0]).resolve()
                if not asset.exists():
                    findings.append(finding("high", "reference", f"Missing image asset: {target}", rel, line))

        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            target = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).resolve().exists():
                findings.append(finding("high", "reference", f"Broken local link: {target}", rel, line))

    return md_files, findings


def run(root: Path, config_path: Path, schema_path: Path):
    findings = []
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(finding("blocker", "build", f"Cannot parse QA configuration: {exc}", str(config_path)))
        return findings

    if config.get("qa_version") != 1:
        findings.append(finding("critical", "consistency", "Unsupported or missing qa_version", str(config_path)))

    project = config.get("project", {})
    if not project.get("primary_language"):
        findings.append(finding("high", "consistency", "project.primary_language is required", str(config_path)))
    if not project.get("languages"):
        findings.append(finding("high", "consistency", "project.languages must not be empty", str(config_path)))

    _, md_findings = scan_markdown(root)
    findings.extend(md_findings)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for i, item in enumerate(findings, 1):
        item["finding_id"] = f"DET-{i:04d}"
        errors = list(validator.iter_errors(item))
        if errors:
            raise RuntimeError(f"Internal finding schema violation: {errors[0].message}")

    return findings


def main():
    parser = argparse.ArgumentParser(prog="publishing-qa")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--config", default="publishing-qa.yml")
    parser.add_argument("--schema", default="schema/finding.schema.json")
    parser.add_argument("--output", default="qa-report.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = (root / args.config).resolve()
    schema = (root / args.schema).resolve()
    findings = run(root, config, schema)

    counts = {s: 0 for s in ("blocker", "critical", "high", "medium", "low", "info")}
    for item in findings:
        counts[item["severity"]] += 1

    report = {
        "format_version": 1,
        "engine": "ploos-publishing-qa",
        "findings": findings,
        "summary": counts,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(counts, sort_keys=True))
    sys.exit(1 if counts["blocker"] or counts["critical"] or counts["high"] else 0)


if __name__ == "__main__":
    main()
