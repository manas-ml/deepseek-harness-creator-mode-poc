"""Cordis plugin: sandbox. Pins a session to a single directory on disk."""
from pathlib import Path


class Sandbox:
    name = "sandbox"

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def describe(self):
        return {"root": str(self.root)}
