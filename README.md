# OpenChemFacts API

API FastAPI pour accéder aux données d'écotoxicologie (ecotox) et générer des graphiques de distribution de sensibilité des espèces (SSD).

## Description

Cette API permet d'accéder aux données d'écotoxicologie stockées dans un fichier Parquet et de générer des visualisations interactives avec Plotly :
- Distribution de sensibilité des espèces (SSD) et calcul de HC20
- Résultats EC10eq par taxon et espèce
- Comparaison de plusieurs substances

## Prérequis

- Python 3.11.9
- Git
- Compte Scalingo (pour le déploiement)

## Installation locale

1. Cloner le dépôt :
```bash
git clone <url-du-repo>
cd backend
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Vérifier que le fichier de données est présent :
```bash
ls data/results_ecotox_*.parquet
```

5. Lancer l'application :
```bash
uvicorn app.main:app --reload
```

L'API sera accessible sur `http://localhost:8000`

## Endpoints disponibles

### Santé de l'API
- `GET /health` - Vérification de l'état de l'API

### Données
- `GET /api/summary` - Résumé des données (nombre de lignes, colonnes, noms des colonnes)
- `GET /api/by_column?column=<nom_colonne>` - Valeurs uniques d'une colonne
- `GET /api/cas/list` - Liste de tous les numéros CAS disponibles avec leurs noms chimiques

### Graphiques
- `GET /api/plot/ssd/{cas}` - Graphique SSD et HC20 pour un produit chimique
  - Exemple : `GET /api/plot/ssd/335104-84-2`
  - Retourne : JSON du graphique Plotly

- `GET /api/plot/ec10eq/{cas}` - Graphique des résultats EC10eq par taxon et espèce
  - Exemple : `GET /api/plot/ec10eq/335104-84-2`
  - Retourne : JSON du graphique Plotly

- `POST /api/plot/ssd/comparison` - Comparaison de plusieurs courbes SSD (maximum 3)
  - Body : `{"cas_list": ["CAS1", "CAS2", "CAS3"]}`
  - Retourne : JSON du graphique Plotly

## Documentation interactive

Une fois l'API lancée, accédez à :
- Documentation Swagger : `http://localhost:8000/docs`
- Documentation ReDoc : `http://localhost:8000/redoc`

## Déploiement sur Scalingo

### 1. Préparation

Assurez-vous que le fichier parquet est bien dans le dépôt Git :
```bash
git add data/results_ecotox_*.parquet
git commit -m "Add data file"
```

### 2. Installation du CLI Scalingo

```bash
# Sur macOS
brew tap scalingo/scalingo
brew install scalingo

# Sur Linux
curl -O https://cli.scalingo.com
chmod +x scalingo_*_linux_amd64
sudo mv scalingo_*_linux_amd64 /usr/local/bin/scalingo

# Sur Windows
# Télécharger depuis https://cli.scalingo.com
```

### 3. Connexion à Scalingo

```bash
scalingo login
```

### 4. Création du projet

```bash
# Depuis le répertoire du projet
scalingo create openchemfacts-api
```

### 5. Liaison du dépôt Git

```bash
scalingo link openchemfacts-api
```

Cette commande ajoute le remote `scalingo` à votre dépôt Git.

### 6. Configuration des variables d'environnement (optionnel)

```bash
scalingo env-set ALLOWED_ORIGINS=https://openchemfacts.com
```

Par défaut, l'API est configurée pour accepter les requêtes depuis `https://openchemfacts.com`.

### 7. Déploiement

```bash
git push scalingo main
```

Scalingo détectera automatiquement :
- Le `Procfile` pour démarrer l'application
- Le `.python-version` pour la version Python
- Le `requirements.txt` pour installer les dépendances

### 8. Vérification du déploiement

```bash
# Voir les logs
scalingo logs

# Vérifier l'état
scalingo status
```

### 9. Configuration d'un domaine personnalisé (optionnel)

```bash
scalingo domains-add api.openchemfacts.com
```

## Structure du projet

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application FastAPI principale
│   ├── api.py           # Routes API
│   ├── data_loader.py   # Chargement des données
│   └── models.py        # Modèles Pydantic
├── data/
│   ├── plotting_functions.py           # Fonctions de visualisation
│   └── results_ecotox_*.parquet       # Données d'écotoxicologie
├── Procfile             # Configuration Scalingo
├── .python-version      # Version Python (majeure uniquement)
├── requirements.txt     # Dépendances Python
├── .gitignore          # Fichiers ignorés par Git
└── README.md           # Ce fichier
```

## Variables d'environnement

- `ALLOWED_ORIGINS` : Origines autorisées pour CORS (séparées par des virgules)
  - Par défaut : `https://openchemfacts.com,https://openchemfacts.lovable.app`
  - Exemple : `https://openchemfacts.com,https://openchemfacts.lovable.app,https://www.openchemfacts.com`

## Fichiers de configuration Scalingo

- `Procfile` : Définit la commande pour démarrer l'application
  ```
  web: uvicorn app.main:app --host 0.0.0.0 --port 8080
  ```

- `.python-version` : Version Python majeure à utiliser (Scalingo utilisera automatiquement la dernière version patch)
  ```
  3.11
  ```
  
  Note : Ne spécifiez que la version majeure (ex: 3.11) pour recevoir automatiquement les mises à jour de sécurité.

## Dépannage

### L'application ne démarre pas sur Scalingo

1. Vérifier les logs : `scalingo logs`
2. Vérifier que le fichier parquet est bien dans Git
3. Vérifier que toutes les dépendances sont dans `requirements.txt`

### Erreur CORS

Vérifier que la variable d'environnement `ALLOWED_ORIGINS` est correctement configurée :
```bash
scalingo env
```

### Le fichier parquet n'est pas trouvé

Assurez-vous que le fichier est bien commité dans Git :
```bash
git ls-files data/results_ecotox_*.parquet
```

## Support

Pour toute question ou problème, consulter la documentation Scalingo : https://doc.scalingo.com

