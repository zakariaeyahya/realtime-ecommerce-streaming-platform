#!/bin/bash
# ============================================================================
# Script de setup complet pour Sprint 1
# ============================================================================
# Ce script démarre tous les services Docker et crée les topics Kafka

set -e  # Arrêt en cas d'erreur

echo "========================================"
echo "Sprint 1 - Setup E-Commerce Platform"
echo "========================================"
echo ""

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que Docker est installé
echo -e "${YELLOW}[1/5]${NC} Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Erreur: Docker n'est pas installé${NC}"
    exit 1
fi
echo -e "${GREEN}Docker trouvé${NC}"
echo ""

# 2. Démarrer les services Docker
echo -e "${YELLOW}[2/5]${NC} Démarrage des services Docker..."
docker-compose up -d
echo -e "${GREEN}Services démarrés${NC}"
echo ""

# 3. Attendre que les services soient prêts
echo -e "${YELLOW}[3/5]${NC} Attente du démarrage des services (30s)..."
sleep 30
echo ""

# 4. Vérifier la santé des services
echo -e "${YELLOW}[4/5]${NC} Vérification de l'état des services..."
docker-compose ps
echo ""

# 5. Créer les topics Kafka
echo -e "${YELLOW}[5/5]${NC} Création des topics Kafka..."
bash scripts/create_topics.sh
echo ""

echo "========================================"
echo -e "${GREEN}Setup terminé avec succès!${NC}"
echo "========================================"
echo ""
echo "Services disponibles:"
echo "  - Kafka: localhost:9092"
echo "  - Schema Registry: http://localhost:8081"
echo "  - Kafka UI: http://localhost:8080"
echo ""
echo "Prochaines étapes:"
echo "  1. Lancer le producer: python ingestion/producer.py"
echo "  2. Lancer le consumer: python ingestion/basic_consumer.py"
echo ""
