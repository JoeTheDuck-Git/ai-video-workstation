"""Synthetic timelines only; these do not validate editor compatibility."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('draft_timeline',ROOT/'scripts/lab/draft-timeline-prototype.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Timeline(unittest.TestCase):
 def make(self,d,source):
  p=Path(d)/'timeline.json'
  p.write_text(json.dumps({'fps':'60000/1001','source':source,'clips':[
   {'id':'a','source_in_frame':11,'source_out_frame':42,'duration_frames':31,'timeline_in_frame':0},
   {'id':'b','source_in_frame':70,'source_out_frame':130,'duration_frames':60,'timeline_in_frame':31}]}))
  return p,hashlib.sha256(p.read_bytes()).hexdigest()
 def test_paths_bounds_audio_and_rounding(self):
  for source in ('/media/example.mp4',r'D:\media\中文 clip.mp4'):
   with tempfile.TemporaryDirectory() as d:
    p,h=self.make(d,source);n=m.neutral_sample(p,h);c=m.capcut_proposal(n);j=m.jianying_proposal(n)
    self.assertEqual(n['sample_frames'],91)
    a,b=c['segment_field_proposals'];self.assertEqual(a['target_timerange']['start']+a['target_timerange']['duration'],b['target_timerange']['start'])
    self.assertEqual(b['source_path'],source)
    self.assertEqual(b['audio_link'],'embedded_source_audio')
    self.assertTrue(all(abs(x['rounding_duration_delta_us'])<=1 for x in (a,b)))
    self.assertIsNone(c['draft_artifact']);self.assertIsNone(j['draft_artifact'])
    self.assertNotIn('segment_field_proposals',j)
 def test_wrong_edl_and_selection_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p,h=self.make(d,'example.mp4')
   for digest,indices in [('wrong',(0,1)),(h,(1,0)),(h,(0,0)),(h,(0,3))]:
    with self.assertRaises(ValueError):m.neutral_sample(p,digest,indices)
 def test_no_native_compatibility_claim(self):
  with tempfile.TemporaryDirectory() as d:
   p,h=self.make(d,'example.mp4');n=m.neutral_sample(p,h)
   for f in (m.capcut_proposal,m.jianying_proposal):
    self.assertEqual(f(n,'example-version','Windows')['compatibility'],'unverified')
if __name__=='__main__':unittest.main()
