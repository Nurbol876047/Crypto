"""
Столбцовая перестановка (columnar transposition) без заполнителей —
текст записывается по строкам в N столбцов (N = длина ключевого слова),
затем столбцы считываются в порядке, заданном алфавитным рангом букв ключа.
Так как заполнители не используются, encrypt(decrypt(x)) всегда точно
восстанавливает исходный текст.

key = {"keyword": str, "alphabet": "kazakh" | "latin"}
"""
import math
from crypto.alphabets import get_alphabet


def _column_order(keyword, alphabet_name):
    """
    Возвращает список исходных индексов столбцов в порядке чтения:
    сортировка по рангу буквы в алфавите, при равенстве — по исходной позиции.
    """
    alphabet = [c.upper() for c in get_alphabet(alphabet_name)]
    ranks = []
    for i, ch in enumerate(keyword.upper()):
        rank = alphabet.index(ch) if ch in alphabet else len(alphabet) + i
        ranks.append((rank, i))
    order = sorted(range(len(keyword)), key=lambda i: (ranks[i][0], ranks[i][1]))
    return order


def _column_heights(length, n_cols):
    """
    При записи текста по строкам в n_cols столбцов первые (length % n_cols)
    столбцов получают по rows букв, остальные — по (rows - 1).
    """
    rows = math.ceil(length / n_cols) if length else 0
    long_cols = length - (rows - 1) * n_cols if rows else 0
    heights = [rows if col < long_cols else rows - 1 for col in range(n_cols)]
    return heights


def encrypt(plaintext, key):
    keyword = key["keyword"]
    alphabet_name = key["alphabet"]
    n_cols = len(keyword)
    length = len(plaintext)
    heights = _column_heights(length, n_cols)

    # Раскладываем текст по столбцам (построчно, слева направо)
    columns = [[] for _ in range(n_cols)]
    col = 0
    for ch in plaintext:
        columns[col].append(ch)
        col = (col + 1) % n_cols

    order = _column_order(keyword, alphabet_name)
    return "".join("".join(columns[c]) for c in order)


def decrypt(ciphertext, key):
    keyword = key["keyword"]
    alphabet_name = key["alphabet"]
    n_cols = len(keyword)
    length = len(ciphertext)
    heights = _column_heights(length, n_cols)
    order = _column_order(keyword, alphabet_name)

    # Разбиваем шифротекст на куски согласно высотам столбцов в порядке чтения
    columns = [None] * n_cols
    pos = 0
    for col in order:
        h = heights[col]
        columns[col] = list(ciphertext[pos:pos + h])
        pos += h

    # Собираем исходный текст обратно построчно
    result = []
    rows = max(heights) if heights else 0
    indices = [0] * n_cols
    for r in range(rows):
        for col in range(n_cols):
            if indices[col] < len(columns[col]):
                result.append(columns[col][indices[col]])
                indices[col] += 1
    return "".join(result)


def validate_key(key):
    """Проверяет корректность ключа столбцовой перестановки."""
    errors = []
    if "alphabet" not in key or key["alphabet"] not in ("kazakh", "latin"):
        errors.append("Алфавит должен быть 'kazakh' немесе 'latin'")
        return errors
    keyword = key.get("keyword", "")
    if not keyword or not isinstance(keyword, str) or len(keyword) < 2:
        errors.append("Кілт сөз кемінде 2 әріптен тұруы керек")
    return errors
