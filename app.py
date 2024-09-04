from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///premier_league_predictor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Import and register blueprints here
    # from .routes import main_bp
    # app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return "404 - Page Not Found", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "500 - Internal Server Error", 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)