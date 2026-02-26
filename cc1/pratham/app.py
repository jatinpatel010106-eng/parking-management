from datetime import datetime, timezone
from math import ceil

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.sqlite_config import get_connection

app = Flask(__name__)
app.secret_key = "replace_this_with_a_secure_secret_key"

PARKING_RATES = {
    "Car": 50,
    "Bike": 20,
    "Truck": 80,
}


# ---------- Utility helpers ----------
def calculate_fee(vehicle_type: str, entry_time: datetime, exit_time: datetime):
    duration_seconds = max((exit_time - entry_time).total_seconds(), 0)
    hours = max(1, ceil(duration_seconds / 3600))
    rate = PARKING_RATES.get(vehicle_type, 30)
    return hours, float(hours * rate)


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def login_required():
    if "user_id" not in session:
        return jsonify({"error": "Please login first."}), 401
    return None


# ---------- Page routes ----------
@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful.",
        "role": user["role"],
        "redirect": url_for("dashboard"),
    })


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already registered."}), 409

    conn.execute(
        "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, email, generate_password_hash(password), "user", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Registration successful. Please login."}), 201


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session.get("username", "User"),
        role=session.get("role", "user"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home_page"))


# ---------- Parking API routes ----------
@app.route("/add_vehicle", methods=["POST"])
def add_vehicle():
    auth_error = login_required()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or request.form
    owner_name = (data.get("owner_name") or "").strip()
    vehicle_number = (data.get("vehicle_number") or "").strip().upper()
    vehicle_type = (data.get("vehicle_type") or "").strip().title()

    if not owner_name or not vehicle_number or vehicle_type not in PARKING_RATES:
        return jsonify({"error": "Provide valid owner name, number, and type."}), 400

    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM vehicles WHERE vehicle_number = ? AND status = 'parked'",
        (vehicle_number,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Vehicle is already parked."}), 409

    entry_time = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO vehicles (vehicle_number, owner_name, vehicle_type, entry_time, status, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        (vehicle_number, owner_name, vehicle_type, entry_time, "parked", session.get("username")),
    )
    conn.commit()
    vehicle_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Vehicle entry added.",
        "vehicle_id": vehicle_id,
        "entry_time": entry_time,
    }), 201


@app.route("/exit_vehicle", methods=["POST"])
def exit_vehicle():
    auth_error = login_required()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or request.form
    vehicle_number = (data.get("vehicle_number") or "").strip().upper()

    if not vehicle_number:
        return jsonify({"error": "Vehicle number is required."}), 400

    conn = get_connection()
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_number = ? AND status = 'parked'",
        (vehicle_number,)
    ).fetchone()

    if not vehicle:
        conn.close()
        return jsonify({"error": "No parked vehicle found with this number."}), 404

    entry_time = datetime.fromisoformat(vehicle["entry_time"])
    exit_time = datetime.now(timezone.utc)

    # Make entry_time timezone-aware if it isn't
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)

    duration_hours, fee = calculate_fee(vehicle["vehicle_type"], entry_time, exit_time)

    conn.execute(
        "UPDATE vehicles SET status = 'exited', exit_time = ?, duration_hours = ?, total_fee = ? WHERE id = ?",
        (exit_time.isoformat(), duration_hours, fee, vehicle["id"]),
    )

    conn.execute(
        """INSERT INTO parking_history 
        (vehicle_number, owner_name, vehicle_type, entry_time, exit_time, duration_hours, total_fee, processed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (vehicle_number, vehicle["owner_name"], vehicle["vehicle_type"],
         vehicle["entry_time"], exit_time.isoformat(), duration_hours, fee, session.get("username")),
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Vehicle exited successfully.",
        "duration_hours": duration_hours,
        "total_fee": fee,
    })


@app.route("/vehicles", methods=["GET"])
def list_vehicles():
    auth_error = login_required()
    if auth_error:
        return auth_error

    query_number = (request.args.get("number") or "").strip().upper()
    conn = get_connection()

    if query_number:
        vehicles = conn.execute(
            "SELECT * FROM vehicles WHERE status = 'parked' AND vehicle_number LIKE ? ORDER BY entry_time ASC",
            (f"%{query_number}%",)
        ).fetchall()
    else:
        vehicles = conn.execute(
            "SELECT * FROM vehicles WHERE status = 'parked' ORDER BY entry_time ASC"
        ).fetchall()

    conn.close()

    response = [{
        "id": v["id"],
        "vehicle_number": v["vehicle_number"],
        "owner_name": v["owner_name"],
        "vehicle_type": v["vehicle_type"],
        "entry_time": v["entry_time"],
        "status": v["status"],
    } for v in vehicles]

    return jsonify(response)


@app.route("/vehicles/<int:vehicle_id>", methods=["DELETE"])
def delete_vehicle(vehicle_id):
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_connection()
    result = conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return jsonify({"error": "Vehicle record not found."}), 404

    return jsonify({"message": "Vehicle record deleted."})


# ---------- Admin API routes ----------
@app.route("/admin/users", methods=["GET"])
def admin_users():
    auth_error = login_required()
    if auth_error:
        return auth_error

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access only."}), 403

    conn = get_connection()
    users = conn.execute("SELECT id, username, email, role FROM users ORDER BY created_at DESC").fetchall()
    conn.close()

    return jsonify([{
        "id": u["id"],
        "username": u["username"],
        "email": u["email"],
        "role": u["role"],
    } for u in users])


@app.route("/admin/history", methods=["GET"])
def admin_history():
    auth_error = login_required()
    if auth_error:
        return auth_error

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access only."}), 403

    conn = get_connection()
    history = conn.execute("SELECT * FROM parking_history ORDER BY exit_time DESC").fetchall()
    conn.close()

    total_earnings = 0.0
    formatted_history = []

    for item in history:
        total_earnings += float(item["total_fee"] or 0)
        formatted_history.append({
            "id": item["id"],
            "vehicle_number": item["vehicle_number"],
            "owner_name": item["owner_name"],
            "vehicle_type": item["vehicle_type"],
            "entry_time": item["entry_time"],
            "exit_time": item["exit_time"],
            "duration_hours": item["duration_hours"],
            "total_fee": item["total_fee"],
        })

    return jsonify({"total_earnings": round(total_earnings, 2), "history": formatted_history})


# ---------- Startup ----------
def bootstrap():
    """Ensure admin account exists on startup."""
    conn = get_connection()
    admin_email = "admin@parking.com"
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Admin", admin_email, generate_password_hash("admin123"), "admin", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    conn.close()


if __name__ == "__main__":
    bootstrap()
    app.run(debug=True)
    