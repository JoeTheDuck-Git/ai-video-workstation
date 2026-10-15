"""Draft data contract + semantic validator. No model calls or media mutations."""
from __future__ import annotations
from fractions import Fraction
from typing import Literal
from pathlib import Path
import json,sys
from pydantic import BaseModel,ConfigDict,Field,model_validator
class Base(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Rational(Base):
    numerator:int=Field(gt=0)
    denominator:int=Field(gt=0)
    def value(self):return Fraction(self.numerator,self.denominator)
class Approval(Base):
    status:Literal['pending','approved','rejected']='pending'
    reviewer:str|None=None
    reviewed_at:str|None=None
    @model_validator(mode='after')
    def signed(self):
        if self.status!='pending' and (not self.reviewer or not self.reviewed_at):raise ValueError('review needs reviewer and timestamp')
        return self
class Media(Base):
    id:str
    version:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    provenance:Literal['synthetic','probed']
    uri:str
    duration_ticks:int=Field(gt=0)
    timebase:Rational
    fps:Rational
    frame_mode:Literal['CFR','VFR']
    width:int=Field(gt=0)
    height:int=Field(gt=0)
    codec:str
    audio:bool
    metadata_evidence:str
    rights:Literal['owned','licensed','unknown','synthetic']
    privacy:Literal['private-local','approved-external','synthetic']
    external_upload_allowed:bool=False
class Span(Base):
    media_id:str
    start_tick:int=Field(ge=0)
    end_tick:int=Field(gt=0)
class Evidence(Base):
    id:str
    span:Span
    modality:Literal['frames','audio','both']
    frame_ticks:list[int]=Field(default_factory=list)
    artifact_refs:list[str]
class Annotation(Base):
    id:str
    span:Span
    category:Literal['shot','narrative-role','caption','transition','speed','crop','sound','effect']
    description:str
    knowledge:Literal['observed','inferred','unknown']
    confidence:float|None=Field(default=None,ge=0,le=1)
    evidence_ids:list[str]
    approval:Approval
    @model_validator(mode='after')
    def honest(self):
        if self.knowledge=='unknown' and self.confidence is not None:raise ValueError('unknown confidence must be null')
        if self.knowledge!='unknown' and (not self.evidence_ids or self.confidence is None):raise ValueError('claims need evidence and confidence')
        return self
class Rule(Base):
    id:str
    instruction:str
    scope:str
    exceptions:list[str]
    annotation_ids:list[str]
    approval:Approval
class Profile(Base):
    id:str
    version:int=Field(gt=0)
    parent_version:int|None=None
    rules:list[Rule]
    approval:Approval
class Effect(Base):
    type:str
    parameters:dict
    support:Literal['verified','candidate','manual','unsupported']
    implementation:str|None=None
    validation_evidence:str|None=None
    alternative:str|None=None
    approval:Approval
class Clip(Base):
    id:str
    source:Span
    timeline_start_tick:int=Field(ge=0)
    timeline_duration_ticks:int=Field(gt=0)
    track:int=Field(ge=0)
    speed:Rational
    narrative_role:str
    match_reason:str
    evidence_ids:list[str]
    rule_ids:list[str]
    effects:list[Effect]
class Plan(Base):
    id:str
    status:Literal['draft','approved']
    profile_id:str
    profile_version:int
    timebase:Rational
    duration_ticks:int=Field(gt=0)
    clips:list[Clip]
    unresolved:list[str]
    approval:Approval
class Bundle(Base):
    schema_version:Literal['0.1-draft']
    synthetic:bool
    media:list[Media]
    evidence:list[Evidence]
    annotations:list[Annotation]
    profile:Profile
    plan:Plan
    @model_validator(mode='after')
    def integrity(self):
        def indexed(items):
            d={i.id:i for i in items}
            if len(d)!=len(items):raise ValueError('duplicate IDs')
            return d
        media=indexed(self.media);ev=indexed(self.evidence);ann=indexed(self.annotations);rules=indexed(self.profile.rules);indexed(self.plan.clips)
        def span(s):
            if s.media_id not in media:raise ValueError('missing media')
            m=media[s.media_id]
            if not 0<=s.start_tick<s.end_tick<=m.duration_ticks:raise ValueError('source span outside media')
            return m
        for m in self.media:
            if self.synthetic != (m.provenance=='synthetic'):raise ValueError('synthetic provenance mismatch')
            if m.external_upload_allowed and m.privacy!='approved-external':raise ValueError('external upload lacks privacy permission')
        for e in self.evidence:
            span(e.span)
            if not e.artifact_refs:raise ValueError('missing evidence artifacts')
            if e.modality in ('frames','both') and not e.frame_ticks:raise ValueError('missing evidence frame ticks')
            if any(not e.span.start_tick<=t<e.span.end_tick for t in e.frame_ticks):raise ValueError('evidence frame out of interval')
        for a in self.annotations:
            span(a.span)
            for eid in a.evidence_ids:
                if eid not in ev:raise ValueError('missing evidence')
                e=ev[eid].span
                if e.media_id!=a.span.media_id or e.end_tick<=a.span.start_tick or e.start_tick>=a.span.end_tick:raise ValueError('unrelated evidence span')
        for rule in rules.values():
            if not rule.annotation_ids or any(i not in ann for i in rule.annotation_ids):raise ValueError('untraced rule')
        p=self.plan
        if (p.profile_id,p.profile_version)!=(self.profile.id,self.profile.version):raise ValueError('stale profile')
        tracks={}
        for c in p.clips:
            m=span(c.source)
            source_time=(c.source.end_tick-c.source.start_tick)*m.timebase.value()/c.speed.value()
            target_time=c.timeline_duration_ticks*p.timebase.value()
            if source_time!=target_time:raise ValueError('source/speed/timeline duration mismatch')
            if c.timeline_start_tick+c.timeline_duration_ticks>p.duration_ticks:raise ValueError('clip past plan end')
            if not c.evidence_ids or any(i not in ev for i in c.evidence_ids):raise ValueError('untraced match')
            for i in c.evidence_ids:
                e=ev[i].span
                if e.media_id!=m.id or e.end_tick<=c.source.start_tick or e.start_tick>=c.source.end_tick:raise ValueError('match evidence from wrong source interval')
            if any(i not in rules for i in c.rule_ids):raise ValueError('missing rule')
            tracks.setdefault(c.track,[]).append((c.timeline_start_tick,c.timeline_start_tick+c.timeline_duration_ticks))
            for fx in c.effects:
                if fx.support=='verified' and (not fx.implementation or not fx.validation_evidence):raise ValueError('verified effect lacks implementation evidence')
                if p.status=='approved' and (fx.support!='verified' or fx.approval.status!='approved'):raise ValueError('unreviewed or unresolved effect cannot be approved for rendering')
        for intervals in tracks.values():
            intervals.sort()
            if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('same-track overlap; use explicit separate track')
        if p.status=='approved':
            if p.unresolved or p.approval.status!='approved' or self.profile.approval.status!='approved':raise ValueError('plan not reviewed')
            used={i for c in p.clips for i in c.rule_ids}
            if any(rules[i].approval.status!='approved' for i in used):raise ValueError('unapproved rule')
            if any(media[c.source.media_id].rights=='unknown' for c in p.clips):raise ValueError('source rights unresolved')
        return self
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--schema':print(json.dumps(Bundle.model_json_schema(),ensure_ascii=False,indent=2))
    else:
        b=Bundle.model_validate_json(Path(sys.argv[1]).read_text())
        print(json.dumps({'valid':True,'synthetic':b.synthetic,'plan_status':b.plan.status,'render_executed':False}))
