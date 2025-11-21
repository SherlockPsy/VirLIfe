#!/bin/bash

# VirLIfe Frontend Production Testing Script

# Configuration
FRONTEND_URL="${FRONTEND_URL:-https://virlife-frontend-production.up.railway.app}"
BACKEND_URL="${BACKEND_URL:-https://virlife-backend-production.up.railway.app}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VirLIfe Frontend Production Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Testing frontend at: ${YELLOW}${FRONTEND_URL}${NC}"
echo -e "Backend URL: ${YELLOW}${BACKEND_URL}${NC}"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed${NC}"
    exit 1
fi

# ===========================================
# Test 1: Frontend HTML Load
# ===========================================
echo -e "${BLUE}Test 1: Frontend HTML Response${NC}"
echo "Command: curl ${FRONTEND_URL}/"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${FRONTEND_URL}/")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d' | head -20)

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $HTTP_STATUS)${NC}"
    if echo "$BODY" | grep -q "VirLIfe"; then
        echo -e "${GREEN}  ✓ Contains 'VirLIfe' title${NC}"
    fi
    if echo "$BODY" | grep -q "index-"; then
        echo -e "${GREEN}  ✓ Contains JavaScript bundle reference${NC}"
    fi
    if echo "$BODY" | grep -q "index-.*\.css"; then
        echo -e "${GREEN}  ✓ Contains CSS bundle reference${NC}"
    fi
    echo ""
    echo "HTML Preview:"
    echo "$BODY" | grep -E "<title>|<script|</head>|</body>"
else
    echo -e "${RED}✗ Failed (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 2: JavaScript Bundle
# ===========================================
echo -e "${BLUE}Test 2: JavaScript Bundle Accessibility${NC}"
# Extract JS file from HTML
JS_FILE=$(curl -s "${FRONTEND_URL}/" | grep -oP 'src="[^"]*index-[^"]*\.js"' | head -1 | sed 's/src="//; s/"//')
if [ -z "$JS_FILE" ]; then
    echo -e "${YELLOW}⚠ Could not extract JS file path from HTML${NC}"
else
    JS_URL="${FRONTEND_URL}${JS_FILE}"
    echo "Testing: ${JS_URL}"
    JS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${JS_URL}")
    if [ "$JS_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ JavaScript bundle accessible (HTTP $JS_STATUS)${NC}"
        JS_SIZE=$(curl -s -o /dev/null -w "%{size_download}" "${JS_URL}")
        echo "  Size: $((JS_SIZE / 1024)) KB"
    else
        echo -e "${RED}✗ JavaScript bundle failed (HTTP $JS_STATUS)${NC}"
    fi
fi
echo ""

# ===========================================
# Test 3: CSS Bundle
# ===========================================
echo -e "${BLUE}Test 3: CSS Bundle Accessibility${NC}"
CSS_FILE=$(curl -s "${FRONTEND_URL}/" | grep -oP 'href="[^"]*index-[^"]*\.css"' | head -1 | sed 's/href="//; s/"//')
if [ -z "$CSS_FILE" ]; then
    echo -e "${YELLOW}⚠ Could not extract CSS file path from HTML${NC}"
else
    CSS_URL="${FRONTEND_URL}${CSS_FILE}"
    echo "Testing: ${CSS_URL}"
    CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${CSS_URL}")
    if [ "$CSS_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ CSS bundle accessible (HTTP $CSS_STATUS)${NC}"
        CSS_SIZE=$(curl -s -o /dev/null -w "%{size_download}" "${CSS_URL}")
        echo "  Size: $((CSS_SIZE / 1024)) KB"
    else
        echo -e "${RED}✗ CSS bundle failed (HTTP $CSS_STATUS)${NC}"
    fi
fi
echo ""

# ===========================================
# Test 4: CORS Headers (from backend)
# ===========================================
echo -e "${BLUE}Test 4: Backend CORS Configuration${NC}"
echo "Checking if backend allows frontend origin..."
CORS_HEADERS=$(curl -s -I -H "Origin: ${FRONTEND_URL}" "${BACKEND_URL}/health" | grep -i "access-control")
if [ -n "$CORS_HEADERS" ]; then
    echo -e "${GREEN}✓ CORS headers present${NC}"
    echo "$CORS_HEADERS"
else
    echo -e "${YELLOW}⚠ No CORS headers detected (might be allowed by default)${NC}"
fi
echo ""

# ===========================================
# Test 5: Frontend -> Backend Connectivity
# ===========================================
echo -e "${BLUE}Test 5: Frontend to Backend API Test${NC}"
echo "Simulating frontend API call to backend..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Referer: ${FRONTEND_URL}/" \
    "${BACKEND_URL}/health")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend can reach backend API (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ Frontend cannot reach backend (HTTP $HTTP_STATUS)${NC}"
    echo "$BODY"
fi
echo ""

# ===========================================
# Test 6: WebSocket Endpoint (from backend)
# ===========================================
echo -e "${BLUE}Test 6: WebSocket Endpoint Availability${NC}"
echo "Checking WebSocket endpoint at: ${BACKEND_URL}/ws"
WS_RESPONSE=$(curl -s -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Version: 13" \
    -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
    "${BACKEND_URL}/ws" 2>&1 | head -10)
if echo "$WS_RESPONSE" | grep -qi "upgrade\|101\|websocket"; then
    echo -e "${GREEN}✓ WebSocket endpoint responds${NC}"
else
    echo -e "${YELLOW}⚠ WebSocket endpoint check inconclusive (HTTP-only test)${NC}"
    echo "  Note: Full WebSocket test requires browser or WebSocket client"
fi
echo ""

# ===========================================
# Summary
# ===========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Frontend Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Frontend URL: ${FRONTEND_URL}"
echo "Backend URL: ${BACKEND_URL}"
echo ""
echo "✓ Basic connectivity tests completed"
echo ""
echo -e "${YELLOW}Note: Full frontend testing requires a browser because:${NC}"
echo "  - React app needs JavaScript execution"
echo "  - WebSocket connections require browser API"
echo "  - User interactions need UI rendering"
echo ""
echo "To fully test the frontend:"
echo "1. Open ${FRONTEND_URL} in a web browser"
echo "2. Open browser Developer Tools (F12)"
echo "3. Check Console for any errors"
echo "4. Check Network tab for API calls"
echo "5. Verify WebSocket connection in Network tab"
echo ""

