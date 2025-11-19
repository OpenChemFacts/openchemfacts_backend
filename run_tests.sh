#!/bin/bash
# Script pour exécuter les tests automatiquement
# Usage: ./run_tests.sh

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
source venv/bin/activate

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

