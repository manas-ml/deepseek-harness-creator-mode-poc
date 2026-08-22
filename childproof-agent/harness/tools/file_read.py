"""Cordis tool plugin: file_read. Read-only file access, sandboxed."""
from pathlib import Path


class FileReadTool:
    name = "file_read"
    permissions = ("read",)
    description = "List and read files inside the sandbox root. No write or delete."

    def __init__(self, sandbox_root):
        self.sandbox_root = Path(sandbox_root).resolve()

    def _resolve(self, relpath):
        target = (self.sandbox_root / relpath).resolve()
        if target != self.sandbox_root and self.sandbox_root not in target.parents:
            raise PermissionError(f"'{relpath}' escapes the sandbox root")
        return target

    def run(self, action="list", path=None, **_):
        if action == "list":
            return {"files": sorted(p.name for p in self.sandbox_root.iterdir() if p.is_file())}
        if action == "read":
            if not path:
                raise ValueError("action=read requires 'path'")
            return {"content": self._resolve(path).read_text(errors="replace")}
        raise ValueError(f"unsupported action '{action}'")


TOOL_CLASS = FileReadTool
