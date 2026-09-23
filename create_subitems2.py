import json
import os
import time
from monday_api import gql

BATCH_SIZE = 12


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    with open("staff_board_meta2.json") as f:
        meta = json.load(f)
    day_staff_items = meta["day_staff_items"]
    cols = meta["sub_cols"]

    with open("schedule_normalized.json") as f:
        tasks = json.load(f)

    created = []
    if os.path.exists("created_subitems2.json"):
        with open("created_subitems2.json") as f:
            created = json.load(f)
    skip = len(created)
    if skip:
        print(f"Resuming, {skip} already created")

    total = len(tasks)
    i = skip
    while i < total:
        batch = tasks[i:i + BATCH_SIZE]
        parts = []
        for j, t in enumerate(batch):
            hh, mm = t["time"].split(":")
            cv = {
                cols["Time"]: {"hour": int(hh), "minute": int(mm)},
                cols["Status"]: {"label": "Not Started"},
            }
            cv_json = esc(json.dumps(cv))
            parent_id = day_staff_items[f'{t["day"]}||{t["staff"]}']
            item_name = esc(t["task"])
            parts.append(f'''
            m{j}: create_subitem(
                parent_item_id: {parent_id},
                item_name: "{item_name}",
                column_values: "{cv_json}"
            ) {{ id }}
            ''')
        mutation = "mutation {" + "".join(parts) + "}"
        data = gql(mutation)
        for j in range(len(batch)):
            created.append(data[f"m{j}"]["id"])

        i += len(batch)
        with open("created_subitems2.json", "w") as f:
            json.dump(created, f)
        print(f"  {i}/{total} subitems created", flush=True)
        time.sleep(1)

    print(f"Done. Total subitems created: {len(created)}")


if __name__ == "__main__":
    main()
