import sqlite3
import bcrypt
import os
from datetime import datetime

DB_PATH = "database/interview_coach.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        overall_score REAL NOT NULL,
        total_questions INTEGER NOT NULL,
        weak_areas TEXT,
        strengths TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        topic TEXT,
        question TEXT NOT NULL,
        student_answer TEXT NOT NULL,
        correctness_score INTEGER,
        depth_score INTEGER,
        clarity_score INTEGER,
        overall_score INTEGER,
        missing_points TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)

    conn.commit()
    conn.close()

# ── Auth ──────────────────────────────────────────────────────

def signup_user(name: str, email: str, password: str) -> dict:
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                  (name, email, password_hash))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {"success": True, "user_id": user_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Email already registered"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(email: str, password: str) -> dict:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if not user:
            return {"success": False, "error": "Email not found"}

        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return {"success": True, "user_id": user["id"],
                    "name": user["name"], "email": user["email"]}
        else:
            return {"success": False, "error": "Incorrect password"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Sessions ──────────────────────────────────────────────────

def save_session(user_id: int, role: str, overall_score: float,
                 total_questions: int, weak_areas: list, strengths: list) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (user_id, role, overall_score, total_questions, weak_areas, strengths)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, role, overall_score, total_questions,
          ", ".join(weak_areas), ", ".join(strengths)))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id

def save_answer(session_id: int, topic: str, question: str, student_answer: str,
                correctness: int, depth: int, clarity: int, overall: int, missing_points: list):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO answers (session_id, topic, question, student_answer,
                             correctness_score, depth_score, clarity_score,
                             overall_score, missing_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, topic, question, student_answer,
          correctness, depth, clarity, overall, ", ".join(missing_points)))
    conn.commit()
    conn.close()

# ── History ───────────────────────────────────────────────────

def get_user_sessions(user_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM sessions WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    sessions = [dict(row) for row in c.fetchall()]
    conn.close()
    return sessions

def get_session_answers(session_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM answers WHERE session_id = ?", (session_id,))
    answers = [dict(row) for row in c.fetchall()]
    conn.close()
    return answers

def get_user_stats(user_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM sessions WHERE user_id = ?", (user_id,))
    total_sessions = c.fetchone()["total"]

    c.execute("SELECT AVG(overall_score) as avg FROM sessions WHERE user_id = ?", (user_id,))
    avg_score = c.fetchone()["avg"] or 0

    c.execute("""
        SELECT role, COUNT(*) as count FROM sessions
        WHERE user_id = ? GROUP BY role ORDER BY count DESC LIMIT 1
    """, (user_id,))
    fav = c.fetchone()
    favourite_role = fav["role"] if fav else "None"

    conn.close()
    return {
        "total_sessions": total_sessions,
        "avg_score": round(avg_score, 1),
        "favourite_role": favourite_role
    }