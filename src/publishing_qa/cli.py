from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .package import build_review_documents, source_digest
from .review import ReviewDocument
from .validation import load_schema, validate


def finding(severity, category, problem, file=None, line=None):
    return {
        "finding_id": "", "severity": severity, "category": category,
        "file": file, "line": line, "claim": None, "problem": problem,
        "suggested_fix": None, "confidence": 1.0,
        "requires_verification": False, "verification_status": "confirmed",
        "reviewer": "deterministic",
    }


def markdown_files(root, paths):
    if not paths:
        return sorted(root.rglob("*.md"))
    found = []
    for item in paths:
        p = root / item
        found.extend(p.rglob("*.md") if p.is_dir() else ([p] if p.suffix == ".md" and p.exists() else []))
    return sorted(set(found))


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return False
    try:
        return yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return False


def scan_markdown(root: Path, config):
    findings = []
    source = config.get("source", {})
    files = markdown_files(root, source.get("paths", []))
    required_fm = source.get("frontmatter_required", [])
    for path in files:
        rel = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(finding("high", "build", "Markdown file is not valid UTF-8", rel))
            continue

        fm = frontmatter(text)
        if required_fm and fm is None:
            findings.append(finding("medium", "consistency", "Required YAML frontmatter is missing", rel, 1))
        elif fm is False:
            findings.append(finding("high", "build", "Invalid YAML frontmatter", rel, 1))
        elif isinstance(fm, dict):
            for key in required_fm:
                if key not in fm or fm[key] in (None, ""):
                    findings.append(finding("medium", "consistency", f"Required frontmatter field is missing: {key}", rel, 1))

        if "\t" in text:
            findings.append(finding("low", "consistency", "Tab character found in Markdown source", rel))

        if text.count("```") % 2:
            findings.append(finding("high", "build", "Unbalanced fenced code block", rel))

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
    return files, findings


def check_language_parity(root, config):
    findings = []
    parity = config.get("parity", {})
    if not parity.get("enabled"):
        return findings
    dirs = parity.get("language_dirs", {})
    primary = config["project"]["primary_language"]
    base = root / dirs.get(primary, primary)
    if not base.exists():
        return [finding("high", "translation", f"Primary language directory is missing: {base.relative_to(root)}")]
    for lang in config["project"].get("languages", []):
        if lang == primary:
            continue
        other = root / dirs.get(lang, lang)
        if not other.exists():
            findings.append(finding("high", "translation", f"Language directory is missing: {other.relative_to(root)}"))
            continue
        for src in base.rglob("*.md"):
            rel = src.relative_to(base)
            if not (other / rel).exists():
                findings.append(finding("high", "translation", f"Missing {lang} counterpart for {rel}", str(src.relative_to(root))))
    return findings


def check_exercises(root, config):
    findings = []
    ex = config.get("exercises", {})
    if not ex.get("enabled"):
        return findings
    exercises = root / ex.get("exercise_dir", "exercises")
    solutions = root / ex.get("solution_dir", "solutions")
    if not exercises.exists():
        return findings
    for src in exercises.rglob("*.md"):
        rel = src.relative_to(exercises)
        if not (solutions / rel).exists():
            findings.append(finding("high", "solution", f"Missing solution for exercise: {rel}", str(src.relative_to(root))))
    return findings



def check_publication(root, config):
    findings = []
    pub = config.get("publication", {})
    if not pub.get("enabled"):
        return findings

    metadata_path = root / pub.get("metadata_file", "publication.yml")
    if not metadata_path.exists():
        return [finding("high", "build", f"Publication metadata file is missing: {metadata_path.relative_to(root)}")]

    try:
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [finding("high", "build", f"Cannot parse publication metadata: {exc}", str(metadata_path.relative_to(root)))]

    for key in pub.get("required_metadata", []):
        value = metadata
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value in (None, "", []):
            findings.append(finding("high", "consistency", f"Required publication metadata is missing: {key}", str(metadata_path.relative_to(root))))

    isbns = metadata.get("isbn", {})
    if isinstance(isbns, dict):
        seen = {}
        for edition, raw in isbns.items():
            if not raw:
                continue
            digits = re.sub(r"[^0-9Xx]", "", str(raw))
            if len(digits) not in (10, 13):
                findings.append(finding("high", "consistency", f"ISBN for {edition} has invalid length", str(metadata_path.relative_to(root))))
            if digits in seen:
                findings.append(finding("high", "consistency", f"ISBN is reused by {seen[digits]} and {edition}", str(metadata_path.relative_to(root))))
            seen[digits] = edition

    for artifact in pub.get("required_artifacts", []):
        if not (root / artifact).exists():
            findings.append(finding("high", "build", f"Required publication artifact is missing: {artifact}"))
    return findings


def check_chapter_order(root, config):
    findings = []
    order = config.get("chapter_order", {})
    if not order.get("enabled"):
        return findings
    manifest = root / order.get("manifest", "chapters.yml")
    if not manifest.exists():
        return [finding("high", "consistency", f"Chapter manifest is missing: {manifest.relative_to(root)}")]
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [finding("high", "build", f"Cannot parse chapter manifest: {exc}", str(manifest.relative_to(root)))]
    chapters = data.get("chapters", data if isinstance(data, list) else [])
    seen = set()
    for item in chapters:
        path = item if isinstance(item, str) else item.get("file")
        if not path:
            findings.append(finding("high", "consistency", "Chapter manifest contains an entry without a file", str(manifest.relative_to(root))))
            continue
        if path in seen:
            findings.append(finding("high", "consistency", f"Duplicate chapter in manifest: {path}", str(manifest.relative_to(root))))
        seen.add(path)
        if not (root / path).exists():
            findings.append(finding("high", "reference", f"Chapter listed in manifest does not exist: {path}", str(manifest.relative_to(root))))
    return findings



def heading_levels(text):
    return [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+.+$", text, re.M)]


def code_fences(text):
    return [m.group(1) or "" for m in re.finditer(r"^```([^\s`]*)[^\n]*$", text, re.M)]


def check_structure_parity(root, config):
    findings = []
    parity = config.get("parity", {})
    if not parity.get("enabled") or not parity.get("structure", False):
        return findings
    dirs = parity.get("language_dirs", {})
    primary = config["project"]["primary_language"]
    base = root / dirs.get(primary, primary)
    if not base.exists():
        return findings
    for lang in config["project"].get("languages", []):
        if lang == primary:
            continue
        other = root / dirs.get(lang, lang)
        if not other.exists():
            continue
        for src in base.rglob("*.md"):
            rel = src.relative_to(base)
            dst = other / rel
            if not dst.exists():
                continue
            a = src.read_text(encoding="utf-8")
            b = dst.read_text(encoding="utf-8")
            if heading_levels(a) != heading_levels(b):
                findings.append(finding("medium", "translation", f"Heading structure differs between {primary} and {lang}: {rel}", str(src.relative_to(root))))
            if code_fences(a) != code_fences(b):
                findings.append(finding("medium", "translation", f"Code-block language structure differs between {primary} and {lang}: {rel}", str(src.relative_to(root))))
    return findings


def run_hooks(root, config):
    findings = []
    for hook in config.get("hooks", []):
        name, command = hook.get("name", "unnamed"), hook.get("command")
        if not command:
            continue
        result = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True)
        if result.returncode:
            findings.append(finding("high", "build", f"Hook failed: {name} (exit {result.returncode})"))
    return findings


def run(root: Path, config_path: Path, schema_path: Path):
    findings = []
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [finding("blocker", "build", f"Cannot parse QA configuration: {exc}", str(config_path))]

    config_schema = Path(__file__).resolve().parent / "schemas" / "config.schema.json"
    validate(config, load_schema(config_schema), "QA config")

    if config.get("qa_version") != 1:
        findings.append(finding("critical", "consistency", "Unsupported or missing qa_version", str(config_path)))
    project = config.get("project", {})
    if not project.get("primary_language"):
        findings.append(finding("high", "consistency", "project.primary_language is required", str(config_path)))
    if not project.get("languages"):
        findings.append(finding("high", "consistency", "project.languages must not be empty", str(config_path)))

    _, md = scan_markdown(root, config)
    findings += md
    if project.get("primary_language") and project.get("languages"):
        findings += check_language_parity(root, config)
    findings += check_exercises(root, config)
    findings += check_publication(root, config)
    findings += check_chapter_order(root, config)
    findings += check_structure_parity(root, config)
    findings += run_hooks(root, config)

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
    findings = run(root, (root / args.config).resolve(), (root / args.schema).resolve())
    counts = {s: 0 for s in ("blocker","critical","high","medium","low","info")}
    for item in findings:
        counts[item["severity"]] += 1
    loaded_config = yaml.safe_load((root / args.config).read_text(encoding="utf-8")) or {}
    source_paths = loaded_config.get("source", {}).get("paths", [])
    if source_paths:
        documents = build_review_documents(root, source_paths)
    else:
        documents = tuple(
            ReviewDocument(str(path.relative_to(root)), path.read_text(encoding="utf-8"))
            for path in markdown_files(root, [])
        )
    blocking = any(counts[s] for s in ("blocker","critical","high"))
    build_blocking = any(
        item["category"] == "build" and item["severity"] in ("blocker","critical","high")
        for item in findings
    )
    report = {
        "format_version": 1,
        "engine": "ploos-publishing-qa",
        "passed": not blocking,
        "build_passed": not build_blocking,
        "source_digest": source_digest(documents),
        "findings": findings,
        "summary": counts,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
