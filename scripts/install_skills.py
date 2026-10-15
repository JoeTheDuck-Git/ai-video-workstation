#!/usr/bin/env python3
"""Install the public manifest as an independent snapshot; back up replaced Skills."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def install(skills_root,state_dir):
    skills_root=Path(skills_root).expanduser().resolve();state_dir=Path(state_dir).expanduser().resolve()
    manifest=json.loads((ROOT/'skills-manifest.json').read_text())
    # Validate the entire payload before replacing anything.
    for name in manifest['files']:
        p=ROOT/name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.is_file():raise ValueError('Invalid install payload: '+name)
    state_dir.mkdir(parents=True,exist_ok=True);skills_root.mkdir(parents=True,exist_ok=True)
    snapshot=Path(tempfile.mkdtemp(prefix='skills-',dir=state_dir))
    for name in manifest['files']:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    try:commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):commit='unknown (source archive)'
    metadata={'runtime_root':str(snapshot),'source_commit':commit,'skills_root':str(skills_root),'skills':manifest['skills'],'backups':[]}
    for name in manifest['skills']:
        dest=skills_root/name
        if dest.exists() or dest.is_symlink():
            backup=snapshot/'backups'/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(dest),str(backup));metadata['backups'].append(str(backup))
        shutil.copytree(snapshot/'skills'/name,dest)
        (dest/'runtime-root.json').write_text(json.dumps({'runtime_root':str(snapshot),'source_commit':commit},indent=2)+'\n')
    (snapshot/'installation.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2));return metadata

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skills-root',required=True);p.add_argument('--state-dir',required=True);a=p.parse_args();install(a.skills_root,a.state_dir)
