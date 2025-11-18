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

## Démarrage du serveur local

### Méthode 1 : Script automatique (recommandé)

**Sur Linux/macOS :**
```bash
chmod +x start_local.sh
./start_local.sh
```

**Sur Windows :**
```batch
start_local.bat
```

Le script vérifie automatiquement :
- ✅ La présence de Python
- ✅ L'existence de l'environnement virtuel (le crée si nécessaire)
- ✅ L'installation des dépendances (les installe si nécessaire)
- ✅ La présence du fichier de données

Le serveur démarre sur `http://localhost:8000` avec rechargement automatique.

### Méthode 2 : Commande manuelle

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Démarrer le serveur
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Vérifier que le serveur est démarré

**Avec le script de vérification :**

**Sur Linux/macOS :**
```bash
chmod +x check_server.sh
./check_server.sh
```

**Sur Windows :**
```batch
check_server.bat
```

**Manuellement :**
- Ouvrir dans votre navigateur : `http://localhost:8000/health`
- Vous devriez voir : `{"status": "ok"}`
- Documentation interactive : `http://localhost:8000/docs`

### Arrêter le serveur

Appuyez sur `Ctrl+C` dans le terminal où le serveur est lancé.

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

### Vue d'ensemble

Le déploiement sur Scalingo se fait via Git. Quand vous poussez votre code sur le remote `scalingo`, Scalingo :
1. Détecte automatiquement le `Procfile` pour démarrer l'application
2. Installe les dépendances depuis `requirements.txt`
3. Démarre l'application avec uvicorn

**Important :** Le serveur distant démarre automatiquement après chaque `git push scalingo main`. Vous n'avez pas besoin de le démarrer manuellement.

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

**Premier déploiement :**
```bash
git push scalingo main
```

**Déploiements suivants :**
```bash
# Après avoir fait des modifications et commité
git push scalingo main
```

Scalingo détectera automatiquement :
- Le `Procfile` pour démarrer l'application
- Le `.python-version` pour la version Python
- Le `requirements.txt` pour installer les dépendances

**Le serveur démarre automatiquement** après le déploiement. Vous n'avez rien à faire de plus.

### 8. Vérification du déploiement et monitoring

#### Vérifier l'état du serveur en production

**Méthode rapide avec script (recommandée) :**

**Sur Windows :**
```batch
check_scalingo.bat
```

**Sur Linux/macOS :**
```bash
chmod +x check_scalingo.sh
./check_scalingo.sh
```

Ce script vérifie automatiquement :
- Le statut de l'application
- Le health check endpoint
- Les erreurs récentes dans les logs
- Les métriques de ressources

**Méthode manuelle :**

**1. Vérifier le statut de l'application :**
```bash
scalingo status
```
Affiche l'état actuel (running, stopped, crashed, etc.) et les informations sur les conteneurs.

**2. Tester l'endpoint health check :**
```bash
# Récupérer l'URL de l'application
scalingo open

# Tester le health check manuellement
curl https://votre-app.scalingo.io/health
```

Le health check retourne :
```json
{
  "status": "ok",
  "timestamp": "2025-01-XX...",
  "data": {
    "status": "ok",
    "rows": 12345
  },
  "version": "0.1.0"
}
```

**3. Voir les logs en temps réel :**
```bash
# Logs en temps réel (streaming)
scalingo logs

# Dernières 100 lignes
scalingo logs --lines 100

# Filtrer les erreurs
scalingo logs --filter "@level:error"

# Logs d'un déploiement spécifique
scalingo logs --deployment <deployment-id>
```

**4. Vérifier les métriques et ressources :**
```bash
# Voir l'utilisation des ressources (CPU, mémoire)
scalingo stats

# Voir les déploiements récents
scalingo deployments
```

**5. Vérifier les variables d'environnement :**
```bash
scalingo env
```

#### Diagnostic en cas de problème (site down)

**Étape 1 : Vérifier l'état de l'application**
```bash
scalingo status
```

**Étape 2 : Consulter les logs récents pour identifier l'erreur**
```bash
# Voir les 200 dernières lignes
scalingo logs --lines 200

# Filtrer uniquement les erreurs
scalingo logs --lines 200 --filter "@level:error OR error OR exception OR traceback"
```

**Étape 3 : Vérifier si l'application répond**
```bash
# Tester le health check
curl -v https://votre-app.scalingo.io/health

# Si pas de réponse, vérifier les logs de build
scalingo logs --type build
```

**Étape 4 : Redémarrer l'application si nécessaire**
```bash
# Redémarrer l'application
scalingo restart

# Vérifier qu'elle redémarre correctement
scalingo logs --lines 50
```

**Étape 5 : Vérifier les déploiements récents**
```bash
# Lister les déploiements
scalingo deployments

# Voir les logs d'un déploiement spécifique
scalingo logs --deployment <deployment-id>
```

#### Configuration du redémarrage automatique

Scalingo redémarre automatiquement l'application si :
- Le processus crash (exit code != 0)
- Le conteneur s'arrête de manière inattendue
- Un nouveau déploiement est effectué

**Pour améliorer la résilience, vous pouvez configurer un health check HTTP :**

1. Dans le dashboard Scalingo, allez dans **Settings** > **Healthcheck**
2. Configurez l'URL : `/health`
3. Scalingo vérifiera automatiquement que l'application répond et la redémarrera si nécessaire

**Redémarrer manuellement l'application :**
```bash
scalingo restart
```

### Scripts de déploiement automatique

**Sur Linux/macOS :**
```bash
chmod +x deploy_scalingo.sh
./deploy_scalingo.sh
```

**Sur Windows :**
```batch
deploy_scalingo.bat
```

Ces scripts configurent automatiquement :
- La connexion à Scalingo
- La création du projet (si nécessaire)
- La liaison du dépôt Git
- Les variables d'environnement

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

### Le serveur local ne démarre pas

1. **Vérifier que Python est installé :**
   ```bash
   python --version  # Doit être 3.11 ou supérieur
   ```

2. **Vérifier que l'environnement virtuel est activé :**
   ```bash
   which python  # Doit pointer vers venv/bin/python
   ```

3. **Réinstaller les dépendances :**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

4. **Vérifier que le port 8000 n'est pas déjà utilisé :**
   ```bash
   # Sur Linux/macOS
   lsof -i :8000
   
   # Sur Windows
   netstat -ano | findstr :8000
   ```
   Si le port est occupé, utilisez un autre port :
   ```bash
   uvicorn app.main:app --port 8001 --reload
   ```

5. **Vérifier que le fichier de données existe :**
   ```bash
   ls data/results_ecotox_*.parquet
   ```

### L'application ne démarre pas sur Scalingo

1. **Vérifier les logs :**
   ```bash
   scalingo logs --lines 100
   scalingo logs --type build  # Logs de build
   ```

2. **Vérifier l'état de l'application :**
   ```bash
   scalingo status
   ```

3. **Vérifier que le fichier parquet est bien dans Git :**
   ```bash
   git ls-files data/results_ecotox_*.parquet
   ```

4. **Vérifier que toutes les dépendances sont dans `requirements.txt`**

5. **Vérifier la configuration du Procfile :**
   ```bash
   cat Procfile
   ```
   Doit contenir : `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. **Vérifier les variables d'environnement :**
   ```bash
   scalingo env
   ```

7. **Tester le health check :**
   ```bash
   curl https://votre-app.scalingo.io/health
   ```

### Le site est down en production

1. **Vérifier l'état immédiatement :**
   ```bash
   scalingo status
   ```

2. **Consulter les logs d'erreur :**
   ```bash
   scalingo logs --lines 200 --filter "error OR exception OR traceback"
   ```

3. **Vérifier les métriques (CPU, mémoire) :**
   ```bash
   scalingo stats
   ```
   Si la mémoire est saturée, l'application peut crasher.

4. **Redémarrer l'application :**
   ```bash
   scalingo restart
   ```

5. **Vérifier les déploiements récents :**
   ```bash
   scalingo deployments
   ```
   Un déploiement récent peut avoir causé le problème.

6. **Configurer un health check HTTP dans Scalingo** (recommandé) :
   - Dashboard Scalingo > Settings > Healthcheck
   - URL : `/health`
   - Cela permettra à Scalingo de redémarrer automatiquement l'application si elle ne répond plus

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

