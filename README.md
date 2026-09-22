# NewsFoundry - Assistant d'Actualités IA & Revue de Presse

NewsFoundry est une application web permettant d'interagir avec un assistant d'actualités intelligent. Propulsée par l'IA, l'application recherche des articles récents, extrait leur contenu complet et génère des revues de presse structurées (RAG) à partir de l'historique de discussion.

## Liens de Production

*   **Frontend (Vercel)** : https://newsfoundry-one.vercel.app/
*   **Backend & Documentation API (Railway)** : https://newsfoundry-production-35c3.up.railway.app/docs

## Fonctionnalités Principales

*   **Assistant Conversationnel** : Un chat interactif capable de répondre aux questions sur l'actualité en s'appuyant sur un contexte quotidien.
*   **Recherche et Extraction d'Articles** : Utilisation d'outils IA pour rechercher des articles en temps réel et en extraire le texte intégral.
*   **Génération de Revues de Presse (RAG)** : Création de synthèses structurées basées sur les articles lus par l'IA au cours de la discussion, grâce à une vectorisation du contenu.
*   **Authentification Sécurisée** : Système de connexion par token JWT avec hachage des mots de passe.
*   **Interface Réactive** : Design moderne, gestion des états de chargement optimistes et alertes visuelles.

## Architecture du Projet

Le projet est divisé en deux environnements distincts pour séparer la logique métier de l'interface utilisateur.

```text
├── frontend/                 # Application Next.js (React)
│   ├── src/app/page.tsx      # Vue principale (Chat, historique, modale de revue)
│   └── src/app/login/        # Page d'authentification
│
├── backend/                  # API REST en Python (FastAPI)
│   ├── src/main.py           # Déclaration des routes (Auth, Chats, Revues, RAG LlamaIndex)
│   ├── src/agent.py          # Configuration des agents PydanticAI et de leurs outils
│   ├── src/models.py         # Schémas de base de données (SQLModel) et de sortie (Pydantic)
│   ├── src/database.py       # Configuration PostgreSQL et seeding
│   ├── src/auth.py           # Logique de sécurité (JWT, bcrypt)
│   └── src/test_chats.py     # Tests d'intégration automatisés
```

## Choix Techniques & Justification

*   **Backend (FastAPI & SQLModel)** : FastAPI a été choisi pour sa rapidité d'exécution, son support natif de l'asynchrone (crucial pour éviter les blocages lors des appels LLM) et sa validation de données via Pydantic. SQLModel simplifie les interactions avec PostgreSQL en unifiant la définition des tables et la validation des données.
*   **Frontend (Next.js & Tailwind CSS)** : Next.js offre un routage simple et performant. L'interface utilise Tailwind pour un prototypage rapide, garantissant une stricte fidélité aux maquettes tout en conservant une architecture de composants "Client" pour la réactivité de l'interface.
*   **Orchestration IA (PydanticAI)** : PydanticAI garantit que le modèle renvoie des données strictement typées (JSON structuré) pour la revue de presse, évitant ainsi les erreurs de parsing côté frontend.
*   **Pipeline RAG (LlamaIndex)** : L'utilisation de LlamaIndex permet de vectoriser et d'extraire sémantiquement les extraits pertinents des articles longs préalablement lus par l'agent. Cela évite de saturer la fenêtre de contexte du LLM tout en enrichissant factuellement la revue de presse.
*   **Modèle LLM (Mistral)** : Utilisation de `open-mistral-nemo` pour son excellent ratio performance/coût et sa compréhension nuancée des instructions en français.

## Stratégie de Prompting

Les instructions système (system prompts) ont été conçues pour limiter les hallucinations et formater les sorties :
*   **Agent Interactif** : L'instruction d'afficher les URL en texte brut à la fin des messages (interdiction absolue du format Markdown `[texte](url)`) assure que l'utilisateur peut toujours copier les liens sources sans que l'interface ne casse le rendu.
*   **Agent Revue de Presse** : L'adoption d'un persona ("Journaliste rédacteur en chef expert") conditionne le modèle à adopter un ton synthétique et professionnel. L'obligation stricte de répondre au format JSON garantit la stabilité de l'affichage web.

## Gestion des Erreurs API

Le backend expose des codes HTTP standards gérés nativement par FastAPI, reflétant précisément l'état de l'application :

| Code HTTP | État           | Cas d'usage & Comportement                                                                      |
| :-------- | :------------- | :---------------------------------------------------------------------------------------------- |
| **401**   | Unauthorized   | Identifiants incorrects ou token manquant/expiré lors des requêtes.                             |
| **404**   | Not Found      | Tentative d'accès à un Chat inexistant ou appartenant à un autre utilisateur (prévention IDOR). |
| **500**   | Internal Error | Panne de la WorldNewsAPI, échec de vectorisation LlamaIndex ou refus de réponse du LLM.         |

## Tests & Déploiement Continu (CI/CD)

Une suite de tests d'intégration a été implémentée avec `pytest` et `TestClient`. Elle valide la logique d'autorisation, garantissant l'accès légitime d'un utilisateur à ses données tout en confirmant le blocage strict des tentatives d'accès aux ressources tierces.

Ces tests sont exécutés automatiquement via GitHub Actions à chaque nouveau commit sur la branche principale, assurant la non-régression du code avant tout déploiement. L'intégration continue utilise `uv` d'Astral pour une installation ultra-rapide des dépendances.

## Prérequis et Installation Locale

Pour exécuter ce projet localement, assurez-vous de disposer de Python 3.13+, de Node.js 18+, et du gestionnaire de paquets `uv` (Astral).

**1. Configuration du Backend**
```bash
cd backend
# Utilisation de uv pour synchroniser les dépendances et créer l'environnement virtuel automatiquement
uv sync
# Lancement du serveur FastAPI
uv run uvicorn src.main:app --reload
```

**2. Configuration du Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Variables d'Environnement

Pour le bon fonctionnement de l'application en local, créez un fichier `.env` dans le dossier `backend/` et un fichier `.env.local` dans le dossier `frontend/`.

**Backend (`backend/.env`) :**
```env
DATABASE_URL="postgresql://utilisateur:motdepasse@localhost:5432/newsfoundry" # Ou sqlite:///database.db
JWT_SECRET="votre_cle_secrete_jwt"
WORLD_NEWS_API_KEY="votre_cle_api_worldnews"
MISTRAL_API_KEY="votre_cle_api_mistral"
```

**Frontend (`frontend/.env.local`) :**
```env
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

---

**Lancement des tests locaux (Backend) :**
```bash
cd backend
# Exécution de pytest via l'environnement géré par uv
uv run pytest src/test_chats.py
```