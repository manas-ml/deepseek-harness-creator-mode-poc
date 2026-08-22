"""Cordis plugin: event log.

Records every step of a session - the prompt, each tool call and its
result, and the final response - so the run can be dumped afterwards as
an inspectable trajectory.
"""
import datetime


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class EventLog:
    name = "event_log"

    def __init__(self):
        self.events = []

    def log(self, kind, data):
        self.events.append({"seq": len(self.events), "ts": _now(), "kind": kind, "data": data})

    def dump(self):
        return list(self.events)
