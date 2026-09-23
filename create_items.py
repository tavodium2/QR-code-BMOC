import json
import time
from monday_api import gql

MY_USER_ID = "117239346"
BATCH_SIZE = 15


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_column_values(cols, time_str, staff, twice_daily):
    hh, mm = time_str.split(":")
    cv = {
        cols["Time"]: {"hour": int(hh), "minute": int(mm)},
        cols["Staff"]: staff,
        cols["Status"]: {"label": "Not Started"},
        cols["Notify on Complete"]: {"personsAndTeams": [{"id": int(MY_USER_ID), "kind": "person"}]},
    }
    if twice_daily:
        cv[cols["Repeats This Day"]] = {"checked": "true"}
    return cv


def main():
    with open("board_meta.json") as f:
        meta = json.load(f)
    board_id = meta["board_id"]
    cols = meta["columns"]
    groups = meta["groups"]

    with open("schedule.json") as f:
        tasks = json.load(f)

    created_ids = []
    skip = len(created_ids)
    if __import__("os").path.exists("created_items.json"):
        with open("created_items.json") as f:
            created_ids = json.load(f)
        skip = len(created_ids)
        print(f"Resuming, {skip} already created")

    total = len(tasks)
    i = skip
    while i < total:
        batch = tasks[i:i + BATCH_SIZE]
        mutation_parts = []
        for j, t in enumerate(batch):
            cv = build_column_values(cols, t["time"], t["staff"], t["twice_daily"])
            cv_json = esc(json.dumps(cv))
            group_id = groups[t["day"]]
            item_name = esc(t["task"])
            mutation_parts.append(f'''
            m{j}: create_item(
                board_id: {board_id},
                group_id: "{group_id}",
                item_name: "{item_name}",
                column_values: "{cv_json}"
            ) {{ id }}
            ''')
        mutation = "mutation {" + "".join(mutation_parts) + "}"
        data = gql(mutation)
        for j in range(len(batch)):
            created_ids.append(data[f"m{j}"]["id"])

        i += len(batch)
        with open("created_items.json", "w") as f:
            json.dump(created_ids, f)
        print(f"  {i}/{total} items created")
        time.sleep(1)

    print(f"Done. Total items created: {len(created_ids)}")


if __name__ == "__main__":
    main()
