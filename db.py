"""
Слой работы с базой данных SQLite (без ORM).
Хранит игроков/команды, прогресс по этапам, журнал попыток и подсказок,
а также ответы на страницу рефлексии.
"""
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "quest.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL CHECK(mode IN ('solo', 'team')),
    display_name TEXT NOT NULL,
    team_members TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stage_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    stage_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    started_at TEXT,
    completed_at TEXT,
    attempts_count INTEGER NOT NULL DEFAULT 0,
    wrong_attempts_count INTEGER NOT NULL DEFAULT 0,
    consecutive_wrong INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    max_hint_level INTEGER NOT NULL DEFAULT 0,
    score INTEGER,
    UNIQUE(player_id, stage_number)
);

CREATE TABLE IF NOT EXISTS attempts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    stage_number INTEGER NOT NULL,
    submitted_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hints_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    stage_number INTEGER NOT NULL,
    hint_level INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reflection_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    row_key TEXT NOT NULL,
    field_key TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(player_id, row_key, field_key)
);
"""


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def reset_all_progress():
    """Полный сброс прогресса: удаляет игроков и все связанные записи."""
    conn = get_connection()
    conn.executescript(
        """
        DELETE FROM reflection_answers;
        DELETE FROM hints_log;
        DELETE FROM attempts_log;
        DELETE FROM stage_progress;
        DELETE FROM players;
        """
    )
    conn.commit()
    conn.close()


# ---------- Игроки ----------

def create_player(mode, display_name, team_members=None):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO players (mode, display_name, team_members, created_at) VALUES (?, ?, ?, ?)",
        (mode, display_name, team_members, now_iso()),
    )
    conn.commit()
    player_id = cur.lastrowid
    conn.close()
    return player_id


def get_player(player_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    conn.close()
    return row


def all_players():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM players ORDER BY created_at").fetchall()
    conn.close()
    return rows


# ---------- Прогресс по этапам ----------

def get_progress(player_id, stage_number):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stage_progress WHERE player_id = ? AND stage_number = ?",
        (player_id, stage_number),
    ).fetchone()
    conn.close()
    return row


def get_all_progress(player_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM stage_progress WHERE player_id = ? ORDER BY stage_number",
        (player_id,),
    ).fetchall()
    conn.close()
    return {row["stage_number"]: row for row in rows}


def ensure_progress_started(player_id, stage_number):
    """Создаёт запись о прогрессе при первом открытии этапа (фиксирует время начала)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stage_progress WHERE player_id = ? AND stage_number = ?",
        (player_id, stage_number),
    ).fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO stage_progress
               (player_id, stage_number, status, started_at, attempts_count,
                wrong_attempts_count, consecutive_wrong, max_hint_level)
               VALUES (?, ?, 'in_progress', ?, 0, 0, 0, 0)""",
            (player_id, stage_number, now_iso()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM stage_progress WHERE player_id = ? AND stage_number = ?",
            (player_id, stage_number),
        ).fetchone()
    conn.close()
    return row


def is_locked(progress_row):
    if not progress_row or not progress_row["locked_until"]:
        return False, 0
    locked_until = datetime.fromisoformat(progress_row["locked_until"])
    remaining = (locked_until - datetime.utcnow()).total_seconds()
    if remaining > 0:
        return True, int(remaining) + 1
    return False, 0


def record_attempt(player_id, stage_number, submitted_answer, is_correct,
                    max_consecutive_wrong, lockout_seconds):
    """
    Записывает попытку в журнал, обновляет счётчики прогресса.
    При достижении max_consecutive_wrong неверных попыток подряд — включает блокировку.
    Возвращает (progress_row, locked: bool, lock_seconds: int).
    """
    conn = get_connection()
    conn.execute(
        """INSERT INTO attempts_log (player_id, stage_number, submitted_answer, is_correct, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (player_id, stage_number, submitted_answer, int(is_correct), now_iso()),
    )

    row = conn.execute(
        "SELECT * FROM stage_progress WHERE player_id = ? AND stage_number = ?",
        (player_id, stage_number),
    ).fetchone()

    attempts_count = row["attempts_count"] + 1
    wrong_attempts_count = row["wrong_attempts_count"] + (0 if is_correct else 1)
    consecutive_wrong = 0 if is_correct else row["consecutive_wrong"] + 1

    locked = False
    lock_seconds = 0
    locked_until = row["locked_until"]
    if consecutive_wrong >= max_consecutive_wrong:
        locked = True
        lock_seconds = lockout_seconds
        locked_until = (datetime.utcnow() + timedelta(seconds=lockout_seconds)).isoformat(timespec="seconds")
        consecutive_wrong = 0

    status = row["status"]
    completed_at = row["completed_at"]
    score = row["score"]
    if is_correct:
        status = "completed"
        completed_at = now_iso()

    conn.execute(
        """UPDATE stage_progress SET
               attempts_count = ?, wrong_attempts_count = ?, consecutive_wrong = ?,
               locked_until = ?, status = ?, completed_at = ?
           WHERE player_id = ? AND stage_number = ?""",
        (attempts_count, wrong_attempts_count, consecutive_wrong, locked_until,
         status, completed_at, player_id, stage_number),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM stage_progress WHERE player_id = ? AND stage_number = ?",
        (player_id, stage_number),
    ).fetchone()
    conn.close()
    return row, locked, lock_seconds


def set_score(player_id, stage_number, score):
    conn = get_connection()
    conn.execute(
        "UPDATE stage_progress SET score = ? WHERE player_id = ? AND stage_number = ?",
        (score, player_id, stage_number),
    )
    conn.commit()
    conn.close()


def record_hint(player_id, stage_number, hint_level):
    """Фиксирует открытие подсказки указанного уровня и обновляет максимальный уровень."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO hints_log (player_id, stage_number, hint_level, created_at) VALUES (?, ?, ?, ?)",
        (player_id, stage_number, hint_level, now_iso()),
    )
    conn.execute(
        """UPDATE stage_progress SET max_hint_level = MAX(max_hint_level, ?)
           WHERE player_id = ? AND stage_number = ?""",
        (hint_level, player_id, stage_number),
    )
    conn.commit()
    conn.close()


# ---------- Рефлексия ----------

def save_reflection_answer(player_id, row_key, field_key, answer_text):
    conn = get_connection()
    conn.execute(
        """INSERT INTO reflection_answers (player_id, row_key, field_key, answer_text, updated_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(player_id, row_key, field_key)
           DO UPDATE SET answer_text = excluded.answer_text, updated_at = excluded.updated_at""",
        (player_id, row_key, field_key, answer_text, now_iso()),
    )
    conn.commit()
    conn.close()


def get_reflection_answers(player_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT row_key, field_key, answer_text FROM reflection_answers WHERE player_id = ?",
        (player_id,),
    ).fetchall()
    conn.close()
    result = {}
    for row in rows:
        result.setdefault(row["row_key"], {})[row["field_key"]] = row["answer_text"]
    return result


# ---------- Статистика для учителя ----------

def get_stats():
    """Возвращает сводную статистику по всем игрокам для панели учителя и экспорта CSV."""
    conn = get_connection()
    players = conn.execute("SELECT * FROM players ORDER BY created_at").fetchall()
    stats = []
    for player in players:
        progress_rows = conn.execute(
            "SELECT * FROM stage_progress WHERE player_id = ? ORDER BY stage_number",
            (player["id"],),
        ).fetchall()
        progress_by_stage = {row["stage_number"]: row for row in progress_rows}
        total_score = sum((row["score"] or 0) for row in progress_rows)
        completed_stages = sum(1 for row in progress_rows if row["status"] == "completed")
        stats.append({
            "player": player,
            "progress": progress_by_stage,
            "total_score": total_score,
            "completed_stages": completed_stages,
        })
    conn.close()
    return stats
