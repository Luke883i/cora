#!/usr/bin/env node
// Static original-Git ESM imports only. NEVER link, evaluate, or run target source.
import {SourceTextModule} from 'node:vm';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
const [repo,revision='HEAD',action,file]=process.argv.slice(2);
const git=(...args)=>execFileSync('git',['-C',repo,...args],{encoding:'utf8',maxBuffer:34000000,timeout:120000});
const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
function report(){
  if(!repo || revision.startsWith('-') || revision.includes('\0'))throw Error('unsafe arguments');
  const commit=git('rev-parse','--verify','--end-of-options',revision+'^{commit}').trim();
  if(!/^[0-9a-f]{40}$/.test(commit))throw Error('invalid Git revision');
  const files=git('ls-tree','-r','--name-only','-z',commit)
    .split('\0').filter(p=>/\.(mjs|js)$/i.test(p)).sort();
  if(files.length>4096)throw Error('too many files');
  let bytes=0;const imports=[],unknown=[],syntaxErrors=[];
  for(const path of files){
    const text=git('show',commit+':'+path);bytes+=Buffer.byteLength(text);
    if(Buffer.byteLength(text)>1048576 || bytes>33554432)throw Error('source bound');
    try{
      const mod=new SourceTextModule(text,{identifier:path});
      for(const specifier of mod.dependencySpecifiers)
        imports.push({path,specifier,scope:'STATIC_ESM_CANDIDATE'});
    }catch(e){syntaxErrors.push({path,reason:'UNPARSEABLE_ESM_SOURCE'});}
    if(/\bimport\s*\(/.test(text))unknown.push({path,kind:'DYNAMIC_IMPORT_CANDIDATE'});
    if(/\brequire\s*\(/.test(text))unknown.push({path,kind:'COMMONJS_REQUIRE_CANDIDATE'});
  }
  const x={schema:'cora-js-static-source/1',commit,files:files.length,bytes,imports,unknown,syntaxErrors,
    scope:'PARSED_ESM_ONLY_DYNAMIC_AND_RUNTIME_UNKNOWN',authority:'NONE',runtimeObserved:false};
  x.digest=digest(x);return x;
}
try{
  const r=report();
  if(action==='--verify'){
    const before=JSON.parse(readFileSync(file,'utf8'));
    if(JSON.stringify(before)!==JSON.stringify(r))throw Error('tampered/stale JS report');
  }else if(action==='--output'){writeFileSync(file,JSON.stringify(r,null,2)+'\n');}
  else if(action)throw Error('unexpected option');
  process.stdout.write(JSON.stringify(r)+'\n');
  // Preserve a replayable partial dossier; the Python caller marks it
  // DEBT_BLOCKED, never a complete source analysis or runtime PASS.
  // Refuse only fatal parser/process errors above.
}catch(e){process.stderr.write('CORA_JS_BLOCKED: '+String(e.message).slice(0,240)+'\n');process.exitCode=2;}
