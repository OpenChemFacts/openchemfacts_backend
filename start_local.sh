#!/bin/bash
# Script pour démarrer le serveur local
# Usage: ./start_local.sh [port]

set -e

PORT=${1:-8000}

echo "=== Démarrage du serveur local ==="
echo ""

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
source venv/Scripts/activate

# Vérifier que les dépendances sont installées
if ! python -c "import fastapi" 2>/dev/null || ! python -c "import slowapi" 2>/dev/null; then
    echo "⚠️  Dépendances non installées. Installation..."
    pip install -r requirements.txt
    echo "✅ Dépendances installées."
fi

# Vérifier que le fichier de données existe
if ! ls data/results_ecotox_*.parquet 1>/dev/null 2>&1; then
    echo "⚠️  Aucun fichier de données trouvé dans data/"
    echo "   Assurez-vous que le fichier results_ecotox_*.parquet existe."
fi

echo ""
echo "🚀 Démarrage du serveur sur http://localhost:$PORT"
echo "   Documentation: http://localhost:$PORT/docs"
echo "   Health check: http://localhost:$PORT/health"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur."
echo ""

# Démarrer le serveur avec rechargement automatique
uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload

