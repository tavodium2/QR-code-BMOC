import json
import os
import time
from collections import defaultdict
from monday_api import gql

DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def create_board():
    q = '''
    mutation {
      create_board(board_name: "Staff Cleaning Tasks", board_kind: public) {
        id
      }
    }
    '''
    return gql(q)["create_board"]["id"]


def create_groups(board_id):
    q = f'{{ boards(ids: {board_id}) {{ groups {{ id title }} }} }}'
    default_group = gql(q)["boards"][0]["groups"][0]["id"]
    gql(f'''
    mutation {{
      update_group(board_id: {board_id}, group_id: "{default_group}", group_attribute: title, new_value: "{DAYS[0]}") {{ id }}
    }}
    ''')
    groups = {DAYS[0]: default_group}
    for day in DAYS[1:]:
        q = f'''
        mutation {{
          create_group(board_id: {board_id}, group_name: "{day}") {{ id }}
        }}
        '''
        groups[day] = gql(q)["create_group"]["id"]
    return groups


def main():
    with open("schedule_normalized.json") as f:
        tasks = json.load(f)

    by_day_staff = defaultdict(list)
    for t in tasks:
        by_day_staff[(t["day"], t["staff"])].append(t)

    print("Creating board...")
    board_id = create_board()
    print(f"  board_id = {board_id}")

    print("Creating day groups...")
    groups = create_groups(board_id)
    print(f"  groups = {groups}")

    print("Creating staff-per-day items...")
    day_staff_items = {}  # (day, staff) -> item_id
    for day in DAYS:
        staff_today = sorted(set(s for (d, s) in by_day_staff if d == day))
        for staff in staff_today:
            q = f'''
            mutation {{
              create_item(board_id: {board_id}, group_id: "{groups[day]}", item_name: "{esc(staff)}") {{ id }}
            }}
            '''
            item_id = gql(q)["create_item"]["id"]
            day_staff_items[(day, staff)] = item_id
        print(f"  {day}: {staff_today}")

    print("Bootstrapping subitems board...")
    first_key = next(iter(day_staff_items))
    q = f'''
    mutation {{
      create_subitem(parent_item_id: {day_staff_items[first_key]}, item_name: "__bootstrap__") {{
        id
        board {{ id }}
      }}
    }}
    '''
    data = gql(q)["create_subitem"]
    sub_board_id = data["board"]["id"]
    bootstrap_id = data["id"]
    print(f"  sub_board_id = {sub_board_id}")

    def add_col(title, col_type, settings=None):
        settings_arg = ""
        if settings:
            settings_arg = f', defaults: {json.dumps(json.dumps(settings))}'
        q = f'''
        mutation {{
          create_column(board_id: {sub_board_id}, title: "{title}", column_type: {col_type}{settings_arg}) {{
            id
          }}
        }}
        '''
        return gql(q)["create_column"]["id"]

    sub_cols = {
        "Time": add_col("Time", "hour"),
        "Status": add_col("Status", "status", {"labels": {"0": "Not Started", "1": "Done"}}),
    }
    print(f"  sub_cols = {sub_cols}")

    gql(f'mutation {{ delete_item(item_id: {bootstrap_id}) {{ id }} }}')

    meta = {
        "board_id": board_id,
        "sub_board_id": sub_board_id,
        "groups": groups,
        "day_staff_items": {f"{d}||{s}": v for (d, s), v in day_staff_items.items()},
        "sub_cols": sub_cols,
    }
    with open("staff_board_meta2.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("Saved staff_board_meta2.json")


if __name__ == "__main__":
    main()
