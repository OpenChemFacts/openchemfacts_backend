# Tests pour OpenChemFacts Backend

## Vue d'ensemble

Ce dossier contient les tests automatisés pour l'API OpenChemFacts Backend. Les tests permettent de vérifier que l'API fonctionne correctement avant de la déployer en production.

## Structure

- `conftest.py` : Configuration pytest et fixtures partagées
- `test_api.py` : Tests des endpoints API
- `test_data_loader.py` : Tests du chargement des données

## Exécuter les tests

### Méthode automatique (recommandée)

**Sur Windows :**
```batch
scripts\run_tests.bat
```

**Sur Linux/macOS :**
```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

### Méthode manuelle

1. **Activer l'environnement virtuel** (si nécessaire)
2. **Exécuter pytest :**
```bash
pytest tests/
```

### Options utiles

```bash
# Voir les détails (verbose)
pytest tests/ -v

# Arrêter au premier échec
pytest tests/ -x

# Afficher les print statements
pytest tests/ -s

# Exécuter un fichier spécifique
pytest tests/test_api.py

# Exécuter un test spécifique
pytest tests/test_api.py::test_health_check
```

## Prérequis

- Environnement virtuel activé
- Dépendances installées (`pip install -r requirements.txt`)
- Fichier de données présent (`data/results_ecotox_*.parquet`)

## Notes importantes

### CAS Number dans les tests

Certains tests utilisent un CAS number de test (`sample_cas` fixture). Assurez-vous que ce CAS existe dans vos données, ou modifiez-le dans `conftest.py` :

```python
@pytest.fixture
def sample_cas():
    return "335104-84-2"  # Remplacez par un CAS valide de vos données
```

### Tests qui peuvent échouer

Certains tests peuvent échouer si :
- Le fichier de données n'existe pas
- Le CAS number de test n'existe pas dans vos données
- Les colonnes attendues ne sont pas présentes dans les données

Dans ce cas, adaptez les tests à votre structure de données.

## Ajouter de nouveaux tests

Voir `Documentation/08_Tests_API.md` pour un guide complet sur l'ajout de nouveaux tests.

## Dépannage

### "ModuleNotFoundError"

**Solution :** Vérifiez que l'environnement virtuel est activé et que les dépendances sont installées.

### "Data file not found"

**Solution :** Vérifiez que le fichier de données existe dans `data/results_ecotox_*.parquet`.

### Tests qui échouent

**Solution :** 
1. Lisez le message d'erreur
2. Vérifiez que le serveur n'est pas déjà en cours d'exécution
3. Adaptez les tests à votre structure de données si nécessaire

