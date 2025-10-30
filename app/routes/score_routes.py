from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.score import Score
from app.models.parking_event import ParkingEvent
from app.extensions import db

score_bp = Blueprint('score_bp', __name__, url_prefix='/scores')

@score_bp.route('', methods=['GET']) # Corresponds to GET /scores
@jwt_required()
def get_watched_scores():
    current_user_id = get_jwt_identity()

    # Query scores, joining with ParkingEvent to filter by user and status
    watched_scores = db.session.query(Score, ParkingEvent).join(
        ParkingEvent, Score.parking_events_id == ParkingEvent.parking_events_id
    ).filter(
        ParkingEvent.user_id == current_user_id,
        ParkingEvent.status == 'score_watched'  # Filter by the specific status
    ).order_by(Score.created_at.desc()).all()

    # Serialize the results
    scores_list = []
    for score, event in watched_scores:
        scores_list.append({
            "parking_events_id": score.parking_events_id,
            "scores_id": score.scores_id,

            # Performance factors
            "time_factor": score.time_factor,
            "landmark_factor": score.landmark_factor,
            "path_performance": score.path_performance,

            # Landmark details
            "landmarks_recalled": score.landmarks_recalled,
            "no_of_landmarks": score.no_of_landmarks,

            # Penalties (NEW FIELDS)
            "peek_penalty": score.peek_penalty or 0,
            "assist_penalty": score.assist_penalty or 0,

            # Score
            "task_score": score.task_score,

            # Dates
            "calculated_at": score.created_at.isoformat() if score.created_at else None,
            "created_at": score.created_at.isoformat() if score.created_at else None,
            "started_at": event.started_at.isoformat() if event.started_at else None,
            "ended_at": event.ended_at.isoformat() if event.ended_at else None,

            # Location info from ParkingEvent
            "parking_location_name": event.parking_location_name,
            "parking_address": event.parking_address,

            # Deprecated (keep for backward compatibility)
            "assistance_points": score.assistance_points or 0,
        })

    return jsonify(scores_list), 200