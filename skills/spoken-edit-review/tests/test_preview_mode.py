"""Synthetic protocol tests: no fixture claims actual media listening."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import test_review_gate as fixtures
from test_source_review import s

g=fixtures.g
spec=importlib.util.spec_from_file_location('preview_planner',Path(__file__).resolve().parents[3]/'scripts/lab/plan-spoken-cut.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PreviewTests(unittest.TestCase):
    def setUp(self):
        fixtures.GateTests.setUp(self)
        tech=g.read(self.p/'technical');tech.update(export_sha256=self.packet['files']['export']['sha256'],map_sha256=self.packet['files']['map']['sha256']);g.write(self.p/'technical',tech)
        self.packet['files']['technical']=g.record(self.p/'technical');self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.report.update(status='needs_review',actual_audio_review=False,audio_review=[],evidence_review_complete=True,
          evidence_review=[{'start':0,'end':10,'method':'codex_evidence_review','evidence_id':'audio','finding':'Synthetic evidence review; not listening'}],
          preview_decisions={},open_findings=[{'kind':'actual_audio_review_unavailable'}])
    def result(self):return g.gate(self.packet,self.report,self.dispatch,mode='preview')
    def test_preview_allowed_but_never_final(self):
        r=self.result();self.assertTrue(r['preview_allowed']);self.assertFalse(r['final_pass']);self.assertFalse(r['actual_audio_review']);self.assertEqual(r['content_status'],'needs_review');self.assertEqual(r['audio_review_coverage'],0)
        self.assertFalse(g.gate(self.packet,self.report,self.dispatch)['final_pass'])
    def test_preview_rejects_mixed_listening_claim_and_stale_qc(self):
        self.report['audio_review']=[{'start':0,'end':10,'method':'human_listening','evidence_id':'audio','finding':'contradictory fixture'}]
        self.assertFalse(self.result()['preview_allowed'])
        self.report['audio_review']=[]
        (self.p/'export').write_text('different synthetic export')
        self.packet['files']['export']=g.record(self.p/'export')
        self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.assertIn('preview_technical_artifact_mismatch',self.result()['blockers'])
    def test_preview_requires_independent_receipts(self):
        self.dispatch.pop('completion_receipt');self.assertFalse(self.result()['preview_allowed'])
    def test_preview_requires_real_full_evidence_coverage(self):
        self.report['evidence_review'][0]['end']=5;self.report['evidence_review']*=2
        r=self.result();self.assertFalse(r['preview_allowed']);self.assertEqual(r['evidence_review_coverage'],.5)
    def test_preview_rejects_stale_evidence_and_technical_failure(self):
        (self.p/'evidence').write_text('changed');self.assertFalse(self.result()['preview_allowed'])
        self.report['evidence']['audio']=g.record(self.p/'evidence')
        g.write(self.p/'technical',{'all_technical_checks_pass':True,'checks':[{'passed':False}]})
        self.packet['files']['technical']=g.record(self.p/'technical');self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.assertFalse(self.result()['preview_allowed'])
    def test_preview_requires_every_candidate_decision(self):
        cues=[{'kind':'possible_retake','start':2,'end':3}];g.write(self.p/'cues',cues)
        self.packet['files']['cues']=g.record(self.p/'cues');self.packet['issues']=g.candidates([],10,cues)
        self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.assertFalse(self.result()['preview_allowed'])
        self.report['preview_decisions']['Q0001']={'action':'keep','reason':'uncertain; preserve pending listening','evidence_id':'audio'}
        self.assertTrue(self.result()['preview_allowed'])
    def source_fixture(self):
        raw=self.p/'raw';g.write(raw,{'segments':[{'start':0,'end':10,'text':'full synthetic transcript','words':[]}]})
        packet={'schema':1,'run_id':'source-preview','editor_id':'editor','duration':10,
          'files':{'source':g.record(self.p/'source'),'raw_asr':g.record(raw),'asr_code':g.record(self.p/'version')},
          'versions':[g.record(x) for x in g.required_versions()], 'settings':s.DEFAULTS,'pause_scan':{'intervals':[]},'candidates':[]}
        self.report.update(run_id=packet['run_id'],blind_assessment={'record':g.record(self.p/'evidence'),'saw_editor_recommendations':False})
        dispatch={**self.dispatch,'run_id':packet['run_id'],'packet_content_sha256':g.hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest(),
          'blind_receipt':g.record(self.p/'receipt'),'blind_assessment_sha256':g.digest(self.p/'evidence')}
        return packet,dispatch
    def test_source_preview_works_final_still_requires_audio(self):
        packet,dispatch=self.source_fixture()
        with patch.object(s.g,'media_duration',return_value=10):
            r=s.check(packet,self.report,dispatch,mode='preview');self.assertTrue(r['approved_for_cut_planning']);self.assertFalse(r['final_pass'])
            self.assertFalse(s.check(packet,self.report,dispatch)['approved_for_cut_planning'])
            self.report['blind_assessment']['record']['sha256']='changed';self.assertFalse(s.check(packet,self.report,dispatch,mode='preview')['approved_for_cut_planning'])
    def test_map_must_be_reviewed_and_not_laundered_into_final(self):
        packet,dispatch=self.source_fixture()
        e=self.p/'boundary';g.write(e,{'method':'codex_evidence_review','actual_audio_review':False,'reviewer_id':'reviewer','finding':'synthetic quiet handle',
          'source_sha256':packet['files']['source']['sha256'],'source_in_frame':0,'source_out_frame':300,'inputs':[g.record(self.p/'evidence')]})
        plan={'review_mode':'preview','actual_audio_review':False,'content_status':'needs_review','final_pass':False,'unresolved_findings':['listening unavailable'],
          'clips':[{'source_in_frame':0,'source_out_frame':300,'boundary_status':'candidate_evidence_reviewed','boundary_evidence':g.record(e)}]}
        self.report['preview_map_content_sha256']=p.content_hash(plan);p.validate_preview_plan(plan,packet,self.report)
        plan['clips'][0]['source_out_frame']=299
        with self.assertRaisesRegex(ValueError,'not independently reviewed'):p.validate_preview_plan(plan,packet,self.report)
        plan['clips'][0]['source_out_frame']=300
        # Bound map default path cannot be promoted by a final-looking report.
        for name,obj in [('packet',packet),('review',self.report),('dispatch',dispatch)]:g.write(self.p/name,obj)
        plan['source_review']={'mode':'preview','map_content_sha256':p.content_hash(plan),'run_id':packet['run_id'],**{k:g.record(self.p/k) for k in ['packet','review','dispatch']}}
        g.write(self.p/'bound-map',plan)
        with self.assertRaisesRegex(ValueError,'cannot authorize final'):p.validate_authorized_plan(self.p/'bound-map')

if __name__=='__main__':unittest.main()
