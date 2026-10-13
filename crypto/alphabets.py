"""Алфавиты, используемые в шифрах проекта, и общие функции нормализации текста."""
import re

# Казахский кириллический алфавит (42 буквы, порядок важен для шифра Цезаря/Виженера)
KAZAKH_ALPHABET = list("АӘБВГҒДЕЁЖЗИЙКҚЛМНҢОӨПРСТУҰҮФХҺЦЧШЩЪЫІЬЭЮЯ")

# Латинский алфавит (26 букв)
LATIN_ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

ALPHABETS = {
    "kazakh": KAZAKH_ALPHABET,
    "latin": LATIN_ALPHABET,
}


def get_alphabet(name):
    """Возвращает список букв алфавита по имени ('kazakh' или 'latin')."""
    try:
        return ALPHABETS[name]
    except KeyError:
        raise ValueError(f"Белгісіз алфавит: {name}")


_PUNCTUATION_RE = re.compile(r"[.,!?;:'\"()\-–—«»_/\\]")
_SPACES_RE = re.compile(r"\s+")


def normalize_answer(text):
    """
    Приводит введённый ответ к единому виду для сравнения с открытым текстом:
    убирает пунктуацию, лишние пробелы, приводит к нижнему регистру.
    """
    if text is None:
        return ""
    text = _PUNCTUATION_RE.sub("", text)
    text = _SPACES_RE.sub(" ", text)
    return text.strip().casefold()
