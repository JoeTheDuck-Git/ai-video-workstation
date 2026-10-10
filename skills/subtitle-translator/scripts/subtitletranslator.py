#!/usr/bin/env python3
"""
Subtitle Translator — translate a clean SRT into another language, keeping the timing perfect.

The AI agent does the translation (natural + culturally adapted, NOT word-for-word) and supplies it as an
index->text JSON. This tool merges that translation onto the SOURCE timecodes, formats it for the
target language, and reports reading speed — because a translation that's correct but too fast to
read is a failure (Chinese is compact; English/Japanese often expand and blow past readable speed).

Pipeline (mirrors Caption Doctor): AI agent = language, tool = mechanics + QC.
  1. The AI agent reads source.srt, writes translations as {"1":"...", "2":"..."} (one per source card).
  2. python3 subtitletranslator.py source.srt --lang en --translations en.json --out source.en.srt

Target formatting:
  - zh-Hant / zh-TW  -> OpenCC s2twp (Taiwan Traditional) + CJK-Latin spacing
  - any target       -> CJK-Latin spacing; timing preserved exactly
Reading-speed limit auto-set: CJK/JA ~9 cps, Latin scripts ~17 cps (override with --max-cps).
"""
import argparse, re, json

try:
    from opencc import OpenCC
    _CC, _S2T = OpenCC("s2twp"), OpenCC("s2t")
    def to_tw(s): return s if _S2T.convert(s)==s else _CC.convert(s)
    HAVE_OPENCC=True
except Exception:
    def to_tw(s): return s
    HAVE_OPENCC=False

CJK_LANGS={"zh","zh-tw","zh-hant","zh-hans","zh-cn","yue","ja","jp"}

def read_text(path):
    raw=open(path,"rb").read()
    if raw.startswith(b"\xef\xbb\xbf"): return raw.decode("utf-8-sig")
    ok=set("，。！？、：；「」『』（）《》—…0123456789")
    best,bs=None,-1.0
    for enc in ("utf-8","gb18030","big5","latin-1"):
        try: s=raw.decode(enc)
        except UnicodeError: continue
        good=sum(1 for c in s if ("一"<=c<="鿿") or (" "<=c<="~") or c in ok)
        sc=good/max(len(s),1)+(0.05 if enc=="utf-8" else 0)
        if sc>bs: best,bs=s,sc
    return best if best is not None else raw.decode("utf-8",errors="replace")

def to_sec(t):
    t=t.strip().replace(".",","); m=re.match(r"(\d+):(\d+):(\d+),(\d+)",t)
    h,mn,s,ms=map(int,m.groups()); return h*3600+mn*60+s+ms/1000.0

def sec_to_srt(x):
    x=max(x,0); h=int(x//3600); m=int((x%3600)//60); s=int(x%60); ms=int(round((x-int(x))*1000))
    if ms==1000: s+=1; ms=0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt(path):
    txt=read_text(path); segs=[]
    for b in re.split(r"\n\s*\n", txt.strip()):
        lines=[l for l in b.splitlines() if l.strip()]
        tc=next((l for l in lines if "-->" in l), None)
        if not tc: continue
        i=lines.index(tc); a,bb=tc.split("-->")
        idx=lines[0].strip() if lines and lines[0].strip().isdigit() else str(len(segs)+1)
        raw=re.sub(r"<[^>]+>","", " ".join(lines[i+1:])).strip()
        segs.append({"idx":idx,"start":to_sec(a),"end":to_sec(bb),"text":raw})
    return segs

def pangu(s):
    s=re.sub(r"([一-鿿])([A-Za-z0-9])",r"\1 \2",s)
    s=re.sub(r"([A-Za-z0-9])([一-鿿])",r"\1 \2",s)
    return re.sub(r"  +"," ",s).strip()

def latin_units(s):
    """Approximate rendered Latin width; capitals and wide glyphs cost more than spaces."""
    total=0.0
    for ch in s:
        if ch.isspace(): total+=0.38
        elif ch in "MW@%&QO": total+=1.15
        elif ch in "ilIjtfr.,:;!'|": total+=0.48
        elif ch.isupper(): total+=0.88
        else: total+=0.74
    return total

def semantic_wrap_latin(text, max_units=29.0, max_lines=2):
    """Keep short English on one line; wrap long text at natural phrase boundaries."""
    text=re.sub(r"\s+"," ",text).strip()
    if not text or latin_units(text)<=max_units: return text, False
    words=text.split(" ")
    # Prefer a balanced break after punctuation or before a conjunction.
    preferred=[]
    conjunctions={"and","but","or","because","so","while","when","that","which","then"}
    for i in range(1,len(words)):
        if words[i-1].endswith((",",";",":","—","–")) or words[i].lower().strip(".,!?;:") in conjunctions:
            preferred.append(i)
    def score(i):
        a,b=" ".join(words[:i])," ".join(words[i:])
        overflow=max(0,latin_units(a)-max_units)+max(0,latin_units(b)-max_units)
        return (overflow,abs(latin_units(a)-latin_units(b)))
    candidates=preferred or list(range(1,len(words)))
    cut=min(candidates,key=score)
    lines=[" ".join(words[:cut])," ".join(words[cut:])]
    needs_split=any(latin_units(x)>max_units for x in lines)
    return "\n".join(lines[:max_lines]), needs_split

def write_srt(caps,path):
    with open(path,"w",encoding="utf-8") as f:
        for i,c in enumerate(caps,1):
            f.write(f"{i}\n{sec_to_srt(c['start'])} --> {sec_to_srt(c['end'])}\n{c['text']}\n\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("srt")
    ap.add_argument("--lang", required=True, help="target language code, e.g. en, ja, zh-hant")
    ap.add_argument("--translations", required=True, help='JSON {"1":"...","2":"..."} from the AI agent')
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-cps", type=float, default=None)
    ap.add_argument("--max-line-units", type=float, default=29.0,
                    help="English visual line-width limit; short cues stay on one line")
    ap.add_argument("--no-auto-wrap", action="store_true",
                    help="disable automatic semantic wrapping for Latin subtitles")
    a=ap.parse_args()
    if not HAVE_OPENCC and a.lang.lower() in CJK_LANGS:
        print("WARNING: opencc not installed - Traditional conversion off. pip install opencc-python-reimplemented")
    trans=json.load(open(a.translations,encoding="utf-8"))
    lang=a.lang.lower(); is_cjk=lang in CJK_LANGS
    max_cps=a.max_cps if a.max_cps else (9.0 if is_cjk else 17.0)
    segs=parse_srt(a.srt)
    missing=0; caps=[]; needs_split=[]
    for s in segs:
        t=trans.get(s["idx"])
        if t is None: t=s["text"]; missing+=1
        if lang in ("zh-tw","zh-hant","zh"): t=to_tw(t)
        t=pangu(t)
        if not is_cjk and not a.no_auto_wrap:
            t, too_long=semantic_wrap_latin(t,a.max_line_units)
            if too_long: needs_split.append(s["idx"])
        caps.append({"start":s["start"],"end":s["end"],"text":t})
    write_srt(caps,a.out)
    # reading-speed QC
    fast=0
    for c in caps:
        dur=c["end"]-c["start"]; n=len(c["text"])
        if dur>0 and n/dur>max_cps: fast+=1; print(f"  ! [{c['text']}] {n/dur:.1f} cps (> {max_cps})")
    print(f"Lang: {a.lang} | {len(caps)} cards | missing translations: {missing} | too-fast: {fast} (limit {max_cps} cps)")
    if needs_split:
        print("  ! These cues still exceed two visual lines and should be split into separate semantic cues: "
              + ", ".join(needs_split))
    print(f"Timing preserved from source. Wrote {a.out}")

if __name__=="__main__":
    main()
