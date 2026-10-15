import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('source_detector',ROOT/'skills/spoken-edit-review/scripts/source_review.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

def row(text,a,b,words=None):return {'text':text,'start':a,'end':b,'words':words or []}

class SourceTests(unittest.TestCase):
    def test_text_score_exact_threshold_not_probability(self):
        d=s.detect([row('這次核心功能完整保留',0,2),row('這次核心功能完整保留',3,5)],10)
        q=next(x for x in d['candidates'] if x['kind']=='text_repeat')
        self.assertEqual(q['text_similarity'],1);self.assertIsNone(q['semantic_score']);self.assertEqual(q['action'],'review_only')
    def test_configurable_priority(self):
        rows=[row('abcdefghij',0,2),row('abcdefghiX',3,5)]
        self.assertTrue(any(x['kind']=='text_repeat' for x in s.detect(rows,10)['candidates']))
        self.assertFalse(any(x['kind']=='text_repeat' for x in s.detect(rows,10,{'priority_threshold':1})['candidates']))
    def test_normal_emphasis_not_deleted(self):
        d=s.detect([row('非常重要真的非常重要',0,2),row('非常重要真的非常重要',3,5)],10)
        self.assertTrue(d['candidates']);self.assertIsNone(d['executable_cuts']);self.assertTrue(all(x['status']=='needs_review' for x in d['candidates']))
    def test_short_repetition_not_high_confidence_mistake(self):
        self.assertEqual(s.detect([row('對對',0,1),row('對對',2,3)],10)['candidates'],[])
    def test_time_window_limits(self):
        self.assertEqual(s.detect([row('這次核心功能完整保留',0,2),row('這次核心功能完整保留',20,22)],30)['candidates'],[])
    def test_half_sentence_restart_below_threshold(self):
        q=s.detect([row('核心功能這個',0,2),row('核心功能可以支援完全不同的用途',3,5)],10)['candidates']
        self.assertTrue(any(x['kind']=='partial_restart' and x['text_similarity']<.9 for x in q))
    def test_low_similarity_rephrase_and_breath_are_candidates_only(self):
        q=s.detect([row('最初我們先嘗試第一種方法',0,2),row('換個說法用其他例子來解釋',2.6,5)],10,pauses=[(2,2.6)])['candidates']
        self.assertTrue(any(x['kind']=='pause_restart_or_rephrase' for x in q));self.assertTrue(all(x['action']=='review_only' for x in q))
    def test_raw_disfluency_confidence_preserved(self):
        raw={'segments':[row('呃我我不是不是這個',0,4,[{'word':'我','start':1,'end':1.2,'probability':.42}])]}
        before=json.dumps(raw);d=s.detect(raw,10)
        self.assertEqual(d['segments'][0]['text'],raw['segments'][0]['text']);self.assertEqual(d['segments'][0]['words'][0]['confidence'],.42);self.assertEqual(json.dumps(raw),before)
    def test_asr_omission_still_flags_timing(self):
        q=s.detect([row('只有整理後一句',0,5,[{'word':'角','start':1,'end':3.2}])],10)['candidates']
        self.assertTrue(any(x['kind']=='timing_anomaly' for x in q))
    @unittest.skipUnless((ROOT/'productions/dji-0044-pilot/evidence/transcript.json').exists(), 'Private pilot artifacts are not distributed')
    def test_real_0044_raw_asr_hidden_restart(self):
        raw=s.g.read(ROOT/'productions/dji-0044-pilot/evidence/transcript.json')
        q=s.detect(raw,198.681817)['candidates']
        self.assertTrue(any(x['kind']=='timing_anomaly' and x['right']['start']==80.96 and abs(x['right']['end']-83.16)<.001 for x in q))
    def test_unreviewed_source_cannot_authorize(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);f=p/'fixture';f.write_text('synthetic evidence, not listening')
            raw=p/'asr';s.g.write(raw,{'segments':[row('這次核心功能完整保留',0,2)]})
            packet={'schema':1,'run_id':'fixture','editor_id':'editor','duration':10,'files':{'source':s.g.record(f),'raw_asr':s.g.record(raw)},'versions':[s.g.record(x) for x in s.g.required_versions()], 'settings':s.DEFAULTS,'pause_scan':{'intervals':[]},'candidates':[]}
            report={'status':'needs_review','audio_review':[]};dispatch={}
            with patch.object(s.g,'media_duration',return_value=10):result=s.check(packet,report,dispatch)
            self.assertFalse(result['approved_for_cut_planning']);self.assertIn('source_audio_coverage',result['blockers']);self.assertIsNone(result['executable_cuts']);self.assertIn('blind_assessment_changed',result['blockers'])
    @unittest.skipUnless((ROOT/'productions/dji-0044-pilot/rough-cut-v1/source-timeline-map.json').exists(), 'Private pilot artifacts are not distributed')
    def test_legacy_map_cannot_bypass_post_gate(self):
        packet={'files':{'map':s.g.record(ROOT/'productions/dji-0044-pilot/rough-cut-v1/source-timeline-map.json')}}
        self.assertIn('source_review_missing_stale_or_unapproved',s.g.source_review_blockers(packet))
    def test_selected_first_take_and_rejected_retakes_enforced(self):
        spec=importlib.util.spec_from_file_location('plan',ROOT/'scripts/lab/plan-spoken-cut.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        packet={'duration':10,'candidates':[{'id':'R1'}]}
        review={'decisions':{'R1':{'classification':'retake','boundary_status':'verified','confirmed_keep_ranges':[[0,2]],'confirmed_remove_ranges':[[3,5]]}}}
        plan={'fps':'30','clips':[{'source_in_frame':0,'source_out_frame':60}]}
        module.validate_decisions(plan,packet,review) # first complete take, not always last
        plan['clips'][0]['source_out_frame']=150
        with self.assertRaises(ValueError):module.validate_decisions(plan,packet,review)
        plan['clips']=[{'source_in_frame':0,'source_out_frame':30},{'source_in_frame':0,'source_out_frame':30}]
        with self.assertRaises(ValueError):module.validate_decisions(plan,packet,review)
        plan['clips']=[{'source_in_frame':90,'source_out_frame':150}]
        with self.assertRaises(ValueError):module.validate_decisions(plan,packet,review)
    def test_executable_map_mutation_invalidates_approval(self):
        spec=importlib.util.spec_from_file_location('plan',ROOT/'scripts/lab/plan-spoken-cut.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'map.json';s.g.write(path,{'fps':'30','source_review':{'map_content_sha256':'obsolete'}})
            with self.assertRaisesRegex(ValueError,'map changed'):module.validate_authorized_plan(path)
    def test_frame_rate_nan_and_unbound_evidence_rejected(self):
        spec=importlib.util.spec_from_file_location('plan',ROOT/'scripts/lab/plan-spoken-cut.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'source';f.write_text('synthetic source')
            packet={'duration':10,'files':{'source':s.g.record(f)}}
            plan={'source':str(f),'fps':'1','total_seconds':1,'clips':[{'kind':'source','source_in_frame':0,'source_out_frame':1,'duration_frames':1,'timeline_in_frame':0}]}
            with patch.object(module.subprocess,'check_output',return_value=json.dumps({'streams':[{'avg_frame_rate':'30','r_frame_rate':'30'}]})):
                with self.assertRaisesRegex(ValueError,'FPS'):module.validate_plan(plan,packet)
                plan['fps']='30';plan['total_seconds']=float('nan')
                with self.assertRaisesRegex(ValueError,'duration'):module.validate_plan(plan,packet)
            evidence=Path(td)/'evidence.json';s.g.write(evidence,{'method':'asr','finding':'test'})
            clip={'boundary_status':'verified','boundary_evidence':s.g.record(evidence),'source_in_frame':0,'source_out_frame':1}
            with self.assertRaises(ValueError):module.validate_boundary(clip,packet,{'reviewer_id':'independent'})
    @unittest.skipUnless((ROOT/'productions/dji-0044-pilot/rough-cut-v1/DJI_0044-v1.mp4').exists(), 'Private pilot artifacts are not distributed')
    def test_pilot_render_entry_blocks_without_review_no_render(self):
        r=ROOT/'productions/dji-0044-pilot/rough-cut-v1';before=s.g.digest(r/'DJI_0044-v1.mp4')
        proc=subprocess.run([sys.executable,str(r/'render.py')],capture_output=True,text=True)
        self.assertNotEqual(proc.returncode,0);self.assertIn('Pre-cut independent source review required',proc.stderr);self.assertEqual(before,s.g.digest(r/'DJI_0044-v1.mp4'))

if __name__=='__main__':unittest.main()
