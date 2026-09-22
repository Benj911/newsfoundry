"""
Module de Tests : Gestion des Discussions (Chats)
=================================================
Ce module contient les tests d'intégration automatisés pour les routes API
liées à la gestion des discussions. Il valide notamment la création des chats
et l'isolation stricte des données entre les utilisateurs (sécurité contre
les vulnérabilités de type IDOR - Insecure Direct Object Reference).
"""

from fastapi.testclient import TestClient
from main import app
from auth import get_current_user_id

# =============================================================================
# UTILITAIRES DE TEST (MOCKS)
# =============================================================================

def override_get_current_user(user_id: int):
    """
    Substitue la dépendance d'authentification de FastAPI pour les tests.
    
    Cette fonction permet de simuler la connexion d'un utilisateur sans avoir
    à générer et valider de réels jetons JWT. Elle force FastAPI à considérer 
    la requête comme provenant du `user_id` spécifié.
    
    Args:
        user_id (int): L'identifiant de l'utilisateur à simuler.
    """
    app.dependency_overrides[get_current_user_id] = lambda: user_id


# =============================================================================
# CAS DE TESTS
# =============================================================================

def test_nominal_access_own_chat():
    """
    Test du parcours nominal : Création et accès à sa propre discussion.
    
    Vérifie qu'un utilisateur authentifié peut créer une nouvelle discussion
    et y accéder ensuite sans erreur.
    """
    # Simulation de l'utilisateur avec l'ID 1
    override_get_current_user(1)
    
    # L'utilisation du bloc "with" est primordiale ici : elle déclenche le 
    # gestionnaire de cycle de vie (lifespan) de FastAPI, ce qui exécute init_db().
    with TestClient(app) as client:
        
        # 1. Création d'une nouvelle discussion
        response_create = client.post("/chats")
        assert response_create.status_code == 200
        
        chat_id = response_create.json()["chat_id"]
        
        # 2. Tentative d'accès autorisé à la discussion fraîchement créée
        response_get = client.get(f"/chats/{chat_id}")
        assert response_get.status_code == 200
        assert response_get.json()["id"] == chat_id


def test_forbidden_access_other_user_chat():
    """
    Test de sécurité : Blocage de l'accès aux discussions d'un tiers.
    
    Vérifie le cloisonnement des données. Si l'utilisateur B tente de lire
    une discussion appartenant à l'utilisateur A, l'API doit bloquer l'accès.
    """
    # Étape 1 : Simulation de l'utilisateur A (ID 1)
    override_get_current_user(1)
    
    with TestClient(app) as client:
        
        # Création d'un chat appartenant à l'utilisateur 1
        response_create = client.post("/chats")
        chat_id = response_create.json()["chat_id"]
        
        # Étape 2 : Changement de contexte, simulation de l'utilisateur B (ID 2)
        override_get_current_user(2)
        
        # Tentative d'accès au chat de l'utilisateur 1 par l'utilisateur 2
        response_get = client.get(f"/chats/{chat_id}")
        
        # Vérification du blocage de sécurité
        # On attend intentionnellement un 404 (Not Found) plutôt qu'un 403 (Forbidden).
        # C'est une bonne pratique de sécurité pour ne pas confirmer l'existence 
        # de l'identifiant à un attaquant potentiel.
        assert response_get.status_code == 404
        assert response_get.json()["detail"] == "Chat introuvable"
        
    # Nettoyage systématique des substitutions de dépendances après l'exécution.
    # Indispensable pour éviter la pollution contextuelle des autres suites de tests.
    app.dependency_overrides.clear()