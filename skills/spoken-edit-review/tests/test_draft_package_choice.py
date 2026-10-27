"""Intent/state integration only: never render, export drafts, or use real media."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('renderer_fixture',Path(__file__).with_name('test_preview_renderer.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
r=f.r

class DraftChoiceTests(unittest.TestCase):
    setUp=f.RendererUnitTests.setUp
    prepare=f.RendererUnitTests.prepare

    def choice_job(self, choice):
        base=self.prepare()
        choices=copy.deepcopy(base['export_choices']);choices['draft_package']=choice
        return self.prepare(export_choices=choices)

    def authorized_files(self, job):
        j=self.tmp/'job.json';a=self.tmp/'auth.json';r.g.write(j,job)
        r.g.write(a,{'render_authorized':True,'instruction':'Synthetic unit test only',
          'job_sha256':r.g.digest(j),'map_sha256':job['map']['sha256'],
          'renderer_sha256':job['renderer']['sha256'],'resolution':job['resolution']})
        return j,a

    def test_missing_remains_pending_and_blocks_output(self):
        job=self.prepare();state=job['draft_package']
        self.assertIsNone(state['requested']);self.assertEqual(state['status'],'pending_confirmation')
        with self.assertRaisesRegex(ValueError,'待確認'):r.render(*self.authorized_files(job))
        self.assertFalse(self.dest.exists())

    def test_no_preserves_video_settings_and_roundtrip(self):
        before=self.prepare();job=self.choice_job({'requested':False})
        self.assertEqual(job['export_settings'],before['export_settings'])
        self.assertEqual(job['compiled'],before['compiled']);self.assertEqual(job['source_clips'],before['source_clips'])
        self.assertEqual(job['draft_package']['status'],'not_requested')
        r.draft_choice.require_video_render(job['draft_package'])
        j,a=self.authorized_files(job);self.assertEqual(r.validate_job(j),job)
        self.assertFalse(self.dest.exists())

    def test_yes_missing_and_complete_are_unsupported_without_movie_fallback(self):
        for choice in ({'requested':True,'selection':'jianying'},{'requested':True,'selection':'jianying','targets':{'jianying':{'platform':'Windows','version':'user-supplied 1.2.3'}},'materials':'copy'}):
            with self.subTest(choice=choice):
                job=self.choice_job(choice);state=job['draft_package']
                self.assertEqual(state['status'],'unsupported');self.assertFalse(state['generation_allowed'])
                self.assertIsNone(state['artifact']);self.assertFalse(state['exporter_available'])
                self.assertEqual(state['targets']['jianying']['missing_details'],['platform','version','materials'] if 'targets' not in choice else [])
                with self.assertRaisesRegex(ValueError,'尚未支援'):r.render(*self.authorized_files(job))
                self.assertFalse(self.dest.exists())

    def test_reference_option_and_external_location_preserved(self):
        mount=self.tmp/'drive';root=mount/'exports';root.mkdir(parents=True)
        cfg=self.tmp/'policy.json';cfg.write_text(json.dumps({'mount_path':str(mount),'output_root':str(root)}))
        choices=self.prepare()['export_choices'];choices['draft_package']={'requested':True,'selection':'jianying','targets':{'jianying':{'platform':'macOS','version':'exact version'}},'materials':'reference'}
        with patch.object(r.locations.os.path,'ismount',return_value=True):
            policy=r.locations.policy(cfg)
            job=self.prepare(export_choices=choices,output_dir='film/v3',output_policy=policy)
        self.assertEqual(job['draft_package']['targets']['jianying']['planned_output_dir'],str(root.resolve()/'film/v3/jianying-draft'))
        self.assertEqual(job['draft_package']['materials'],'reference');self.assertEqual(job['output_policy'],policy)
        self.assertFalse((root/'film').exists())
        j,a=self.authorized_files(job)
        with patch.object(r.locations.os.path,'ismount',return_value=False):
            with self.assertRaisesRegex(ValueError,'not mounted'):r.validate_job(j)

    def test_malformed_or_capcut_choices_not_guessed(self):
        for choice in ('yes',{'requested':'yes'},{'requested':1},{'platform':'CapCut'}, {'platform':'iOS'}, {'version':''}, {'materials':'upload'},{'generated':True}):
            with self.subTest(choice=choice):
                with self.assertRaises(ValueError):self.choice_job(choice)
        self.assertFalse(self.dest.exists())

    def test_intent_or_state_tampering_rejected(self):
        original=self.choice_job({'requested':True})
        for field in ('draft_package','export_choices','draft_choice_module'):
            job=copy.deepcopy(original)
            if field=='draft_package':job[field]['requested']=False
            elif field=='export_choices':job[field]['draft_package']['requested']=False
            else:job[field]['sha256']='changed'
            j,a=self.authorized_files(job)
            with self.assertRaises(ValueError):r.validate_job(j)
        self.assertFalse(self.dest.exists())

if __name__=='__main__':unittest.main()
