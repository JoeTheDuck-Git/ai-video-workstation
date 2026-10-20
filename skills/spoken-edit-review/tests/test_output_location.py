import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('locations_test',ROOT/'scripts/lab/output-location.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class OutputPolicyTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.p=Path(t.name).resolve();self.mount=self.p/'drive';self.root=self.mount/'exports';self.root.mkdir(parents=True);self.cfg=self.p/'config.json';self.cfg.write_text(json.dumps({'mount_path':str(self.mount),'output_root':str(self.root)}))
 def test_missing_mount_stops_without_creating_folders(self):
  with patch.object(m.os.path,'ismount',return_value=False):
   with self.assertRaisesRegex(ValueError,'not mounted'):m.policy(self.cfg)
  self.assertEqual(list(self.root.iterdir()),[])
 def test_readonly_drive_stops(self):
  with patch.object(m.os.path,'ismount',return_value=True),patch.object(m.os,'access',return_value=False):
   with self.assertRaisesRegex(ValueError,'not writable'):m.policy(self.cfg)
 def test_relative_routes_external_and_local_absolute_blocked(self):
  with patch.object(m.os.path,'ismount',return_value=True):
   r=m.policy(self.cfg);d,root=m.destination('film/version2',self.p,r);self.assertEqual(d,self.root/'film/version2');self.assertEqual(root,self.root)
   with self.assertRaisesRegex(ValueError,'external output root'):m.destination(self.p/'internal',self.p,r)
   self.assertFalse(d.exists())
 def test_config_change_and_link_escape_blocked(self):
  with patch.object(m.os.path,'ismount',return_value=True):
   r=m.policy(self.cfg);link=self.root/'escape'
   try:link.symlink_to(self.p,target_is_directory=True)
   except OSError:self.skipTest('symlink unavailable')
   with self.assertRaisesRegex(ValueError,'external output root'):m.destination(link/'output',self.p,r)
   self.cfg.write_text(self.cfg.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'changed'):m.destination('film/version2',self.p,r)
if __name__=='__main__':unittest.main()
