# Email Agent - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Start the Application
```bash
cd /tmp/cc-agent/59755413/project
python app.py
```

### Step 2: Login as HR
- Open browser: `http://localhost:5000`
- Login with HR credentials
- You'll see the HR Dashboard

### Step 3: Access Email System
- Click the **"Email Management System"** button
- Or navigate to: `http://localhost:5000/email/dashboard`

---

## 📧 What You Can Do Right Now

### ✅ Working Features (No Setup Required):
1. **View Email Dashboard** - See statistics and overview
2. **Browse Inbox** - View email threads (if any exist in database)
3. **Read Threads** - Open and read email conversations
4. **View Sent Emails** - See history of sent messages
5. **Explore Compose UI** - See the email composition interface

### ⚠️ Requires Configuration:
- **Actual Email Sending** - Needs SendGrid API key and backend controller

---

## 🎨 UI Overview

### Email Dashboard
```
┌─────────────────────────────────────────┐
│  📊 Statistics (4 cards)                │
│  ├─ Total Emails                        │
│  ├─ Sent Emails                         │
│  ├─ Received Emails                     │
│  └─ Total Threads                       │
├─────────────────────────────────────────┤
│  🎯 Quick Actions                       │
│  ├─ Compose New Email                   │
│  ├─ View Inbox                          │
│  ├─ Sent Emails                         │
│  └─ Back to HR Dashboard                │
├─────────────────────────────────────────┤
│  📋 Available Templates (24 types)      │
└─────────────────────────────────────────┘
```

### Navigation Flow
```
HR Dashboard
    ↓
Email Dashboard
    ↓
├→ Compose → [AI Email Generator]
├→ Inbox → Thread View → Message Details
└→ Sent → Email Details Modal
```

---

## 📝 Available Email Templates

### Quick Reference:
1. Offer Letter
2. Appointment Letter
3. Joining Reminder
4. Onboarding Schedule
5. Probation Completion
6. Promotion
7. Salary Increment
8. Leave Approval/Rejection
9. Attendance Warning
10. Performance Warning
11. Appreciation
12. Project Assignment
13. Training Invitation
14. Meeting Invite
15. Task Reminder
16. Birthday/Anniversary
17. Farewell
18. Resignation Acceptance
19. Termination
20. Holiday/Policy Announcements

---

## 🎯 Using the Compose Interface

### Example Queries:
```
"Send offer letter to Sarah Khan for Senior Developer position, joining March 15, 2024"

"Send birthday wishes to all employees with birthday today"

"Send promotion email to Ali Zaidi, new position: Team Lead"

"Send meeting invite to Technical department for project review on Friday 2 PM"
```

### Template Quick-Insert:
1. Select template from dropdown
2. Text auto-fills in textarea
3. Customize with specific details
4. Click "Generate and Send"

---

## 📂 File Locations

### Templates (Jinja2):
```
/templates
├── email_dashboard.html    ← Main dashboard
├── email_inbox.html        ← Thread list
├── email_thread.html       ← Conversation view
├── email_sent.html         ← Sent emails
└── email_compose.html      ← Compose interface
```

### Backend:
```
/orchestrator
└── email_agent.py          ← Email agent wrapper

/routes
└── email_routes.py         ← Flask routes

/static/css
└── style.css               ← Includes email styles
```

### Data:
```
/
├── mailbox.db              ← Email database (auto-created)
├── employees.json          ← Employee database
└── email_templates_agentic.csv ← Email templates
```

---

## 🔧 Configuration (Optional)

### To Enable Email Sending:

**1. Install Dependencies:**
```bash
pip install sendgrid openai python-dotenv beautifulsoup4 langchain-core
```

**2. Set Environment Variables:**
Create `.env` file:
```
SENDGRID_API_KEY=your_sendgrid_key
OPENROUTER_API_KEY=your_openrouter_key
EMAIL_USER=noreply@yourcompany.com
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_PASSWORD=your_app_password
```

**3. Integrate Backend Controller:**
See `EMAIL_AGENT_INTEGRATION.md` for detailed instructions.

---

## 🐛 Troubleshooting

### Database Not Found?
- Database creates automatically on first run
- Check file: `mailbox.db` in project root

### No Emails Showing?
- Database starts empty
- Use compose feature to send test emails
- Or manually insert test data

### Styles Not Loading?
- Clear browser cache
- Check `/static/css/style.css` exists
- Verify CDN links (Bootstrap 5, Bootstrap Icons)

### 404 Errors?
- Ensure `email_routes.py` is registered in `app.py`
- Check blueprint prefix: `/email/`

---

## 📊 Testing the UI

### Without Email Sending:
1. Navigate to Email Dashboard
2. Explore UI components
3. Check statistics display
4. Try compose interface (won't actually send)

### With Database:
```python
# Create test email in database
import sqlite3
conn = sqlite3.connect('mailbox.db')
cur = conn.cursor()
cur.execute("""
    INSERT INTO mails (direction, timestamp, sender_email, recipient_email,
                       subject, body, status, thread_id)
    VALUES ('sent', datetime('now'), 'hr@company.com', 'employee@company.com',
            'Test Email', '<p>This is a test</p>', 'sent', 'test-thread-123')
""")
conn.commit()
conn.close()
```

Then refresh inbox to see test email.

---

## 🎓 Learning Path

### For UI Customization:
1. Study `templates/email_*.html` files
2. Modify `static/css/style.css` for styling
3. Bootstrap 5 docs: https://getbootstrap.com

### For Backend Integration:
1. Review `orchestrator/email_agent.py`
2. Study `routes/email_routes.py`
3. See `email_agent_final2.py` for full controller

---

## 📖 Documentation Files

- **`QUICK_START.md`** ← You are here (Getting started)
- **`EMAIL_AGENT_INTEGRATION.md`** ← Detailed technical guide
- **`IMPLEMENTATION_SUMMARY.md`** ← Complete implementation overview

---

## ✨ Key Features

### Professional UI:
- ✅ Clean, modern design
- ✅ Bootstrap 5 styling
- ✅ Responsive layout
- ✅ Intuitive navigation

### Smart Organization:
- ✅ Thread-based inbox
- ✅ Color-coded messages
- ✅ Status badges
- ✅ Statistics dashboard

### User-Friendly:
- ✅ Quick action buttons
- ✅ Template dropdowns
- ✅ Example queries
- ✅ Empty states

---

## 🎉 You're Ready!

The Email Agent UI is fully integrated and ready to use. Start by exploring the dashboard and testing the interface.

**Need Help?**
- Check `EMAIL_AGENT_INTEGRATION.md` for details
- Review `IMPLEMENTATION_SUMMARY.md` for architecture
- All templates are well-commented

**Happy Emailing! 📧**
