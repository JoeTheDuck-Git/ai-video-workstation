#!/usr/bin/env python3
"""Read-only media review packaging and fail-closed delivery gate. No media edits."""
import argparse
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import subprocess
import uuid


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def record(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': digest(p)}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def coverage(rows, duration):
    intervals = []
    for row in rows:
        a, b = row['start'], row['end']
        if not finite(a) or not finite(b) or not 0 <= a < b <= duration + .001:
            raise ValueError('Invalid coverage interval')
        intervals.append((a, min(b, duration)))
    union = []
    for a, b in sorted(intervals):
        if union and a <= union[-1][1]:
            union[-1][1] = max(b, union[-1][1])
        else:
            union.append([a, b])
    return sum(b - a for a, b in union) / duration if duration > 0 else 0


def norm(text):
    return re.sub(r'[^\w]', '', text).lower()


def candidates(windows, duration, cues=()):
    """Navigation heuristics, never edit decisions or speech truth."""
    out = []
    seen = set()
    def add(kind, a, b, details):
        a, b = max(0, a), min(duration, b)
        if b <= a:
            return
        key = (kind, a, b, json.dumps(details, sort_keys=True))
        if key in seen:
            return
        seen.add(key)
        out.append({'id': 'Q%04d' % (len(out) + 1), 'kind': kind,
                    'start': a, 'end': b, 'details': details,
                    'status': 'open', 'action': 'review_only'})
    for window in windows:
        for w in window.get('words', []):
            a, b = w['start'], w['end']
            if not finite(a) or not finite(b) or a < 0 or b < a or b > duration + .001:
                raise ValueError('Invalid word timing')
            text = w.get('text', w.get('word', ''))
            # Broad cue: prolonged words may be intentional emphasis.
            if b - a > max(1.0, .65 * len(norm(text))):
                add('long_word', max(window['start'], a - .5), min(window['end'], b + .5),
                    {'word': text, 'word_start': a, 'word_end': b})
            elif b == a:
                add('zero_length_word', a - .5, b + .5, {'word': text})
    for i, left in enumerate(windows):
        for right in windows[i + 1:]:
            a, b = max(left['start'], right['start']), min(left['end'], right['end'])
            if b - a < 1:
                continue
            def excerpt(w):
                return norm(''.join(x.get('text', x.get('word', '')) for x in w.get('words', [])
                                    if a <= (x['start'] + x['end']) / 2 < b))
            x, y = excerpt(left), excerpt(right)
            if x and y and difflib.SequenceMatcher(None, x, y).ratio() < .75:
                add('window_disagreement', a, b, {'left': x, 'right': y})
    for cue in cues:
        a, b = cue['start'], cue['end']
        if not finite(a) or not finite(b) or not 0 <= a <= b <= duration:
            raise ValueError('Invalid supplied cue interval')
        if a == b:
            a, b = max(0, a - .5), min(duration, b + .5)
        add(cue['kind'], a, b, cue.get('details', {}))
    return out


def media_duration(path):
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=duration', '-of', 'json', str(path)], text=True))
    duration = float(probe['streams'][0]['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Invalid actual video duration')
    return duration


def runtime_root():
    locator = Path(__file__).resolve().parents[1] / 'runtime-root.json'
    if locator.exists():
        root = Path(json.loads(locator.read_text())['runtime_root']).resolve()
        if not (root / 'WORKSTATION_PROMPTS.md').is_file():
            raise ValueError('Installed runtime snapshot missing; reinstall Skills')
        return root
    return Path(__file__).resolve().parents[3]


def required_versions():
    root = runtime_root()
    return [root / x for x in [
        'skills/spoken-edit-review/SKILL.md',
        'skills/spoken-edit-review/references/independent-review.md',
        'skills/reference-guided-cut-planner/SKILL.md',
        'WORKSTATION_PROMPTS.md', 'docs/reference-editing-lab/EDITING_PROMPT.md',
        'docs/reference-editing-lab/protected-phrases.json',
        'docs/reference-editing-lab/CONTRACT.md',
        'scripts/lab/deliver-spoken-cut.py', 'scripts/lab/plan-spoken-cut.py',
        'skills/spoken-edit-review/scripts/source_review.py',
        'skills/spoken-edit-review/references/source-review.md',
        'skills/spoken-edit-review/references/preview-mode.md']]


def prepare(config):
    duration = config['duration']
    if not finite(duration) or duration <= 0:
        raise ValueError('Positive finite duration required')
    required = {'source', 'export', 'map', 'asr', 'technical'}
    if not required <= config['files'].keys() or not config.get('versions') or not config.get('editor_id'):
        raise ValueError('Source/export/map/asr/technical, versions and editor identity required')
    files = {k: record(v) for k, v in config['files'].items()}
    implementations = config.get('implementations', {})
    if not {'renderer', 'technical_qc', 'asr'} <= implementations.keys():
        raise ValueError('Renderer, technical QC and ASR implementation paths required')
    implementations = {k: record(v) for k, v in implementations.items()}
    versions = [record(v) for v in config['versions']] + [record(v) for v in required_versions()]
    actual_duration = media_duration(files['export']['path'])
    mapped_duration = read(files['map']['path']).get('total_seconds')
    if not finite(mapped_duration) or abs(mapped_duration - actual_duration) > .04 or abs(duration - actual_duration) > .001:
        raise ValueError('Configured/map duration disagrees with actual video')
    duration = actual_duration
    # Always bind the actual gate implementation, regardless of supplied versions.
    versions.append(record(__file__))
    windows = read(files['asr']['path'])
    if not isinstance(windows, list):
        raise ValueError('ASR must be output-time windows with start/end/words')
    asr_coverage = coverage(windows, duration)
    cues = read(files['cues']['path']) if 'cues' in files else []
    return {'schema': 1, 'run_id': str(uuid.uuid4()), 'editor_id': config['editor_id'],
            'duration': duration, 'files': files, 'versions': versions, 'implementations': implementations,
            'asr_coverage': asr_coverage, 'issues': candidates(windows, duration, cues),
            'status': 'awaiting_independent_review', 'scope': 'all retained interiors, joins, start and farewell'}


def intact(rec):
    try:
        return digest(rec['path']) == rec['sha256']
    except (OSError, KeyError, TypeError):
        return False


def evidence_preview_check(report,duration,issues,decision_key):
    """Explicit independent evidence review, never an audio or editorial final pass."""
    errors=[];valid=[];evidence=report.get('evidence',{})
    if report.get('actual_audio_review') is not False or report.get('status')!='needs_review':errors.append('preview_labels_required')
    if report.get('audio_review')!=[]:errors.append('preview_cannot_claim_audio_review')
    if report.get('evidence_review_complete') is not True:errors.append('preview_review_incomplete')
    for row in report.get('evidence_review',[]):
        if row.get('method')!='codex_evidence_review' or not row.get('finding') or row.get('evidence_id') not in evidence or not intact(evidence[row['evidence_id']]):
            errors.append('preview_range_evidence_missing')
        else:valid.append(row)
    try:covered=coverage(valid,duration)
    except (ValueError,KeyError,TypeError):covered=0;errors.append('preview_ranges_invalid')
    if covered<1-1e-9:errors.append('preview_evidence_coverage_incomplete')
    for q in issues:
        d=report.get(decision_key,{}).get(q['id'],{})
        if d.get('action') not in ('keep','candidate_change','already_excluded') or not d.get('reason') or d.get('evidence_id') not in evidence or not intact(evidence[d['evidence_id']]):
            errors.append('preview_candidate_unaddressed:'+q['id'])
    if not isinstance(report.get('open_findings'),list) or not report['open_findings']:
        errors.append('preview_audio_limitation_not_recorded')
    return covered,errors


def source_review_blockers(packet,mode="final"):
    import importlib.util
    path = runtime_root()/'scripts/lab/plan-spoken-cut.py'
    spec = importlib.util.spec_from_file_location('source_plan_check', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    try:
        plan = module.validate_authorized_plan(packet['files']['map']['path'],allow_preview=mode=='preview')
        if digest(plan['source']) != packet['files']['source']['sha256']:
            return ['source_review_source_mismatch']
        return []
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
        return ['source_review_missing_stale_or_unapproved']


def gate(packet, report, dispatch, mode="final"):
    if mode not in ("final","preview"):raise ValueError("Invalid gate mode")
    blockers = list(source_review_blockers(packet) if mode=="final" else source_review_blockers(packet,mode))
    def require(ok, reason):
        if not ok:
            blockers.append(reason)
    require(packet.get('schema') == 1, 'unsupported_packet')
    require({'source', 'export', 'map', 'asr', 'technical'} <= packet['files'].keys(), 'required_inputs_missing')
    require({'renderer', 'technical_qc', 'asr'} <= packet.get('implementations', {}).keys(), 'required_implementations_missing')
    bound_versions = {r.get('path') for r in packet['versions']}
    require({str(v.resolve()) for v in required_versions()} <= bound_versions, 'required_rules_missing')
    for rec in list(packet['files'].values()) + packet['versions'] + list(packet.get('implementations', {}).values()):
        require(intact(rec), 'changed_or_missing:' + rec.get('path', '?'))
    require(abs(media_duration(packet['files']['export']['path']) - packet['duration']) <= .001, 'duration_changed')
    cues = read(packet['files']['cues']['path']) if 'cues' in packet['files'] else []
    require(packet['issues'] == candidates(read(packet['files']['asr']['path']), packet['duration'], cues), 'candidate_queue_changed')
    require(dispatch.get('run_id') == packet['run_id'] and dispatch.get('tool') == 'collaboration.spawn_agent', 'missing_dispatch')
    require(dispatch.get('agent_id') and dispatch.get('agent_id') != packet['editor_id'], 'reviewer_not_independent')
    require(report.get('reviewer_id') == dispatch.get('agent_id') and report.get('run_id') == packet['run_id'], 'review_identity_or_run_mismatch')
    require(report.get('packet_sha256') == dispatch.get('packet_sha256'), 'packet_attestation_mismatch')
    # Compare content, not JSON serialization chosen by callers.
    require(dispatch.get('packet_content_sha256') == hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest(), 'packet_changed_after_dispatch')
    require(bool(dispatch.get('tool_receipt')) and intact(dispatch['tool_receipt']), 'dispatch_receipt_missing_or_changed')
    require(bool(dispatch.get('completion_receipt')) and intact(dispatch['completion_receipt']), 'completion_receipt_missing_or_changed')
    if mode=='final':require(report.get('status') == 'pass', 'content_review_not_pass')
    evidence = report.get('evidence', {})
    for key, rec in evidence.items():
        require(intact(rec), 'review_evidence_changed:' + key)
    def evidenced(rows):
        valid = []
        for row in rows:
            if row.get('evidence_id') not in evidence or not intact(evidence[row['evidence_id']]):
                blockers.append('missing_range_evidence')
            elif row.get('method') not in ('human_listening', 'audio_understanding'):
                blockers.append('asr_is_not_audio_review')
            elif not row.get('finding'):
                blockers.append('missing_range_finding')
            else:
                valid.append(row)
        return valid
    audio_rows = evidenced(report.get('audio_review', []))
    try:
        audio_coverage = coverage(audio_rows, packet['duration'])
    except (ValueError, KeyError, TypeError):
        audio_coverage = 0
        blockers.append('invalid_audio_coverage')
    assisted=0
    if mode=='final':
        require(audio_coverage >= 1 - 1e-9, 'incomplete_audio_review')
        require(report.get('interiors_reviewed') is True and report.get('joins_and_ending_reviewed') is True, 'missing_scope_review')
        resolutions = report.get('issue_resolutions', {})
        for issue in packet['issues']:
            res = resolutions.get(issue['id'], {})
            # Fixes change the export/map; a new packet must be prepared, never close as fixed here.
            require(res.get('disposition') in ('intentional_keep', 'false_positive') and bool(res.get('reason'))
                    and res.get('evidence_id') in evidence, 'unresolved_candidate:' + issue['id'])
        require(not report.get('open_findings'), 'reviewer_open_findings')
    else:
        assisted,errors=evidence_preview_check(report,packet['duration'],packet['issues'],'preview_decisions')
        blockers.extend(errors)
        require(report.get('interiors_reviewed') is True and report.get('joins_and_ending_reviewed') is True,'missing_scope_review')
    technical = read(packet['files']['technical']['path'])
    if mode=='preview':
        require(technical.get('export_sha256')==packet['files']['export']['sha256'] and technical.get('map_sha256')==packet['files']['map']['sha256'],'preview_technical_artifact_mismatch')
    checks = technical.get('checks', [])
    require(technical.get('all_technical_checks_pass') is True and bool(checks)
            and all(c.get('passed') is True for c in checks), 'technical_not_pass')
    return {'run_id': packet['run_id'], 'final_pass': not blockers and mode=='final',
            'preview_allowed':not blockers and mode=='preview',
            'mode':mode,'actual_audio_review':audio_coverage>=1-1e-9 if mode=='final' else False,
            'evidence_review_coverage':assisted,'unresolved_findings':report.get('open_findings',[]),
            'delivery': ('final' if mode=='final' else 'evidence_reviewed_preview') if not blockers else 'blocked',
            'technical_pass': technical.get('all_technical_checks_pass') is True,
            'content_status': report.get('status', 'needs_review') if mode=='final' else 'needs_review',
            'asr_coverage': packet['asr_coverage'], 'audio_review_coverage': audio_coverage,
            'blockers': sorted(set(blockers)),
            'trust_boundary': 'Host must capture real tool receipts and reviewer output; JSON cannot authenticate an agent or prove listening.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('config'); p.add_argument('output')
    g = sub.add_parser('gate'); g.add_argument('packet'); g.add_argument('report'); g.add_argument('dispatch'); g.add_argument('output');g.add_argument('--mode',choices=['final','preview'],default='final')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            write(args.output, prepare(read(args.config))); return 0
        dispatch = read(args.dispatch)
        if dispatch.get('packet_sha256') != digest(args.packet):
            raise ValueError('Packet file differs from dispatched packet')
        result = gate(read(args.packet), read(args.report), dispatch,args.mode)
        write(args.output, result)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['final_pass'] or result['preview_allowed'] else 2
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as e:
        print('Review blocked: ' + str(e), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
