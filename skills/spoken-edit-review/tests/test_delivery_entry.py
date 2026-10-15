import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import test_review_gate as fixtures
g=fixtures.g

entry_path=Path(__file__).resolve().parents[3]/'scripts/lab/deliver-spoken-cut.py'
spec=importlib.util.spec_from_file_location('delivery_entry',entry_path)
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)

class EntryTests(unittest.TestCase):
    def setUp(self):
        fixtures.GateTests.setUp(self)
        source_mock=patch.object(entry.g,'source_review_blockers',return_value=[]);source_mock.start();self.addCleanup(source_mock.stop)
        mock=patch.object(entry.g,'media_duration',return_value=10);mock.start();self.addCleanup(mock.stop)
        g.write(self.p/'packet.json',self.packet)
        self.dispatch['packet_sha256']=g.digest(self.p/'packet.json')
        self.report['packet_sha256']=self.dispatch['packet_sha256']
        self.report['status']='needs_review';self.report['audio_review']=[]
        g.write(self.p/'dispatch.json',self.dispatch)
        self.args=[str(self.p/x) for x in ['packet.json','report.json','dispatch.json','delivery.json']]
    def invoke(self,mode=None):
        g.write(self.p/'report.json',self.report)
        return entry.main(self.args+(['--mode',mode] if mode else [])),g.read(self.p/'delivery.json')
    def test_default_final_blocks_needs_review(self):
        rc,d=self.invoke();self.assertEqual(rc,2);self.assertFalse(d['delivery_allowed']);self.assertIsNone(d['artifact'])
    def test_explicit_draft_cannot_claim_final(self):
        rc,d=self.invoke('draft');self.assertEqual(rc,0);self.assertFalse(d['final_pass']);self.assertEqual(d['label'],'UNREVIEWED_DRAFT')
    def test_draft_rejects_stale_map(self):
        (self.p/'map').write_text('changed')
        rc,d=self.invoke('draft');self.assertEqual(rc,2);self.assertFalse(d['delivery_allowed'])
    def test_missing_receipt_replaces_old_allowed_output(self):
        g.write(self.p/'delivery.json',{'delivery_allowed':True})
        (self.p/'dispatch.json').unlink()
        rc,d=self.invoke();self.assertEqual(rc,2);self.assertFalse(d['delivery_allowed'])

if __name__=='__main__':unittest.main()
