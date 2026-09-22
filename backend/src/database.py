"""
Module Gestion de Base de Données
=================================
Ce module configure la connexion à la base de données PostgreSQL (ou SQLite en local) 
via SQLModel et SQLAlchemy. Il fournit le générateur de session utilisé comme 
dépendance dans FastAPI et contient la logique d'initialisation de l'environnement 
(création des tables et injection des données par défaut).
"""

import os
import bcrypt
from sqlmodel import SQLModel, Session, create_engine, select
from models import User

# Récupération de la chaîne de connexion depuis l'environnement (ex: Railway, Docker)
DATABASE_URL = os.getenv("DATABASE_URL")

# Création du moteur de base de données. 
# Le paramètre echo=True affiche les requêtes SQL dans la console, 
# ce qui est utile pour le débogage mais devrait idéalement être désactivé en production.
engine = create_engine(DATABASE_URL, echo=True)


# =============================================================================
# GESTION DES SESSIONS
# =============================================================================

def get_session():
    """
    Générateur de session pour la base de données.
    
    Conçu pour être utilisé avec le système d'injection de dépendances de FastAPI (`Depends`).
    Garantit qu'une session de base de données est ouverte au début d'une requête HTTP
    et fermée proprement à la fin, même en cas d'erreur.
    
    Yields:
        Session: Une instance de session SQLModel active.
    """
    with Session(engine) as session:
        yield session


# =============================================================================
# INITIALISATION ET PEUPLEMENT (SEEDING)
# =============================================================================

def init_db():
    """
    Initialise le schéma de la base de données et peuple les données par défaut.
    
    Cette fonction crée toutes les tables définies dans les modèles SQLModel si elles 
    n'existent pas encore. Ensuite, elle s'assure qu'un utilisateur de test est présent 
    dans la base avec un mot de passe valide (haché via bcrypt), ce qui facilite 
    le développement et les tests initiaux.
    """
    # Création des tables à partir des métadonnées SQLModel
    SQLModel.metadata.create_all(engine)
    print("Database initialized successfully")

    # Définition des identifiants de l'utilisateur de test par défaut
    default_email = "test@test.com"
    default_password = "test"

    # Génération d'un hash bcrypt propre pour éviter le stockage de mots de passe en clair
    salt = bcrypt.gensalt()
    new_hashed_password = bcrypt.hashpw(default_password.encode("utf-8"), salt).decode("utf-8")

    with Session(engine) as session:
        # Vérification de l'existence de l'utilisateur de test
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        if not user:
            # Création de l'utilisateur s'il n'existe pas lors du premier lancement
            session.add(User(email=default_email, hashed_password=new_hashed_password))
            session.commit()
        else:
            # Force la mise à jour du mot de passe. Cela permet de s'assurer que 
            # même si la base de données a subi une altération des hashs, le compte de test reste accessible.
            user.hashed_password = new_hashed_password
            session.add(user)
            session.commit()