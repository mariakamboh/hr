"""
Main Flask application entry point
"""
from flask import Flask
from config import Config
from database import db

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.employee_routes import employee_bp
    from routes.hr_routes import hr_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(hr_bp)
    
    # Root route - redirect to login
    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        if 'user_id' in session:
            role = session.get('role')
            if role == 'employee':
                return redirect(url_for('employee.dashboard'))
            elif role == 'hr':
                return redirect(url_for('hr.dashboard'))
        return redirect(url_for('auth.login'))
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

