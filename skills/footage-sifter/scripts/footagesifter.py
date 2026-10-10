#!/usr/bin/env python3
"""
Footage Sifter — turn a folder of raw clips into an organized, ready-to-edit project.

The AI agent does the editorial judgment (grouping takes, picking the best one, ordering the
selects, naming things) and writes a sift.json manifest. This tool does the mechanics:

Outputs (into --out):
  1) sift_report.txt      — the cull: groups, takes, verdicts + reasons, selects order
  2) rename.sh / .bat     — safe rename+sort into 01_SELECTS / 02_BACKUPS / 03_REJECTS
                            (never overwrites; review before running)
     還原.sh / 還原.bat     — one-command undo (Mac / Windows)
  3) selects.fcpxml       — DaVinci: File > Import > Timeline -> selects land on a
                            timeline in order, trimmed to their in/out
  4) resolve_selects.py   — DaVinci: Workspace > Console (Py3) fallback; reads each
                            clip's REAL fps so timing cannot drift

Manifest (written by the AI agent, UTF-8 JSON):
{
  "project": "0703_vlog",
  "fps": 30, "width": 1080, "height": 1920,          // fallback if media not probeable
  "clips": [
    {"file": "IMG_3859.MOV",                          // filename as it is on disk
     "media": "/Volumes/SD/IMG_3859.MOV",             // optional: full path (ffprobe it)
     "group": "opening hook",                         // take family / content bucket
     "take": 2,                                        // optional take number
     "verdict": "select",                              // select | backup | reject
     "reason": "best energy, clean read",
     "order": 1,                                       // selects order (selects only)
     "in": 3.5, "out": 12.0,                           // optional sub-range (seconds)
     "duration": 15.2,                                 // needed only if media unprobeable
     "new_name": "opening-hook_t2"}                    // optional; default: slug(group)_tN
  ]
}

Usage:
  python3 footagesifter.py sift.json --out out_sift
"""
import argparse, json, os, re, shlex, sys, unicodedata
from pathlib import Path
from xml.sax.saxutils import escape as _xe
from media_tools import find_ffmpeg_pair

def xa(s):
    """Escape a string for use inside an XML attribute."""
    return _xe(str(s), {'"': "&quot;", "'": "&apos;"})

VERDICTS = ("select", "backup", "reject")

# Output language — default 繁體中文（台灣）, the pack's audience. --en switches to English.
L_ZH = {
    "folders": {"select": "01_精選", "backup": "02_備用", "reject": "03_淘汰"},
    "marks":   {"select": "★ 精選", "backup": "  備用", "reject": "  淘汰"},
    "title":   "FOOTAGE SIFTER — 素材整理報告",
    "project": "專案", "clips": "片段", "sel": "精選", "back": "備用", "rej": "淘汰",
    "runtime": "精選總長（已修剪）",
    "order_h": "精選順序（這就是你的粗剪順序）",
    "groups_h": "分組／各拍次",
    "clip_w":  "個片段",
    "sh_hdr":  ["#!/bin/bash",
                "# Footage Sifter — 先看過這個檔，確認沒問題再執行：  bash rename.sh",
                "# 請在放素材的資料夾裡執行。",
                "# 可以重複執行：絕不覆蓋檔案，已搬移的會自動略過。", ""],
    "bat_hdr": ["@echo off", "chcp 65001 >nul",
                "rem Footage Sifter - 先看過這個檔，確認沒問題再執行 rename.bat",
                "rem 請在放素材的資料夾裡執行。絕不覆蓋、已搬移會略過。", ""],
    "skip_t":  "略過（目標已存在）", "skip_s": "略過（已搬移過？）",
    "tl": "精選 SELECTS",
    "restore_name": "還原.sh",
    "restore_hdr": ["#!/bin/bash",
                    "# Footage Sifter — 一鍵還原：把所有檔案搬回原本的名字和位置",
                    "# 在放素材的資料夾裡執行：  bash 還原.sh", ""],
    "restore_bat_name": "還原.bat",
    "restore_bat_hdr": ["@echo off", "chcp 65001 >nul",
                        "rem Footage Sifter - 一鍵還原：把所有檔案搬回原本的名字和位置",
                        "rem 在放素材的資料夾裡執行（雙擊或在命令列輸入 還原.bat）", ""],
}
L_EN = {
    "folders": {"select": "01_SELECTS", "backup": "02_BACKUPS", "reject": "03_REJECTS"},
    "marks":   {"select": "★ SELECT", "backup": "  backup", "reject": "  reject"},
    "title":   "FOOTAGE SIFTER — SIFT REPORT",
    "project": "Project", "clips": "Clips", "sel": "Selects", "back": "Backups", "rej": "Rejects",
    "runtime": "Selects runtime (trimmed)",
    "order_h": "SELECTS ORDER (this is your rough assembly)",
    "groups_h": "GROUPS / TAKES",
    "clip_w":  " clip(s)",
    "sh_hdr":  ["#!/bin/bash", "# Footage Sifter — review this, then:  bash rename.sh",
                "# Run it INSIDE the folder that holds the clips.",
                "# Safe to re-run: never overwrites, skips files already moved.", ""],
    "bat_hdr": ["@echo off", "chcp 65001 >nul",
                "rem Footage Sifter - review this, then run: rename.bat",
                "rem Run it INSIDE the folder that holds the clips.", ""],
    "skip_t":  "SKIP (target exists)", "skip_s": "skip (already moved?)",
    "tl": "SELECTS",
    "restore_name": "restore.sh",
    "restore_hdr": ["#!/bin/bash",
                    "# Footage Sifter — one-command undo: every file back to its original name/place",
                    "# Run INSIDE the clips folder:  bash restore.sh", ""],
    "restore_bat_name": "restore.bat",
    "restore_bat_hdr": ["@echo off", "chcp 65001 >nul",
                        "rem Footage Sifter - one-command undo: every file back to its original name/place",
                        "rem Run INSIDE the clips folder: restore.bat", ""],
}
L = L_ZH  # set in main()

def detect_specs(path):
    """fps / resolution / duration straight from the file via ffprobe.
    Handles phone footage stored landscape with a rotation flag."""
    import subprocess
    try:
        _, ffprobe = find_ffmpeg_pair()
        if not ffprobe:
            return None
        out = subprocess.run([ffprobe, "-v", "quiet", "-print_format", "json",
                              "-show_format", "-show_streams", "-select_streams", "v:0", path],
                             capture_output=True, text=True).stdout
        data = json.loads(out)
        st = data["streams"][0]
        w, h = int(st["width"]), int(st["height"])
        rot = 0
        for sd in st.get("side_data_list", []):
            if "rotation" in sd: rot = abs(int(sd["rotation"]))
        if "rotate" in st.get("tags", {}): rot = abs(int(st["tags"]["rotate"]))
        if rot in (90, 270): w, h = h, w
        num, den = st.get("r_frame_rate", "0/1").split("/")
        fps = round(float(num) / float(den), 3) if float(den) else 0
        dur = float(data.get("format", {}).get("duration") or st.get("duration") or 0)
        return {"width": w, "height": h, "fps": fps, "duration": dur}
    except Exception:
        return None

def slug(s):
    """Filesystem-safe name; keeps CJK (student folders are often 中文)."""
    s = unicodedata.normalize("NFC", s.strip())
    s = re.sub(r"[\\/:*?\"<>|]", "", s)          # forbidden on macOS/Windows
    s = re.sub(r"\s+", "-", s)
    return s or "clip"

def load_manifest(path):
    manifest_path = os.path.abspath(os.path.expanduser(path))
    manifest_dir = os.path.dirname(manifest_path)
    m = json.load(open(manifest_path, encoding="utf-8-sig"))
    clips = m.get("clips", [])
    if not clips:
        sys.exit("Manifest has no clips.")
    problems = []
    seen_names = {}
    for i, c in enumerate(clips, 1):
        c.setdefault("verdict", "backup")
        if c["verdict"] not in VERDICTS:
            problems.append(f"clip {i} ({c.get('file','?')}): verdict must be one of {VERDICTS}")
        if not c.get("file"):
            problems.append(f"clip {i}: missing \"file\"")
        c.setdefault("group", "ungrouped")
        # probe real specs when we can
        media = c.get("media") or c.get("file", "")
        if media and not os.path.isabs(media):
            media = os.path.abspath(os.path.join(manifest_dir, media))
        if media:
            c["media"] = media
        c["_specs"] = detect_specs(media) if media and os.path.exists(media) else None
        if c["_specs"] and not c.get("duration"):
            c["duration"] = c["_specs"]["duration"]
        # build the target name once, uniquely — ALWAYS keep the original stem so the
        # camera's own ID (IMG_4558…) survives: reversible, relinkable, backup-matchable
        stem, ext = os.path.splitext(os.path.basename(c["file"]))
        base = c.get("new_name") or (slug(c["group"]) + (f"_t{c['take']}" if c.get("take") else ""))
        base = f"{slug(base)}_{slug(stem)}"
        n = seen_names.get(base, 0); seen_names[base] = n + 1
        if n: base = f"{base}_{n+1}"
        c["_newbase"], c["_ext"] = base, ext
    selects = [c for c in clips if c["verdict"] == "select"]
    if not selects:
        problems.append("no clip has verdict \"select\" — a sift with zero selects is a mistake")
    # selects order: explicit "order" wins, else manifest order
    selects.sort(key=lambda c: (c.get("order", 10**9)))
    for k, c in enumerate(selects, 1):
        c["_ord"] = k
    for c in selects:
        a, b = c.get("in"), c.get("out")
        if a is not None and b is not None and b <= a:
            problems.append(f"{c['file']}: out ({b}) must be greater than in ({a})")
        if b is None and not c.get("duration"):
            problems.append(f"{c['file']}: no \"out\" and no probeable/declared duration — "
                            f"add \"duration\" (seconds) or a \"media\" path")
    if problems:
        sys.exit("Manifest problems:\n  - " + "\n  - ".join(problems))
    return m, clips, selects

def sec_to_tc(x):
    x = max(x, 0); h = int(x // 3600); m = int((x % 3600) // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def clip_range(c):
    a = c.get("in") or 0.0
    b = c.get("out") if c.get("out") is not None else c.get("duration")
    return a, b

def write_report(m, clips, selects, path):
    groups = {}
    for c in clips:
        groups.setdefault(c["group"], []).append(c)
    total = len(clips)
    n_sel, n_back, n_rej = (sum(1 for c in clips if c["verdict"] == v) for v in VERDICTS)
    sel_len = sum(b - a for a, b in (clip_range(c) for c in selects))
    with open(path, "w", encoding="utf-8") as f:
        f.write(L["title"] + "\n" + "=" * 60 + "\n")
        f.write(f"{L['project']}: {m.get('project', '(unnamed)')}\n")
        f.write(f"{L['clips']}: {total}   {L['sel']}: {n_sel}   {L['back']}: {n_back}   {L['rej']}: {n_rej}\n")
        f.write(f"{L['runtime']}: {sel_len:.1f}s\n\n")
        f.write(L["order_h"] + "\n" + "-" * 60 + "\n")
        for c in selects:
            a, b = clip_range(c)
            f.write(f"  {c['_ord']:02d}. {c['file']}  ->  {c['_newbase']}{c['_ext']}\n"
                    f"      {sec_to_tc(a)}–{sec_to_tc(b)}  ({b-a:.1f}s)  「{c.get('reason','')}」\n")
        f.write("\n" + L["groups_h"] + "\n" + "-" * 60 + "\n")
        for g, cs in groups.items():
            f.write(f"\n■ {g}  ({len(cs)}{L['clip_w']})\n")
            for c in sorted(cs, key=lambda x: x.get("take", 0)):
                mark = L["marks"][c["verdict"]]
                take = f" take {c['take']}" if c.get("take") else ""
                f.write(f"  [{mark}]{take}  {c['file']}  — {c.get('reason','')}\n")
    return sel_len

def bq(s):
    """Quote one argument for a .bat line. Inside double quotes cmd.exe leaves & | < > ( ) alone,
    but still expands %VAR% even there, so a literal % must be doubled."""
    return '"' + str(s).replace('"', "").replace("%", "%%") + '"'

def bat_move(src, dst):
    """One guarded cmd.exe move line: never overwrites, skips what's already moved."""
    wsrc, wdst = src.replace("/", chr(92)), dst.replace("/", chr(92))
    return (f'if exist {bq(wdst)} (echo {bq(L["skip_t"] + ": " + wdst)}) else '
            f'if exist {bq(wsrc)} (move {bq(wsrc)} {bq(wdst)}) '
            f'else (echo {bq(L["skip_s"] + ": " + wsrc)})')

def write_rename_scripts(clips, out):
    sh, bat = list(L["sh_hdr"]), list(L["bat_hdr"])
    FOLDERS = L["folders"]
    for d in dict.fromkeys(FOLDERS.values()):
        sh.append(f'mkdir -p "{d}"'); bat.append(f'if not exist {bq(d)} mkdir {bq(d)}')
    sh.append(""); bat.append("")
    for c in clips:
        folder = FOLDERS[c["verdict"]]
        pre = f"{c['_ord']:02d}_" if c["verdict"] == "select" else ""
        dst = f"{folder}/{pre}{c['_newbase']}{c['_ext']}"
        qsrc, qdst = shlex.quote(c["file"]), shlex.quote(dst)
        sh.append(f'if [ -e {qdst} ]; then echo {shlex.quote(L["skip_t"] + ": " + dst)}; '
                  f'elif [ -e {qsrc} ]; then mv -- {qsrc} {qdst}; '
                  f'else echo {shlex.quote(L["skip_s"] + ": " + c["file"])}; fi')
        bat.append(bat_move(c["file"], dst))
    p1, p2 = os.path.join(out, "rename.sh"), os.path.join(out, "rename.bat")
    open(p1, "w", encoding="utf-8").write("\n".join(sh) + "\n")
    open(p2, "w", encoding="utf-8", newline="\r\n").write("\n".join(bat) + "\n")
    os.chmod(p1, 0o755)
    # undo script — every rename is fully reversible, zero disk cost (beats duplicating)
    rs, rb = list(L["restore_hdr"]), list(L["restore_bat_hdr"])
    for c in clips:
        folder = L["folders"][c["verdict"]]
        pre = f"{c['_ord']:02d}_" if c["verdict"] == "select" else ""
        src = f"{folder}/{pre}{c['_newbase']}{c['_ext']}"
        qsrc, qdst = shlex.quote(src), shlex.quote(c["file"])
        rs.append(f'if [ -e {qdst} ]; then echo {shlex.quote(L["skip_t"] + ": " + c["file"])}; '
                  f'elif [ -e {qsrc} ]; then mv -- {qsrc} {qdst}; '
                  f'else echo {shlex.quote(L["skip_s"] + ": " + src)}; fi')
        rb.append(bat_move(src, c["file"]))
    rs.append('rmdir "' + '" "'.join(dict.fromkeys(L["folders"].values())) + '" 2>/dev/null || true')
    for d in dict.fromkeys(L["folders"].values()):
        rb.append(f'if exist {bq(d)} rmdir {bq(d)} 2>nul')   # only removes a folder once it's empty
    p3 = os.path.join(out, L["restore_name"])
    open(p3, "w", encoding="utf-8").write("\n".join(rs) + "\n")
    os.chmod(p3, 0o755)
    p4 = os.path.join(out, L["restore_bat_name"])
    open(p4, "w", encoding="utf-8", newline="\r\n").write("\n".join(rb) + "\n")

def frames(x, fps): return int(round(max(x, 0) * fps))

def write_fcpxml(m, selects, path):
    # sequence format: first probed select wins, else manifest fallback
    fps = m.get("fps", 30); w = m.get("width", 1080); h = m.get("height", 1920)
    for c in selects:
        if c["_specs"] and c["_specs"]["fps"]:
            fps, w, h = c["_specs"]["fps"], c["_specs"]["width"], c["_specs"]["height"]
            break
    fps_i = int(round(fps)); fmt = f"FFVideoFormat{w}x{h}p{fps_i}"
    res, spine, head = [], [], 0
    for k, c in enumerate(selects, 1):
        rid = f"r{k+1}"
        a, b = clip_range(c)
        dur_clip = c.get("duration") or b
        from urllib.parse import quote
        media = c.get("media") or c["file"]
        uri = (Path(media).as_uri() if os.path.isabs(media)          # also right for C:\ paths
               else "file://" + quote("/" + media))
        res.append(f'    <asset id="{rid}" name="{xa(os.path.basename(c["file"]))}" start="0s" '
                   f'duration="{frames(dur_clip, fps)}/{fps_i}s" hasVideo="1" hasAudio="1" '
                   f'audioSources="1" audioChannels="2" format="r1">\n'
                   f'      <media-rep kind="original-media" src="{xa(uri)}"/>\n    </asset>')
        si = frames(a, fps); dur = frames(b, fps) - si
        if dur <= 0: continue
        clip_label = xa(f"{c['_ord']:02d} {c['_newbase']}")
        spine.append(f'        <asset-clip ref="{rid}" offset="{head}/{fps_i}s" '
                     f'name="{clip_label}" start="{si}/{fps_i}s" '
                     f'duration="{dur}/{fps_i}s" format="r1" tcFormat="NDF"/>')
        head += dur
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
  <resources>
    <format id="r1" name="{fmt}" frameDuration="1/{fps_i}s" width="{w}" height="{h}"/>
{chr(10).join(res)}
  </resources>
  <library>
    <event name="Footage Sift">
      <project name="{xa(m.get('project', 'Sift'))} — {L['tl']}">
        <sequence format="r1" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
{chr(10).join(spine)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
    open(path, "w", encoding="utf-8").write(xml)
    return head / fps

def write_xmeml(m, selects, path):
    """Premiere Pro import: legacy FCP7 XML (xmeml). Premiere does NOT read fcpxml.
    Video + stereo audio clipitems, linked, sequential on one track."""
    from urllib.parse import quote
    fps = m.get("fps", 30); w = m.get("width", 1080); h = m.get("height", 1920)
    for c in selects:
        if c["_specs"] and c["_specs"]["fps"]:
            fps, w, h = c["_specs"]["fps"], c["_specs"]["width"], c["_specs"]["height"]
            break
    ntsc = "TRUE" if abs(fps - round(fps)) > 0.001 else "FALSE"
    tb = int(round(fps))
    rate = f"<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>"
    vitems, aitems, head = [], [], 0
    for k, c in enumerate(selects, 1):
        a, b = clip_range(c)
        fi, fo = frames(a, fps), frames(b, fps)
        dur = fo - fi
        if dur <= 0: continue
        media = c.get("media") or c["file"]
        pathurl = ("file://localhost" + Path(media).as_uri()[len("file://"):] if os.path.isabs(media)
                   else "file://localhost" + quote("/" + media))
        fdur = frames(c.get("duration") or b, fps)
        name = xa(os.path.basename(c["file"]))
        label = xa(f"{c['_ord']:02d} {c['_newbase']}")
        file_el = (f'<file id="f{k}"><name>{name}</name><pathurl>{pathurl}</pathurl>{rate}'
                   f'<duration>{fdur}</duration><media><video>'
                   f'<samplecharacteristics><width>{w}</width><height>{h}</height>'
                   f'</samplecharacteristics></video>'
                   f'<audio><channelcount>2</channelcount></audio></media></file>')
        common = (f'<duration>{fdur}</duration>{rate}<start>{head}</start><end>{head+dur}</end>'
                  f'<in>{fi}</in><out>{fo}</out>')
        vitems.append(f'<clipitem id="v{k}"><name>{label}</name>{common}{file_el}</clipitem>')
        aitems.append(f'<clipitem id="a{k}"><name>{label}</name>{common}<file id="f{k}"/>'
                      f'<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex>'
                      f'</sourcetrack></clipitem>')
        head += dur
    nl = "\n          "
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence>
    <name>{xa(m.get('project', 'Sift'))} — {L['tl']}</name>
    <duration>{head}</duration>
    {rate}
    <media>
      <video>
        <format><samplecharacteristics>{rate}<width>{w}</width><height>{h}</height></samplecharacteristics></format>
        <track>
          {nl.join(vitems)}
        </track>
      </video>
      <audio>
        <track>
          {nl.join(aitems)}
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>
'''
    open(path, "w", encoding="utf-8").write(xml)

def write_resolve_script(m, selects, path):
    tl_name = f"{m.get('project', 'Sift')} - {L['tl']} "   # embedded with !r so quotes can't break the script
    entries = []
    for c in selects:
        a, b = clip_range(c)
        entries.append((os.path.basename(c["file"]), round(a, 3), round(b, 3)))
    open(path, "w", encoding="utf-8").write(f'''#!/usr/bin/env python
# DaVinci Resolve — build the SELECTS timeline. Reads each clip's REAL fps so timing
# cannot drift. HOW TO RUN: import the clips into the Media Pool, then in
# Workspace > Console (Py3) run:
#   exec(open("<path to this file>", encoding="utf-8").read())
CLIPS = {entries!r}   # (filename, in_sec, out_sec) in selects order

import time
try:
    resolve
except NameError:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")

proj = resolve.GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool()
pool = {{c.GetName(): c for c in mp.GetRootFolder().GetClipList()}}
missing = [n for n, _, _ in CLIPS if n not in pool]
if missing:
    raise SystemExit("Not in Media Pool: " + ", ".join(missing))

items = []
for name, a, b in CLIPS:
    clip = pool[name]
    fps = float(clip.GetClipProperty("FPS"))
    items.append({{"mediaPoolItem": clip,
                  "startFrame": int(round(a * fps)),
                  "endFrame":   int(round(b * fps)) - 1}})

name = {tl_name!r} + time.strftime("%H%M%S")
tl = mp.CreateEmptyTimeline(name)
proj.SetCurrentTimeline(tl)
mp.AppendToTimeline(items)
n = len(tl.GetItemListInTrack("video") or [])
print("New timeline:", name, "| clips placed:", n, "of", len(CLIPS))
''')

def main():
    global L
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", help="sift.json written by the AI agent")
    ap.add_argument("--out", default=".")
    ap.add_argument("--en", action="store_true",
                    help="English outputs (default: 繁體中文 台灣 — the pack's audience)")
    a = ap.parse_args()
    L = L_EN if a.en else L_ZH
    m, clips, selects = load_manifest(a.manifest)
    os.makedirs(a.out, exist_ok=True)
    sel_len = write_report(m, clips, selects, os.path.join(a.out, "sift_report.txt"))
    write_rename_scripts(clips, a.out)
    final = write_fcpxml(m, selects, os.path.join(a.out, "selects.fcpxml"))
    write_xmeml(m, selects, os.path.join(a.out, "selects_premiere.xml"))
    write_resolve_script(m, selects, os.path.join(a.out, "resolve_selects.py"))
    probed = sum(1 for c in clips if c["_specs"])
    print(f"Clips {len(clips)} | selects {len(selects)} ({sel_len:.1f}s) | media probed {probed}/{len(clips)}")
    print(f"Selects timeline length: {final:.1f}s")
    print(f"Wrote: sift_report.txt, rename.sh, rename.bat, {L['restore_name']}, {L['restore_bat_name']}, "
          "selects.fcpxml (FCP/DaVinci), selects_premiere.xml (Premiere), resolve_selects.py (DaVinci console)")

if __name__ == "__main__":
    main()
