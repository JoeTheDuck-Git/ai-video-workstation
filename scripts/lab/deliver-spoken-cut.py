#!/usr/bin/env python3
"""Talking-head delivery entry. No rendering or upload; authorize a bound deliverable."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/'skills/spoken-edit-review/scripts/review_gate.py'
spec = importlib.util.spec_from_file_location('review_gate', SCRIPT)
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('packet');p.add_argument('review');p.add_argument('dispatch');p.add_argument('output')
    p.add_argument('--mode',choices=['final','draft','preview'],default='final')
    a=p.parse_args(argv)
    output=Path(a.output)
    try:
        packet=g.read(a.packet);report=g.read(a.review);dispatch=g.read(a.dispatch)
        if dispatch.get('packet_sha256') != g.digest(a.packet):
            raise ValueError('Packet differs from dispatched bytes')
        # No cached gate-result or technical pass can bypass fresh evaluation.
        result=g.gate(packet,report,dispatch,mode='preview' if a.mode=='preview' else 'final')
        draft_blockers=('content_review_not_pass','incomplete_audio_review','missing_scope_review','reviewer_open_findings','unresolved_candidate:','asr_is_not_audio_review','missing_range_evidence','missing_range_finding')
        draft_safe=result['technical_pass'] and all(any(b==x or (x.endswith(':') and b.startswith(x)) for x in draft_blockers) for b in result['blockers'])
        permitted=result['final_pass'] or (a.mode=='preview' and result['preview_allowed']) or (a.mode=='draft' and draft_safe)
        result.update(requested_mode=a.mode,delivery_allowed=permitted,
          label='reviewed_final' if result['final_pass'] and a.mode=='final' else ('EVIDENCE_REVIEWED_PREVIEW_NEEDS_AUDIO_REVIEW' if a.mode=='preview' else 'UNREVIEWED_DRAFT'),
          artifact=packet['files']['export'] if permitted else None,
          entrypoint_sha256=g.digest(__file__))
        g.write(output,result)
        print(json.dumps(result,ensure_ascii=False))
        return 0 if permitted else 2
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as e:
        # Replace any prior allowed receipt on this output path with a blocked state.
        g.write(output,{'delivery_allowed':False,'final_pass':False,'artifact':None,'error':str(e)})
        print('Delivery blocked: '+str(e),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
