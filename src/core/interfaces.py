"""
Interface definitions for breaking circular dependencies.
Provides abstract contracts for core components.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IChatbot(ABC):
    """Interface for chatbot to break circular dependencies"""

    @abstractmethod
    async def process_message(self, user_message: str, session_id: str = None, language: str = None) -> Dict[str, Any]:
        """Process user message and return response"""
        pass

    @abstractmethod
    def get_suggestions(self, session_id: Optional[str] = None, language: str = "en") -> List[Dict]:
        """Get conversation suggestions"""
        pass

    @abstractmethod
    def reset_session(self, session_id: Optional[str] = None) -> Dict:
        """Reset conversation session"""
        pass

class IDatabaseManager(ABC):
    """Interface for database manager"""

    @abstractmethod
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute database query"""
        pass

class ISessionManager(ABC):
    """Interface for session manager"""

    @abstractmethod
    def create_session(self, user_id: str = None, metadata: Dict = None) -> str:
        """Create new session"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        pass

class INLUEngine(ABC):
    """Interface for NLU engine"""

    @abstractmethod
    async def process(self, text: str, session_id: str, language: str = "en") -> Dict[str, Any]:
        """Process text through NLU pipeline"""
        pass

class IDialogManager(ABC):
    """Interface for dialog manager"""

    @abstractmethod
    async def get_action(self, nlu_result: Dict, session: Dict) -> Dict[str, Any]:
        """Get dialog action based on NLU result"""
        pass

class IResponseGenerator(ABC):
    """Interface for response generator"""

    @abstractmethod
    async def generate(self, dialog_action: Dict, nlu_result: Dict, session: Dict) -> Dict[str, Any]:
        """Generate response based on dialog action"""
        pass

class IKnowledgeBase(ABC):
    """Interface for knowledge base"""

    @abstractmethod
    async def search(self, query: str, language: str = "en") -> List[Dict]:
        """Search knowledge base"""
        pass

class IServiceHub(ABC):
    """Interface for service hub"""

    @abstractmethod
    def get_service(self, service_name: str) -> Any:
        """Get service by name"""
        pass 