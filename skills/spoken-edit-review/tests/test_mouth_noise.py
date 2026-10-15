import importlib.util
from pathlib import Path
import unittest
import numpy as np
p=Path(__file__).resolve().parents[1]/'scripts/mouth_noise_candidates.py'
s=importlib.util.spec_from_file_location('mouth',p); mod=importlib.util.module_from_spec(s); s.loader.exec_module(mod)

class MouthNoiseSafety(unittest.TestCase):
    def test_silence_is_not_a_detection(self):
        self.assertEqual(mod.detect(np.zeros(48000),[]),[])
    def test_impulse_is_candidate_never_edit(self):
        x=np.random.default_rng(1).normal(0,.0001,48000); x[24000]=.05
        events=mod.detect(x,[{'start':0,'end':2,'words':[]}])
        self.assertTrue(any(e['start']<=1<=e['end'] for e in events))
        self.assertTrue(all(e['action']=='review_only' for e in events))
    def test_same_event_as_quiet_plosive_is_protected(self):
        x=np.random.default_rng(1).normal(0,.0001,48000); x[24000]=.05
        w=[{'start':0,'end':2,'words':[{'start':.9,'end':1.1,'text':'quiet consonant'}]}]
        events=[e for e in mod.detect(x,w) if e['start']<=1<=e['end']]
        self.assertTrue(events); self.assertTrue(all(e['status']=='protected_word_or_tail' for e in events))
    def test_aspiration_and_tail_guard(self):
        w=[{'start':0,'end':3,'words':[{'start':1,'end':2,'text':'word'}]}]
        for a,b in [(.94,.98),(2.02,2.07),(1.4,1.5)]:
            self.assertEqual(mod.protection(a,b,w)[0],'protected_word_or_tail')
    def test_unknown_gap_protected(self):
        self.assertEqual(mod.protection(1,1.1,[])[0],'protected_unknown_coverage')
        self.assertEqual(mod.protection(1,1.1,[{'start':0,'end':1.02},{'start':1.05,'end':2}])[0],'protected_unknown_coverage')
    def test_breath_in_gap_never_confirmed_noise(self):
        x=np.random.default_rng(3).normal(0,.0001,48000)
        x[23000:25000]+=np.random.default_rng(4).normal(0,.003,2000)*np.hanning(2000)
        events=mod.detect(x,[{'start':0,'end':2,'words':[]}])
        self.assertTrue(events)
        for e in events:
            self.assertEqual(e['action'],'review_only'); self.assertIn('breath',e['uncertainty'])
    def test_context_across_join_is_split(self):
        m={'fps':'30','clips':[{'id':'a','timeline_in_frame':0,'duration_frames':30,'source_in_frame':30},{'id':'b','timeline_in_frame':30,'duration_frames':30,'source_in_frame':90}]}
        r=mod.source_pieces(m,.9,1.1)
        self.assertEqual(len(r),2); self.assertAlmostEqual(r[0]['source_end'],2); self.assertAlmostEqual(r[1]['source_start'],3)
    def test_overlapping_asr_disagreement_protects(self):
        w=[{'start':0,'end':2,'words':[]},{'start':0,'end':2,'words':[{'start':.8,'end':1.2,'text':'soft word'}]}]
        self.assertEqual(mod.protection(1,1.01,w)[0],'protected_word_or_tail')
if __name__=='__main__': unittest.main()
