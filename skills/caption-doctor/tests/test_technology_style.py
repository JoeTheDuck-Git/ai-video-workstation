import sys,tempfile,unittest,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from caption_style import format_technology_caption as fmt, ass_text, format_caption
from captiondoctor import parse_srt,write_srt,pangu,preserve

class TechnologyStyle(unittest.TestCase):
 def test_commas(self):
  self.assertEqual(fmt('先備份，再登入,最後確認'),'先備份  再登入  最後確認')
 def test_existing_spaces(self):
  self.assertEqual(fmt('甲  ，   乙'), '甲  乙')
  self.assertEqual(fmt('甲，，乙'), '甲  乙')
 def test_number_groups(self):
  self.assertEqual(fmt('1,234,567 美金，提升 1.5 倍！'),'1,234,567 美金  提升 1.5 倍！')
  self.assertEqual(fmt('12，345 元，完成'),'12，345 元  完成')
 def test_numeric_group_before_phrase_comma(self):
  self.assertEqual(fmt('金額1,234,567，完成。'),'金額1,234,567  完成')
  self.assertEqual(fmt('1,234,下一項'),'1,234  下一項')
  self.assertEqual(fmt('1,234,567, next'),'1,234,567  next')
 def test_not_all_numeric_commas_are_thousands(self):
  self.assertEqual(fmt('選項 1,2,3'),'選項 1  2  3')
 def test_edges(self):
  self.assertEqual(fmt('，先備份，\n，再登入,  '),'先備份\n再登入')
  self.assertEqual(fmt('，\n , '),'')
 def test_meaningful_marks(self):
  self.assertEqual(fmt('真的嗎？\n回來了！\n版本 1.5〔待核對〕。'),'真的嗎？\n回來了！\n版本 1.5〔待核對〕')
  self.assertEqual(fmt('等等...'),'等等...')
 def test_idempotence_and_normalizer(self):
  text=fmt('Meta，Manus'); self.assertEqual(fmt(text),text)
  self.assertEqual(pangu(text),text)
  self.assertEqual(text,'Meta'+chr(32)*2+'Manus')
 def test_ass_and_srt_same_text_and_times(self):
  text=fmt('先備份，再登入\n保留 1,234 元')
  self.assertEqual(ass_text(text),r'先備份  再登入\N保留 1,234 元')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'captions.srt'; cues=[{'start':1.2,'end':3.4,'text':text}]
   write_srt(cues,p)
   self.assertEqual(parse_srt(p),cues)
   self.assertEqual(preserve(parse_srt(p),False),cues)
 def test_cli_style_and_empty_cue(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'in.srt';out=Path(d)/'out.srt'
   write_srt([{'start':1.,'end':3.,'text':'甲，乙\n金額 1,234 元。'},{'start':4.,'end':5.,'text':'，'}],src)
   subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/captiondoctor.py'),str(src),'--out',str(out),'--technology-style'],check=True,capture_output=True)
   cues=parse_srt(out);self.assertEqual(len(cues),1);self.assertEqual(cues[0]['text'],'甲  乙\n金額 1,234 元');self.assertEqual((cues[0]['start'],cues[0]['end']),(1.,3.))
 def test_reject_estimated_reflow(self):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/captiondoctor.py'),'unused.srt','--technology-style','--reflow'],capture_output=True)
  self.assertEqual(p.returncode,2)

class PunctuationChoices(unittest.TestCase):
 def test_no_punctuation_unicode_numeric_and_runs(self):
  self.assertEqual(format_caption('「售價 1,234 元」，提升 1.5 倍？！', 'no-punctuation'), '售價 1  234 元  提升 1  5 倍')
  self.assertEqual(format_caption('甲  ，！？  乙；丙：丁、戊……己...庚', 'no-punctuation'), '甲  乙  丙  丁  戊  己  庚')
 def test_lines_uncertainty_and_idempotence(self):
  text=format_caption('，甲？\n〔待核對〕：乙！\n？！？', 'no-punctuation')
  self.assertEqual(text, '甲\n待核對  乙')
  self.assertEqual(format_caption(text, 'no-punctuation'), text)
  self.assertEqual(ass_text(text), r'甲\N待核對  乙')
 def test_existing_is_unchanged(self):
  text='金額 1,234 元，成長 1.5 倍！'
  self.assertEqual(format_caption(text,'existing'),fmt(text))
 def test_cli_choices_preserve_times(self):
  script=Path(__file__).resolve().parents[1]/'scripts/captiondoctor.py'
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'in.srt'; out=Path(d)/'out.srt'
   write_srt([{'start':1.2,'end':3.4,'text':'甲？乙，金額 1,234 元。'},{'start':4.,'end':5.,'text':'，'}], src)
   for mode,expected in [('no-punctuation','甲  乙  金額 1  234 元'),('existing','甲？乙  金額 1,234 元')]:
    subprocess.run([sys.executable,str(script),str(src),'--out',str(out),'--punctuation-style',mode],check=True,capture_output=True)
    self.assertEqual(parse_srt(out),[{'start':1.2,'end':3.4,'text':expected}])
   p=subprocess.run([sys.executable,str(script),str(src),'--punctuation-style','no-punctuation','--reflow'],capture_output=True)
   self.assertEqual(p.returncode,2)

if __name__=='__main__':unittest.main()
