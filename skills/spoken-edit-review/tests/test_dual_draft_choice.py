import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('draft_base',Path(__file__).with_name('test_draft_package_choice.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
r=b.r
class DualDraftTests(unittest.TestCase):
 setUp=b.DraftChoiceTests.setUp
 prepare=b.DraftChoiceTests.prepare
 choice_job=b.DraftChoiceTests.choice_job
 authorized_files=b.DraftChoiceTests.authorized_files
 def test_yes_without_product_stays_pending_and_does_not_render(self):
  j=self.choice_job({'requested':True});self.assertEqual(j['draft_package']['status'],'pending_target')
  with self.assertRaisesRegex(ValueError,'目標待確認'):r.render(*self.authorized_files(j))
  self.assertFalse(self.dest.exists())
 def test_both_keep_versions_and_validation_separate(self):
  j=self.choice_job({'requested':True,'selection':'both','materials':'reference','targets':{'capcut':{'platform':'macOS','version':'8.9.4322','build':'9.0.0-beta4'}}})
  t=j['draft_package']['targets'];self.assertEqual(set(t),{'capcut','jianying'})
  self.assertEqual(t['capcut']['version'],'8.9.4322');self.assertIsNone(t['jianying']['version'])
  self.assertEqual(t['jianying']['missing_details'],['platform','version'])
  for x in t.values():
   self.assertEqual(x['validation_status'],'not_tested');self.assertEqual(x['support_status'],'unsupported');self.assertIsNone(x['artifact'])
  self.assertNotEqual(t['capcut']['planned_output_dir'],t['jianying']['planned_output_dir'])
  with self.assertRaisesRegex(ValueError,'尚未支援'):r.render(*self.authorized_files(j))
  self.assertFalse(self.dest.exists())
 def test_capcut_only_and_no_preserve_intent(self):
  j=self.choice_job({'requested':True,'selection':'capcut'});self.assertEqual(set(j['draft_package']['targets']),{'capcut'})
  self.assertEqual(self.choice_job({'requested':False})['draft_package']['status'],'not_requested')
  self.assertEqual(self.choice_job({'requested':None,'selection':'both'})['draft_package']['status'],'pending_confirmation')
 def test_legacy_alias_maps_only_to_jianying_and_conflict_rejected(self):
  opts=self.prepare()['export_choices'];opts['jianying_draft']={'requested':True,'platform':'Windows','version':'old exact','materials':'copy'}
  j=self.prepare(export_choices=opts);self.assertEqual(j['draft_package']['selection'],'jianying');self.assertNotIn('jianying_draft',j)
  self.assertEqual(j['draft_package']['targets']['jianying']['version'],'old exact')
  opts['draft_package']={'requested':False}
  with self.assertRaisesRegex(ValueError,'conflicting'):self.prepare(export_choices=opts)
 def test_cannot_inject_success_or_other_target(self):
  for value in [{'requested':True,'selection':'both','targets':{'capcut':{'support_status':'supported'}}},
                {'requested':True,'selection':'capcut','targets':{'jianying':{'version':'x'}}},
                {'requested':True,'selection':'both','targets':{'capcut':{'artifact':'fake'}}}]:
   with self.assertRaises(ValueError):self.choice_job(value)
if __name__=='__main__':unittest.main()
