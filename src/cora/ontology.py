"""Explicit, immutable-source ontology declarations; names never imply product identity."""
from __future__ import annotations
import json
from .evidence import valid_path, domain_hash
from .git_snapshot import git


def validate_ontology(doc: object) -> dict:
    if not isinstance(doc, dict) or set(doc) != {'schema', 'products', 'software'} or doc.get('schema') != 'cora-ontology/1':
        raise ValueError('ontology schema mismatch')
    if not isinstance(doc['products'], list) or not isinstance(doc['software'], list):
        raise ValueError('ontology arrays required')
    for category in ('products', 'software'):
        seen: set[str] = set()
        for obj in doc[category]:
            fields = {'id', 'roots', 'entrypoints'} if category == 'products' else {'id', 'roots', 'product_ids'}
            if not isinstance(obj, dict) or set(obj) != fields:
                raise ValueError('ontology object shape mismatch')
            name = obj['id']
            if not isinstance(name, str) or not name or not all(c.isascii() and (c.isalnum() or c in '_-.') for c in name) or name in seen:
                raise ValueError('invalid or duplicate ontology identity')
            seen.add(name)
            roots = obj['roots']
            if not isinstance(roots, list) or not roots or any(not valid_path(p) for p in roots) or len(set(roots)) != len(roots):
                raise ValueError('invalid ontology roots')
            if category == 'products':
                e = obj['entrypoints']
                if not isinstance(e, list) or any(not valid_path(p) for p in e) or len(e) != len(set(e)):
                    raise ValueError('invalid entrypoints')
            else:
                refs = obj['product_ids']
                if not isinstance(refs, list) or not refs or any(not isinstance(x, str) for x in refs) or len(refs) != len(set(refs)):
                    raise ValueError('invalid software product references')
    names = {p['id'] for p in doc['products']}
    if any(ref not in names for s in doc['software'] for ref in s['product_ids']):
        raise ValueError('software references missing product')
    return doc


def committed_ontology(repo, commit: str, path: str = 'cora.ontology.json') -> dict:
    if not valid_path(path):
        raise ValueError('invalid ontology path')
    payload = git(repo, 'show', f'{commit}:{path}', max_output=1024*1024)
    doc = json.loads(payload.decode('utf-8'))
    validate_ontology(doc)
    return {'document': doc, 'digest': domain_hash('CORA:ontology:1', doc), 'source': f'{commit}:{path}'}


def members(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(root + '/') for root in roots)
