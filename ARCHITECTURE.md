# Email Agent Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flask HR Assistant                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Employee   │  │      HR      │  │    Email     │        │
│  │   Dashboard  │  │   Dashboard  │  │   Dashboard  │  ← NEW │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                 │                   │                │
│         ↓                 ↓                   ↓                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  RAG Agent   │  │ Hiring Agent │  │ Email Agent  │  ← NEW │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                 │                   │                │
│         ↓                 ↓                   ↓                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    cv_db     │  │    cv_db     │  │  mailbox.db  │  ← NEW │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Email Agent Architecture

### Layer 1: User Interface (Jinja2 Templates)

```
┌────────────────────────────────────────────────────────────┐
│                     Email UI Layer                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  email_dashboard.html                                      │
│  ├─ Statistics Cards (4)                                   │
│  ├─ Quick Actions                                          │
│  ├─ Top Email Types                                        │
│  └─ Template List                                          │
│                                                            │
│  email_inbox.html                                          │
│  └─ Thread Cards (clickable)                              │
│     ├─ Subject                                             │
│     ├─ Participants                                        │
│     └─ Timestamp                                           │
│                                                            │
│  email_thread.html                                         │
│  └─ Message List                                           │
│     ├─ Sender/Recipient                                    │
│     ├─ Direction Badge                                     │
│     ├─ Email Type                                          │
│     └─ HTML Body                                           │
│                                                            │
│  email_sent.html                                           │
│  └─ Table + Modal                                          │
│                                                            │
│  email_compose.html                                        │
│  └─ AI Composer                                            │
│     ├─ Natural Language Input                              │
│     ├─ Template Dropdowns                                  │
│     └─ Examples                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layer 2: Routing (Flask Blueprints)

```
┌────────────────────────────────────────────────────────────┐
│                  routes/email_routes.py                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Blueprint: 'email' (/email/*)                            │
│                                                            │
│  GET  /email/dashboard                                     │
│       └→ render email_dashboard.html                      │
│                                                            │
│  GET  /email/inbox                                         │
│       └→ fetch threads                                     │
│       └→ render email_inbox.html                          │
│                                                            │
│  GET  /email/thread/<thread_id>                           │
│       └→ fetch messages                                    │
│       └→ render email_thread.html                         │
│                                                            │
│  GET  /email/sent                                          │
│       └→ fetch sent emails                                 │
│       └→ render email_sent.html                           │
│                                                            │
│  GET  /email/compose                                       │
│       └→ render email_compose.html                        │
│                                                            │
│  GET  /email/stats                                         │
│       └→ return JSON statistics                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layer 3: Business Logic (Orchestrator)

```
┌────────────────────────────────────────────────────────────┐
│             orchestrator/email_agent.py                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  class EmailAgentWrapper:                                  │
│                                                            │
│    __init__(self)                                          │
│    └─ Initialize database connection                       │
│    └─ Ensure table structure                              │
│                                                            │
│    get_inbox_threads(limit=50)                            │
│    └─ SELECT thread_id, MAX(timestamp), subject           │
│    └─ GROUP BY thread_id                                  │
│    └─ Get participants for each thread                     │
│    └─ Return list of thread summaries                     │
│                                                            │
│    get_thread_messages(thread_id)                         │
│    └─ SELECT * FROM mails WHERE thread_id = ?            │
│    └─ ORDER BY timestamp ASC                              │
│    └─ Return list of messages                             │
│                                                            │
│    get_sent_emails(limit=50)                              │
│    └─ SELECT * FROM mails WHERE direction = 'sent'        │
│    └─ ORDER BY timestamp DESC                             │
│    └─ Return list of sent emails                          │
│                                                            │
│    get_email_stats()                                       │
│    └─ COUNT(*) total emails                               │
│    └─ COUNT(*) WHERE direction = 'sent'                   │
│    └─ COUNT(*) WHERE direction = 'received'               │
│    └─ COUNT(DISTINCT thread_id)                           │
│    └─ Top 5 email types by count                          │
│    └─ Return statistics dictionary                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layer 4: Data Storage (SQLite)

```
┌────────────────────────────────────────────────────────────┐
│                      mailbox.db                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Table: mails                                              │
│  ├─ id (INTEGER PRIMARY KEY)                              │
│  ├─ direction (TEXT) ← 'sent' | 'received'               │
│  ├─ timestamp (TEXT) ← ISO format                         │
│  ├─ sender_email (TEXT)                                   │
│  ├─ recipient_email (TEXT)                                │
│  ├─ subject (TEXT)                                        │
│  ├─ body (TEXT) ← HTML content                           │
│  ├─ status (TEXT) ← 'sent' | 'queued' | 'failed'        │
│  ├─ email_type (TEXT) ← Template type                     │
│  ├─ thread_id (TEXT) ← UUID for threading                │
│  └─ in_reply_to (INTEGER) ← FK to parent message         │
│                                                            │
│  Indexes (recommended):                                    │
│  ├─ idx_thread_id ON (thread_id)                         │
│  ├─ idx_recipient ON (recipient_email)                    │
│  └─ idx_timestamp ON (timestamp)                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Viewing Inbox

```
User                  UI                Routes            Agent           Database
  │                   │                   │                │                │
  │  Click Inbox      │                   │                │                │
  ├──────────────────→│                   │                │                │
  │                   │  GET /email/inbox │                │                │
  │                   ├──────────────────→│                │                │
  │                   │                   │ get_inbox_     │                │
  │                   │                   │ threads()      │                │
  │                   │                   ├───────────────→│                │
  │                   │                   │                │ SELECT threads │
  │                   │                   │                ├───────────────→│
  │                   │                   │                │ Return rows    │
  │                   │                   │                ←────────────────┤
  │                   │                   │ Return threads │                │
  │                   │                   ←────────────────┤                │
  │                   │ Render template   │                │                │
  │                   ←───────────────────┤                │                │
  │  Display Inbox    │                   │                │                │
  ←───────────────────┤                   │                │                │
  │                   │                   │                │                │
```

### Opening a Thread

```
User                  UI                Routes            Agent           Database
  │                   │                   │                │                │
  │  Click Thread     │                   │                │                │
  ├──────────────────→│                   │                │                │
  │                   │ GET /email/       │                │                │
  │                   │ thread/<id>       │                │                │
  │                   ├──────────────────→│                │                │
  │                   │                   │ get_thread_    │                │
  │                   │                   │ messages(id)   │                │
  │                   │                   ├───────────────→│                │
  │                   │                   │                │ SELECT msgs    │
  │                   │                   │                │ WHERE thread=id│
  │                   │                   │                ├───────────────→│
  │                   │                   │                │ Return msgs    │
  │                   │                   │                ←────────────────┤
  │                   │                   │ Return messages│                │
  │                   │                   ←────────────────┤                │
  │                   │ Render template   │                │                │
  │                   ←───────────────────┤                │                │
  │  Display Thread   │                   │                │                │
  ←───────────────────┤                   │                │                │
  │                   │                   │                │                │
```

### Loading Statistics (AJAX)

```
User                  UI                Routes            Agent           Database
  │                   │                   │                │                │
  │  Page Load        │                   │                │                │
  ├──────────────────→│                   │                │                │
  │                   │  JS: fetch        │                │                │
  │                   │  /email/stats     │                │                │
  │                   ├──────────────────→│                │                │
  │                   │                   │ get_email_     │                │
  │                   │                   │ stats()        │                │
  │                   │                   ├───────────────→│                │
  │                   │                   │                │ COUNT queries  │
  │                   │                   │                ├───────────────→│
  │                   │                   │                │ Return counts  │
  │                   │                   │                ←────────────────┤
  │                   │                   │ Return JSON    │                │
  │                   │                   ←────────────────┤                │
  │                   │ Update DOM        │                │                │
  │                   │ elements          │                │                │
  │  See Stats        │                   │                │                │
  ←───────────────────┤                   │                │                │
  │                   │                   │                │                │
```

---

## Integration Points

### With Existing HR System

```
┌─────────────────────────────────────────────────────────────┐
│                  app.py (Main Flask App)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Blueprints Registered:                                     │
│  ├─ auth_bp      → /auth/*      (Login, Signup, Logout)   │
│  ├─ employee_bp  → /employee/*  (RAG Dashboard)            │
│  ├─ hr_bp        → /hr/*        (Hiring Dashboard)         │
│  └─ email_bp     → /email/*     (Email Dashboard) ← NEW    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### With Orchestrator

```
┌─────────────────────────────────────────────────────────────┐
│            orchestrator/orchestrator.py                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Registered Agents:                                         │
│  ├─ 'rag_agent'     → RAGAgentWrapper()                    │
│  ├─ 'hiring_agent'  → HiringAgentWrapper()                │
│  └─ 'email_agent'   → EmailAgentWrapper() ← NEW            │
│                                                             │
│  Role Mapping:                                              │
│  ├─ 'employee' → 'rag_agent'                               │
│  └─ 'hr'       → 'hiring_agent'                            │
│                                                             │
│  get_agent_by_name('email_agent')                          │
│  └─ Returns EmailAgentWrapper instance                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Dependencies

### Backend Dependencies

```
Flask Application
    │
    ├─ Flask Framework
    │  ├─ flask
    │  └─ flask-sqlalchemy
    │
    ├─ Authentication (Existing)
    │  ├─ werkzeug.security
    │  └─ session management
    │
    └─ Email Agent (NEW)
       ├─ SQLite3 (built-in)
       ├─ orchestrator.email_agent
       └─ routes.email_routes
```

### Frontend Dependencies

```
HTML Templates
    │
    ├─ Bootstrap 5 (CDN)
    │  └─ https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/
    │
    ├─ Bootstrap Icons (CDN)
    │  └─ https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/
    │
    └─ Custom CSS
       └─ /static/css/style.css
```

---

## Security Architecture

### Authentication Flow

```
┌──────────────────────────────────────────────────────────┐
│  All email routes protected by require_hr_login()        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  def require_hr_login():                                 │
│    if 'user_id' not in session:                         │
│      return None  → Redirect to login                   │
│    if session.get('role') != 'hr':                      │
│      return None  → Unauthorized                        │
│    return True                                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Data Security

```
┌──────────────────────────────────────────────────────────┐
│  Database Security                                       │
├──────────────────────────────────────────────────────────┤
│  ✓ Parameterized SQL queries (prevents injection)        │
│  ✓ Session-based authentication                          │
│  ✓ Role-based access control (HR only)                   │
│  ✓ HTML escaping in templates                            │
│  ✓ HTTPS recommended for production                      │
└──────────────────────────────────────────────────────────┘
```

---

## File Organization

```
/project
│
├─ app.py                          Main Flask application
│
├─ orchestrator/
│  ├─ __init__.py
│  ├─ orchestrator.py             Central agent router
│  ├─ rag_agent.py                RAG agent (existing)
│  ├─ hiring_agent.py             Hiring agent (existing)
│  └─ email_agent.py              Email agent (NEW)
│
├─ routes/
│  ├─ __init__.py
│  ├─ auth_routes.py              Auth (existing)
│  ├─ employee_routes.py          Employee (existing)
│  ├─ hr_routes.py                HR (existing)
│  └─ email_routes.py             Email (NEW)
│
├─ templates/
│  ├─ base.html                   Base template (modified)
│  ├─ login.html
│  ├─ signup.html
│  ├─ employee_dashboard.html
│  ├─ hr_dashboard.html           (modified)
│  ├─ email_dashboard.html        (NEW)
│  ├─ email_inbox.html            (NEW)
│  ├─ email_thread.html           (NEW)
│  ├─ email_sent.html             (NEW)
│  └─ email_compose.html          (NEW)
│
├─ static/
│  └─ css/
│     └─ style.css                (modified with email styles)
│
├─ Database Files
│  ├─ app.db                      User authentication
│  ├─ cv_db/                      CV storage
│  └─ mailbox.db                  Email storage (NEW)
│
└─ Data Files
   ├─ employees.json              Employee database (NEW)
   └─ email_templates_agentic.csv Email templates (NEW)
```

---

## Scalability Considerations

### Current Architecture
- Single SQLite database
- Synchronous operations
- Session-based auth
- Single server deployment

### Recommended Improvements for Production

```
┌──────────────────────────────────────────────────────────┐
│  Production Enhancements                                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Database                                             │
│     ├─ Migrate to PostgreSQL                            │
│     ├─ Add connection pooling                           │
│     └─ Implement database backups                       │
│                                                          │
│  2. Email Sending                                        │
│     ├─ Add message queue (Celery/RQ)                    │
│     ├─ Async email sending                              │
│     └─ Retry logic for failures                         │
│                                                          │
│  3. Performance                                          │
│     ├─ Add Redis caching                                │
│     ├─ Pagination for large datasets                    │
│     └─ Database indexes                                 │
│                                                          │
│  4. Monitoring                                           │
│     ├─ Logging (structured logs)                        │
│     ├─ Error tracking (Sentry)                          │
│     └─ Performance monitoring                           │
│                                                          │
│  5. Security                                             │
│     ├─ Rate limiting                                    │
│     ├─ CSRF protection                                  │
│     └─ Input validation                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development (Current)

```
┌─────────────────────────────┐
│   Flask Development Server  │
│   (localhost:5000)          │
│                             │
│   ├─ SQLite databases       │
│   ├─ File storage           │
│   └─ Session storage        │
└─────────────────────────────┘
```

### Production (Recommended)

```
┌──────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
└─────────────────────┬────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼─────┐            ┌─────▼────┐
    │  WSGI    │            │  WSGI    │
    │  Server  │            │  Server  │
    │ (Gunicorn)│           │ (Gunicorn)│
    └────┬─────┘            └─────┬────┘
         │                         │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │   PostgreSQL Database   │
         └─────────────────────────┘
```

---

This architecture document provides a complete technical overview of how the Email Agent integrates with your existing Flask HR Assistant system.
