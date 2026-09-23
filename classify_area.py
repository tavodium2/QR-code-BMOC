import re

AREAS = [
    "Bathrooms", "Tents", "20 Upstairs", "18 Main Synagogue",
    "Coffee Stations",
    "Kitchen Food Prep", "Kitchen Cleaning", "18 Upstairs",
    "Rabbi Coren's Office", "Mikvah", "Deep Cleaning of the Mikvah",
    "Property", "General / Other",
]

FOOD_PREP_EXACT = {
    "make pasta", "make farina", "set up soup", "fill up soup", "prep cholent",
    "fill up farina", "add to the soup pots", "check on soups",
    "have someone put up new soups if needed", "kitchen food prep",
    "prep 3 soups (friday 1 round)", "prep spaghetti or rice",
}

KITCHEN_CLEAN_EXACT = {
    "clean kitchen", "service kitchen", "reclean kitchen",
    "put away pots/utensils", "clean out fridges.", "clean fridges",
    "start with kitchen", "clean kitchen,wash all pots and utensils",
}


def classify(text):
    t = text.strip().lower()

    if t == "cleaning":
        return "Mikvah"

    if "mikv" in t:
        if "deep" in t:
            return "Deep Cleaning of the Mikvah"
        return "Mikvah"

    if "bathroom" in t:
        return "Bathrooms"

    if "tent" in t:
        return "Tents"

    if "coren" in t:
        return "Rabbi Coren's Office"

    if "coffee" in t:
        return "Coffee Stations"

    if t in FOOD_PREP_EXACT:
        return "Kitchen Food Prep"
    if t in KITCHEN_CLEAN_EXACT:
        return "Kitchen Cleaning"
    if "kitchen" in t:
        return "Kitchen Cleaning"

    if "18" in t and ("office" in t or "upstairs offices" in t):
        return "18 Upstairs"
    if "18" in t and "main" in t:
        return "18 Main Synagogue"
    if re.search(r"\b18\b", t) and "upstairs" in t:
        return "18 Upstairs"
    if re.search(r"\b18\b", t):
        return "18 Main Synagogue"

    if re.search(r"\b20\b", t) and "upstairs" in t:
        return "20 Upstairs"

    if any(k in t for k in ["outside", "parking", "walkway", "property", "advertisement", "ash tray", "sidewalk"]):
        return "Property"

    return "General / Other"


if __name__ == "__main__":
    import json
    from collections import Counter, defaultdict

    tasks = json.load(open("schedule_normalized.json"))
    counts = Counter()
    examples = defaultdict(list)
    for t in tasks:
        area = classify(t["task"])
        counts[area] += 1
        if len(examples[area]) < 6:
            examples[area].append(t["task"])

    for area in AREAS:
        print(f"{area:35s} {counts[area]:4d}  e.g. {examples[area][:4]}")
