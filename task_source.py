"""
Pluggable data source for the scan-handler app.

LocalTemplateSource: reads template.json + a local completions.json file.
Used until a real Monday board exists - lets us fully exercise the matching
flow end-to-end without touching production.

MondaySource: queries/updates the real Monday.com board. Activates
automatically once BOARD_ID is set in .env (i.e. once the production board
has been created and approved).
"""
import json
import os
from datetime import datetime, time as dtime

from matching import find_matching_tasks


def _to_time(s):
    h, m = map(int, s.split(":"))
    return dtime(h, m)


class LocalTemplateSource:
    """Mock source for pre-production testing. Persists completions locally
    so state survives app restarts, without touching Monday at all."""

    def __init__(self, template_path="template.json", completions_path="completions.json"):
        self.template_path = template_path
        self.completions_path = completions_path
        self.template = json.load(open(template_path))
        self.completions = {}
        if os.path.exists(completions_path):
            self.completions = json.load(open(completions_path))

    def _save(self):
        json.dump(self.completions, open(self.completions_path, "w"), indent=2)

    def _task_key(self, day, worker, start_time, area, task):
        return f"{day}|{worker}|{start_time}|{area}|{task}"

    def distinct_workers(self):
        return sorted(set(t["worker"] for t in self.template))

    def distinct_areas(self):
        areas = set()
        for t in self.template:
            a = t["area"]
            if a and not str(a).startswith(("UNRESOLVED", "UNCLASSIFIED")):
                areas.add(a)
        return sorted(areas)

    def find_active_tasks(self, worker, area, day, now_time):
        """day: e.g. 'Sunday' (simulated 'today' since there's no real date yet).
        Returns list of task dicts with a 'key' field for later completion."""
        worker_tasks = [
            {**t, "start_time": _to_time(t["start_time"])}
            for t in self.template
            if t["worker"] == worker and t["day"] == day
        ]
        matches = find_matching_tasks(worker_tasks, area, now_time)
        out = []
        for m in matches:
            key = self._task_key(day, worker, m["start_time"].strftime("%H:%M"), area, m["task"])
            if self.completions.get(key):
                continue  # already done, don't re-offer
            out.append({**m, "start_time": m["start_time"].strftime("%H:%M"), "key": key})
        return out

    def mark_done(self, task, worker):
        key = task["key"]
        self.completions[key] = {
            "completed_by": worker,
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._save()
        return True


class MondaySource:
    """Real Monday.com-backed source. Only usable once BOARD_ID is configured."""

    def __init__(self, board_id, column_ids):
        self.board_id = board_id
        self.column_ids = column_ids  # dict: worker, area, date, start_time, status, completed_by, completed_at

    def find_active_tasks(self, worker, area, day, now_time):
        raise NotImplementedError(
            "MondaySource requires the production board's exact column IDs and "
            "item layout, which don't exist yet - board hasn't been created/approved."
        )

    def mark_done(self, task, worker):
        raise NotImplementedError("Same as above - not wired until the real board exists.")


def get_source():
    board_id = os.environ.get("PRODUCTION_BOARD_ID", "").strip()
    if board_id:
        raise RuntimeError(
            "PRODUCTION_BOARD_ID is set, but MondaySource isn't implemented yet "
            "(needs the approved board's real column IDs). Unset it to keep using "
            "LocalTemplateSource for testing."
        )
    return LocalTemplateSource()
