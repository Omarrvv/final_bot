# 🗄️ **REFACTORING PLAN 2: DATABASE & SESSION CONSOLIDATION**

## **📋 Overview**

**Duration:** 2-3 days  
**Priority:** CRITICAL - Core functionality  
**Dependencies:** Plan 1 (Foundation Stabilization) complete  
**Risk Level:** Medium (data integrity critical)

### **Strategic Objectives**

1. **Eliminate Database Manager Chaos** - Remove 2 redundant managers, keep 1
2. **Fix Session Management** - Consolidate 3 session managers to 1 standardized approach
3. **Enable Connection Pooling** - Fix resource management failures
4. **Add Transaction Management** - Ensure ACID compliance

---

## **🎯 PHASE 2A: Database Layer Consolidation**

**Duration:** 6-8 hours  
**Risk:** Medium

### **Step 1.1: Choose Primary Database Manager** ⏱️ _1 hour_

**Analysis:**

- **DatabaseManager** (270 lines) - Legacy wrapper, deprecated
- **DatabaseManagerService** (1,232 lines) - Facade over facade, bloated
- **PostgresqlDatabaseManager** (930 lines) - Direct implementation

**Decision: Keep PostgresqlDatabaseManager as primary, eliminate facades**

### **Step 1.2: Create Unified Database Service** ⏱️ _3 hours_

```python
# src/database/unified_db_service.py (NEW)
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)

class UnifiedDatabaseService:
    """Single database service with connection pooling"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=self.database_url,
            cursor_factory=RealDictCursor
        )
        logger.info("✅ Database connection pool initialized")

    @contextmanager
    def get_connection(self):
        """Get connection from pool with proper cleanup"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)

    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute query with connection pooling"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
```

**Testing:**

```python
# tests/test_unified_db.py
def test_connection_pooling():
    """Test connection pool works"""
    db = UnifiedDatabaseService("postgresql://test")

    # Test multiple connections
    with db.get_connection() as conn1:
        with db.get_connection() as conn2:
            assert conn1 is not conn2

def test_transaction_rollback():
    """Test transaction rollback works"""
    db = UnifiedDatabaseService("postgresql://test")

    with pytest.raises(Exception):
        with db.transaction() as conn:
            # Insert data
            # Raise exception
            # Should rollback
            raise Exception("Test rollback")
```

### **Step 1.3: Replace All Database Manager Usage** ⏱️ _2-3 hours_

**Systematic replacement:**

```python
# Before (in multiple files):
from src.knowledge.database import DatabaseManager
from src.knowledge.database_service import DatabaseManagerService

# After (single import):
from src.database.unified_db_service import UnifiedDatabaseService
```

**Files to update:**

- `src/chatbot.py`
- `src/api/routes/*.py`
- `src/knowledge/knowledge_base_service.py`

**Validation after each file:**

```bash
python -c "from src.database.unified_db_service import UnifiedDatabaseService; print('DB OK')"
```

### **Step 1.4: Remove Legacy Database Managers** ⏱️ _30 minutes_

```bash
# Archive old managers
mkdir -p archives/deprecated_database/
mv src/knowledge/database.py archives/deprecated_database/
mv src/knowledge/database_service.py archives/deprecated_database/
```

---

## **📱 PHASE 2B: Session Management Consolidation**

**Duration:** 4-5 hours
**Risk:** Medium

### **Step 2.1: Choose Session Manager** ⏱️ _30 minutes_

**Analysis:**

- **MemorySessionManager** (286 lines) - Simple, no persistence
- **RedisSessionManager** (677 lines) - Complex, has context bleeding bug
- **EnhancedSessionManager** (685 lines) - Most complete, newest

**Decision: Standardize on EnhancedSessionManager, fix context bleeding**

### **Step 2.2: Fix Context Bleeding Issues** ⏱️ _2 hours_

```python
# src/session/enhanced_session_manager.py (FIXED)
class EnhancedSessionManager:
    """Fixed session manager without shared state"""

    def __init__(self, redis_uri: str = "redis://localhost:6379/0", ttl: int = 604800):
        # INSTANCE-level storage (not class-level)
        self.local_sessions = {}  # Remove underscore (not shared)
        self.local_sessions_lock = threading.RLock()  # Instance lock
        self.redis_available = True  # Instance flag

        self.backends = [
            RedisSessionBackend(redis_uri),
            MemorySessionBackend()
        ]

    def _cache_session_locally(self, session_id: str, session: Dict[str, Any]) -> None:
        """Cache session data in instance memory (not shared)"""
        with self.local_sessions_lock:
            # Deep copy to prevent mutation issues
            self.local_sessions[session_id] = copy.deepcopy(session)
```

**Testing:**

```python
# tests/test_session_isolation.py
def test_session_isolation():
    """Test sessions don't bleed between managers"""
    manager1 = EnhancedSessionManager()
    manager2 = EnhancedSessionManager()

    session1 = manager1.create_session()
    session2 = manager2.create_session()

    # Modify session1
    manager1.update_session(session1, {"test": "data1"})

    # session2 should not see session1's data
    session2_data = manager2.get_session(session2)
    assert "test" not in session2_data
```

### **Step 2.3: Standardize Session Data Format** ⏱️ _1.5 hours_

```python
# src/models/session_models.py (NEW)
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class StandardSessionData(BaseModel):
    """Standardized session data structure"""
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    language: str = "en"
    messages: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
```

### **Step 2.4: Update Session Usage** ⏱️ _1 hour_

**Update chatbot.py session handling:**

```python
# src/chatbot.py (UPDATE get_or_create_session method)
async def get_or_create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Updated session handling with standard format"""
    if session_id:
        session = self.session_manager.get_session(session_id)
        if session and not session.get('is_expired', False):
            return session

    # Create new session with standard format
    new_session = self.session_manager.create_session()
    return new_session
```

---

## **🔄 PHASE 2C: Transaction Management Implementation**

**Duration:** 3-4 hours  
**Risk:** Low

### **Step 3.1: Add Transaction Support** ⏱️ _2 hours_

```python
# src/database/transaction_manager.py (NEW)
from contextlib import contextmanager
from src.database.unified_db_service import UnifiedDatabaseService

class TransactionManager:
    """Manage database transactions"""

    def __init__(self, db_service: UnifiedDatabaseService):
        self.db_service = db_service

    @contextmanager
    def atomic_operation(self):
        """Ensure atomic operations"""
        with self.db_service.transaction() as conn:
            yield conn
            # Auto-commit on success, rollback on exception

    def bulk_insert_with_transaction(self, table: str, records: List[Dict]):
        """Bulk insert with proper transaction"""
        with self.atomic_operation() as conn:
            cursor = conn.cursor()
            for record in records:
                # Insert with proper transaction boundary
                cursor.execute(f"INSERT INTO {table} (...) VALUES (...)", record)
```

### **Step 3.2: Update Critical Operations** ⏱️ _1-2 hours_

**Add transactions to multi-step operations:**

```python
# Example: Session creation with history
def create_session_with_history(self, user_id: str, initial_message: str):
    """Create session and first message atomically"""
    with self.transaction_manager.atomic_operation() as conn:
        # Step 1: Create session
        session_id = self._create_session_record(conn, user_id)

        # Step 2: Add initial message
        self._add_message_record(conn, session_id, initial_message)

        # Both succeed or both fail
        return session_id
```

---

## **🧪 PHASE 2D: Integration Testing & Validation**

**Duration:** 2-3 hours
**Risk:** Low

### **Step 4.1: Database Integration Tests** ⏱️ _1 hour_

```python
# tests/test_database_consolidation.py
class TestDatabaseConsolidation:
    def test_single_database_manager(self):
        """Test only one database manager exists"""
        # Verify old managers removed
        with pytest.raises(ImportError):
            from src.knowledge.database import DatabaseManager

    def test_connection_pooling_active(self):
        """Test connection pooling works"""
        db = UnifiedDatabaseService(test_db_url)

        # Test pool has connections
        assert db.pool.minconn == 2
        assert db.pool.maxconn == 20

    def test_transaction_rollback(self):
        """Test transactions rollback properly"""
        # Test rollback functionality
        pass

    def test_query_performance(self):
        """Test queries perform well with pooling"""
        # Measure query times with pooling
        pass
```

### **Step 4.2: Session Management Tests** ⏱️ _1 hour_

```python
# tests/test_session_consolidation.py
class TestSessionConsolidation:
    def test_single_session_manager(self):
        """Test only EnhancedSessionManager used"""
        # Verify old managers not imported
        pass

    def test_no_context_bleeding(self):
        """Test sessions isolated between requests"""
        # Concurrent session test
        pass

    def test_session_data_format(self):
        """Test standardized session format"""
        manager = EnhancedSessionManager()
        session = manager.create_session()

        required_fields = ['session_id', 'created_at', 'expires_at', 'language']
        for field in required_fields:
            assert field in session
```

### **Step 4.3: End-to-End Integration** ⏱️ _1 hour_

```bash
# Integration test script
#!/bin/bash
# test_plan2_integration.sh

echo "🧪 Testing Plan 2 Integration..."

# Test 1: Database operations work
python -c "
from src.database.unified_db_service import UnifiedDatabaseService
from src.config import settings

db = UnifiedDatabaseService(settings.database_url)
result = db.execute_query('SELECT 1 as test')
print('✅ Database operations work')
"

# Test 2: Session management works
python -c "
from src.session.enhanced_session_manager import EnhancedSessionManager

manager = EnhancedSessionManager()
session_id = manager.create_session()
session = manager.get_session(session_id)
print('✅ Session management works')
"

echo "🎉 Plan 2 Integration Tests Complete!"
```

---

## **📊 SUCCESS CRITERIA & VALIDATION**

### **✅ Phase Completion Checklist**

**Database Consolidation:**

- [ ] Single database service (UnifiedDatabaseService) operational
- [ ] Connection pooling enabled and working
- [ ] All old database managers removed/archived
- [ ] Database queries use connection pool
- [ ] Transaction support added for multi-step operations

**Session Management:**

- [ ] Single session manager (EnhancedSessionManager) active
- [ ] Context bleeding issues fixed
- [ ] Standardized session data format
- [ ] Session isolation between requests verified
- [ ] Old session managers removed/archived

**System Stability:**

- [ ] All database operations functional
- [ ] Session creation/retrieval working
- [ ] No performance regressions
- [ ] Transaction rollback working

### **🎯 Key Performance Indicators**

| Metric                   | Before Plan 2 | After Plan 2 | Target  |
| ------------------------ | ------------- | ------------ | ------- |
| Database Managers        | 3 competing   | 1 unified    | 1       |
| Session Managers         | 3 with bugs   | 1 fixed      | 1       |
| Connection Pool          | Not used      | Active       | 100%    |
| DB Query Time            | Variable      | < 100ms      | < 100ms |
| Session Context Bleeding | Yes           | No           | 0       |

### **🚨 Rollback Procedures**

**If Critical Issues:**

1. **Database Rollback:**

```bash
# Restore old database managers
cp archives/deprecated_database/* src/knowledge/
# Update imports back
```

2. **Session Rollback:**

```bash
# Restore old session managers if needed
# Fall back to MemorySessionManager for stability
```

---

## **➡️ TRANSITION TO PLAN 3**

### **Prerequisites for Plan 3:**

- [ ] Single database service operational
- [ ] Session management stable
- [ ] Connection pooling active
- [ ] All Plan 2 tests passing

### **Plan 3 Enablements:**

- **Stable Data Layer** - Performance optimization can safely proceed
- **Unified Session Management** - NLU can rely on consistent sessions
- **Connection Pooling** - Reduces resource pressure for model loading

**Plan 2 provides the stable data and session foundation needed for performance optimization in Plan 3.**

---

**🎯 Expected Outcome:** Consolidated, efficient database and session management with connection pooling, transaction support, and eliminated architectural chaos.
