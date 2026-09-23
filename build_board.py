import json
from monday_api import gql

MY_USER_ID = "117239346"
DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


def create_board():
    q = """
    mutation {
      create_board(board_name: "Cleaning Schedule 2026", board_kind: public) {
        id
      }
    }
    """
    data = gql(q)
    return data["create_board"]["id"]


def create_columns(board_id):
    cols = {}

    def add(title, col_type, settings=None):
        settings_arg = ""
        if settings:
            settings_arg = f', defaults: {json.dumps(json.dumps(settings))}'
        q = f"""
        mutation {{
          create_column(board_id: {board_id}, title: "{title}", column_type: {col_type}{settings_arg}) {{
            id
          }}
        }}
        """
        data = gql(q)
        cols[title] = data["create_column"]["id"]

    add("Time", "hour")
    add("Staff", "text")
    add("Status", "status", {"labels": {"0": "Not Started", "1": "Done"}})
    add("Repeats This Day", "checkbox")
    add("Notify on Complete", "people")
    return cols


def create_groups(board_id):
    # board is created with one default group; rename it to Sunday, then add the rest
    q = f'{{ boards(ids: {board_id}) {{ groups {{ id title }} }} }}'
    data = gql(q)
    default_group = data["boards"][0]["groups"][0]["id"]

    groups = {}
    rename_q = f'''
    mutation {{
      update_group(board_id: {board_id}, group_id: "{default_group}", group_attribute: title, new_value: "Sunday") {{
        id
      }}
    }}
    '''
    gql(rename_q)
    groups["Sunday"] = default_group

    for day in DAYS[1:]:
        q = f'''
        mutation {{
          create_group(board_id: {board_id}, group_name: "{day}") {{
            id
          }}
        }}
        '''
        data = gql(q)
        groups[day] = data["create_group"]["id"]
    return groups


def main():
    import sys
    if len(sys.argv) > 1:
        board_id = sys.argv[1]
        print(f"Reusing board_id = {board_id}")
    else:
        print("Creating board...")
        board_id = create_board()
        print(f"  board_id = {board_id}")

    print("Creating columns...")
    cols = create_columns(board_id)
    print(f"  columns = {cols}")

    print("Creating groups...")
    groups = create_groups(board_id)
    print(f"  groups = {groups}")

    with open("board_meta.json", "w") as f:
        json.dump({"board_id": board_id, "columns": cols, "groups": groups}, f, indent=2)

    print("Saved board_meta.json")


if __name__ == "__main__":
    main()
