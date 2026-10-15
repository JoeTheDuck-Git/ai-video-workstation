import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/review_gate.py'
spec = importlib.util.spec_from_file_location('review_gate', SCRIPT)
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class GateTests(unittest.TestCase):
    def setUp(self):
        source_mock=patch.object(g,'source_review_blockers',return_value=[]);source_mock.start();self.addCleanup(source_mock.stop)
        # These original tests isolate post-cut gate behavior; source gate has its own tests.
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        for name in ['source', 'export', 'map', 'version', 'receipt', 'evidence']:
            (self.p/name).write_text('test fixture only: ' + name)
        g.write(self.p/'map', {'total_seconds':10})
        mock = patch.object(g, 'media_duration', return_value=10); mock.start(); self.addCleanup(mock.stop)
        g.write(self.p/'technical', {'all_technical_checks_pass': True, 'checks': [{'passed': True}]})
        g.write(self.p/'asr', [{'start': 0, 'end': 10, 'words': []}])
        self.packet = g.prepare({'duration': 10, 'editor_id': 'editor',
          'files': {k: str(self.p/k) for k in ['source','export','map','technical','asr']},
          'versions': [str(self.p/'version')],
          'implementations':{k:str(self.p/'version') for k in ['renderer','technical_qc','asr']}})
        self.dispatch = {'tool':'collaboration.spawn_agent', 'agent_id':'reviewer',
          'run_id': self.packet['run_id'], 'packet_sha256':'fixture',
          'packet_content_sha256':g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest(),
          'tool_receipt':g.record(self.p/'receipt'), 'completion_receipt':g.record(self.p/'receipt')}
        self.report = {'reviewer_id':'reviewer','run_id':self.packet['run_id'],'packet_sha256':'fixture','status':'pass',
          'evidence':{'audio':g.record(self.p/'evidence')},
          'audio_review':[{'start':0,'end':10,'method':'human_listening','evidence_id':'audio','finding':'synthetic fixture'}],
          'interiors_reviewed':True,'joins_and_ending_reviewed':True,'issue_resolutions':{},'open_findings':[]}

    def test_point_cues_preserved_and_invalid_rejected(self):
        q=g.candidates([],10,[{'kind':'user','start':5,'end':5,'details':'one'},{'kind':'user','start':5,'end':5,'details':'two'}])
        self.assertEqual(len(q),2);self.assertEqual(q[0]['start'],4.5)
        for a,b in [(6,5),(-1,3),(2,11),(float('nan'),3)]:
            with self.assertRaises(ValueError):g.candidates([],10,[{'kind':'user','start':a,'end':b}])
    def test_duration_underreport_blocked(self):
        config={'duration':5,'editor_id':'editor','files':{k:str(self.p/k) for k in ['source','export','map','technical','asr']},'versions':[str(self.p/'version')],'implementations':{k:str(self.p/'version') for k in ['renderer','technical_qc','asr']}}
        with self.assertRaises(ValueError):g.prepare(config)
    def test_missing_required_rule_blocks(self):
        self.packet['versions']=[g.record(self.p/'version')]
        self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.assertIn('required_rules_missing',self.result()['blockers'])
    def result(self):return g.gate(self.packet,self.report,self.dispatch)
    def test_complete_structural_fixture(self):self.assertTrue(self.result()['final_pass'])
    def test_needs_review_not_pass(self):
        self.report['status']='needs_review';self.assertFalse(self.result()['final_pass'])
    def test_asr_not_listening(self):
        self.report['audio_review'][0]['method']='asr';self.assertFalse(self.result()['final_pass'])
    def test_overlap_not_fake_full_coverage(self):
        self.report['audio_review'][0]['end']=6
        self.report['audio_review']*=2
        self.assertEqual(self.result()['audio_review_coverage'],.6)
        self.assertFalse(self.result()['final_pass'])
    def test_zero_coverage(self):
        self.report['audio_review']=[];self.assertFalse(self.result()['final_pass'])
    def test_self_review_and_missing_receipt(self):
        self.dispatch['agent_id']='editor';self.dispatch.pop('completion_receipt');self.assertFalse(self.result()['final_pass'])
    def test_changed_media_map_rule_and_evidence(self):
        for name in ['source','export','map','version','evidence']:
            with self.subTest(name=name):
                f=self.p/name;old=f.read_text();f.write_text('changed')
                self.assertFalse(self.result()['final_pass']);f.write_text(old)
    def test_0043_known_boundary_farewell_freeze_block(self):
        for kind in ['residual_syllable','farewell_truncated','authored_freeze']:
            with self.subTest(kind=kind):
                cues=[{'kind':kind,'start':2,'end':3}]
                g.write(self.p/'cues',cues);self.packet['files']['cues']=g.record(self.p/'cues')
                self.packet['issues']=g.candidates([],10,cues)
                self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
                self.assertIn('unresolved_candidate:Q0001',self.result()['blockers'])
    def test_normal_emphasis_breath_no_auto_delete(self):
        cues=g.candidates([{'start':0,'end':10,'words':[{'text':'非常','start':1,'end':3}]}],10,[{'kind':'low_energy','start':4,'end':4.5}])
        self.assertTrue(cues);self.assertTrue(all(x['action']=='review_only' for x in cues))
        g.write(self.p/'cues',[{'kind':x['kind'],'start':x['start'],'end':x['end'],'details':x['details']} for x in cues])
        self.packet['files']['cues']=g.record(self.p/'cues')
        self.packet['issues']=cues
        self.dispatch['packet_content_sha256']=g.hashlib.sha256(json.dumps(self.packet,sort_keys=True).encode()).hexdigest()
        self.report['issue_resolutions']={x['id']:{'disposition':'intentional_keep','reason':'fixture: emphasis / normal breath in context','evidence_id':'audio'} for x in cues}
        self.assertTrue(self.result()['final_pass'])
    def test_context_short_window_disagreement(self):
        a={'start':0,'end':4,'words':[{'text':'核心能力是新視角','start':1,'end':3}]}
        b={'start':0,'end':4,'words':[{'text':'核心能力是新預測核心能力是新視角','start':1,'end':3}]}
        self.assertTrue(any(x['kind']=='window_disagreement' for x in g.candidates([a,b],4)))
    def test_real_0044_merged_asr_flags(self):
        root=Path(__file__).resolve().parents[3]
        f=root/'productions/dji-0044-pilot/rough-cut-v1/final-asr.json'
        if not f.exists():self.skipTest('Private pilot artifacts are not distributed')
        q=g.candidates(g.read(f),176.6765)
        self.assertTrue(any(x['kind']=='long_word' and x['details'].get('word')=='角' and 70<x['start']<73 for x in q))
    def test_real_0043_evidence_regressions(self):
        root=Path(__file__).resolve().parents[3]/'productions/dji-0043-pilot'
        if not (root/'rough-cut-v5-natural/audio-diagnosis/measurements.json').exists():self.skipTest('Private pilot artifacts are not distributed')
        data=g.read(root/'rough-cut-v5-natural/audio-diagnosis/measurements.json')
        incoming=next(x for x in data if x['name']=='source_in')
        ending=next(x for x in data if x['name']=='source_ending')
        # Real recorded energy around the failed in-point and after the failed out-point.
        self.assertTrue(any(abs(t-incoming['cut'])<.05 and db>-25 for t,db in incoming['rms_20ms_dbfs']))
        self.assertTrue(any(ending['cut']<t<ending['cut']+.8 and db>-25 for t,db in ending['rms_20ms_dbfs']))
        oldmap=g.read(root/'rough-cut-v4-review/source-timeline-map.json')
        holds=[c for c in oldmap['clips'] if c['kind']=='hold']
        self.assertTrue(any(c['duration_frames']==15 for c in holds))
        cues=[{'kind':'residual_syllable','start':39.7,'end':40.3,'details':incoming},
              {'kind':'farewell_truncated','start':170,'end':171,'details':ending},
              {'kind':'authored_freeze','start':82.1487,'end':82.399,'details':holds}]
        q=g.candidates([],180,cues)
        self.assertEqual(len(q),3);self.assertTrue(all(x['status']=='open' and x['action']=='review_only' for x in q))
    def test_new_reviewer_finding_blocks(self):
        self.report['open_findings']=[{'kind':'retake'}];self.assertFalse(self.result()['final_pass'])

if __name__=='__main__':unittest.main()
