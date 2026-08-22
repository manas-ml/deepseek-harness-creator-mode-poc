"""Stand-in for the model adapter plugin.

A real DeepSeek Harness preset resolves `model` to an actual model
adapter. This POC has no model credentials wired up, so the "reasoning"
is replaced with one deterministic policy that plays the part of a single
agent used across both runs: given a cleanup prompt, find the best
available way to identify junk, then remove it if permitted to.

The demo's point rests entirely on this being the *same* policy in both
runs - what changes is which tools the preset mounts, not how the agent
thinks.
"""

NAIVE_JUNK_HINTS = ("temp", "tmp", "local", ".log", ".ds_store")


def looks_junk_naive(filename):
    """Crude fallback used only when no safe_scanner tool is mounted: a
    plain substring guess over the filename. It's what an agent with raw
    shell access and no structured scanner is left to improvise with -
    good enough to catch real junk, sloppy enough to also flag
    config.local.json as "junk" because it contains "local".
    """
    lowered = filename.lower()
    return any(hint in lowered for hint in NAIVE_JUNK_HINTS)
