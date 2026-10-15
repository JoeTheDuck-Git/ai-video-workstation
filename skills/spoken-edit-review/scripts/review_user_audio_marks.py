from pathlib import Path
import importlib.util,json,argparse,math
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
script=Path(__file__).with_name('mouth_noise_candidates.py')
s=importlib.util.spec_from_file_location('m',script);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def user_windows(seconds,duration,radius=2):
    if not math.isfinite(duration) or duration<=0 or not math.isfinite(radius) or radius<=0:raise ValueError('Invalid duration/radius')
    result=[]
    for t in seconds:
        if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or not 0<=t<duration:raise ValueError('Invalid user time')
        result.append((t,max(0,t-radius),min(duration,t+radius)))
    return result

def mark_tag(index,seconds):
    return f'U{index:02d}-{seconds:09.3f}s'

def related_events(events,start,end):
    # Protection controls repair eligibility, never visibility of user reports.
    return [e for e in events if e['end']>start and e['start']<end]

def main():
    ap=argparse.ArgumentParser(description='User-reported mouth-noise windows: no filtering, diagnosis only, no repair.')
    ap.add_argument('--prior-report',required=True);ap.add_argument('--marks',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    old=json.loads(Path(args.prior_report).read_text())
    for key in ['export','source','map','asr']:
        rec=old['inputs'][key]
        if m.sha(rec['path'])!=rec['sha256']:raise ValueError('Changed input: '+key)
    windows=json.loads(Path(old['inputs']['asr']['path']).read_text());plan=json.loads(Path(old['inputs']['map']['path']).read_text())
    marks=json.loads(Path(args.marks).read_text());bounds=user_windows(marks['reported_seconds'],plan['total_seconds'],marks.get('radius_seconds',2))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    x=m.pcm(old['inputs']['export']['path']);sr=24000
    rows=[]
    for i,(t,a,b) in enumerate(bounds,1):
     tag=mark_tag(i,t); xx=x[round(a*sr):round(b*sr)]
     m.context_wav(old['inputs']['export']['path'],a,b,out/f'{tag}-original.wav')
     parts=m.source_pieces(plan,a,b)
     for j,p in enumerate(parts,1):m.context_wav(plan['source'],p['source_start'],p['source_end'],out/f'{tag}-source-{j}.wav')
     words=[]
     for q in windows:
      for w in q.get('words',[]):
       if w['end']>a and w['start']<b and w not in words:words.append(w)
     words.sort(key=lambda w:(w['start'],w['end']))
     nearby=related_events(old['events'],a,b)
     center=[e for e in nearby if e['end']>t-.3 and e['start']<t+.3]
     frames=np.lib.stride_tricks.sliding_window_view(xx,480)[::240];rms=np.sqrt(np.mean(frames.astype(float)**2,axis=1));db=20*np.log10(np.maximum(rms,1e-12));crest=20*np.log10(np.maximum(np.max(abs(frames),axis=1),1e-12)/np.maximum(rms,1e-12))
     # Global neighborhood, so diagnostic thresholds exactly match previous detector.
     fullframes=np.lib.stride_tricks.sliding_window_view(x,480)[::240]
     centerids=range(max(0,round((t-.3)*100)),min(len(fullframes),round((t+.3)*100)))
     diagnostics=[]
     for k in centerids:
      f=fullframes[k];v=20*np.log10(max(float(np.sqrt(np.mean(f.astype(float)**2))),1e-12));baseframes=fullframes[max(0,k-30):min(len(fullframes),k+31)];basedb=20*np.log10(np.maximum(np.sqrt(np.mean(baseframes.astype(float)**2,axis=1)),1e-12));base=float(np.percentile(basedb,25));c=20*np.log10(max(float(np.max(abs(f))),1e-12)/max(10**(v/20),1e-12))
      diagnostics.append({'start':k*.01,'end':k*.01+.02,'rms_dbfs':v,'rise_db':v-base,'crest_db':c,'threshold_pass':bool(v>-70 and v-base>=9 and c>=7),'protection':m.protection(k*.01,k*.01+.02,windows)[0]})
     fig,axs=plt.subplots(3,1,figsize=(13,8));ts=np.arange(len(xx))/sr+a
     axs[0].plot(ts,xx,lw=.45);axs[0].set_ylabel('Amplitude');axs[0].set_title(tag+' USER approximate mark (not confirmed noise)')
     axs[1].specgram(xx,NFFT=512,Fs=sr,noverlap=384,xextent=(a,b),vmin=-110,vmax=-20);axs[1].set_ylim(0,8000);axs[1].set_ylabel('Hz')
     axs[2].plot(np.arange(len(db))*.01+a,db);axs[2].set_ylabel('20ms RMS dBFS');axs[2].set_xlabel('Export seconds')
     for ax in axs:ax.axvline(t,color='red',ls='--');ax.set_xlim(a,b)
     for w in words:axs[2].axvspan(max(a,w['start']),min(b,w['end']),alpha=.025,color='orange')
     fig.tight_layout();fig.savefig(out/f'{tag}.png');plt.close(fig)
     rows.append({'id':tag,'reported_time':t,'reported_time_is_approximate':True,'kind':'user_report_not_machine_confirmation','context_output':[a,b],'context_source':parts,'point_source':m.source_pieces(plan,t,t+.000001),'machine_events_in_context':nearby,'machine_events_near_mark':center,'words':words,'near_mark_frame_diagnostics':diagnostics,'previous_primary_list_inclusion':any(e['id'] in old['sampled_ids'] and e['status'].startswith('asr_gap') for e in nearby),'decision':'unresolved_preserve_pending_review','actual_audio_review':False})
    report={'inputs':{**old['inputs'],'user_marks':m.record(args.marks),'analysis_code':m.record(__file__),'mapping_code':m.record(script),'prior_report':m.record(args.prior_report)},'actual_audio_review':False,'content_status':'needs_review','marks':rows}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    for r in rows:print(r['id'],'near',[(e['id'],e['start'],e['end'],e['status'],e['id'] in old['sampled_ids']) for e in r['machine_events_near_mark']], 'words',[(w['text'],w['start'],w['end']) for w in r['words']])

if __name__=="__main__":main()
