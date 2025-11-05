# Flask RAG & Hiring Agent System

A modular Flask web application with an intelligent orchestrator that routes requests to appropriate AI agents based on user roles.

## Features

- **Authentication System**: Signup and login with role-based access (Employee/HR)
- **Employee Dashboard**: Query company documents using RAG (Retrieval-Augmented Generation)
- **HR Dashboard**: Manage candidate hiring with AI-powered evaluation
- **Modular Orchestrator**: Easily extensible system for adding new agents

## Project Structure

```
/app
 ├── /routes
 │    ├── auth_routes.py        → signup/login routes
 │    ├── employee_routes.py    → employee dashboard routes
 │    ├── hr_routes.py          → hr dashboard routes
 │
 ├── /templates                 → HTML files
 ├── /static                    → CSS/JS files
 ├── /orchestrator
 │    ├── orchestrator.py       → main orchestrator logic
 │    ├── rag_agent.py          → connect existing RAG system
 │    ├── hiring_agent.py       → connect existing Hiring Agent
 │    └── (future agents here)
 │
 ├── database.py                → database setup and user model
 ├── app.py                     → main Flask entry point
 └── config.py                  → settings and keys
```

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables** (optional):
```bash
export GOOGLE_API_KEY="your-api-key"
export SECRET_KEY="your-secret-key"
```

3. **Run the application**:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Signup
1. Navigate to `/auth/signup`
2. Create an account with role: **Employee** or **HR**

### Employee Dashboard
- Access at `/employee/dashboard` after login
- Ask questions about company documents
- View document statistics

### HR Dashboard
- Access at `/hr/dashboard` after login
- Upload CVs to the database
- Process job hiring with candidate evaluation
- View CV database statistics

## Orchestrator Architecture

The orchestrator is designed to be easily extensible. To add a new agent:

1. **Create agent wrapper** in `/orchestrator/`:
```python
# orchestrator/new_agent.py
class NewAgentWrapper:
    def __init__(self):
        # Initialize your agent
        pass
    
    def process(self, input_data):
        # Process request
        return result
```

2. **Register in orchestrator**:
```python
from orchestrator.new_agent import NewAgentWrapper
orchestrator.register_agent('new_agent', NewAgentWrapper(), role='user_role')
```

3. **Create routes** (optional):
Add routes in `/routes/` to expose agent functionality via API.

## Configuration

Edit `config.py` to customize:
- Database path
- API keys
- Secret key for session management

## Database

The application uses SQLite by default for user authentication. The RAG and Hiring Agent systems use ChromaDB for document/CV storage.

## Notes

- Ensure the `hiring-agent` directory exists with the RAG and Hiring Agent implementations
- The `cv_db` directory will be created automatically for ChromaDB storage
- CV uploads are stored in `/uploads/cvs/`

