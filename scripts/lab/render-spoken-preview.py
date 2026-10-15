#!/usr/bin/env python3
"""Prepare or execute a bound preview job. prepare never runs FFmpeg."""
import argparse
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PLANNER=Path(__file__).with_name('plan-spoken-cut.py')
spec=importlib.util.spec_from_file_location('preview_plan',PLANNER)
planner=importlib.util.module_from_spec(spec);spec.loader.exec_module(planner)
g=planner.s.g
RESOLUTIONS={'480p':480,'720p':720,'1080p':1080,'4K':2160,'original':None}


SETTINGS=Path(__file__).with_name('export-settings.py')
spec=importlib.util.spec_from_file_location('export_settings',SETTINGS)
export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)


def probe_source(path):
    return export.source_streams(path)


def compile_filters(plan,resolution,video,audio,settings):
    if resolution not in RESOLUTIONS:raise ValueError('Explicit supported resolution required')
    fps=Fraction(plan['fps']);rate=int(audio['sample_rate'])
    if rate<=0 or int(audio['channels']) not in (1,2):raise ValueError('Unsupported source audio')
    sar=Fraction(video.get('sample_aspect_ratio','1:1').replace(':','/'))
    dar=Fraction(video['width'],video['height'])*sar
    height=RESOLUTIONS[resolution] or video['height']
    width=video['width'] if resolution=='original' else int(round(float(dar*height)/2))*2
    if height>video['height']:raise ValueError('Upscaling requires explicit separate workflow; use original media, not a preview')
    if width<=0 or height<=0 or height%2:raise ValueError('Invalid output geometry')
    out_sar=dar*height/width
    rows=plan['clips'];n=len(rows);filters=[];sample_spans=[]
    video_input='0:'+str(video['index']) if 'index' in video else '0:v:0'
    audio_input='0:'+str(audio['index']) if 'index' in audio else '0:a:0'
    filters.append(('['+video_input+']split=%d')%n+''.join('[vin%d]'%i for i in range(n)))
    filters.append(('['+audio_input+']asplit=%d')%n+''.join('[ain%d]'%i for i in range(n)))
    for i,c in enumerate(rows):
        lo,hi=c['source_in_frame'],c['source_out_frame']
        sa,sb=round(Fraction(lo*rate,1)/fps),round(Fraction(hi*rate,1)/fps)
        sample_spans.append([sa,sb])
        filters.append(f'[vin{i}]trim=start_frame={lo}:end_frame={hi},setpts=PTS-STARTPTS,scale={width}:{height},setsar={out_sar.numerator}/{out_sar.denominator}:max=10000,format=yuv420p[v{i}]')
        filters.append(f'[ain{i}]atrim=start_sample={sa}:end_sample={sb},asetpts=PTS-STARTPTS[a{i}]')
    # Frame-rate conversion only follows the explicit user selection.
    export_fps=Fraction(settings['frame_rate'])
    filters.append(''.join(f'[v{i}]' for i in range(n))+f'concat=n={n}:v=1:a=0,fps={export_fps.numerator}/{export_fps.denominator}:round=near[vout]')
    gain=plan.get('gain_db',0)
    if not g.finite(gain) or not -30<=gain<=12:raise ValueError('Invalid gain')
    filters.append(''.join(f'[a{i}]' for i in range(n))+f'concat=n={n}:v=0:a=1,volume={gain}dB[aout]')
    return {'filter_graph':';\n'.join(filters),'width':width,'height':height,'sample_aspect_ratio':str(out_sar),
      'display_aspect_ratio':str(dar),'export_fps':str(export_fps),'audio_sample_rate':rate,'audio_channels':int(audio['channels']),
      'source_audio_sample_spans':sample_spans,'expected_duration':plan['total_seconds'],
      'duration_tolerance_seconds':float(1/export_fps)+.001}


def prepare_job(map_path,expected_sha,expected_version,resolution,output_dir,export_choices=None,project_root=None):
    map_path=Path(map_path).resolve();output_dir=Path(output_dir).resolve()
    if g.digest(map_path)!=expected_sha:raise ValueError('Wrong map SHA; refusing legacy or substituted map')
    plan=planner.validate_authorized_plan(map_path,allow_preview=True)
    if plan.get('version')!=expected_version:raise ValueError('Wrong map version')
    if plan.get('review_mode')!='preview' or plan.get('source_review',{}).get('mode')!='preview':raise ValueError('Preview renderer requires preview-bound map')
    project_root=Path(project_root).resolve() if project_root is not None else (ROOT/'productions').resolve()
    if output_dir==project_root or not output_dir.is_relative_to(project_root) or output_dir.exists():raise ValueError('Output must be a new directory within project root')
    if sum(c['duration_frames'] for c in plan['clips'])!=plan['total_frames']:raise ValueError('Map frame total mismatch')
    if plan['total_seconds']>plan.get('target_max_seconds',float('inf')):raise ValueError('Duration budget exceeded')
    video,audio=probe_source(plan['source'])
    settings=export.resolve(export_choices,resolution,video,audio,plan['fps'],export.available_encoders())
    compiled=compile_filters(plan,resolution,video,audio,settings)
    settings.update(width=compiled['width'],height=compiled['height'])
    return {'schema':1,'mode':'preview','map':g.record(map_path),'map_version':expected_version,
      'map_content_sha256':planner.content_hash(plan),'source':g.record(plan['source']),
      'renderer':g.record(__file__),'planner':g.record(PLANNER),'settings_module':g.record(SETTINGS),'resolution':resolution,
      'export_choices':export_choices,'export_settings':settings,'source_probe':{'video':video,'audio':audio},
      'project_root':str(project_root),'output_dir':str(output_dir),'output_name':'preview.mp4','actual_audio_review':False,'content_status':'needs_review','final_pass':False,
      'compiled':compiled,'source_clips':[{k:c[k] for k in ['id','source_in_frame','source_out_frame','timeline_in_frame','duration_frames']} for c in plan['clips']]}


def validate_job(path):
    job=g.read(path)
    if job.get('renderer')!=g.record(__file__) or job.get('planner')!=g.record(PLANNER) or job.get('settings_module')!=g.record(SETTINGS):raise ValueError('Renderer/planner version binding changed')
    current=prepare_job(job['map']['path'],job['map']['sha256'],job['map_version'],job['resolution'],job['output_dir'],job.get('export_choices'),job.get('project_root'))
    if current!=job:raise ValueError('Job settings/evidence changed; prepare again')
    return job


def filter_file_option():
    # Older FFmpeg uses a dedicated script option; newer versions removed it.
    help_text=subprocess.check_output(['ffmpeg','-hide_banner','-h','full'],text=True,encoding='utf-8',errors='replace',stderr=subprocess.DEVNULL)
    return '-filter_complex_script' if '-filter_complex_script' in help_text else '-/filter_complex'


def ffmpeg_command(job,filter_path,output):
    c=job['compiled'];e=job['export_settings']
    return ['ffmpeg','-v','warning','-nostdin','-n','-i',job['source']['path'],filter_file_option(),str(filter_path),
      '-map','[vout]','-map','[aout]','-c:v',e['video_encoder'],'-preset','fast','-b:v',str(e['video_bitrate_target']),
      '-pix_fmt','yuv420p','-fps_mode','cfr','-c:a',e['audio_codec'],'-b:a',str(e['audio_bitrate_target']),'-ar',str(c['audio_sample_rate']),
      '-ac',str(c['audio_channels']),'-movflags','+faststart',str(output)]


def render(job_path,authorization_path):
    job=validate_job(job_path);auth=g.read(authorization_path)
    # Host records the user's later resolution/resume instruction, not a new approval request.
    if (auth.get('render_authorized') is not True or not auth.get('instruction') or
        auth.get('job_sha256')!=g.digest(job_path) or auth.get('map_sha256')!=job['map']['sha256'] or
        auth.get('renderer_sha256')!=job['renderer']['sha256'] or auth.get('resolution')!=job['resolution']):
        raise ValueError('Explicit bound resume instruction required; render remains on hold')
    dest=Path(job['output_dir']);dest.mkdir(parents=True,exist_ok=False)
    graph=dest/'render-filter.txt';graph.write_text(job['compiled']['filter_graph'])
    g.write(dest/'render-job.json',job);g.write(dest/'resume-authorization.json',auth)
    # Exact bytes keep the source review hash valid for post-export review and QC.
    (dest/'source-timeline-map.json').write_bytes(Path(job['map']['path']).read_bytes())
    output=dest/job['output_name'];command=ffmpeg_command(job,graph,output)
    g.write(dest/'command.json',command)
    with (dest/'render.log').open('w') as log:
        subprocess.run(command,stdout=log,stderr=log,check=True)
    g.write(dest/'export-spec-qa.json',export.measured(output,job['export_settings']))
    g.write(dest/'render-result.json',{'render_complete':True,'export':g.record(output),'map':g.record(dest/'source-timeline-map.json'),
      'renderer':g.record(__file__),'job':g.record(job_path),'actual_audio_review':False,'content_status':'needs_review','final_pass':False,'delivery_allowed':False,
      'pending':['Technical QC bound to export/map hashes','Independent post-export evidence review','Preview delivery gate']})
    return output


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--map',required=True);p.add_argument('--expect-map-sha256',required=True);p.add_argument('--expect-version',required=True)
    p.add_argument('--export-settings',required=True,help='JSON of explicit user export choices');p.add_argument('--resolution',choices=RESOLUTIONS,required=True);p.add_argument('--project-root',required=True,help='User project directory; output must be a new descendant');p.add_argument('--output-dir',required=True);p.add_argument('--job',required=True)
    p=sub.add_parser('validate');p.add_argument('job')
    p=sub.add_parser('render');p.add_argument('job');p.add_argument('--resume-authorization',required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':
            job=prepare_job(args.map,args.expect_map_sha256,args.expect_version,args.resolution,args.output_dir,g.read(args.export_settings),args.project_root)
            with Path(args.job).open('x') as f:json.dump(job,f,ensure_ascii=False,indent=2)
            print('Prepared only; no rendering: '+args.job)
        elif args.command=='validate':validate_job(args.job);print('Bound job valid; no rendering')
        else:print(render(args.job,args.resume_authorization))
        return 0
    except (ValueError,KeyError,TypeError,OSError,StopIteration,subprocess.SubprocessError) as e:
        print('Preview renderer blocked: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
