#!/bin/bash
# Send test events to raw-events Kafka topic
# Usage: docker exec streaming-kafka-1 sh /flink/tests/../scripts/send_test_events.sh
# Or:    docker cp scripts/send_test_events.sh streaming-kafka-1:/tmp/ && docker exec streaming-kafka-1 sh /tmp/send_test_events.sh

BROKER="localhost:9092"
TOPIC="raw-events"

echo "=== Sending test events to topic: $TOPIC ==="

kafka-console-producer --broker-list $BROKER --topic $TOPIC <<'EVENTS'
{"event_id":"evt_001","event_type":"transaction","user_id":"user_1001","item_id":"SKU0001","price":150.0,"quantity":2,"category":"Electronics","timestamp":"2026-02-14T10:00:00"}
{"event_id":"evt_002","event_type":"transaction","user_id":"user_1002","item_id":"SKU0099","price":9500.0,"quantity":1,"category":"Electronics","timestamp":"2026-02-14T10:00:01"}
{"event_id":"evt_003","event_type":"view","user_id":"user_1003","item_id":"SKU0042","price":25.0,"quantity":1,"category":"Books","timestamp":"2026-02-14T10:00:02"}
{"event_id":"evt_004","event_type":"transaction","user_id":"user_1004","item_id":"SKU0015","price":75.0,"quantity":3,"category":"Fashion","timestamp":"2026-02-14T10:00:03"}
{"event_id":"evt_005","event_type":"transaction","user_id":"user_1005","item_id":"SKU0200","price":8700.0,"quantity":1,"category":"Automotive","timestamp":"2026-02-14T10:00:04"}
{"event_id":"evt_006","event_type":"addtocart","user_id":"user_1006","item_id":"SKU0033","price":45.0,"quantity":1,"category":"Beauty","timestamp":"2026-02-14T10:00:05"}
{"event_id":"evt_007","event_type":"transaction","user_id":"user_1007","item_id":"SKU0077","price":320.0,"quantity":5,"category":"Home","timestamp":"2026-02-14T10:00:06"}
{"event_id":"evt_008","event_type":"transaction","user_id":"user_1008","item_id":"SKU0150","price":12000.0,"quantity":1,"category":"Furniture","timestamp":"2026-02-14T10:00:07"}
{"event_id":"evt_009","event_type":"view","user_id":"user_1009","item_id":"SKU0005","price":15.0,"quantity":10,"category":"Food","timestamp":"2026-02-14T10:00:08"}
{"event_id":"evt_010","event_type":"transaction","user_id":"user_1010","item_id":"SKU0088","price":550.0,"quantity":2,"category":"Sports","timestamp":"2026-02-14T10:00:09"}
EVENTS

echo "=== Done! 10 events sent to $TOPIC ==="
