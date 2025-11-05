"""
Employee routes - Employee dashboard and RAG queries
"""
from flask import Blueprint, request, render_template, jsonify, session, redirect, url_for, flash
from orchestrator.orchestrator import get_orchestrator

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def require_employee_login():
    """Check if user is logged in as employee"""
    if 'user_id' not in session:
        return None
    if session.get('role') != 'employee':
        return None
    return True


@employee_bp.route('/dashboard')
def dashboard():
    """Employee dashboard"""
    if not require_employee_login():
        flash('Please login as employee to access this page', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('employee_dashboard.html', username=session.get('username'))


@employee_bp.route('/query', methods=['POST'])
def query():
    """Handle RAG query from employee"""
    if not require_employee_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Get orchestrator and route to RAG agent
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='employee')
        
        if not route_result.get('agent'):
            return jsonify({
                'error': route_result.get('error', 'RAG agent not available')
            }), 500
        
        # Query the RAG agent
        rag_agent = route_result['agent']
        answer = rag_agent.query(question)
        
        return jsonify({
            'question': question,
            'answer': answer,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500


@employee_bp.route('/stats', methods=['GET'])
def stats():
    """Get RAG system statistics"""
    if not require_employee_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='employee')
        
        if not route_result.get('agent'):
            return jsonify({'error': 'RAG agent not available'}), 500
        
        rag_agent = route_result['agent']
        stats = rag_agent.get_stats()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

