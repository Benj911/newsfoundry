NewsFoundry - Assistant d'Actualités IA & Revue de Presse

NewsFoundry est une application web permettant d'interagir avec un assistant d'actualités intelligent. Propulsée par l'IA, l'application recherche des articles récents, extrait leur contenu complet et génère des revues de presse structurées (RAG) à partir de l'historique de discussion.

🔗 Liens de Production

Frontend (Vercel) : (https://newsfoundry-aiwm04erv-benj911s-projects.vercel.app/)
Backend & BDD (Railway) : https://newsfoundry-production-35c3.up.railway.app

📂 Architecture du Projet

Le projet est divisé en deux environnements distincts pour séparer la logique métier de l'interface utilisateur.
frontend/ : Application Next.js (React).
  src/app/page.tsx : Vue principale contenant la logique de discussion, les onglets et la modale de génération de revue.
  src/app/login/page.tsx : Page d'authentification.

backend/ : API REST en Python (FastAPI).
  src/main.py : Déclaration des routes API (Authentification, Chats, Revues de presse) et implémentation du pipeline RAG LlamaIndex.
  src/agent.py : Configuration des agents PydanticAI (Agent interactif avec outils, Agent de synthèse) et injection des dépendances.
  src/models.py : Schémas de base de données (SQLModel) et structures de sortie (Pydantic).
  src/database.py & src/auth.py : Connexion PostgreSQL et gestion des tokens JWT.
  
🛠 Choix Techniques & Justification

Backend (FastAPI & SQLModel) : FastAPI a été choisi pour sa rapidité d'exécution, son support natif de l'asynchrone (crucial pour les appels LLM) et sa validation de données via Pydantic. SQLModel simplifie les interactions avec PostgreSQL en unifiant les modèles de données et de validation.

Frontend (Next.js & Tailwind CSS) : Next.js offre un routage simple et performant. L'interface utilise Tailwind pour un prototypage rapide et respecte une architecture de composants "Client" pour la réactivité de l'UI (loaders, gestion d'états dynamiques).

Orchestration IA (PydanticAI) : PydanticAI garantit que le LLM renvoie des données strictement typées (JSON structuré) pour la revue de presse, évitant ainsi les erreurs de parsing côté frontend.

Pipeline RAG (LlamaIndex) : L'utilisation de LlamaIndex permet d'extraire sémantiquement les extraits pertinents des articles longs préalablement lus, évitant de saturer la fenêtre de contexte du modèle tout en enrichissant la revue de presse finale. 

Modèle LLM (Mistral) : Utilisation de open-mistral-nemo pour son excellent ratio performance/coût et sa bonne compréhension des instructions en français.

🧠 Stratégie de PromptingLes prompts système ont été conçus pour limiter les hallucinations et structurer fermement les sorties :

Agent Interactif : L'instruction d'afficher les URL en texte brut (interdiction du format [texte](url)) assure que l'utilisateur peut copier les liens et que l'interface ne casse pas l'affichage avec le parseur Markdown.

Agent Revue de Presse : L'adoption d'un persona ("Journaliste rédacteur en chef expert") pousse le modèle à adopter un ton synthétique et professionnel. L'obligation de répondre uniquement via le format JSON strict garantit la stabilité de l'application web.

⚠️ Gestion des Erreurs API
Le backend expose des erreurs HTTP claires gérées nativement par FastAPI :
Code HTTP       Cas d'usage               Message / Comportement

401             Unauthorized              Identifiants incorrects ou token manquant/expiré lors du login.

404             Not Found                 Tentative d'accès à un Chat qui n'existe pas ou qui appartient à un autre utilisateur.

500             Internal Server Error     Panne de l'API WorldNewsAPI, échec de parsing LlamaIndex ou refus de réponse structurée du LLM.

🧪 Tests & Déploiement Continu
Une suite de tests a été implémentée pour garantir la validité de la logique d'autorisation (accès légitime vs interdiction d'accès aux ressources tierces).
Ces tests sont exécutés automatiquement via GitHub Actions (CI/CD) à chaque commit sur la branche main.
Pour lancer les tests localement (Bash) :
cd backend
uv run pytest

🚀 Optimisation des Performances
Piste d'amélioration          Détails

Métrique                      Temps de création d'une nouvelle discussion (Actuellement ~1500ms).

Diagnostic                    À chaque POST /chats, le backend appelle WorldNewsAPI en synchrone pour injecter l'actualité du jour, 
                              bloquant la réponse UI.

Implémentation                Mise en cache du résultat de fetch_daily_news() avec alru_cache ou Redis. 
                              L'actualité globale ne changeant pas chaque  seconde, un TTL (Time To Live) de 1 heure est suffisant.

Objectif Mesurable            Réduire la latence de création d'un chat à < 100ms pour une expérience utilisateur instantanée.