"""
Загрузка и сохранение конфигурации квеста (config/quest.json), а также
построение шифротекстов этапов "на лету" из открытого текста и ключа.
Шифротекст никогда не хранится в готовом виде — он всегда вычисляется заново.
"""
import hashlib
import json
import os
import random
import re

from crypto import caesar, vigenere, columnar, playfair, rsa_utils
from crypto.alphabets import normalize_answer, get_alphabet

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "quest.json")

CIPHER_MODULES = {
    "caesar": caesar,
    "vigenere": vigenere,
    "columnar": columnar,
    "playfair": playfair,
}

STAGE_COUNT = 6


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    """Атомарно сохраняет конфиг (пишет во временный файл и заменяет оригинал)."""
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CONFIG_PATH)


def get_stage_config(config, stage_number):
    return config["stages"][str(stage_number)]


def build_stage_view(config, stage_number):
    """Строит все данные, нужные для отображения этапа, включая свежий шифротекст."""
    stage = get_stage_config(config, stage_number)
    cipher = stage["cipher"]
    view = {
        "number": stage_number,
        "title": stage["title"],
        "subtitle": stage["subtitle"],
        "intro": stage["intro"],
        "cipher": cipher,
        "hints": stage["hints"],
    }
    if cipher in CIPHER_MODULES:
        module = CIPHER_MODULES[cipher]
        view["ciphertext"] = module.encrypt(stage["plaintext"], stage["key"])
        if cipher in ("caesar", "vigenere", "columnar"):
            view["key_alphabet"] = stage["key"].get("alphabet")
        if cipher == "caesar":
            view["frequencies"] = caesar.letter_frequencies(view["ciphertext"], stage["key"]["alphabet"])
    elif cipher == "hash":
        files = stage["files"]
        ref_content = next(f["content"] for f in files if f["label"] == stage["reference_label"])
        view["files"] = files
        view["reference_hash"] = hashlib.sha256(ref_content.encode("utf-8")).hexdigest()
    elif cipher == "rsa":
        res = rsa_utils.encrypt(stage["plaintext"], stage["key"])
        view["n"] = res["n"]
        view["e"] = res["e"]
        view["cipher_numbers"] = res["cipher"]
        view["rsa_alphabet"] = rsa_utils.RSA_ALPHABET
    return view


def _letters_only(text):
    return re.sub(r"[^A-Za-z]", "", text or "").upper()


def check_answer(config, stage_number, submitted_answer):
    """Сравнивает ответ игрока с открытым текстом этапа после нормализации."""
    stage = get_stage_config(config, stage_number)
    cipher = stage["cipher"]

    if cipher == "hash":
        correct = normalize_answer(stage["reference_label"])
        submitted = normalize_answer(submitted_answer)
        return submitted == correct

    if cipher == "playfair":
        correct = playfair.preprocessed_plaintext(stage["plaintext"])
        submitted = _letters_only(submitted_answer)
        return submitted == correct

    correct = normalize_answer(stage["plaintext"])
    submitted = normalize_answer(submitted_answer)
    return submitted == correct


def get_code_fragment(config, stage_number):
    stage = get_stage_config(config, stage_number)
    if stage.get("code_fragment"):
        return stage["code_fragment"]
    return stage["plaintext"]


def get_final_code(config):
    return "-".join(get_code_fragment(config, n) for n in range(1, STAGE_COUNT + 1))


# ---------- Случайные ключи (кнопка "Сгенерировать случайно" в панели учителя) ----------

KAZAKH_KEYWORDS = ["ОРБИТА", "ҒАРЫШ", "ЖҰЛДЫЗ", "АСПАН", "РАКЕТА", "ПЛАНЕТА", "СПУТНИК"]
LATIN_KEYWORDS = ["ARGO", "ORBIT", "COSMOS", "LAUNCH", "ROCKET", "GALAXY", "SPUTNIK"]


def generate_random_key(cipher, alphabet="kazakh"):
    """Генерирует случайный корректный ключ для указанного типа шифра."""
    if cipher == "caesar":
        n = len(get_alphabet(alphabet))
        return {"shift": random.randint(1, n - 1), "alphabet": alphabet}
    if cipher in ("vigenere", "columnar"):
        words = KAZAKH_KEYWORDS if alphabet == "kazakh" else LATIN_KEYWORDS
        return {"keyword": random.choice(words), "alphabet": alphabet}
    if cipher == "playfair":
        return {"keyword": random.choice(LATIN_KEYWORDS)}
    if cipher == "rsa":
        return rsa_utils.generate_random_key()
    raise ValueError("Бұл шифр үшін кездейсоқ кілт жасау қолданылмайды")
