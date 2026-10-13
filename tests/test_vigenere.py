from crypto import vigenere


def test_known_vector_latin():
    key = {"keyword": "LEMON", "alphabet": "latin"}
    ciphertext = vigenere.encrypt("ATTACKATDAWN", key)
    assert ciphertext == "LXFOPVEFRNHR"
    assert vigenere.decrypt(ciphertext, key) == "ATTACKATDAWN"


def test_roundtrip_latin_with_spaces():
    key = {"keyword": "KEY", "alphabet": "latin"}
    plaintext = "ATTACK AT DAWN"
    ciphertext = vigenere.encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert vigenere.decrypt(ciphertext, key) == plaintext


def test_roundtrip_kazakh():
    key = {"keyword": "ҒАРЫШ", "alphabet": "kazakh"}
    plaintext = "ҮШІНШІ ЕСІК АШЫЛДЫ ЗЕРТХАНА КІЛТІ АРГО"
    ciphertext = vigenere.encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert vigenere.decrypt(ciphertext, key) == plaintext


def test_spaces_do_not_consume_key():
    key = {"keyword": "AB", "alphabet": "latin"}
    # Пробел не должен сдвигать позицию ключа: "A A" эквивалентно "AA" по сдвигам
    assert vigenere.encrypt("A A", key).replace(" ", "") == vigenere.encrypt("AA", key)


def test_validate_key():
    assert vigenere.validate_key({"keyword": "KEY", "alphabet": "latin"}) == []
    assert vigenere.validate_key({"keyword": "", "alphabet": "latin"}) != []
    assert vigenere.validate_key({"keyword": "123", "alphabet": "latin"}) != []
