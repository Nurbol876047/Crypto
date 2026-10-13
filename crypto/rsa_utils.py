"""
Учебный RSA с маленькими числами (p, q < 100).
key = {"p": int, "q": int, "e": int}

Алфавит для кодирования символов открытого текста (37 символов):
цифры 0-9, латинские буквы A-Z, пробел.
n = p * q должно быть больше длины этого алфавита, чтобы каждый символ
кодировался однозначно.
"""
import random

RSA_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "


def is_prime(n):
    """Проверка на простоту пробным делением (числа маленькие, этого достаточно)."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def gcd(a, b):
    """Наибольший общий делитель (алгоритм Евклида)."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a, b):
    """Расширенный алгоритм Евклида: возвращает (g, x, y) такие, что a*x + b*y = g."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def modinverse(a, m):
    """Обратный элемент a по модулю m (a*x ≡ 1 mod m). Бросает ValueError, если его нет."""
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise ValueError(f"{a} модуль {m} бойынша кері элементі жоқ (gcd = {g})")
    return x % m


def char_to_num(ch):
    idx = RSA_ALPHABET.find(ch.upper())
    if idx == -1:
        raise ValueError(f"RSA алфавитінде жоқ таңба: {ch!r}")
    return idx


def num_to_char(num):
    if not (0 <= num < len(RSA_ALPHABET)):
        raise ValueError(f"RSA алфавитінен тыс код: {num}")
    return RSA_ALPHABET[num]


def encrypt(plaintext, key):
    """
    Шифрует текст посимвольно: c_i = m_i^e mod n.
    Возвращает словарь {"n": n, "e": e, "cipher": [список чисел]}.
    """
    p, q, e = key["p"], key["q"], key["e"]
    n = p * q
    cipher = [pow(char_to_num(ch), e, n) for ch in plaintext]
    return {"n": n, "e": e, "cipher": cipher}


def decrypt_with_d(cipher_numbers, n, d):
    """Расшифровывает список чисел, зная n и закрытую экспоненту d."""
    chars = [num_to_char(pow(c, d, n)) for c in cipher_numbers]
    return "".join(chars)


def compute_private_key(p, q, e):
    """По p, q, e вычисляет n, phi(n) и закрытую экспоненту d."""
    n = p * q
    phi = (p - 1) * (q - 1)
    d = modinverse(e, phi)
    return n, phi, d


def validate_key(key):
    """
    Проверяет ключ RSA для учебных целей:
    p и q — разные простые числа меньше 100, n больше размера алфавита,
    e взаимно просто с phi(n) и 1 < e < phi(n).
    """
    errors = []
    p = key.get("p")
    q = key.get("q")
    e = key.get("e")
    if not isinstance(p, int) or not is_prime(p) or not (1 < p < 100):
        errors.append("p 100-ден кем жай сан болуы керек")
    if not isinstance(q, int) or not is_prime(q) or not (1 < q < 100):
        errors.append("q 100-ден кем жай сан болуы керек")
    if isinstance(p, int) and isinstance(q, int) and p == q:
        errors.append("p және q бірдей болмауы керек")
    if errors:
        return errors
    n = p * q
    if n <= len(RSA_ALPHABET):
        errors.append(f"n = p*q мәні алфавит өлшемінен ({len(RSA_ALPHABET)}) үлкен болуы керек")
        return errors
    phi = (p - 1) * (q - 1)
    if not isinstance(e, int) or not (1 < e < phi):
        errors.append(f"e саны 1-ден {phi}-ге дейін болуы керек")
        return errors
    if gcd(e, phi) != 1:
        errors.append("e саны phi(n)-мен өзара жай болуы керек (gcd(e, phi) = 1)")
    return errors


def generate_random_key():
    """Генерирует случайный корректный учебный ключ RSA (p, q < 100, e подобрано автоматически)."""
    primes = [x for x in range(11, 98) if is_prime(x)]
    while True:
        p, q = random.sample(primes, 2)
        n = p * q
        if n <= len(RSA_ALPHABET):
            continue
        phi = (p - 1) * (q - 1)
        candidates = [x for x in range(2, phi) if gcd(x, phi) == 1]
        if not candidates:
            continue
        e = random.choice(candidates)
        return {"p": p, "q": q, "e": e}
