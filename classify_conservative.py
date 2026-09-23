import re

# Areas reliably supported by Excel/Details data (confident matches only).
# Anything not matching one of these falls to UNRESOLVED (if physically-implied)
# or NOT_AREA_BASED (if it's inherently non-physical: break, admin, supply refill).

RESOLVED_AREAS = [
    "Bathrooms", "Tents", "20 Upstairs", "18 Main Synagogue",
    "Coffee Stations",  # general concept confident; WHICH specific station is an open question
    "Kitchen Food Prep", "Kitchen Cleaning", "18 Upstairs",
    "Rabbi Coren's Office", "Mikvah", "Deep Cleaning of the Mikvah",
    "Property",
]

# Physically-implied but NOT confidently resolvable to a Details-sheet area
# (open questions #2 and #3) - requires_qr_scan=True, area=UNRESOLVED
UNRESOLVED_PATTERNS = [
    (re.compile(r"\b20\s*(down|downstairs|dwn)\b"), "UNRESOLVED: 20 Downstairs (not in Details sheet)"),
    (re.compile(r"confer(e|a)nce\s*room"), "UNRESOLVED: Conference Room (not in Details sheet)"),
]

FOOD_PREP_EXACT = {
    "make pasta", "make farina", "set up soup", "fill up soup", "prep cholent",
    "fill up farina", "add to the soup pots", "check on soups",
    "have someone put up new soups if needed", "kitchen food prep",
    "prep 3 soups (friday 1 round)", "prep spaghetti or rice", "food prep",
}
KITCHEN_CLEAN_EXACT = {
    "clean kitchen", "service kitchen", "reclean kitchen",
    "put away pots/utensils", "clean out fridges.", "clean fridges",
    "start with kitchen", "clean kitchen,wash all pots and utensils",
}

# Tasks that are inherently non-physical - never area-bound, regardless of wording
NOT_AREA_EXACT = {
    "lunch break", "breakfast", "good night", "supper break",
    "take inventory", "update lists", "update purchasing requests",
    "report with issues/orders", "report with issues/ordering",
    "restock water bottles", "fill water bottles", "fill water bottles 20",
    "fill water bottles 20-18", "fill up water bottles 18",
    "fill up water bottles 20", "fill up water bottles 18/20",
    "restock all paper towels and tissues", "restock tissues papertowels",
    "restock paper towels", "deliver mail/packages", "fill towels",
    "fill soaps", "restock", "tables", "vaccum",
    "check on all locations that all is in order",
    "leave unless the avos ubanim needs cleaning.",
    "serve kiddush 1", "serve kiddush 2", "serve kiddush  3",
    "prepare kiddush", "setup kiddush 3",
}


def classify(text):
    """Returns (requires_qr_scan: bool, area: str|None)"""
    raw = text.strip()
    t = raw.lower()

    if "mikv" in t:
        if "deep" in t:
            return True, "Deep Cleaning of the Mikvah"
        return True, "Mikvah"

    if "bathroom" in t:
        return True, "Bathrooms"

    for pattern, label in UNRESOLVED_PATTERNS:
        if pattern.search(t):
            return True, label

    if "tent" in t:
        return True, "Tents"

    if "coren" in t:
        return True, "Rabbi Coren's Office"

    if "coffee" in t:
        return True, "Coffee Stations"

    if t in FOOD_PREP_EXACT:
        return True, "Kitchen Food Prep"
    if t in KITCHEN_CLEAN_EXACT:
        return True, "Kitchen Cleaning"
    if "kitchen" in t:
        return True, "Kitchen Cleaning"

    if "18" in t and ("office" in t):
        return True, "18 Upstairs"
    if "18" in t and "main" in t:
        return True, "18 Main Synagogue"
    if re.search(r"\b18\b", t) and "upstairs" in t:
        return True, "18 Upstairs"

    if re.search(r"\b20\b", t) and "upstairs" in t:
        return True, "20 Upstairs"

    if any(k in t for k in ["outside", "parking", "walkway", "property", "advertisement", "ash tray", "sidewalk"]):
        return True, "Property"

    if t in NOT_AREA_EXACT:
        return False, None

    # anything else: unclear whether it's area-bound - do not guess either way,
    # surface explicitly for manual review rather than silently bucketing
    return None, "UNCLASSIFIED: needs manual review"


if __name__ == "__main__":
    import json
    from collections import Counter, defaultdict

    tasks = json.load(open("schedule.json"))  # unmerged staff names (raw from Excel)
    counts = Counter()
    examples = defaultdict(list)
    for t in tasks:
        qr, area = classify(t["task"])
        key = area if area else ("NOT_AREA_BASED" if qr is False else "UNCLASSIFIED")
        counts[key] += 1
        if len(examples[key]) < 5:
            examples[key].append(t["task"])

    for key, n in counts.most_common():
        print(f"{key:55s} {n:4d}  e.g. {examples[key]}")
    print("\nTOTAL:", sum(counts.values()))
