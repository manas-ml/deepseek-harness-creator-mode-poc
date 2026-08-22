"""Cordis tool plugin: safe-scanner.

Read-only. Scans a directory and guesses, per file, whether it looks safe
to remove, with a one-line reason. Never writes or deletes anything and
never shells out - it's a pure file-read + pattern-match tool.
"""
import json
import re
from pathlib import Path

DEFAULT_RULES_PATH = Path(__file__).parent / "rules.json"


def load_rules(rules_path=None):
    path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
    with open(path) as f:
        return json.load(f)


class SafeScannerTool:
    name = "safe_scanner"
    permissions = ("read",)
    description = "Read-only scan that flags files that look safe to remove, with a reason."

    def __init__(self, sandbox_root, rules_path=None, extra_exclude=None):
        self.sandbox_root = Path(sandbox_root).resolve()
        self.rules_path = rules_path
        self.extra_exclude = list(extra_exclude or [])

    def run(self, **_):
        rules = load_rules(self.rules_path)
        junk_patterns = rules.get("junk_patterns", [])
        exclude_always = list(rules.get("exclude_always", [])) + self.extra_exclude

        report = []
        for entry in sorted(self.sandbox_root.iterdir()):
            if not entry.is_file():
                continue
            verdict, reason = self._classify(entry.name, junk_patterns, exclude_always)
            report.append({"file": entry.name, "looks_safe_to_remove": verdict, "reason": reason})
        return {"report": report}

    @staticmethod
    def _classify(name, junk_patterns, exclude_always):
        for pat in exclude_always:
            if re.search(pat, name):
                return False, f"protected: matches '{pat}'"
        for pat in junk_patterns:
            if re.search(pat, name):
                return True, f"junk: matches '{pat}'"
        return False, "no junk pattern matched; treated as content"


TOOL_CLASS = SafeScannerTool
