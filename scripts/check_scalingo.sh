#!/bin/bash
# Script pour vérifier l'état du serveur Scalingo en production
# Usage: ./scripts/check_scalingo.sh

echo "=== Vérification du serveur Scalingo ==="
echo ""

# Vérifier que le CLI Scalingo est installé
if ! command -v scalingo &> /dev/null; then
    echo "❌ Le CLI Scalingo n'est pas installé."
    echo "Téléchargez-le depuis : https://cli.scalingo.com"
    exit 1
fi

echo "1. Vérification du statut de l'application..."
scalingo status
echo ""

echo "2. Test du health check..."
APP_URL=$(scalingo open --print 2>/dev/null || echo "")
if [ -z "$APP_URL" ]; then
    echo "⚠️  Impossible de récupérer l'URL. Vérification manuelle nécessaire."
else
    echo "URL: $APP_URL"
    echo "Test de ${APP_URL}/health..."
    curl -s "${APP_URL}/health" | python -m json.tool 2>/dev/null || curl -s "${APP_URL}/health"
    echo ""
    echo ""
fi

echo "3. Dernières lignes des logs (erreurs uniquement)..."
scalingo logs --lines 50 --filter "error OR exception OR traceback" 2>/dev/null || echo "Aucune erreur récente trouvée dans les logs."
echo ""

echo "4. Métriques de ressources..."
scalingo stats --one-shot 2>/dev/null || echo "Impossible de récupérer les stats."
echo ""

echo "=== Vérification terminée ==="
echo ""
echo "Commandes utiles:"
echo "  - Voir tous les logs: scalingo logs"
echo "  - Redémarrer: scalingo restart"
echo "  - Ouvrir l'app: scalingo open"
echo ""

