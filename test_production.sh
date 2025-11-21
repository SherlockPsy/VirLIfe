#!/bin/bash

# VirLIfe Production Testing Script
# This script tests your production Railway backend

# ===========================================
# CONFIGURATION
# ===========================================
# IMPORTANT: Replace this with your actual Railway backend URL
# You can find this in Railway dashboard → your backend service → Settings → Networking
BACKEND_URL="${BACKEND_URL:-https://virlife-backend-production-xxxx.up.railway.app}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VirLIfe Production System Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Testing backend at: ${YELLOW}${BACKEND_URL}${NC}"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed${NC}"
    echo "Please install curl to run these tests"
    exit 1
fi

# ===========================================
# Test 1: Root Endpoint
# ===========================================
echo -e "${BLUE}Test 1: Root Endpoint (/)${NC}"
echo "Command: curl ${BACKEND_URL}/"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BACKEND_URL}/")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 2: Basic Health Check
# ===========================================
echo -e "${BLUE}Test 2: Health Check (/health)${NC}"
echo "Command: curl ${BACKEND_URL}/health"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BACKEND_URL}/health")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 3: Full Health Check
# ===========================================
echo -e "${BLUE}Test 3: Full Health Check (/health/full)${NC}"
echo "Command: curl ${BACKEND_URL}/health/full"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BACKEND_URL}/health/full")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 4: Gateway Status
# ===========================================
echo -e "${BLUE}Test 4: Gateway Status (/api/v1/status)${NC}"
echo "Command: curl ${BACKEND_URL}/api/v1/status"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BACKEND_URL}/api/v1/status")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 5: World Advance (POST)
# ===========================================
echo -e "${BLUE}Test 5: World Advance (/api/v1/world/advance)${NC}"
echo "Command: curl -X POST ${BACKEND_URL}/api/v1/world/advance -H 'Content-Type: application/json' -d '{\"ticks\": 1}'"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"ticks": 1}' \
    "${BACKEND_URL}/api/v1/world/advance")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 6: Render Endpoint (GET)
# ===========================================
echo -e "${BLUE}Test 6: Render Endpoint (/api/v1/render?user_id=1)${NC}"
echo "Command: curl '${BACKEND_URL}/api/v1/render?user_id=1&pov=second_person'"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    "${BACKEND_URL}/api/v1/render?user_id=1&pov=second_person")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Summary
# ===========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "All tests completed!"
echo ""
echo "Next steps:"
echo "1. Check the responses above for any errors"
echo "2. Verify database connectivity in /health/full"
echo "3. Verify Railway-only infrastructure is working"
echo ""
echo -e "${YELLOW}Note: If you see 'Connection refused' or 'DNS resolution failed',${NC}"
echo -e "${YELLOW}make sure your Railway backend URL is correct.${NC}"
echo ""

