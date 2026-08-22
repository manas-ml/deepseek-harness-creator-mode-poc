"""Directory snapshot/diff helper, used to prove demo-task/ was or wasn't
touched by a given run.
"""
import hashlib
from pathlib import Path


def snapshot_dir(root):
    root = Path(root)
    out = {}
    for p in sorted(root.iterdir()):
        if p.is_file():
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_snapshots(before, after):
    before_names, after_names = set(before), set(after)
    return {
        "added": sorted(after_names - before_names),
        "removed": sorted(before_names - after_names),
        "modified": sorted(n for n in before_names & after_names if before[n] != after[n]),
        "unchanged": sorted(n for n in before_names & after_names if before[n] == after[n]),
    }
