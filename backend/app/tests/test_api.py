def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "testuser@repomind.io", "password": "superpassword", "full_name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@repomind.io"
    assert "id" in data

def test_login_user(client):
    # 1. Register
    client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@repomind.io", "password": "loginpassword", "full_name": "Login User"}
    )
    
    # 2. Login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "loginuser@repomind.io", "password": "loginpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_me(client):
    # 1. Register
    client.post(
        "/api/v1/auth/register",
        json={"email": "meuser@repomind.io", "password": "mypassword", "full_name": "Me User"}
    )
    
    # 2. Login to get token
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "meuser@repomind.io", "password": "mypassword"}
    )
    token = login_resp.json()["access_token"]
    
    # 3. Retrieve profiles
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "meuser@repomind.io"
