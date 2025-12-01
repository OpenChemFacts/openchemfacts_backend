#!/bin/bash
# Script pour exécuter les tests automatiquement
# Usage: ./scripts/run_tests.sh

set -e

echo "=== Execution des tests ==="
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
    echo ""
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

# Vérifier que pytest est installé
if ! python -c "import pytest" 2>/dev/null; then
    echo "⚠️  pytest n'est pas installé. Installation..."
    pip install pytest httpx
    echo "✅ pytest installé."
    echo ""
fi

# Exécuter les tests
echo "Exécution des tests..."
echo ""
pytest tests/ -v

echo ""
echo "=== Tests terminés ==="

