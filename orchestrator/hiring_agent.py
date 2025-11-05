"""
Hiring Agent Wrapper - Integrates the existing Hiring Agent system
"""
import sys
import os

# Add hiring-agent directory to path
hiring_agent_path = os.path.join(os.path.dirname(__file__), '..', 'hiring-agent')
sys.path.insert(0, hiring_agent_path)

try:
    from hiring_agent import HiringAgent
    # Import config from parent directory
    parent_dir = os.path.join(os.path.dirname(__file__), '..')
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from config import Config
except ImportError as e:
    print(f"Warning: Could not import Hiring Agent: {e}")
    HiringAgent = None
    Config = None


class HiringAgentWrapper:
    """
    Wrapper for the HiringAgent system to integrate with orchestrator
    
    This class provides a clean interface to the existing Hiring Agent
    located in hiring-agent/hiring_agent.py
    """
    
    def __init__(self):
        """Initialize the Hiring Agent"""
        if HiringAgent is None:
            raise ImportError("Hiring Agent not available")
        if Config is None:
            raise ImportError("Config not available")
        
        # Get database path and API key
        cv_db_path = os.path.join(os.path.dirname(__file__), '..', Config.RAG_DB_PATH)
        cv_db_path = os.path.abspath(cv_db_path)
        api_key = Config.GOOGLE_API_KEY
        
        self.agent = HiringAgent(api_key=api_key, cv_db_path=cv_db_path)
        print("Hiring Agent Wrapper initialized")
    
    def process_job_hiring(self, job_description: str, 
                          initial_retrieval: int = 30, 
                          final_candidates: int = 5) -> list:
        """
        Process job hiring with candidate evaluation
        
        Args:
            job_description: Job requirements and description
            initial_retrieval: Number of CVs to retrieve initially (default: 30)
            final_candidates: Number of final candidates to evaluate (default: 5)
            
        Returns:
            List of candidate dictionaries formatted for UI display
        """
        try:
            print(f"\n[Wrapper] Starting hiring process...")
            print(f"[Wrapper] Initial retrieval: {initial_retrieval}, Final candidates: {final_candidates}")
            
            # Run the core hiring flow
            candidates = self.agent.process_job_hiring(
                job_description=job_description,
                initial_retrieval=initial_retrieval,
                final_candidates=final_candidates
            )
            
            print(f"[Wrapper] Received {len(candidates) if candidates else 0} candidates from agent")
            
            if not candidates:
                return []
            
            # Convert candidates to UI-friendly format
            result = []
            for i, candidate in enumerate(candidates[:final_candidates], 1):
                print(f"[Wrapper] Processing candidate {i}: {getattr(candidate, 'name', 'Unknown')}")
                
                # Extract data from candidate object
                candidate_dict = self._format_candidate_for_ui(candidate)
                result.append(candidate_dict)
                
                # Debug output
                print(f"  - Name: {candidate_dict['name']}")
                print(f"  - Score: {candidate_dict['overall_score']:.1f}")
                print(f"  - Decision: {candidate_dict['decision']}")
                print(f"  - Skills: {len(candidate_dict['key_skills'])} found")
            
            print(f"[Wrapper] Returning {len(result)} formatted candidates\n")
            return result
            
        except Exception as e:
            print(f"[Wrapper] ERROR in process_job_hiring: {str(e)}")
            import traceback
            traceback.print_exc()
            return [{'error': f"Error processing hiring: {str(e)}"}]
    
    def _format_candidate_for_ui(self, candidate) -> dict:
        """
        Format a Candidate object for UI display
        Ensures all required fields are present with proper fallbacks
        """
        # Extract basic info
        name = getattr(candidate, 'name', None) or \
               getattr(candidate, 'filename', 'Unknown')
        
        if name == 'Unknown' or not name.strip():
            filename = getattr(candidate, 'filename', '')
            if filename:
                name = os.path.splitext(filename)[0]
        
        # Extract score
        overall_score = getattr(candidate, 'overall_score', 0)
        if not isinstance(overall_score, (int, float)) or overall_score == 0:
            # Try to get from scoring breakdown
            scoring = getattr(candidate, 'scoring', {})
            if isinstance(scoring, dict):
                overall_score = scoring.get('overall_score', 0)
        
        # Ensure score is a valid number
        try:
            overall_score = float(overall_score)
        except (ValueError, TypeError):
            overall_score = 0.0
        
        # Extract decision
        decision = getattr(candidate, 'decision', 'PENDING')
        if not decision or str(decision).strip().upper() == 'PENDING':
            # Infer decision from score
            if overall_score >= 85:
                decision = 'STRONG_HIRE'
            elif overall_score >= 70:
                decision = 'HIRE'
            elif overall_score >= 50:
                decision = 'MAYBE'
            else:
                decision = 'REJECT'
        
        # Extract skills
        key_skills = getattr(candidate, 'key_skills', []) or []
        if not isinstance(key_skills, list):
            key_skills = []
        
        # Extract experience
        relevant_experience = getattr(candidate, 'relevant_experience', []) or []
        if not isinstance(relevant_experience, list):
            relevant_experience = []
        
        # Extract education
        education = getattr(candidate, 'education_qualifications', []) or []
        if not isinstance(education, list):
            education = []
        
        # Extract achievements
        achievements = getattr(candidate, 'achievements', []) or []
        if not isinstance(achievements, list):
            achievements = []
        
        # Extract concerns
        concerns = getattr(candidate, 'concerns', []) or []
        if not isinstance(concerns, list):
            concerns = []
        
        # Extract reasoning
        reasoning = getattr(candidate, 'reasoning', '') or ''
        if not reasoning:
            reasoning = "Evaluation completed. See skills and experience for details."
        
        # Extract scoring breakdown
        scoring = getattr(candidate, 'scoring', {})
        if not isinstance(scoring, dict):
            scoring = {}
        
        # Build UI-formatted dictionary
        return {
            'name': name,
            'filename': getattr(candidate, 'filename', name),
            'overall_score': round(overall_score, 1),
            'score': round(overall_score, 1),  # Include both for compatibility
            'decision': decision,
            'credibility_status': getattr(candidate, 'credibility_status', 'NOT_VERIFIED'),
            'reasoning': reasoning,
            'key_skills': key_skills[:10],  # Limit to top 10
            'relevant_experience': relevant_experience[:5],  # Limit to top 5
            'education_qualifications': education,
            'achievements': achievements[:5],  # Limit to top 5
            'concerns': concerns,
            'soft_skills': getattr(candidate, 'soft_skills', []) or [],
            'scoring': scoring,
            'evaluation_timestamp': getattr(candidate, 'evaluation_timestamp', ''),
            'resume_summary': getattr(candidate, 'resume_summary', '')[:500]  # Truncate
        }
    
    def add_cv(self, file_path: str, metadata: dict = None) -> dict:
        """
        Add a CV to the database
        
        Args:
            file_path: Path to CV file
            metadata: Optional metadata dictionary
            
        Returns:
            Dict with success status
        """
        try:
            success = self.agent.add_cv(file_path, metadata)
            return {'success': success, 'file_path': file_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_cv_stats(self) -> dict:
        """Get CV database statistics"""
        try:
            return self.agent.get_cv_stats()
        except Exception as e:
            return {'error': str(e)}
    
    def search_cvs(self, job_description: str, limit: int = 10) -> list:
        """
        Search CVs matching job description
        
        Args:
            job_description: Job requirements
            limit: Maximum number of results
            
        Returns:
            List of matching CVs
        """
        try:
            return self.agent.search_cvs(job_description, limit=limit)
        except Exception as e:
            return [{'error': str(e)}]