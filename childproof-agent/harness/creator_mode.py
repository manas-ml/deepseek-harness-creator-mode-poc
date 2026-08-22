"""Creator Mode helpers: runtime introspection, in-memory plugin loading,
and preset authoring/saving - all without touching harness source code.
"""
import importlib.util
import json
from pathlib import Path


def load_plugin_from_path(path, class_name):
    """Dynamically import a plugin module straight from a file path and
    return the requested class. This is how Creator Mode loads a tool
    "in memory" for live testing before it's wired into any saved preset.
    """
    path = Path(path)
    module_name = "creator_mode_plugin_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def save_preset(preset: dict, path):
    """Persist a preset dict as a real, reusable JSON preset file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(preset, f, indent=2)
        f.write("\n")
    return path


def load_preset(path):
    with open(path) as f:
        return json.load(f)
