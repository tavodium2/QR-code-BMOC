import os
import re
import qrcode
from task_source import LocalTemplateSource

# Placeholder base URL - swap for the real deployed domain before printing for real use.
BASE_URL = os.environ.get("SCAN_APP_BASE_URL", "http://127.0.0.1:5055")

OUT_DIR = "qr_codes"


def slugify(area):
    return re.sub(r"[^a-z0-9]+", "-", area.lower()).strip("-")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    source = LocalTemplateSource()
    areas = source.distinct_areas()

    print(f"Generating {len(areas)} QR codes (base URL: {BASE_URL})")
    for area in areas:
        slug = slugify(area)
        url = f"{BASE_URL}/scan/{slug}"
        img = qrcode.make(url)
        path = os.path.join(OUT_DIR, f"{slug}.png")
        img.save(path)
        print(f"  {area:35s} -> {url}  ({path})")

    print(f"\n{len(areas)} QR codes written to {OUT_DIR}/")
    print("NOTE: these encode a LOCAL dev URL. Before printing/posting physically, "
          "regenerate with SCAN_APP_BASE_URL set to the real deployed domain.")
    print("NOTE: only the 12 confidently-resolved areas got a code. Tents/Bathrooms "
          "sub-splitting and the other open questions are still pending confirmation.")


if __name__ == "__main__":
    main()
