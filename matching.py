"""
Core task-matching logic: given a worker, an area, and "now", find the correct
scheduled task item in Monday.com.

Matching rule (per approved Phase 1/2 design):
  - Candidate tasks = items where Area == scanned area, Worker == selected worker,
    Date == today.
  - A task's "active window" = from its Start Time until that SAME worker's
    NEXT listed task that day (the Excel source has no explicit end times).
  - "now" must fall inside that window for a task to be considered active.
  - Zero matches -> caller must show "no scheduled task found".
  - Multiple matches -> caller must show them for explicit human choice, never guess.
"""
from datetime import datetime, timedelta


def compute_active_window(worker_tasks_today, task):
    """worker_tasks_today: all of one worker's tasks today, sorted by start_time (datetime.time).
    task: the specific task dict to compute a window for.
    Returns (window_start, window_end) as datetime.time objects.
    window_end is the start time of the worker's next task that day, or
    end-of-day (23:59) if this is their last task.
    """
    times = sorted(worker_tasks_today, key=lambda t: t["start_time"])
    idx = times.index(task)
    window_start = task["start_time"]
    if idx + 1 < len(times):
        window_end = times[idx + 1]["start_time"]
    else:
        window_end = None  # open-ended: last task of the day
    return window_start, window_end


def find_matching_tasks(all_tasks_for_worker_today, area, now_time):
    """all_tasks_for_worker_today: list of task dicts (already filtered to one worker,
       one date), each with start_time (datetime.time) and area (str).
    area: the scanned area (str), must match exactly.
    now_time: datetime.time of the current moment.
    Returns list of matching task dicts (0, 1, or many).
    """
    area_tasks = [t for t in all_tasks_for_worker_today if t.get("area") == area]
    matches = []
    for t in area_tasks:
        start, end = compute_active_window(all_tasks_for_worker_today, t)
        if end is None:
            in_window = now_time >= start
        else:
            in_window = start <= now_time < end
        if in_window:
            matches.append(t)
    return matches
