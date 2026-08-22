"""Cordis tool plugin: shell. Full shell access, scoped to the sandbox root.

This is the "risky" capability in the Standard preset: it can create,
modify, or delete anything the agent decides to touch. A minimal verb
allowlist and a cwd pin keep it from ever reaching outside sandbox_root,
but nothing stops it from deleting a file *inside* the sandbox that a
more careful agent would have left alone - that gap is exactly what the
demo is about.
"""
import shlex
import subprocess
from pathlib import Path

ALLOWED_VERBS = {"ls", "rm", "cat", "stat"}


class ShellTool:
    name = "shell"
    permissions = ("read", "write", "delete", "shell")
    description = "Run a shell command with cwd pinned to the sandbox root."

    def __init__(self, sandbox_root):
        self.sandbox_root = Path(sandbox_root).resolve()

    def run(self, command, **_):
        parts = shlex.split(command)
        if not parts:
            raise ValueError("empty command")
        if parts[0] not in ALLOWED_VERBS:
            raise PermissionError(f"verb '{parts[0]}' is not allowed in this demo shell")
        if any(".." in p or p.startswith("/") for p in parts[1:]):
            raise PermissionError("path escapes sandbox root")
        result = subprocess.run(
            parts, cwd=self.sandbox_root, capture_output=True, text=True, timeout=10
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


TOOL_CLASS = ShellTool
