"""
Email routes - Email Agent integration
"""
from flask import Blueprint, request, render_template, jsonify, session, redirect, url_for, flash
from orchestrator.orchestrator import get_orchestrator

email_bp = Blueprint('email', __name__, url_prefix='/email')


def require_hr_login():
    """Check if user is logged in as HR"""
    if 'user_id' not in session:
        return None
    if session.get('role') != 'hr':
        return None
    return True


@email_bp.route('/dashboard')
def dashboard():
    """Email dashboard - main interface"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))

    return render_template('email_dashboard.html', username=session.get('username'))


@email_bp.route('/inbox')
def inbox():
    """View inbox threads"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))

    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr', agent_name='email_agent')

        if not route_result.get('agent'):
            flash('Email agent not available', 'error')
            return redirect(url_for('email.dashboard'))

        email_agent = route_result['agent']
        threads = email_agent.get_inbox_threads(limit=100)

        return render_template('email_inbox.html', threads=threads, username=session.get('username'))
    except Exception as e:
        flash(f'Error loading inbox: {str(e)}', 'error')
        return redirect(url_for('email.dashboard'))


@email_bp.route('/thread/<thread_id>')
def thread_view(thread_id):
    """View a specific email thread"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))

    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr', agent_name='email_agent')

        if not route_result.get('agent'):
            flash('Email agent not available', 'error')
            return redirect(url_for('email.inbox'))

        email_agent = route_result['agent']
        messages = email_agent.get_thread_messages(thread_id)

        if not messages:
            flash('Thread not found', 'error')
            return redirect(url_for('email.inbox'))

        subject = messages[0].get('subject', '(No Subject)')

        return render_template('email_thread.html',
                             messages=messages,
                             subject=subject,
                             thread_id=thread_id,
                             username=session.get('username'))
    except Exception as e:
        flash(f'Error loading thread: {str(e)}', 'error')
        return redirect(url_for('email.inbox'))


@email_bp.route('/sent')
def sent():
    """View sent emails"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))

    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr', agent_name='email_agent')

        if not route_result.get('agent'):
            flash('Email agent not available', 'error')
            return redirect(url_for('email.dashboard'))

        email_agent = route_result['agent']
        emails = email_agent.get_sent_emails(limit=100)

        return render_template('email_sent.html', emails=emails, username=session.get('username'))
    except Exception as e:
        flash(f'Error loading sent emails: {str(e)}', 'error')
        return redirect(url_for('email.dashboard'))


@email_bp.route('/stats', methods=['GET'])
def stats():
    """Get email statistics"""
    if not require_hr_login():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr', agent_name='email_agent')

        if not route_result.get('agent'):
            return jsonify({'error': 'Email agent not available'}), 500

        email_agent = route_result['agent']
        stats = email_agent.get_email_stats()

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_bp.route('/compose')
def compose():
    """Compose new email"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))

    return render_template('email_compose.html', username=session.get('username'))


@email_bp.route('/send', methods=['POST'])
def send_email():
    """Process and send email from compose form"""
    if not require_hr_login():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'success': False, 'message': 'Query is required'}), 400
        
        # Get email agent from orchestrator
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr', agent_name='email_agent')
        
        if not route_result.get('agent'):
            return jsonify({'success': False, 'message': 'Email agent not available'}), 500
        
        email_agent = route_result['agent']
        
        # Process the email request
        result = email_agent.process_email_request(query)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in send_email route: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500