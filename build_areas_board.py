import json
from monday_api import gql

MY_USER_ID = "117239346"

AREAS = [
    {
        "name": "Bathrooms",
        "checklist": [
            "Plunge if there is a clog, Snake if it needs it",
            "Clean toilet bowl and behind the seat",
            "Pick up seat and clean bottom of the seat",
            "Restock toilet paper/tissues",
            "Spray and wipe walls",
            "Refill soap dispenser or put out new disposable soap",
            "Sweep", "Mop",
            "(Weekly) Air fresheners, plugins and Zent diffusers",
        ],
    },
    {
        "name": "Tents",
        "checklist": [
            "Vacuum the whole tent (pay attention to walls and corners)",
            "Put all books in a stack on the end of each table",
            "All papers should be put in a stack on the end of the table",
            "Wipe down all tables, put a tissue box in the center",
            "Make all tables straight", "Make all chairs straight", "Empty garbage",
        ],
    },
    {
        "name": "20 Upstairs",
        "checklist": [
            "Clean and restock coffee area, clean fridge",
            "All books and papers stacked at end of each table",
            "Tissue boxes in center of each table", "Sweep floor",
            "Make all tables straight", "Make all chairs straight",
            "Change garbage bags", "Close all windows and lower shades",
            "(Friday) Spray and wipe windowsills and baseboards",
            "(Friday) Dust bookshelves",
        ],
    },
    {
        "name": "18 Main Synagogue",
        "checklist": [
            "All books and papers stacked at end of each table",
            "Wipe down all tables", "Sweep floor",
            "Make all tables straight", "Make all chairs straight",
            "Change garbage bags", "Close all windows and lower shades",
            "(Friday) Spray and wipe windowsills and baseboards",
            "(Friday) Dust bookshelves",
        ],
    },
    {
        "name": "Coffee Station of 18 Main",
        "checklist": [
            "Empty drain container", "Empty coffee drain", "Empty milk drain",
            "Add milk", "Refill coffee", "Refill sugar", "Refill cocoa",
            "Refill tea regular", "Refill tea decaf", "Brewed coffee",
            "Wash down counters", "Restock cups", "Restock covers",
            "Restock red straws", "Check on cookies",
            "Clean fridge, throw out anything that's not milk",
            "Sweep and mop area", "Throw out any papers, other food",
        ],
    },
    {
        "name": "Coffee Station of 18 Upstairs",
        "checklist": [
            "Empty drain container", "Empty coffee drain", "Empty milk drain",
            "Add milk", "Refill coffee", "Refill sugar", "Refill cocoa",
            "Refill tea regular", "Refill tea decaf",
            "Wash down counters", "Restock cups", "Restock covers",
            "Restock red straws",
            "Clean fridge, throw out anything that's not milk",
            "Throw out any papers, other food", "Sweep and mop, vacuum",
            "(Friday last cleaning) All coats/things on shelf go to Lost and Found shed",
        ],
    },
    {
        "name": "Kitchen Food Prep",
        "checklist": [
            "Prep 3 soups (Friday 1 round)", "Prep spaghetti or rice",
            "Check every 2 hrs and replenish as needed",
            "(Thursday) Make Cholent",
        ],
    },
    {
        "name": "Kitchen Cleaning",
        "checklist": [
            "Clean all pots and sink", "Change garbage bag",
            "Spray and wipe counter", "(Friday) Clean refrigerators",
        ],
    },
    {
        "name": "18 Upstairs",
        "checklist": [
            "Vacuum the room", "Close all windows and lower shades",
            "All papers stacked at end of table", "Wipe down all tables",
            "Make all tables straight", "Make all chairs straight",
            "(Friday) Spray and wipe windowsills and baseboards",
            "Vacuum hallway and sweep and mop",
        ],
    },
    {
        "name": "Rabbi Coren's Office",
        "checklist": [
            "All books and papers in a pile at end of table", "Wipe down all tables",
            "Vacuum", "Make all tables straight", "Make all chairs straight",
            "Change garbage bags",
        ],
    },
    {
        "name": "Mikvah",
        "checklist": [
            "Clean bathroom", "Pick up towels from the floor", "Empty towel bins",
            "Clean up shower room from bags, soap bars, anything left around",
            "Spray and wipe surfaces and mirrors",
        ],
    },
    {
        "name": "Deep Cleaning of the Mikvah",
        "checklist": [
            "Pick up towels from the floor", "Empty towel bins",
            "Clean up shower room from bags, soap bars, anything left around",
            "Spray down the shower walls", "Refill soap and shampoo as needed",
            "Refill towels", "Spray and wipe all surfaces",
            "(Last time of the day) Put in chlorine", "(Friday) Drain well filter",
        ],
    },
    {
        "name": "Property",
        "checklist": [
            "Walk around and pick up all wrappers, cigarette butts, water bottles, etc.",
            "Wipe down picnic tables", "Straighten out picnic tables",
            "Clean out ash trays", "Clean in between parking lot/bushes and sidewalk",
            "Clean parking lots near 18/20 and across the street",
            "Empty garbage bins",
            "Walk around and report all items that need repairs or cleaning",
            "Take inventory: towels, paper goods, food, cleaning supplies",
        ],
    },
]


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def create_board():
    q = '''
    mutation {
      create_board(board_name: "Area Cleaning Checklist (QR)", board_kind: public) {
        id
      }
    }
    '''
    return gql(q)["create_board"]["id"]


def create_columns(board_id):
    cols = {}

    def add(title, col_type, settings=None):
        settings_arg = ""
        if settings:
            settings_arg = f', defaults: {json.dumps(json.dumps(settings))}'
        q = f'''
        mutation {{
          create_column(board_id: {board_id}, title: "{title}", column_type: {col_type}{settings_arg}) {{
            id
          }}
        }}
        '''
        cols[title] = gql(q)["create_column"]["id"]

    add("Status", "status", {"labels": {"0": "Not Done Today", "1": "Done"}})
    add("Notify on Complete", "people")
    add("Facility Manager (escalation)", "people")
    add("Checklist Details", "long_text")
    add("QR Code", "file")
    return cols


def main():
    import sys
    if len(sys.argv) > 1:
        board_id = sys.argv[1]
        cols = {
            "Status": "color_mm7e2zbk",
            "Reset Frequency": "color_mm7evb0t",
            "Notify on Complete": "multiple_person_mm7ey4yz",
            "Facility Manager (escalation)": "multiple_person_mm7eztx6",
            "Checklist Details": "long_text_mm7ees76",
            "QR Code": "file_mm7ed4d2",
        }
        print(f"Reusing board_id = {board_id}")
    else:
        print("Creating Area Cleaning Checklist board...")
        board_id = create_board()
        print(f"  board_id = {board_id}")

        print("Creating columns...")
        cols = create_columns(board_id)
        print(f"  columns = {cols}")

    created = {}
    for area in AREAS:
        checklist_text = "\n".join(f"- {item}" for item in area["checklist"])
        cv = {
            cols["Status"]: {"label": "Not Done Today"},
            cols["Reset Frequency"]: {"label": "Once Daily"},
            cols["Notify on Complete"]: {"personsAndTeams": [{"id": int(MY_USER_ID), "kind": "person"}]},
            cols["Facility Manager (escalation)"]: {"personsAndTeams": [{"id": int(MY_USER_ID), "kind": "person"}]},
            cols["Checklist Details"]: checklist_text,
        }
        cv_json = esc(json.dumps(cv))
        item_name = esc(area["name"])
        q = f'''
        mutation {{
          create_item(
            board_id: {board_id},
            item_name: "{item_name}",
            column_values: "{cv_json}"
          ) {{ id }}
        }}
        '''
        item_id = gql(q)["create_item"]["id"]
        created[area["name"]] = item_id
        print(f'  created area item: {area["name"]} -> {item_id}')

    with open("areas_board_meta.json", "w") as f:
        json.dump({"board_id": board_id, "columns": cols, "items": created}, f, indent=2)
    print("Saved areas_board_meta.json")


if __name__ == "__main__":
    main()
