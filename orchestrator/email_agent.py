"""
Email Agent Wrapper - Integrates the Email Agent system
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config


class EmailAgentWrapper:
    """
    Wrapper for the Email Agent system to integrate with orchestrator
    """

    def __init__(self):
        """Initialize the Email Agent"""
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'mailbox.db')
        self.db_path = os.path.abspath(self.db_path)
        self._ensure_db()
        print("Email Agent Wrapper initialized")

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
