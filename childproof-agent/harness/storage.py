"""Cordis plugin: storage.

Trivial local-filesystem backend for saved presets and trajectories -
swappable for e.g. a remote store in a real DeepSeek Harness deployment.
"""
from pathlib import Path


class LocalStorage:
    name = "local_fs"

    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir).resolve()

    def describe(self):
        return {"kind": "local_fs", "base_dir": str(self.base_dir)}
