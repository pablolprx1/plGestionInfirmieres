# API de Gestion des Visites Infirmières

Cette API permet de gérer les visites entre infirmières et patients dans un système de soins à domicile.

## Structure du Projet

```
.
├── main.py              # Point d'entrée de l'application
├── requirements.txt     # Dépendances du projet
├── app/
│   ├── __init__.py     # Initialisation du package
│   ├── api/
│   │   ├── __init__.py
│   │   ├── visites.py      # Gestion des visites
│   │   ├── patients.py     # Gestion des patients
│   │   ├── infirmieres.py  # Gestion des infirmières
│   │   └── auth.py         # Authentification
│   ├── models/
│   │   └── models.py       # Modèles de données
│   ├── security/
│   │   └── security.py     # Sécurité et authentification
│   ├── utils.py            # Utilitaires
│   └── database.py         # Configuration de la base de données
└── README.md              # Documentation du projet
```

## Configuration Principale

### Fichier main.py
Le fichier principal qui configure l'application FastAPI. Il définit les routes principales et inclut les différents routeurs pour la gestion des visites et l'authentification.

### Configuration de la Base de Données (database.py)
Configuration de la connexion à la base de données MySQL avec un pool de connexions pour optimiser les performances. Les paramètres de connexion incluent l'utilisateur, le mot de passe, l'hôte et le nom de la base de données.

### Modèles de Données (models.py)
Définition des modèles Pydantic pour la validation des données :
- `Infirmiere` : Informations sur les infirmières
- `Personne` : Informations de base sur les personnes (patients et infirmières)
- `Visite` : Détails des visites entre infirmières et patients

### Sécurité (security.py)
Gestion de l'authentification et de la sécurité :
- Configuration JWT pour les tokens d'authentification
- Fonctions de hachage des mots de passe
- Gestion des tokens d'accès
- Vérification des rôles et des permissions

## Endpoints de l'API

### 1. Authentification (`/token`)
- **POST** `/token`
- **Description**: Authentification des utilisateurs
- **Body**: Login et mot de passe
- **Réponse**: Token JWT pour l'authentification

### 2. Gestion des Visites (`/api/visites`)

#### Récupérer toutes les visites
- **GET** `/api/visites/`
- **Description**: Récupère toutes les visites de l'utilisateur connecté (infirmière ou patient)
- **Authentification**: Requise
- **Rôles**: Infirmière, Patient

#### Récupérer une visite spécifique
- **GET** `/api/visites/{visite_id}`
- **Description**: Récupère les détails d'une visite spécifique
- **Authentification**: Requise
- **Rôles**: Infirmière, Patient

#### Récupérer toutes les visites (Infirmière en chef)
- **GET** `/api/visites/all`
- **Description**: Récupère toutes les visites (accès réservé aux infirmières en chef)
- **Authentification**: Requise
- **Rôles**: Infirmière en chef

#### Créer une nouvelle visite
- **POST** `/api/visites/`
- **Description**: Crée une nouvelle visite
- **Authentification**: Requise
- **Rôles**: Infirmière, Patient

#### Mettre à jour une visite
- **PUT** `/api/visites/{visite_id}`
- **Description**: Met à jour les informations d'une visite
- **Authentification**: Requise
- **Rôles**: Infirmière, Patient

#### Supprimer une visite
- **DELETE** `/api/visites/{visite_id}`
- **Description**: Supprime une visite
- **Authentification**: Requise
- **Rôles**: Infirmière, Patient

## Sécurité

- Tous les endpoints nécessitent une authentification via JWT
- Les rôles sont vérifiés pour chaque opération
- Les infirmières ne peuvent accéder qu'à leurs propres visites
- Les patients ne peuvent accéder qu'à leurs propres visites
- Les infirmières en chef ont accès à toutes les visites

## Exemples de Tests Postman

### Collection Postman
1. Créez une nouvelle collection dans Postman
2. Configurez une variable d'environnement `base_url` avec la valeur `http://localhost:8000`
3. Configurez une variable d'environnement `token` pour stocker votre token JWT

### Authentification
1. Obtenez un token JWT via l'endpoint d'authentification
2. Stockez le token dans la variable d'environnement `token`
3. Utilisez le token dans l'en-tête `Authorization: Bearer {{token}}` pour tous les appels API

## Gestion des Erreurs

L'API renvoie les codes d'erreur HTTP suivants :
- 400: Requête invalide
- 401: Non authentifié
- 403: Accès refusé
- 404: Ressource non trouvée
- 500: Erreur serveur

## Démarrage

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurez la base de données dans `database.py`

3. Lancez le serveur :
```bash
uvicorn main:app --reload
```

4. Accédez à la documentation Swagger :
```
http://localhost:8000/docs
```

## Dépendances Requises

```txt
fastapi==0.68.0
uvicorn==0.15.0
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.5
mysql-connector-python==8.0.26
pydantic==1.8.2
``` 