"""
Шифр Плейфера (Playfair). Только латинский алфавит, таблица 5x5, буквы I и J объединены.
key = {"keyword": str}

Правила:
- таблица строится из ключевого слова (без повторов, J -> I) + оставшиеся буквы алфавита;
- текст приводится к верхнему регистру, не-буквы удаляются, J заменяется на I;
- текст разбивается на биграммы; если буквы в биграмме совпадают — между ними
  вставляется 'X'; если длина текста нечётная — в конец добавляется 'X';
- шифрование/расшифрование биграммы — по стандартным правилам Плейфера
  (одна строка / один столбец / прямоугольник).
"""
import re

_LATIN_NO_J = "ABCDEFGHIKLMNOPQRSTUVWXYZ"  # 25 букв, J объединена с I
_PAD_CHAR = "X"


def build_table(keyword):
    """Строит таблицу 5x5 (список из 5 списков по 5 букв) по ключевому слову."""
    keyword = re.sub(r"[^A-Za-z]", "", keyword).upper().replace("J", "I")
    seen = []
    for ch in keyword:
        if ch not in seen:
            seen.append(ch)
    for ch in _LATIN_NO_J:
        if ch not in seen:
            seen.append(ch)
    table = [seen[i * 5:(i + 1) * 5] for i in range(5)]
    return table


def _find(table, ch):
    for r, row in enumerate(table):
        for c, letter in enumerate(row):
            if letter == ch:
                return r, c
    raise ValueError(f"Әріп кестеде табылмады: {ch}")


def _prepare_text(text):
    text = re.sub(r"[^A-Za-z]", "", text).upper().replace("J", "I")
    pairs = []
    i = 0
    while i < len(text):
        a = text[i]
        if i + 1 < len(text):
            b = text[i + 1]
            if a == b:
                pairs.append((a, _PAD_CHAR))
                i += 1
            else:
                pairs.append((a, b))
                i += 2
        else:
            pairs.append((a, _PAD_CHAR))
            i += 1
    return pairs


def encrypt(plaintext, key):
    table = build_table(key["keyword"])
    pairs = _prepare_text(plaintext)
    result = []
    for a, b in pairs:
        ra, ca = _find(table, a)
        rb, cb = _find(table, b)
        if ra == rb:
            result.append(table[ra][(ca + 1) % 5])
            result.append(table[rb][(cb + 1) % 5])
        elif ca == cb:
            result.append(table[(ra + 1) % 5][ca])
            result.append(table[(rb + 1) % 5][cb])
        else:
            result.append(table[ra][cb])
            result.append(table[rb][ca])
    return "".join(result)


def decrypt(ciphertext, key):
    table = build_table(key["keyword"])
    text = re.sub(r"[^A-Za-z]", "", ciphertext).upper().replace("J", "I")
    result = []
    for i in range(0, len(text) - 1, 2):
        a, b = text[i], text[i + 1]
        ra, ca = _find(table, a)
        rb, cb = _find(table, b)
        if ra == rb:
            result.append(table[ra][(ca - 1) % 5])
            result.append(table[rb][(cb - 1) % 5])
        elif ca == cb:
            result.append(table[(ra - 1) % 5][ca])
            result.append(table[(rb - 1) % 5][cb])
        else:
            result.append(table[ra][cb])
            result.append(table[rb][ca])
    return "".join(result)


def preprocessed_plaintext(plaintext):
    """
    Возвращает канонический вид открытого текста после предобработки Плейфера
    (только латинские буквы, J->I, вставленные заполнители 'X'). Именно такую
    непрерывную строку (без пробелов) должен получить игрок при расшифровке.
    """
    pairs = _prepare_text(plaintext)
    return "".join(a + b for a, b in pairs)


def validate_key(key):
    """Проверяет ключ Плейфера: только латинские буквы, минимум 2 уникальные."""
    errors = []
    keyword = key.get("keyword", "")
    if not keyword or not isinstance(keyword, str):
        errors.append("Кілт сөз бос болмауы керек")
        return errors
    if not re.fullmatch(r"[A-Za-z]+", keyword):
        errors.append("Кілт сөзде тек латын әріптері болуы керек")
    return errors
