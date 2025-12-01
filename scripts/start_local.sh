#!/bin/bash
# Script pour démarrer le serveur local
# Usage: ./scripts/start_local.sh [port]

set -e

PORT=${1:-8000}

echo "=== Démarrage du serveur local ==="
echo ""

# Vérifier si le port est déjà utilisé
if command -v lsof &> /dev/null; then
    # Unix/Linux/macOS
    if lsof -i TCP:$PORT -sTCP:LISTEN &> /dev/null; then
        echo "❌ Le port $PORT est déjà utilisé."
        echo "   Fermez le serveur qui tourne déjà sur ce port ou choisissez un autre port :"
        echo "   ./scripts/start_local.sh 8001"
        exit 1
    fi
elif command -v netstat &> /dev/null; then
    # Windows (Git Bash)
    if netstat -ano | grep -q ":$PORT.*LISTENING"; then
        echo "❌ Le port $PORT est déjà utilisé."
        echo "   Fermez le serveur qui tourne déjà sur ce port ou choisissez un autre port :"
        echo "   ./scripts/start_local.sh 8001"
        exit 1
    fi
fi

# Vérifier que Python est installé
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python n'est pas installé."
    exit 1
fi

# Utiliser python3 si disponible, sinon python
PYTHON_CMD=$(command -v python3 || command -v python)

# Vérifier que l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "⚠️  Environnement virtuel non trouvé. Création..."
    $PYTHON_CMD -m venv venv
    echo "✅ Environnement virtuel créé."
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
# Détecter le chemin d'activation selon l'OS (Windows vs Unix)
if [ -f "venv/Scripts/activate" ]; then
    # Windows (Git Bash ou WSL)
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Unix/Linux/macOS
    source venv/bin/activate
else
    echo "❌ Impossible de trouver le script d'activation de l'environnement virtuel."
    echo "   Vérifiez que venv/Scripts/activate ou venv/bin/activate existe."
    exit 1
fi

# Vérifier que les dépendances sont installées
if ! python -c "import fastapi" 2>/dev/null || ! python -c "import slowapi" 2>/dev/null; then
    echo "⚠️  Dépendances non installées. Installation..."
    pip install -r requirements.txt
    echo "✅ Dépendances installées."
fi

# Vérifier que uvicorn est installé
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "⚠️  uvicorn n'est pas installé. Installation..."
    pip install uvicorn[standard]
    echo "✅ uvicorn installé."
fi

# Vérifier que le fichier de données existe
if ! ls data/results_ecotox_*.parquet 1>/dev/null 2>&1; then
    echo "⚠️  Aucun fichier de données trouvé dans data/"
    echo "   Assurez-vous que le fichier results_ecotox_*.parquet existe."
fi

# Afficher la configuration de sécurité
if [ "$RATE_LIMIT_ENABLED" = "true" ]; then
    echo "ℹ️  Rate limiting activé (via variable d'environnement)"
else
    echo "ℹ️  Rate limiting désactivé par défaut (mode développement)"
    echo "   Pour l'activer: export RATE_LIMIT_ENABLED=true"
fi

echo ""
echo "🚀 Démarrage du serveur sur http://localhost:$PORT"
echo "   Documentation: http://localhost:$PORT/docs"
echo "   Health check: http://localhost:$PORT/health"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur."
echo ""

# Démarrer le serveur avec rechargement automatique
uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload --log-level info

