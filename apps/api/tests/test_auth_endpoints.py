from tests.factories import add_user, login


async def test_login_with_correct_credentials_returns_token(client, session_factory):
    async with session_factory() as session:
        await add_user(session)

    response = await client.post(
        "/auth/login", data={"username": "ceo@senus.com", "password": "s3cret"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_with_wrong_password_is_rejected(client, session_factory):
    async with session_factory() as session:
        await add_user(session)

    response = await client.post(
        "/auth/login", data={"username": "ceo@senus.com", "password": "wrong"}
    )

    assert response.status_code == 401


async def test_protected_endpoint_requires_a_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_protected_endpoint_works_with_a_valid_token(client, session_factory):
    async with session_factory() as session:
        await add_user(session)
    token = await login(client)

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ceo@senus.com"
