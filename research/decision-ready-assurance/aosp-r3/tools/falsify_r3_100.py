#!/usr/bin/env python3
"""100 physical, disposable Word XML editorial mutants with explicit independent oracle.
This is source-bounded falsification, NOT real software execution, AI vision or human review.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"ENGLISH_AGNOSTIC_VISUAL_METHOD_R3.docx"
SPEC=ROOT/"MUTATION_CATALOG_R3_100.json"
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def xml_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        d=ET.fromstring(z.read("word/document.xml"))
    return "\n".join("".join((t.text or "") for t in p.iter(W+"t")) for p in d.iter(W+"p"))

def replace_in_docx(data: bytes, anchor: str, replacement: str) -> bytes:
    out=io.BytesIO()
    hit=0
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out,"w") as dst:
        for info in src.infolist():
            content=src.read(info.filename)
            if info.filename=="word/document.xml":
                root=ET.fromstring(content)
                for node in root.iter(W+"t"):
                    if node.text and anchor in node.text:
                        node.text=node.text.replace(anchor,replacement,1)
                        hit+=1
                content=ET.tostring(root,encoding="utf-8",xml_declaration=True)
            dst.writestr(info,content)
    if hit!=1:
        raise ValueError(f"ambiguous or missing source anchor {anchor!r}: {hit}")
    return out.getvalue()

def oracle(text: str, families: list[dict]) -> list[str]:
    errors=[]
    for f in families:
        if f["anchor"] not in text:
            errors.append(f["id"]+":REMOVED_REQUIRED_CLAIM")
        if any(bad.casefold() in text.casefold() for bad in f["mutations"]):
            errors.append(f["id"]+":FALSE_EPISTEMIC_PROMOTION")
    return errors

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--archive",type=Path)
    args=p.parse_args()
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    families=spec["families"]
    original=SOURCE.read_bytes()
    if spec["schema"]!="cora-r3-editorial-physical-100/1" or len(families)!=20:
        raise SystemExit("wrong finite model")
    if git_blob(original)!=spec["expected_git_blob_sha"]:
        raise SystemExit("wrong exact source blob")
    if hashlib.sha256(original).hexdigest()!=spec["expected_sha256"]:
        raise SystemExit("wrong exact source SHA256")
    expected=set(f["id"] for f in families)
    if len(expected)!=20 or any(len(f["mutations"])!=5 for f in families):
        raise SystemExit("wrong family cardinality")
    if oracle(xml_text(original),families):
        raise SystemExit("baseline violates editorial model")
    results=[]
    z=zipfile.ZipFile(args.archive,"w",compression=zipfile.ZIP_DEFLATED) if args.archive else None
    try:
        with tempfile.TemporaryDirectory() as temp:
            for f in families:
                for bad in f["mutations"]:
                    idx=len(results)+1
                    id_="M"+str(idx).zfill(3)
                    sample=replace_in_docx(original,f["anchor"],bad)
                    physical=Path(temp)/(id_+".docx")
                    physical.write_bytes(sample)
                    reread=physical.read_bytes()
                    issues=oracle(xml_text(reread),families)
                    results.append({"id":id_,"family":f["id"],
                       "verdict":"KILLED" if any(x.startswith(f["id"]+":") for x in issues) else "SURVIVED",
                       "git_blob_sha":git_blob(reread),
                       "sha256":hashlib.sha256(reread).hexdigest(),
                       "oracle_codes":issues})
                    if z:z.writestr("mutants/"+id_+".docx",reread)
        benign=[]
        for i in range(10):
            o=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(original)) as src,zipfile.ZipFile(o,"w") as dst:
                for item in src.infolist():
                    data=src.read(item.filename)
                    if item.filename=="docProps/core.xml":
                        data=data.replace(b"</dc:description>",f" (benign {i})".encode()+b"</dc:description>")
                    dst.writestr(item,data)
            ok=not oracle(xml_text(o.getvalue()),families)
            benign.append(ok)
            if z:z.writestr("controls/B"+str(i).zfill(2)+".docx",o.getvalue())
        if z:z.writestr("manifest.json",json.dumps({"mutants":results,"benign":benign},indent=2))
    finally:
        if z:z.close()
    success=sum(r["verdict"]=="KILLED" for r in results)
    ids=len({r["git_blob_sha"] for r in results})
    report={
       "schema":"cora-r3-physical-word-mutation/1","scope":"AUTHOR_SCOPED_EDITORIAL",
       "baseline_git_blob":git_blob(original),"baseline_sha256":hashlib.sha256(original).hexdigest(),
       "mutants":len(results),"families":len(families),"detected":success,
       "distinct_mutated_git_blobs":ids,
       "survivors":[r["id"] for r in results if r["verdict"]!="KILLED"],
       "benign_controls":10,"benign_accepted":sum(benign),
       "external_human_test":"NOT_DONE","runtime_product_test":"NOT_DONE",
       "results":results}
    if args.output:
        args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
    return 0 if len(results)==100 and success==100 and ids==100 and sum(benign)==10 else 1

if __name__=="__main__":
    sys.exit(main())
