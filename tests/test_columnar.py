from crypto import columnar


def test_known_vector_latin():
    # Проверено вручную: ключ ZEBRA даёт порядок столбцов A,B,E,R,Z -> индексы 4,2,1,3,0
    key = {"keyword": "ZEBRA", "alphabet": "latin"}
    ciphertext = columnar.encrypt("HELLOWORLD", key)
    assert ciphertext == "ODLREOLLHW"
    assert columnar.decrypt(ciphertext, key) == "HELLOWORLD"


def test_roundtrip_latin_various_lengths():
    key = {"keyword": "SECRET", "alphabet": "latin"}
    for plaintext in ["A", "AB", "HELLO", "HELLOWORLDFROMCRYPTOGRAPHY", "X" * 37]:
        ciphertext = columnar.encrypt(plaintext, key)
        assert columnar.decrypt(ciphertext, key) == plaintext


def test_roundtrip_kazakh_with_spaces():
    key = {"keyword": "ОРБИТА", "alphabet": "kazakh"}
    plaintext = "ЕКІНШІ ЕСІК АШЫЛДЫ БАЙЛАНЫС БӨЛМЕСІНДЕ ҮШ ЭКРАН БАР"
    ciphertext = columnar.encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert columnar.decrypt(ciphertext, key) == plaintext


def test_validate_key():
    assert columnar.validate_key({"keyword": "KEY", "alphabet": "latin"}) == []
    assert columnar.validate_key({"keyword": "K", "alphabet": "latin"}) != []
    assert columnar.validate_key({"keyword": "", "alphabet": "latin"}) != []
