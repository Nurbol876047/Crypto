from crypto import playfair


def test_known_vector_monarchy():
    # Классический учебный пример шифра Плейфера
    key = {"keyword": "MONARCHY"}
    ciphertext = playfair.encrypt("INSTRUMENTS", key)
    assert ciphertext == "GATLMZCLRQXA"


def test_build_table_merges_i_and_j():
    table = playfair.build_table("MONARCHY")
    flat = [ch for row in table for ch in row]
    assert "J" not in flat
    assert "I" in flat
    assert len(flat) == 25
    assert len(set(flat)) == 25


def test_roundtrip_simple():
    key = {"keyword": "ARGO"}
    plaintext = "PLAYFAIR"
    ciphertext = playfair.encrypt(plaintext, key)
    decrypted = playfair.decrypt(ciphertext, key)
    # Без повторов внутри пар и без наращивания нечётной длины -> восстанавливается точно
    assert decrypted == plaintext


def test_roundtrip_matches_preprocessed_form():
    key = {"keyword": "ARGO"}
    plaintext = "HELLOWORLD"
    ciphertext = playfair.encrypt(plaintext, key)
    decrypted = playfair.decrypt(ciphertext, key)
    # Для текста с повторами/нечётной длиной результат совпадает с канонической
    # (предобработанной с заполнителями) формой, а не с исходным текстом буквально
    assert decrypted == playfair.preprocessed_plaintext(plaintext)


def test_double_letters_get_padding():
    # Между повторяющимися буквами (LL) вставляется заполнитель X
    preprocessed = playfair.preprocessed_plaintext("BALLOON")
    assert preprocessed == "BALXLOON"


def test_j_replaced_by_i():
    key = {"keyword": "ARGO"}
    ciphertext_j = playfair.encrypt("JAZZ", key)
    ciphertext_i = playfair.encrypt("IAZZ", key)
    assert ciphertext_j == ciphertext_i


def test_validate_key():
    assert playfair.validate_key({"keyword": "ARGO"}) == []
    assert playfair.validate_key({"keyword": "АРГО"}) != []
    assert playfair.validate_key({"keyword": ""}) != []
