#!/usr/bin/env python3
"""Size-budgeted H.264 share derivative; preserves master and copies all audio."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))


def audio_packets(path):
    return subprocess.check_output(['ffprobe','-v','error','-select_streams','a','-show_packets','-show_data_hash','sha256','-show_entries','packet=stream_index,pts,dts,duration,size,data_hash','-of','json',str(path)])


def budget_rate(max_bytes, duration, audio_bytes, reserve=0.04):
    if max_bytes <= 0 or duration <= 0 or audio_bytes < 0 or not 0 < reserve < 1:
        raise ValueError('Invalid size budget')
    rate=int((max_bytes*(1-reserve)-audio_bytes)*8/duration)
    if rate < 100000:
        raise ValueError('Budget too small while preserving audio; choose a larger budget or explicitly change delivery settings')
    return rate


def render(source, output, max_bytes):
    source=Path(source).resolve();output=Path(output).resolve()
    if source==output or output.exists():raise ValueError('Use a new output path; never overwrite a master or earlier share')
    data=probe(source);videos=[s for s in data['streams'] if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic')]
    audios=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1:raise ValueError('One moving video stream required')
    v=videos[0]
    if v.get('pix_fmt')!='yuv420p':raise ValueError('Only approved 8-bit yuv420p SDR derivatives supported; no implicit HDR conversion')
    if v.get('color_transfer') in ('smpte2084','arib-std-b67'):raise ValueError('HDR requires a separate approved color workflow')
    if any(a['codec_name'] not in ('aac','mp3','alac') for a in audios):raise ValueError('Audio codec needs an explicit MP4-compatible delivery choice')
    raw=audio_packets(source);packets=json.loads(raw).get('packets',[])
    audio_bytes=sum(int(p['size']) for p in packets)
    duration=float(data['format']['duration']);rate=budget_rate(max_bytes,duration,audio_bytes)
    output.parent.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='mobile-share-') as temp:
        temp=Path(temp);candidate=temp/'share.mp4'
        base=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(source),'-map',f"0:{v['index']}",'-c:v','libx264','-preset','slow','-b:v',str(rate),'-pix_fmt','yuv420p','-fps_mode','passthrough','-passlogfile',str(temp/'pass')]
        subprocess.run(base+['-pass','1','-an','-f','null','-'],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(base+['-map','0:a?','-pass','2','-c:a','copy','-movflags','+faststart',str(candidate)],check=True)
        got=probe(candidate);gv=next(s for s in got['streams'] if s['codec_type']=='video')
        # Compare audio packets excluding stream index: selected video is always output stream zero.
        def normalize(raw):return [{k:x for k,x in p.items() if k!='stream_index'} for p in json.loads(raw).get('packets',[])]
        checks={'within_budget':candidate.stat().st_size<max_bytes,'geometry':(gv['width'],gv['height'],gv.get('sample_aspect_ratio'))==(v['width'],v['height'],v.get('sample_aspect_ratio')),'fps':Fraction(gv['avg_frame_rate'])==Fraction(v['avg_frame_rate']),'duration':abs(float(got['format']['duration'])-duration)<0.001,'audio_packets':normalize(audio_packets(candidate))==normalize(raw),'codec':gv['codec_name']=='h264'}
        subprocess.run(['ffmpeg','-v','error','-i',str(candidate),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
        checks['full_decode']=True
        if not all(checks.values()):raise ValueError('Share verification failed: '+json.dumps(checks))
        import shutil
        shutil.copyfile(candidate,output)
    report={'source':str(source),'source_sha256':source_hash,'output':str(output),'max_bytes':max_bytes,'size_bytes':output.stat().st_size,'video_target_bps':rate,'video_measured_bps':gv.get('bit_rate'),'audio':'copy; no bitrate re-encode','audio_measured_bps':[a.get('bit_rate') for a in got['streams'] if a['codec_type']=='audio'],'checks':checks,'visual_review':'required: inspect long/small subtitles and motion in actual output','actual_audio_listening':False,'delivery_status':'technical_pass_pending_visual_review'}
    output.with_suffix('.qa.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('output');p.add_argument('--max-bytes',type=int,required=True)
    a=p.parse_args();print(json.dumps(render(a.source,a.output,a.max_bytes),indent=2))
