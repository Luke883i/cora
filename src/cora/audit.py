"""Read-only filesystem inventory and declared product boundary audit.

A current working-tree snapshot, NOT a historical Git commit or runtime closure.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

EXCLUDE = frozenset({".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", "dist", "build", ".cora"})


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def owner_of(path: str, roots: dict[str, str]) -> list[str]:
    """Match path components, not substring prefixes."""
    return sorted(name for name, root in roots.items() if path == root or path.startswith(root + "/"))


def audit(repo: Path, declarations: dict | None = None) -> dict:
    repo = repo.resolve(strict=True)
    if not repo.is_dir():
        raise ValueError("repository is not a directory")
    declarations = declarations or {"products": []}
    products = declarations.get("products", [])
    if not isinstance(products, list):
        raise ValueError("products must be a list")
    roots: dict[str, str] = {}
    entrypoints: list[tuple[str, str]] = []
    errors: list[dict[str, str]] = []
    for p in products:
        name, root = p["id"], str(p["root"]).strip("/")
        if not name or name in roots or not root or any(x in (".", "..") for x in root.split("/")) or "\\" in root:
            raise ValueError("invalid or duplicate product declaration")
        roots[name] = root
        for e in p.get("entrypoints", []):
            if not isinstance(e, str) or e.startswith("/") or "\\" in e or ".." in e.split("/"):
                raise ValueError("unsafe entrypoint")
            entrypoints.append((name, e))
    files: list[dict] = []
    def visit(d: Path) -> None:
        for p in sorted(d.iterdir(), key=lambda item: item.name):
            rel = p.relative_to(repo).as_posix()
            if p.is_symlink():
                errors.append({"type": "unresolved_symlink", "path": rel})
            elif p.is_dir():
                if p.name not in EXCLUDE:
                    visit(p)
            elif p.is_file():
                content_hash = hashlib.sha256(p.read_bytes()).hexdigest()
                files.append({"path": rel, "sha256": content_hash, "products": owner_of(rel, roots)})
    visit(repo)
    paths = {f["path"] for f in files}
    for i, (name, root) in enumerate(sorted(roots.items())):
        for other, other_root in sorted(roots.items())[i + 1:]:
            if root == other_root or root.startswith(other_root + "/") or other_root.startswith(root + "/"):
                errors.append({"type": "overlapping_product_roots", "path": f"{name}:{other}"})
    seen: set[str] = set()
    for name, e in entrypoints:
        if e in seen:
            errors.append({"type": "duplicate_entrypoint", "path": e})
        seen.add(e)
        if e not in paths:
            errors.append({"type": "missing_entrypoint", "path": e})
        if name not in owner_of(e, roots):
            errors.append({"type": "entrypoint_outside_product", "path": e})
    files.sort(key=lambda f: f["path"])
    errors.sort(key=lambda e: (e["type"], e["path"]))
    payload = {"schema": "cora-pr01-inventory/1", "scope": "working-tree-read-only", "products": [{"id": k, "root": v} for k,v in sorted(roots.items())], "files": files, "findings": errors, "coverage": {"filesystem": "observed", "runtime": "unsupported", "dynamic_imports": "unsupported", "external_consumers": "unsupported", "historical_git": "unsupported"}}
    payload["digest_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    return payload


def read_declarations(repo: Path, path: str) -> dict:
    target = (repo / path).resolve()
    if not target.is_relative_to(repo.resolve()):
        raise ValueError("declaration path escapes repository")
    if not target.exists():
        return {"products": []}
    return json.loads(target.read_text(encoding="utf-8"))
