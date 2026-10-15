#!/usr/bin/env python3
"""Non-destructive transient navigation; NOT a mouth-noise classifier or editor."""
import argparse, hashlib, json, subprocess, wave
from pathlib import Path
from fractions import Fraction
import numpy as np

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def record(p): return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def run(args): return subprocess.check_output(args,stderr=subprocess.PIPE)
def pcm(p): return np.frombuffer(run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-ac','1','-ar','24000','-f','f32le','-']),dtype='<f4')

def source_pieces(m,start,end):
    fps=float(Fraction(m['fps'])); result=[]
    for c in m['clips']:
        a=c['timeline_in_frame']/fps; b=a+c['duration_frames']/fps
        lo,hi=max(start,a),min(end,b)
        if hi>lo:
            src=c['source_in_frame']/fps
            result.append({'clip_id':c['id'],'output_start':lo,'output_end':hi,'source_start':src+lo-a,'source_end':src+hi-a})
    return result

def protection(a,b,windows):
    words=[w for q in windows for w in q.get('words',[]) if float(w['start'])<b+.08 and float(w['end'])>a-.08]
    if words: return 'protected_word_or_tail', [w.get('text',w.get('word','')) for w in words]
    spans=sorted((float(q['start']),float(q['end'])) for q in windows)
    cursor=a
    for lo,hi in spans:
        if lo<=cursor: cursor=max(cursor,hi)
    if cursor<b: return 'protected_unknown_coverage',[]
    return 'asr_gap_candidate_not_confirmed_non_speech',[]

def detect(x,windows,sr=24000):
    hop=round(.01*sr); n=round(.02*sr)
    if len(x)<n: return []
    frames=np.lib.stride_tricks.sliding_window_view(x,n)[::hop]
    rms=np.sqrt(np.mean(frames.astype(np.float64)**2,axis=1)); db=20*np.log10(np.maximum(rms,1e-12))
    peak=np.max(np.abs(frames),axis=1); crest=20*np.log10(np.maximum(peak,1e-12)/np.maximum(rms,1e-12))
    baseline=np.array([np.percentile(db[max(0,i-30):min(len(db),i+31)],25) for i in range(len(db))])
    ids=np.flatnonzero((db-baseline>=9)&(crest>=7)&(db>-70))
    groups=[]
    for i in ids:
        if not groups or i-groups[-1][-1]>3: groups.append([int(i)])
        else: groups[-1].append(int(i))
    result=[]; freq=np.fft.rfftfreq(n,1/sr)
    for g in groups:
        # Duration is a navigation filter only; longer swallowing sounds can be missed.
        a=g[0]*hop/sr; b=(g[-1]*hop+n)/sr
        if b-a>.35: continue
        i=max(g,key=lambda j:db[j]-baseline[j]); power=np.abs(np.fft.rfft(frames[i]*np.hanning(n)))**2
        total=float(power.sum())+1e-20; status,words=protection(a,b,windows)
        result.append({'start':a,'end':b,'peak_time':(i*hop+n/2)/sr,'local_rise_db':float(db[i]-baseline[i]),'rms_dbfs':float(db[i]),'crest_db':float(crest[i]),'low_band_fraction':float(power[freq<500].sum()/total),'high_band_fraction':float(power[freq>3000].sum()/total),'status':status,'nearby_asr_words':words,'action':'review_only','reason':'Short local energy rise with high peak/RMS; spectral ratios provided for comparison, not identity.','uncertainty':'May be quiet phoneme, aspiration, breath, handling or codec noise; ASR gaps are not verified non-speech.'})
    return result

def context_wav(media,a,b,out):
    run(['ffmpeg','-v','error','-n','-i',str(media),'-ss',str(a),'-t',str(b-a),'-map','0:a:0','-c:a','pcm_s16le',str(out)])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--export',required=True); ap.add_argument('--map',required=True); ap.add_argument('--asr',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    m=json.loads(Path(args.map).read_text()); windows=json.loads(Path(args.asr).read_text()); out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    paths={'export':args.export,'map':args.map,'asr':args.asr,'source':m['source'],'implementation':__file__}
    before={k:record(v) for k,v in paths.items()}
    if before['source']['sha256']!=m['original_source_sha256']: raise ValueError('Source hash mismatch')
    if any(c['kind']!='source' or c.get('playback_rate',1)!=1 for c in m['clips']): raise ValueError('Only original-speed source maps supported')
    x=pcm(args.export); duration=len(x)/24000
    if abs(duration-m['total_seconds'])>.1: raise ValueError('Export/map duration mismatch')
    events=detect(x,windows)
    for i,e in enumerate(events,1):
        e['id']=f'M{i:04d}'; e['source_pieces']=source_pieces(m,e['start'],e['end'])
        e['near_edit']=len(source_pieces(m,max(0,e['start']-.15),min(duration,e['end']+.15)))>1
    ranked=sorted(events,key=lambda e:(e['status']!='asr_gap_candidate_not_confirmed_non_speech',-e['local_rise_db']))[:12]
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for e in ranked:
        a=max(0,e['start']-.65); b=min(duration,e['end']+.65); stem=out/e['id']; files=[]
        wav=Path(str(stem)+'-export.wav'); context_wav(args.export,a,b,wav); files.append(record(wav))
        pieces=source_pieces(m,a,b); e['context_source_pieces']=pieces
        e['context_unmapped_seconds']=max(0,(b-a)-sum(p['output_end']-p['output_start'] for p in pieces))
        e['source_pcm_comparison']=[]
        for j,p in enumerate(pieces):
            wav=Path(str(stem)+f'-source-{j+1}.wav'); context_wav(m['source'],p['source_start'],p['source_end'],wav); files.append(record(wav))
            sx=pcm(wav); ex=x[round(p['output_start']*24000):round(p['output_end']*24000)]; size=min(len(sx),len(ex))
            corr=float(np.corrcoef(sx[:size],ex[:size])[0,1]) if size>1 and np.std(sx[:size])>1e-9 and np.std(ex[:size])>1e-9 else None
            e['source_pcm_comparison'].append({'clip_id':p['clip_id'],'compared_samples':size,'sample_rate':24000,'correlation':corr,'actual_audio_review':False})
        lo,hi=int(a*24000),int(b*24000); xx=x[lo:hi]; fig,ax=plt.subplots(2,1,figsize=(10,5))
        ax[0].plot(np.arange(len(xx))/24000+a,xx,linewidth=.5); ax[0].axvspan(e['start'],e['end'],color='orange',alpha=.35); ax[0].set_title(e['id']+' '+e['status']); ax[0].set_ylabel('Analysis mono amplitude')
        ax[1].specgram(xx,NFFT=512,Fs=24000,noverlap=384,xextent=(a,b),vmin=-110,vmax=-20); ax[1].set_ylim(0,10000); ax[1].set_xlabel('Export seconds'); ax[1].set_ylabel('Hz'); fig.tight_layout(); img=Path(str(stem)+'.png'); fig.savefig(img); plt.close(fig); files.append(record(img)); e['context_output']=[a,b]; e['evidence']=files
    unchanged={k:sha(v)==before[k]['sha256'] for k,v in paths.items()}
    if not all(unchanged.values()): raise ValueError('Inputs changed during analysis')
    report={'kind':'mouth_noise_navigation_not_classifier','inputs':before,'inputs_unchanged':unchanged,'actual_audio_review':False,'content_status':'needs_review','final_pass':False,'analyzed_output_range':[0,duration],'listening_coverage_seconds':0,'parameters':{'sample_rate':24000,'frame_ms':20,'hop_ms':10,'local_percentile':25,'local_radius_ms':300,'min_rise_db':9,'min_crest_db':7,'min_rms_dbfs':-70,'max_event_seconds':.35,'word_guard_ms':80},'limitations':['No calibrated swallowing detector. False positives and missed events expected.','Mono/24k analysis may miss channel-specific or high-frequency events.','ASR gaps are uncertain; protected events must not be deleted.','Only top 12 navigation events have context artifacts; no actual listening performed.','No media edits, no render and no external calls.'],'event_count':len(events),'sampled_ids':[e['id'] for e in ranked],'events':events}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    lines=['# Unconfirmed audio-event candidates','', 'Numerical analysis only; listening coverage: 0. No audio has been changed.','', '|ID|Export seconds|Source seconds|Status|Local rise dB|','|---|---|---|---|---|']
    for e in ranked:
        src='; '.join(f"{p['source_start']:.3f}–{p['source_end']:.3f}" for p in e['source_pieces'])
        lines.append(f"|{e['id']}|{e['start']:.3f}–{e['end']:.3f}|{src}|{e['status']}|{e['local_rise_db']:.1f}|")
    lines.extend(['','Full event list and evidence hashes: report.json. Orange plots mark analysis candidates, not cut boundaries.','Unreported speech, consonants, breaths and codec/handling noise can resemble these events. User timestamp calibration is pending.'])
    (out/'CANDIDATES.md').write_text('\n'.join(lines)+'\n'); print(json.dumps({'events':len(events),'sampled':len(ranked),'unchanged':unchanged}))
if __name__=='__main__': main()
