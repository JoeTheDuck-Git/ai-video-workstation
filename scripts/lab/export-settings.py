"""Explicit export choices and capability checks; no media rendering."""
from fractions import Fraction
import json
import subprocess

ENCODERS={'h264':'libx264','hevc':'libx265'}

def probe(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
    return data

def source_streams(path):
    data=probe(path)
    videos=[s for s in data['streams'] if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic')]
    audios=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or len(audios)!=1:
        raise ValueError('This adapter requires one video and one audio track; show all tracks and request an explicit supported alternative')
    video,audio=videos[0],audios[0]
    video['excluded_attached_picture_indices']=[s['index'] for s in data['streams'] if s.get('disposition',{}).get('attached_pic')]
    packets=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams',str(video['index']),'-show_packets','-show_entries','packet=pts_time','-of','json',str(path)],text=True))['packets']
    pts=sorted(float(p['pts_time']) for p in packets if 'pts_time' in p)
    delta=[b-a for a,b in zip(pts,pts[1:])]
    native=Fraction(video.get('r_frame_rate','0/1'))
    video['frame_timing']='cfr' if native>0 and delta and all(abs(d-float(1/native))<.00001 for d in delta) else 'vfr_or_unknown'
    if any(abs(float(s.get('start_time',0)))>.000001 for s in (video,audio)):
        raise ValueError('Nonzero source start requires an explicit PTS adapter')
    return video,audio

def available_encoders():
    lines=subprocess.check_output(['ffmpeg','-hide_banner','-encoders'],text=True,stderr=subprocess.DEVNULL).splitlines()
    return {parts[1] for line in lines if len(parts:=line.split())>=2 and len(parts[0])==6}

def positive(value,label):
    if isinstance(value,bool):raise ValueError(label+' must be a positive integer bitrate')
    try: n=int(value)
    except (ValueError,TypeError):raise ValueError(label+' unknown; ask user for an explicit bitrate')
    if str(n)!=str(value) or n<=0:raise ValueError(label+' must be a positive integer bitrate')
    return n

def resolve(choices,resolution,video,audio,map_fps,encoders):
    required={'resolution','frame_rate','video_codec','audio_bitrate','video_bitrate','rate_control'}
    if not isinstance(choices,dict) or required-set(choices):raise ValueError('Missing export choices; ask user before preparing a render')
    if choices['resolution']!=resolution:raise ValueError('Conflicting resolution choices')
    if video.get('frame_timing')!='cfr':raise ValueError('VFR or unknown timing requires a PTS-aware adapter; ask before CFR conversion')
    if Fraction(video['r_frame_rate'])!=Fraction(map_fps):raise ValueError('Source FPS differs from frame-index EDL')
    pixel_format=video.get('pix_fmt','yuv420p')
    if video.get('color_transfer') in ('smpte2084','arib-std-b67'):
        raise ValueError('HDR source needs an explicit supported color adapter')
    if pixel_format not in ('yuv420p','yuvj420p'):
        if not (pixel_format=='yuv420p10le' and choices.get('pixel_conversion')=='bt709_10_to_8_draft' and all(video.get(k)=='bt709' for k in ('color_space','color_transfer','color_primaries'))):
            raise ValueError('10-bit source needs explicit supported pixel conversion')
    try: rate=Fraction(map_fps) if choices['frame_rate']=='source' else Fraction(str(choices['frame_rate']))
    except (ValueError,ZeroDivisionError): raise ValueError('Invalid requested frame rate')
    if rate<=0 or rate>120:raise ValueError('Unsupported requested frame rate')
    codec=video.get('codec_name') if choices['video_codec']=='source' else choices['video_codec']
    encoder=ENCODERS.get(codec)
    if not encoder or encoder not in encoders:raise ValueError('Requested video encoder unavailable; ask user for supported alternative')
    if 'aac' not in encoders:raise ValueError('AAC encoder unavailable')
    if choices['rate_control']!='vbr':raise ValueError('Only single-pass average-target VBR supported; ask for an alternative')
    vb=positive(video.get('bit_rate') if choices['video_bitrate']=='source' else choices['video_bitrate'],'Source video bitrate' if choices['video_bitrate']=='source' else 'Video bitrate')
    ab=positive(audio.get('bit_rate') if choices['audio_bitrate']=='source' else choices['audio_bitrate'],'Source audio bitrate' if choices['audio_bitrate']=='source' else 'Audio bitrate')
    if not 8000<=ab<=512000:raise ValueError('Audio bitrate outside supported AAC range; ask for alternative')
    return {'frame_rate':str(rate),'video_codec':codec,'video_encoder':encoder,'video_bitrate_target':vb,'rate_control':'single_pass_average_target_vbr','audio_codec':'aac','audio_bitrate_target':ab,'video_track_index':video.get('index'),'pixel_conversion':choices.get('pixel_conversion','native_8bit'),'excluded_attached_picture_indices':video.get('excluded_attached_picture_indices',[]),'audio_track_index':audio.get('index'),'source_audio_codec':audio.get('codec_name'),'quality_note':'Video/audio re-encode; same codec or bitrate is not lossless. VBR target is approximate average, not each second.'}

def measured(path,settings):
    data=probe(path); v=next(s for s in data['streams'] if s['codec_type']=='video'); aud=[s for s in data['streams'] if s['codec_type']=='audio']
    checks={'video_codec':v['codec_name']==settings['video_codec'],'frame_rate':Fraction(v['r_frame_rate'])==Fraction(settings['frame_rate']),'audio_track_count':len(aud)==1,'audio_codec':len(aud)==1 and aud[0]['codec_name']==settings['audio_codec']}
    for field in ('width','height'):
        if field in settings:checks[field]=v[field]==settings[field]
    return {'spec_checks':checks,'spec_pass':all(checks.values()),'requested':settings,'actual':{'width':v['width'],'height':v['height'],'frame_rate':v.get('r_frame_rate'),'average_frame_rate':v.get('avg_frame_rate'),'video_codec':v['codec_name'],'video_bitrate_measured':v.get('bit_rate'),'audio_tracks':[{'index':s['index'],'codec':s['codec_name'],'bitrate_measured':s.get('bit_rate')} for s in aud]},'bitrate_note':'Stream averages from ffprobe; missing is unknown. Targets are not measured values.','delivery_allowed':False}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Read original specifications; no rendering')
    parser.add_argument('source')
    args=parser.parse_args()
    print(json.dumps(probe(args.source),ensure_ascii=False,indent=2))
