import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Use Render environment variable if set (recommended), otherwise fallback for local dev
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

# Make DB path robust (works on Render and locally)
DB_NAME = os.path.join(os.path.dirname(__file__), "app.db")


# ---------- Database helpers ----------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def login_required():
    return session.get("user_id") is not None


def current_user_id():
    return session.get("user_id")


# ---------- Page routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        return render_template("register.html", error="Username and password are required.")

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        conn.close()
        return render_template("register.html", error="Username already exists.")

    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password))
    )
    conn.commit()
    conn.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        return render_template("login.html", error="Please enter username and password.")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid username or password.")

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session.get("username"))


# ---------- API routes for tasks ----------
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401

    user_id = current_user_id()

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, task, created_at FROM tasks WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    tasks = [{"id": r["id"], "task": r["task"], "created_at": r["created_at"]} for r in rows]
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    task = (data.get("task") or "").strip()

    if not task:
        return jsonify({"error": "Task cannot be empty"}), 400

    user_id = current_user_id()

    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO tasks (user_id, task) VALUES (?, ?)",
        (user_id, task)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"message": "Saved", "id": new_id})


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401

    user_id = current_user_id()

    conn = get_db_connection()
    cur = conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Deleted", "id": task_id})


# ✅ IMPORTANT FOR RENDER (Gunicorn imports app.py, so init_db must run on import)
init_db()

if __name__ == "__main__":
    app.run(debug=True)
