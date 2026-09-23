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
from datetime import datetime, date, time as dtime

from matching import find_matching_tasks
from monday_api import gql


def _to_time(s):
    h, m = map(int, s.split(":"))
    return dtime(h, m)


class LocalTemplateSource:
    """Mock source for pre-production testing. Persists completions locally
    so state survives app restarts, without touching Monday at all."""

    uses_real_dates = False

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
    """Real Monday.com-backed source - the actual production path. Monday is the
    source of truth: items can be edited/added directly on the board and this
    class will pick up the change on the next scan (no caching)."""

    uses_real_dates = True

    def __init__(self, board_id, column_ids):
        self.board_id = board_id
        self.cols = column_ids  # dict: Date, Worker, Area, Start Time, Status, Completed By, Completed At

    def _fetch_all_items(self):
        col_ids_str = ", ".join(f'"{c}"' for c in self.cols.values())
        q = f'''
        {{
          boards(ids: {self.board_id}) {{
            items_page(limit: 100) {{
              items {{
                id
                name
                column_values(ids: [{col_ids_str}]) {{ id text }}
              }}
            }}
          }}
        }}
        '''
        data = gql(q)
        items = data["boards"][0]["items_page"]["items"]
        out = []
        for it in items:
            vals = {cv["id"]: cv["text"] for cv in it["column_values"]}
            out.append({
                "id": it["id"],
                "task": it["name"],
                "date": vals.get(self.cols["Date"], "") or "",
                "worker": vals.get(self.cols["Worker"], "") or "",
                "area": vals.get(self.cols["Area"], "") or "",
                "start_time_raw": vals.get(self.cols["Start Time"], "") or "",
                "status": vals.get(self.cols["Status"], "") or "",
            })
        return out

    def distinct_workers(self):
        items = self._fetch_all_items()
        return sorted(set(i["worker"] for i in items if i["worker"]))

    def distinct_areas(self):
        items = self._fetch_all_items()
        return sorted(set(i["area"] for i in items if i["area"]))

    def find_active_tasks(self, worker, area, date_str, now_time):
        """date_str: 'YYYY-MM-DD' (real date, since Monday is the source of truth
        and items are dated, not day-of-week templates)."""
        items = self._fetch_all_items()
        worker_tasks = []
        for i in items:
            if i["worker"] != worker or i["date"] != date_str:
                continue
            if not i["start_time_raw"]:
                continue
            # Monday's hour column renders as "07:50 AM" - parse to a time object
            t = datetime.strptime(i["start_time_raw"], "%I:%M %p").time()
            worker_tasks.append({**i, "start_time": t})

        matches = find_matching_tasks(worker_tasks, area, now_time)
        out = []
        for m in matches:
            if m["status"] == "Done":
                continue  # already completed, don't re-offer
            out.append({**m, "start_time": m["start_time"].strftime("%H:%M"), "key": m["id"]})
        return out

    def mark_done(self, task, worker):
        item_id = task["key"]
        cv = {
            self.cols["Status"]: {"label": "Done"},
            self.cols["Completed By"]: worker,
            self.cols["Completed At"]: datetime.now().isoformat(timespec="seconds"),
        }
        cv_json = json.dumps(json.dumps(cv))
        q = f'''
        mutation {{
          change_multiple_column_values(board_id: {self.board_id}, item_id: {item_id}, column_values: {cv_json}) {{ id }}
        }}
        '''
        gql(q)
        return True


def get_source():
    board_id = os.environ.get("PRODUCTION_BOARD_ID", "").strip()
    if board_id:
        # Prefer simple individual env vars (robust against dashboard UIs that
        # mangle pasted JSON via bracket/quote auto-pairing). Falls back to one
        # JSON blob (PRODUCTION_BOARD_COLUMNS) for convenience in local dev.
        simple = {
            "Date": os.environ.get("PRODUCTION_COL_DATE", ""),
            "Worker": os.environ.get("PRODUCTION_COL_WORKER", ""),
            "Area": os.environ.get("PRODUCTION_COL_AREA", ""),
            "Start Time": os.environ.get("PRODUCTION_COL_START_TIME", ""),
            "Status": os.environ.get("PRODUCTION_COL_STATUS", ""),
            "Completed By": os.environ.get("PRODUCTION_COL_COMPLETED_BY", ""),
            "Completed At": os.environ.get("PRODUCTION_COL_COMPLETED_AT", ""),
        }
        if all(simple.values()):
            return MondaySource(board_id, simple)

        raw = os.environ.get("PRODUCTION_BOARD_COLUMNS", "")
        if raw:
            return MondaySource(board_id, json.loads(raw))

        raise RuntimeError(
            "PRODUCTION_BOARD_ID is set but no column mapping was found "
            "(set the individual PRODUCTION_COL_* vars, or PRODUCTION_BOARD_COLUMNS as JSON)."
        )
    return LocalTemplateSource()
