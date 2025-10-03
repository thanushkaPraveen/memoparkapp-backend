from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.parking_event import ParkingEvent
from app.models.landmark import Landmark
from app.models.score import Score

from app.extensions import db
import datetime

# Create a Blueprint for parking routes
parking_bp = Blueprint('parking_bp', __name__, url_prefix='/parking')

# add parking
@parking_bp.route('', methods=['POST'])  # Corresponds to POST /parking
@jwt_required()
def create_parking_event():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    latitude = data.get('parking_latitude')
    longitude = data.get('parking_longitude')

    if not latitude or not longitude:
        return jsonify({"message": "Latitude and longitude are required"}), 400

    # Create a new ParkingEvent object with all provided fields
    new_event = ParkingEvent(
        user_id=current_user_id,
        parking_latitude=latitude,
        parking_longitude=longitude,
        parking_location_name=data.get('parking_location_name'),
        parking_address=data.get('parking_address'),
        notes=data.get('notes'),
        parking_type=data.get('parking_type', 'outside'), # Defaults to 'outside' if not provided
        level_floor=data.get('level_floor'),
        parking_slot=data.get('parking_slot'),
        photo_url=data.get('photo_url'),
        photo_s3_key=data.get('photo_s3_key'),
        started_at=datetime.datetime.now(datetime.timezone.utc)  # Record the start time
    )

    db.session.add(new_event)
    db.session.commit()

    # Manually create a dictionary from the new_event object for the JSON response
    response_data = {
        "parking_events_id": new_event.parking_events_id,
        "user_id": new_event.user_id,
        "parking_latitude": float(new_event.parking_latitude),
        "parking_longitude": float(new_event.parking_longitude),
        "parking_location_name": new_event.parking_location_name,
        "parking_address": new_event.parking_address,
        "notes": new_event.notes,
        "parking_type": new_event.parking_type.name,  # Use .name for enums
        "level_floor": new_event.level_floor,
        "parking_slot": new_event.parking_slot,
        "photo_url": new_event.photo_url,
        "photo_s3_key": new_event.photo_s3_key,
        "started_at": new_event.started_at.isoformat(),
        "ended_at": new_event.ended_at,
        "status": new_event.status.name  # Use .name for enums
    }

    return jsonify(response_data), 201

# add landmarks
@parking_bp.route('/<int:event_id>/landmarks', methods=['POST'])
@jwt_required()
def add_landmarks_to_event(event_id):
    current_user_id = get_jwt_identity()

    # First, find the parking event and make sure it belongs to the current user
    parking_event = ParkingEvent.query.filter_by(
        parking_events_id=event_id,
        user_id=current_user_id
    ).first()

    # If the event doesn't exist or doesn't belong to the user, return a 404
    if not parking_event:
        return jsonify({"message": "Parking event not found"}), 404

    data = request.get_json()
    landmarks_data = data.get('landmarks')

    # Check if landmarks_data is a list
    if not isinstance(landmarks_data, list):
        return jsonify({"message": "Request body must contain a 'landmarks' array"}), 400

    new_landmarks = []
    for landmark_data in landmarks_data:
        new_landmark = Landmark(
            parking_events_id=event_id,  # Link to the specific parking event
            location_name=landmark_data.get('location_name'),
            landmark_latitude=landmark_data.get('landmark_latitude'),
            landmark_longitude=landmark_data.get('landmark_longitude')
            # Add any other landmark fields here
        )
        db.session.add(new_landmark)
        new_landmarks.append(new_landmark)

    # Commit all new landmarks to the database in one transaction
    db.session.commit()

    return jsonify({
        "message": f"{len(new_landmarks)} landmarks added successfully to event {event_id}"
    }), 201


@parking_bp.route('/<int:event_id>/score', methods=['POST'])
@jwt_required()
def add_score_to_event(event_id):
    current_user_id = get_jwt_identity()

    # Find the parking event and verify it belongs to the current user
    parking_event = ParkingEvent.query.filter_by(
        parking_events_id=event_id,
        user_id=current_user_id
    ).first()

    if not parking_event:
        return jsonify({"message": "Parking event not found"}), 404

    # Check if a score already exists for this event (one-to-one relationship)
    if parking_event.score:
        return jsonify({"message": "A score for this event already exists"}), 409

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required"}), 400

    # Create the new Score object
    new_score = Score(
        parking_events_id=event_id,
        time_factor=data.get('time_factor'),
        landmark_factor=data.get('landmark_factor'),
        path_performance=data.get('path_performance'),
        assistance_points=data.get('assistance_points'),
        no_of_landmarks=data.get('no_of_landmarks'),
        landmarks_recalled=data.get('landmarks_recalled'),
        task_score=data.get('task_score')
    )

    db.session.add(new_score)
    db.session.commit()

    # Create a dictionary for the response
    response_data = {
        "scores_id": new_score.scores_id,
        "parking_events_id": new_score.parking_events_id,
        "task_score": new_score.task_score
    }

    return jsonify(response_data), 201