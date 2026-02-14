#!/bin/bash

set -e

echo "[DOCKER] Demarrage de la plateforme Docker..."

# 1. Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker n'est pas installe"
    exit 1
fi

# 2. Vérifier ports disponibles
echo "[CHECK] Verification des ports..."
for port in 9092 6123 8081 6379 2181; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "[WARNING] Port $port est deja utilise!"
        exit 1
    fi
done

# 3. Démarrer services
echo "[START] Demarrage des services..."
docker-compose up -d

# 4. Attendre que Kafka soit prêt
echo "[WAIT] Attente de Kafka (30s)..."
sleep 30

# 5. Créer topics Kafka
echo "[KAFKA] Creation des topics Kafka..."
docker-compose exec -T kafka kafka-topics \
    --create \
    --bootstrap-server localhost:9092 \
    --topic events \
    --partitions 12 \
    --replication-factor 1 \
    --if-not-exists

docker-compose exec -T kafka kafka-topics \
    --create \
    --bootstrap-server localhost:9092 \
    --topic inventory-changes \
    --partitions 8 \
    --replication-factor 1 \
    --if-not-exists

# 6. Vérifier l'état
echo "[OK] Verification de l'etat des services..."
docker-compose ps

echo ""
echo "===================================================================="
echo "[SUCCESS] Plateforme demarree avec succes!"
echo "===================================================================="
echo ""
echo "[INFO] URLs d'acces:"
echo "  > Flink Web UI    : http://localhost:8081"
echo "  > Kafka UI        : http://localhost:8080"
echo "  > Redis           : localhost:6379"
echo ""
