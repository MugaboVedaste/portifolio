"""Flask backend for the portfolio.

The public pages look exactly like the old static site. The Certificates and
Projects sections are read from Neon Postgres; files are stored on Cloudinary.
A password-protected /admin area lets the owner add / edit / delete them.

Required environment variables (see .env.example):
    DATABASE_URL, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET, ADMIN_PASSWORD, FLASK_SECRET_KEY
"""
import os
import re
import secrets
import urllib.request
from functools import wraps
from urllib.parse import unquote, urlparse

import cloudinary
import cloudinary.uploader
import pg8000.dbapi
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

import seed_data

load_dotenv(".env.local")
load_dotenv()  # plain .env, if present

# Static files (style.css, script.js, assets/...) live in /public and are served
# at the site root, exactly like the old static site (and like Vercel's CDN).
app = Flask(__name__, static_folder="public", static_url_path="")
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
    # Vercel serverless functions reject request bodies larger than 4.5 MB.
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)

# The home page shows this many projects per category; the rest are on /projects.
HOME_PER_CATEGORY = 3

ALLOWED = {
    "png": "image", "jpg": "image", "jpeg": "image", "webp": "image",
    "pdf": "pdf",
}

CERT_SCHEMA = """
CREATE TABLE certificates (
    id            SERIAL PRIMARY KEY,
    kind          TEXT NOT NULL CHECK (kind IN ('image', 'pdf')),
    title         TEXT NOT NULL,
    subtitle      TEXT NOT NULL DEFAULT '',
    url           TEXT NOT NULL,
    public_id     TEXT,
    resource_type TEXT,
    position      INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

PROJECT_SCHEMA = """
CREATE TABLE projects (
    id           SERIAL PRIMARY KEY,
    slug         TEXT NOT NULL UNIQUE,
    category     TEXT NOT NULL,
    title        TEXT NOT NULL,
    brief        TEXT NOT NULL DEFAULT '',
    icon         TEXT NOT NULL DEFAULT 'fa-folder',
    tags         TEXT[] NOT NULL DEFAULT '{}',
    repo_url     TEXT NOT NULL DEFAULT '',
    live_url     TEXT NOT NULL DEFAULT '',
    image_url    TEXT NOT NULL DEFAULT '',
    image_alt    TEXT NOT NULL DEFAULT '',
    public_id    TEXT,
    overview     TEXT NOT NULL DEFAULT '',
    implemented  TEXT[] NOT NULL DEFAULT '{}',
    technologies TEXT[] NOT NULL DEFAULT '{}',
    learning     TEXT NOT NULL DEFAULT '',
    position     INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

PROFILE_SCHEMA = """
CREATE TABLE profile_images (
    id         SERIAL PRIMARY KEY,
    label      TEXT NOT NULL DEFAULT '',
    url        TEXT NOT NULL,
    public_id  TEXT,
    is_active  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

DEFAULT_PROFILE = "assets/images/profile1.jpg"

_schema_ready = False


# --------------------------------------------------------------------------
# Database (Neon). pg8000 is pure Python, so it works locally and on Vercel.
# --------------------------------------------------------------------------
def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    u = urlparse(url)
    return pg8000.dbapi.connect(
        user=unquote(u.username or ""),
        password=unquote(u.password or ""),
        host=u.hostname,
        port=u.port or 5432,
        database=(u.path or "/").lstrip("/"),
        ssl_context=True,  # Neon requires TLS
    )


def run(sql, params=(), fetch=None):
    """Run one statement in its own transaction.

    fetch: None -> nothing, "one" -> one row dict (or None), "all" -> list of dicts.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        result = None
        if fetch:
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            result = (rows[0] if rows else None) if fetch == "one" else rows
        conn.commit()
        return result
    finally:
        conn.close()


def table_exists(name):
    return run("SELECT to_regclass(%s) AS t", (f"public.{name}",), fetch="one")["t"] is not None


def ensure_schema():
    """Create the tables and seed the original content - only when a table is
    first created, so deleting everything later never brings old items back."""
    global _schema_ready
    if _schema_ready:
        return
    if not table_exists("certificates"):
        run(CERT_SCHEMA)
        for i, (kind, title, subtitle, url) in enumerate(seed_data.CERTIFICATES):
            run("INSERT INTO certificates (kind, title, subtitle, url, position) "
                "VALUES (%s, %s, %s, %s, %s)", (kind, title, subtitle, url, i))
    if not table_exists("projects"):
        run(PROJECT_SCHEMA)
        for i, p in enumerate(seed_data.PROJECTS):
            run(
                "INSERT INTO projects (slug, category, title, brief, icon, tags, repo_url, "
                "live_url, image_url, image_alt, overview, implemented, technologies, "
                "learning, position) VALUES (%s,%s,%s,%s,%s,%s::text[],%s,%s,%s,%s,%s,"
                "%s::text[],%s::text[],%s,%s) ON CONFLICT (slug) DO NOTHING",
                (p["slug"], p["category"], p["title"], p["brief"], p["icon"], p["tags"],
                 p["repo_url"], p["live_url"], p["image_url"], p["image_alt"],
                 p["overview"], p["implemented"], p["technologies"], p["learning"], i),
            )
    if not table_exists("profile_images"):
        run(PROFILE_SCHEMA)
        for label, url in seed_data.PROFILE_IMAGES:
            run("INSERT INTO profile_images (label, url, is_active) VALUES (%s, %s, %s)",
                (label, url, url == DEFAULT_PROFILE))
    _schema_ready = True


def list_profile_images():
    ensure_schema()
    return run("SELECT * FROM profile_images ORDER BY id", fetch="all")


def active_profile_url():
    ensure_schema()
    row = run("SELECT url FROM profile_images WHERE is_active LIMIT 1", fetch="one")
    return row["url"] if row else DEFAULT_PROFILE


def cld_opt(url, width=900):
    """Serve Cloudinary images resized + compressed (f_auto,q_auto). Others unchanged."""
    marker = "/image/upload/"
    if url and "res.cloudinary.com" in url and marker in url:
        return url.replace(marker, f"{marker}f_auto,q_auto,w_{width}/", 1)
    return url


app.jinja_env.filters["cld_opt"] = cld_opt


def list_certificates():
    ensure_schema()
    return run("SELECT * FROM certificates ORDER BY position, id", fetch="all")


def list_projects():
    ensure_schema()
    return run("SELECT * FROM projects ORDER BY position, id", fetch="all")


def group_by_category(projects, limit=None):
    """[(category, [projects...]), ...] in order of first appearance."""
    groups = {}
    for p in projects:
        groups.setdefault(p["category"], []).append(p)
    return [(cat, items[:limit] if limit else items) for cat, items in groups.items()]


def project_data(projects):
    """The data the 'View Details' modal in script.js reads."""
    return {
        p["slug"]: {
            "title": p["title"],
            "overview": p["overview"],
            "implemented": p["implemented"],
            "technologies": p["technologies"],
            "learning": p["learning"],
        }
        for p in projects
    }


# --------------------------------------------------------------------------
# Public site
# --------------------------------------------------------------------------
@app.route("/")
def index():
    try:
        certs = list_certificates()
        projects = list_projects()
        profile_url = active_profile_url()
    except Exception:  # keep the portfolio up even if the database is down
        app.logger.exception("Could not load content")
        certs, projects, profile_url = [], [], DEFAULT_PROFILE
    groups = group_by_category(projects)
    return render_template(
        "index.html",
        images=[c for c in certs if c["kind"] == "image"],
        pdfs=[c for c in certs if c["kind"] == "pdf"],
        categories=[(cat, items[:HOME_PER_CATEGORY]) for cat, items in groups],
        has_more=any(len(items) > HOME_PER_CATEGORY for _, items in groups),
        project_data=project_data(projects),
        profile_url=profile_url,
    )


@app.route("/projects")
def projects_page():
    try:
        projects = list_projects()
    except Exception:
        app.logger.exception("Could not load projects")
        projects = []
    return render_template(
        "projects.html",
        categories=group_by_category(projects),
        project_data=project_data(projects),
    )


# --------------------------------------------------------------------------
# Admin helpers
# --------------------------------------------------------------------------
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


def check_csrf():
    sent = request.form.get("csrf", "")
    if not secrets.compare_digest(sent, session.get("csrf", "")):
        abort(400, "Invalid CSRF token")


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper


def check_upload(file, allowed_kinds):
    """Validate extension AND content. Returns (kind, error)."""
    name = file.filename or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    kind = ALLOWED.get(ext)
    if kind not in allowed_kinds:
        return None, "Only PNG, JPG, WEBP images" + (" and PDF files" if "pdf" in allowed_kinds else "") + " are allowed."
    head = file.stream.read(8)
    file.stream.seek(0)
    is_pdf = head.startswith(b"%PDF")
    is_img = head.startswith((b"\x89PNG", b"\xff\xd8", b"RIFF"))
    if (kind == "pdf" and not is_pdf) or (kind == "image" and not is_img):
        return None, "File content does not match its type."
    return kind, None


def upload_to_cloudinary(file, folder):
    # PDFs are uploaded as "image" resources so Cloudinary serves them inline.
    return cloudinary.uploader.upload(
        file.stream, folder=f"portfolio/{folder}", resource_type="image"
    )


def deliverable(url):
    """True if Cloudinary will actually serve the file (PDFs can be blocked by
    the account's security settings, which answers 401)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        return urllib.request.urlopen(req, timeout=15).status == 200
    except Exception:
        return False


def destroy_asset(public_id):
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception:
        app.logger.exception("Cloudinary delete failed")


# --------------------------------------------------------------------------
# Admin: login
# --------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    expected = os.environ.get("ADMIN_PASSWORD")
    if request.method == "POST":
        check_csrf()
        if not expected:
            flash("ADMIN_PASSWORD is not configured on the server.", "error")
        elif secrets.compare_digest(request.form.get("password", ""), expected):
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("Wrong password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    check_csrf()
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin", strict_slashes=False)
@admin_required
def admin():
    return render_template("admin.html", certs=list_certificates(), projects=list_projects(),
                           profiles=list_profile_images())


# --------------------------------------------------------------------------
# Admin: certificates
# --------------------------------------------------------------------------
@app.route("/admin/upload", methods=["POST"])
@admin_required
def admin_upload():
    check_csrf()
    file = request.files.get("file")
    title = request.form.get("title", "").strip()[:120]
    subtitle = request.form.get("subtitle", "").strip()[:120]
    if not file or not file.filename:
        flash("Choose a file.", "error")
        return redirect(url_for("admin"))
    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("admin"))

    kind, error = check_upload(file, {"image", "pdf"})
    if error:
        flash(error, "error")
        return redirect(url_for("admin"))

    try:
        result = upload_to_cloudinary(file, "certificates")
    except Exception:
        app.logger.exception("Cloudinary upload failed")
        flash("Upload to Cloudinary failed. Check the Cloudinary credentials.", "error")
        return redirect(url_for("admin"))

    if kind == "pdf" and not deliverable(result["secure_url"]):
        destroy_asset(result["public_id"])
        flash("Cloudinary is blocking PDF delivery on this account, so the link would be "
              "broken. In the Cloudinary Console go to Settings → Security and enable "
              "“PDF and ZIP files delivery”, then upload again.", "error")
        return redirect(url_for("admin"))

    ensure_schema()
    pos = run("SELECT COALESCE(MAX(position), -1) + 1 AS p FROM certificates", fetch="one")["p"]
    run(
        "INSERT INTO certificates (kind, title, subtitle, url, public_id, resource_type, position) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (kind, title, subtitle, result["secure_url"], result["public_id"], "image", pos),
    )
    flash(f"Added “{title}”.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:cert_id>", methods=["POST"])
@admin_required
def admin_delete(cert_id):
    check_csrf()
    row = run("DELETE FROM certificates WHERE id = %s RETURNING public_id",
              (cert_id,), fetch="one")
    if row:
        destroy_asset(row["public_id"])
    flash("Deleted.", "ok")
    return redirect(url_for("admin"))


# --------------------------------------------------------------------------
# Admin: projects
# --------------------------------------------------------------------------
ICON_RE = re.compile(r"^fa-[a-z0-9-]{1,40}$")
ICONS = ["fa-folder", "fa-shopping-cart", "fa-boxes", "fa-palette", "fa-tshirt",
         "fa-mobile-alt", "fa-home", "fa-wind", "fa-code", "fa-server", "fa-database",
         "fa-chart-line", "fa-robot", "fa-globe", "fa-mobile", "fa-cogs", "fa-book",
         "fa-gamepad", "fa-heartbeat", "fa-graduation-cap"]
app.jinja_env.globals["ICONS"] = ICONS


def split_lines(text, limit=40):
    return [ln.strip()[:300] for ln in text.splitlines() if ln.strip()][:limit]


def split_csv(text, limit=20):
    return [t.strip()[:60] for t in text.split(",") if t.strip()][:limit]


def clean_url(value):
    """Only http(s) links are accepted (blocks javascript: and similar)."""
    value = value.strip()[:500]
    if not value:
        return "", None
    if not re.match(r"^https?://[^\s]+$", value, re.I):
        return "", "Links must start with http:// or https://"
    return value, None


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "project"
    return f"{s}-{secrets.token_hex(3)}"


def project_form_values(form):
    """Parse and validate the project form. Returns (values, error)."""
    repo, e1 = clean_url(form.get("repo_url", ""))
    live, e2 = clean_url(form.get("live_url", ""))
    icon = form.get("icon", "fa-folder").strip()
    v = {
        "category": form.get("category", "").strip()[:60],
        "title": form.get("title", "").strip()[:120],
        "brief": form.get("brief", "").strip()[:300],
        "icon": icon if ICON_RE.match(icon) else "fa-folder",
        "tags": split_csv(form.get("tags", ""), 8),
        "repo_url": repo,
        "live_url": live,
        "overview": form.get("overview", "").strip()[:2000],
        "implemented": split_lines(form.get("implemented", "")),
        "technologies": split_csv(form.get("technologies", "")),
        "learning": form.get("learning", "").strip()[:1000],
    }
    error = e1 or e2
    if not error and not v["category"]:
        error = "Category is required."
    if not error and not v["title"]:
        error = "Title is required."
    if not error and not v["overview"]:
        error = "Overview is required (it is shown in “View Details”)."
    return v, error


def save_project(project):
    """Shared by 'new' and 'edit'. `project` is the existing row or None."""
    check_csrf()
    values, error = project_form_values(request.form)
    file = request.files.get("image")
    has_file = bool(file and file.filename)

    if not error and has_file:
        _, error = check_upload(file, {"image"})
    if error:
        flash(error, "error")
        # Re-show the form with what the user typed.
        shown = dict(project or {})
        shown.update(values)
        shown["tags"] = request.form.get("tags", "")
        shown["implemented"] = request.form.get("implemented", "")
        shown["technologies"] = request.form.get("technologies", "")
        return render_template("admin_project.html", project=shown, editing=bool(project),
                               categories=existing_categories()), 400

    image_url = project["image_url"] if project else ""
    image_alt = project["image_alt"] if project else ""
    public_id = project["public_id"] if project else None
    old_public_id = None

    if has_file:
        try:
            result = upload_to_cloudinary(file, "projects")
        except Exception:
            app.logger.exception("Cloudinary upload failed")
            flash("Image upload failed. Check the Cloudinary credentials.", "error")
            return redirect(request.url)
        old_public_id = public_id
        image_url, public_id = result["secure_url"], result["public_id"]
        image_alt = f"{values['title']} screenshot"
    elif project and request.form.get("remove_image"):
        old_public_id = public_id
        image_url, image_alt, public_id = "", "", None

    args = (values["category"], values["title"], values["brief"], values["icon"],
            values["tags"], values["repo_url"], values["live_url"], image_url, image_alt,
            public_id, values["overview"], values["implemented"], values["technologies"],
            values["learning"])
    ensure_schema()
    if project:
        run(
            "UPDATE projects SET category=%s, title=%s, brief=%s, icon=%s, tags=%s::text[], "
            "repo_url=%s, live_url=%s, image_url=%s, image_alt=%s, public_id=%s, overview=%s, "
            "implemented=%s::text[], technologies=%s::text[], learning=%s WHERE id=%s",
            args + (project["id"],),
        )
    else:
        pos = run("SELECT COALESCE(MAX(position), -1) + 1 AS p FROM projects", fetch="one")["p"]
        run(
            "INSERT INTO projects (category, title, brief, icon, tags, repo_url, live_url, "
            "image_url, image_alt, public_id, overview, implemented, technologies, learning, "
            "slug, position) VALUES (%s,%s,%s,%s,%s::text[],%s,%s,%s,%s,%s,%s,%s::text[],"
            "%s::text[],%s,%s,%s)",
            args + (slugify(values["title"]), pos),
        )
    destroy_asset(old_public_id)
    flash(f"Saved “{values['title']}”.", "ok")
    return redirect(url_for("admin") + "#projects")


def existing_categories():
    return sorted({p["category"] for p in list_projects()})


def get_project_or_404(project_id):
    ensure_schema()
    row = run("SELECT * FROM projects WHERE id = %s", (project_id,), fetch="one")
    if not row:
        abort(404)
    return row


@app.route("/admin/projects/new", methods=["GET", "POST"])
@admin_required
def admin_project_new():
    if request.method == "POST":
        return save_project(None)
    return render_template("admin_project.html", project={"icon": "fa-folder"}, editing=False,
                           categories=existing_categories())


@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_project_edit(project_id):
    project = get_project_or_404(project_id)
    if request.method == "POST":
        return save_project(project)
    shown = dict(project)
    shown["tags"] = ", ".join(project["tags"])
    shown["implemented"] = "\n".join(project["implemented"])
    shown["technologies"] = ", ".join(project["technologies"])
    return render_template("admin_project.html", project=shown, editing=True,
                           categories=existing_categories())


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def admin_project_delete(project_id):
    check_csrf()
    row = run("DELETE FROM projects WHERE id = %s RETURNING public_id", (project_id,), fetch="one")
    if row:
        destroy_asset(row["public_id"])
    flash("Project deleted.", "ok")
    return redirect(url_for("admin") + "#projects")


# --------------------------------------------------------------------------
# Admin: profile image
# --------------------------------------------------------------------------
@app.route("/admin/profile/upload", methods=["POST"])
@admin_required
def admin_profile_upload():
    check_csrf()
    file = request.files.get("file")
    label = request.form.get("label", "").strip()[:80]
    if not file or not file.filename:
        flash("Choose an image.", "error")
        return redirect(url_for("admin") + "#profile")
    _, error = check_upload(file, {"image"})
    if error:
        flash(error, "error")
        return redirect(url_for("admin") + "#profile")
    try:
        result = upload_to_cloudinary(file, "profile")
    except Exception:
        app.logger.exception("Cloudinary upload failed")
        flash("Upload to Cloudinary failed. Check the Cloudinary credentials.", "error")
        return redirect(url_for("admin") + "#profile")

    ensure_schema()
    activate = bool(request.form.get("activate"))
    new = run(
        "INSERT INTO profile_images (label, url, public_id) VALUES (%s, %s, %s) RETURNING id",
        (label or "Profile photo", result["secure_url"], result["public_id"]), fetch="one")
    if activate:
        run("UPDATE profile_images SET is_active = (id = %s)", (new["id"],))
    flash("Profile image uploaded" + (" and now in use." if activate else "."), "ok")
    return redirect(url_for("admin") + "#profile")


@app.route("/admin/profile/<int:image_id>/use", methods=["POST"])
@admin_required
def admin_profile_use(image_id):
    check_csrf()
    ensure_schema()
    if not run("SELECT 1 AS x FROM profile_images WHERE id = %s", (image_id,), fetch="one"):
        abort(404)
    run("UPDATE profile_images SET is_active = (id = %s)", (image_id,))
    flash("Profile image changed.", "ok")
    return redirect(url_for("admin") + "#profile")


@app.route("/admin/profile/<int:image_id>/delete", methods=["POST"])
@admin_required
def admin_profile_delete(image_id):
    check_csrf()
    ensure_schema()
    row = run("SELECT is_active FROM profile_images WHERE id = %s", (image_id,), fetch="one")
    if not row:
        abort(404)
    if row["is_active"]:
        flash("That image is in use. Pick another one first, then delete it.", "error")
        return redirect(url_for("admin") + "#profile")
    gone = run("DELETE FROM profile_images WHERE id = %s RETURNING public_id", (image_id,), fetch="one")
    destroy_asset(gone["public_id"])
    flash("Image deleted.", "ok")
    return redirect(url_for("admin") + "#profile")


@app.errorhandler(413)
def too_large(_e):
    flash("File too large (max 4 MB).", "error")
    return redirect(url_for("admin") if session.get("admin") else url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
