"""
vulnerable_app.py — A deliberately insecure Flask application.
DO NOT deploy this anywhere. It exists solely to test security reviewers.
"""

import os
import re
import pickle
import hashlib
import logging
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from tempfile import mktemp
from flask import Flask, request, redirect, render_template_string, session, jsonify

app = Flask(__name__)
app.secret_key = "changeme"  # Weak / default secret key

# ──────────────────────────────────────────────────────────────────────
# 1. Hardcoded credentials & API keys
# ──────────────────────────────────────────────────────────────────────
DB_USER = "root"
DB_PASS = "toor"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# ──────────────────────────────────────────────────────────────────────
# 2. Logging sensitive data
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    logging.debug(f"Login attempt: user={username}, pass={password}")

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    # 3. SQL Injection
    cur.execute(
        "SELECT * FROM users WHERE username='" + username +
        "' AND password='" + password + "'"
    )
    user = cur.fetchone()
    conn.close()

    if user:
        session["user"] = username
        return redirect("/dashboard")
    return "Invalid credentials", 401


# ──────────────────────────────────────────────────────────────────────
# 4. Insecure password hashing (MD5, no salt)
# ──────────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    password_hash = hashlib.md5(password.encode()).hexdigest()

    conn = sqlite3.connect("app.db")
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password_hash),
    )
    conn.commit()
    conn.close()
    return "Registered", 201


# ──────────────────────────────────────────────────────────────────────
# 5. OS Command Injection
# ──────────────────────────────────────────────────────────────────────
@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    result = subprocess.check_output(f"ping -c 3 {host}", shell=True)
    return result


# ──────────────────────────────────────────────────────────────────────
# 6. Server-Side Template Injection (SSTI)
# ──────────────────────────────────────────────────────────────────────
@app.route("/greet")
def greet():
    name = request.args.get("name", "World")
    template = f"<h1>Hello, {name}!</h1>"
    return render_template_string(template)


# ──────────────────────────────────────────────────────────────────────
# 7. Reflected XSS (no escaping)
# ──────────────────────────────────────────────────────────────────────
@app.route("/search")
def search():
    query = request.args.get("q", "")
    return f"<p>Results for: {query}</p>"


# ──────────────────────────────────────────────────────────────────────
# 8. Path Traversal / Arbitrary File Read
# ──────────────────────────────────────────────────────────────────────
@app.route("/read")
def read_file():
    filename = request.args.get("file")
    with open("/var/data/" + filename) as f:
        return f.read()


# ──────────────────────────────────────────────────────────────────────
# 9. Insecure Deserialization
# ──────────────────────────────────────────────────────────────────────
@app.route("/import_profile", methods=["POST"])
def import_profile():
    blob = request.get_data()
    profile = pickle.loads(blob)
    return jsonify(profile)


# ──────────────────────────────────────────────────────────────────────
# 10. Open Redirect
# ──────────────────────────────────────────────────────────────────────
@app.route("/redirect")
def open_redirect():
    url = request.args.get("url")
    return redirect(url)


# ──────────────────────────────────────────────────────────────────────
# 11. XML External Entity (XXE) Injection
# ──────────────────────────────────────────────────────────────────────
@app.route("/parse_xml", methods=["POST"])
def parse_xml():
    xml_data = request.get_data()
    tree = ET.fromstring(xml_data)
    return tree.text or ""


# ──────────────────────────────────────────────────────────────────────
# 12. Insecure Temporary File (race condition)
# ──────────────────────────────────────────────────────────────────────
@app.route("/upload", methods=["POST"])
def upload():
    tmp_path = mktemp()  # predictable, race-prone
    with open(tmp_path, "wb") as f:
        f.write(request.get_data())
    return f"Saved to {tmp_path}"


# ──────────────────────────────────────────────────────────────────────
# 13. Mass Assignment / Over-posting
# ──────────────────────────────────────────────────────────────────────
@app.route("/update_profile", methods=["POST"])
def update_profile():
    conn = sqlite3.connect("app.db")
    data = request.json
    # Blindly trusts every key the client sends, including "is_admin"
    sets = ", ".join(f"{k}='{v}'" for k, v in data.items())
    conn.execute(f"UPDATE users SET {sets} WHERE username='{session['user']}'")
    conn.commit()
    conn.close()
    return "Updated"


# ──────────────────────────────────────────────────────────────────────
# 14. Weak Regex — ReDoS
# ──────────────────────────────────────────────────────────────────────
@app.route("/validate_email")
def validate_email():
    email = request.args.get("email", "")
    pattern = r"^([a-zA-Z0-9_.+-]+)*@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return "Valid"
    return "Invalid"


# ──────────────────────────────────────────────────────────────────────
# 15. CORS misconfiguration — wildcard with credentials
# ──────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ──────────────────────────────────────────────────────────────────────
# 16. Eval on user input
# ──────────────────────────────────────────────────────────────────────
@app.route("/calc")
def calc():
    expr = request.args.get("expr", "0")
    return str(eval(expr))


# ──────────────────────────────────────────────────────────────────────
# 17. Sensitive data in URL / GET parameters
# ──────────────────────────────────────────────────────────────────────
@app.route("/transfer")
def transfer():
    to_account = request.args.get("to")
    amount = request.args.get("amount")
    token = request.args.get("auth_token")
    # ... processes transfer using GET params (logged, cached, bookmarked)
    return f"Sent {amount} to {to_account}"


# ──────────────────────────────────────────────────────────────────────
# 18. Debug mode enabled
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
