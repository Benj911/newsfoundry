# Roadmap d'Améliorations et d'Optimisations

Ce document dresse le bilan des axes d'amélioration techniques de NewsFoundry. Il identifie les goulots d'étranglement actuels (bottlenecks) et propose des solutions architecturales pour préparer l'application à une mise en production à grande échelle.

## 1. Expérience Utilisateur (UX) et Interface

**A. Streaming des réponses du Chat (Fluidité UX)**
*   **Observation :** Actuellement, l'utilisateur patiente 3 à 8 secondes face à un indicateur de chargement avant l'affichage complet de la réponse. Une attente supérieure à 2 secondes sans feedback textuel dégrade considérablement l'expérience utilisateur.
*   **Objectif :** Réduire le temps de première réponse (Time To First Byte - TTFB) à moins de 300 millisecondes.
*   **Implémentation :** Remplacer l'appel asynchrone classique par `agent.run_stream()` côté FastAPI. Utiliser les Server-Sent Events (SSE) ou l'API Web Streams côté Next.js pour afficher les *chunks* générés par le LLM en temps réel (effet machine à écrire).

**B. Pagination des messages (Lazy Loading)**
*   **Observation :** L'intégralité de l'historique d'une discussion est chargée en une seule requête. Pour de longues conversations, cela ralentit le rendu frontend et alourdit le payload JSON.
*   **Objectif :** Réduire le poids des requêtes API et accélérer l'affichage initial de l'interface.
*   **Implémentation :** Utiliser `limit` et `offset` dans les requêtes SQLModel pour charger uniquement les 20 derniers messages. Côté React, implémenter un défilement infini (Infinite Scroll) pour récupérer l'historique dynamiquement.

## 2. Architecture IA et Pipeline RAG

**A. Vectorisation asynchrone en arrière-plan**
*   **Observation :** La génération de la revue prend entre 10 et 20 secondes car l'extraction de texte et la vectorisation LlamaIndex se font de manière bloquante au moment du clic.
*   **Objectif :** Lisser la charge de traitement pour maintenir un temps de génération sous les 10 secondes.
*   **Implémentation :** Déplacer le téléchargement et l'intégration LlamaIndex dans des `BackgroundTasks` de FastAPI. Dès que l'agent lit une URL dans le chat, le système la vectorise instantanément en arrière-plan. 

**B. Condensation périodique du contexte**
*   **Observation :** Les requêtes deviennent plus lentes et coûteuses à mesure que l'historique s'allonge (saturation de la fenêtre de contexte).
*   **Implémentation :** Au-delà de 15 messages, utiliser l'IA pour générer un résumé synthétique invisible de l'historique. Ce résumé remplacera les anciens messages dans le prompt, réduisant la consommation de tokens.

## 3. Optimisations Backend et Infrastructure

**A. Délégation asynchrone des tâches longues (Task Queue)**
*   **Observation :** La génération de la revue de presse maintient une connexion HTTP ouverte pendant de longues secondes, risquant un "Timeout" 504 de la part de l'hébergeur (Vercel/Railway).
*   **Objectif :** Sécuriser la génération des contenus longs.
*   **Implémentation :** Déporter l'exécution vers un *Worker* (via Celery ou Redis Queue). L'API répondrait immédiatement un statut HTTP 202 "Accepted". Le frontend interrogerait ensuite le backend par *polling* ou via des WebSockets pour récupérer le résultat.

**B. Mise en cache globale des actualités (Cron Job)**
*   **Observation :** La création d'un chat déclenche un appel synchrone vers WorldNewsAPI. L'actualité ne changeant pas chaque minute, interroger l'API en boucle est inutile et coûteux.
*   **Objectif :** Rendre la création de discussion instantanée (< 50ms).
*   **Implémentation :** Intégrer un planificateur (ex: APScheduler) pour interroger l'API externe une fois par heure. Le résultat sera stocké en cache (Redis ou PostgreSQL). La route `POST /chats` lira cette donnée pré-chargée sans latence.

**C. Optimisation de la base de données (Connection Pooling)**
*   **Observation :** Une forte charge de trafic risque de multiplier les ouvertures de connexions vers PostgreSQL, saturant les limites de l'instance.
*   **Implémentation :** Configurer SQLAlchemy avec les paramètres `pool_size` et `max_overflow` pour recycler un bassin de connexions partagées.

## 4. Observabilité et MLOps

**A. Tracing granulaire avec MLflow**
*   **Observation :** En cas de lenteur inexpliquée, l'architecture actuelle rend difficile l'identification du coupable (API tierce, base de données, ou modèle LLM).
*   **Objectif :** Obtenir des métriques précises sur les temps d'exécution et la consommation de tokens.
*   **Implémentation :** Intégrer `mlflow.pydantic_ai`. Exploiter l'interface MLflow pour visualiser les *spans* temporels de chaque outil appelé et monitorer les dégradations de performance au fil du temps.