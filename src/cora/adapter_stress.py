"""Pre-seeded multi-ecosystem manifest mutations with external expected-result tuples.

Twenty-four curated families, one million DISTINCT serialized inputs when seed=883;
not one million independent repositories or runtime traces.
"""
from __future__ import annotations
import hashlib
from .mutations import mix64, MASK
from .adapters import parse_manifest

FORMATS = ('package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod', 'pom.xml', 'requirements.txt')
VARIANTS = ('runtime', 'optional', 'unresolved', 'malformed')
FAMILIES = tuple(f'{fmt}:{variant}' for fmt in FORMATS for variant in VARIANTS)


def fixture(case: int, salt: int) -> tuple[str, bytes, set[tuple[str,str,str]], bool, bool]:
    """Produce raw source and an expected result authored independently of the parser.

    Returns name, raw bytes, dependency tuple set, expects_unknown, expects_parse_failure.
    """
    fmt,variant = FAMILIES[case % len(FAMILIES)].rsplit(':',1)
    # A unique, legal package name for each case; varied versions and paths too.
    n = f'pkg_{case:07x}'
    v = f'{1 + salt % 9}.{salt >> 9 & 31}.{salt >> 19 & 31}'
    dep = set()
    unknown = variant == 'unresolved'
    bad = variant == 'malformed'
    if fmt == 'package.json':
        if variant == 'runtime':
            raw = f'{{"dependencies":{{"{n}":"^{v}"}}}}';dep.add((n,'^'+v,'dependencies'))
        elif variant == 'optional':
            raw = f'{{"devDependencies":{{"{n}":"~{v}"}}}}';dep.add((n,'~'+v,'devDependencies'))
        elif variant == 'unresolved':
            raw = f'{{"dependencies":{{"{n}":"{v}"}},"workspaces":["packages/*"]}}';dep.add((n,v,'dependencies'))
        else: raw = '{"dependencies":' + n
    elif fmt == 'pyproject.toml':
        if variant == 'runtime':
            raw = f'[project]\nname="demo"\ndependencies=["{n}>={v}"]\n';dep.add((n,f'{n}>={v}','project.dependencies'))
        elif variant == 'optional':
            raw = f'[project.optional-dependencies]\ntest=["{n}=={v}"]\n';dep.add((n,f'{n}=={v}','optional:test'))
        elif variant == 'unresolved':
            raw = f'[project]\ndependencies=["{n}=={v}"]\n[build-system]\nrequires=["setuptools"]\n';dep.add((n,f'{n}=={v}','project.dependencies'))
        else: raw = f'[project\nname="{n}"'
    elif fmt == 'Cargo.toml':
        if variant == 'runtime':
            raw = f'[dependencies]\n{n}="{v}"\n';dep.add((n,v,'dependencies'))
        elif variant == 'optional':
            raw = f'[dev-dependencies]\n{n}="{v}"\n';dep.add((n,v,'dev-dependencies'))
        elif variant == 'unresolved':
            raw = f'[dependencies]\n{n}={{version="{v}",path="../{n}"}}\n';dep.add((n,v,'dependencies'))
        else: raw = f'[dependencies]\n{n}="unterminated'
    elif fmt == 'go.mod':
        if variant == 'runtime':
            raw = f'module example.com/demo\nrequire example.com/{n} v{v}\n';dep.add((f'example.com/{n}',f'v{v}','require'))
        elif variant == 'optional':
            raw = f'module example.com/demo\nrequire (\n example.com/{n} v{v}\n)\n';dep.add((f'example.com/{n}',f'v{v}','require'))
        elif variant == 'unresolved':
            raw = f'module example.com/demo\nrequire example.com/{n} v{v}\nreplace example.com/old => example.com/{n}\n';dep.add((f'example.com/{n}',f'v{v}','require'))
        else:
            # Go syntax is not fully parsed: incomplete require => explicitly unknown, NOT false parse success.
            raw = f'module example.com/demo\nrequire example.com/{n}\n';unknown = True;bad=False
    elif fmt == 'pom.xml':
        if variant == 'runtime':
            raw = f'<project><dependencies><dependency><groupId>org.demo</groupId><artifactId>{n}</artifactId><version>{v}</version></dependency></dependencies></project>';dep.add((f'org.demo:{n}',v,'maven'))
        elif variant == 'optional':
            raw = f'<project><dependencies><dependency><groupId>org.demo</groupId><artifactId>{n}</artifactId><version>{v}</version></dependency></dependencies></project>';dep.add((f'org.demo:{n}',v,'maven'))
        elif variant == 'unresolved':
            raw = f'<project><dependencies><dependency><groupId>org.demo</groupId><artifactId>{n}</artifactId><version>${{version}}</version></dependency></dependencies></project>'
        else: raw = f'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///tmp/{n}">]><project>&x;</project>'
    else:
        if variant == 'runtime':
            raw = f'{n}=={v}\n';dep.add((n,f'{n}=={v}','requirements'))
        elif variant == 'optional':
            raw = f'# optional for testing\n{n}>={v}\n';dep.add((n,f'{n}>={v}','requirements'))
        elif variant == 'unresolved':
            raw = f'{n}=={v}\n-r other_{n}.txt\n';dep.add((n,f'{n}=={v}','requirements'))
        else:
            raw = f'--index-url https://example.invalid/{n}\n';unknown=True;bad=False
    return fmt,raw.encode(),dep,unknown,bad


def stress_adapters(*, seed:int=883, cases:int=1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=10_000_000:
        raise ValueError('seed integer and cases in 1..10_000_000 required')
    stream = hashlib.sha256()
    unique = set()
    mismatches=0
    status_counts={'parsed':0,'unresolved':0,'malformed':0}
    distribution={k:0 for k in FAMILIES}
    for i in range(cases):
        salt=mix64((i ^ seed) & MASK)
        family=FAMILIES[salt % len(FAMILIES)]
        fmt,raw,expected,expect_unknown,expect_bad=fixture(salt % len(FAMILIES),salt)
        # Ensure byte-distinct per case, including repeated family and malformed inputs.
        # Manifest suffix is a legitimate comment in each supported syntax except JSON/XML;
        # for those, embed a varying legal dependency identifier for normal variants.
        # We use a numeric per-case package name by overriding the fixture's package token.
        original = f'pkg_{(salt % len(FAMILIES)):07x}'
        replacement = f'pkg_{i:07x}'
        raw = raw.replace(original.encode(), replacement.encode())
        expected={(a.replace(original,replacement),b.replace(original,replacement),c) for a,b,c in expected}
        if not raw.endswith(b'\n') and fmt in ('pyproject.toml','Cargo.toml','go.mod','requirements.txt'):
            raw += b'\n'
        h=hashlib.blake2b(raw,digest_size=16).digest()
        unique.add(h)
        stream.update(i.to_bytes(8,'big')+h)
        try:
            output=parse_manifest(fmt,raw)
            parsed=True
        except ValueError:
            parsed=False
            output=None
        if parsed==expect_bad or (parsed and (set(output.dependencies)!=expected or bool(output.unknown)!=expect_unknown)):
            mismatches+=1
        status_counts['malformed' if not parsed else 'unresolved' if output.unknown else 'parsed']+=1
        distribution[family]+=1
    return {'schema':'cora-adapter-stress/1','cases':cases,'seed':seed,'families':len(FAMILIES),
            'mismatches':mismatches,'distinct_input_fingerprints':len(unique),
            'fingerprint':'blake2b-128','stream_sha256':stream.hexdigest(),
            'distribution':distribution,'outcomes':status_counts,
            'limits':['Synthetic manifest mutations, not physical Git repositories or real dependency executions',
                      'Oracles come from fixture templates, not independent production truth',
                      'Distinctness is of serialized fixture inputs, not of deployment topologies']}
