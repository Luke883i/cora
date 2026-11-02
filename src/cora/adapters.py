"""Versioned bounded manifest adapters; declared dependencies do not imply runtime use."""
from __future__ import annotations
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from .evidence import domain_hash, validate_ledger
from .git_snapshot import snapshot, git

ADAPTER_SCHEMA = 'cora-adapter-report/1'
VERSION = '0.4.0a1'
MAX_MANIFEST = 512 * 1024
SUPPORTED = {
    'package.json': ('node-package-json', '1'),
    'pyproject.toml': ('python-pyproject', '1'),
    'requirements.txt': ('python-requirements', '1'),
    'Cargo.toml': ('rust-cargo', '1'),
    'go.mod': ('go-mod', '1'),
    'pom.xml': ('maven-pom', '1'),
}
DECLARATIVE_UNKNOWN = {
    'Dockerfile':'docker-runtime-build-unknown',
    'docker-compose.yml':'compose-runtime-unknown',
    'compose.yaml':'compose-runtime-unknown',
    'build.gradle':'gradle-dependency-unknown',
    'build.gradle.kts':'gradle-dependency-unknown',
}

@dataclass(frozen=True)
class Result:
    dependencies: tuple[tuple[str,str,str], ...]
    unknown: tuple[str, ...]

def _spec(name: str) -> str:
    if not isinstance(name,str) or not name.strip():
        raise ValueError('dependency name invalid')
    return name.strip()

def parse_manifest(name: str, raw: bytes) -> Result:
    """Bounded partial extraction, keeping indirect or unsupported semantics unknown."""
    if len(raw)>MAX_MANIFEST: raise ValueError('manifest size limit exceeded')
    try:
        txt=raw.decode('utf-8')
        deps:set[tuple[str,str,str]]=set()
        unknown:set[str]=set()
        if name=='package.json':
            doc=json.loads(txt)
            if not isinstance(doc,dict): raise ValueError('package JSON root is not object')
            for field in ('dependencies','devDependencies','optionalDependencies','peerDependencies'):
                obj=doc.get(field,{})
                if not isinstance(obj,dict):
                    unknown.add(field+':invalid-shape');continue
                for key,val in obj.items():
                    if isinstance(key,str) and isinstance(val,str): deps.add((key,val,field))
                    else: unknown.add(field+':nonstring-entry')
            if doc.get('workspaces') is not None: unknown.add('workspaces:unresolved')
            if doc.get('scripts') is not None: unknown.add('scripts:not-executed')
            if doc.get('imports') is not None or doc.get('exports') is not None:
                unknown.add('module-resolution:unresolved')
        elif name=='pyproject.toml':
            doc=tomllib.loads(txt)
            project=doc.get('project',{})
            if not isinstance(project,dict): raise ValueError('project must be table')
            for value in project.get('dependencies',[]):
                if isinstance(value,str):
                    deps.add((_spec(re.split(r'[<>=!~;\[\] ]',value,maxsplit=1)[0]),value,'project.dependencies'))
                else: unknown.add('python-dependency:nonstring')
            for group,values in project.get('optional-dependencies',{}).items():
                if isinstance(values,list):
                    for value in values:
                        if isinstance(value,str):
                            deps.add((_spec(re.split(r'[<>=!~;\[\] ]',value,maxsplit=1)[0]),value,'optional:'+group))
                        else: unknown.add('optional-dependency:nonstring')
                else: unknown.add('optional-dependencies:invalid-shape')
            if doc.get('build-system'): unknown.add('build-backend:execution-not-observed')
            if doc.get('tool'): unknown.add('tool-specific-configuration:not-modeled')
        elif name=='requirements.txt':
            for line in txt.splitlines():
                line=line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith(('-','.','git+','http:','https:')):
                    unknown.add('pip-directive-or-url:unresolved');continue
                dep=re.split(r'[<>=!~;\[\] ]',line,maxsplit=1)[0]
                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',dep):
                    deps.add((dep,line,'requirements'))
                else: unknown.add('pip-requirement:unparsed')
        elif name=='Cargo.toml':
            doc=tomllib.loads(txt)
            for group in ('dependencies','dev-dependencies','build-dependencies'):
                for key,value in doc.get(group,{}).items():
                    if isinstance(value,str): deps.add((key,value,group))
                    elif isinstance(value,dict):
                        if isinstance(value.get('version'),str):
                            deps.add((key,value['version'],group))
                        else: unknown.add(group+':nonregistry-dependency:'+key)
                        if any(k in value for k in ('path','git','branch','rev')):
                            unknown.add(group+':source-resolution:'+key)
                    else: unknown.add(group+':unexpected-type:'+key)
            if doc.get('workspace'): unknown.add('workspace:unresolved')
            if doc.get('target'): unknown.add('conditional-target:unresolved')
        elif name=='go.mod':
            in_block=False
            for line in txt.splitlines():
                line=line.split('//',1)[0].strip()
                if line=='require (': in_block=True;continue
                if in_block and line==')': in_block=False;continue
                if line.startswith(('replace ','exclude ','retract ','toolchain ')):
                    unknown.add('go-directive:unresolved');continue
                spec=(line[8:].strip() if line.startswith('require ') else line if in_block else '')
                if spec:
                    parts=spec.split()
                    if len(parts)==2: deps.add((parts[0],parts[1],'require'))
                    else: unknown.add('go-require:unparsed')
        elif name=='pom.xml':
            if '<!DOCTYPE' in txt.upper() or '<!ENTITY' in txt.upper():
                raise ValueError('DTD/entity unsupported')
            root=ET.fromstring(txt)
            for d in root.findall('.//{*}dependencies/{*}dependency'):
                artifact=d.findtext('{*}artifactId')
                group=d.findtext('{*}groupId')
                version=d.findtext('{*}version')
                if artifact and group:
                    if version and ('$'+'{') not in version:
                        deps.add((group+':'+artifact,version,'maven'))
                    else: unknown.add('maven-property-or-missing-version:'+group+':'+artifact)
                else: unknown.add('maven-incomplete-dependency')
            if root.findall('.//{*}profiles'):
                unknown.add('maven-profiles:unresolved')
        else: raise ValueError('unsupported parser: '+name)
        return Result(tuple(sorted(deps)),tuple(sorted(unknown)))
    except (UnicodeDecodeError,json.JSONDecodeError,tomllib.TOMLDecodeError,ET.ParseError,TypeError,KeyError,AttributeError) as exc:
        raise ValueError('malformed manifest '+name) from exc

def kind_for_path(path:str)->tuple[str,str]:
    name=path.rsplit('/',1)[-1]
    if name in SUPPORTED: return SUPPORTED[name][0],'supported_partial'
    if name in DECLARATIVE_UNKNOWN or path.startswith('.github/workflows/') and name.endswith(('.yml','.yaml')):
        return DECLARATIVE_UNKNOWN.get(name,'github-actions-unknown'),'unsupported'
    if name.endswith('.csproj'): return 'dotnet-csproj-unknown','unsupported'
    return 'unrecognized','not_applicable'

def adapter_audit(repo:Path,revision:str='HEAD')->dict:
    ledger=snapshot(repo,revision)
    validate_ledger(ledger)
    commit=ledger['commit']
    observations=[]
    for rec in ledger['records']:
        adapter,coverage=kind_for_path(rec['path'])
        if coverage=='not_applicable': continue
        deps:list[dict]=[]
        unknown:list[str]=[]
        status='partial' if coverage=='supported_partial' else 'unsupported'
        if rec['status']!='observed_git_blob':
            status='unresolved';unknown.append('git-object:'+rec['status'])
        elif coverage=='unsupported':
            unknown.append('adapter-not-implemented')
        elif rec['size'] is None or rec['size']>MAX_MANIFEST:
            status='unresolved';unknown.append('manifest-size-exceeded')
        else:
            raw=git(repo,'cat-file','blob',rec['git_oid'],max_output=MAX_MANIFEST+1)
            try:
                result=parse_manifest(rec['path'].rsplit('/',1)[-1],raw)
                deps=[{'name':n,'constraint':v,'source_field':f,'claim':'declared_only'} for n,v,f in result.dependencies]
                unknown.extend(result.unknown)
            except ValueError:
                status='unresolved';unknown.append('manifest-parse-error')
        observations.append({'path':rec['path'],'adapter':adapter,'adapter_version':'1','status':status,
            'source_record_digest':rec['digest'],'dependencies':deps,'unknown':sorted(set(unknown))})
    report={'schema':ADAPTER_SCHEMA,'commit':commit,'ledger_digest':ledger['ledger_digest'],
        'observations':sorted(observations,key=lambda o:o['path']),
        'coverage':{'manifest_declarations':'bounded_partial','runtime':'unsupported','resolved_dependency_graph':'unsupported',
                    'external_consumers':'unsupported','workflow_execution':'unsupported','nonselected_formats':'not_analyzed'},
        'adapter_catalog':[{'name':v[0],'version':v[1],'pattern':k,'claims':['declared_dependency_only']} for k,v in sorted(SUPPORTED.items())]}
    report['report_digest']=domain_hash('CORA:adapter-report:1',report)
    return report

def verify_adapter_report(repo:Path,report:dict)->bool:
    if not isinstance(report,dict) or report.get('schema')!=ADAPTER_SCHEMA:
        raise ValueError('invalid adapter report')
    if report.get('report_digest')!=domain_hash('CORA:adapter-report:1',{k:v for k,v in report.items() if k!='report_digest'}):
        raise ValueError('adapter digest mismatch')
    if adapter_audit(repo,report['commit'])!=report:
        raise ValueError('report does not match committed Git evidence')
    return True
