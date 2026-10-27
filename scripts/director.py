#!/usr/bin/env python3
"""Local validation-enhanced Image Director; not an approval service or sandbox."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path

import director_validate as v
import director_checklists as worklists

HERE=Path(__file__).resolve().parent


def atomic_json(path,value):
    path=Path(path); v.under(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    # task lock serializes receipt writers; do not follow a pre-existing symlink.
    flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW
    fd=os.open(tmp,flags,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)


def exact_file(path,data):
    path=Path(path); v.under(path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        v.need(not path.is_symlink() and path.read_bytes()==data, 'existing version changed: '+str(path))
    else:
        with path.open('xb') as f: f.write(data)


@contextmanager
def locked(root):
    directory=v.under(Path(root)/'work/director')
    directory.mkdir(parents=True,exist_ok=True)
    lock=directory/'.lock'
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'r+') as f:
        try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise v.Invalid('another director process is running for this task')
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)


def dirs(b):
    root=v.under(b['task']['root'], allow_root=True)
    tag=b['id']+'-v'+str(b['version'])
    return root/'work/director'/tag,root/'outputs/generated-images'/tag


def table_cell(value):
    return str(value).replace('|','\\|').replace('\n','<br>')


def render_text(b):
    lines=['# '+b['id']+' v'+str(b['version']), '', '原始需求：'+b['task']['request'], '']
    if b['stage']=='inventory':
        for r in b['references']:
            lines += ['## '+r['id']+' · '+r['role'], json.dumps(r['inventory'],ensure_ascii=False),'']
    elif b['stage']=='keywords':
        lines += ['| 字面词 | 词性/语义 | L2 候选 | L3 延伸 | icon 候选 | 场景对齐 |','|---|---|---|---|---|---|']
        for k in b['keywords']:
            row=[k['word'],k['semantic'],' / '.join(k['l2']),' / '.join(k['l3']),' / '.join(k['icons']),k['scene_alignment']]
            lines.append('| '+' | '.join(table_cell(x) for x in row)+' |')
    elif b['stage']=='directions':
        lines += ['| 方案 | 主体 | 主打语义 |','|---|---|---|']
        for s in b['directions']:
            lines.append('| '+' | '.join(table_cell(x) for x in (s['id']+'：'+s['name'],s['subject'],s['meaning']))+' |')
    else:
        if b['stage']=='composition':
            axes=b['variation_axes']
            lines += ['## 构图变体表','| 变体 | '+' | '.join(table_cell(a['label']) for a in axes)+' |','|---|---|---|---|---|']
            for s in b['schemes']:
                lines.append('| '+' | '.join(table_cell(x) for x in [s['id']+'：'+s['name']]+[s['variation_values'][a['id']] for a in axes])+' |')
            lines += ['']
        for s in b.get('schemes',[]):
            prompt=v.sent_prompt(s)
            fence='`' * max(3,max((len(x) for x in __import__('re').findall(r'`+',prompt)),default=0)+1)
            lines += ['## '+s['id']+'：'+s['name'], '', '### 实际发送 Prompt',fence+'text',prompt,fence,'','### 对照清单']
            lines += ['- '+k+'：'+val for k,val in s['checklist'].items()]
            lines += ['']
    return '\n'.join(lines)+'\n'


def freeze(b):
    work,output=dirs(b)
    exact_file(work/'bundle.json',v.canonical(b))
    exact_file(work/'review.md',render_text(b).encode('utf-8'))
    for s in b.get('schemes',[]):
        exact_file(work/(s['id']+'.prompt.txt'),v.sent_prompt(s).encode('utf-8'))
    return work,output


def inputs(b):
    refs={r['id']:r for r in b['references']}
    if b['stage'] in ('ip-correction','style-correction'):
        p=b['parent']; receipt=json.loads(v.descriptor(p['receipt']))
        item=receipt['items'][p['scheme_id']]
        parent={'path':item['path'],'sha256':item['sha256'],'id':'selected-image'}
        role='ip' if b['stage']=='ip-correction' else 'style'
        target=next(r for r in b['references'] if r['role']==role)
        return [parent,target]
    ordered=[refs[rid] for rid in b['reference_ids']]
    if b['stage'] in ('composition','refinement'):
        p=b['parent']; receipt=json.loads(v.descriptor(p['receipt']))
        item=receipt['items'][p['scheme_id']]
        ordered.append({'path':item['path'],'sha256':item['sha256'],'id':'selected-parent'})
    return ordered


def requests(b,work,output):
    refs=[]
    for index,r in enumerate(inputs(b)):
        data=v.descriptor(r,image=True)
        info=v.image_info(data)
        suffix={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}.get(info['format'])
        v.need(suffix is not None,'image reference must be PNG, JPEG or WebP')
        path=work/'references'/('%02d'%index+suffix)
        exact_file(path,data)
        refs.append({'path':str(path),'sha256':v.digest(data)})
    jobs=[]
    for s in b['schemes']:
        path=work/(s['id']+'.prompt.txt'); data=path.read_bytes()
        v.need(data==v.sent_prompt(s).encode('utf-8'),'prompt archive/send mismatch')
        target=output/(s['id']+'.png')
        arguments={'prompt':v.sent_prompt(s)}
        if refs: arguments['referenced_image_paths']=[r['path'] for r in refs]
        content={'prompt_sha256':v.digest(data),'references':refs,'parameters':b['parameters'],'n':1}
        jobs.append({'id':s['id'],'path':str(target),'tool':'image_gen.imagegen','arguments':arguments,
                     'request_hash':v.hash_obj(content),'content':content})
    return jobs


def run(b, execute=False):
    v.validate(b)
    v.need(b['stage'] in v.GENERATING,'run accepts generation stages only')
    v.need(not execute,'--execute was removed: dispatch each checked request through the Codex built-in image_gen tool')
    backend='codex-built-in-imagegen'
    with locked(b['task']['root']):
        work,output=freeze(b)
        jobs=requests(b,work,output)
        task_plan=worklists.official_plan(b,jobs)
        snapshot={'bundle_hash':v.hash_obj(b),'jobs':jobs,'backend':backend}
        exact_file(work/'requests.json',v.canonical(snapshot))
        receipt_path=work/'receipt.json'
        if receipt_path.exists():
            receipt=v.read_json(receipt_path)
            v.need(receipt.get('bundle_hash')==v.hash_obj(b) and receipt.get('backend')==backend and
                   receipt.get('plan_hash')==v.hash_obj(task_plan),'receipt mismatch')
            v.need(set(receipt.get('items',{}))=={j['id'] for j in jobs},'receipt job set changed')
        else:
            receipt={'bundle_hash':v.hash_obj(b),'plan_hash':v.hash_obj(task_plan),'stage':b['stage'],
                     'backend':backend,'items':{j['id']:{'status':'not_started','path':j['path'],
                     'request_hash':j['request_hash'],'attempts':0,'events':[]} for j in jobs}}
        atomic_json(receipt_path,receipt)
        worklists.materialize(work,task_plan,receipt)
        return {'status':'prepared','calls':0,'requests':str(work/'requests.json'),'receipt':str(receipt_path),
                'review':str(work/'review.md'),'next':'dispatch_each_job_with_image_gen'}


def review_template(b):
    v.validate(b); work,_=dirs(b)
    receipt=v.read_json(work/'receipt.json')
    v.need(receipt['bundle_hash']==v.hash_obj(b),'receipt mismatch')
    items={}
    for s in b['schemes']:
        item=receipt['items'][s['id']]
        if item['status']!='success': continue
        v.descriptor({'path':item['path'],'sha256':item['sha256']},image=True)
        items[s['id']]={'image_sha256':item['sha256'],'checks':{
            key:{'expected':expected,'observed':'','verdict':'unknown'} for key,expected in s['checklist'].items()}}
    return {'bundle_hash':v.hash_obj(b),'items':items,'notice':'Fill observed values only after actually viewing images; never auto-pass.'}


def export_final(b):
    v.validate(b); v.need(b['stage']=='final','final stage required')
    with locked(b['task']['root']):
        work,out=freeze(b)
        parent,scheme,image=v.selected_parent(b,0)
        exports=b['final'].get('exports') or [{'id':'final','asset':image,'background':b['final']['background']}]
        prepared=[]
        for item in exports:
            data=v.descriptor(item['asset'],image=True)
            target=v.under(Path(b['task']['root'])/'outputs/final'/(b['id']+'-v'+str(b['version']))/(item['id']+'.png'))
            if target.exists(): v.need(target.read_bytes()==data,'existing final export changed')
            prepared.append((target,data))
        files=[]
        for target,data in prepared:
            exact_file(target,data)
            files.append({'path':str(target),'sha256':v.digest(data),'image':v.image_info(data)})
        report={'status':'exported','files':files,'scope':'local decision records only; not authenticated approval or visual acceptance'}
        atomic_json(work/'export-receipt.json',report)
        return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('validate','subjects','render','run','review-template','export'))
    p.add_argument('bundle'); p.add_argument('--execute',action='store_true',help='deprecated and rejected; use checked built-in image_gen dispatch')
    a=p.parse_args()
    try:
        b=v.read_json(a.bundle)
        if a.command=='validate':
            v.validate(b); result={'status':'pass','scope':'deterministic subset only'}
        elif a.command=='subjects': result={'subjects':v.decision_hashes(b),'notice':'Hashes are not approvals; do not invent user responses.'}
        elif a.command=='render':
            v.validate(b)
            with locked(b['task']['root']): work,_=freeze(b)
            result={'review':str(work/'review.md')}
        elif a.command=='run': result=run(b,a.execute)
        elif a.command=='review-template': result=review_template(b)
        else: result=export_final(b)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 3 if result.get('status')=='incomplete' else 0
    except (v.Invalid,ValueError,TypeError,KeyError,OSError,ImportError) as e:
        print(json.dumps({'status':'rejected','error':str(e)},ensure_ascii=False)); return 2

if __name__=='__main__': raise SystemExit(main())
