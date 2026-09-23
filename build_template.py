import json
from classify_conservative import classify

COLOR_TO_CATEGORY = {
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
    None: "Uncategorized",
}


def main():
    tasks = json.load(open("schedule.json"))       # raw, unmerged worker names
    colors = json.load(open("task_colors.json"))
    assert len(tasks) == len(colors)

    template = []
    for t, color in zip(tasks, colors):
        requires_qr, area = classify(t["task"])
        template.append({
            "day": t["day"],
            "start_time": t["time"],
            "worker": t["staff"],          # exact as written in Excel, NOT merged
            "task": t["task"],
            "requires_qr_scan": requires_qr,   # True / False / None (undetermined)
            "area": area,                       # resolved name, "UNRESOLVED: ..." or "UNCLASSIFIED: ..." or None
            "category_color": COLOR_TO_CATEGORY.get(color, "Uncategorized"),
        })

    with open("template.json", "w") as f:
        json.dump(template, f, indent=2)

    # summary
    distinct_workers = sorted(set(t["worker"] for t in template))
    print("Distinct worker strings (unmerged, exactly as in Excel):", distinct_workers)

    resolved = [t for t in template if t["requires_qr_scan"] is True and not str(t["area"]).startswith(("UNRESOLVED", "UNCLASSIFIED"))]
    unresolved_physical = [t for t in template if t["requires_qr_scan"] is True and str(t["area"]).startswith("UNRESOLVED")]
    unclassified = [t for t in template if t["requires_qr_scan"] is None]
    not_area = [t for t in template if t["requires_qr_scan"] is False]

    print(f"\nQR-ready (confident area):     {len(resolved)}")
    print(f"QR-eligible but area unresolved: {len(unresolved_physical)}")
    print(f"Needs manual review (unclear):  {len(unclassified)}")
    print(f"Not area-based (no QR needed):  {len(not_area)}")
    print(f"TOTAL:                          {len(template)}")


if __name__ == "__main__":
    main()
