#!/bin/bash
# ============================================================================
# Script de test des endpoints API FastAPI (Sprint 7)
# Usage: bash scripts/test_api.sh [HOST] [PORT]
# ============================================================================

HOST=${1:-localhost}
PORT=${2:-8000}
BASE_URL="http://${HOST}:${PORT}"
REDIS_PORT_LOCAL=${REDIS_PORT:-6379}

PASSED=0
FAILED=0

# Couleurs
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="$3"

    response=$(curl -s -o /tmp/api_response.json -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" == "$expected_code" ]; then
        echo -e "  ${GREEN}PASS${NC} [$response] $name"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} [$response] $name (attendu: $expected_code)"
        cat /tmp/api_response.json 2>/dev/null
        echo ""
        FAILED=$((FAILED + 1))
    fi
}

inject_redis_data() {
    # Utilise Python (py launcher Windows ou python)
    PY=$(command -v py 2>/dev/null || command -v python 2>/dev/null)
    if [ -z "$PY" ]; then echo "  Python introuvable"; return 1; fi
    $PY -c "
import redis, json, sys
try:
    r = redis.Redis(host='localhost', port=${REDIS_PORT_LOCAL}, db=0, decode_responses=True)
    r.ping()
except Exception as e:
    print(f'  Redis non accessible: {e}', file=sys.stderr)
    sys.exit(1)

r.setex('fraud:test_user_42', 300, json.dumps({
    'user_id': 'test_user_42',
    'fraud_score': 0.92,
    'amount': 1500.0,
    'timestamp': '2024-01-15T10:30:00'
}))

r.setex('reco:test_user_42', 300, json.dumps({
    'user_id': 'test_user_42',
    'recommendations': [
        {'item_id': 'item_100', 'score': 0.95, 'category': 'Electronics'},
        {'item_id': 'item_200', 'score': 0.87, 'category': 'Books'}
    ],
    'timestamp': '2024-01-15T10:30:00'
}))

r.setex('inventory:TEST_SKU', 300, json.dumps({
    'product_id': 'TEST_SKU',
    'current_quantity': 50,
    'forecast_7days': [45, 40, 35, 30, 25, 20, 15],
    'timestamp': '2024-01-15T10:30:00'
}))

print('  Donnees test injectees dans Redis')
" 2>&1
}

cleanup_redis_data() {
    PY=$(command -v py 2>/dev/null || command -v python 2>/dev/null)
    $PY -c "
import redis
r = redis.Redis(host='localhost', port=${REDIS_PORT_LOCAL}, db=0)
r.delete('fraud:test_user_42', 'reco:test_user_42', 'inventory:TEST_SKU')
" 2>/dev/null
}

echo "============================================"
echo " Test API FastAPI - ${BASE_URL}"
echo "============================================"
echo ""

# --- Verifier que l'API est accessible ---
echo -e "${YELLOW}[0] Verification connexion API...${NC}"
if ! curl -s --connect-timeout 3 "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}ERREUR: API non accessible sur ${BASE_URL}${NC}"
    echo "Lancez d'abord: uvicorn serving.api.main:app --reload --port ${PORT}"
    exit 1
fi
echo -e "  ${GREEN}API accessible${NC}"
echo ""

# --- 1. Health Check ---
echo -e "${YELLOW}[1] Health Check${NC}"
test_endpoint "GET /health" "${BASE_URL}/health" "200"
echo -e "${CYAN}  Reponse:${NC}"
curl -s "${BASE_URL}/health" 2>/dev/null | py -m json.tool 2>/dev/null
echo ""

# --- 2. Swagger / OpenAPI ---
echo -e "${YELLOW}[2] Documentation Swagger${NC}"
test_endpoint "GET /docs" "${BASE_URL}/docs" "200"
test_endpoint "GET /openapi.json" "${BASE_URL}/openapi.json" "200"
echo ""

# --- 3. Endpoints sans data (attendu 404) ---
echo -e "${YELLOW}[3] Endpoints sans data (404 attendu = normal)${NC}"
test_endpoint "GET /fraud/inexistant" "${BASE_URL}/fraud/utilisateur_inexistant_xyz" "404"
test_endpoint "GET /recommendations/inexistant" "${BASE_URL}/recommendations/utilisateur_inexistant_xyz" "404"
test_endpoint "GET /inventory/inexistant" "${BASE_URL}/inventory/produit_inexistant_xyz" "404"
echo ""

# --- 4. Metrics Prometheus ---
echo -e "${YELLOW}[4] Metrics Prometheus${NC}"
test_endpoint "GET /metrics" "${BASE_URL}/metrics" "200"
echo ""

# --- 5. Injection donnees test + verification endpoints avec data ---
echo -e "${YELLOW}[5] Injection donnees test dans Redis + verification${NC}"

if inject_redis_data; then
    echo ""

    test_endpoint "GET /fraud/test_user_42" "${BASE_URL}/fraud/test_user_42" "200"
    test_endpoint "GET /recommendations/test_user_42" "${BASE_URL}/recommendations/test_user_42" "200"
    test_endpoint "GET /inventory/TEST_SKU" "${BASE_URL}/inventory/TEST_SKU" "200"

    echo ""
    echo -e "${CYAN}  --- Reponse /fraud/test_user_42 ---${NC}"
    curl -s "${BASE_URL}/fraud/test_user_42" 2>/dev/null | py -m json.tool 2>/dev/null
    echo ""
    echo -e "${CYAN}  --- Reponse /recommendations/test_user_42 ---${NC}"
    curl -s "${BASE_URL}/recommendations/test_user_42" 2>/dev/null | py -m json.tool 2>/dev/null
    echo ""
    echo -e "${CYAN}  --- Reponse /inventory/TEST_SKU ---${NC}"
    curl -s "${BASE_URL}/inventory/TEST_SKU" 2>/dev/null | py -m json.tool 2>/dev/null
    echo ""

    # Cleanup
    cleanup_redis_data
    echo -e "  ${GREEN}Donnees test nettoyees${NC}"
else
    echo -e "  ${YELLOW}SKIP${NC} Redis non accessible, injection impossible"
    echo "  Verifiez que Redis tourne: docker-compose up -d redis"
fi

echo ""
echo "============================================"
echo -e " Resultats: ${GREEN}${PASSED} PASS${NC} / ${RED}${FAILED} FAIL${NC}"
echo "============================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
