#!/bin/bash
# Production System Test Suite
# Tests all endpoints through curl commands
#
# Usage: ./test_production.sh <BASE_URL>
# Example: ./test_production.sh https://virlife-production.up.railway.app

set -e  # Exit on error

BASE_URL="${1:-}"
if [ -z "$BASE_URL" ]; then
    echo "ERROR: Please provide the Railway production URL"
    echo "Usage: $0 <BASE_URL>"
    echo "Example: $0 https://virlife-production.up.railway.app"
    exit 1
fi

# Remove trailing slash if present
BASE_URL="${BASE_URL%/}"

echo "=========================================="
echo "VirLIfe Production System Test Suite"
echo "=========================================="
echo "Testing: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>&1)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo "  Response: $(echo "$body" | head -c 200)..."
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        echo "  Response: $body"
        ((FAILED++))
        return 1
    fi
}

# ============================================================================
# 1. HEALTH CHECKS
# ============================================================================
echo "1. HEALTH CHECKS"
echo "----------------"

test_endpoint "Root endpoint" "GET" "/" "" 200
test_endpoint "Basic health check" "GET" "/health" "" 200
test_endpoint "Full health check" "GET" "/health/full" "" 200

echo ""

# ============================================================================
# 2. STATUS ENDPOINT
# ============================================================================
echo "2. STATUS ENDPOINT"
echo "------------------"

test_endpoint "System status" "GET" "/status" "" 200

echo ""

# ============================================================================
# 3. WORLD ADVANCE
# ============================================================================
echo "3. WORLD ADVANCE"
echo "----------------"

test_endpoint "Advance world 1 tick" "POST" "/world/advance" '{"ticks": 1}' 200
test_endpoint "Advance world 5 ticks" "POST" "/world/advance" '{"ticks": 5}' 200

echo ""

# ============================================================================
# 4. USER ACTION
# ============================================================================
echo "4. USER ACTION"
echo "--------------"

# First, we need to check if there's a user. Let's try with user_id=1
test_endpoint "User action: speak" "POST" "/user/action" \
    '{"user_id": 1, "action_type": "speak", "text": "Hello, world!"}' \
    200

test_endpoint "User action: move" "POST" "/user/action" \
    '{"user_id": 1, "action_type": "move", "destination_location_id": 1}' \
    200

echo ""

# ============================================================================
# 5. RENDER ENDPOINT
# ============================================================================
echo "5. RENDER ENDPOINT"
echo "------------------"

test_endpoint "Render for user" "GET" "/render?user_id=1&pov=second_person" "" 200

echo ""

# ============================================================================
# 6. ERROR HANDLING
# ============================================================================
echo "6. ERROR HANDLING"
echo "-----------------"

# Test invalid endpoint
echo -n "Testing invalid endpoint... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/invalid" 2>&1)
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "404" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP 404)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (Expected 404, got $http_code)"
    ((FAILED++))
fi

# Test invalid JSON
echo -n "Testing invalid JSON... "
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"invalid": json}' \
    "$BASE_URL/world/advance" 2>&1)
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "422" ] || [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (Expected 422/400, got $http_code)"
fi

echo ""

# ============================================================================
# 7. PHASE 9 SPECIFIC TESTS (Redis/Qdrant)
# ============================================================================
echo "7. PHASE 9 FEATURES"
echo "-------------------"

# Check if Redis/Qdrant are configured via health/full
echo -n "Checking Phase 9 services in /health/full... "
response=$(curl -s "$BASE_URL/health/full")
if echo "$response" | grep -q "redis"; then
    echo -e "${GREEN}✓ Redis status found${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Redis status not found${NC}"
fi

if echo "$response" | grep -q "qdrant"; then
    echo -e "${GREEN}✓ Qdrant status found${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Qdrant status not found${NC}"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi


