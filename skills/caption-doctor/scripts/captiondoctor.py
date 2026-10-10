#!/usr/bin/env python3
"""
Caption Doctor — clean an auto-caption SRT so it imports beautifully into CapCut (or any editor).

Fixes what auto-captions get wrong, to professional-subtitle standards:
  LANGUAGE (the AI agent's job, passed in via --fix / --fix-file):
    - recognition errors (clot->Claude, 代辦->待辦, 溜溝->溜狗)
    - Simplified -> Traditional Mandarin (Taiwan vocab, OpenCC s2twp; already-Traditional left alone)
    - spoken English -> Traditional Mandarin (default), keeping genuine names (Codex, CapCut) as-is
  MECHANICS (this tool):
    - WORD-AWARE line breaks via jieba: never splits a word, a name, an English word, or a number;
      never strands a lone character (orphan-balancing).
    - line length <= --maxlen characters.
    - timing: minimum on-screen duration, a small gap between captions (no flicker), no overlaps.
    - optional: drop lone filler captions (嗯/呃/啊).
    - a reading-speed (CPS) report that flags any caption that is too fast or too short.

Output: clean UTF-8 .srt  ->  CapCut: Captions > Add Captions > pick the file.

Usage:
  python3 captiondoctor.py IN.srt --out clean.srt --maxlen 12 --drop-fillers \\
      --fix "clot=>Claude; 代辦=>待辦; 指令碼=>腳本; 4點=>四點"
"""
import argparse, re, os
from pathlib import Path

# ---- Traditional Taiwan conversion (smart: only convert Simplified) --------------
try:
    from opencc import OpenCC
    _CC, _S2T = OpenCC("s2twp"), OpenCC("s2t")
    def to_tw(s): return s if _S2T.convert(s) == s else _CC.convert(s)
    HAVE_OPENCC = True
except Exception:
    def to_tw(s): return s
    HAVE_OPENCC = False

try:
    import jieba
    jieba.setLogLevel(60)
    HAVE_JIEBA = True
except Exception:
    HAVE_JIEBA = False

TERMINAL = set("。！？.!?")
FILLER_SOLO = set("嗯呃啊欸誒齁蛤唉喔噢哦唔嗯嗯")

def to_sec(t):
    t=t.strip().replace(".",","); m=re.match(r"(\d+):(\d+):(\d+),(\d+)",t)
    h,mn,s,ms=map(int,m.groups()); return h*3600+mn*60+s+ms/1000.0

def sec_to_srt(x):
    x=max(x,0); h=int(x//3600); m=int((x%3600)//60); s=int(x%60); ms=int(round((x-int(x))*1000))
    if ms==1000: s+=1; ms=0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt(path):
    txt=open(path,encoding="utf-8-sig").read(); segs=[]
    for b in re.split(r"\n\s*\n", txt.strip()):
        lines=[l for l in b.splitlines() if l.strip()]
        tc=next((l for l in lines if "-->" in l), None)
        if not tc: continue
        i=lines.index(tc); a,bb=tc.split("-->")
        raw=re.sub(r"<[^>]+>","", " ".join(lines[i+1:])).strip()
        segs.append({"start":to_sec(a),"end":to_sec(bb),"text":raw})
    return segs

def apply_fixes(text, fixes):
    for a,b in fixes: text=text.replace(a,b)
    return text

def has_cjk(s): return any("一"<=c<="鿿" for c in s)
def pangu(s):
    """Add a space between Chinese and Latin letters/digits (先用Codex -> 先用 Codex; Pocket 3跟 -> Pocket 3 跟)."""
    s=re.sub(r"([一-鿿])([A-Za-z0-9])", r"\1 \2", s)
    s=re.sub(r"([A-Za-z0-9])([一-鿿])", r"\1 \2", s)
    return re.sub(r"  +", " ", s).strip()
def is_lone_filler(text):
    t=re.sub(r"[，。！？、,.!?…\s]","",text)
    return t in FILLER_SOLO or (len(t)<=1 and t in FILLER_SOLO)

def tokenize(text):
    if HAVE_JIEBA and has_cjk(text):
        return [w for w in jieba.cut(text) if w.strip()]
    return text.split() if not has_cjk(text) else list(text)

def pack_lines(text, maxlen):
    """Pack word tokens into <=maxlen-char lines without ever splitting a token
    (word / name / English / number). Balance to avoid a lone trailing character."""
    toks=tokenize(text); lines=[]; cur=""
    for t in toks:
        if not cur: cur=t
        elif len(cur)+len(t) <= maxlen: cur+=t
        else: lines.append(cur); cur=t
    if cur: lines.append(cur)
    # orphan fix: if last line is a single CJK char, pull it onto the previous line
    if len(lines)>=2 and len(lines[-1])==1 and len(lines[-2])+1 <= maxlen+1:
        lines[-2]+=lines.pop()
    return lines or [text]

def preserve(segs, drop_fillers):
    """DEFAULT mode: fix the text, keep every original timecode exactly. Never re-times,
    so captions stay perfectly in sync with the audio. Optionally drops lone-filler cards."""
    caps=[]
    for s in segs:
        t=s["text"].strip()
        if not t: continue
        if drop_fillers and is_lone_filler(t): continue
        caps.append({"start":s["start"], "end":s["end"], "text":t})
    return caps

def reflow(segs, maxlen, merge_gap, min_dur, min_gap, drop_fillers):
    if drop_fillers:
        segs=[s for s in segs if not is_lone_filler(s["text"])]
    # merge contiguous fragments into utterances (break on terminal punctuation)
    utts=[]; cur=None
    for s in segs:
        if cur and s["start"]-cur["end"]<=merge_gap and (not cur["text"] or cur["text"][-1] not in TERMINAL):
            cur["text"]+=s["text"]; cur["end"]=s["end"]
        else:
            cur={"start":s["start"],"end":s["end"],"text":s["text"]}; utts.append(cur)
    # re-split into caption lines, re-timed by character share
    caps=[]
    for u in utts:
        lines=pack_lines(u["text"], maxlen)
        total=sum(len(l) for l in lines) or 1
        t=u["start"]; span=u["end"]-u["start"]
        for ln in lines:
            dur=span*len(ln)/total
            caps.append({"start":t,"end":t+dur,"text":ln}); t+=dur
    # timing pass: min duration, then a small gap between neighbours, no overlap
    for c in caps:
        if c["end"]-c["start"]<min_dur: c["end"]=c["start"]+min_dur
    for i in range(len(caps)-1):
        if caps[i]["end"] > caps[i+1]["start"]-min_gap:
            caps[i]["end"]=max(caps[i]["start"]+0.3, caps[i+1]["start"]-min_gap)
    return caps

def write_srt(caps, path):
    with open(path,"w",encoding="utf-8") as f:
        for i,c in enumerate(caps,1):
            f.write(f"{i}\n{sec_to_srt(c['start'])} --> {sec_to_srt(c['end'])}\n{c['text']}\n\n")

def report(caps, maxlen, max_cps, min_dur):
    issues=0
    for c in caps:
        n=len(c["text"]); dur=c["end"]-c["start"]; cps=n/dur if dur else 99
        why=[]
        if n>maxlen: why.append(f">{maxlen} chars")
        if dur<min_dur-1e-3: why.append("short")
        if cps>max_cps: why.append(f"{cps:.1f}cps")
        if why: issues+=1; print(f"  ! [{c['text']}] {', '.join(why)}")
    print(f"Quality: {len(caps)} captions, {issues} flagged "
          f"(jieba={HAVE_JIEBA}, opencc={HAVE_OPENCC}). Max {maxlen} chars/line, <= {max_cps} cps.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("srt"); ap.add_argument("--out", default="clean.srt")
    ap.add_argument("--maxlen", type=int, default=12, help="max characters per caption line")
    ap.add_argument("--merge-gap", type=float, default=0.6)
    ap.add_argument("--min-dur", type=float, default=0.8, help="minimum on-screen seconds")
    ap.add_argument("--min-gap", type=float, default=0.08, help="gap between captions (~2 frames)")
    ap.add_argument("--max-cps", type=float, default=9.0, help="reading-speed flag (chars/sec)")
    ap.add_argument("--drop-fillers", action="store_true")
    ap.add_argument("--reflow", action="store_true",
                    help="ADVANCED: re-chunk lines to --maxlen. This RE-TIMES sub-cards by estimate "
                         "(no word-level data) and can drift from the audio. Off by default so the "
                         "original, correctly-synced timecodes are preserved. Not for word-by-word.")
    ap.add_argument("--fix", default="", help='corrections applied before AND after conversion: "a=>b; c=>d"')
    ap.add_argument("--fix-file", help="UTF-8 glossary with one wrong=>right pair per line")
    a=ap.parse_args()
    raw_fixes = [p for p in a.fix.split(";") if "=>" in p]
    if a.fix_file:
        glossary = Path(a.fix_file).expanduser()
        if not glossary.is_file():
            ap.error(f"找不到字幕詞庫: {glossary}")
        for line in glossary.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=>" in line:
                raw_fixes.append(line)
    fixes=[(x.strip(),y.strip()) for x,y in (p.split("=>",1) for p in raw_fixes)]
    segs=parse_srt(a.srt)
    for s in segs:
        s["text"]=pangu(apply_fixes(to_tw(apply_fixes(s["text"], fixes)), fixes))  # pre+convert+post+spacing
    if a.reflow:
        print("[reflow] re-chunking to <=%d chars; sub-card timing is ESTIMATED and may drift." % a.maxlen)
        caps=reflow(segs, a.maxlen, a.merge_gap, a.min_dur, a.min_gap, a.drop_fillers)
    else:
        caps=preserve(segs, a.drop_fillers)
    write_srt(caps, a.out)
    print(f"Mode: {'REFLOW (re-timed)' if a.reflow else 'PRESERVE (original timing kept)'}")
    print(f"In {len(segs)} lines -> out {len(caps)} caption lines. Wrote {a.out}")
    report(caps, a.maxlen, a.max_cps, a.min_dur)

if __name__=="__main__":
    main()
