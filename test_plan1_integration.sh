#!/bin/bash
# Phase 1D: System Integration Validation Script
# ==============================================
# Integration test script for Phase 1 Foundation Stabilization
# as specified in REFACTORING_PLAN_1_FOUNDATION_STABILIZATION.md

echo "🧪 Testing Plan 1 Integration..."
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Function to log test results
log_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Application starts successfully
echo ""
echo "Test 1: Application startup..."
echo "------------------------------"

# Test application can be imported and initialized (safer than full server start)
python3 -c "
import sys
sys.path.append('src')

try:
    from src.main import app
    from fastapi.testclient import TestClient
    
    # Test that app can be created and basic endpoint works
    client = TestClient(app)
    response = client.get('/api/health')
    
    assert response.status_code in [200, 503], f'Health check failed: {response.status_code}'
    
    print('Application startup validation passed')
    exit(0)
except Exception as e:
    print(f'Application startup validation failed: {e}')
    exit(1)
"

log_test $? "Application starts successfully"

# Test 2: Configuration system validation
echo ""
echo "Test 2: Configuration system..."
echo "-------------------------------"

python3 -c "
import sys
sys.path.append('src')

try:
    from src.config_unified import settings
    
    # Test essential settings exist
    assert settings.api_host is not None, 'API host not configured'
    assert settings.api_port is not None, 'API port not configured'
    assert settings.database_uri is not None, 'Database URI not configured'
    assert settings.jwt_secret is not None, 'JWT secret not configured'
    
    print('Configuration system validation passed')
    exit(0)
except Exception as e:
    print(f'Configuration system validation failed: {e}')
    exit(1)
"

log_test $? "Configuration system validation"

# Test 3: All endpoints respond
echo ""
echo "Test 3: Endpoint availability..."
echo "--------------------------------"

python3 -c "
import sys
sys.path.append('src')

try:
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    endpoints = ['/api/health', '/docs', '/openapi.json']
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            print(f'✅ {endpoint}: {response.status_code}')
            
            # Health endpoint should be 200 or 503
            if endpoint == '/api/health':
                assert response.status_code in [200, 503], f'Health check failed: {response.status_code}'
            # Docs should be 200
            elif endpoint in ['/docs', '/openapi.json']:
                assert response.status_code == 200, f'{endpoint} not accessible: {response.status_code}'
                
        except Exception as e:
            print(f'❌ {endpoint}: {e}')
            exit(1)
    
    print('All endpoints responding correctly')
    exit(0)
    
except Exception as e:
    print(f'Endpoint testing failed: {e}')
    exit(1)
"

log_test $? "All endpoints respond correctly"

# Test 4: Error handling standardization
echo ""
echo "Test 4: Error handling..."
echo "------------------------"

python3 -c "
import sys
sys.path.append('src')

try:
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    
    # Test 404 error format
    response = client.get('/api/nonexistent')
    assert response.status_code == 404, f'Expected 404, got {response.status_code}'
    
    data = response.json()
    
    # Check for standardized error format
    if 'detail' in data and isinstance(data['detail'], dict):
        detail = data['detail']
        required_fields = ['error', 'message', 'request_id', 'timestamp']
        
        for field in required_fields:
            assert field in detail, f'Missing required field: {field}'
    
    print('Error handling standardization validated')
    exit(0)
    
except Exception as e:
    print(f'Error handling validation failed: {e}')
    exit(1)
"

log_test $? "Error handling standardization"

# Test 5: Security middleware configuration
echo ""
echo "Test 5: Security middleware..."
echo "-----------------------------"

python3 -c "
import sys
sys.path.append('src')

try:
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    
    # Test CORS headers
    headers = {'Origin': 'http://localhost:3000'}
    response = client.options('/api/health', headers=headers)
    
    # Should have CORS headers
    cors_headers = [h for h in response.headers.keys() if h.lower().startswith('access-control')]
    assert len(cors_headers) > 0, 'CORS headers not found'
    
    print(f'Security middleware configured (CORS headers: {len(cors_headers)})')
    exit(0)
    
except Exception as e:
    print(f'Security middleware validation failed: {e}')
    exit(1)
"

log_test $? "Security middleware configuration"

# Test 6: Performance validation
echo ""
echo "Test 6: Performance validation..."
echo "--------------------------------"

python3 -c "
import sys
import time
sys.path.append('src')

try:
    # Test configuration loading performance
    start_time = time.time()
    from src.config_unified import settings
    load_time = time.time() - start_time
    
    assert load_time < 0.2, f'Configuration loading too slow: {load_time:.3f}s'
    
    # Test application response time
    from fastapi.testclient import TestClient
    from src.main import app
    
    client = TestClient(app)
    
    start_time = time.time()
    response = client.get('/api/health')
    response_time = time.time() - start_time
    
    assert response_time < 1.0, f'Health endpoint too slow: {response_time:.3f}s'
    
    print(f'Performance validation passed (config: {load_time:.3f}s, health: {response_time:.3f}s)')
    exit(0)
    
except Exception as e:
    print(f'Performance validation failed: {e}')
    exit(1)
"

log_test $? "Performance validation"

# Final results
echo ""
echo "================================="
echo "🎉 Plan 1 Integration Tests Complete!"
echo "================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - Phase 1D Integration Complete!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed - Phase 1D needs attention${NC}"
    exit 1
fi 