import re
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

from task_source import get_source

app = Flask(__name__)
source = get_source()

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def today_name():
    # Python's date.weekday(): Monday=0..Sunday=6; DAYS starts at Sunday.
    wd = datetime.now().weekday()
    return DAYS[0] if wd == 6 else DAYS[wd + 1]


def slugify(area):
    return re.sub(r"[^a-z0-9]+", "-", area.lower()).strip("-")


AREA_SLUGS = {slugify(a): a for a in source.distinct_areas()}


@app.route("/")
def index():
    # dev-only index listing all area scan links, so this can be tested without printed QR codes yet
    return render_template("index.html", areas=sorted(AREA_SLUGS.items(), key=lambda x: x[1]))


@app.route("/scan/<area_slug>")
def scan(area_slug):
    area = AREA_SLUGS.get(area_slug)
    if not area:
        return render_template("error.html", message=f"Unknown area code: {area_slug}"), 404
    workers = source.distinct_workers()
    return render_template("scan.html", area=area, area_slug=area_slug, workers=workers,
                            simulated_day=request.args.get("day", today_name()))


@app.route("/scan/<area_slug>/complete", methods=["POST"])
def complete(area_slug):
    area = AREA_SLUGS.get(area_slug)
    if not area:
        return render_template("error.html", message=f"Unknown area code: {area_slug}"), 404

    worker = request.form.get("worker")
    day = request.form.get("day", DAYS[0])
    now_str = request.form.get("now_time", "")
    if now_str:
        hh, mm = map(int, now_str.split(":"))
        now_time = datetime.now().replace(hour=hh, minute=mm).time()
    else:
        now_time = datetime.now().time()

    matches = source.find_active_tasks(worker, area, day, now_time)

    if len(matches) == 0:
        return render_template(
            "result.html", status="none", area=area, worker=worker,
            message="No scheduled task found for this worker and area at this time.",
        )
    if len(matches) > 1:
        return render_template(
            "result.html", status="multiple", area=area, worker=worker, matches=matches,
            message="Multiple possible tasks found - please pick the correct one.",
            area_slug=area_slug, day=day,
        )

    task = matches[0]
    source.mark_done(task, worker)
    return render_template("result.html", status="done", area=area, worker=worker, task=task)


@app.route("/scan/<area_slug>/complete_specific", methods=["POST"])
def complete_specific(area_slug):
    area = AREA_SLUGS.get(area_slug)
    worker = request.form.get("worker")
    day = request.form.get("day")
    task_key = request.form.get("task_key")

    matches = source.find_active_tasks(worker, area, day, datetime.now().time())
    task = next((m for m in matches if m["key"] == task_key), None)
    if not task:
        return render_template("error.html", message="That task is no longer available (maybe already completed)."), 400

    source.mark_done(task, worker)
    return render_template("result.html", status="done", area=area, worker=worker, task=task)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5055))
    app.run(debug=True, host="127.0.0.1", port=port)
