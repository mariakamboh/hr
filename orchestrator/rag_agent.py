"""
RAG Agent Wrapper - Integrates the existing RAG system
"""
import sys
import os

# Add hiring-agent directory to path
hiring_agent_path = os.path.join(os.path.dirname(__file__), '..', 'hiring-agent')
sys.path.insert(0, hiring_agent_path)

try:
    from unified_RAG import EmployeeRAG
    # Import config from parent directory
    parent_dir = os.path.join(os.path.dirname(__file__), '..')
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from config import Config
except ImportError as e:
    print(f"Warning: Could not import RAG system: {e}")
    EmployeeRAG = None
    Config = None


class RAGAgentWrapper:
    """
    Wrapper for the EmployeeRAG system to integrate with orchestrator
    
    This class provides a clean interface to the existing RAG system
    located in hiring-agent/unified_RAG.py
    """
    
    def __init__(self):
        """Initialize the RAG agent"""
        if EmployeeRAG is None:
            raise ImportError("RAG system not available")
        if Config is None:
            raise ImportError("Config not available")
        
        # Get database path (relative to app root)
        db_path = os.path.join(os.path.dirname(__file__), '..', Config.RAG_DB_PATH)
        db_path = os.path.abspath(db_path)
        self.rag = EmployeeRAG(db_path=db_path)
        print("RAG Agent Wrapper initialized")
    
    def query(self, question: str) -> str:
        """
        Query company documents using RAG
        
        Args:
            question: User's question about company documents
            
        Returns:
            Answer string
        """
        try:
            return self.rag.query_documents(question)
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def get_stats(self) -> dict:
        """Get RAG system statistics"""
        try:
            return self.rag.get_database_stats()
        except Exception as e:
            return {'error': str(e)}
    
    def list_documents(self) -> list:
        """List all available documents"""
        try:
            return self.rag.list_all_documents()
        except Exception as e:
            return []

