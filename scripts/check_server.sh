#!/bin/bash
# Script pour vérifier si le serveur local est démarré
# Usage: ./scripts/check_server.sh [port]

PORT=${1:-8000}
URL="http://localhost:$PORT"

echo "=== Vérification du serveur local ==="
echo ""

# Vérifier si curl est disponible
if ! command -v curl &> /dev/null; then
    echo "⚠️  curl n'est pas installé. Installation de curl recommandée pour ce script."
    echo "   Vérification manuelle: ouvrez $URL/health dans votre navigateur"
    exit 1
fi

# Vérifier le endpoint /health
echo "Vérification de $URL/health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Serveur démarré et fonctionnel !"
    echo ""
    echo "📊 Endpoints disponibles:"
    echo "   - Health: $URL/health"
    echo "   - Documentation: $URL/docs"
    echo "   - ReDoc: $URL/redoc"
    echo "   - API Summary: $URL/api/summary"
    echo ""
    
    # Afficher la réponse du health check
    echo "Réponse du health check:"
    curl -s "$URL/health" | python -m json.tool 2>/dev/null || curl -s "$URL/health"
    echo ""
else
    echo "❌ Serveur non accessible (code HTTP: $HTTP_CODE)"
    echo ""
    echo "Le serveur n'est probablement pas démarré."
    echo "Pour démarrer le serveur:"
    echo "   ./scripts/start_local.sh $PORT"
    echo "   ou"
    echo "   uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload"
    exit 1
fi

