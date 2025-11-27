#!/bin/bash
# Script pour déployer l'application sur Scalingo
# À exécuter après avoir installé le CLI Scalingo et être connecté

set -e

echo "=== Déploiement sur Scalingo ==="
echo ""

# Vérifier que le CLI Scalingo est installé
if ! command -v scalingo &> /dev/null; then
    echo "❌ Le CLI Scalingo n'est pas installé."
    echo "Téléchargez-le depuis : https://cli.scalingo.com"
    exit 1
fi

# Nom du projet
PROJECT_NAME="openchemfacts-api"

echo "1. Connexion à Scalingo..."
echo "   (Cette étape ouvrira votre navigateur pour l'authentification)"
scalingo login

echo ""
echo "2. Création du projet '$PROJECT_NAME'..."
scalingo create "$PROJECT_NAME"

echo ""
echo "3. Liaison du dépôt Git..."
scalingo link "$PROJECT_NAME"

echo ""
echo "4. Configuration de la variable d'environnement CORS..."
scalingo env-set ALLOWED_ORIGINS=https://openchemfacts.com

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "Pour déployer, exécutez :"
echo "  git push scalingo main"
echo ""
echo "Pour voir les logs :"
echo "  scalingo logs"
echo ""
echo "Pour vérifier l'état :"
echo "  scalingo status"

