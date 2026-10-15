"""Renderer unit tests isolate validated-plan input. Separate integration tests reject stale real evidence. No encoder runs; synthetic fixtures never authorize production."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('preview_renderer',ROOT/'scripts/lab/render-spoken-preview.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
HISTORICAL_MAP=ROOT/'productions/private-regression/planned-preview.json.map.json'

class RendererUnitTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.tmp=Path(tmp.name)
        self.dest=ROOT/'productions'/('test-never-render-'+self.tmp.name)
        # Only downstream renderer behavior is isolated here. The real source-review
        # gates are exercised separately below and in test_preview_mode.py.
        source=self.tmp/'synthetic-source';source.write_bytes(b'not media: unit fixture only')
        plan={'version':'synthetic-renderer-fixture','source':str(source),'fps':'60000/1001',
          'review_mode':'preview','source_review':{'mode':'preview'},'target_max_seconds':180,
          'total_frames':10408,'total_seconds':10408/(60000/1001),'gain_db':-3.8,'clips':[]}
        pos=0
        for i,(lo,hi) in enumerate([(0,1978),(2571,4711),(4893,9819),(10510,11874)]):
            plan['clips'].append({'id':f'fixture-{i}','kind':'source','source_in_frame':lo,'source_out_frame':hi,'duration_frames':hi-lo,'timeline_in_frame':pos});pos+=hi-lo
        self.map=self.tmp/'synthetic-map.json';r.g.write(self.map,plan)
        validator=patch.object(r.planner,'validate_authorized_plan',return_value=plan)
        self.validator=validator.start();self.addCleanup(validator.stop)
        probe=patch.object(r,'probe_source',return_value=({'width':3840,'height':2160,'sample_aspect_ratio':'1:1'},{'sample_rate':'48000','channels':2}))
        probe.start();self.addCleanup(probe.stop)

        original=subprocess.run
        def no_encoder(cmd,*args,**kwargs):
            if Path(cmd[0]).name=='ffmpeg':raise AssertionError('Test must never execute encoder')
            return original(cmd,*args,**kwargs)
        p=patch.object(r.subprocess,'run',side_effect=no_encoder);p.start();self.addCleanup(p.stop)
    def prepare(self,res='480p',**kw):
        args=dict(map_path=self.map,expected_sha=r.g.digest(self.map),expected_version='synthetic-renderer-fixture',resolution=res,output_dir=self.dest);args.update(kw)
        return r.prepare_job(**args)
    def test_four_span_fixture_compiles_native_samples(self):
        j=self.prepare();c=j['compiled']
        self.assertEqual([(x['source_in_frame'],x['source_out_frame']) for x in j['source_clips']],[(0,1978),(2571,4711),(4893,9819),(10510,11874)])
        self.assertIn('trim=start_frame=2571:end_frame=4711',c['filter_graph']);self.assertIn('concat=n=4',c['filter_graph'])
        self.assertEqual(c['source_audio_sample_spans'][1],[2058857,3772569]);self.assertAlmostEqual(c['expected_duration'],173.6401333333)
        self.assertEqual((c['width'],c['height']),(854,480));self.assertEqual(c['display_aspect_ratio'],'16/9');self.assertEqual(c['sample_aspect_ratio'],'1280/1281')
        self.assertFalse(self.dest.exists())
    def test_resolution_changes_geometry_not_cuts(self):
        a=self.prepare('480p');b=self.prepare('720p');self.assertEqual(a['source_clips'],b['source_clips']);self.assertEqual(a['map'],b['map'])
        self.assertEqual((b['compiled']['width'],b['compiled']['height']),(1280,720));self.assertEqual(b['compiled']['export_fps'],'30000/1001')
    def test_wrong_expected_sha_or_version_blocks(self):
        with self.assertRaisesRegex(ValueError,'Wrong map SHA'):self.prepare(expected_sha='0'*64)
        with self.assertRaisesRegex(ValueError,'Wrong map version'):self.prepare(expected_version='0044-v1')
    def test_job_tampering_renderer_binding_and_new_output_guard(self):
        j=self.prepare();f=self.tmp/'job.json';r.g.write(f,j);self.assertEqual(r.validate_job(f),j)
        changed=copy.deepcopy(j);changed['compiled']['filter_graph']='old v1 graph';r.g.write(f,changed)
        with self.assertRaisesRegex(ValueError,'Job settings'):r.validate_job(f)
        changed=copy.deepcopy(j);changed['renderer']['sha256']='wrong';r.g.write(f,changed)
        with self.assertRaisesRegex(ValueError,'version binding'):r.validate_job(f)
        self.dest.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'new directory'):self.prepare(output_dir=self.dest)
    def test_no_resume_no_encode_or_output_creation(self):
        j=self.prepare();f=self.tmp/'job.json';a=self.tmp/'auth.json';r.g.write(f,j);r.g.write(a,{'render_authorized':False})
        with self.assertRaisesRegex(ValueError,'resume instruction'):r.render(f,a)
        self.assertFalse(self.dest.exists())
        r.g.write(a,{'render_authorized':True,'instruction':'Synthetic test only','job_sha256':'stale','map_sha256':j['map']['sha256'],'renderer_sha256':j['renderer']['sha256'],'resolution':'480p'})
        with self.assertRaisesRegex(ValueError,'resume instruction'):r.render(f,a)
        self.assertFalse(self.dest.exists())
    def test_command_no_overwrite_and_uses_job_source(self):
        j=self.prepare();cmd=r.ffmpeg_command(j,self.tmp/'filters',self.tmp/'output.mp4')
        self.assertIn('-n',cmd);self.assertNotIn('-y',cmd);self.assertEqual(cmd[cmd.index('-i')+1],j['source']['path'])
        self.assertIn('libx264',cmd);self.assertIn('aac',cmd)

@unittest.skipUnless(HISTORICAL_MAP.exists(), 'Private historical map is not distributed')
class ReviewBindingIntegrationTests(unittest.TestCase):
    """Use actual planner/gates and historical evidence, never the unit stubs."""
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.tmp=Path(tmp.name)
        self.dest=ROOT/'productions'/('test-stale-never-render-'+self.tmp.name)
        original=subprocess.run
        def no_encoder(cmd,*args,**kwargs):
            if Path(cmd[0]).name=='ffmpeg':raise AssertionError('Encoder must not run')
            return original(cmd,*args,**kwargs)
        encoder=patch.object(r.subprocess,'run',side_effect=no_encoder)
        encoder.start();self.addCleanup(encoder.stop)
    def prepare(self,**kw):
        args=dict(map_path=HISTORICAL_MAP,expected_sha=r.g.digest(HISTORICAL_MAP),expected_version='0044-v2-preview-candidate',resolution='480p',output_dir=self.dest);args.update(kw)
        return r.prepare_job(**args)
    def test_historical_review_rejected_after_rule_update(self):
        plan=r.g.read(HISTORICAL_MAP);binding=plan['source_review']
        result=r.planner.s.authorize(*[binding[k]['path'] for k in ['packet','review','dispatch']],mode='preview')
        self.assertFalse(result['approved_for_cut_planning'])
        self.assertIn('stale_source_evidence',result['blockers'])
        packet=r.g.read(binding['packet']['path'])
        stale=[x['path'] for x in packet['versions'] if not r.g.intact(x)]
        self.assertIn(str(ROOT/'skills/spoken-edit-review/SKILL.md'),stale)
        with self.assertRaisesRegex(ValueError,'Source review not approved'):self.prepare()
        self.assertFalse(self.dest.exists())
    def test_legacy_v1_even_with_matching_file_hash_rejected(self):
        old=ROOT/'productions/dji-0044-pilot/rough-cut-v1/source-timeline-map.json'
        with self.assertRaises(ValueError):self.prepare(map_path=old,expected_sha=r.g.digest(old),expected_version='0044-v1')
    def test_modified_map_cannot_be_authorized_by_its_new_file_hash(self):
        data=r.g.read(HISTORICAL_MAP);data['clips'][1]['source_out_frame']=5000;f=self.tmp/'changed-map.json';r.g.write(f,data)
        with self.assertRaisesRegex(ValueError,'map changed'):self.prepare(map_path=f,expected_sha=r.g.digest(f))

if __name__=='__main__':unittest.main()
