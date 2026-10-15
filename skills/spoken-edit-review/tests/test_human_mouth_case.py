import hashlib,json,wave,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
CASE=ROOT/'mouth-noise-review/first-gap-trial/human-confirmed-first-gap/human-review.json'
def read(path):
 with wave.open(str(path),'rb') as f:return (f.getframerate(),f.getnchannels(),f.getnframes()),np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2)
@unittest.skipUnless(CASE.exists(), 'Private listening-case artifacts are not distributed')
class HumanCaseRegression(unittest.TestCase):
 def setUp(self):self.r=json.loads(CASE.read_text())
 def test_exact_listened_artifact_and_library_binding(self):
  r=self.r; s=r['samples']['listened_ab'];self.assertEqual(hashlib.sha256(Path(s['path']).read_bytes()).hexdigest(),r['library_binding']['sha256']);self.assertTrue(r['library_binding']['library_file_id'].startswith('libfile_'))
  for rec in r['samples'].values():self.assertEqual(hashlib.sha256(Path(rec['path']).read_bytes()).hexdigest(),rec['sha256']);self.assertEqual(rec['sha256'],rec['source_record']['sha256'])
 def test_confirmed_trial_preserves_context_and_assembly(self):
  r=self.r;pa,a=read(r['samples']['original_context']['path']);pb,b=read(r['samples']['processed_context']['path']);pc,c=read(r['samples']['listened_ab']['path']);self.assertEqual(pa,pb);self.assertEqual(pa,(48000,2,144000));self.assertEqual(pc,(48000,2,336000));lo,hi=r['local_processing']['sample_range_half_open']
  self.assertTrue(np.array_equal(a[:lo],b[:lo]));self.assertTrue(np.array_equal(a[hi:],b[hi:]));self.assertFalse(np.array_equal(a[lo:hi],b[lo:hi]));self.assertTrue(np.array_equal(c[:144000],a));self.assertTrue(np.array_equal(c[192000:],b));self.assertFalse(np.any(c[144000:192000]))
 def test_human_confirmation_not_global_or_agent_listening(self):
  r=self.r;self.assertTrue(r['human_review']['performed']);self.assertTrue(r['human_review']['source_message_id']);self.assertFalse(r['agent_actual_audio_review']);self.assertFalse(r['final_pass']);self.assertFalse(r['whole_film_human_review']);self.assertFalse(r['authorized_full_film_render']);self.assertFalse(r['authorized_other_points']);self.assertEqual(len(r['other_reported_seconds_unresolved']),6)
if __name__=='__main__':unittest.main()
