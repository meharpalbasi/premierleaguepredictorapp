import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # Import Flask-Migrate
import logging

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Instantiate Migrate

def create_app():
    print("Starting create_app")
    
    app = Flask(__name__)  # No need to specify template_folder now

    print(f"Created Flask app with name: {app.name}")
    print(f"App root path: {app.root_path}")
    print(f"App template folder: {app.template_folder}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Contents of app folder: {os.listdir(app.root_path)}")
    
    # Check if the templates folder exists correctly
    templates_path = os.path.join(app.root_path, 'templates')
    if os.path.exists(templates_path):
        print(f"Contents of template folder: {os.listdir(templates_path)}")
    else:
        print("Templates folder not found!")

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, '..', 'instance')
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'premier_league_predictor.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the app and database

    # Import models here to ensure they're known to Flask-Migrate
    from .models import User, Question, Prediction, Match

    from .routes import main as main_blueprint
    from .routes import auth as auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/premier_league_predictor.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Premier League Predictor startup')

    return app

# Import models at the bottom to avoid circular imports
from .models import User, Question, Prediction, Match
