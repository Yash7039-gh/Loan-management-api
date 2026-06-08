from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
CORS(app)

# ──────────────────────────────────────────
# DATABASE CONNECTION
# ──────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "loandb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", 5432)
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            course VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS loans (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            amount NUMERIC(12,2) NOT NULL,
            interest_rate NUMERIC(5,2) NOT NULL DEFAULT 8.5,
            tenure_months INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','closed')),
            applied_at TIMESTAMP DEFAULT NOW(),
            approved_at TIMESTAMP,
            remarks TEXT
        );

        CREATE TABLE IF NOT EXISTS repayments (
            id SERIAL PRIMARY KEY,
            loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
            amount_paid NUMERIC(12,2) NOT NULL,
            paid_at TIMESTAMP DEFAULT NOW(),
            remarks TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ──────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────
def row_to_dict(cursor, rows):
    cols = [desc[0] for desc in cursor.description]
    if isinstance(rows, list):
        return [dict(zip(cols, r)) for r in rows]
    return dict(zip(cols, rows)) if rows else None

def serialize(obj):
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return obj

# ──────────────────────────────────────────
# ROOT
# ──────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "api": "Student Loan Management API",
        "version": "1.0.0",
        "author": "Yash Yadav",
        "endpoints": {
            "students": "/api/students",
            "loans": "/api/loans",
            "repayments": "/api/repayments",
            "dashboard": "/api/dashboard"
        }
    })

# ──────────────────────────────────────────
# STUDENTS
# ──────────────────────────────────────────
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY created_at DESC")
    students = serialize(row_to_dict(cur, cur.fetchall()))
    cur.close(); conn.close()
    return jsonify({"success": True, "count": len(students), "data": students})

@app.route("/api/students/<int:sid>", methods=["GET"])
def get_student(sid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = %s", (sid,))
    s = row_to_dict(cur, cur.fetchone())
    cur.close(); conn.close()
    if not s:
        return jsonify({"success": False, "message": "Student not found"}), 404
    return jsonify({"success": True, "data": serialize(s)})

@app.route("/api/students", methods=["POST"])
def create_student():
    data = request.get_json()
    required = ["name", "email", "course"]
    for f in required:
        if f not in data:
            return jsonify({"success": False, "message": f"'{f}' is required"}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO students (name, email, course) VALUES (%s, %s, %s) RETURNING *",
            (data["name"], data["email"], data["course"])
        )
        student = serialize(row_to_dict(cur, cur.fetchone()))
        conn.commit()
        return jsonify({"success": True, "message": "Student created", "data": student}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"success": False, "message": "Email already exists"}), 409
    finally:
        cur.close(); conn.close()

@app.route("/api/students/<int:sid>", methods=["PUT"])
def update_student(sid):
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE students SET name=%s, email=%s, course=%s WHERE id=%s RETURNING *",
        (data.get("name"), data.get("email"), data.get("course"), sid)
    )
    updated = row_to_dict(cur, cur.fetchone())
    conn.commit(); cur.close(); conn.close()
    if not updated:
        return jsonify({"success": False, "message": "Student not found"}), 404
    return jsonify({"success": True, "message": "Student updated", "data": serialize(updated)})

@app.route("/api/students/<int:sid>", methods=["DELETE"])
def delete_student(sid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=%s RETURNING id", (sid,))
    deleted = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    if not deleted:
        return jsonify({"success": False, "message": "Student not found"}), 404
    return jsonify({"success": True, "message": f"Student {sid} deleted"})

# ──────────────────────────────────────────
# LOANS
# ──────────────────────────────────────────
@app.route("/api/loans", methods=["GET"])
def get_loans():
    status = request.args.get("status")
    conn = get_db()
    cur = conn.cursor()
    if status:
        cur.execute("""
            SELECT l.*, s.name as student_name, s.email, s.course
            FROM loans l JOIN students s ON l.student_id = s.id
            WHERE l.status = %s ORDER BY l.applied_at DESC
        """, (status,))
    else:
        cur.execute("""
            SELECT l.*, s.name as student_name, s.email, s.course
            FROM loans l JOIN students s ON l.student_id = s.id
            ORDER BY l.applied_at DESC
        """)
    loans = serialize(row_to_dict(cur, cur.fetchall()))
    cur.close(); conn.close()
    return jsonify({"success": True, "count": len(loans), "data": loans})

@app.route("/api/loans/<int:lid>", methods=["GET"])
def get_loan(lid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.*, s.name as student_name, s.email, s.course
        FROM loans l JOIN students s ON l.student_id = s.id
        WHERE l.id = %s
    """, (lid,))
    loan = row_to_dict(cur, cur.fetchone())
    cur.close(); conn.close()
    if not loan:
        return jsonify({"success": False, "message": "Loan not found"}), 404
    return jsonify({"success": True, "data": serialize(loan)})

@app.route("/api/loans", methods=["POST"])
def apply_loan():
    data = request.get_json()
    required = ["student_id", "amount", "tenure_months"]
    for f in required:
        if f not in data:
            return jsonify({"success": False, "message": f"'{f}' is required"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE id=%s", (data["student_id"],))
    if not cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "Student not found"}), 404
    cur.execute("""
        INSERT INTO loans (student_id, amount, interest_rate, tenure_months, remarks)
        VALUES (%s, %s, %s, %s, %s) RETURNING *
    """, (
        data["student_id"], data["amount"],
        data.get("interest_rate", 8.5),
        data["tenure_months"],
        data.get("remarks", "")
    ))
    loan = serialize(row_to_dict(cur, cur.fetchone()))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "message": "Loan application submitted", "data": loan}), 201

@app.route("/api/loans/<int:lid>/status", methods=["PATCH"])
def update_loan_status(lid):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ["approved", "rejected", "closed"]:
        return jsonify({"success": False, "message": "Invalid status"}), 400
    conn = get_db()
    cur = conn.cursor()
    approved_at = datetime.now() if new_status == "approved" else None
    cur.execute("""
        UPDATE loans SET status=%s, approved_at=%s, remarks=%s
        WHERE id=%s RETURNING *
    """, (new_status, approved_at, data.get("remarks", ""), lid))
    loan = row_to_dict(cur, cur.fetchone())
    conn.commit(); cur.close(); conn.close()
    if not loan:
        return jsonify({"success": False, "message": "Loan not found"}), 404
    return jsonify({"success": True, "message": f"Loan {new_status}", "data": serialize(loan)})

# ──────────────────────────────────────────
# REPAYMENTS
# ──────────────────────────────────────────
@app.route("/api/repayments", methods=["POST"])
def add_repayment():
    data = request.get_json()
    if "loan_id" not in data or "amount_paid" not in data:
        return jsonify({"success": False, "message": "'loan_id' and 'amount_paid' are required"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM loans WHERE id=%s", (data["loan_id"],))
    loan = cur.fetchone()
    if not loan:
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "Loan not found"}), 404
    if loan[0] != "approved":
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "Repayment only allowed for approved loans"}), 400
    cur.execute("""
        INSERT INTO repayments (loan_id, amount_paid, remarks)
        VALUES (%s, %s, %s) RETURNING *
    """, (data["loan_id"], data["amount_paid"], data.get("remarks", "")))
    repayment = serialize(row_to_dict(cur, cur.fetchone()))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "message": "Repayment recorded", "data": repayment}), 201

@app.route("/api/repayments/loan/<int:lid>", methods=["GET"])
def get_repayments(lid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM repayments WHERE loan_id=%s ORDER BY paid_at DESC", (lid,))
    repayments = serialize(row_to_dict(cur, cur.fetchall()))
    cur.execute("SELECT SUM(amount_paid) FROM repayments WHERE loan_id=%s", (lid,))
    total = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    return jsonify({"success": True, "total_paid": float(total), "data": repayments})

# ──────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM loans")
    total_loans = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM loans WHERE status='approved'")
    approved = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM loans WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM loans WHERE status='rejected'")
    rejected = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM loans WHERE status='approved'")
    total_disbursed = float(cur.fetchone()[0])
    cur.execute("SELECT COALESCE(SUM(amount_paid),0) FROM repayments")
    total_repaid = float(cur.fetchone()[0])
    cur.close(); conn.close()
    return jsonify({
        "success": True,
        "data": {
            "total_students": total_students,
            "total_loans": total_loans,
            "approved_loans": approved,
            "pending_loans": pending,
            "rejected_loans": rejected,
            "total_disbursed": total_disbursed,
            "total_repaid": total_repaid,
            "outstanding": round(total_disbursed - total_repaid, 2)
        }
    })

# ──────────────────────────────────────────
# RUN
# ──────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
