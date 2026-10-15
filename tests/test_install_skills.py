from pathlib import Path
import subprocess,tempfile,json,unittest,importlib.util,os,sys
ROOT=Path(__file__).resolve().parents[1]
class Installation(unittest.TestCase):
 def test_actual_offline_entry_and_backup(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d)/'空間 中文';dest=d/'codex-skills';state=d/'state'
   custom=dest/'caption-doctor';custom.mkdir(parents=True);(custom/'custom.txt').write_text('keep me')
   cmd=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'install-skills.ps1'),'-SkillsRoot',str(dest),'-StateDir',str(state),'-Python',sys.executable] if os.name=='nt' else ['bash',str(ROOT/'install.sh'),'--codex-only','--skills-only','--skills-root',str(dest),'--state-dir',str(state)]
   subprocess.run(cmd,check=True,stdout=subprocess.PIPE)
   manifest=json.loads((ROOT/'skills-manifest.json').read_text())
   for name in manifest['skills']:self.assertTrue((dest/name/'SKILL.md').is_file())
   loc=json.loads((dest/'spoken-edit-review/runtime-root.json').read_text());runtime=Path(loc['runtime_root'])
   self.assertEqual((runtime/'backups/caption-doctor/custom.txt').read_text(),'keep me')
   self.assertTrue((dest/'caption-doctor/scripts/caption_style.py').is_file())
   self.assertTrue((runtime/'scripts/lab/export-settings.py').is_file())
   spec=importlib.util.spec_from_file_location('installed_gate',dest/'spoken-edit-review/scripts/review_gate.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
   self.assertTrue(all(p.is_file() for p in g.required_versions()))
   for name in ['plan-spoken-cut.py','render-spoken-preview.py','deliver-spoken-cut.py']:
    subprocess.run([sys.executable,'-X','utf8',str(runtime/'scripts/lab'/name),'--help'],check=True,stdout=subprocess.PIPE)
   self.assertEqual(json.loads((runtime/'docs/reference-editing-lab/protected-phrases.json').read_text())['phrases'],[])
   for f in manifest['files']:self.assertEqual((ROOT/f).read_bytes(),(runtime/f).read_bytes())
