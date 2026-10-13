import pytest

from crypto import rsa_utils


def test_is_prime():
    primes = [2, 3, 5, 7, 11, 13, 47, 53, 97]
    for p in primes:
        assert rsa_utils.is_prime(p), p
    non_primes = [0, 1, 4, 6, 8, 9, 100, 91]
    for n in non_primes:
        assert not rsa_utils.is_prime(n), n


def test_gcd():
    assert rsa_utils.gcd(48, 18) == 6
    assert rsa_utils.gcd(17, 13) == 1
    assert rsa_utils.gcd(0, 5) == 5


def test_modinverse():
    # 3 * 7 = 21 = 1 mod 20
    assert rsa_utils.modinverse(3, 20) == 7
    with pytest.raises(ValueError):
        rsa_utils.modinverse(2, 4)  # gcd(2,4) = 2, обратного элемента нет


def test_encrypt_decrypt_roundtrip():
    key = {"p": 47, "q": 53, "e": 7}
    plaintext = "KZ2026"
    result = rsa_utils.encrypt(plaintext, key)
    n, phi, d = rsa_utils.compute_private_key(key["p"], key["q"], key["e"])
    decrypted = rsa_utils.decrypt_with_d(result["cipher"], n, d)
    assert decrypted == plaintext


def test_char_mapping_roundtrip():
    for ch in rsa_utils.RSA_ALPHABET:
        num = rsa_utils.char_to_num(ch)
        assert rsa_utils.num_to_char(num) == ch


def test_validate_key():
    assert rsa_utils.validate_key({"p": 47, "q": 53, "e": 7}) == []
    assert rsa_utils.validate_key({"p": 4, "q": 53, "e": 7}) != []  # 4 не простое
    assert rsa_utils.validate_key({"p": 47, "q": 47, "e": 7}) != []  # p == q
    assert rsa_utils.validate_key({"p": 3, "q": 5, "e": 2}) != []  # n=15 слишком мал для алфавита
    assert rsa_utils.validate_key({"p": 47, "q": 53, "e": 4}) != []  # e не взаимно просто с phi


def test_generate_random_key_is_valid():
    for _ in range(20):
        key = rsa_utils.generate_random_key()
        assert rsa_utils.validate_key(key) == []
