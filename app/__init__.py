from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create upload folder if it doesn't exist
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'receipts'), exist_ok=True)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'receipts')

    # Initialize Flask extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        # Import models to ensure they're known to Flask-Migrate
        from app import models

        # Import and register blueprints
        from app.routes.auth import bp as auth_bp
        from app.routes.main import main as main_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)

        # Create database tables if they don't exist
        db.create_all()

    return app 