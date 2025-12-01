# Configuration de Sécurité - Guide Rapide

## Aucun fichier .env nécessaire !

**Par défaut, l'API est configurée pour fonctionner sans configuration :**
- ✅ Rate limiting : **DÉSACTIVÉ** (pour faciliter les tests)
- ✅ Security headers : **ACTIVÉS** (protection de base)
- ✅ Limite de taille : **2MB** (permissif)
- ✅ Messages d'erreur : **Détaillés** (mode développement)

## Personnalisation (optionnelle)

Si vous voulez activer le rate limiting pour tester :

```bash
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_PER_MINUTE=120
./scripts/start_local.sh
```

## Configuration complète

Voir `Documentation/12_Configuration_Securite.md` pour la documentation complète.

