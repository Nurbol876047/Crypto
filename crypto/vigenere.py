"""
Шифр Виженера с поддержкой настраиваемого алфавита (казахский или латинский).
key = {"keyword": str, "alphabet": "kazakh" | "latin"}
Пробелы и прочие символы, не входящие в алфавит, не шифруются и не сдвигают ключ.
"""
from crypto.alphabets import get_alphabet


def _key_shifts(keyword, alphabet_name):
    alphabet = [c.upper() for c in get_alphabet(alphabet_name)]
    shifts = []
    for ch in keyword.upper():
        if ch in alphabet:
            shifts.append(alphabet.index(ch))
    if not shifts:
        raise ValueError("Кілт сөзде алфавитке жататын кемінде бір әрiп болуы керек")
    return shifts


def _process(text, keyword, alphabet_name, direction):
    alphabet = get_alphabet(alphabet_name)
    upper = [c.upper() for c in alphabet]
    lower = [c.lower() for c in alphabet]
    n = len(upper)
    shifts = _key_shifts(keyword, alphabet_name)
    k = len(shifts)

    result = []
    key_pos = 0
    for ch in text:
        if ch in upper:
            idx = upper.index(ch)
            s = shifts[key_pos % k] * direction
            result.append(upper[(idx + s) % n])
            key_pos += 1
        elif ch in lower:
            idx = lower.index(ch)
            s = shifts[key_pos % k] * direction
            result.append(lower[(idx + s) % n])
            key_pos += 1
        else:
            result.append(ch)
    return "".join(result)


def encrypt(plaintext, key):
    return _process(plaintext, key["keyword"], key["alphabet"], direction=1)


def decrypt(ciphertext, key):
    return _process(ciphertext, key["keyword"], key["alphabet"], direction=-1)


def validate_key(key):
    """Проверяет корректность ключа шифра Виженера."""
    errors = []
    if "alphabet" not in key or key["alphabet"] not in ("kazakh", "latin"):
        errors.append("Алфавит должен быть 'kazakh' немесе 'latin'")
        return errors
    keyword = key.get("keyword", "")
    if not keyword or not isinstance(keyword, str):
        errors.append("Кілт сөз бос болмауы керек")
        return errors
    alphabet = [c.upper() for c in get_alphabet(key["alphabet"])]
    if not any(ch.upper() in alphabet for ch in keyword):
        errors.append("Кілт сөзде таңдалған алфавитке жататын кемінде бір әрiп болуы керек")
    return errors
