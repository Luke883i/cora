"""PR07 installed-artifact validation on two independent synthetic Git fixtures.

Not production-site validation. Wheel gets a fresh isolated venv; sdist gets a
separate venv exposing system build tooling so --no-build-isolation works offline.
"""
from __future__ import annotations
import argparse
import json
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*argv, cwd=None):
    p=subprocess.run(list(map(str,argv)),cwd=cwd,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},capture_output=True,text=True,timeout=120)
    if p.returncode:
        raise ValueError(f'command failed ({p.returncode}): {list(map(str,argv))}: {p.stderr[-1000:]}')
    return p.stdout


def git(repo, *args):return run('git','-C',repo,*args).strip()

def put(repo, name, content):
    file=repo/name;file.parent.mkdir(exist_ok=True,parents=True);file.write_text(content,encoding='utf-8')

def fixture_python(root):
    root.mkdir()
    git(root,'init','-q');git(root,'config','user.name','External Oracle');git(root,'config','user.email','external@invalid.example')
    put(root,'apps/alpha/main.py','import shared.util\n')
    put(root,'apps/beta/main.py','VALUE = 1\n')
    put(root,'src/shared/util.py','READY = True\n')
    put(root,'cora.ontology.json',json.dumps({'schema':'cora-ontology/1','products':[{'id':'alpha','roots':['apps/alpha'],'entrypoints':['apps/alpha/main.py']},{'id':'beta','roots':['apps/beta'],'entrypoints':['apps/beta/main.py']}],'software':[{'id':'shared','roots':['src/shared'],'product_ids':['alpha','beta']}]},sort_keys=True))
    git(root,'add','.');git(root,'commit','-qm','independent Python fixture')
    return git(root,'rev-parse','HEAD')

def fixture_polyglot(root):
    root.mkdir()
    git(root,'init','-q');git(root,'config','user.name','External Oracle');git(root,'config','user.email','external@invalid.example')
    put(root,'frontend/package.json','{"dependencies":{"react":"^19.0.0"},"workspaces":["packages/*"]}\n')
    put(root,'backend/go.mod','module example.com/probe\nrequire example.com/library v1.2.3\n')
    put(root,'infra/Dockerfile','FROM scratch\n')
    git(root,'add','.');git(root,'commit','-qm','independent polyglot fixture')
    return git(root,'rev-parse','HEAD')

def call_json(binpath, *args):return json.loads(run(binpath,*args))

def validate_one(binpath, home):
    fixtureA=home/'repo-python';commitA=fixture_python(fixtureA)
    fixtureB=home/'repo-polyglot';commitB=fixture_polyglot(fixtureB)
    if run(binpath,'version').strip()!='0.8.0a1':raise ValueError('incorrect installed version')
    ledger=call_json(binpath,'snapshot',fixtureA)
    if ledger['commit']!=commitA or len(ledger['records'])!=4:raise ValueError('Python committed Git snapshot oracle mismatch')
    graph=call_json(binpath,'graph',fixtureA)
    expected=('file:apps/alpha/main.py','file:src/shared/util.py','static_import_candidate')
    got={(e['source'],e['target'],e['kind']) for e in graph['edges']}
    if expected not in got:raise ValueError('Python static graph oracle mismatch')
    cert=call_json(binpath,'closure',fixtureA,'--claim','committed_blob','--path','src/shared/util.py')
    if cert['status']!='PASS_SCOPED':raise ValueError('Python certificate oracle mismatch')
    declared=call_json(binpath,'adapter-audit',fixtureB)
    if declared['commit']!=commitB:raise ValueError('Polyglot provenance mismatch')
    deps={(o['path'],d['name'],d['constraint']) for o in declared['observations'] for d in o['dependencies']}
    expected_deps={('frontend/package.json','react','^19.0.0'),('backend/go.mod','example.com/library','v1.2.3')}
    if deps!=expected_deps:raise ValueError('Polyglot declarations oracle mismatch')
    if declared['coverage']['runtime']!='unsupported':raise ValueError('Unsupported runtime claim elevated')
    node=next(o for o in declared['observations'] if o['path']=='frontend/package.json')
    if 'workspaces:unresolved' not in node['unknown']:raise ValueError('Workspace uncertainty missing')
    docker=next(o for o in declared['observations'] if o['path']=='infra/Dockerfile')
    if docker['status']!='unsupported':raise ValueError('Docker wrongly inferred as supported')
    return {'python_fixture':{'commit':commitA,'files':len(ledger['records']),'graph_oracle':'PASS','closure_oracle':'PASS'},
            'polyglot_fixture':{'commit':commitB,'declared_dependencies':len(deps),'unknown_workspaces':'PASS','unsupported_docker':'PASS'}}

def validate_artifacts(wheel:Path,sdist:Path,*,home:Path|None=None)->dict:
    import shutil
    with tempfile.TemporaryDirectory(prefix='cora-pr07-external-',dir=home) as t:
        base=Path(t)
        results={}
        for kind,artifact in [('wheel',wheel),('sdist',sdist)]:
            venv=base/('venv-'+kind)
            python=sys.executable
            command=[python,'-m','venv']
            if kind=='sdist':command.append('--system-site-packages')
            command.append(str(venv));run(*command)
            py=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            binpath=venv/('Scripts/cora.exe' if os.name=='nt' else 'bin/cora')
            if kind=='sdist':
                # Expose only the preinstalled builder toolchain to this venv for offline source builds.
                spec=importlib.util.find_spec('setuptools')
                if spec is None or spec.origin is None:raise ValueError('builder unavailable')
                backing=Path(spec.origin).parent.parent
                site=Path(run(py,'-c','import sysconfig; print(sysconfig.get_paths()["purelib"])').strip())
                (site/'cora-build-backend.pth').write_text(str(backing)+'\n')
            run(py,'-m','pip','install','--no-index','--no-deps','--no-build-isolation',str(artifact))
            # Run from unrelated empty directory: prevent implicit import of source checkout.
            installation=base/('source-independent-'+kind)
            installation.mkdir()
            results[kind]=validate_one(binpath,installation)
            origin=json.loads(run(py,'-c','import cora,json; print(json.dumps({"version":cora.__version__,"path":cora.__file__}))'))
            if origin['version']!='0.8.0a1' or not Path(origin['path']).is_relative_to(venv):
                raise ValueError('artifact installation unexpectedly imported from outside the venv')
            metadata=run(py,'-m','pip','show','cora-audit')
            if 'Version: 0.8.0a1' not in metadata:raise ValueError('install metadata mismatch')
        return {'schema':'cora-external-validation/1','status':'SCOPED_FIXTURES_PASS',
                'distribution_forms':results,'offline_index':'disabled','python':sys.version.split()[0],
                'limitations':['both independent repositories are pre-seeded synthetic Git fixtures, not external production projects',
                    'sdist venv explicitly exposes local preinstalled setuptools build backend for offline build; not hermetic',
                    'no external services, deployments or runtime use tested']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--wheel',required=True,type=Path);p.add_argument('--sdist',required=True,type=Path);p.add_argument('--output',type=Path)
    x=p.parse_args()
    result=json.dumps(validate_artifacts(x.wheel,x.sdist),sort_keys=True,indent=2)+'\n'
    if x.output:x.output.write_text(result)
    else:print(result,end='')
if __name__=='__main__':main()
