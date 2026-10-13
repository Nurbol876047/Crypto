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


def _split_into_parts(word, part_count):
    """Сөзді дәйекті бөліктерге бөледі (мысалы, бөлмедегі бірнеше экранға шашырату үшін)."""
    n = len(word)
    base, extra = divmod(n, part_count)
    sizes = [base + 1] * extra + [base] * (part_count - extra)
    parts = []
    pos = 0
    for size in sizes:
        if size:
            parts.append(word[pos:pos + size])
            pos += size
    return parts


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
        if cipher == "vigenere":
            view["keyword_fragments"] = _split_into_parts(stage["key"]["keyword"], 3)
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


def get_answer_reveal(config, stage_number):
    """
    Нақты жауап пен оның неге дұрыс екенін түсіндіретін қысқа мәтінді қайтарады
    («Жауапты көру» батырмасы үшін). Мәндер ағымдағы конфигтен алынады, сондықтан
    мұғалім кілтті өзгертсе де түсіндірме сәйкес қалады.
    """
    stage = get_stage_config(config, stage_number)
    cipher = stage["cipher"]

    if cipher == "caesar":
        shift = stage["key"]["shift"]
        answer = stage["plaintext"]
        explanation = (
            f"Бұл мәтінде әр әріп алфавит бойынша дәл {shift} позицияға ығыстырылған — сондықтан "
            f"шифрмәтіннің әр әрпін {shift} қадам кері санасаңыз, ашық мәтін қайта пайда болады. "
            "Бір ғана сан бүкіл хабарды жасырады: сол санды тапсаңыз, бәрі бірден ашылады."
        )
    elif cipher == "vigenere":
        keyword = stage["key"]["keyword"]
        answer = stage["plaintext"]
        explanation = (
            f"Бұл — бірнеше Цезарь ығысуының тізбегі: «{keyword}» кілт сөзінің әр әрпі өз ығысу шамасын "
            "береді, әрі бұл ығысулар мәтін бойы қайта-қайта қайталанады. Сондықтан бір сдвигпен емес, "
            "кілт әрпіне сәйкес әр позицияны бөлек кері ығыстыру керек."
        )
    elif cipher == "columnar":
        keyword = stage["key"]["keyword"]
        answer = stage["plaintext"]
        explanation = (
            f"Әріптер ауыстырылмаған, тек орындары араласқан: мәтін «{keyword}» сөзінің ұзындығындай "
            f"({len(keyword)}) бағанға жазылып, содан соң бағандар кілт әріптерінің алфавиттегі реті "
            "бойынша қайта оқылған. Шифрмәтінді сол ретпен бағандарға бөліп, бастапқы ретімен "
            "құрастырса, сөйлем қалпына келеді."
        )
    elif cipher == "playfair":
        keyword = stage["key"]["keyword"]
        answer = playfair.preprocessed_plaintext(stage["plaintext"])
        explanation = (
            f"«{keyword}» кілт сөзімен құрылған 5×5 кестеде шифрмәтіннің әр әріп жұбы орналасуына қарай "
            "(бір жолда — оңға, бір бағанда — төмен, басқаша — бағандары ауыстырылып) ашылады. "
            f"Оқылатын мәтін: «{stage['plaintext']}». Бірақ «Жауап» өрісіне дәл осы блоктағыдай, "
            "бос орынсыз және соңындағы қосымша «X» әрпімен бірге жазу керек."
        )
    elif cipher == "hash":
        label = stage["reference_label"]
        answer = label
        explanation = (
            "SHA-256 — қайтымсыз функция: тіпті бір ғана әріп өзгерсе де, нәтиже хэш мүлдем басқаша "
            f"болады («көшкін эффектісі»). Бес файлдың ішінен тек {label}-файлдың мәтінінен есептелген "
            "хэш беттегі эталон хэшпен дәл сәйкес келеді, қалғандарының мәтінінде бір-екі таңба өзгертілген."
        )
    elif cipher == "rsa":
        p, q, e = stage["key"]["p"], stage["key"]["q"], stage["key"]["e"]
        n, phi, d = rsa_utils.compute_private_key(p, q, e)
        answer = stage["plaintext"]
        explanation = (
            f"n={n} санын p={p} және q={q} жай көбейткіштеріне жіктегеннен кейін φ(n)={phi} есептеледі, "
            f"содан e={e} санының φ(n) бойынша кері элементі d={d} табылады. Әр санды m = c^d mod n "
            "формуласымен ашып, нәтиже сандарын кодтар кестесі арқылы әріп/санға айналдырса, жауап шығады."
        )
    else:
        answer = stage.get("plaintext", "")
        explanation = ""

    return {
        "answer": answer,
        "explanation": explanation,
        "fragment": get_code_fragment(config, stage_number),
    }


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
