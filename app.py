
from flask import Flask, request, jsonify, render_template, session, redirect
from functools import wraps
from flask_cors import CORS
import mysql.connector
from datetime import date, datetime
import os

# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    if os.environ.get("PORT"):
        raise RuntimeError("SECRET_KEY is not configured")
    app.secret_key = "local-development-only-change-this-key"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("PORT"))


# ============================================================
# DATABASE CONNECTION
# Local MySQL or hosted MySQL using environment variables
# ============================================================

def get_db_connection():
    host = os.environ.get("MYSQLHOST", "127.0.0.1")

    config = {
        "host": host,
        "user": os.environ.get("MYSQLUSER", "root"),
        "password": os.environ.get("MYSQLPASSWORD"),
        "database": os.environ.get("MYSQLDATABASE", "feedback_system"),
        "port": int(os.environ.get("MYSQLPORT", "3306")),
        "connection_timeout": 10,
        "ssl_disabled": host in ("127.0.0.1", "localhost")
    }

    ssl_ca = os.environ.get("MYSQLSSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True

    return mysql.connector.connect(**config)


# ============================================================
# JSON DATE CONVERSION
# ============================================================

def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


# ============================================================
# ACCESS CONTROL
# ============================================================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper


def admin_api_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({
                "status": "error",
                "message": "Admin login required"
            }), 401
        return f(*args, **kwargs)
    return wrapper


def staff_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("staff_logged_in"):
            return redirect("/staff-login")
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# WEB PAGE ROUTES
# ============================================================

@app.route("/")
@app.route("/index.html")
def home():
    return render_template("index.html")


@app.route("/admin")
@app.route("/admin.html")
def admin_page():
    return render_template("admin.html")


@app.route("/staff-login")
def staff_login_page():
    return render_template("staff-login.html")


@app.route("/attendance.html")
def attendance_page():
    return render_template("attendance.html")


@app.route("/clg.html")
def clg_page():
    return render_template("clg.html")


@app.route("/clgdetails.html")
def clg_details_page():
    return render_template("clgdetails.html")


@app.route("/dashboard.html")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/feedback.html")
def feedback_page():
    return render_template("feedback.html")


@app.route("/final.html")
def final_page():
    return render_template("final.html")


@app.route("/parent.html")
def parent_page():
    return render_template("parent.html")


@app.route("/parent-dashboard.html")
def parent_dashboard_page():
    return render_template("parent-dashboard.html")


@app.route("/student.html")
def student_page():
    return render_template("student.html")


@app.route("/student-dashboard.html")
def student_dashboard_page():
    return render_template("student-dashboard.html")


@app.route("/student-profile.html")
def student_profile_page():
    return render_template("student-profile.html")


@app.route("/notices.html")
def notices_page():
    return render_template("notices.html")


@app.route("/staff-dashboard.html")
@staff_required
def staff_dashboard_page():
    return render_template("staff-dashboard.html")


@app.route("/admin-dashboard.html")
@admin_required
def admin_dashboard_page():
    return render_template("admin-dashboard.html")


@app.route("/admin-feedback.html")
@admin_required
def admin_feedback_page():
    return render_template("admin-feedback.html")


@app.route("/admin-notices.html")
@admin_required
def admin_notices_page():
    return render_template("admin-notices.html")


# ============================================================
# LOGIN HISTORY API
# ============================================================

@app.route("/api/login", methods=["POST"])
def save_login():
    data = request.get_json(silent=True) or {}

    user_id = data.get("userId")
    user_type = data.get("userType", "unknown")
    branch = data.get("branch")

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "User ID required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback_history
                (user_id, user_type, branch)
            VALUES (%s, %s, %s)
        """, (user_id, user_type, branch))

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Login recorded successfully"
        }), 200

    except Exception:
        app.logger.exception("Login history insert failed")
        return jsonify({
            "status": "error",
            "message": "Could not record login"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "Username and password are required"
        }), 400

    expected_username = os.environ.get("ADMIN_USERNAME")
    expected_password = os.environ.get("ADMIN_PASSWORD")

    if not expected_username or not expected_password:
        return jsonify({
            "status": "error",
            "message": "Admin credentials are not configured"
        }), 500

    if username != expected_username or password != expected_password:
        return jsonify({
            "status": "error",
            "message": "Invalid admin username or password"
        }), 401

    session.clear()
    session["admin_logged_in"] = True
    session["admin_username"] = username

    return jsonify({
        "status": "success",
        "message": "Admin login successful",
        "redirect": "/admin-dashboard.html"
    }), 200


# ============================================================
# STAFF / HOD / HOSTEL ADMIN LOGIN
# ============================================================


@app.route("/api/staff-login", methods=["POST"])
def staff_login():
    data = request.get_json(silent=True) or {}

    user_id = (data.get("user_id") or "").strip()
    password = data.get("password") or ""

    if not user_id or not password:
        return jsonify({
            "status": "error",
            "message": "User ID and password are required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()

        # Buffered cursor reads the query results before cleanup.
        cursor = conn.cursor(dictionary=True, buffered=True)

        cursor.execute("""
            SELECT user_id, password, branch, user_type
            FROM users
            WHERE user_id = %s
              AND user_type IN ('hod', 'hostel_admin')
        """, (user_id,))

        user = cursor.fetchone()

        if not user or user["password"] != password:
            return jsonify({
                "status": "error",
                "message": "Invalid user ID or password"
            }), 401

        role = user["user_type"]
        branch = user["branch"]

        if role == "hod" and branch not in (
            "CME", "ECE", "CCP", "DPH"
        ):
            return jsonify({
                "status": "error",
                "message": "Invalid department assignment"
            }), 403

        if role == "hostel_admin" and branch != "HOSTEL":
            return jsonify({
                "status": "error",
                "message": "Invalid Hostel Admin assignment"
            }), 403

        session.clear()
        session["staff_logged_in"] = True
        session["staff_user_id"] = user["user_id"]
        session["staff_role"] = role
        session["staff_branch"] = branch

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "redirect": "/staff-dashboard.html"
        }), 200

    except Exception:
        app.logger.exception("Staff login failed")
        return jsonify({
            "status": "error",
            "message": "Unable to complete staff login"
        }), 500

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                app.logger.exception("Could not close staff login cursor")

        if conn is not None:
            try:
                conn.close()
            except Exception:
                app.logger.exception("Could not close staff login connection")


# ============================================================
# STAFF INFORMATION API
# ============================================================

@app.route("/api/staff-info", methods=["GET"])
@staff_required
def get_staff_info():
    return jsonify({
        "status": "success",
        "user_id": session.get("staff_user_id"),
        "role": session.get("staff_role"),
        "branch": session.get("staff_branch")
    }), 200


# ============================================================
# SUBMIT STUDENT / PARENT FEEDBACK
# This route must exist only once.
# ============================================================

@app.route("/api/submit-feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}

    feedback_for = data.get("feedbackFor")
    category = data.get("category")
    message = (data.get("message") or "").strip()
    user_type = data.get("userType", "Student")
    rating = data.get("rating")
    user_id = data.get("userId") or "Student"
    branch = (data.get("branch") or "").strip().upper()

    if feedback_for not in ("College", "Hostel"):
        return jsonify({
            "status": "error",
            "message": "Please select College or Hostel."
        }), 400

    if not isinstance(category, str) or not category.strip():
        return jsonify({
            "status": "error",
            "message": "Please select a feedback category."
        }), 400

    if not message:
        return jsonify({
            "status": "error",
            "message": "Please enter your feedback."
        }), 400

    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Rating must be between 1 and 5."
        }), 400

    if user_type not in ("Student", "Parent"):
        return jsonify({
            "status": "error",
            "message": "Invalid user type."
        }), 400

    if feedback_for == "Hostel":
        branch = "HOSTEL"
    elif branch not in ("CME", "ECE", "CCP", "DPH"):
        return jsonify({
            "status": "error",
            "message": "Department is missing or invalid. Please log in again."
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback
                (name, message, created_at, user_type,
                 category, rating, branch)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (
            user_id,
            message,
            user_type,
            category.strip(),
            rating,
            branch
        ))

        feedback_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Feedback saved successfully.",
            "id": feedback_id
        }), 201

    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("Feedback insert failed")
        return jsonify({
            "status": "error",
            "message": "Could not save feedback. Please check the database schema."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# ADMIN FEEDBACK API
# ============================================================

@app.route("/api/admin-feedback", methods=["GET"])
@admin_api_required
def get_admin_feedback():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, message, created_at,
                   user_type, category, rating, phone,
                   roll_number, is_anonymous, branch
            FROM feedback
            ORDER BY created_at DESC, id DESC
        """)

        feedback_list = json_safe(cursor.fetchall())

        return jsonify({
            "status": "success",
            "feedback": feedback_list
        }), 200

    except Exception:
        app.logger.exception("Admin feedback retrieval failed")
        return jsonify({
            "status": "error",
            "message": "Could not retrieve feedback"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# STAFF FEEDBACK API
# HODs only see their department.
# Hostel Admin only sees HOSTEL feedback.
# ============================================================

@app.route("/api/staff-feedback", methods=["GET"])
@staff_required
def get_staff_feedback():
    role = session.get("staff_role")
    branch = session.get("staff_branch")

    if role == "hod" and branch in ("CME", "ECE", "CCP", "DPH"):
        params = (branch,)
    elif role == "hostel_admin" and branch == "HOSTEL":
        params = ("HOSTEL",)
    else:
        return jsonify({
            "status": "error",
            "message": "You are not authorized to view this feedback."
        }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, category, rating, message, created_at
            FROM feedback
            WHERE branch = %s
            ORDER BY created_at DESC, id DESC
        """, params)

        feedback_list = json_safe(cursor.fetchall())

        return jsonify({
            "status": "success",
            "feedback": feedback_list
        }), 200

    except Exception:
        app.logger.exception("Staff feedback retrieval failed")
        return jsonify({
            "status": "error",
            "message": "Unable to load feedback"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# PUBLIC NOTICES API
# ============================================================

@app.route("/api/notices", methods=["GET"])
def get_notices():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, title, description, notice_date, created_at
            FROM college_notices
            ORDER BY notice_date DESC, id DESC
        """)

        notices = json_safe(cursor.fetchall())

        return jsonify({
            "status": "success",
            "notices": notices
        }), 200

    except Exception:
        app.logger.exception("Notice retrieval failed")
        return jsonify({
            "status": "error",
            "message": "Could not retrieve notices"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# ADD NOTICE - ADMIN ONLY
# ============================================================

@app.route("/api/notices", methods=["POST"])
@admin_api_required
def add_notice():
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    notice_date = data.get("date")

    if not title or not description or not notice_date:
        return jsonify({
            "status": "error",
            "message": "Title, description and date are required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO college_notices
                (title, description, notice_date)
            VALUES (%s, %s, %s)
        """, (title, description, notice_date))

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Notice added successfully"
        }), 201

    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("Notice insert failed")
        return jsonify({
            "status": "error",
            "message": "Could not add notice"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# DELETE NOTICE - ADMIN ONLY
# ============================================================

@app.route("/api/notices/<int:notice_id>", methods=["DELETE"])
@admin_api_required
def delete_notice(notice_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM college_notices WHERE id = %s",
            (notice_id,)
        )

        deleted = cursor.rowcount
        conn.commit()

        if deleted == 0:
            return jsonify({
                "status": "error",
                "message": "Notice not found"
            }), 404

        return jsonify({
            "status": "success",
            "message": "Notice deleted successfully"
        }), 200

    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("Notice deletion failed")
        return jsonify({
            "status": "error",
            "message": "Could not delete notice"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# LOGOUT ROUTES
# ============================================================

@app.route("/staff-logout")
def staff_logout():
    session.clear()
    return redirect("/staff-login")


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect("/admin")


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
