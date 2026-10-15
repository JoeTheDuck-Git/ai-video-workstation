"""Offline provenance checks; not media quality or execution tests."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

class ArchiveTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / 'vendor/editing-rules/manifest.json').exists(), 'Optional upstream archive is not distributed')
    def test_pinned_bytes_and_unique_paths(self):
        base = ROOT / 'vendor/editing-rules'
        rows = json.loads((base / 'manifest.json').read_text())
        seen = set()
        for row in rows:
            key = (row['source'], row['path'])
            self.assertNotIn(key, seen)
            seen.add(key)
            file = base / row['source'] / row['path']
            self.assertFalse(file.is_symlink())
            blob = file.read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), row['sha256'])
            self.assertEqual(len(blob), row['bytes'])
        for skill in ('edit-video', 'cut-silences', 'cut-mistakes', 'short-form-edit'):
            self.assertIn(('student-kit', '.claude/skills/' + skill + '/SKILL.md'), seen)
        for skill in ('general-video', 'hyperframes-core'):
            self.assertIn(('hyperframes-official', 'skills/' + skill + '/SKILL.md'), seen)
        for source in ('student-kit', 'hyperframes-official'):
            self.assertIn((source, 'LICENSE'), seen)

    @unittest.skipUnless((ROOT / 'docs/reference-editing-lab/protected-baseline.json').exists(), 'Private integration baseline is not distributed')
    def test_protected_baseline(self):
        baseline = json.loads((ROOT / 'docs/reference-editing-lab/protected-baseline.json').read_text())
        for name, digest in baseline.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)

if __name__ == '__main__':
    unittest.main()
