"""
HR routes - HR dashboard and Hiring Agent integration
"""
from flask import Blueprint, request, render_template, jsonify, session, redirect, url_for, flash
from orchestrator.orchestrator import get_orchestrator
import os
from werkzeug.utils import secure_filename

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

# Allowed file extensions for CV uploads
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'cvs')


def require_hr_login():
    """Check if user is logged in as HR"""
    if 'user_id' not in session:
        return None
    if session.get('role') != 'hr':
        return None
    return True


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@hr_bp.route('/dashboard')
def dashboard():
    """HR dashboard"""
    if not require_hr_login():
        flash('Please login as HR to access this page', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('hr_dashboard.html', username=session.get('username'))


@hr_bp.route('/process_hiring', methods=['POST'])
def process_hiring():
    """Process job hiring with candidate evaluation"""
    if not require_hr_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    job_description = data.get('job_description', '').strip()
    initial_retrieval = data.get('initial_retrieval', 30)
    final_candidates = data.get('final_candidates', 5)
    
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400
    
    try:
        # Get orchestrator and route to Hiring Agent
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr')
        
        if not route_result.get('agent'):
            return jsonify({
                'error': route_result.get('error', 'Hiring agent not available')
            }), 500
        
        # Process hiring
        hiring_agent = route_result['agent']
        candidates = hiring_agent.process_job_hiring(
            job_description=job_description,
            initial_retrieval=initial_retrieval,
            final_candidates=final_candidates
        )
        
        return jsonify({
            'candidates': candidates,
            'total_candidates': len(candidates),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'Error processing hiring: {str(e)}'}), 500


@hr_bp.route('/upload_cv', methods=['POST'])
def upload_cv():
    """Upload CV to database"""
    if not require_hr_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT'}), 400
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get orchestrator and route to Hiring Agent
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr')
        
        if not route_result.get('agent'):
            return jsonify({'error': 'Hiring agent not available'}), 500
        
        # Add CV to database
        hiring_agent = route_result['agent']
        result = hiring_agent.add_cv(file_path)
        
        if result.get('success'):
            return jsonify({
                'message': 'CV uploaded successfully',
                'filename': filename,
                'status': 'success'
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to add CV')}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error uploading CV: {str(e)}'}), 500


@hr_bp.route('/cv_stats', methods=['GET'])
def cv_stats():
    """Get CV database statistics"""
    if not require_hr_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr')
        
        if not route_result.get('agent'):
            return jsonify({'error': 'Hiring agent not available'}), 500
        
        hiring_agent = route_result['agent']
        stats = hiring_agent.get_cv_stats()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/search_cvs', methods=['POST'])
def search_cvs():
    """Search CVs matching job description"""
    if not require_hr_login():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    job_description = data.get('job_description', '').strip()
    limit = data.get('limit', 10)
    
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400
    
    try:
        orchestrator = get_orchestrator()
        route_result = orchestrator.route_request(user_role='hr')
        
        if not route_result.get('agent'):
            return jsonify({'error': 'Hiring agent not available'}), 500
        
        hiring_agent = route_result['agent']
        results = hiring_agent.search_cvs(job_description, limit=limit)
        
        return jsonify({
            'results': results,
            'total_results': len(results),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

