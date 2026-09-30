import os
from flask import Flask, redirect, url_for, send_from_directory, render_template
from flask_login import LoginManager, current_user
from backend.config import Config
from backend.database import get_db, create_all_tables
from backend.db_models import User
from backend.ml_service import MLService

# Initialize Blueprints
from backend.routes.auth import auth_bp
from backend.routes.farmer import farmer_bp
from backend.routes.vet import vet_bp
from backend.routes.admin import admin_bp
from backend.routes.library import library_bp
from backend.routes.api import api_bp

def create_app():
    # Configure template and static directories pointing strictly inside the frontend folder
    app = Flask(
        __name__,
        template_folder=Config.TEMPLATE_FOLDER,
        static_folder=Config.STATIC_FOLDER,
        static_url_path='/static'
    )
    app.config.from_object(Config)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Database & ML models
    with app.app_context():
        create_all_tables()
        MLService.load_models()

    # Flask-Login Configuration
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db()
        return db.query(User).get(int(user_id))

    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db = get_db()
        if db:
            db.remove()

    # Serve uploaded images securely
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Root route redirection based on role
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'farmer':
                return redirect(url_for('farmer.dashboard'))
            elif current_user.role == 'vet':
                return redirect(url_for('vet.dashboard'))
            elif current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(vet_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(api_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_title="404 - Page Not Found", error_msg="The requested page could not be located."), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('base.html', error_title="403 - Forbidden", error_msg="You do not have administrative clearance for this action."), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error_title="500 - Server Error", error_msg="An unexpected error occurred. Please try again."), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
