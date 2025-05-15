from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from app.config import Config
from flask_cors import CORS



# Import Swagger UI blueprint
from app.swagger import swagger_ui_blueprint

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()

def create_app():


    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    
    # Register Swagger UI blueprint
    app.register_blueprint(swagger_ui_blueprint, url_prefix='/api/docs')

    # Register Blueprints for API routes
    from app.routes import observation_blueprint  # Ensure this file exists with appropriate routes
    app.register_blueprint(observation_blueprint, url_prefix='/api/v1/observations')

    return app
