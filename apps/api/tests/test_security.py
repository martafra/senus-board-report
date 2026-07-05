from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse")
    assert hashed != "correct-horse"
    assert verify_password("correct-horse", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="ceo@senus.com")
    assert decode_access_token(token) == "ceo@senus.com"


def test_garbage_token_is_rejected_not_raised():
    assert decode_access_token("not-a-real-token") is None
