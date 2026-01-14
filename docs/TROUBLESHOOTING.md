# Guide de Dépannage - Sprint 1

## Problèmes Courants et Solutions

### 1. Problèmes Docker / Kafka

#### Kafka ne démarre pas

**Symptôme:**
```
ecommerce-kafka | Error: Kafka broker not running
```

**Solutions:**

1. Vérifier que Zookeeper est démarré:
```bash
docker-compose ps
```

2. Attendre plus longtemps (Kafka prend 20-30s):
```bash
sleep 30
docker-compose logs kafka
```

3. Redémarrer complètement:
```bash
docker-compose down -v
docker-compose up -d
```

#### Port 9092 déjà utilisé

**Symptôme:**
```
Error: Port 9092 is already allocated
```

**Solutions:**

1. Identifier le processus:
```bash
# Windows
netstat -ano | findstr :9092

# Linux/Mac
lsof -i :9092
```

2. Arrêter le processus ou changer le port dans `docker-compose.yml`:
```yaml
ports:
  - "9093:9092"  # Utiliser 9093 au lieu de 9092
```

#### Zookeeper unhealthy

**Symptôme:**
```
zookeeper | Connection refused
```

**Solutions:**

1. Vérifier les logs:
```bash
docker-compose logs zookeeper
```

2. Nettoyer les volumes:
```bash
docker-compose down -v
docker volume prune
docker-compose up -d
```

### 2. Problèmes Producer

#### Producer ne peut pas se connecter à Kafka

**Symptôme:**
```
ERROR - Échec initialisation producer: Failed to connect
```

**Solutions:**

1. Vérifier que Kafka est accessible:
```bash
docker exec ecommerce-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

2. Vérifier la configuration dans `.env`:
```bash
KAFKA_BROKERS=localhost:9092  # Pas kafka:9092 depuis l'hôte
```

3. Utiliser l'adresse IP Docker:
```python
# Si localhost ne fonctionne pas
KAFKA_BROKERS=127.0.0.1:9092
```

#### BufferError: Local: Queue full

**Symptôme:**
```
WARNING - Buffer plein, attente...
```

**Solutions:**

1. Ralentir la vitesse d'envoi:
```bash
python ingestion/producer.py --speed 0.5
```

2. Augmenter le buffer:
```python
PRODUCER_CONFIG = {
    'buffer.memory': 67108864,  # 64MB au lieu de 32MB
}
```

3. Flush plus fréquemment:
```python
self.producer.poll(0)  # Appeler après chaque produce()
```

#### Événements pas générés

**Symptôme:**
Le producer tourne mais aucun événement n'apparaît.

**Solutions:**

1. Vérifier les logs DEBUG:
```python
LOG_LEVEL=DEBUG python ingestion/producer.py
```

2. Vérifier le callback:
```python
def _delivery_callback(self, err, msg):
    if err:
        logger.error(f"FAILED: {err}")
    else:
        logger.info(f"SUCCESS: {msg.topic()}")
```

### 3. Problèmes Consumer

#### Consumer ne reçoit aucun message

**Symptôme:**
```
INFO - Abonné aux topics: raw-events
(puis silence)
```

**Solutions:**

1. Vérifier que le topic existe:
```bash
docker exec ecommerce-kafka kafka-topics --list --bootstrap-server localhost:9092
```

2. Vérifier qu'il y a des messages:
```bash
docker exec ecommerce-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-events \
  --from-beginning \
  --max-messages 5
```

3. Reset des offsets:
```bash
# Arrêter le consumer d'abord
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --topic raw-events \
  --reset-offsets --to-earliest \
  --execute
```

#### Consumer lag trop élevé

**Symptôme:**
```
Consumer lag > 10000 messages
```

**Solutions:**

1. Augmenter le nombre de consumers:
```bash
# Terminal 1
python ingestion/basic_consumer.py

# Terminal 2 (même group_id)
python ingestion/basic_consumer.py
```

2. Optimiser la configuration:
```python
CONSUMER_CONFIG = {
    'max.poll.records': 1000,      # Plus de messages par poll
    'fetch.min.bytes': 50000,       # Batches plus grands
}
```

### 4. Problèmes de Dépendances Python

#### Module 'confluent_kafka' not found

**Symptôme:**
```
ModuleNotFoundError: No module named 'confluent_kafka'
```

**Solutions:**

1. Installer les dépendances:
```bash
pip install -r ingestion/requirements.txt
```

2. Vérifier l'environnement virtuel:
```bash
which python  # Doit pointer vers venv/bin/python
```

3. Réinstaller confluent-kafka:
```bash
pip install --force-reinstall confluent-kafka==2.5.0
```

#### Import error avec dotenv

**Symptôme:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Solution:**
```bash
pip install python-dotenv
```

### 5. Problèmes de Tests

#### Tests échouent avec "Connection refused"

**Symptôme:**
```
pytest tests/ -v
ERROR - Connection refused
```

**Solution:**

Les tests d'intégration nécessitent Kafka en cours d'exécution. Utilisez le skip:
```bash
pytest tests/unit/ -v  # Seulement les tests unitaires
```

#### Fixtures non trouvées

**Symptôme:**
```
fixture 'event_producer_instance' not found
```

**Solution:**

Vérifier que `tests/conftest.py` est présent et correct:
```bash
ls tests/conftest.py
pytest --fixtures  # Lister les fixtures disponibles
```

### 6. Problèmes de Performance

#### Throughput trop bas

**Symptôme:**
< 100 events/sec avec speed=1

**Solutions:**

1. Activer le batching:
```python
PRODUCER_CONFIG = {
    'linger.ms': 50,      # Attendre 50ms
    'batch.size': 65536,  # Batches de 64KB
}
```

2. Désactiver les logs DEBUG:
```bash
LOG_LEVEL=INFO
```

3. Utiliser compression:
```python
'compression.type': 'lz4'  # Plus rapide que snappy
```

#### Consumer trop lent

**Symptôme:**
Lag augmente continuellement

**Solutions:**

1. Traitement asynchrone:
```python
# Au lieu de traiter directement
self._process_message(message)

# Utiliser une queue
self.queue.put(message)  # Thread pool processing
```

2. Augmenter poll timeout:
```python
CONSUMER_POLL_TIMEOUT = 5.0  # Au lieu de 1.0
```

### 7. Problèmes de Logs

#### Logs trop verbeux

**Solution:**
```bash
# Dans .env
LOG_LEVEL=WARNING  # Au lieu de DEBUG ou INFO
```

#### Logs non formatés

**Vérifier:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 8. Commandes de Diagnostic

#### Vérifier l'état complet

```bash
# Services Docker
docker-compose ps

# Topics Kafka
docker exec ecommerce-kafka kafka-topics --list --bootstrap-server localhost:9092

# Consumer groups
docker exec ecommerce-kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# Lag détaillé
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --describe

# Logs en temps réel
docker-compose logs -f kafka
```

#### Nettoyer complètement

```bash
# Arrêter et supprimer tout
docker-compose down -v
docker volume prune -f
docker network prune -f

# Redémarrer proprement
bash scripts/setup.sh
```

## Obtenir de l'Aide

### Logs Utiles

1. **Logs Docker:**
```bash
docker-compose logs kafka > kafka.log
docker-compose logs zookeeper > zookeeper.log
```

2. **Logs Python:**
```bash
python ingestion/producer.py 2>&1 | tee producer.log
```

### Informations à Fournir

Lors d'une demande d'aide, incluez:
- Version de Docker: `docker --version`
- Version de Python: `python --version`
- Logs d'erreur complets
- Configuration (sans secrets)
- Résultat de `docker-compose ps`

### Ressources

- [Confluent Documentation](https://docs.confluent.io/)
- [Kafka Troubleshooting](https://kafka.apache.org/documentation/#troubleshooting)
- [Docker Compose Issues](https://github.com/docker/compose/issues)
