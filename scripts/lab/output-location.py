"""Local workstation output policy. Never create a missing mount or fall back."""
from pathlib import Path
import hashlib,json,os
DEFAULT_CONFIG=Path(__file__).resolve().parents[2]/'.local'/'output-location.json'

def policy(config_path=DEFAULT_CONFIG):
    p=Path(config_path)
    if not p.exists():
        if p==DEFAULT_CONFIG:return None
        raise ValueError('Output location configuration is missing')
    data=json.loads(p.read_text())
    mount=Path(data['mount_path']);root=Path(data['output_root'])
    if not mount.is_absolute() or not root.is_absolute() or mount.is_symlink():raise ValueError('Invalid output mount/root')
    if not os.path.ismount(mount):raise ValueError('Output drive is not mounted; reconnect it before rendering: '+str(mount))
    if root.resolve()==mount.resolve() or not root.resolve().is_relative_to(mount.resolve()):raise ValueError('Output root escapes mounted drive')
    if not root.is_dir() or not os.access(root,os.W_OK|os.X_OK):raise ValueError('Output root is absent or not writable: '+str(root))
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mount_path':str(mount.resolve()),'output_root':str(root.resolve())}

def destination(output_dir,project_root,record):
    if record is None:return Path(output_dir).resolve(),Path(project_root).resolve()
    current=policy(record['path'])
    if current!=record:raise ValueError('Output configuration changed; prepare a new job')
    root=Path(record['output_root']);dest=Path(output_dir)
    if not dest.is_absolute():dest=root/dest
    dest=dest.resolve()
    if dest==root or not dest.is_relative_to(root):raise ValueError('Output must be a new directory under configured external output root')
    return dest,root
