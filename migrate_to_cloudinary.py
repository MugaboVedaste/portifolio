"""One-off: move the original local files (public/assets/...) to Cloudinary.

Usage (from the project folder, with .env.local filled in):
    python migrate_to_cloudinary.py            # images only
    python migrate_to_cloudinary.py --pdf      # also PDFs (needs the Cloudinary
                                               # "PDF and ZIP files delivery" setting ON)

Each file is uploaded, its URL is checked to be reachable, and only then is the
database row updated to point at Cloudinary. Safe to re-run: rows that already
point at Cloudinary are skipped. Local files are NOT deleted.
"""
import os
import sys
import urllib.error
import urllib.request

import cloudinary.uploader

from app import app, destroy_asset, ensure_schema, run  # noqa: F401  (importing app configures Cloudinary)

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
INCLUDE_PDF = "--pdf" in sys.argv


def reachable(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200
    except urllib.error.URLError as e:
        print("   not reachable:", getattr(e, "code", e))
        return False


def migrate(table, folder, col, title_col="title"):
    rows = run(
        f"SELECT id, {title_col} AS title, {col} AS url, public_id FROM {table} "
        f"WHERE public_id IS NULL AND {col} <> '' ORDER BY id", fetch="all")
    for r in rows:
        url = r["url"]
        if url.startswith("http"):
            continue
        is_pdf = url.lower().endswith(".pdf")
        if is_pdf and not INCLUDE_PDF:
            print(f"skip (PDF, run with --pdf later): {r['title']}")
            continue
        path = os.path.join(PUBLIC, *url.split("/"))
        if not os.path.isfile(path):
            print(f"missing file, skipped: {path}")
            continue
        print(f"uploading {r['title']} ...")
        res = cloudinary.uploader.upload(
            path, folder=f"portfolio/{folder}", resource_type="image",
            use_filename=True, unique_filename=True)
        if not reachable(res["secure_url"]):
            destroy_asset(res["public_id"])
            print("   -> NOT migrated (file not deliverable); left as local file")
            continue
        run(f"UPDATE {table} SET {col}=%s, public_id=%s WHERE id=%s",
            (res["secure_url"], res["public_id"], r["id"]))
        print("   -> done")


if __name__ == "__main__":
    ensure_schema()  # creates + seeds any table that does not exist yet
    migrate("certificates", "certificates", "url")
    migrate("projects", "projects", "image_url")
    migrate("profile_images", "profile", "url", title_col="label")
    print("finished")
