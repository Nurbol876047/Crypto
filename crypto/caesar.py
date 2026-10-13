"""
Шифр Цезаря с поддержкой настраиваемого алфавита (казахский или латинский).
key = {"shift": int, "alphabet": "kazakh" | "latin"}
"""
from crypto.alphabets import get_alphabet


def _alphabet_len(alphabet_name):
    return len(get_alphabet(alphabet_name))


def _shift_text(text, shift, alphabet_name):
    alphabet = get_alphabet(alphabet_name)
    upper = [c.upper() for c in alphabet]
    lower = [c.lower() for c in alphabet]
    n = len(upper)
    shift = shift % n
    result = []
    for ch in text:
        if ch in upper:
            idx = upper.index(ch)
            result.append(upper[(idx + shift) % n])
        elif ch in lower:
            idx = lower.index(ch)
            result.append(lower[(idx + shift) % n])
        else:
            result.append(ch)
    return "".join(result)


def encrypt(plaintext, key):
    return _shift_text(plaintext, key["shift"], key["alphabet"])


def decrypt(ciphertext, key):
    return _shift_text(ciphertext, -key["shift"], key["alphabet"])


def letter_frequencies(text, alphabet_name):
    """Считает частоты букв в тексте (для гистограммы частотного анализа)."""
    alphabet = [c.upper() for c in get_alphabet(alphabet_name)]
    counts = {letter: 0 for letter in alphabet}
    total = 0
    for ch in text.upper():
        if ch in counts:
            counts[ch] += 1
            total += 1
    return {"counts": counts, "total": total}


def validate_key(key):
    """Проверяет корректность ключа шифра Цезаря. Возвращает список ошибок (пустой — если всё верно)."""
    errors = []
    if "alphabet" not in key or key["alphabet"] not in ("kazakh", "latin"):
        errors.append("Алфавит должен быть 'kazakh' немесе 'latin'")
        return errors
    n = _alphabet_len(key["alphabet"])
    shift = key.get("shift")
    if not isinstance(shift, int):
        errors.append("Ығысу (shift) бүтін сан болуы керек")
    elif not (0 < shift < n):
        errors.append(f"Ығысу 1-ден {n - 1}-ге дейін болуы керек")
    return errors
