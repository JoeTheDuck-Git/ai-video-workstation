"""Public synthetic media only: installer snapshot + real encoder, not editorial approval."""
import importlib.util,json,os,platform,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd):
 return subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
with tempfile.TemporaryDirectory(prefix='native-') as tmp:
 d=Path(tmp)/'中文 空間';d.mkdir()
 installer=load('installer',ROOT/'scripts/install_skills.py')
 meta=installer.install(d/'skills',d/'state');runtime=Path(meta['runtime_root'])
 r=load('render_smoke',runtime/'scripts/lab/render-spoken-preview.py')
 source=d/'來源 素材.mp4'
 run(['ffmpeg','-v','error','-n','-f','lavfi','-i','testsrc2=size=1280x720:rate=30:duration=3','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=3','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(source)])
 video,audio=r.probe_source(source)
 plan={'fps':'30','total_seconds':2.,'clips':[{'source_in_frame':0,'source_out_frame':30},{'source_in_frame':60,'source_out_frame':90}]}
 choices={'resolution':'480p','frame_rate':'30','video_codec':'h264','audio_bitrate':128000,'video_bitrate':650000,'rate_control':'vbr'}
 settings=r.export.resolve(choices,'480p',video,audio,'30',r.export.available_encoders())
 compiled=r.compile_filters(plan,'480p',video,audio,settings)
 settings.update(width=compiled['width'],height=compiled['height'])
 graph=d/'濾鏡 script.txt';graph.write_text(compiled['filter_graph'],encoding='utf-8')
 output=d/'剪輯 成片.mp4'
 job={'source':{'path':str(source)},'compiled':compiled,'export_settings':settings}
 run(r.ffmpeg_command(job,graph,output))
 run(['ffmpeg','-v','error','-xerror','-i',str(output),'-f','null','-'])
 qa=r.export.measured(output,settings);assert qa['spec_pass'],qa
 probe=r.export.probe(output);v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert abs(float(v['duration'])-2)<.035
 assert abs(float(v['duration'])-float(a['duration']))<.05
 assert abs(float(v.get('start_time',0))-float(a.get('start_time',0)))<.05
 assert 10000<output.stat().st_size<2000000
 style=load('smoke_style',runtime/'skills/caption-doctor/scripts/caption_style.py')
 caption=style.format_technology_caption('金額1,234,567，完成。')
 assert caption=='金額1,234,567  完成'
 report={'os':platform.platform(),'python':sys.version,'runner_image':os.getenv('ImageOS'),'runner_image_version':os.getenv('ImageVersion'),'ffmpeg':run(['ffmpeg','-version']).splitlines()[0],'ffprobe':run(['ffprobe','-version']).splitlines()[0],'skills':len(meta['skills']),'unicode_space_absolute_path':str(d),'qa':qa,'duration_seconds':v['duration'],'av_duration_delta':abs(float(v['duration'])-float(a['duration'])),'bytes':output.stat().st_size,'caption':caption,'full_decode':True,'editorial_visual_listening_review':False}
 text=json.dumps(report,ensure_ascii=False,indent=2);print(text)
 if os.getenv('GITHUB_STEP_SUMMARY'):
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write('## Native synthetic render evidence\n```json\n'+text+'\n```\n')
