import json
import os
import time
from monday_api import gql
from classify_area import classify

BATCH_SIZE = 20


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    with open("staff_board_meta2.json") as f:
        meta = json.load(f)
    sub_board_id = meta["sub_board_id"]
    area_col = meta["sub_cols"]["Area"]

    with open("schedule_normalized.json") as f:
        tasks = json.load(f)
    with open("created_subitems2.json") as f:
        item_ids = json.load(f)

    assert len(item_ids) == len(tasks), f"mismatch: {len(item_ids)} items vs {len(tasks)} tasks"

    progress_file = "area_update_progress.json"
    done = 0
    if os.path.exists(progress_file):
        done = json.load(open(progress_file))["done"]
        print(f"Resuming from {done}")

    total = len(tasks)
    i = done
    while i < total:
        batch = list(zip(item_ids[i:i + BATCH_SIZE], tasks[i:i + BATCH_SIZE]))
        parts = []
        for j, (item_id, t) in enumerate(batch):
            area = classify(t["task"])
            cv = {area_col: {"label": area}}
            cv_json = esc(json.dumps(cv))
            parts.append(f'''
            m{j}: change_multiple_column_values(
                board_id: {sub_board_id},
                item_id: {item_id},
                column_values: "{cv_json}"
            ) {{ id }}
            ''')
        mutation = "mutation {" + "".join(parts) + "}"
        gql(mutation)

        i += len(batch)
        json.dump({"done": i}, open(progress_file, "w"))
        print(f"  {i}/{total} area tags applied", flush=True)
        time.sleep(0.5)

    print("Done applying area colors.")


if __name__ == "__main__":
    main()
