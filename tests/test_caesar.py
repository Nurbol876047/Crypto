from crypto import caesar
from crypto.alphabets import LATIN_ALPHABET


def test_roundtrip_latin():
    key = {"shift": 5, "alphabet": "latin"}
    plaintext = "THE QUICK BROWN FOX"
    ciphertext = caesar.encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert caesar.decrypt(ciphertext, key) == plaintext


def test_roundtrip_kazakh():
    key = {"shift": 7, "alphabet": "kazakh"}
    plaintext = "БІРІНШІ ЕСІК АШЫЛДЫ МАҚСАТ ҰШЫРУ КОДЫН ТАУЫП АЛУ"
    ciphertext = caesar.encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert caesar.decrypt(ciphertext, key) == plaintext


def test_known_vector_latin():
    key = {"shift": 3, "alphabet": "latin"}
    assert caesar.encrypt("ABC", key) == "DEF"
    assert caesar.decrypt("DEF", key) == "ABC"


def test_case_preserved():
    key = {"shift": 1, "alphabet": "latin"}
    assert caesar.encrypt("AbZ", key) == "BcA"


def test_non_alphabet_chars_untouched():
    key = {"shift": 4, "alphabet": "latin"}
    ciphertext = caesar.encrypt("A, B! 123", key)
    assert ciphertext == "E, F! 123"


def test_shift_wraps_modulo_alphabet_length():
    n = len(LATIN_ALPHABET)
    key_small = {"shift": 3, "alphabet": "latin"}
    key_wrapped = {"shift": 3 + n, "alphabet": "latin"}
    assert caesar.encrypt("HELLO", key_small) == caesar.encrypt("HELLO", key_wrapped)


def test_validate_key():
    assert caesar.validate_key({"shift": 5, "alphabet": "latin"}) == []
    assert caesar.validate_key({"shift": 0, "alphabet": "latin"}) != []
    assert caesar.validate_key({"shift": 5, "alphabet": "unknown"}) != []
