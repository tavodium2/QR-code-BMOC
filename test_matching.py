import json
from datetime import time
from matching import find_matching_tasks

template = json.load(open("template.json"))


def to_time(s):
    h, m = map(int, s.split(":"))
    return time(h, m)


def worker_day_tasks(worker, day):
    out = []
    for t in template:
        if t["worker"] == worker and t["day"] == day:
            out.append({**t, "start_time": to_time(t["start_time"])})
    return out


# Case 1: normal single match - Sidne, Mikvah, Sunday, at 07:55 (inside 07:50 window)
tasks = worker_day_tasks("Sidne", "Sunday")
m = find_matching_tasks(tasks, "Mikvah", time(7, 55))
print("Case 1 (expect 1 match, 'Check Mikva, Chlorine test'):", [t["task"] for t in m])

# Case 2: same worker, same area, different time slot later in the day - should resolve to a DIFFERENT task
m2 = find_matching_tasks(tasks, "Mikvah", time(10, 5))
print("Case 2 (expect a different Mikvah task, 'Check Mikva' at 10:00):", [t["task"] for t in m2])

# Case 3: outside any window - between tasks that don't cover this area at this moment
m3 = find_matching_tasks(tasks, "Mikvah", time(23, 0))
print("Case 3 (expect 0 matches, no Mikvah task active at 23:00):", [t["task"] for t in m3])

# Case 4: scanning the WRONG area for this worker at this time
m4 = find_matching_tasks(tasks, "Tents", time(7, 55))
print("Case 4 (expect 0 matches, Sidne isn't doing Tents at 07:55):", [t["task"] for t in m4])

# Case 5: last task of the day (open-ended window) still matches
last_task_time = max(t["start_time"] for t in tasks)
m5 = find_matching_tasks(tasks, next(t["area"] for t in tasks if t["start_time"] == last_task_time), time(23, 55))
print("Case 5 (expect last task to still match late at night):", [t["task"] for t in m5])
