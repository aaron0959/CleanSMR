from flask import Blueprint
from app.routes.observation_routes import observation_routes

observation_blueprint = Blueprint('observations', __name__)
observation_blueprint.register_blueprint(observation_routes)
