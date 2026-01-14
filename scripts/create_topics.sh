#!/bin/bash
# ============================================================================
# Script de création des topics Kafka
# ============================================================================
# Crée tous les topics définis dans config/kafka/topics.yaml

set -e

echo "Création des topics Kafka..."

# Kafka container name
KAFKA_CONTAINER="ecommerce-kafka"

# Fonction pour créer un topic
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication=$3

    echo "  Création du topic: $topic_name (partitions=$partitions, replication=$replication)"

    docker exec $KAFKA_CONTAINER kafka-topics \
        --create \
        --if-not-exists \
        --bootstrap-server localhost:9092 \
        --topic $topic_name \
        --partitions $partitions \
        --replication-factor $replication
}

# Création des topics selon topics.yaml
create_topic "raw-events" 3 1
create_topic "inventory-changes" 2 1
create_topic "fraud-scores" 2 1
create_topic "recommendations" 2 1
create_topic "business-metrics" 1 1

echo ""
echo "Vérification des topics créés:"
docker exec $KAFKA_CONTAINER kafka-topics \
    --list \
    --bootstrap-server localhost:9092

echo ""
echo "Topics créés avec succès!"
