import json
import time
from monday_api import gql

MY_USER_ID = "117239346"


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


def create_staff_items(board_id, staff_names):
    # rename default group
    q = f'{{ boards(ids: {board_id}) {{ groups {{ id title }} }} }}'
    default_group = gql(q)["boards"][0]["groups"][0]["id"]
    gql(f'''
    mutation {{
      update_group(board_id: {board_id}, group_id: "{default_group}", group_attribute: title, new_value: "Staff") {{ id }}
    }}
    ''')

    items = {}
    for name in staff_names:
        q = f'''
        mutation {{
          create_item(board_id: {board_id}, group_id: "{default_group}", item_name: "{esc(name)}") {{ id }}
        }}
        '''
        items[name] = gql(q)["create_item"]["id"]
        print(f"  staff item: {name} -> {items[name]}")
    return items


def bootstrap_subitems_board(first_parent_id):
    q = f'''
    mutation {{
      create_subitem(parent_item_id: {first_parent_id}, item_name: "__bootstrap__") {{
        id
        board {{ id }}
      }}
    }}
    '''
    data = gql(q)["create_subitem"]
    sub_board_id = data["board"]["id"]
    bootstrap_item_id = data["id"]
    return sub_board_id, bootstrap_item_id


def create_subitem_columns(sub_board_id):
    cols = {}

    def add(title, col_type, settings=None):
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
        cols[title] = gql(q)["create_column"]["id"]

    add("Day", "status", {"labels": {
        "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
        "4": "Thursday", "5": "Friday", "6": "Saturday",
    }})
    add("Time", "hour")
    add("Status", "status", {"labels": {"0": "Not Started", "1": "Done"}})
    return cols


STAFF_ALIAS = {"Frantz": "Franz"}


def main():
    with open("schedule.json") as f:
        tasks = json.load(f)

    for t in tasks:
        t["staff"] = STAFF_ALIAS.get(t["staff"], t["staff"])

    staff_names = sorted(set(t["staff"] for t in tasks))
    print("Staff:", staff_names)

    print("Creating board...")
    board_id = create_board()
    print(f"  board_id = {board_id}")

    print("Creating staff main items...")
    staff_items = create_staff_items(board_id, staff_names)

    print("Bootstrapping subitems board...")
    first_staff = staff_names[0]
    sub_board_id, bootstrap_id = bootstrap_subitems_board(staff_items[first_staff])
    print(f"  sub_board_id = {sub_board_id}")

    print("Creating subitem columns...")
    sub_cols = create_subitem_columns(sub_board_id)
    print(f"  sub_cols = {sub_cols}")

    # delete bootstrap subitem
    gql(f'mutation {{ delete_item(item_id: {bootstrap_id}) {{ id }} }}')

    with open("schedule_normalized.json", "w") as f:
        json.dump(tasks, f, indent=2)

    with open("staff_board_meta.json", "w") as f:
        json.dump({
            "board_id": board_id,
            "sub_board_id": sub_board_id,
            "staff_items": staff_items,
            "sub_cols": sub_cols,
        }, f, indent=2)
    print("Saved staff_board_meta.json")


if __name__ == "__main__":
    main()
