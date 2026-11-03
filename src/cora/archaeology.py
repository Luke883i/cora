"""Read-only, bounded Git archaeology for *development episodes*, not dead-code proof.

The time dimension is sourced from committed Git objects, never guessed from
current file names or from a model. PR associations require externally supplied
labels and remain explicitly unauthenticated until separately checked.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re
import subprocess

from .evidence import domain_hash, valid_path
from .git_snapshot import git

SCHEMA = 'cora-archaeology/1'
TOPIC = re.compile(r'^([a-z]{2,16})(?:\(([\w.-]{1,50})\))?:', re.ASCII)
SHA = re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')


def _decode_path(raw: bytes) -> str:
    try:
        path = raw.decode('utf-8', 'strict')
    except UnicodeDecodeError as exc:
        raise ValueError('Git history has a path not representable in UTF-8') from exc
    if not valid_path(path):
        raise ValueError('Git history has an unsafe path')
    return path


def _changes(repo: Path, sha: str, parent: str | None) -> list[dict]:
    if parent:
        data = git(repo, 'diff', '--no-ext-diff', '--find-renames=50%', '--name-status', '-z', parent, sha, '--', max_output=8*1024*1024)
    else:
        data = git(repo, 'diff-tree', '--root', '-r', '--no-commit-id', '--name-status', '-z', sha, '--', max_output=8*1024*1024)
    parts = data.split(b'\0')
    changes: list[dict] = []
    i = 0
    while i < len(parts) and parts[i]:
        token = parts[i].decode('ascii', 'strict'); i += 1
        if not token or token[0] not in ('A', 'M', 'D', 'R', 'C', 'T'):
            raise ValueError('unsupported Git history status '+token)
        if i >= len(parts) or not parts[i]:
            raise ValueError('malformed Git name-status record')
        old = _decode_path(parts[i]); i += 1
        new = old
        if token[0] in ('R', 'C'):
            if i >= len(parts) or not parts[i]:
                raise ValueError('truncated Git rename/copy')
            new = _decode_path(parts[i]); i += 1
        changes.append({'status': token, 'old': old, 'new': new})
        if len(changes) > 2048:
            raise ValueError('Git commit exceeds history diff path budget')
    return changes


def _pr_index(doc: dict | None) -> dict[str, str]:
    if doc is None:
        return {}
    if not isinstance(doc, dict) or set(doc) != {'schema', 'commits'} or doc['schema'] != 'cora-pr-index/1' or not isinstance(doc['commits'], dict) or len(doc['commits']) > 20000:
        raise ValueError('PR index schema invalid')
    result: dict[str, str] = {}
    for sha, pr in doc['commits'].items():
        if not isinstance(sha,str) or not SHA.fullmatch(sha) or type(pr) is not int or not 1 <= pr <= 1_000_000:
            raise ValueError('invalid untrusted PR association')
        result[sha] = f'PR-{pr}'
    return result


def mine_history(repo: Path, revision: str = 'HEAD', *, max_commits: int = 256, pr_index: dict | None = None) -> dict:
    """Mine commit provenance and change coupling without checkout or target execution."""
    repo = Path(repo).resolve(strict=True)
    if type(max_commits) is not int or not 1 <= max_commits <= 1000:
        raise ValueError('max_commits outside bounded range')
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', revision+'^{commit}').decode('ascii').strip()
    rows = git(repo, 'rev-list', '--topo-order', '--parents', '--max-count='+str(max_commits+1), commit, max_output=512*1024).decode('ascii').splitlines()
    truncated = len(rows) > max_commits
    index = _pr_index(pr_index)
    events = []
    by_path: dict[str,list[str]] = defaultdict(list)
    pair_count: Counter[tuple[str,str]] = Counter()
    pair_skipped = 0
    for row in rows[:max_commits]:
        chunks = row.split()
        sha = chunks[0]
        parent = chunks[1] if len(chunks)>1 else None
        message = git(repo, 'show', '-s', '--format=%s', sha, max_output=16*1024).decode('utf-8', 'replace').strip()[:250]
        match = TOPIC.match(message)
        topic = match.group(1) if match else 'unclassified'
        scope = match.group(2) if match else None
        changes = _changes(repo, sha, parent)
        current_paths = sorted({item['new'] for item in changes if item['status'][0] != 'D'})
        for item in changes:
            by_path[item['new']].append(sha)
            if item['old'] != item['new']:
                by_path[item['old']].append(sha)
        if len(current_paths) <= 64 and len(chunks) <= 2:
            for i,a in enumerate(current_paths):
                for b in current_paths[i+1:]:
                    pair_count[(a,b)] += 1
        elif len(current_paths) > 64:
            pair_skipped += 1
        events.append({'commit':sha,'first_parent':parent,'merge':len(chunks)>2,
                       'message':message,'conventional_kind':topic,'conventional_scope':scope,
                       'pr_association':index.get(sha),'pr_association_source':'operator_supplied_unverified' if sha in index else 'not_available',
                       'changes':changes})
    evidence = {'schema':SCHEMA,'commit':commit,'bounded_commits':max_commits,
                'history_truncated':truncated,'events':events,
                'cochange_pairs':[{'a':a,'b':b,'count':n} for (a,b),n in sorted(pair_count.items()) if n >= 2],
                'touched_commits':{k:sorted(set(v)) for k,v in sorted(by_path.items())},
                'excluded_large_atomic_changes':pair_skipped,
                'coverage':{
                  'git_history':'bounded_committed_first_parent_diff_per_commit',
                  'merge_commits':'recorded_but_not_counted_for_cochange',
                  'copy_rename':'Git_similarity_heuristic_not_symbol_equivalence',
                  'pr_identity':'operator_provided_unverified_or_unknown',
                  'all_refs':'not_analyzed',
                  'squashed_changes':'not_recoverable_without_external_PR_data',
                  'runtime_and_external_consumers':'unsupported'
                }}
    evidence['digest'] = domain_hash('CORA:archaeology:1', evidence)
    return evidence


def verify_history(repo:Path, report:dict) -> bool:
    if not isinstance(report,dict) or report.get('schema') != SCHEMA:
        raise ValueError('invalid archaeology report')
    supplied = {e['commit']: int(e['pr_association'][3:]) for e in report.get('events',[])
                if isinstance(e.get('pr_association'),str) and e['pr_association'].startswith('PR-')}
    pr = {'schema':'cora-pr-index/1','commits':supplied} if supplied else None
    expected = mine_history(repo, report['commit'], max_commits=report['bounded_commits'], pr_index=pr)
    if expected != report:
        raise ValueError('archaeology history differs from original Git objects')
    return True
