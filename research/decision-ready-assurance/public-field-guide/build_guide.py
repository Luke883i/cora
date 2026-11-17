from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_LINE_SPACING
from pathlib import Path
import json, re, hashlib

WORK = Path(__file__).resolve().parent
ATLAS=WORK/'Original_Source_Register_149.json'
OUT=WORK/'From_Intent_to_Evidence.docx'
NAVY=RGBColor(24,44,66)
INK=RGBColor(38,50,62)
GRAY=RGBColor(92,103,111)
TEAL=RGBColor(0,109,111)
LIGHT=RGBColor(222,229,231)

D=Document()
sec=D.sections[0]
sec.page_height,sec.page_width= Inches(11.69), Inches(8.27)
sec.top_margin=Inches(.66);sec.bottom_margin=Inches(.61)
sec.left_margin=Inches(.85);sec.right_margin=Inches(.85)
sec.header_distance=Inches(.34);sec.footer_distance=Inches(.35)
D.core_properties.title='From Intent to Evidence'
D.core_properties.subject='Evidence-guided engineering across seven public Git repositories'
D.core_properties.author=''
D.core_properties.keywords='software engineering; reproducibility; Git; assurance'
D.core_properties.comments=''

normal=D.styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(9.8);normal.font.color.rgb=INK
normal.paragraph_format.space_after=Pt(4.5)
normal.paragraph_format.line_spacing=1.11

def set_style(name,size,bold=False,color=INK,before=0,after=0,keep=True):
 st=D.styles[name] if name in D.styles else D.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
 st.font.name='Aptos Display' if size>=14 else 'Aptos'
 st.font.size=Pt(size);st.font.bold=bold;st.font.color.rgb=color
 st.paragraph_format.space_before=Pt(before);st.paragraph_format.space_after=Pt(after)
 st.paragraph_format.keep_with_next=keep
 return st
set_style('Title',25,True,NAVY,0,10)
set_style('Subtitle',12,False,GRAY,0,18)
set_style('Heading 1',14.5,True,NAVY,13,6)
set_style('Heading 2',11.2,True,NAVY,10,4)
set_style('Small Note',8.8,False,GRAY,0,5,False)
set_style('Source Note',8.55,False,INK,0,0,False)
set_style('Kicker',8.4,True,TEAL,0,5)
set_style('Key Point',10.1,True,NAVY,8,8,False)

# Prevent footer clutter
foot=sec.footer.paragraphs[0]; foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
foot.style='Small Note'
foot.add_run('FROM INTENT TO EVIDENCE     ').font.color.rgb=GRAY
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');foot._p.append(f)
head=sec.header.paragraphs[0];head.style='Small Note'
head.add_run('EVIDENCE-GUIDED SOFTWARE ENGINEERING').font.color.rgb=GRAY
head.paragraph_format.space_after=Pt(0)

# Low-level helpers

def shade(cell, fill):
 tcPr=cell._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),fill);tcPr.append(sh)

def borders(cell,bottom='E2E8EA'):
 tcPr=cell._tc.get_or_add_tcPr(); b=OxmlElement('w:tcBorders');x=OxmlElement('w:bottom');x.set(qn('w:val'),'single');x.set(qn('w:sz'),'4');x.set(qn('w:color'),bottom);b.append(x);tcPr.append(b)

def table_header(row):
 trPr=row._tr.get_or_add_trPr(); x=OxmlElement('w:tblHeader');x.set(qn('w:val'),'true');trPr.append(x)

def link(paragraph,caption,url):
 part=paragraph.part
 rid=part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
 hl=OxmlElement('w:hyperlink');hl.set(qn('r:id'),rid)
 run=OxmlElement('w:r');rpr=OxmlElement('w:rPr');cl=OxmlElement('w:color');cl.set(qn('w:val'),'006D6F');rpr.append(cl)
 ul=OxmlElement('w:u');ul.set(qn('w:val'),'single');rpr.append(ul);run.append(rpr)
 t=OxmlElement('w:t');t.text=caption;run.append(t);hl.append(run);paragraph._p.append(hl)

def para(txt='',style=None):
 p=D.add_paragraph(style=style);p.add_run(txt);return p

def rich(prefix,bold_text,rest,style=None):
 p=D.add_paragraph(style=style)
 if prefix:p.add_run(prefix)
 r=p.add_run(bold_text);r.bold=True
 p.add_run(rest)
 return p

def section(title,desc=None):
 D.add_heading(title,1)
 if desc:para(desc)

def sub(title):D.add_heading(title,2)

def source_table(records):
 t=D.add_table(rows=1,cols=2)
 t.alignment=WD_TABLE_ALIGNMENT.CENTER
 t.autofit=False
 t.columns[0].width=Inches(5.18);t.columns[1].width=Inches(1.24)
 h=t.rows[0];table_header(h)
 for c,s in zip(h.cells,['Recorded source change','Original Git revision']):
  c.text=s;shade(c,'F1F5F5');c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
  for p in c.paragraphs:p.style='Source Note'; p.runs[0].bold=True
 for i,r in enumerate(records):
  row=t.add_row();row.cells[0].text=r['label'];row.cells[1].text=''
  row.cells[0].width=Inches(5.18);row.cells[1].width=Inches(1.24)
  for c in row.cells:
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   if i%2==1:shade(c,'FAFBFB')
   borders(c)
  row.cells[0].paragraphs[0].style='Source Note'
  p=row.cells[1].paragraphs[0];p.style='Source Note';link(p,r['sha'][:10],r['url'])
 D.add_paragraph().paragraph_format.space_after=Pt(1)

def source_inline(records):
    p=D.add_paragraph(style='Source Note')
    p.paragraph_format.space_after=Pt(11)
    p.paragraph_format.keep_together=True
    lead=p.add_run('Original source changes: ')
    lead.bold=True
    for i,r in enumerate(records):
        if i:p.add_run('  ·  ')
        txt=r['label'].rstrip('.')
        # Anchor text remains meaningful; exact revision and full file identity are in the link.
        link(p,txt,r['url'])

# Collect seven-repo original source records
atlas=json.loads(ATLAS.read_text())
rec=[dict(repo=x['repository'].split('/')[-1], sha=x['commit_sha'],file_url=x['file_url']) for x in atlas['records'] if x['featured_case_source']]
group={}
for x in rec:group.setdefault(x['repo'],[]).append(x)
assert {k:len(v) for k,v in group.items()} == {'academics':4,'cora':6,'ictc':6,'teddy':6,'lumen':6,'NILO':6,'iKant_EDU':6}
rewrites={
 'ictc':[
  'Wait for the browser interaction to finish before inspecting the panel.',
  'Report the exact browser failure instead of hiding the failed check.',
  'Repeat metadata checks after the page updates.',
  'Check the meaning of the maturity indicator on every display path.',
  'Track how seven procedures produce metrics across users and revisions.',
  'Distinguish missing metadata from a wrong explanation.'
 ],
 'teddy':[
  'Update the motion evidence when movement rules change.',
  'Compare newer gesture tests with previously defined movement limits.',
  'Test whether animated surfaces move consistently with the body.',
  'Keep real service responses separate from simulated ones.',
  'Retain recent conversation context without scrambling its order.',
  'Keep browser graphics failures visible and clean up test sessions.'
 ],
 'lumen':[
  'Check that the public programme record names the right owner.',
  'Reject invalid claims about participation in the programme.',
  'Test cache failures and network responses across 80 modeled states.',
  'Offer a clear update action without losing what the reader typed.',
  'Reject unsafe characters in data-storage paths.',
  'Check database settings when the server starts.'
 ],
 'NILO':[
  'Update an older browser expectation after adding a new level.',
  'Keep graphics fault checks valid as the game expands.',
  'Preserve earlier physical fault checks for the new game state.',
  'Separate essential release conditions from external acceptance.',
  'Test eight deliberately broken delivery configurations.',
  'Align the defeat state and real keys with the game rules.'
 ],
 'iKant_EDU':[
  'Show the exact interface failure without removing the quality gate.',
  'Detect stale evidence after moving files and changing paths.',
  'Rebuild evidence identities for the relocated source files.',
  'Prevent test automation from rewriting the proposed code revision.',
  'Declare allowed changes and reject unrelated byte differences.',
  'Use the exact proposed source revision in project-session checks.'
 ],
 'cora':[
  'Specify expected results separately from the software being examined.',
  'Connect visual failure hypotheses to their source records.',
  'Publish an editable guide with evidence-based diagrams.',
  'Require all fifteen stated editorial conditions to hold.',
  'Preserve an inconclusive comparison against a strong checklist.',
  'Classify research files without treating them as runtime proof.'
 ],
 'academics':[
  'Rebuild source records when programme membership changes.',
  'Remove programme entries no longer in scope.',
  'Repair a broken link in the public research directory.',
  'Clarify the heading that guides readers to public repositories.'
 ]
}
for name,rows in group.items():
 assert len(rows)==len(rewrites[name]);
 for j,r in enumerate(rows): r['label']=rewrites[name][j];r['url']=r['file_url']

# EXECUTIVE ENTRY
para('A PRACTICAL FIELD GUIDE', 'Kicker')
D.add_paragraph('Build with AI. Verify before you trust.', 'Title')
D.add_paragraph('From an idea to accountable software decisions, illustrated by seven public Git histories.', 'Subtitle')
para('AI can produce a convincing patch faster than a team can assess its consequences. A better process begins with what a person needs to achieve, works backward to what must be true, changes one coherent part of the system, tests possible failure, and records who can accept the result. Neither clean code nor a green test alone is a release decision.')
para('The central rule', 'Kicker')
para('A claim is as strong as the observation that supports it—not as strong as the language used to describe it.', 'Key Point')
sub('A repeatable engineering loop')
rows=[
 ('Define the result','Describe the user action and every condition required for success.'),
 ('Change the software','Implement a reversible change and identify the exact source revision.'),
 ('Challenge the change','Run appropriate application tests and try realistic failure cases.'),
 ('Decide and learn','Record what passed, what failed, what remains unknown and who approves the next step.'),
]
for k,v in rows:
 p=D.add_paragraph(style='Normal')
 p.paragraph_format.space_after=Pt(2)
 p.add_run(k+'. ').bold=True
 p.add_run(v)
sub('Where the examples come from')
para('The cases draw on 149 selected, source-identified records across ICTC, Teddy, LUMEN, NILO, iKant_EDU, CORA and the academics programme registry. The linked examples below point to specific file versions. They show recorded engineering changes, not 149 independently repeated product tests.')
para('Reading guide: start with the method, examine a project case close to your own work, and use the closing decision questions before accepting a change.', 'Small Note')

section('Start with the result a person must achieve')
para('Consider a web application for reporting a problem. Someone submits a report, finds it again after the server restarts, and cannot close another person’s report. A pleasant screen is not enough: the result also requires durable storage, correct permissions, reliable retrieval and recovery.').paragraph_format.keep_with_next=True
sub('Work backward from success')
t=D.add_table(rows=1,cols=2);t.autofit=False;t.columns[0].width=Inches(2.2);t.columns[1].width=Inches(4.1)
for c,x in zip(t.rows[0].cells,['Required condition','A test that could disprove it']):c.text=x;shade(c,'F1F5F5');c.paragraphs[0].runs[0].bold=True
table_header(t.rows[0])
for a,b in [
 ('Report is saved','Restart the server, then retrieve the same record.'),
 ('Only authorized people can change it','Try to close another person’s report; the action must fail.'),
 ('The interface reflects actual data','Reload the page and compare it with persisted records.'),
 ('Failure can be diagnosed','Introduce a controlled error and inspect the recorded cause.'),
 ('The change can be reversed','Restore the previous version and confirm no data are lost.'),
]:
 cells=t.add_row().cells;cells[0].text=a;cells[1].text=b
 for c in cells:borders(c);c.paragraphs[0].style='Source Note'
para('All mandatory conditions must hold. A hundred successful interface tests cannot compensate for one failed authorization test.', 'Key Point')
sub('Change the roadmap when evidence changes')
para('For each proposed change, record the previous accepted revision, the intended user result, affected components, positive and negative tests, a recovery plan and a reviewer. Once tests reveal a new dependency or a surviving defect, revise the sequence of work. A plan is a hypothesis, not permission to ignore a failure.')

section('Know what the evidence can actually establish')
para('Source code, test scripts, screenshots and decisions answer different questions. Keep their claims separate.')
t=D.add_table(rows=1,cols=2);t.autofit=False;t.columns[0].width=Inches(2.06);t.columns[1].width=Inches(4.24)
for c,x in zip(t.rows[0].cells,['Evidence','What it can—and cannot—show']):c.text=x;shade(c,'F1F5F5');c.paragraphs[0].runs[0].bold=True
table_header(t.rows[0])
for a,b in [
 ('Git revision','Identifies tracked source bytes and history; not a running product.'),
 ('Test result','Records behavior within a named run and environment; not every situation.'),
 ('Screenshot','Shows pixels at one instant; not the root cause of an error.'),
 ('Dependency inventory','Lists known components; does not exclude unknown security flaws.'),
 ('Signed build evidence','Can verify a trusted build origin; not feature correctness.'),
 ('Human review','Records a decision by an accountable person; not infallibility.'),
]:
 c=t.add_row().cells;c[0].text=a;c[1].text=b
 for cell in c:borders(cell);cell.paragraphs[0].style='Source Note'
sub('Make the test capable of detecting a real mistake')
para('An AI assistant may write the change, the tests and a confident explanation. That can create self-confirming evidence. Define the expected result separately, include a test that should fail for a deliberately broken version, and preserve failures that remain undetected. A simulated fault tests the checker; it does not mean that the live application was broken.')
sub('Simplify without losing responsibilities')
para('Before moving or deleting code, trace known readers and writers, dynamically loaded modules, file paths, build rules, stored records and recovery procedures. Compare the old and new behavior. Unknown consumers are unresolved work, not evidence that deletion is safe. Fewer files or lines may reduce maintenance cost; they do not, by themselves, establish functional equivalence.')

section('What seven projects have in common')
for b,r in [
 ('Visible failures.','Tests should expose the specific operation that failed, instead of turning an error into a reassuring summary.'),
 ('Correct state over time.','A snapshot may look right while a restart, page update or later step reveals a defect.'),
 ('Independent expected results.','The checks must be able to reject plausible but wrong output.'),
 ('Source identity.','A result belongs to a precise revision and cannot be silently transferred to another.'),
 ('Preserved control.','Changes to roles, access or project membership must not accidentally grant authority.'),
 ('Human decision.','A reviewer accepts known residual risk; the coding assistant cannot approve itself.'),
]:rich('',b+' ',r)
para('The histories provide comparable examples of source changes, not comparable measures of engineering productivity. A repaired web cache, a game level and a corrected registry link differ in difficulty and intended outcome.')

# Case sections
cases=[
('ICTC','Compliance knowledge and procedural workflows',
 'A modal inspector obscured controls. Subsequent corrections moved its context into the normal page flow, and browser checks were added to distinguish an unfinished interaction from missing or wrong metadata.',
 'Examine the user’s role, the visible requirement, the persisted record after a restart and the exact browser failure. The source examples do not independently certify legal compliance or production behavior.'),
('Teddy','Local conversation and animated character',
 'Character movement, the shape of animated surfaces, conversation memory and browser request security produced different failure modes. The history adds movement checks, preserves conversation chronology and separates genuine service responses from simulated ones.',
 'Reproduce a gesture in an actual browser, check request identity and establish which model or service answered. An anatomical test cannot establish charm, empathy or reliable external service availability.'),
('LUMEN','Library services and offline web application',
 'A cache write may fail after the network has already delivered fresh content. The original work tests update behavior under storage constraints, protects a user’s unfinished form and strengthens startup and storage-path checks.',
 'Verify fresh online content, offline fallback, safe updates and real process restart. Public code does not establish live institutional catalogue integration, device-wide reliability or operational recovery.'),
('NILO','Narrative platform game',
 'Adding a third level changed legitimate expectations in older tests. The history preserves graphics fault checks, verifies the actual game-state rules and separates deployment constraints from player acceptance.',
 'Replay movement, boss states, saved checkpoints and the delivered build in a real browser. Deterministic gameplay checks do not prove enjoyment, artistic quality or commercial completeness.'),
('iKant_EDU','Experimental controller for language-model interactions',
 'Restructuring the repository moved files, changed server paths and invalidated generated evidence. Fixes rebound exact source identities and prevented a test workflow from rewriting the proposed source revision.',
 'Identify active and indirect consumers, retest the original entrypoints and verify the actual host interaction. A smaller directory tree or green local check cannot prove successful admission into an external host.'),
('CORA','Local engineering-assurance method and software',
 'An editorial checker initially missed a false claim because the expected words were still present. The source history records stronger negative tests, explicit evidence roles and a research comparison that did not demonstrate a differential advantage.',
 'Check that the expected result is independent of the proposed code, the evidence matches the exact revision and open gaps remain visible. The measured comparison on selected examples does not establish superiority to a strong checklist.'),
('academics','Public research programme registry',
 'Programme membership, source references and reader navigation are maintained as a public directory. The recorded changes remove obsolete entries, update source identities and repair a link and heading.',
 'Check that each stated member resolves to its intended repository and original record. Shared programme membership does not mean shared runtime, one approval authority or independent peer review.'),
]
for name,subtitle,story,gate in cases:
 section(name)
 p=para(subtitle,'Small Note');p.paragraph_format.space_after=Pt(10);p.paragraph_format.keep_with_next=True
 rich('','What happened. ',story).paragraph_format.keep_with_next=True
 rich('','What would make the conclusion stronger. ',gate).paragraph_format.keep_with_next=True
 source_inline(group[name if name in group else name.lower()])

section('Use the evidence to make a decision')
para('Before approving a change, ask five practical questions. Each answer should identify its evidence and any remaining uncertainty.')
questions=[
 ('What must work for the user?','List the mandatory outcomes, including access and recovery.'),
 ('What was actually run?','Record the source revision, command, environment, result and surviving failures.'),
 ('What might still be affected?','Name unknown consumers, side effects, external services and rollback risks.'),
 ('Which protections are effective?','Check permissions, reviewer independence, sensitive data and release controls—not merely their configuration files.'),
 ('Who makes the decision?','Identify the accountable reviewer and the conditions for revisiting acceptance.'),
]
for a,b in questions:rich('',a+' ',b)
sub('Does a structured method add value beyond a strong checklist?')
para('That is an open experimental question. A fair comparison would give equivalent tasks and information to three groups: a capable AI coding assistant with a strong persistent checklist; the same assistant following the structured method; and the same assistant using both the method and its local checking software. Independent reviewers should compare serious errors missed, human work, rework, recovery readiness and cost—not how persuasive the reports look.')
para('One published, author-selected comparison found identical results for the structured decision rule and an informed checklist on sixteen test cases. This is a useful null result, not a general finding of equivalence or a causal advantage.')
sub('Scope of this field guide')
para('The 149 selected historical references identify source files and commits across seven public repositories. The forty links in the project sections open additional exact-source examples. The material was not used here to rerun all seven products, authenticate an independent reviewer, conduct usability trials or measure development-time savings. Source history can explain the sequence of corrections; it cannot alone show that a method caused faster or better engineering.')
para('Takeaway: use AI to propose and implement; use independently meaningful observations to challenge; keep approval with accountable people.', 'Key Point')

D.save(OUT)
# Stabilize ZIP entry times and metadata so identical source inputs give identical DOCX bytes.
import io, os, zipfile
with zipfile.ZipFile(OUT,'r') as source:
  original=[(n,source.read(n)) for n in source.namelist()]
stream=io.BytesIO()
with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as target:
  for name,payload in original:
    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
    info.compress_type=zipfile.ZIP_DEFLATED
    info.external_attr=(0o644<<16)
    info.create_system=3
    target.writestr(info,payload,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
OUT.write_bytes(stream.getvalue())
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'source_links':sum(len(v) for v in group.values()),'paragraphs':len(D.paragraphs),'tables':len(D.tables)},indent=2))
