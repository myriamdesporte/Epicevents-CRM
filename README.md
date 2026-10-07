# Epic Events CRM

Application CRM interne en ligne de commande pour Epic Events, entreprise d'organisation d'événements.

Elle permet de gérer les collaborateurs, les clients, les contrats et les événements selon le département de 
chaque collaborateur.

---

## Environnement technique

Architecture back-end sécurisée avec **Python**, **PostgreSQL** et **SQLAlchemy**.

La base de données et son outil d'administration tournent dans **Docker**.

L'application Python s'exécute dans un **environnement virtuel** sur la machine et se connecte à la 
base via `localhost:5433`.

---

## Prérequis

- **Python 3.14**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inclut Docker Compose)

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/myriamdesporte/Epicevents-CRM.git
cd Epicevents-CRM
```

### 2. Activer l'environnement virtuel

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate 
# Windows
venv\Scripts\activate
```

### 3. Installer les dépendances Python
```bash
pip install -r requirements.txt
```


## Configuration

Le dépôt ne contient **aucun secret**. Copier le modèle et remplacer les valeurs notées `changeme` :

```bash
cp .env.example .env
```

Les variables attendues dans `.env` :

| Variable                  | Rôle                                                                |
|---------------------------|---------------------------------------------------------------------|
| `POSTGRES_ADMIN_USER`     | Compte administrateur PostgreSQL (conteneur)                        |
| `POSTGRES_ADMIN_PASSWORD` | Mot de passe superutilisateur `postgres`(administration uniquement) |
| `PGADMIN_EMAIL`           | Identifiant de connexion à l'interface web pgAdmin                  |
| `PGADMIN_PASSWORD`        | Mot de passe pgAdmin                                                |
| `DB_USER`                 | Compte applicatif utilisé par l'application                         |
| `DB_PASSWORD`             | Mot de passe du compte applicatif `epicevents_app`                  |
| `DB_HOST`                 | Hôte de la base (`localhost`)                                       |
| `DB_PORT`                 | Hôte de la base (`5433`)                                            |
| `DB_NAME`                 | Nom de la base (`epicevents`)                                       |
| `JWT_SECRET`              | Secret de signature des jetons de session (32 caractères minimum)   |
| `SENTRY_DSN`              | Adresse d'envoi des rapports Sentry (facultative)                   |


Pour générer une clé secrète ou un jeton aléatoire :

```bash
 python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Les variables `DB_HOST=localhost` et `DB_PORT=5433` permettent à l'application Python 
(exécutée sur la machine) de joindre la base de données conteneurisée.

⚠️ Le fichier `.env` est ignoré par Git (`.gitignore`) et ne doit **jamais** être versionné.

## Mise en place de la base de données

### 1. Démarrer PostgreSQL et pgAdmin

```bash
docker compose up -d
```

Au premier lancement, Docker télécharge les images `postgres:17`et `dpage/pgadmin`,
puis initialise la base `epicevents` avec les valeurs du `.env`.

PostgreSQL écoute sur le port **5433** de la machine hôte.
pgAdmin est accessible sur <http:/localhost:8080>.

Vérifier que les deux conteneurs tournent :

```bash
docker compose ps
```

→ `epicevents_db` et `epicevents_pgadmin` doivent être à l'état `Up`.  

### 2. Créer le compte applicatif (moindre privilège)

L'application ne se connecte **jamais** avec le superutilisateur.

Un rôle dédié `epicevents_app`, limité aux opérations CRUD, doit être créé **une seule fois** en 
exécutant `scripts/init_app_user.sql` en tant qu'administrateur.

Le script contient un placeholder `<APP_PASSWORD>` : le remplacer par la valeur de `DB_PASSWORD`
du `.env` avant exécution.

**Option A : en ligne de commande**

```bash
cp scripts/init_app_user.sql scripts/init_app_user_local.sql
# Éditer init_app_user_local.sql : remplacer <APP_PASSWORD> par le DB_PASSWORD
docker compose exec -T db psql -U postgres -d epicevents < scripts/init_app_user_local.sql
# Supprimer le fichier scripts/init_app_user_local.sql (pour ne pas versionner les secrets)
rm scripts/init_app_user_local.sql
```

**Option B : via pgAdmin**

1. Ouvrir http://localhost:8080 et se connecter (identifiants pgAdmin du `.env`)
2. Enregistrer le serveur : clic droit sur *Servers* → *Register* → *Server...* puis onglet *Connection* 
   - Host : `db`
   - Port : `5432`
   - Maintenance database : `epicevents` 
   - Username : `postgres`
   - Password : votre `POSTGRES_ADMIN_PASSWORD`.
3. Ouvrir un *Query Tool* sur la base `epicevents`, coller le contenu du script `scripts/init_app_user.sql`
   avec votre `DB_PASSWORD` à la place du placeholder et exécuter. 


### 3. Vérifier la connexion

```bash
python check_connection.py
```

→ doit afficher la version de PostgreSQL et le compte utilisé `Utilisateur : epicevents_app`.

### 4. Créer les tables et les rôles

Une fois les dépendances installées et la base démarrée, générer les tables à partir des modèles SQLAlchemy :


```bash
python init_db.py 
```

→ doit afficher `Tables created successfully`.

Le script créé les cinq tables et insère les trois rôles (`sales`, `support`, `management`).

Vérifier la présence des tables :

- via **psql** : `docker compose exec db psql -U epicevents_app -d epicevents -c "\dt"`
- via **pgAdmin** : rafraîchir le serveur puis déplier *epicevents* → *Schémas* → *public* → *tables*

→ doit afficher les quatre tables : `users`, `clients`, `contracts`, `events` 

### 5. Créer le premier collaborateur

Aucun collaborateur n'existe encore, donc personne ne peut se connecter pour en créer un.

Ce script permet de créer un premier collaborateur du département gestion:

```bash
python create_first_user.py
```

### 6. Remplir la base avec un jeu de démonstration *(facultatif)*

```bash
python seed_demo_data.py
```

Le script demande un seul mot de passe partagé par tous les comptes qu'il crée puis affiche
la liste des identifiants. Le compte de gestion créé à l'étape précédente n'est pas touché.

Pour rejouer le script :

```bash
python seed_demo_data.py --reset
```

---

## Utilisation

L'application s'éxecute avec `python -m epicevents menu`.

```bash
python -m epicevents --help   # La liste des commandes
python -m epicevents login    # Ouvrir une session
python -m epicevents whoami   # Voir la session en cours
python -m epicevents logout   # Fermer la session
```

### 1. Deux façons d'utiliser l'application

```bash
python -m epicevents menu
```

Le **menu** affiche les actions disponibles et les enchaine sans nécessité de connaître les commandes.

Il propose la connexion au démarrage s'il n'y a pas de session en cours.

Les **commandes** restent disponibles pour aller plus vite ou pour écrire un script. 

```bash
python -m epicevents client
Options:
  --help  Show this message and exit.
Commands:
  create  Create a client.
  list    List the clients.
  show    Show every field of one client.
  update  Update one of your own clients.
```

Les deux interfaces appellent **exactement les mêmes services** : mêmes règles, mêmes validations, mêmes affichages.


### 2. Consulter les données

Tous les collaborateurs ont accès en lecture seule à toutes les données, comme le prévoit le cahier des charges.

```bash
python -m epicevents client list
python -m epicevents client --mine   # Mes clients

python -m epicevents contract list
python -m epicevents contract list --unsigned   # Contrats non signés
python -m epicevents contract list --unpaid     # Restant à payer
python -m epicevents contract list --mine     # Les contrats de mes clients

python -m epicevents event list
python -m epicevents event list --no-support  # Événement sans support assigné
python -m epicevents event list --mine    # Événements qui me sont assignés
```

Les listes donnent l'essentiel ; la commande `show` donne **tous** les champs d'une fiche :

```bash
python -m epicevents clients show 1
python -m epicevents contract show 2
python -m epicevents event show 3
```

### 3. Créer et modifier 

Chaque commande vérifie d'abord que **le rôle** autorise l'action, puis que le collaborateur a le droit d'agir **sur 
cet objet précis**.

```bash
# Gestion : les collaborateurs et les contrats
python -m epicevents user create
python -m epicevents user update 3 --role support
python -m epicevents user delete 3
python -m epicevents contract create --client-id 1 --total-amount 1000 --amount-due 1000
python -m epicevents contract sign 2

# Commercial : ses clients, et les événements de ses contrats signés
python -m epicevents client create
python -m epicevents client update 1 --phone "+33 6 12 34 56 78"
python -m epicevents event create --contract-id 2 --name "Mariage" \
    --start "2026-06-04 13:00" --end "2026-06-05 02:00" \
    --location "Cande-sur-Beuvron" --attendees 75

# Gestion : affecter un support à un événement
python -m epicevents event assign-support 1 --user-id 4

# Support : ses propres événements
python -m epicevents event update 1 --attendees 200
```

### 4. Sécurité

Les mots de passe sont **toujours demandés au clavier**, jamais acceptés comme
option, ni à la création d'un collaborateur ni au changement de mot de passe.

Une commande de mise à jour ne modifie que les champs donnés : une option omise
laisse la valeur existante inchangée.

À la connexion, un jeton est écrit dans `~/.epicevents/token`. Tant qu'il est
valide, les commandes suivantes ne redemandent pas les identifiants.

---

## Structure du projet

```
epicevents/
├── __main__.py          Point d'entrée : python -m epicevents
│
│                        Modules transverses, utilisés par plusieurs couches :
├── config.py            Lecture des variables d'environnement
├── database.py          Moteur SQLAlchemy, sessions, Base déclarative
├── exceptions.py        Exceptions communes liées à l'authentification et aux autorisations.
├── monitoring.py        Journalisation vers Sentry (seul fichier important sentry_sdk)
├── permissions.py       Matrice rôle → actions autorisées
├── security.py          Hachage et vérification des mots de passe
├── validators.py        Vérification et nettoyage des valeurs saisies
│
├── models/              Structure des données — le « Model » de MVC
│   ├── base.py          ModelBase : id, created_at, updated_at
│   ├── role.py          Role + RoleName
│   ├── user.py          User + set_password / check_password
│   ├── client.py        Client
│   ├── contract.py      Contract
│   └── event.py         Event
│
├── repositories/        Accès aux données : le seul endroit qui interroge la base
│   ├── base.py          list_all(), get(), add(), update(), delete()
│   ├── role.py          + get_by_name()
│   ├── user.py          + get_by_email(), get_by_employee_number()
│   ├── client.py        + list_for_sales_contact()
│   ├── contract.py      + list_unsigned(), list_not_fully_paid()
│   └── event.py         + list_without_support(), list_for_support_contact()
│
├── services/            Règles métier : droit, propriété, validation, écriture
│   ├── auth.py          Authentification par jeton et autorisation
│   ├── user.py          Créer / modifier / supprimer un collaborateur
│   ├── client.py        Créer / modifier un client
│   ├── contract.py      Créer / modifier / signer un contrat
│   └── event.py         Créer un événement, affecter un support
│
├── controllers/         Le « Controller » : lit la saisie, appelle, délègue
│   ├── main.py          Groupe de commandes click
│   ├── errors.py        Que faire quand une commande échoue
│   ├── guards.py        Refuse une commande avant qu'elle ne pose ses questions
│   ├── options.py       Ne retient que les options réellement saisies
│   ├── menu.py          Menu interactif, qui pilote les commandes existantes
│   ├── auth.py          login / logout / whoami
│   ├── user.py          user list / create / update / delete
│   ├── client.py        client list / show / create / update
│   ├── contract.py      contract list / show / create / update / sign
│   └── event.py         event list / show / create / update / assign-support
│
├── views/               La « View » : mise en forme uniquement
│   ├── console.py       Briques d'affichage (seul fichier important rich)
│   ├── user.py          Collaborateurs, messages de session
│   ├── client.py        Liste, fiche détaillée et confirmations
│   ├── contract.py      Idem pour un contrat
│   └── event.py         Idem pour un événement
│
├── tests/
│   ├── unit/              # Tests unitaires
│   └── integration/       # Tests d'intégration
│ 
├── scripts/
│   └── init_app_user.sql    Création du rôle applicatif (moindre privilège)
│ 
├── init_db.py               Création des tables et des rôles
├── check_connection.py      Vérification de la connexion
├── create_first_user.py     Amorçage du premier collaborateur
├── seed_demo_data.py        Jeu de données de démonstration (facultatif)
│ 
├── requirements.txt         Liste des dépendances Python du projet
└── docker-compose.yaml      PostgreSQL + pgAdmin
```
