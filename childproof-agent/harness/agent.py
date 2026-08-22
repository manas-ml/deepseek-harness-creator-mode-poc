"""The demo agent: one cleanup policy, run under two different toolsets.

Policy: given a "clean this up" prompt, prefer a structured safe_scanner
if one is mounted; otherwise fall back to a naive filename heuristic over
whatever file_read gives us. Then remove every candidate the policy found
- but only if a shell (the only mounted tool capable of deleting, in this
demo) is actually available.
"""
import shlex

from . import model_mock


def _call(tool, event_log, **kwargs):
    event_log.log("tool_call", {"tool": tool.name, "args": kwargs})
    try:
        result = tool.run(**kwargs)
        event_log.log("tool_result", {"tool": tool.name, "result": result})
        return result
    except Exception as exc:
        event_log.log("tool_error", {"tool": tool.name, "error": str(exc)})
        raise


def run_cleanup(prompt, tools, event_log):
    event_log.log("prompt", {"text": prompt})

    used_scanner = "safe_scanner" in tools
    report = []
    if used_scanner:
        result = _call(tools["safe_scanner"], event_log)
        report = result["report"]
    elif "file_read" in tools:
        listing = _call(tools["file_read"], event_log, action="list")
        report = [
            {
                "file": f,
                "looks_safe_to_remove": model_mock.looks_junk_naive(f),
                "reason": "naive filename heuristic (no safe_scanner mounted)",
            }
            for f in listing["files"]
        ]

    candidates = [r["file"] for r in report if r["looks_safe_to_remove"]]

    removed = []
    blocked = []
    for f in candidates:
        if "shell" in tools:
            _call(tools["shell"], event_log, command=f"rm -f {shlex.quote(f)}")
            removed.append(f)
        else:
            blocked.append(f)

    summary = {
        "scan_report": report,
        "candidates_identified": candidates,
        "removed": removed,
        "identified_but_not_removed_no_permission": blocked,
        "used_safe_scanner": used_scanner,
        "message": _render_message(removed, blocked),
    }
    event_log.log("final_response", summary)
    return summary


def _render_message(removed, blocked):
    if removed:
        return f"Removed: {', '.join(removed)}."
    if blocked:
        return (
            f"These look safe to remove: {', '.join(blocked)}. "
            "I don't have write or delete access under this preset, so I "
            "did not touch anything."
        )
    return "Nothing in this folder looked safe to remove."
