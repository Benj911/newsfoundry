from fastapi.testclient import TestClient
from main import app
from auth import get_current_user_id

client = TestClient(app)

def override_get_current_user(user_id: int):
    app.dependency_overrides[get_current_user_id] = lambda: user_id

def test_nominal_access_own_chat():
    # Simule l'utilisateur 1
    override_get_current_user(1)
    
    # Création du chat
    response_create = client.post("/chats")
    assert response_create.status_code == 200
    chat_id = response_create.json()["chat_id"]
    
    # Accès autorisé à son propre chat
    response_get = client.get(f"/chats/{chat_id}")
    assert response_get.status_code == 200
    assert response_get.json()["id"] == chat_id

def test_forbidden_access_other_user_chat():
    # Utilisateur 1 crée un chat
    override_get_current_user(1)
    response_create = client.post("/chats")
    chat_id = response_create.json()["chat_id"]
    
    # Utilisateur 2 tente d'y accéder
    override_get_current_user(2)
    response_get = client.get(f"/chats/{chat_id}")
    
    # Vérification du blocage (404 pour ne pas révéler l'existence du chat)
    assert response_get.status_code == 404
    assert response_get.json()["detail"] == "Chat introuvable"
    
    app.dependency_overrides.clear()