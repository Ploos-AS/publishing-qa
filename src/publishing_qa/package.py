from __future__ import annotations

import hashlib
from pathlib import Path

from .review import ReviewDocument


def build_review_documents(root: Path, paths: list[str], language: str | None = None):
    documents = []
    for item in paths:
        path = root / item
        candidates = sorted(path.rglob("*.md")) if path.is_dir() else [path]
        for source in candidates:
            if not source.is_file():
                continue
            documents.append(ReviewDocument(
                path=str(source.relative_to(root)),
                content=source.read_text(encoding="utf-8"),
                language=language,
            ))
    return tuple(documents)


def source_digest(documents: tuple[ReviewDocument, ...]) -> str:
    digest = hashlib.sha256()
    for doc in sorted(documents, key=lambda d: d.path):
        digest.update(doc.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(doc.content.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
