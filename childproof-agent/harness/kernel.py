"""Minimal stand-in for DeepSeek Harness's Cordis plugin kernel.

Real Cordis resolves a preset into mounted plugins for the model adapter,
tool registry, sandbox, storage, and event log. This module reproduces
just enough of that shape - registration, introspection, and preset-driven
boot - to run the childproof-agent demo without requiring the actual
DeepSeek Harness runtime.
"""
from pathlib import Path

from .creator_mode import load_plugin_from_path
from .event_log import EventLog
from .sandbox import Sandbox
from .storage import LocalStorage
from .tools.file_read import FileReadTool
from .tools.shell import ShellTool

BUILTIN_TOOLS = {
    "file_read": FileReadTool,
    "shell": ShellTool,
}

SAFE_SCANNER_PATH = Path(__file__).resolve().parent.parent / "plugins" / "safe-scanner" / "plugin.py"

CATEGORIES = ("model", "tool", "sandbox", "storage", "event_log")


class PluginKernel:
    def __init__(self):
        self.plugins = {category: {} for category in CATEGORIES}

    def mount(self, category, plugin):
        self.plugins.setdefault(category, {})[plugin.name] = plugin

    def tools(self):
        return self.plugins.get("tool", {})

    def event_log(self):
        return next(iter(self.plugins["event_log"].values()))

    def list_plugins(self):
        return {
            category: sorted(self.plugins.get(category, {}))
            for category in CATEGORIES
        }

    def print_plugins(self, title="Mounted plugins"):
        print(f"== {title} ==")
        for category in CATEGORIES:
            names = sorted(self.plugins.get(category, {}))
            print(f"  {category}: {', '.join(names) if names else '(none)'}")


class ModelAdapter:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return {"name": self.name, "note": "deterministic mock, see harness/model_mock.py"}


def boot_from_preset(preset, sandbox_root, extra_scanner_exclude=None):
    """Build a fresh PluginKernel from a preset dict. Each call is an
    independent session - nothing is shared with a previous boot, which is
    what makes a "fresh session loading intern-mode" a meaningful test.
    """
    kernel = PluginKernel()
    kernel.mount("sandbox", Sandbox(sandbox_root))
    kernel.mount("storage", LocalStorage("."))
    kernel.mount("event_log", EventLog())
    kernel.mount("model", ModelAdapter(preset.get("model", "mock-model")))

    for tool_name in preset.get("tools", []):
        if tool_name == "safe_scanner":
            cls = load_plugin_from_path(SAFE_SCANNER_PATH, class_name="SafeScannerTool")
            tool = cls(sandbox_root, extra_exclude=extra_scanner_exclude)
        elif tool_name in BUILTIN_TOOLS:
            tool = BUILTIN_TOOLS[tool_name](sandbox_root)
        else:
            raise ValueError(f"unknown tool '{tool_name}' in preset")
        kernel.mount("tool", tool)

    return kernel
