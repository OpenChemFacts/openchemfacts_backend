#!/bin/bash
# Script pour démarrer le serveur local SANS rechargement automatique
# Utile pour déboguer les problèmes de connexion
# Usage: ./scripts/start_local_no_reload.sh [port]

set -e

PORT=${1:-8000}

echo "=== Démarrage du serveur local (SANS reload) ==="
echo ""

# Vérifier si le port est déjà utilisé
if command -v lsof &> /dev/null; then
    # Unix/Linux/macOS
    if lsof -i TCP:$PORT -sTCP:LISTEN &> /dev/null; then
        echo "❌ Le port $PORT est déjà utilisé."
        echo "   Fermez le serveur qui tourne déjà sur ce port ou choisissez un autre port :"
        echo "   ./scripts/start_local_no_reload.sh 8001"
        exit 1
    fi
elif command -v netstat &> /dev/null; then
    # Windows (Git Bash)
    if netstat -ano | grep -q ":$PORT.*LISTENING"; then
        echo "❌ Le port $PORT est déjà utilisé."
        echo "   Fermez le serveur qui tourne déjà sur ce port ou choisissez un autre port :"
        echo "   ./scripts/start_local_no_reload.sh 8001"
        exit 1
    fi
fi

# Vérifier que l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé."
    echo "   Créez-le d'abord avec: python -m venv venv"
    exit 1
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

# Vérifier que uvicorn est installé
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn n'est pas installé."
    echo "   Installez-le avec: pip install uvicorn[standard]"
    exit 1
fi

echo ""
echo "🚀 Démarrage du serveur sur http://localhost:$PORT (SANS reload)"
echo "   Documentation: http://localhost:$PORT/docs"
echo "   Health check: http://localhost:$PORT/health"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur."
echo ""

# Démarrer le serveur SANS rechargement automatique
uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level debug

