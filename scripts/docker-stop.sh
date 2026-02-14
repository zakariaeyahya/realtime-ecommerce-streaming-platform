#!/bin/bash

set -e

echo "[STOP] Arret de la plateforme Docker..."

# Arrêter les containers
docker-compose down -v

echo "[OK] Services arretes"
