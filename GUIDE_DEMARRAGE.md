# Guide de démarrage rapide

## 🚀 Démarrage du serveur local

### Méthode simple (recommandée)

**Windows :**
```batch
scripts\start_local.bat
```

**Linux/macOS :**
```bash
./scripts/start_local.sh
```

### Vérifier que le serveur est démarré

**Windows :**
```batch
scripts\check_server.bat
```

**Linux/macOS :**
```bash
./scripts/check_server.sh
```

**Ou manuellement :**
- Ouvrir : http://localhost:8000/health
- Doit afficher : `{"status": "ok"}`

### Endpoints utiles

- **Health check** : http://localhost:8000/health
- **Documentation** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## 🌐 Déploiement sur Scalingo

### Configuration initiale (une seule fois)

**Windows :**
```batch
scripts\deploy_scalingo.bat
```

**Linux/macOS :**
```bash
./scripts/deploy_scalingo.sh
```

### Déployer une nouvelle version

```bash
# 1. Faire vos modifications et commit
git add .
git commit -m "Vos modifications"

# 2. Pousser sur Scalingo
git push scalingo main
```

**Le serveur démarre automatiquement** après le push. Aucune action supplémentaire nécessaire.

### Vérifier le déploiement

```bash
# Voir l'état
scalingo status

# Voir les logs
scalingo logs

# Ouvrir l'application dans le navigateur
scalingo open
```

---

## 📋 Checklist de démarrage local

- [ ] Python 3.11+ installé
- [ ] Environnement virtuel créé (`python -m venv venv`)
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier de données présent (`data/results_ecotox_*.parquet`)
- [ ] Serveur démarré (`./scripts/start_local.sh` ou `scripts\start_local.bat`)
- [ ] Serveur vérifié (`./scripts/check_server.sh` ou `scripts\check_server.bat`)

---

## 🔍 Dépannage rapide

### Le serveur local ne répond pas

1. Vérifier que le serveur est démarré : `./scripts/check_server.sh`
2. Vérifier le port : le port 8000 est-il libre ?
3. Vérifier les logs dans le terminal où le serveur est lancé

### Le serveur Scalingo ne démarre pas

1. Vérifier les logs : `scalingo logs`
2. Vérifier que le fichier parquet est dans Git : `git ls-files data/*.parquet`
3. Vérifier le Procfile : `cat Procfile`

---

## 💡 Points importants

- **Serveur local** : Démarrage manuel avec `scripts/start_local.sh`/`scripts/start_local.bat`
- **Serveur Scalingo** : Démarrage automatique après `git push scalingo main`
- **Rechargement** : Le serveur local recharge automatiquement les modifications (mode `--reload`)
- **Port** : Par défaut 8000, modifiable dans les scripts

