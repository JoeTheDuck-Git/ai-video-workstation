"""Structural proposals only. No editor draft writer, app launch, copies or encoders."""
from fractions import Fraction
import hashlib,json
from pathlib import Path


def microseconds(frame,fps):
    return round(Fraction(frame*1000000,1)/Fraction(fps))

def neutral_sample(map_path,expected_sha256,indices=(0,1)):
    raw=Path(map_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('Not the final verified EDL')
    m=json.loads(raw);cursor=0
    if Fraction(m['fps'])<=0:raise ValueError('Invalid frame rate')
    for c in m['clips']:
        if any(type(c[k]) is not int for k in ('timeline_in_frame','source_in_frame','source_out_frame','duration_frames')) or c['source_in_frame']<0 or c['duration_frames']<=0:raise ValueError('Invalid frame bounds')
        if c['timeline_in_frame']!=cursor or c['source_out_frame']-c['source_in_frame']!=c['duration_frames']:raise ValueError('Invalid EDL continuity')
        cursor+=c['duration_frames']
    original_frames=cursor
    if len(indices) not in (2,3) or tuple(sorted(set(indices)))!=tuple(indices) or any(i<0 or i>=len(m['clips']) for i in indices):raise ValueError('Choose 2–3 unique ordered source clips')
    clips=[];cursor=0
    for i in indices:
        c=m['clips'][i];n=c['duration_frames']
        clips.append({'id':c['id'],'source_in_frame':c['source_in_frame'],'source_out_frame':c['source_out_frame'],
          'original_timeline_in_frame':c['timeline_in_frame'],'sample_in_frame':cursor,'sample_out_frame':cursor+n,
          'audio_link':'embedded_source_audio','speed':'1/1'})
        cursor+=n
    return {'schema':'neutral-draft-proposal-v1','source':m['source'],'edl_sha256':expected_sha256,'fps':m['fps'],
      'original_frames':original_frames,'original_duration_seconds':str(Fraction(original_frames,1)/Fraction(m['fps'])),'sample_frames':cursor,
      'sample_duration_seconds':str(Fraction(cursor,1)/Fraction(m['fps'])),'clips':clips,
      'material_mode':'reference_for_structural_test_only','delivery_material_mode':'unconfirmed','subtitles':None}

def capcut_proposal(neutral,version=None,platform=None):
    rows=[];fps=neutral['fps']
    for c in neutral['clips']:
        a,b=microseconds(c['sample_in_frame'],fps),microseconds(c['sample_out_frame'],fps)
        sa,sb=microseconds(c['source_in_frame'],fps),microseconds(c['source_out_frame'],fps)
        rows.append({'source_clip_id':c['id'],'source_timerange':{'start':sa,'duration':sb-sa},
          'target_timerange':{'start':a,'duration':b-a},'speed':1.0,'volume':1.0,
          'audio_link':'embedded_source_audio','source_path':neutral['source'],
          'rounding_duration_delta_us':(sb-sa)-(b-a)})
    return {'product':'CapCut','proposal_only':True,'draft_artifact':None,'compatibility':'unverified',
      'target_version':version,'platform':platform,'segment_field_proposals':rows,
      'requires':['current-version isolated native draft','material/auxiliary reference mapping','app open/save/reopen test','external output write permission']}

def jianying_proposal(neutral,version=None,platform=None):
    return {'product':'Jianying','proposal_only':True,'draft_artifact':None,'compatibility':'unverified',
      'target_version':version,'platform':platform,'neutral_edl_sha256':neutral['edl_sha256'],
      'status':'needs_native_format_sample' if version and platform else 'needs_target_version_platform',
      'requires':['Jianying-specific native sample','separate format adapter','app open/save/reopen test']}
