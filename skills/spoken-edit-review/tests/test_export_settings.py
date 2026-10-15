import importlib.util,json,unittest,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('exp',ROOT/'scripts/lab/export-settings.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
spec=importlib.util.spec_from_file_location('renderer_export',ROOT/'scripts/lab/render-spoken-preview.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class ExportSettingsTests(unittest.TestCase):
 def setUp(self):
  self.v={'codec_name':'hevc','bit_rate':'54000000','r_frame_rate':'60000/1001','frame_timing':'cfr','width':3840,'height':2160,'sample_aspect_ratio':'1:1'}
  self.a={'codec_name':'aac','bit_rate':'192000','index':1,'sample_rate':'48000','channels':2}
  self.c={'resolution':'original','frame_rate':'source','video_codec':'source','audio_bitrate':'source','video_bitrate':55000000,'rate_control':'vbr'}
 def resolve(self,c=None,v=None,a=None,enc=None):return e.resolve(c if c is not None else self.c,'original',v or self.v,a or self.a,'60000/1001',enc if enc is not None else {'libx264','libx265','aac'})
 def test_native_choices(self):
  x=self.resolve();self.assertEqual(x['frame_rate'],'60000/1001');self.assertEqual(x['video_encoder'],'libx265');self.assertEqual(x['audio_bitrate_target'],192000);self.assertEqual(x['video_bitrate_target'],55000000)
 def test_source_average_not_55_default(self):
  c=dict(self.c,video_bitrate='source');self.assertEqual(self.resolve(c)['video_bitrate_target'],54000000)
 def test_missing_choice(self):
  for k in self.c:
   c=dict(self.c);del c[k]
   with self.assertRaisesRegex(ValueError,'Missing'):self.resolve(c)
 def test_unknown_bitrate(self):
  a=dict(self.a);del a['bit_rate']
  with self.assertRaisesRegex(ValueError,'unknown'):self.resolve(a=a)
 def test_vfr_blocked(self):
  with self.assertRaisesRegex(ValueError,'VFR'):self.resolve(v=dict(self.v,frame_timing='vfr_or_unknown'))
 def test_codec_and_mode_capability(self):
  with self.assertRaisesRegex(ValueError,'unavailable'):self.resolve(enc={'libx264','aac'})
  with self.assertRaisesRegex(ValueError,'Only single'):self.resolve(dict(self.c,rate_control='two_pass'))
 def test_multiple_audio_requires_explicit_adapter(self):
  with patch.object(e,'probe',return_value={'streams':[dict(self.v,codec_type='video'),dict(self.a,codec_type='audio'),dict(self.a,codec_type='audio')]}):
   with self.assertRaisesRegex(ValueError,'all tracks'):e.source_streams('fixture')
 def test_explicit_sdr_10bit_conversion(self):
  v=dict(self.v,pix_fmt='yuv420p10le',color_space='bt709',color_transfer='bt709',color_primaries='bt709')
  with self.assertRaisesRegex(ValueError,'10-bit'):self.resolve(v=v)
  self.assertEqual(self.resolve(dict(self.c,pixel_conversion='bt709_10_to_8_draft'),v=v)['pixel_conversion'],'bt709_10_to_8_draft')
  with self.assertRaisesRegex(ValueError,'HDR'):self.resolve(dict(self.c,pixel_conversion='bt709_10_to_8_draft'),v=dict(v,color_transfer='smpte2084'))
 def test_attached_thumbnail_is_not_moving_video(self):
  data={'streams':[dict(self.v,index=2,codec_type='video'),dict(self.a,codec_type='audio'),{'index':5,'codec_type':'video','disposition':{'attached_pic':1}}]}
  pts={'packets':[{'pts_time':'0.000000'},{'pts_time':'0.016683'},{'pts_time':'0.033367'}]}
  with patch.object(e,'probe',return_value=data),patch.object(e.subprocess,'check_output',return_value=json.dumps(pts)):
   v,a=e.source_streams('fixture')
  self.assertEqual(v['index'],2);self.assertEqual(v['excluded_attached_picture_indices'],[5]);self.assertEqual(v['frame_timing'],'cfr')
 def test_native_filter_and_command(self):
  settings=self.resolve();plan={'fps':'60000/1001','total_seconds':1.001,'clips':[{'source_in_frame':0,'source_out_frame':60}]}
  compiled=r.compile_filters(plan,'original',self.v,self.a,settings)
  self.assertEqual(compiled['export_fps'],'60000/1001');self.assertEqual((compiled['width'],compiled['height']),(3840,2160))
  cmd=r.ffmpeg_command({'compiled':compiled,'export_settings':settings,'source':{'path':'original.mp4'}},'graph','out.mp4')
  self.assertEqual(cmd[cmd.index('-b:v')+1],'55000000');self.assertEqual(cmd[cmd.index('-b:a')+1],'192000');self.assertIn('libx265',cmd);self.assertNotIn('-maxrate',cmd)
 def test_no_upscale_from_preview(self):
  with self.assertRaisesRegex(ValueError,'Upscaling'):r.compile_filters({'fps':'30'},'4K',dict(self.v,width=854,height=480),self.a,self.resolve())
 def test_geometry_preserves_native_sar(self):
  p={'fps':'60000/1001','total_seconds':1.001,'clips':[{'source_in_frame':0,'source_out_frame':60}]}
  c=r.compile_filters(p,'original',dict(self.v,width=1440,height=1080,sample_aspect_ratio='4:3'),self.a,self.resolve())
  self.assertEqual(c['width'],1440);self.assertEqual(c['sample_aspect_ratio'],'4/3')
 def test_measurements_not_targets(self):
  data={'streams':[dict(self.v,codec_type='video',bit_rate='48000000',avg_frame_rate='60000/1001'),dict(self.a,codec_type='audio',bit_rate='190000')]}
  with patch.object(e,'probe',return_value=data):out=e.measured('fake',self.resolve())
  self.assertEqual(out['actual']['video_bitrate_measured'],'48000000');self.assertEqual(out['requested']['video_bitrate_target'],55000000)
if __name__=='__main__':unittest.main()
