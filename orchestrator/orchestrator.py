"""
Orchestrator - Central brain for routing requests to appropriate agents

This module provides a flexible, extensible system for managing multiple AI agents.
To add a new agent:
1. Create a new agent file in this directory (e.g., new_agent.py)
2. Import it and register it using register_agent()
3. The orchestrator will automatically route requests based on user role or query type
"""
from typing import Dict, Any, Optional, Callable
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hiring-agent'))


class Orchestrator:
    """
    Central orchestrator that routes requests to appropriate agents
    
    Agents are registered by name and can be selected based on:
    - User role (employee, hr, etc.)
    - Query type (detected from query content)
    - Explicit agent name
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.role_mapping: Dict[str, str] = {
            'employee': 'rag_agent',
            'hr': 'hiring_agent'
        }
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize and register all available agents"""
        try:
            from orchestrator.rag_agent import RAGAgentWrapper
            self.register_agent('rag_agent', RAGAgentWrapper(), role='employee')
            print("✓ RAG Agent registered")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize RAG Agent: {e}")

        try:
            from orchestrator.hiring_agent import HiringAgentWrapper
            self.register_agent('hiring_agent', HiringAgentWrapper(), role='hr')
            print("✓ Hiring Agent registered")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize Hiring Agent: {e}")

        try:
            from orchestrator.email_agent import EmailAgentWrapper
            self.register_agent('email_agent', EmailAgentWrapper())
            print("✓ Email Agent registered")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize Email Agent: {e}")
    
    def register_agent(self, name: str, agent_instance: Any, role: Optional[str] = None):
        """
        Register a new agent with the orchestrator
        
        Args:
            name: Unique identifier for the agent (e.g., 'rag_agent', 'hiring_agent')
            agent_instance: Instance of the agent class
            role: Optional role mapping (e.g., 'employee', 'hr')
        """
        self.agents[name] = {
            'instance': agent_instance,
            'role': role
        }
        if role:
            self.role_mapping[role] = name
        print(f"Registered agent: {name} (role: {role or 'none'})")
    
    def get_agent_by_role(self, role: str) -> Optional[Any]:
        """
        Get agent instance based on user role
        
        Args:
            role: User role ('employee' or 'hr')
            
        Returns:
            Agent instance or None if not found
        """
        agent_name = self.role_mapping.get(role)
        if agent_name and agent_name in self.agents:
            return self.agents[agent_name]['instance']
        
        # Attempt lazy initialization if agent not present yet
        try:
            if role == 'employee':
                from orchestrator.rag_agent import RAGAgentWrapper
                self.register_agent('rag_agent', RAGAgentWrapper(), role='employee')
                return self.agents.get('rag_agent', {}).get('instance')
            if role == 'hr':
                from orchestrator.hiring_agent import HiringAgentWrapper
                self.register_agent('hiring_agent', HiringAgentWrapper(), role='hr')
                return self.agents.get('hiring_agent', {}).get('instance')
        except Exception as e:
            # Leave as None; route_request will surface the error message
            pass
        
        return None
    
    def get_agent_by_name(self, agent_name: str) -> Optional[Any]:
        """
        Get agent instance by explicit name
        
        Args:
            agent_name: Name of the agent ('rag_agent', 'hiring_agent', etc.)
            
        Returns:
            Agent instance or None if not found
        """
        if agent_name in self.agents:
            return self.agents[agent_name]['instance']
        return None
    
    def route_request(self, user_role: str, query: Optional[str] = None, 
                     agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent
        
        Args:
            user_role: User role ('employee' or 'hr')
            query: Optional query text (for future query-based routing)
            agent_name: Optional explicit agent name (overrides role-based routing)
            
        Returns:
            Dict with agent instance and metadata
        """
        # Explicit agent name takes priority
        if agent_name:
            agent = self.get_agent_by_name(agent_name)
            if agent:
                return {
                    'agent': agent,
                    'agent_name': agent_name,
                    'selected_by': 'explicit'
                }
            else:
                return {
                    'agent': None,
                    'error': f'Agent "{agent_name}" not found'
                }
        
        # Route by user role
        agent = self.get_agent_by_role(user_role)
        if agent:
            agent_name = self.role_mapping.get(user_role)
            return {
                'agent': agent,
                'agent_name': agent_name,
                'selected_by': 'role'
            }
        
        return {
            'agent': None,
            'error': f'No agent found for role "{user_role}"'
        }
    
    def list_agents(self) -> Dict[str, Any]:
        """List all registered agents"""
        return {
            'agents': list(self.agents.keys()),
            'role_mapping': self.role_mapping,
            'total_agents': len(self.agents)
        }


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

