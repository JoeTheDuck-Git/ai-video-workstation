#!/usr/bin/env python3
"""Pre-cut source review. Candidate navigation only; no automatic edit decisions."""
import argparse
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import uuid

spec=importlib.util.spec_from_file_location('gate_utils',Path(__file__).with_name('review_gate.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
DEFAULTS={'priority_threshold':.90,'min_chars':6,'window_seconds':12.,'phrase_chars':12,'pause_seconds':.4,'noise_db':-35}


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text).casefold() if c.isalnum())


def settings(config):
    c={**DEFAULTS,**config}
    if not .5<=c['priority_threshold']<=1 or not 4<=c['min_chars']<=30 or not 1<=c['window_seconds']<=60 or not c['min_chars']<=c['phrase_chars']<=48 or not .1<=c['pause_seconds']<=3 or not -80<=c['noise_db']<=-10:
        raise ValueError('Invalid detector settings')
    return c


def segments(raw,duration):
    rows=raw.get('segments',[]) if isinstance(raw,dict) else raw
    out=[]
    for i,s in enumerate(rows):
        a,b=s['start'],s['end']
        if not g.finite(a) or not g.finite(b) or not 0<=a<=b<=duration+.001:raise ValueError('Invalid source segment timing')
        words=[]
        for w in s.get('words',[]):
            x,y=w['start'],w['end']
            if not g.finite(x) or not g.finite(y) or not 0<=x<=y<=duration+.001:raise ValueError('Invalid source word timing')
            words.append({**w,'text':w.get('word',w.get('text','')),'confidence':w.get('probability',w.get('confidence'))})
        out.append({'id':'S%04d'%i,'start':a,'end':b,'text':s.get('text',''),'words':words,
                    'confidence':s.get('avg_logprob'), 'confidence_kind':'avg_logprob' if 'avg_logprob' in s else None})
    return out


def detect(raw,duration,config=None,pauses=()):
    c=settings(config or {});segs=segments(raw,duration);units=[]
    for s in segs:
        units.append(s)
        # Nonoverlapping word-bounded phrase blocks supplement whole-segment comparisons.
        buf=[]
        for w in s['words']:
            buf.append(w)
            if len(normalized(''.join(x['text'] for x in buf)))>=c['phrase_chars']:
                units.append({'start':buf[0]['start'],'end':buf[-1]['end'],'text':''.join(x['text'] for x in buf)});buf=[]
        if buf:units.append({'start':buf[0]['start'],'end':buf[-1]['end'],'text':''.join(x['text'] for x in buf)})
    units=sorted({(u['start'],u['end'],u['text']):u for u in units}.values(),key=lambda u:(u['start'],u['end']))
    out=[];seen=set()
    def add(kind,left,right,reason,score=None):
        a,b=min(left['start'],right['start']),max(left['end'],right['end'])
        key=(kind,a,b,left['text'],right['text'])
        if key in seen:return
        seen.add(key)
        out.append({'id':'R%04d'%(len(out)+1),'kind':kind,'start':a,'end':b,
          'left':{k:left[k] for k in ['start','end','text']},'right':{k:right[k] for k in ['start','end','text']},
          'reason':reason,'text_similarity':score,'semantic_score':None,
          'priority':'high' if score is not None and score>=c['priority_threshold'] else 'review',
          'context':{'start':max(0,a-2),'end':min(duration,b+2),'media':'source'},'status':'needs_review','action':'review_only'})
    for i,left in enumerate(units):
        x=normalized(left['text'])
        if len(x)<c['min_chars']:continue
        for right in units[i+1:]:
            if right['start']-left['end']>c['window_seconds']:break
            if right['start']<left['end'] or right['end']<=left['end']:continue
            y=normalized(right['text'])
            if len(y)<c['min_chars']:continue
            score=difflib.SequenceMatcher(None,x,y,autojunk=False).ratio()
            if score>=c['priority_threshold']:
                add('text_repeat',left,right,'Character sequence similarity reached configurable priority threshold; not error probability',score)
            else:
                prefix=0
                for a,b in zip(x,y):
                    if a!=b:break
                    prefix+=1
                if prefix>=4:
                    add('partial_restart',left,right,'Shared initial >=4 normalized characters; possible restart or intentional repetition',score)
    for s in segs:
        for w in s['words']:
            if w['end']-w['start']>max(1.,.65*len(normalized(w['text']))):
                add('timing_anomaly',s,{'start':w['start'],'end':w['end'],'text':w['text']},'Abnormally long word: ASR may hide pause, omitted words or retake; not a phoneme boundary')
    for a,b in pauses:
        if not g.finite(a) or not g.finite(b) or not 0<=a<b<=duration+.001:raise ValueError('Invalid measured pause')
        if b-a<c['pause_seconds']:continue
        before=[u for u in units if u['start']<a and u['end']>=a-3]
        after=[u for u in units if u['end']>b and u['start']<=b+3]
        if before and after:
            left=max(before,key=lambda u:u['start']);right=min(after,key=lambda u:u['end'])
            add('pause_restart_or_rephrase',left,right,'Measured low energy %.3f-%.3f; review restart/rephrase/breath even below text threshold'%(a,b))
    return {'settings':c,'segments':segs,'candidates':out,'executable_cuts':None,
      'limits':'ASR output is preserved without editorial cleanup, not guaranteed verbatim. No semantic model or listening performed. Below threshold is not a pass.'}


def scan_pauses(source,duration,c):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',source,'-vn','-af',
        'silencedetect=noise=%sdB:d=%s'%(c['noise_db'],c['pause_seconds']),'-f','null','-'],capture_output=True,text=True)
    if r.returncode:raise ValueError('Source audio pause scan failed')
    starts=[float(x) for x in re.findall(r'silence_start: ([0-9.]+)',r.stderr)]
    ends=[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',r.stderr)]
    pauses=[(a,min(ends[i] if i<len(ends) else duration,duration)) for i,a in enumerate(starts) if a<duration]
    return pauses,r.stderr


def prepare(config):
    files={k:g.record(v) for k,v in config['files'].items()}
    if not {'source','raw_asr','asr_code'}<=files.keys():raise ValueError('Source, raw ASR and ASR code required')
    duration=g.media_duration(files['source']['path']);c=settings(config.get('settings',{}))
    pauses,log=scan_pauses(files['source']['path'],duration,c)
    data=detect(g.read(files['raw_asr']['path']),duration,c,pauses)
    # Raw transcript remains a byte-identical bound file; normalized strings are only for scoring.
    return {'schema':1,'run_id':str(uuid.uuid4()),'editor_id':config['editor_id'],'files':files,
      'duration':duration,'versions':[g.record(v) for v in g.required_versions()]+[g.record(__file__),g.record(Path(__file__).with_name('review_gate.py'))],
      'pause_scan':{'method':'ffmpeg silencedetect, not VAD/listening','intervals':pauses,'log':log},**data}


def check(packet,review,dispatch,mode="final"):
    if mode not in ("final","preview"):raise ValueError("Invalid review mode")
    blockers=[]
    def need(ok,why):
        if not ok:blockers.append(why)
    need(packet.get('schema')==1,'source_schema')
    need({'source','raw_asr','asr_code'}<=packet['files'].keys(),'source_inputs_missing')
    for rec in list(packet['files'].values())+packet['versions']:need(g.intact(rec),'stale_source_evidence')
    need({str(p.resolve()) for p in g.required_versions()}<={r['path'] for r in packet['versions']},'source_rules_missing')
    need(abs(g.media_duration(packet['files']['source']['path'])-packet['duration'])<.001,'source_duration')
    expected=detect(g.read(packet['files']['raw_asr']['path']),packet['duration'],packet['settings'],packet['pause_scan']['intervals'])
    need(packet['candidates']==expected['candidates'],'source_queue_changed')
    need(dispatch.get('tool')=='collaboration.spawn_agent' and dispatch.get('run_id')==packet['run_id'],'source_dispatch')
    need(dispatch.get('agent_id') and dispatch['agent_id']!=packet['editor_id'] and review.get('reviewer_id')==dispatch['agent_id'],'source_independence')
    need(review.get('run_id')==packet['run_id'] and review.get('packet_sha256')==dispatch.get('packet_sha256'),'source_review_binding')
    need(dispatch.get('packet_content_sha256')==g.hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest(),'source_packet_changed')
    for key in ['tool_receipt','blind_receipt','completion_receipt']:need(bool(dispatch.get(key)) and g.intact(dispatch[key]),'source_'+key)
    blind=review.get('blind_assessment',{})
    need(dispatch.get('blind_assessment_sha256') and dispatch.get('blind_assessment_sha256')==blind.get('record',{}).get('sha256'),'blind_assessment_changed')
    need(bool(blind.get('record')) and g.intact(blind['record']) and blind.get('saw_editor_recommendations') is False,'blind_review_missing')
    if mode=='final':need(review.get('status')=='pass','source_needs_review')
    evidence=review.get('evidence',{});valid=[]
    for rec in evidence.values():need(g.intact(rec),'source_review_evidence_changed')
    for row in review.get('audio_review',[]):
        ok=row.get('method') in ('human_listening','audio_understanding') and row.get('evidence_id') in evidence and g.intact(evidence[row['evidence_id']]) and bool(row.get('finding'))
        need(ok,'source_audio_method_or_evidence')
        if ok:valid.append(row)
    try:covered=g.coverage(valid,packet['duration'])
    except (ValueError,KeyError,TypeError):covered=0
    if mode=='final':
        need(covered>=1-1e-9,'source_audio_coverage')
        for q in packet['candidates']:
            d=review.get('decisions',{}).get(q['id'],{})
            need(d.get('classification') in ['retake','intentional_emphasis','normal_breath','transcription_error'] and d.get('evidence_id') in evidence and bool(d.get('reason')),'unresolved_source:'+q['id'])
            if d.get('classification')=='retake':
                need(bool(d.get('selected_take_reason')) and d.get('selected_take') in ['left','right','other'],'unselected_take:'+q['id'])
        need(not review.get('open_findings'),'source_open_findings')
        assisted=0
    else:
        assisted, errors=g.evidence_preview_check(review,packet['duration'],packet['candidates'],'preview_decisions')
        blockers.extend(errors)
    return {'run_id':packet['run_id'],'mode':mode,'approved_for_cut_planning':not blockers,
        'actual_audio_review':covered>=1-1e-9 if mode=='final' else False,
        'content_status':review.get('status','needs_review') if mode=='final' else 'needs_review',
        'final_pass':not blockers if mode=='final' else False,
        'evidence_review_coverage':assisted,'audio_review_coverage':covered,
        'unresolved_findings':review.get('open_findings',[]),
        'blockers':sorted(set(blockers)),'executable_cuts':None}


def authorize(packet_path,review_path,dispatch_path,mode="final"):
    packet,review,dispatch=map(g.read,[packet_path,review_path,dispatch_path])
    if g.digest(packet_path)!=dispatch.get('packet_sha256'):raise ValueError('Source packet file changed')
    return check(packet,review,dispatch,mode)


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('prepare');a.add_argument('config');a.add_argument('output')
    a=s.add_parser('authorize');a.add_argument('packet');a.add_argument('review');a.add_argument('dispatch');a.add_argument('output');a.add_argument('--mode',choices=['final','preview'],default='final')
    a=p.parse_args()
    try:
        if a.cmd=='prepare':g.write(a.output,prepare(g.read(a.config)));return 0
        result=authorize(a.packet,a.review,a.dispatch,a.mode);g.write(a.output,result);print(json.dumps(result));return 0 if result['approved_for_cut_planning'] else 2
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as e:
        g.write(a.output,{'approved_for_cut_planning':False,'executable_cuts':None,'error':str(e)});return 2
if __name__=='__main__':raise SystemExit(main())
