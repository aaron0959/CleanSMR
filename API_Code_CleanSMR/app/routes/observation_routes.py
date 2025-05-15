from flask import Blueprint, request, jsonify
from app.models import Observation
from app.schemas import ObservationSchema
from app import db
import datetime

observation_routes = Blueprint('observation_routes', __name__)

observation_schema = ObservationSchema()
observations_schema = ObservationSchema(many=True)

@observation_routes.route('/', methods=['GET'])
def get_all_observations():
    observations = Observation.query.all()
    return observations_schema.jsonify(observations), 200

@observation_routes.route('/<int:observation_id>', methods=['GET'])
def get_observation(observation_id):
    observation = Observation.query.get(observation_id)
    if not observation:
        return jsonify({"error": "Observation not found"}), 404
    return observation_schema.jsonify(observation), 200

@observation_routes.route('/', methods=['POST'])
def add_observation():
    json_data = request.get_json()
    try:
        new_observation = Observation(
            date=datetime.datetime.strptime(json_data['date'], '%Y-%m-%d').date(),
            time=datetime.datetime.strptime(json_data['time'], '%H:%M:%S').time(),
            timezone_offset=json_data.get('timezone_offset'),
            coordinates=json_data.get('coordinates'),
            water_temp=json_data.get('water_temp'),
            air_temp=json_data.get('air_temp'),
            humidity=json_data.get('humidity'),
            wind_speed=json_data.get('wind_speed'),
            wind_direction=json_data.get('wind_direction'),
            precipitation=json_data.get('precipitation'),
            haze=json_data.get('haze'),
            becquerel=json_data.get('becquerel'),
        )
        db.session.add(new_observation)
        db.session.commit()
        return observation_schema.jsonify(new_observation), 201
    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

@observation_routes.route('/<int:observation_id>', methods=['PUT'])
def update_observation(observation_id):
    observation = Observation.query.get(observation_id)
    if not observation:
        return jsonify({"error": "Observation not found"}), 404
    
    json_data = request.get_json()
    try:
        observation.date = datetime.datetime.strptime(json_data['date'], '%Y-%m-%d').date()
        observation.time = datetime.datetime.strptime(json_data['time'], '%H:%M:%S').time()
        observation.timezone_offset = json_data.get('timezone_offset', observation.timezone_offset)
        observation.coordinates = json_data.get('coordinates', observation.coordinates)
        observation.water_temp = json_data.get('water_temp', observation.water_temp)
        observation.air_temp = json_data.get('air_temp', observation.air_temp)
        observation.humidity = json_data.get('humidity', observation.humidity)
        observation.wind_speed = json_data.get('wind_speed', observation.wind_speed)
        observation.wind_direction = json_data.get('wind_direction', observation.wind_direction)
        observation.precipitation = json_data.get('precipitation', observation.precipitation)
        observation.haze = json_data.get('haze', observation.haze)
        observation.becquerel = json_data.get('becquerel', observation.becquerel)
        
        db.session.commit()
        return observation_schema.jsonify(observation), 200
    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

@observation_routes.route('/<int:observation_id>', methods=['DELETE'])
def delete_observation(observation_id):
    observation = Observation.query.get(observation_id)
    if not observation:
        return jsonify({"error": "Observation not found"}), 404
    db.session.delete(observation)
    db.session.commit()
    return jsonify({"message": f"Observation {observation_id} deleted"}), 200
