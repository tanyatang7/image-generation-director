#!/usr/bin/env python3
"""Deterministic checks for Image Generation Director. Local records are NOT authentication."""
import argparse
import hashlib
import io
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path(os.environ.get('IMAGE_DIRECTOR_ROOT') or Path.cwd()).expanduser().resolve()
SCHEMA = 1
STAGES = ('inventory', 'keywords', 'directions', 'round1', 'composition', 'refinement', 'ip-correction', 'style-correction', 'final')
GENERATING = STAGES[3:8]
COMBINATIONS = {'C1':'A1','C2':'A1','C3':'A2','C4':'A3','C5':'A3','C6':'A4','C7':'A4','C8':'A5','C9':'A5'}
CHECK_FIELDS = ('relation','decoration_count','decoration_shape','decoration_position','interior','icon_count','icon_position','icon_type','surface','perspective','framing','crop','palette')
CORRECTION_IP = '保持图1的风格、质感、元素和构图不变，替换为图2的IP形象，'
CORRECTION_STYLE_IP = '保持图1的构图、元素和IP形象不变，替换为图2的风格、配色、质感'
CORRECTION_STYLE_OTHER = '保持图1的构图、元素、主体形态和主色调不变，仅替换为图2的风格、配色、质感'
# User selected refill-to-five + renewed review, and label-free send text.
PROMPT_LABEL = re.compile(r'(?:^|[\n;；])\s*(?:[-*]\s*)?(?:场景|使用场景|主体|动作|主体姿态|副元素|副元素动态|点缀|构图关系|配色|透视|风格|scene|subject|action|pose|secondary element|composition|palette|perspective|style)\s*[:：]', re.IGNORECASE)

class Invalid(ValueError):
    pass

def need(condition, message):
    if not condition:
        raise Invalid(message)

def text(value, where):
    need(isinstance(value, str) and value.strip(), where + ': expected nonempty text')
    return value

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def hash_obj(value):
    return digest(canonical(value))

def read_json(path):
    def unique(pairs):
        result = {}
        for k,v in pairs:
            need(k not in result, 'duplicate JSON key: ' + k)
            result[k] = v
        return result
    value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)
    need(isinstance(value, dict), 'JSON root must be an object')
    return value

def under(path, root=ROOT, *, allow_root=False):
    p = Path(path)
    need(p.is_absolute(), 'absolute path required: ' + str(p))
    p = p.resolve()
    need((allow_root and p == root.resolve()) or root.resolve() in p.parents, 'path outside root: ' + str(p))
    return p

def image_info(data):
    from PIL import Image
    with Image.open(io.BytesIO(data)) as img:
        img.verify()
    with Image.open(io.BytesIO(data)) as img:
        img.load()
        alpha = img.convert('RGBA').getchannel('A')
        return {'width':img.width, 'height':img.height, 'format':img.format,
                'has_alpha_channel': 'A' in img.getbands() or 'transparency' in img.info,
                'has_transparent_pixels':alpha.getextrema()[0] < 255}

def descriptor(ref, image=False):
    need(isinstance(ref, dict), 'file descriptor required')
    p = Path(text(ref.get('path'), 'file.path'))
    need(p.is_absolute() and p.is_file(), 'missing absolute file: ' + str(p))
    data = p.read_bytes()
    need(digest(data) == ref.get('sha256'), 'file changed/hash mismatch: ' + str(p))
    if image:
        image_info(data)
    return data

def identity(item):
    text(item.get('id'), 'id')
    need(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',item['id']), 'unsafe id: ' + item['id'])
    return item['id']

def objects(items, name):
    need(isinstance(items, list), name + ': expected array')
    ids = []
    for item in items:
        need(isinstance(item, dict), name + ': expected objects')
        ids.append(identity(item))
    need(len(ids) == len(set(ids)), name + ': duplicate ids')
    return items

def decision(b, name, subject, actions):
    d = b.get('decisions', {}).get(name)
    need(isinstance(d, dict), 'waiting for local user-response record: ' + name)
    need(d.get('action') in actions, 'decision not approved/selected: ' + name)
    need(d.get('subject_hash') == hash_obj(subject), 'stale decision: ' + name)
    text(d.get('response_text'), name + '.response_text')
    text(d.get('source'), name + '.source')
    return d

def subjects(b):
    return {'inventory': {'task':b.get('task'), 'references':b.get('references')},
            'keywords': {'inventory_hash':hash_obj({'task':b.get('task'),'references':b.get('references')}),'keywords':b.get('keywords')},
            'directions': {'inventory_hash':hash_obj({'task':b.get('task'),'references':b.get('references')}),'keywords_hash':hash_obj(b.get('keywords')), 'directions':b.get('directions')}}

def decision_hashes(b):
    result={k:hash_obj(x) for k,x in subjects(b).items()}
    if b.get('parent'):
        p=b['parent']
        parent=json.loads(descriptor(p['bundle']))
        rec=json.loads(descriptor(p['receipt']))
        descriptor(p['review'])
        result['parent_choice']=hash_obj({'bundle_hash':hash_obj(parent),'receipt_sha256':p['receipt']['sha256'],'review_sha256':p['review']['sha256']})
        if b.get('final'):
            item=rec['items'][p['scheme_id']]
            result['final']=hash_obj({'image':{'path':item['path'],'sha256':item['sha256']},'parent_bundle_hash':hash_obj(parent),'export_spec':b['final']})
    return result


def coverage(schemes, composition=False):
    combos = [s['combination'] for s in schemes]
    need(max(Counter(combos).values(), default=0) <= 2, 'same C combination used more than twice')
    values = combos if composition else [COMBINATIONS[c] for c in combos]
    need(len(set(values)) >= 3, 'need at least 3 ' + ('C combinations' if composition else 'A relations'))

def scheme(s, mode, expanded=False):
    identity(s)
    for field in ('name','subject','meaning','motion','perspective'):
        text(s.get(field), s['id'] + '.' + field)
    need(s.get('combination') in COMBINATIONS, s['id'] + ': invalid C combination')
    need(isinstance(s.get('elements'), list) and len(s['elements']) > 0, 'elements required')
    for x in s['elements']:
        text(x, 'element')
    need(len(set(s['elements'])) == len(s['elements']), 'duplicate element identifiers')
    if mode == 'ip':
        need(s.get('ip_role') in ('main','secondary'), 'IP role must be main or secondary')
    if expanded:
        prompts = s.get('prompts', {})
        for lang in ('zh','en'):
            text(prompts.get(lang), s['id'] + '.prompts.' + lang)
            need(prompts[lang] == prompts[lang].strip(), 'prompt must not have leading/trailing whitespace')
            need(not PROMPT_LABEL.search(prompts[lang]), 'prompt contains field labels: compose complete label-free text before freezing; do not strip at send time')
        need(s.get('send_language') in ('zh','en'), 'send_language required')
        checks = s.get('checklist', {})
        need(isinstance(checks, dict), 'checklist object required')
        for field in CHECK_FIELDS:
            text(checks.get(field), s['id'] + '.checklist.' + field)

def selected_parent(b, depth):
    p = b.get('parent')
    need(isinstance(p, dict), 'parent bundle/receipt/selection required')
    raw = descriptor(p.get('bundle'))
    parent = json.loads(raw)
    validate(parent, depth=depth+1)
    rec = json.loads(descriptor(p.get('receipt')))
    need(rec.get('bundle_hash') == hash_obj(parent), 'parent receipt belongs to another bundle')
    need(rec.get('backend') == 'codex-built-in-imagegen', 'non-built-in receipts cannot authorize production descendants')
    sid = text(p.get('scheme_id'), 'parent.scheme_id')
    item = rec.get('items',{}).get(sid,{})
    need(item.get('status') == 'success', 'selected parent image is not a successful result')
    image = {'path':item.get('path'), 'sha256':item.get('sha256')}
    descriptor(image, image=True)
    expected = {s['id'] for s in parent['schemes']}
    need(set(rec.get('items',{})) == expected, 'parent round has missing/extra result records')
    need(not any(x.get('status') in ('pending','running') for x in rec['items'].values()), 'parent round still running')
    review = json.loads(descriptor(p.get('review')))
    need(review.get('bundle_hash') == hash_obj(parent), 'review belongs to another bundle')
    failed = False
    for ps in parent['schemes']:
        outcome = rec['items'][ps['id']]
        if outcome['status'] != 'success':
            failed = True
            continue
        row = review.get('items',{}).get(ps['id'],{})
        need(row.get('image_sha256') == outcome['sha256'], 'missing/stale visual review: '+ps['id'])
        descriptor({'path':outcome['path'],'sha256':outcome['sha256']},image=True)
        need(set(row.get('checks',{})) == set(ps['checklist']), 'visual review must address every checklist field')
        for field, observed in row['checks'].items():
            text(observed.get('observed'), 'review.'+field)
            need(observed.get('verdict') in ('pass','fail','unknown'), 'invalid review verdict')
            failed |= observed['verdict'] != 'pass'
    subject = {'bundle_hash':hash_obj(parent),'receipt_sha256':p['receipt']['sha256'],'review_sha256':p['review']['sha256']}
    d = decision(b, 'parent_choice', subject, ('select','accept_current','correct','continue_correction'))
    need(d.get('selected_id') == sid, 'choice does not match parent image')
    if failed:
        need(d.get('accepts_issues') is True, 'parent has failed/unknown fields or failed images: user disposition required')
    need(parent['task'] == b['task'], 'parent task identity/requirements changed')
    if parent['references'] != b['references']:
        decision(b, 'reference_change', {'before':parent['references'],'after':b['references']}, ('confirm',))
    source_scheme = next(x for x in parent['schemes'] if x['id'] == sid)
    return parent, source_scheme, image

def validate(b, stage=None, depth=0):
    need(depth <= 12, 'dependency chain too deep/cyclic')
    need(b.get('schema_version') == SCHEMA, 'unsupported schema_version')
    stage = stage or b.get('stage')
    need(stage in STAGES, 'unknown stage')
    identity(b)
    need(type(b.get('version')) is int and b['version'] >= 1, 'version must be positive integer')
    task = b.get('task', {})
    for k in ('id','request','scenario'):
        text(task.get(k), 'task.'+k)
    under(task.get('root',''), allow_root=True)
    need(task.get('mode') in ('ip','non-ip'), 'task.mode must be ip or non-ip')
    refs = objects(b.get('references'), 'references')
    roles = [r.get('role') for r in refs]
    need(all(x in ('style','ip','detail') for x in roles), 'unknown reference role')
    need(roles.count('style') <= 1 and roles.count('ip') <= 1, 'duplicate primary reference roles')
    if task['mode'] == 'ip':
        need(roles.count('style') == 1 and roles.count('ip') == 1, 'IP mode requires style and IP roles (same file allowed)')
    if 'style' not in roles:
        text(task.get('style_text'), 'task.style_text required without style reference')
    for r in refs:
        descriptor(r, image=True)
        inv = r.get('inventory',{})
        for k in ('subject_type','background'):
            text(inv.get(k), 'inventory.'+k)
        for k in ('colors','accessories'):
            need(isinstance(inv.get(k),list) and len(inv[k]) <= 3, 'inventory.'+k+' must be an array of at most 3')
            for x in inv[k]: text(x,'inventory.'+k)
    if stage == 'inventory': return
    subs = subjects(b)
    decision(b, 'inventory', subs['inventory'], ('confirm',))
    kw = objects(b.get('keywords'), 'keywords')
    need(3 <= len(kw) <= 5, 'keywords must have 3–5 entries as defined in core.md; semantic grouping remains human/AI review')
    for k in kw:
        for field in ('word','semantic','scene_alignment'): text(k.get(field), 'keyword.'+field)
        need(isinstance(k.get('l2'),list) and len(k['l2']) == 5, 'each keyword needs 5 L2 candidates')
        for x in k['l2']: text(x,'L2 candidate')
        need(isinstance(k.get('icons'),list) and 2 <= len(k['icons']) <= 4, 'each keyword needs 2–4 icon candidates')
        for x in k['icons']: text(x,'icon candidate')
        need(isinstance(k.get('l3'),list), 'L3 candidates must be an array, may be empty')
    if stage == 'keywords': return
    decision(b, 'keywords', subs['keywords'], ('confirm',))
    dirs = objects(b.get('directions'), 'directions')
    need(len(dirs) == 5, 'initial direction pool must contain exactly 5 schemes')
    for s in dirs: scheme(s,task['mode'])
    exception = b.get('decisions',{}).get('reference_layout')
    if exception:
        decision(b,'reference_layout',subs['inventory'],('reuse_layout','close_edit'))
    else:
        coverage(dirs)
    if task['mode'] == 'ip':
        need({s['ip_role'] for s in dirs} == {'main','secondary'}, 'IP directions must mix main and secondary roles')
    if stage == 'directions': return
    choice = decision(b, 'directions', subs['directions'], ('confirm',))
    ids = choice.get('selected_ids')
    need(isinstance(ids,list) and len(ids)>0 and len(ids)==len(set(ids)), 'selected direction IDs required')
    need(set(ids) <= {s['id'] for s in dirs}, 'selected direction outside reviewed pool')
    need(len(ids) == 5, 'excluded directions must be replaced to restore five, then the revised pool must be reviewed before generation')
    if stage == 'final':
        validate_final(b, depth)
        return
    schemes = objects(b.get('schemes'), 'schemes')
    need(schemes, 'no generation schemes')
    for s in schemes: scheme(s,task['mode'],expanded=True)
    if stage == 'round1':
        need([s['id'] for s in schemes] == ids, 'round1 must contain exactly the selected IDs, in order')
        for s in schemes:
            original = next(x for x in dirs if x['id']==s['id'])
            need(all(s.get(k)==v for k,v in original.items()), 'direction silently changed while expanding prompt: '+s['id'])
        need(len({s['prompts'][s['send_language']] for s in schemes}) == len(schemes), 'duplicate round1 prompts')
    else:
        parent, ps, image = selected_parent(b, depth)
        if stage == 'composition':
            need(parent['stage'] == 'round1', 'composition requires selected round1 image')
            need(len(schemes)==5, 'composition requires 5 variants')
            coverage(schemes, composition=True)
            axes=objects(b.get('variation_axes'),'variation_axes')
            need(len(axes)==4 and {'combination','motion'} <= {a['id'] for a in axes},'choose 4 variation axes including combination and motion')
            for a in axes: text(a.get('label'),'variation axis label')
            for entry in schemes:
                values=entry.get('variation_values',{})
                need(set(values)=={a['id'] for a in axes},'variation values must match the chosen axes')
                for value in values.values(): text(value,'variation value')
                need(values['combination']==entry['combination'] and values['motion']==entry['motion'],'variation table differs from scheme')
            for s in schemes:
                need(set(s['elements']) == set(ps['elements']), 'composition changed bound elements')
            if task['mode']=='ip':
                need({s['ip_role'] for s in schemes}=={'main','secondary'}, 'IP variants must mix main and secondary roles')
        elif stage == 'refinement':
            need(parent['stage']=='composition', 'refinement requires selected composition')
            need(len(schemes)==3, 'refinement requires 3 images')
            need(b['decisions']['parent_choice'].get('next')=='refine', 'refinement not chosen')
            need(len({s['prompts'][s['send_language']] for s in schemes})==1, 'refinement uses same prompt in 3 independent calls')
        elif stage == 'ip-correction':
            need(task['mode']=='ip' and parent['stage'] in ('composition','refinement'), 'invalid IP correction parent/mode')
            need(len(schemes)==1 and sent_prompt(schemes[0])==CORRECTION_IP, 'IP correction must use exact fixed prompt')
            need(b['decisions']['parent_choice']['action']=='correct', 'correction not chosen')
        elif stage == 'style-correction':
            need(len(schemes)==1, 'style correction requires one image')
            if task['mode']=='ip':
                need(parent['stage']=='ip-correction', 'IP mode must correct IP before style')
                fixed=CORRECTION_STYLE_IP
            else:
                need(parent['stage'] in ('composition','refinement'), 'invalid non-IP correction parent')
                fixed=CORRECTION_STYLE_OTHER
            need(sent_prompt(schemes[0])==fixed, 'style correction must use exact fixed prompt')
            need(b['decisions']['parent_choice']['action'] in ('correct','continue_correction'), 'correction not chosen/continued')
    params = b.get('parameters',{})
    need(set(params) <= {'model','size','quality','output_format'}, 'unsupported parameter; no force/augmentation/batch override')
    need(params.get('model')=='gpt-image-2' and params.get('output_format')=='png', 'backend must be gpt-image-2 PNG')
    need(params.get('quality') in ('low','medium','high','auto'), 'invalid quality')
    size = params.get('size')
    need(size=='auto' or isinstance(size,str) and re.fullmatch(r'\d+x\d+',size), 'invalid size')
    ordered = [r['id'] for role in ('style','ip','detail') for r in refs if r['role']==role]
    need(b.get('reference_ids')==ordered, 'reference order must be style, IP, then details; do not deduplicate same files')

def sent_prompt(s):
    return s['prompts'][s['send_language']]

def validate_final(b, depth):
    parent, ps, image = selected_parent(b,depth)
    need(parent['stage'] in ('composition','refinement','ip-correction','style-correction'), 'cannot finalize first-round exploration')
    target = {'image':image,'parent_bundle_hash':hash_obj(parent),'export_spec':b.get('final')}
    d = decision(b,'final',target,('deliver_without_correction','deliver_after_correction','stop_correction'))
    if d['action']=='deliver_after_correction':
        need(parent['stage']=='style-correction', 'correction has not completed')
    elif d['action']=='stop_correction':
        need(parent['stage'] in ('ip-correction','style-correction'), 'no correction to stop')
    for field in ('comparison','background'):
        text(b.get('final',{}).get(field),'final.'+field)
    need(b['final']['background'] in ('preserve','transparent'), 'final background must be preserve or transparent')
    exports = b['final'].get('exports')
    if exports is None:
        exports = [{'id':'final','asset':image,'background':b['final']['background']}]
    objects(exports,'final.exports')
    need(exports,'no final exports')
    for export in exports:
        asset=export.get('asset')
        info=image_info(descriptor(asset,image=True))
        need(info['format']=='PNG','final asset must be PNG')
        need(export.get('background') in ('preserve','transparent'),'export background required')
        if export['background']=='transparent':
            need(info['has_transparent_pixels'],'export has no transparent pixels')
        for field in ('width','height'):
            if field in export:
                need(type(export[field]) is int and info[field]==export[field],'actual export '+field+' mismatch')
        if asset != image:
            text(export.get('processing_note'),'processed export needs provenance note')
            need(export.get('source_sha256')==image['sha256'],'processed export must reference selected source image')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle'); p.add_argument('--stage',choices=STAGES); p.add_argument('--subjects',action='store_true')
    a=p.parse_args()
    try:
        b=read_json(a.bundle)
        if a.subjects:
            result={'subjects':decision_hashes(b),'notice':'Hashes are not approvals; source records are local and unauthenticated.'}
        else:
            validate(b,a.stage)
            result={'status':'pass','stage':a.stage or b['stage'],'bundle_hash':hash_obj(b), 'scope':'structure/file consistency only; user records and visual claims are not authenticated'}
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except (Invalid,ValueError,KeyError,TypeError,OSError,ImportError) as e:
        print(json.dumps({'status':'fail','error':str(e)},ensure_ascii=False)); return 2

if __name__=='__main__':
    raise SystemExit(main())
