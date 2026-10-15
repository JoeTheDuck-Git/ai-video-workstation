#!/usr/bin/env python3
"""Authorize an explicit source map only after independent pre-cut review. Never render."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import math

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('source_review',ROOT/'skills/spoken-edit-review/scripts/source_review.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def validate_plan(plan,packet):
    from fractions import Fraction
    if s.g.digest(plan['source'])!=packet['files']['source']['sha256']:raise ValueError('Plan source mismatch')
    rate=Fraction(plan['fps']);fps=float(rate);pos=0
    actual=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,r_frame_rate','-of','json',plan['source']],text=True))['streams'][0]
    if rate!=Fraction(actual['avg_frame_rate']) or Fraction(actual['r_frame_rate'])!=rate:raise ValueError('Source FPS mismatch or unsupported VFR; inspect real PTS before planning')
    if not math.isfinite(fps) or fps<=0:raise ValueError('Invalid fps')
    if not plan.get('clips'):raise ValueError('No planned source clips')
    for c in plan['clips']:
        if c['kind']!='source':raise ValueError('Only original moving source clips supported')
        lo,hi=c['source_in_frame'],c['source_out_frame']
        if type(lo)!=int or type(hi)!=int or not 0<=lo<hi or hi/fps>packet['duration']+.04:raise ValueError('Invalid source bounds')
        if c['timeline_in_frame']!=pos or c['duration_frames']!=hi-lo:raise ValueError('Invalid map continuity')
        pos+=hi-lo
    if not s.g.finite(plan['total_seconds']) or abs(plan['total_seconds']-pos/fps)>.001:raise ValueError('Invalid map duration')


def validate_decisions(plan,packet,review):
    from fractions import Fraction
    fps=float(Fraction(plan['fps']))
    spans=[(c['source_in_frame']/fps,c['source_out_frame']/fps) for c in plan['clips']]
    def intervals(rows):
        if not rows:raise ValueError('Retake needs confirmed source intervals before executable cuts')
        for a,b in rows:
            if not s.g.finite(a) or not s.g.finite(b) or not 0<=a<b<=packet['duration']:
                raise ValueError('Invalid confirmed decision interval')
        return rows
    for q in packet['candidates']:
        decision=review['decisions'][q['id']]
        if decision['classification']!='retake':continue
        if decision.get('boundary_status')!='verified':raise ValueError('Retake boundaries not acoustically verified')
        remove=intervals(decision.get('confirmed_remove_ranges',[]))
        keep=intervals(decision.get('confirmed_keep_ranges',[]))
        for a,b in remove:
            if any(min(z,b)-max(x,a)>1/fps for x,z in spans):raise ValueError('Map still retains rejected retake')
        for a,b in keep:
            parts=[{'start':max(x,a)-a,'end':min(z,b)-a} for x,z in spans if min(z,b)>max(x,a)]
            kept=sum(v['end']-v['start'] for v in parts)
            union=s.g.coverage(parts,b-a)*(b-a)
            if kept-union>1e-9 or abs(union-(b-a))>1/fps:raise ValueError('Map loses or duplicates selected complete take')


def validate_boundary(c,packet,review):
    rec=c.get('boundary_evidence')
    if c.get('boundary_status')!='verified' or not rec or not s.g.intact(rec):
        raise ValueError('Unverified executable boundary')
    evidence=s.g.read(rec['path'])
    if evidence.get('source_sha256')!=packet['files']['source']['sha256'] or evidence.get('source_in_frame')!=c['source_in_frame'] or evidence.get('source_out_frame')!=c['source_out_frame']:
        raise ValueError('Boundary evidence does not bind source and exact frames')
    if evidence.get('method') not in ['human_listening','audio_understanding'] or evidence.get('reviewer_id')!=review.get('reviewer_id') or not evidence.get('finding'):
        raise ValueError('Boundary lacks independent acoustic evidence')


def content_hash(plan):
    return s.g.hashlib.sha256(json.dumps({k:v for k,v in plan.items() if k!='source_review'},sort_keys=True).encode()).hexdigest()


def validate_preview_plan(plan,packet,review):
    if plan.get('review_mode')!='preview' or plan.get('actual_audio_review') is not False or plan.get('content_status')!='needs_review' or plan.get('final_pass') is not False:
        raise ValueError('Preview labels required on map')
    if review.get('preview_map_content_sha256')!=content_hash(plan):raise ValueError('Preview map not independently reviewed')
    previous=0
    for c in plan['clips']:
        if c['source_in_frame']<previous:raise ValueError('Preview source repeated or reordered without supported policy')
        previous=c['source_out_frame']
        rec=c.get('boundary_evidence',{})
        if c.get('boundary_status')!='candidate_evidence_reviewed' or not s.g.intact(rec):raise ValueError('Missing preview boundary evidence')
        e=s.g.read(rec['path'])
        if e.get('source_sha256')!=packet['files']['source']['sha256'] or e.get('source_in_frame')!=c['source_in_frame'] or e.get('source_out_frame')!=c['source_out_frame']:
            raise ValueError('Preview evidence source/frame mismatch')
        if e.get('method')!='codex_evidence_review' or e.get('actual_audio_review') is not False or not e.get('finding') or e.get('reviewer_id')!=review.get('reviewer_id'):
            raise ValueError('Preview boundary evidence method/reviewer mismatch')
        if not e.get('inputs') or not all(s.g.intact(r) for r in e['inputs']):raise ValueError('Stale preview boundary inputs')
    if not plan.get('unresolved_findings'):raise ValueError('Preview limitations missing')


def approve(packet_path,review_path,dispatch_path,plan_path,mode="final"):
    result=s.authorize(packet_path,review_path,dispatch_path,mode)
    if not result['approved_for_cut_planning']:return None,result
    packet=s.g.read(packet_path);plan=s.g.read(plan_path);validate_plan(plan,packet)
    if mode=='preview':
        validate_preview_plan(plan,packet,s.g.read(review_path))
    else:
        if plan.get('review_mode')=='preview':raise ValueError('Preview map cannot authorize final')
        validate_decisions(plan,packet,s.g.read(review_path))
        for c in plan['clips']:
            validate_boundary(c,packet,s.g.read(review_path))
    plan.pop('source_review',None)
    plan_hash=s.g.hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
    plan['source_review']={'mode':mode,'map_content_sha256':plan_hash,'run_id':packet['run_id'],'packet':s.g.record(packet_path),'review':s.g.record(review_path),'dispatch':s.g.record(dispatch_path)}
    return plan,result


def validate_authorized_plan(path,allow_preview=False):
    plan=s.g.read(path);binding=plan.get('source_review',{})
    content={k:v for k,v in plan.items() if k!='source_review'}
    if binding.get('map_content_sha256')!=s.g.hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest():raise ValueError('Executable map changed after authorization')
    for key in ['packet','review','dispatch']:
        if not binding.get(key) or not s.g.intact(binding[key]):raise ValueError('Source review binding missing/stale')
    packet=s.g.read(binding['packet']['path'])
    if binding.get('run_id')!=packet['run_id']:raise ValueError('Source review run mismatch')
    mode=binding.get('mode','final')
    if mode not in ('final','preview'):raise ValueError('Invalid bound map mode')
    if mode=='preview' and not allow_preview:raise ValueError('Preview map cannot authorize final')
    result=s.authorize(*[binding[k]['path'] for k in ['packet','review','dispatch']],mode=mode)
    if not result['approved_for_cut_planning']:raise ValueError('Source review not approved')
    validate_plan(plan,packet)
    if mode=='preview':
        validate_preview_plan(plan,packet,s.g.read(binding['review']['path']))
    else:
        if plan.get('review_mode')=='preview':raise ValueError('Preview map cannot authorize final')
        validate_decisions(plan,packet,s.g.read(binding['review']['path']))
        for c in plan['clips']:
            validate_boundary(c,packet,s.g.read(binding['review']['path']))
    return plan


def main():
    p=argparse.ArgumentParser();p.add_argument('packet');p.add_argument('review');p.add_argument('dispatch');p.add_argument('proposed_map');p.add_argument('output');p.add_argument('--mode',choices=['final','preview'],default='final');a=p.parse_args()
    try:
        plan,result=approve(a.packet,a.review,a.dispatch,a.proposed_map,a.mode)
        s.g.write(a.output,{'approved':plan is not None,'map':plan,'review_result':result})
        if plan is None:
            Path(str(a.output)+'.map.json').unlink(missing_ok=True)
            return 2
        # JSON envelope is not executable: explicit map output has bound review.
        s.g.write(str(a.output)+'.map.json',plan);return 0
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as e:
        s.g.write(a.output,{'approved':False,'map':None,'error':str(e)})
        Path(str(a.output)+'.map.json').unlink(missing_ok=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
