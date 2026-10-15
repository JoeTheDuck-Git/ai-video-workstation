import json,copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from contracts import Bundle
class ContractTests(unittest.TestCase):
    def setUp(self):self.b=json.loads((ROOT/'fixtures/synthetic-bundle.json').read_text())
    def reject(self,mutate):
        mutate(self.b)
        with self.assertRaises(ValueError):Bundle.model_validate(self.b)
    def test_valid_synthetic_fractional_rate(self):Bundle.model_validate(self.b)
    def test_out_of_bounds(self):self.reject(lambda b:b['plan']['clips'][0]['source'].update(end_tick=100000))
    def test_negative_interval(self):self.reject(lambda b:b['annotations'][0]['span'].update(start_tick=-1))
    def test_duplicate_ids(self):self.reject(lambda b:b['media'].append(copy.deepcopy(b['media'][0])))
    def test_stale_profile(self):self.reject(lambda b:b['plan'].update(profile_version=2))
    def test_wrong_evidence_source(self):self.reject(lambda b:b['plan']['clips'][0].update(evidence_ids=['reference-frames']))
    def test_missing_evidence(self):self.reject(lambda b:b['annotations'][0].update(evidence_ids=[]))
    def test_unknown_confidence(self):self.reject(lambda b:b['annotations'][0].update(knowledge='unknown'))
    def test_duration_conversion(self):self.reject(lambda b:b['plan']['clips'][0].update(timeline_duration_ticks=60000))
    def test_unreviewed_approval(self):self.reject(lambda b:b['plan'].update(status='approved'))
    def test_fake_effect_support(self):self.reject(lambda b:b['plan']['clips'][0]['effects'][0].update(support='verified'))
    def test_privacy(self):self.reject(lambda b:b['media'][0].update(external_upload_allowed=True))
    def test_overlap(self):
        c=copy.deepcopy(self.b['plan']['clips'][0]);c['id']='clip-2';self.reject(lambda b:b['plan']['clips'].append(c))
    def test_render_elapsed_not_media_time(self):self.reject(lambda b:b['media'][0].update(renderElapsedMs=5000))
    def test_synthetic_must_be_labelled(self):self.reject(lambda b:b.update(synthetic=False))
if __name__=='__main__':unittest.main()
