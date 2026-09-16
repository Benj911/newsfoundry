# Analyse et Optimisation des Performances

**1. Streaming des réponses du Chat (Fluidité UX)**
*   **Observation :** Actuellement, l'utilisateur attend de 3 à 8 secondes face à un indicateur de chargement avant de voir la réponse de l'IA. Selon les standards d'interface, une attente supérieure à 1 ou 2 secondes sans feedback textuel dégrade considérablement l'expérience utilisateur.
*   **Objectif :** Réduire le temps de première réponse (Time To First Byte - TTFB) à moins de 300 millisecondes en affichant la réponse mot par mot.
*   **Implémentation :**
    *   **Backend :** Remplacer l'appel asynchrone classique `agent.run()` par `agent.run_stream()` dans FastAPI. Utiliser une `StreamingResponse` pour renvoyer les morceaux de texte (*chunks*) au fur et à mesure de leur génération par Mistral.
    *   **Frontend :** Modifier la requête Next.js pour consommer ce flux via l'API Web Streams ou les Server-Sent Events (SSE), et mettre à jour l'état du message en temps réel.

**2. Réduction du temps de génération de la Revue de Presse**
*   **Observation :** La génération de la revue prend entre 10 et 20 secondes. Cette latence augmente drastiquement en fonction de la longueur de l'historique et du nombre d'articles lus, car l'extraction de texte et la vectorisation LlamaIndex se font de manière bloquante au moment du clic sur le bouton "Générer".
*   **Objectif :** Maintenir un temps de génération sous les 10 secondes, indépendamment du nombre de sources accumulées.
*   **Implémentation :** 
    *   **Vectorisation asynchrone :** Déplacer le téléchargement et l'intégration LlamaIndex dans une tâche de fond (`BackgroundTasks` de FastAPI). Dès que l'utilisateur demande à lire un article dans le chat, le système le vectorise en arrière-plan sans attendre la création de la revue.
    *   **Résumé périodique :** Si une discussion dépasse 15 messages, utiliser l'IA pour générer un condensé invisible de l'historique afin de réduire la charge de contexte (et les coûts en tokens) lors de la génération finale.

**3. Observabilité et Tracing avec MLflow (MLOps)**
*   **Observation :** En cas de lenteur inexpliquée, l'architecture actuelle est opaque. Il est impossible de déterminer visuellement si la latence provient du réseau (WorldNewsAPI), de la base de données PostgreSQL, ou du modèle d'IA (Mistral).
*   **Objectif :** Obtenir des métriques granulaires sur le temps d'exécution de chaque étape et sur la consommation de tokens pour cibler les efforts de refactoring.
*   **Implémentation :**
    *   Intégrer la librairie `mlflow` au backend.
    *   Activer le tracing automatique de PydanticAI via `mlflow.pydantic_ai`.
    *   Exploiter l'interface locale MLflow pour visualiser les *spans* temporels de chaque appel d'outil et analyser les éventuelles dégradations de performance au fil du temps.

**4. Mise en cache globale des actualités (Cron Job)**
*   **Observation :** Actuellement, la création d'une nouvelle discussion déclenche un appel synchrone à WorldNewsAPI. Sachant que l'actualité mondiale ne change pas chaque minute, interroger l'API en boucle ralentit l'expérience utilisateur (~2 secondes d'attente) et consomme inutilement le quota de requêtes.
*   **Objectif :** Rendre la création de discussion instantanée (< 50ms) et diviser les coûts d'API drastiquement.
*   **Implémentation :** Intégrer un planificateur de tâches (comme `APScheduler` ou `FastAPI-Utils`) pour interroger WorldNewsAPI une seule fois par heure en arrière-plan. Le résultat sera stocké en mémoire cache (Redis) ou dans une table de configuration de la base PostgreSQL. La route `POST /chats` se contentera de lire cette donnée pré-chargée de manière instantanée.

**5. Pagination des messages (Lazy Loading)**
*   **Observation :** Actuellement, l'intégralité de l'historique d'une discussion est chargée en une seule requête. Pour de longues conversations (ex: +50 messages), cela ralentit le rendu frontend, augmente le poids du payload JSON et surcharge la mémoire côté serveur.
*   **Objectif :** Réduire le poids des requêtes API et accélérer l'affichage initial des discussions.
*   **Implémentation :** Utiliser `limit` et `offset` dans les requêtes SQLModel pour charger uniquement les 20 derniers messages. Côté Next.js, implémenter un défilement infini (infinite scroll) pour récupérer les messages plus anciens dynamiquement lorsque l'utilisateur remonte dans l'historique.

**6. Optimisation de la Base de Données (Connection Pooling)**
*   **Observation :** Si le trafic augmente, le backend risque d'ouvrir une multitude de connexions simultanées vers PostgreSQL. Cela peut saturer rapidement les limites d'une instance de base de données gratuite (comme celle de Railway) et provoquer des crashs.
*   **Objectif :** Maintenir la stabilité du backend sous charge et réduire la latence liée à l'ouverture de nouvelles connexions.
*   **Implémentation :** Configurer le moteur de base de données SQLAlchemy/SQLModel avec des paramètres `pool_size` et `max_overflow`. Le système recyclera un pool de connexions existantes partagées entre les utilisateurs au lieu d'en ouvrir et fermer de nouvelles en permanence.

**7. Délégation asynchrone des tâches longues (Task Queue)**
*   **Observation :** La génération de la revue de presse maintient la requête HTTP ouverte pendant 10 à 20 secondes. Sur la majorité des hébergeurs, si l'IA tarde trop, le serveur coupe la connexion d'office (erreur "Timeout") et l'utilisateur perd son résultat.
*   **Objectif :** Sécuriser la génération des contenus longs et éviter totalement les erreurs de déconnexion forcée.
*   **Implémentation :** Déporter l'exécution de la revue de presse vers un "Worker" en arrière-plan (via Celery ou Redis Queue). La route API répondrait immédiatement un statut HTTP 202 "Génération en cours". Le frontend interrogerait ensuite le backend toutes les 3 secondes (polling) ou utiliserait des WebSockets pour afficher le résultat dès qu'il est prêt.