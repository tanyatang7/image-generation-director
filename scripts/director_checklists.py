#!/usr/bin/env python3
"""Linked local worklists. Not a protected tool gateway or user approval service."""
import argparse
import json
from pathlib import Path
import shutil

import director_validate as v

COUNTS = {'round1': 5, 'composition': 5, 'refinement': 3,
          'ip-correction': 1, 'style-correction': 1}
TRANSITIONS = {'confirm_directions': ('directions', 'round1'),
               'select_direction': ('round1', 'composition'),
               'select_composition': ('composition', 'refinement')}


def write(path, value):
    path = v.under(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    v.need(not tmp.is_symlink(), 'temporary path is a symlink')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def frozen(path, value):
    path = v.under(path)
    if path.exists():
        v.need(not path.is_symlink() and v.read_json(path) == value,
               'worklist version changed; create a new version')
    else:
        write(path, value)


def quoted(record, label):
    v.need(isinstance(record, dict), label + ' record required')
    v.text(record.get('text'), label + '.text')
    v.text(record.get('source'), label + '.source')


def expected_stage(spec):
    """Agent classifies intent; this verifies its declared transition, not natural language."""
    current = spec['current_stage']
    decision = spec['decision']
    quoted(decision, 'decision')
    action = decision['action']
    if action in TRANSITIONS:
        prior, target = TRANSITIONS[action]
        v.need(current == prior, 'choice does not match current stage')
        if action.startswith('select_'):
            v.text(decision.get('selected_id'), 'decision.selected_id')
        count = COUNTS[target]
    elif action == 'modify':
        v.need(current in COUNTS, 'cannot treat a direction choice as a single edit')
        target, count = current, COUNTS[current]
    elif action == 'explicit_override':
        override = spec.get('override')
        quoted(override, 'explicit override')
        target, count = override.get('stage'), override.get('count')
        v.need(target in COUNTS and type(count) is int and count > 0,
               'explicit override stage/count invalid')
    else:
        raise v.Invalid('unsupported intent; record human decision before generation')
    v.need(spec['next_stage'] == target, 'next stage differs from declared user decision')
    v.need(spec['expected_count'] == count, 'expected count differs from transition')
    return target, count


def make_plan(stage, jobs, context, backend):
    v.need(len({j['id'] for j in jobs}) == len(jobs), 'duplicate task id')
    for job in jobs:
        v.text(job['id'], 'task id')
        v.need('/' not in job['id'] and job['id'] not in ('.', '..'), 'unsafe task id')
        v.text(job['prompt'], 'prompt')
        v.need(isinstance(job['checks'], dict) and bool(job['checks']), 'acceptance criteria required')
        for value in job['checks'].values(): v.text(value, 'acceptance criterion')
    return {'schema_version': 1, 'stage': stage, 'backend': backend,
            'context': context, 'expected_count': len(jobs), 'tasks': jobs,
            'boundary': 'Local agent-written records; not authenticated decisions or global interception.'}


def validate_assets(plan):
    for job in plan['tasks']:
        for ref in job['references']: v.descriptor(ref, image=True)
        if 'prompt_file' in job:
            v.need(Path(job['prompt_file']).read_text(encoding='utf-8') == job['prompt'],
                   'saved prompt differs from planned request')


def materialize(work, plan, receipt=None, review=None):
    """Generate three views; executing successfully never fills visual/human PASS."""
    work = v.under(work)
    frozen(work / 'task-list.json', plan)
    if review is None and receipt and (work / 'saved-check-review.json').exists():
        review = v.read_json(work / 'saved-check-review.json')
    if receipt:
        v.need(set(receipt['items']) == {j['id'] for j in plan['tasks']}, 'receipt task set differs')
    if review:
        v.need(set(review['items']).issubset({j['id'] for j in plan['tasks']}), 'unknown review task')
    execution, checks = [], []
    for job in plan['tasks']:
        item = (receipt or {}).get('items', {}).get(job['id'], {})
        status = item.get('status', 'not_started')
        evidence = None
        if status == 'success':
            evidence = {'path': item['path'], 'sha256': item['sha256']}
            v.descriptor(evidence, image=True)
        execution.append({'task_id': job['id'], 'status': status,
                          'attempts': item.get('attempts', 0), 'evidence': evidence,
                          'events': item.get('events', [])})
        rr = (review or {}).get('items', {}).get(job['id'])
        if rr:
            v.need(evidence and rr.get('image_sha256') == evidence['sha256'], 'review image changed')
            v.need(set(rr['checks']) == set(job['checks']), 'review is missing or adding criteria')
        for key, criterion in job['checks'].items():
            result = {'expected': criterion, 'observed': '', 'verdict': 'unknown',
                      'reviewer': '', 'method': '', 'reviewer_kind': 'ai_visual'}
            if rr:
                incoming = rr['checks'][key]
                v.need(incoming.get('expected', criterion) == criterion, 'review criterion changed')
                result.update(incoming)
                v.need(result['verdict'] in ('pass', 'fail', 'unknown'), 'invalid check verdict')
                v.need(result['reviewer_kind'] in ('program', 'ai_visual'), 'human acceptance belongs to human decision record')
                if result['verdict'] != 'unknown':
                    for field in ('observed', 'reviewer', 'method'): v.text(result[field], field)
            checks.append({'task_id': job['id'], 'criterion_id': key, **result,
                           'image_sha256': evidence['sha256'] if evidence else None})
    all_done = bool(execution) and all(x['status'] == 'success' for x in execution)
    all_pass = bool(checks) and all(x['verdict'] == 'pass' for x in checks)
    # A stored decision is a source declaration, not verified approval.
    human = (review or {}).get('human_decision')
    if human:
        quoted(human, 'human decision')
        v.need(human.get('selected_id') in {j['id'] for j in plan['tasks']}, 'human selected unknown task')
    result = {'execution_complete': all_done, 'checks_complete': all(x['verdict'] != 'unknown' for x in checks),
              'checks_passed': all_done and all_pass, 'human_decision': human,
              'next': 'await_user_choice' if all_done and all_pass else 'review_or_repair',
              'scope': 'Files and records checked locally; does not prove natural-language intent or user acceptance.'}
    write(work / 'execution-list.json', {'items': execution})
    write(work / 'check-list.json', {'items': checks, 'summary': result})
    ledger = []
    for job, actual in zip(plan['tasks'], execution):
        task_checks = [x for x in checks if x['task_id'] == job['id']]
        if actual['status'] in ('failed', 'uncertain', 'invalid_output', 'failed_after_retries', 'retryable'):
            state = 'blocked'
        elif actual['status'] == 'running': state = 'running'
        elif actual['status'] != 'success': state = 'not_done'
        elif any(x['verdict'] == 'fail' for x in task_checks): state = 'check_failed'
        elif any(x['verdict'] == 'unknown' for x in task_checks): state = 'unverified'
        else: state = 'verified'
        completed = ''
        if actual['status'] == 'success':
            completed = 'PNG file decoded and SHA-256 checked; visual/human acceptance is separate.'
        if state == 'verified':
            completed += ' Every planned criterion has a recorded observation, reviewer and method.'
        if state == 'blocked' and actual['events']:
            completed = 'Execution did not complete: ' + json.dumps(actual['events'][-1], ensure_ascii=False)
        ledger.append({'task_id': job['id'], 'requirement': job.get('name', job['id']),
                       'requirement_source': plan['context'], 'acceptance': job['checks'],
                       'status': state, 'actual_execution_status': actual['status'],
                       'completed_what_and_basis': completed, 'evidence': actual['evidence'],
                       'checks': task_checks, 'events': actual['events']})
    write(work / 'task-ledger.json', {'context': plan['context'], 'items': ledger, 'summary': result})
    def cell(x): return str(x).replace('|', '\\|').replace('\n', '<br>')
    def markdown(name, headers, rows):
        lines = ['# ' + name, '', '| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)]
        lines += ['| ' + ' | '.join(cell(c) for c in row) + ' |' for row in rows]
        path = v.under(work / (name + '.md'))
        v.need(not path.is_symlink(), 'markdown path is a symlink')
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    markdown('task-list', ['任务', '应做', '通过条件'],
             [(j['id'], j.get('name', j['id']), json.dumps(j['checks'], ensure_ascii=False)) for j in plan['tasks']])
    markdown('execution-list', ['任务', '执行状态', '次数', '实际产物证据'],
             [(x['task_id'], x['status'], x['attempts'], x['evidence']) for x in execution])
    markdown('check-list', ['任务', '检查项', '标准', '观察', '结果', '检查者'],
             [(x['task_id'], x['criterion_id'], x['expected'], x['observed'], x['verdict'], x['reviewer']) for x in checks])
    labels = {'not_done': '未做', 'running': '执行中', 'blocked': '受阻/待核实',
              'unverified': '已执行，未验证', 'check_failed': '检查未通过', 'verified': '已完成检查'}
    markdown('task-ledger', ['任务/要求', '验收标准', '状态', '实际完成及依据', '证据'],
             [(x['task_id'] + ' / ' + x['requirement'], json.dumps(x['acceptance'], ensure_ascii=False),
               labels[x['status']], x['completed_what_and_basis'], x['evidence']) for x in ledger])
    return result


def official_plan(b, jobs):
    by_id = {s['id']: s for s in b['schemes']}
    return make_plan(b['stage'], [
        {'id': j['id'], 'name': by_id[j['id']]['name'], 'prompt': v.sent_prompt(by_id[j['id']]),
         'references': j['content']['references'], 'output': j['path'], 'checks': by_id[j['id']]['checklist'],
         'tool': j['tool'], 'arguments': j['arguments']}
        for j in jobs], {'bundle_hash': v.hash_obj(b), 'decisions': b.get('decisions', {}),
                        'prior_stage_checked_by': 'director_validate.selected_parent'}, 'codex-built-in-imagegen')


def prepare(spec):
    stage, count = expected_stage(spec)
    v.need(len(spec['jobs']) == count, 'job count mismatch: expected ' + str(count))
    work = v.under(spec['work'])
    jobs = []
    for entry in spec['jobs']:
        refs = [{'path': str(Path(f).resolve()), 'sha256': v.digest(Path(f).read_bytes())}
                for f in entry['reference_paths']]
        for ref in refs: v.descriptor(ref, image=True)
        v.under(entry['output'])
        arguments = {'prompt': entry['prompt']}
        if refs: arguments['referenced_image_paths'] = [r['path'] for r in refs]
        jobs.append({'id': entry['id'], 'name': entry.get('name', entry['id']), 'prompt': entry['prompt'],
                     'references': refs, 'output': entry['output'], 'checks': entry['checks'],
                     'tool': 'image_gen.imagegen', 'arguments': arguments})
    plan = make_plan(stage, jobs, {k: spec[k] for k in ('current_stage', 'next_stage', 'decision', 'expected_count')},
                     'codex-built-in-imagegen')
    plan['context']['modifications'] = spec.get('modifications', [])
    if spec.get('override'): plan['context']['override'] = spec['override']
    if stage == 'refinement' and len({j['prompt'] for j in jobs}) != 1:
        quoted(spec.get('distinct_prompts'), 'distinct prompt user request')
        plan['context']['distinct_prompts'] = spec['distinct_prompts']
    validate_assets(plan)
    frozen(work / 'task-list.json', plan)
    requests = [{'id': j['id'], 'tool': j['tool'], 'arguments': j['arguments']} for j in jobs]
    frozen(work / 'checked-requests.json', requests)
    receipt_path = work / 'execution-receipt.json'
    if not receipt_path.exists():
        write(receipt_path, {'backend': plan['backend'], 'plan_hash': v.hash_obj(plan), 'items': {
            j['id']: {'status': 'not_started', 'attempts': 0, 'events': []} for j in jobs}})
    receipt = v.read_json(receipt_path)
    v.need(receipt['plan_hash'] == v.hash_obj(plan), 'receipt belongs to another plan')
    materialize(work, plan, receipt)
    return {'status': 'prepared', 'calls': 0, 'work': str(work), 'requests': str(work / 'checked-requests.json')}


def event(work, event):
    work = v.under(work)
    # Serialize asynchronous callbacks; image calls themselves run outside this lock.
    from director import locked
    with locked(work):
        plan = v.read_json(work / 'task-list.json')
        validate_assets(plan)
        receipt_path = work / 'execution-receipt.json'
        if not receipt_path.exists(): receipt_path = work / 'receipt.json'
        receipt = v.read_json(receipt_path)
        v.need(receipt['plan_hash'] == v.hash_obj(plan), 'receipt belongs to another plan')
        sid = event['task_id']; item = receipt['items'][sid]
        job = next(j for j in plan['tasks'] if j['id'] == sid)
        state = event['status']
        v.need(state in ('running', 'success', 'failed', 'uncertain'), 'invalid event status')
        if state == 'running':
            v.need(item['status'] == 'not_started', 'already dispatched; reconcile instead of repeating')
            v.need(not Path(job['output']).exists(), 'unreconciled output already exists')
            item['attempts'] += 1
        else:
            v.need(item['status'] in ('running', 'uncertain'), 'result without matching dispatch')
            v.text(event.get('tool_call_id'), 'tool_call_id')
            if state == 'success':
                data = Path(event['path']).read_bytes(); info = v.image_info(data)
                v.need(info['format'] == 'PNG', 'expected PNG result')
                dest = v.under(job['output']); dest.parent.mkdir(parents=True, exist_ok=True)
                v.need(not dest.exists(), 'refuse to overwrite existing output')
                shutil.copyfile(event['path'], dest)
                item.update(path=str(dest), sha256=v.digest(data), image=info)
            else: v.text(event.get('reason'), 'failure/uncertainty reason')
        item['status'] = state; item['events'].append(event)
        write(receipt_path, receipt)
        summary = materialize(work, plan, receipt)
        if state == 'running':
            summary['tool'] = job.get('tool', 'image_gen.imagegen')
            summary['arguments'] = job.get('arguments', {'prompt': job['prompt']})
        return summary


def inspect(work, review_path=None):
    work = v.under(work); plan = v.read_json(work / 'task-list.json')
    validate_assets(plan)
    receipt_path = work / 'execution-receipt.json'
    if not receipt_path.exists(): receipt_path = work / 'receipt.json'
    receipt = v.read_json(receipt_path)
    if 'plan_hash' in receipt: v.need(receipt['plan_hash'] == v.hash_obj(plan), 'receipt identity changed')
    else: v.need(receipt.get('bundle_hash') == plan['context'].get('bundle_hash'), 'receipt identity changed')
    review = v.read_json(review_path) if review_path else None
    result = materialize(work, plan, receipt, review)
    if review is not None: write(work / 'saved-check-review.json', review)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare', 'event', 'inspect'))
    p.add_argument('path'); p.add_argument('--record'); p.add_argument('--review')
    a = p.parse_args()
    try:
        if a.command == 'prepare': result = prepare(v.read_json(a.path))
        elif a.command == 'event': result = event(a.path, v.read_json(a.record))
        else: result = inspect(a.path, a.review)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (v.Invalid, ValueError, TypeError, KeyError, OSError, StopIteration) as e:
        print(json.dumps({'status': 'rejected', 'error': str(e)}, ensure_ascii=False)); return 2


if __name__ == '__main__': raise SystemExit(main())
