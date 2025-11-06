"""
Email Agent Wrapper - Integrates the Email Agent system with AI-powered email generation
"""
import os
import sys
import sqlite3
import json
import csv
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config

# Try to import Google Generative AI for email generation
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-generativeai not available. Email generation will be limited.")

# Try to import SendGrid for email sending (optional)
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("Warning: SendGrid not available. Emails will be saved to database but not sent.")


class EmailAgentWrapper:
    """
    Wrapper for the Email Agent system to integrate with orchestrator
    Provides AI-powered email generation, template matching, and sending capabilities
    """

    def __init__(self):
        """Initialize the Email Agent"""
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'mailbox.db')
        self.db_path = os.path.abspath(self.db_path)
        self.templates_path = os.path.join(os.path.dirname(__file__), '..', 'email_templates_agentic.csv')
        self.employees_path = os.path.join(os.path.dirname(__file__), '..', 'employees.json')
        
        # Load templates and employees
        self.email_templates = self._load_templates()
        self.employees = self._load_employees()
        
        # Initialize AI model if available
        self.ai_model = None
        if GENAI_AVAILABLE and Config.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=Config.GOOGLE_API_KEY)
                # Allow model override via env, default to a supported model
                model_name = os.environ.get('GOOGLE_GEMINI_MODEL', 'gemini-2.0-flash-exp')
                self.ai_model = genai.GenerativeModel(model_name)
                print(f"✓ AI model initialized for email generation: {model_name}")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize AI model: {e}")
        
        # Initialize SendGrid if available
        self.sendgrid_client = None
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.email_user = os.environ.get('EMAIL_USER', 'hr@indigo.com')
        
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            try:
                self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
                print("✓ SendGrid initialized for email sending")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize SendGrid: {e}")
        
        self._ensure_db()
        print("Email Agent Wrapper initialized")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load email templates from CSV file"""
        templates = {}
        try:
            if os.path.exists(self.templates_path):
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email_type = row.get('EmailType', '').lower().strip()
                        instruction = row.get('Instruction', '').strip()
                        if email_type and instruction:
                            templates[email_type] = instruction
                print(f"✓ Loaded {len(templates)} email templates")
            else:
                print(f"⚠ Warning: Templates file not found: {self.templates_path}")
        except Exception as e:
            print(f"⚠ Warning: Could not load templates: {e}")
        return templates
    
    def _load_employees(self) -> List[Dict[str, Any]]:
        """Load employees from JSON file"""
        employees = []
        try:
            if os.path.exists(self.employees_path):
                with open(self.employees_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    employees = data.get('indigo_employees', [])
                print(f"✓ Loaded {len(employees)} employees")
            else:
                print(f"⚠ Warning: Employees file not found: {self.employees_path}")
        except Exception as e:
            print(f"⚠ Warning: Could not load employees: {e}")
        return employees

    def _ensure_db(self):
        """Ensure mailbox database exists with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Create mails table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT,
            timestamp TEXT,
            sender_email TEXT,
            recipient_email TEXT,
            subject TEXT,
            body TEXT,
            status TEXT,
            email_type TEXT,
            thread_id TEXT,
            in_reply_to INTEGER
        )
        """)

        conn.commit()
        conn.close()

    def get_inbox_threads(self, limit=50):
        """Get inbox threads summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT thread_id, MAX(timestamp) as last_time, subject
                FROM mails
                GROUP BY thread_id
                ORDER BY last_time DESC
                LIMIT ?
            """, (limit,))

            rows = cur.fetchall()
            threads = []

            for row in rows:
                tid = row["thread_id"]
                # Get participants
                cur.execute("""
                    SELECT sender_email, recipient_email FROM mails
                    WHERE thread_id = ?
                    LIMIT 10
                """, (tid,))
                parts = cur.fetchall()
                participants = set()
                for p in parts:
                    if p[0]:
                        participants.add(p[0])
                    if p[1]:
                        participants.add(p[1])

                threads.append({
                    "thread_id": tid,
                    "last_time": row["last_time"],
                    "subject": row["subject"] or "(No Subject)",
                    "participants": ", ".join(list(participants)[:5])
                })

            conn.close()
            return threads
        except Exception as e:
            print(f"Error fetching threads: {e}")
            return []

    def get_thread_messages(self, thread_id):
        """Get all messages in a thread"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM mails
                WHERE thread_id = ?
                ORDER BY timestamp ASC
            """, (thread_id,))

            msgs = [dict(r) for r in cur.fetchall()]
            conn.close()
            return msgs
        except Exception as e:
            print(f"Error fetching thread messages: {e}")
            return []

    def get_sent_emails(self, limit=50):
        """Get sent emails"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM mails
                WHERE direction = 'sent'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            emails = [dict(r) for r in cur.fetchall()]
            conn.close()
            return emails
        except Exception as e:
            print(f"Error fetching sent emails: {e}")
            return []

    def get_email_stats(self):
        """Get email statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Total emails
            cur.execute("SELECT COUNT(*) FROM mails")
            total = cur.fetchone()[0]

            # Sent emails
            cur.execute("SELECT COUNT(*) FROM mails WHERE direction = 'sent'")
            sent = cur.fetchone()[0]

            # Received emails
            cur.execute("SELECT COUNT(*) FROM mails WHERE direction = 'received'")
            received = cur.fetchone()[0]

            # Total threads
            cur.execute("SELECT COUNT(DISTINCT thread_id) FROM mails")
            threads = cur.fetchone()[0]

            # Recent email types
            cur.execute("""
                SELECT email_type, COUNT(*) as count
                FROM mails
                WHERE email_type IS NOT NULL
                GROUP BY email_type
                ORDER BY count DESC
                LIMIT 5
            """)
            email_types = [{"type": row[0], "count": row[1]} for row in cur.fetchall()]

            conn.close()

            return {
                "total_emails": total,
                "sent_emails": sent,
                "received_emails": received,
                "total_threads": threads,
                "top_email_types": email_types
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {
                "total_emails": 0,
                "sent_emails": 0,
                "received_emails": 0,
                "total_threads": 0,
                "top_email_types": []
            }
    
    def find_employees(self, query: str) -> List[Dict[str, Any]]:
        """
        Find employees matching a search query
        Supports searching by name, department, designation, or email
        """
        if not self.employees:
            return []
        
        query_lower = query.lower().strip()
        matches = []
        
        for emp in self.employees:
            name = emp.get('name', '').lower()
            email = emp.get('email', '').lower()
            dept = emp.get('department', '').lower()
            designation = emp.get('designation', '').lower()
            
            # Check if query matches any field
            if (query_lower in name or 
                query_lower in email or 
                query_lower in dept or 
                query_lower in designation or
                name.startswith(query_lower) or
                email.startswith(query_lower)):
                matches.append(emp)
        
        return matches
    
    def match_email_type(self, query: str) -> Optional[str]:
        """
        Match the query to an email type from templates
        Returns the matched email type or None
        """
        query_lower = query.lower()
        
        # Direct match first
        for email_type in self.email_templates.keys():
            if email_type in query_lower:
                return email_type
        
        # Fuzzy matching - check for keywords
        email_keywords = {
            'offer letter': ['offer', 'offer letter', 'job offer'],
            'appointment letter': ['appointment', 'appoint'],
            'joining reminder': ['joining', 'reminder', 'join date'],
            'onboarding schedule': ['onboarding', 'orientation'],
            'probation completion': ['probation', 'probation complete'],
            'promotion': ['promotion', 'promoted', 'promote'],
            'salary increment': ['salary', 'raise', 'increment', 'pay raise'],
            'leave approval': ['leave approval', 'approved leave'],
            'leave rejection': ['leave rejection', 'reject leave', 'leave denied'],
            'attendance warning': ['attendance warning', 'attendance issue'],
            'performance warning': ['performance warning', 'performance issue'],
            'appreciation': ['appreciation', 'appreciate', 'great work', 'well done'],
            'project assignment': ['project assignment', 'assign project'],
            'training invitation': ['training', 'training invite'],
            'meeting invite': ['meeting', 'meeting invite', 'meet'],
            'task reminder': ['task reminder', 'remind task'],
            'birthday': ['birthday', 'happy birthday', 'birth day'],
            'work anniversary': ['anniversary', 'work anniversary'],
            'farewell': ['farewell', 'goodbye', 'leaving'],
            'resignation acceptance': ['resignation', 'resign'],
            'termination': ['termination', 'terminate', 'fired'],
            'holiday announcement': ['holiday', 'holiday announcement'],
            'policy update': ['policy', 'policy update'],
            'general announcement': ['announcement', 'announce']
        }
        
        for email_type, keywords in email_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return email_type
        
        return None
    
    def generate_email_content(self, email_type: str, recipient_info: Dict[str, Any], 
                               query_context: str) -> Dict[str, str]:
        """
        Generate email content using AI or template
        Returns dict with 'subject' and 'body' keys
        """
        if not self.ai_model:
            # Fallback: Use template instruction to generate basic email
            template_instruction = self.email_templates.get(email_type, 
                f"Write a professional {email_type} email")
            
            # Simple template-based generation
            recipient_name = recipient_info.get('name', 'Employee')
            subject = f"{email_type.title()} - {recipient_name}"
            body = f"""
            <html>
            <body>
            <p>Dear {recipient_name},</p>
            <p>{template_instruction}</p>
            <p>Best regards,<br>HR Team</p>
            </body>
            </html>
            """
            return {'subject': subject, 'body': body}
        
        # AI-powered generation
        try:
            template_instruction = self.email_templates.get(email_type, 
                f"Write a professional {email_type} email")
            
            recipient_name = recipient_info.get('name', 'Employee')
            recipient_dept = recipient_info.get('department', '')
            recipient_designation = recipient_info.get('designation', '')
            recipient_email = recipient_info.get('email', '')
            
            prompt = f"""You are an HR professional writing a professional email.

EMAIL TYPE: {email_type}
TEMPLATE INSTRUCTION: {template_instruction}

RECIPIENT INFORMATION:
- Name: {recipient_name}
- Designation: {recipient_designation}
- Department: {recipient_dept}
- Email: {recipient_email}

ADDITIONAL CONTEXT FROM REQUEST: {query_context}

Generate a professional, personalized email with:
1. A clear, professional subject line
2. A well-formatted HTML email body that includes:
   - Appropriate greeting
   - Clear, professional content based on the email type
   - Any relevant details from the context
   - Professional closing

Respond in JSON format:
{{
    "subject": "Email subject line",
    "body": "<html>...</html>"
}}

Make the email professional, warm, and appropriate for HR communications."""

            response = self.ai_model.generate_content(prompt)
            
            # Parse response (try to extract JSON)
            response_text = response.text.strip()
            
            # Try to extract JSON from response (handle nested JSON)
            # Look for JSON object boundaries
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end+1]
                try:
                    result = json.loads(json_str)
                    return {
                        'subject': result.get('subject', f"{email_type.title()} - {recipient_name}"),
                        'body': result.get('body', response_text)
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Try regex for simple JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        'subject': result.get('subject', f"{email_type.title()} - {recipient_name}"),
                        'body': result.get('body', response_text)
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Extract subject and body from response
            lines = response_text.split('\n')
            subject = f"{email_type.title()} - {recipient_name}"
            body = response_text
            
            # Try to extract subject if present
            for i, line in enumerate(lines):
                if 'subject' in line.lower() or 'subject:' in line.lower():
                    subject_match = re.search(r'(?i)subject[:\s]+(.+)', line)
                    if subject_match:
                        subject = subject_match.group(1).strip().strip('"\'')
                    break
            
            # Wrap body in HTML if not already
            if '<html' not in body.lower():
                body = f"""
                <html>
                <body>
                {body.replace(chr(10), '<br>')}
                </body>
                </html>
                """
            
            return {'subject': subject, 'body': body}
            
        except Exception as e:
            print(f"Error generating email content: {e}")
            # Fallback generation
            recipient_name = recipient_info.get('name', 'Employee')
            subject = f"{email_type.title()} - {recipient_name}"
            body = f"""
            <html>
            <body>
            <p>Dear {recipient_name},</p>
            <p>This is regarding: {email_type}</p>
            <p>Details: {query_context}</p>
            <p>Best regards,<br>HR Team</p>
            </body>
            </html>
            """
            return {'subject': subject, 'body': body}
    
    def send_email_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SendGrid"""
        if not self.sendgrid_client:
            return False
        
        try:
            message = Mail(
                from_email=self.email_user,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.sendgrid_client.send(message)
            return response.status_code in [200, 201, 202]
        except Exception as e:
            print(f"Error sending email via SendGrid: {e}")
            return False
    
    def save_email_to_db(self, direction: str, sender_email: str, recipient_email: str,
                        subject: str, body: str, email_type: str, 
                        status: str = 'sent', thread_id: Optional[str] = None) -> int:
        """Save email to database and return the email ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Generate thread_id if not provided
            if not thread_id:
                thread_id = str(uuid.uuid4())
            
            timestamp = datetime.now().isoformat()
            
            cur.execute("""
                INSERT INTO mails (direction, timestamp, sender_email, recipient_email, 
                                 subject, body, status, email_type, thread_id, in_reply_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (direction, timestamp, sender_email, recipient_email, subject, body,
                  status, email_type, thread_id, None))
            
            email_id = cur.lastrowid
            conn.commit()
            conn.close()
            return email_id
        except Exception as e:
            print(f"Error saving email to database: {e}")
            return -1
    
    def process_email_request(self, user_query: str) -> Dict[str, Any]:
        """
        Main method to process an email request from natural language query
        Returns dict with status, message, and details
        """
        try:
            # Step 1: Match email type
            email_type = self.match_email_type(user_query)
            if not email_type:
                return {
                    'success': False,
                    'message': 'Could not identify email type from query',
                    'suggestions': list(self.email_templates.keys())[:10]
                }
            
            # Step 2: Find recipients
            # Extract potential employee names/departments from query
            recipients = []
            query_lower = user_query.lower()
            
            # Check if query mentions "all employees" or department
            if 'all employees' in query_lower or 'everyone' in query_lower:
                recipients = self.employees
            elif any(dept.lower() in query_lower for dept in ['technical', 'actuarial', 'hr', 'executive', 'human resources']):
                # Find by department
                for dept in ['technical', 'actuarial', 'hr', 'executive', 'human resources']:
                    if dept.lower() in query_lower:
                        recipients = [e for e in self.employees if dept.lower() in e.get('department', '').lower()]
                        break
            else:
                # Find by name
                for emp in self.employees:
                    name_parts = emp.get('name', '').lower().split()
                    if any(part in query_lower for part in name_parts if len(part) > 2):
                        recipients.append(emp)
            
            if not recipients:
                # Fallback: Try to find by partial match
                words = user_query.split()
                for word in words:
                    if len(word) > 3:
                        found = self.find_employees(word)
                        if found:
                            recipients.extend(found)
                            break
            
            # Remove duplicates
            seen_emails = set()
            unique_recipients = []
            for rec in recipients:
                email = rec.get('email')
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    unique_recipients.append(rec)
            
            if not unique_recipients:
                return {
                    'success': False,
                    'message': 'Could not find recipient(s) from query',
                    'available_employees': [e.get('name') for e in self.employees[:10]]
                }
            
            # Step 3: Generate and send emails
            results = []
            for recipient in unique_recipients:
                # Generate email content
                email_content = self.generate_email_content(email_type, recipient, user_query)
                
                # Send email (if SendGrid available)
                email_sent = False
                if self.sendgrid_client:
                    email_sent = self.send_email_via_sendgrid(
                        recipient.get('email'),
                        email_content['subject'],
                        email_content['body']
                    )
                
                # Save to database
                email_id = self.save_email_to_db(
                    direction='sent',
                    sender_email=self.email_user,
                    recipient_email=recipient.get('email'),
                    subject=email_content['subject'],
                    body=email_content['body'],
                    email_type=email_type,
                    status='sent' if email_sent else 'queued'
                )
                
                results.append({
                    'recipient': recipient.get('name'),
                    'email': recipient.get('email'),
                    'subject': email_content['subject'],
                    'status': 'sent' if email_sent else 'saved (SendGrid not configured)',
                    'email_id': email_id
                })
            
            return {
                'success': True,
                'message': f'Successfully processed {len(results)} email(s)',
                'email_type': email_type,
                'results': results
            }
            
        except Exception as e:
            print(f"Error processing email request: {e}")
            return {
                'success': False,
                'message': f'Error processing request: {str(e)}'
            }
