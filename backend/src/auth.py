"""
Module Authentification
=======================
Ce module centralise la logique de sécurité de l'application. 
Il gère la vérification des mots de passe hachés (via bcrypt) ainsi que 
la création et la validation des jetons JWT (JSON Web Tokens) utilisés 
pour maintenir la session de l'utilisateur.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuration du logger pour tracer les erreurs liées à la sécurité
logger = logging.getLogger("uvicorn.error")


# =============================================================================
# CONFIGURATION JWT
# =============================================================================

# La clé secrète doit idéalement être définie dans les variables d'environnement.
# Une valeur par défaut est fournie pour le développement ou les environnements non configurés.
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-jwt-key-prod-newsfoundry-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Expiration fixée à 24 heures


# =============================================================================
# GESTION DES MOTS DE PASSE
# =============================================================================

def verify_password(plain_password: str, hashed_password: str | bytes | memoryview) -> bool:
    """
    Vérifie la correspondance entre un mot de passe en clair et son empreinte hachée.
    
    Cette fonction intègre une logique de conversion de type robuste pour prévenir 
    les erreurs liées aux différents pilotes de base de données (SQLite renvoie 
    parfois des strings, PostgreSQL via asyncpg peut renvoyer des memoryviews).
    
    Args:
        plain_password (str): Le mot de passe saisi par l'utilisateur.
        hashed_password (str | bytes | memoryview): Le mot de passe haché stocké en base.
        
    Returns:
        bool: True si le mot de passe correspond, False sinon.
    """
    try:
        # Normalisation du mot de passe haché en format bytes
        if isinstance(hashed_password, memoryview):
            hashed_bytes = hashed_password.tobytes()
        elif isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode("utf-8")
        elif isinstance(hashed_password, bytes):
            hashed_bytes = hashed_password
        else:
            return False

        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)
        
    except Exception as exc:
        # Journalisation de l'erreur pour l'audit de sécurité sans exposer les détails techniques au client
        logger.error(f"Erreur de vérification bcrypt : {exc}")
        return False


# =============================================================================
# GESTION DES JETONS (TOKENS)
# =============================================================================

def create_access_token(data: dict) -> str:
    """
    Génère un nouveau jeton JWT avec une durée de validité limitée.
    
    Args:
        data (dict): Le payload à encoder dans le jeton (ex: identifiant de l'utilisateur).
        
    Returns:
        str: Le jeton JWT signé.
    """
    to_encode = data.copy()
    
    # Ajout de la revendication 'exp' (expiration) requise par le standard JWT
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Configuration de FastAPI pour extraire automatiquement le token du header 'Authorization: Bearer'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Dépendance FastAPI (Depends) utilisée pour protéger les routes de l'API.
    Elle décode le jeton fourni dans la requête, vérifie sa validité, et extrait l'ID utilisateur.
    
    Args:
        token (str): Le jeton JWT fourni automatiquement par FastAPI via le header Authorization.
        
    Returns:
        int: L'identifiant de l'utilisateur connecté.
        
    Raises:
        HTTPException: 401 Unauthorized si le jeton est absent, invalide ou expiré.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Le décodage vérifie implicitement la signature et l'expiration du jeton
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
        return user_id
        
    except jwt.PyJWTError:
        # Cette exception englobe toutes les erreurs JWT courantes (ExpiredSignatureError, DecodeError, etc.)
        raise credentials_exception