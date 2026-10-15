import importlib.util
from pathlib import Path
import tempfile,subprocess,unittest,json
p=Path(__file__).resolve().parents[1]/'scripts/mobile_share.py'
s=importlib.util.spec_from_file_location('share',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MobileShare(unittest.TestCase):
 def test_budget(self):
  rate=m.budget_rate(19000000,170,5100000)
  self.assertLess((rate*170/8+5100000),19000000)
  with self.assertRaises(ValueError):m.budget_rate(100,170,1000)
 def test_real_media(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source.mp4';out=Path(d)/'share.mp4'
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=30000/1001','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','3','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(src)],check=True)
   r=m.render(src,out,400000)
   self.assertTrue(all(r['checks'].values()));self.assertLess(out.stat().st_size,400000)
   self.assertEqual(r['audio'],'copy; no bitrate re-encode')
   with self.assertRaises(ValueError):m.render(src,out,400000)
