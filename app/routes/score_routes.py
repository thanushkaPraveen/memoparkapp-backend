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
    watched_scores = db.session.query(Score).join(
        ParkingEvent, Score.parking_events_id == ParkingEvent.parking_events_id
    ).filter(
        ParkingEvent.user_id == current_user_id,
        ParkingEvent.status == 'score_watched' # Filter by the specific status
    ).order_by(Score.created_at.desc()).all()

    # Serialize the results
    scores_list = []
    for score in watched_scores:
        scores_list.append({
            "scores_id": score.scores_id,
            "parking_events_id": score.parking_events_id,
            "time_factor": score.time_factor,
            "landmark_factor": score.landmark_factor,
            "path_performance": score.path_performance,
            "assistance_points": score.assistance_points,
            "no_of_landmarks": score.no_of_landmarks,
            "landmarks_recalled": score.landmarks_recalled,
            "task_score": score.task_score,
            "created_at": score.created_at.isoformat()
        })

    return jsonify(scores_list), 200