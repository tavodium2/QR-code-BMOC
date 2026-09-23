import json
import os
import time
from monday_api import gql

BATCH_SIZE = 5

COLOR_TO_AREA = {
    "FFB6D7A8": "Main Building (18/20) & Coffee",
    "FFE06666": "Property (Outside)",
    "FFD5A6BD": "Kitchen",
    "FFFFFFFF": "Bathrooms",
    "FF00FFFF": "Mikvah",
    "FFFFD966": "Tents",
    "FFFFE599": "Tents",
    "FFF4CCCC": "Meals / Breaks",
    "FFA4C2F4": "Water Bottles",
    "FF6D9EEB": "Water Bottles",
    "FF9FC5E8": "Water Bottles",
    "FF6FA8DC": "Water Bottles",
    "FFCCCCCC": "End of Shift",
    "FFD9D9D9": "End of Shift",
    None: "Bathrooms",
}


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    with open("staff_board_meta2.json") as f:
        meta = json.load(f)
    sub_board_id = meta["sub_board_id"]
    area_col = meta["sub_cols"]["Area"]

    with open("created_subitems2.json") as f:
        item_ids = json.load(f)
    with open("task_colors.json") as f:
        colors = json.load(f)

    assert len(item_ids) == len(colors), f"mismatch: {len(item_ids)} items vs {len(colors)} colors"

    progress_file = "area_from_color_progress.json"
    done = 0
    if os.path.exists(progress_file):
        done = json.load(open(progress_file))["done"]
        print(f"Resuming from {done}")

    total = len(item_ids)
    i = done
    while i < total:
        batch = list(zip(item_ids[i:i + BATCH_SIZE], colors[i:i + BATCH_SIZE]))
        parts = []
        for j, (item_id, color) in enumerate(batch):
            area = COLOR_TO_AREA.get(color, "Bathrooms" if color is None else None)
            if area is None:
                raise RuntimeError(f"Unmapped color: {color}")
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
        time.sleep(1.5)

    print("Done.")


if __name__ == "__main__":
    main()
