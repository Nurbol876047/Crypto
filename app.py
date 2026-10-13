"""
Криптографиялық Escape Room — «Байқоңыр бункері: ұшыру коды».
Основной файл Flask-приложения: маршруты для игроков и панели учителя.
"""
import csv
import io
import json
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, Response, abort
)

import db
import quest_config
from crypto import caesar, vigenere, columnar, playfair, rsa_utils
from crypto.alphabets import get_alphabet

app = Flask(__name__)
app.secret_key = "baikonur-escape-room-dev-secret-2026"

db.init_db()

CIPHER_VALIDATORS = {
    "caesar": caesar.validate_key,
    "vigenere": vigenere.validate_key,
    "columnar": columnar.validate_key,
    "playfair": playfair.validate_key,
    "rsa": rsa_utils.validate_key,
}


# ---------- Вспомогательные функции ----------

def compute_score(scoring_cfg, max_hint_level, wrong_attempts_count):
    score = (
        scoring_cfg["max_score"]
        - scoring_cfg["hint_penalty"] * max_hint_level
        - scoring_cfg["attempt_penalty"] * (wrong_attempts_count // scoring_cfg["attempt_penalty_every"])
    )
    return max(scoring_cfg["min_score_if_completed"], score)


def player_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        player_id = session.get("player_id")
        # Сессия может указывать на игрока, которого больше нет в базе
        # (например, учитель нажал "Сброс прогресса") — тогда тихо выходим вместо падения.
        if not player_id or db.get_player(player_id) is None:
            session.pop("player_id", None)
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapper


def teacher_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("teacher_authenticated"):
            return redirect(url_for("teacher_login"))
        return view(*args, **kwargs)
    return wrapper


def current_player():
    return db.get_player(session["player_id"])


# ---------- Игровые маршруты ----------

@app.route("/")
def index():
    if session.get("player_id"):
        return redirect(url_for("bunker"))
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    mode = request.form.get("mode")
    if mode == "solo":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Атыңызды енгізіңіз.")
            return redirect(url_for("index"))
        player_id = db.create_player("solo", name)
    elif mode == "team":
        team_name = (request.form.get("team_name") or "").strip()
        members = [
            (request.form.get(f"member{i}") or "").strip()
            for i in range(1, 5)
        ]
        members = [m for m in members if m]
        if not team_name or len(members) < 2:
            flash("Топ атауы және кемінде 2 қатысушы аты қажет.")
            return redirect(url_for("index"))
        player_id = db.create_player("team", team_name, json.dumps(members, ensure_ascii=False))
    else:
        flash("Режимді таңдаңыз.")
        return redirect(url_for("index"))

    session.clear()
    session["player_id"] = player_id
    return redirect(url_for("bunker"))


@app.route("/logout")
def logout():
    session.pop("player_id", None)
    return redirect(url_for("index"))


@app.route("/bunker")
@player_required
def bunker():
    player_id = session["player_id"]
    config = quest_config.load_config()
    progress = db.get_all_progress(player_id)

    stages = []
    for n in range(1, quest_config.STAGE_COUNT + 1):
        stage_cfg = quest_config.get_stage_config(config, n)
        row = progress.get(n)
        status = row["status"] if row else "not_started"
        stages.append({
            "number": n,
            "title": stage_cfg["title"],
            "subtitle": stage_cfg["subtitle"],
            "status": status,
            "locked": False,
            "fragment": quest_config.get_code_fragment(config, n) if status == "completed" else None,
            "score": row["score"] if row and row["score"] is not None else None,
        })

    all_completed = all(s["status"] == "completed" for s in stages)
    started_timestamps = [row["started_at"] for row in progress.values() if row["started_at"]]
    started_at = min(started_timestamps) if started_timestamps else None

    return render_template(
        "bunker.html",
        player=current_player(),
        stages=stages,
        all_completed=all_completed,
        started_at=started_at,
    )


@app.route("/stage/<int:n>")
@player_required
def stage(n):
    if not (1 <= n <= quest_config.STAGE_COUNT):
        abort(404)
    player_id = session["player_id"]

    row = db.ensure_progress_started(player_id, n)
    locked, lock_seconds = db.is_locked(row)

    config = quest_config.load_config()
    view = quest_config.build_stage_view(config, n)
    opened_hints = view["hints"][: row["max_hint_level"]]

    return render_template(
        "stage.html",
        stage=view,
        progress=row,
        locked=locked,
        lock_seconds=lock_seconds,
        opened_hints=opened_hints,
        total_hints=len(view["hints"]),
        solved=row["status"] == "completed",
        fragment=quest_config.get_code_fragment(config, n) if row["status"] == "completed" else None,
    )


@app.route("/api/stage/<int:n>/submit", methods=["POST"])
@player_required
def submit_answer(n):
    if not (1 <= n <= quest_config.STAGE_COUNT):
        abort(404)
    player_id = session["player_id"]
    data = request.get_json(silent=True) or {}
    answer = data.get("answer", "")

    row = db.ensure_progress_started(player_id, n)
    locked, lock_seconds = db.is_locked(row)
    if locked:
        return jsonify(correct=False, locked=True, lock_seconds=lock_seconds), 423

    config = quest_config.load_config()
    correct = quest_config.check_answer(config, n, answer)
    lockout_cfg = config["lockout"]

    row, locked_after, lock_seconds_after = db.record_attempt(
        player_id, n, answer, correct,
        lockout_cfg["max_consecutive_wrong"], lockout_cfg["lockout_seconds"],
    )

    if correct:
        score = compute_score(config["scoring"], row["max_hint_level"], row["wrong_attempts_count"])
        db.set_score(player_id, n, score)
        fragment = quest_config.get_code_fragment(config, n)
        return jsonify(
            correct=True,
            score=score,
            fragment=fragment,
            finished=(n == quest_config.STAGE_COUNT),
            next_url=url_for("bunker"),
            attempts=row["attempts_count"],
        )

    remaining = max(0, lockout_cfg["max_consecutive_wrong"] - row["consecutive_wrong"])
    return jsonify(
        correct=False,
        locked=locked_after,
        lock_seconds=lock_seconds_after,
        attempts_before_lock=remaining,
        attempts=row["attempts_count"],
    )


@app.route("/api/stage/<int:n>/hint", methods=["POST"])
@player_required
def request_hint(n):
    if not (1 <= n <= quest_config.STAGE_COUNT):
        abort(404)
    player_id = session["player_id"]
    data = request.get_json(silent=True) or {}
    try:
        level = int(data.get("level"))
    except (TypeError, ValueError):
        return jsonify(error="Қате деңгей"), 400
    if level < 1 or level > 3:
        return jsonify(error="Деңгей 1-3 аралығында болуы керек"), 400

    config = quest_config.load_config()
    stage_cfg = quest_config.get_stage_config(config, n)
    row = db.ensure_progress_started(player_id, n)

    if level > row["max_hint_level"] + 1:
        return jsonify(error="Алдымен алдыңғы деңгейді ашыңыз"), 400
    if level > row["max_hint_level"]:
        db.record_hint(player_id, n, level)

    return jsonify(level=level, text=stage_cfg["hints"][level - 1])


@app.route("/api/stage/4/check-key", methods=["POST"])
@player_required
def check_playfair_key():
    data = request.get_json(silent=True) or {}
    submitted = (data.get("keyword") or "").strip()
    config = quest_config.load_config()
    stage_cfg = quest_config.get_stage_config(config, 4)
    real_keyword = stage_cfg["key"]["keyword"]
    if submitted.upper() != real_keyword.upper():
        return jsonify(ok=False)
    table = playfair.build_table(real_keyword)
    return jsonify(ok=True, table=table)


@app.route("/final")
@player_required
def final():
    player_id = session["player_id"]
    progress = db.get_all_progress(player_id)
    if not all(progress.get(n) and progress[n]["status"] == "completed" for n in range(1, quest_config.STAGE_COUNT + 1)):
        flash("Алдымен барлық бөлмелерді шешіңіз.")
        return redirect(url_for("bunker"))

    config = quest_config.load_config()
    final_code = quest_config.get_final_code(config)
    rows = []
    total_score = 0
    for n in range(1, quest_config.STAGE_COUNT + 1):
        row = progress[n]
        total_score += row["score"] or 0
        rows.append({
            "number": n,
            "title": quest_config.get_stage_config(config, n)["title"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "attempts": row["attempts_count"],
            "hints_used": row["max_hint_level"],
            "score": row["score"],
        })

    return render_template(
        "final.html",
        player=current_player(),
        final_code=final_code,
        rows=rows,
        total_score=total_score,
    )


@app.route("/reflection", methods=["GET", "POST"])
@player_required
def reflection():
    player_id = session["player_id"]
    progress = db.get_all_progress(player_id)
    if not all(progress.get(n) and progress[n]["status"] == "completed" for n in range(1, quest_config.STAGE_COUNT + 1)):
        flash("Рефлексия тек квестті толық аяқтағаннан кейін қолжетімді.")
        return redirect(url_for("bunker"))

    config = quest_config.load_config()

    if request.method == "POST":
        for row_cfg in config["reflection_rows"]:
            for field_cfg in config["reflection_fields"]:
                field_name = f"{row_cfg['row_key']}__{field_cfg['field_key']}"
                value = (request.form.get(field_name) or "").strip()
                if value:
                    db.save_reflection_answer(player_id, row_cfg["row_key"], field_cfg["field_key"], value)
        flash("Жауаптарыңыз сақталды.")
        return redirect(url_for("reflection"))

    answers = db.get_reflection_answers(player_id)
    return render_template(
        "reflection.html",
        rows=config["reflection_rows"],
        fields=config["reflection_fields"],
        answers=answers,
    )


# ---------- Панель учителя ----------

@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        config = quest_config.load_config()
        if password == config["teacher_password"]:
            session["teacher_authenticated"] = True
            return redirect(url_for("teacher_dashboard"))
        flash("Құпия сөз қате.")
    return render_template("teacher_login.html")


@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher_authenticated", None)
    return redirect(url_for("teacher_login"))


@app.route("/teacher")
@teacher_required
def teacher_dashboard():
    config = quest_config.load_config()
    stats = db.get_stats()
    stage_titles = {
        n: quest_config.get_stage_config(config, n)["title"]
        for n in range(1, quest_config.STAGE_COUNT + 1)
    }
    return render_template(
        "teacher_dashboard.html",
        stats=stats,
        stage_titles=stage_titles,
        stage_count=quest_config.STAGE_COUNT,
    )


@app.route("/teacher/editor/<int:n>", methods=["GET", "POST"])
@teacher_required
def teacher_editor(n):
    if not (1 <= n <= quest_config.STAGE_COUNT):
        abort(404)
    config = quest_config.load_config()
    stage_cfg = quest_config.get_stage_config(config, n)
    cipher = stage_cfg["cipher"]
    errors = []
    preview = None

    if request.method == "POST":
        new_stage = dict(stage_cfg)
        new_stage["hints"] = [
            request.form.get("hint1", "").strip(),
            request.form.get("hint2", "").strip(),
            request.form.get("hint3", "").strip(),
        ]
        new_stage["code_fragment"] = (request.form.get("code_fragment") or "").strip() or None

        if cipher in ("caesar", "vigenere", "columnar"):
            plaintext = request.form.get("plaintext", "").strip()
            alphabet = request.form.get("alphabet", "kazakh")
            new_stage["plaintext"] = plaintext
            if cipher == "caesar":
                try:
                    shift = int(request.form.get("shift", "0"))
                except ValueError:
                    shift = -1
                key = {"shift": shift, "alphabet": alphabet}
            else:
                key = {"keyword": request.form.get("keyword", "").strip(), "alphabet": alphabet}
            new_stage["key"] = key
            errors = CIPHER_VALIDATORS[cipher](key)
            if not plaintext:
                errors.append("Ашық мәтін бос болмауы керек")

        elif cipher == "playfair":
            plaintext = request.form.get("plaintext", "").strip()
            key = {"keyword": request.form.get("keyword", "").strip()}
            new_stage["plaintext"] = plaintext
            new_stage["key"] = key
            errors = CIPHER_VALIDATORS[cipher](key)
            if not plaintext:
                errors.append("Ашық мәтін бос болмауы керек")

        elif cipher == "rsa":
            try:
                p = int(request.form.get("p", "0"))
                q = int(request.form.get("q", "0"))
                e = int(request.form.get("e", "0"))
            except ValueError:
                p = q = e = 0
            key = {"p": p, "q": q, "e": e}
            plaintext = request.form.get("plaintext", "").strip().upper()
            new_stage["key"] = key
            new_stage["plaintext"] = plaintext
            errors = CIPHER_VALIDATORS[cipher](key)
            bad_chars = sorted(set(ch for ch in plaintext if ch not in rsa_utils.RSA_ALPHABET))
            if bad_chars:
                errors.append(f"Мәтінде рұқсат етілмеген таңбалар бар: {', '.join(bad_chars)} (тек A-Z, 0-9, бос орын)")
            if not plaintext:
                errors.append("Ашық мәтін (код) бос болмауы керек")

        elif cipher == "hash":
            files = []
            for i in range(1, 6):
                label = request.form.get(f"file_label_{i}", "").strip()
                content = request.form.get(f"file_content_{i}", "").strip()
                if label and content:
                    files.append({"label": label, "content": content})
            reference_label = request.form.get("reference_label", "").strip()
            new_stage["files"] = files
            new_stage["reference_label"] = reference_label
            if len(files) != 5:
                errors.append("Дәл 5 файл толтырылуы керек")
            labels = [f["label"] for f in files]
            if len(set(labels)) != len(labels):
                errors.append("Файл белгілері қайталанбауы керек")
            if reference_label not in labels:
                errors.append("Эталон файл белгісі тізімде болуы керек")
            else:
                import hashlib
                ref_content = next(f["content"] for f in files if f["label"] == reference_label)
                ref_hash = hashlib.sha256(ref_content.encode("utf-8")).hexdigest()
                matches = [f["label"] for f in files if hashlib.sha256(f["content"].encode("utf-8")).hexdigest() == ref_hash]
                if len(matches) != 1:
                    errors.append("Бірнеше файлдың хэші сәйкес келеді — файл мазмұндарын ерекшелендіріңіз")

        if not errors:
            config["stages"][str(n)] = new_stage
            quest_config.save_config(config)
            flash("Кезең сақталды. Тапсырма студенттер үшін автоматты түрде жаңартылды.")
            return redirect(url_for("teacher_editor", n=n))
        else:
            stage_cfg = new_stage

    preview = quest_config.build_stage_view(config, n) if not errors else None

    return render_template(
        "teacher_editor.html",
        n=n,
        stage=stage_cfg,
        cipher=cipher,
        errors=errors,
        preview=preview,
        kazakh_alphabet="".join(get_alphabet("kazakh")),
        latin_alphabet="".join(get_alphabet("latin")),
        rsa_alphabet=rsa_utils.RSA_ALPHABET,
    )


@app.route("/teacher/editor/<int:n>/randomize", methods=["POST"])
@teacher_required
def teacher_randomize(n):
    if not (1 <= n <= quest_config.STAGE_COUNT):
        abort(404)
    config = quest_config.load_config()
    stage_cfg = quest_config.get_stage_config(config, n)
    cipher = stage_cfg["cipher"]
    data = request.get_json(silent=True) or {}
    alphabet = data.get("alphabet", "kazakh")

    if cipher not in ("caesar", "vigenere", "columnar", "playfair", "rsa"):
        return jsonify(error="Бұл кезең үшін кездейсоқ кілт жасау қолданылмайды"), 400

    key = quest_config.generate_random_key(cipher, alphabet)
    plaintext = data.get("plaintext") or stage_cfg["plaintext"]

    if cipher in ("caesar", "vigenere", "columnar"):
        ciphertext = quest_config.CIPHER_MODULES[cipher].encrypt(plaintext, key)
    elif cipher == "playfair":
        ciphertext = playfair.encrypt(plaintext, key)
    else:
        res = rsa_utils.encrypt(plaintext.upper(), key)
        ciphertext = " ".join(str(c) for c in res["cipher"])

    return jsonify(key=key, ciphertext=ciphertext)


@app.route("/teacher/map")
@teacher_required
def teacher_map():
    config = quest_config.load_config()
    views = []
    for n in range(1, quest_config.STAGE_COUNT + 1):
        stage_cfg = quest_config.get_stage_config(config, n)
        view = quest_config.build_stage_view(config, n)
        views.append({"cfg": stage_cfg, "view": view, "number": n})
    final_code = quest_config.get_final_code(config)
    return render_template("teacher_map.html", views=views, final_code=final_code)


@app.route("/teacher/export.csv")
@teacher_required
def teacher_export_csv():
    stats = db.get_stats()
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["ID", "Режим", "Атауы", "Қатысушылар"]
    for n in range(1, quest_config.STAGE_COUNT + 1):
        header += [f"Кезең {n}: әрекет", f"Кезең {n}: көмек", f"Кезең {n}: балл"]
    header.append("Жалпы балл")
    writer.writerow(header)

    for entry in stats:
        player = entry["player"]
        row = [player["id"], player["mode"], player["display_name"], player["team_members"] or ""]
        for n in range(1, quest_config.STAGE_COUNT + 1):
            p = entry["progress"].get(n)
            if p:
                row += [p["attempts_count"], p["max_hint_level"], p["score"] if p["score"] is not None else ""]
            else:
                row += ["", "", ""]
        row.append(entry["total_score"])
        writer.writerow(row)

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=quest_statistics.csv"},
    )


@app.route("/teacher/reset", methods=["GET", "POST"])
@teacher_required
def teacher_reset():
    if request.method == "POST":
        db.reset_all_progress()
        flash("Барлық прогресс нөлденді.")
        return redirect(url_for("teacher_dashboard"))
    return render_template("teacher_reset.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
