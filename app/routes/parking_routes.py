from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.parking_event import ParkingEvent
from app.models.landmark import Landmark
from app.models.score import Score

from app.extensions import db
import datetime

import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app
import time

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

@parking_bp.route('', methods=['GET']) # Corresponds to GET /parking
@jwt_required()
def get_all_parking_events():
    current_user_id = get_jwt_identity()

    # Query the database for all events belonging to the current user
    user_events = ParkingEvent.query.filter_by(user_id=current_user_id).order_by(ParkingEvent.created_at.desc()).all()

    # Serialize the list of event objects into a list of dictionaries
    events_list = []
    for event in user_events:
        events_list.append({
            "parking_events_id": event.parking_events_id,
            "parking_location_name": event.parking_location_name,
            "notes": event.notes,
            "started_at": event.started_at.isoformat(),
            "status": event.status.name
        })

    return jsonify(events_list), 200


@parking_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_single_parking_event(event_id):
    current_user_id = get_jwt_identity()

    # Query for the specific event, ensuring it belongs to the current user
    event = ParkingEvent.query.filter_by(
        parking_events_id=event_id,
        user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"message": "Parking event not found"}), 404

    # --- Generate Pre-signed URL for the photo ---
    photo_url = None
    if event.photo_s3_key:
        s3_client = boto3.client(
           "s3",
           aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
           aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
           region_name=current_app.config['AWS_REGION']
        )
        try:
            photo_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': current_app.config['S3_BUCKET'], 'Key': event.photo_s3_key},
                ExpiresIn=3600  # URL is valid for 1 hour
            )
        except Exception as e:
            # Handle potential S3 errors gracefully
            print(f"Error generating pre-signed URL: {e}")
            photo_url = None

    # --- Serialize related landmarks ---
    landmarks_list = []
    for landmark in event.landmarks:
        landmarks_list.append({
            "landmarks_id": landmark.landmarks_id,
            "location_name": landmark.location_name,
            "is_achieved": landmark.is_achieved
        })

    # --- Serialize related score ---
    score_data = None
    if event.score:
        score_data = {
            "scores_id": event.score.scores_id,
            "task_score": event.score.task_score
        }

    # --- Build the final response object ---
    response_data = {
        "parking_events_id": event.parking_events_id,
        "user_id": event.user_id,
        "parking_latitude": float(event.parking_latitude),
        "parking_longitude": float(event.parking_longitude),
        "parking_location_name": event.parking_location_name,
        "parking_address": event.parking_address,
        "notes": event.notes,
        "parking_type": event.parking_type.name,  # Use .name for enums
        "level_floor": event.level_floor,
        "parking_slot": event.parking_slot,
        "photo_url": photo_url, # This will be the temporary, working URL
        "started_at": event.started_at.isoformat(),
        "ended_at": event.ended_at,
        "status": event.status.name,
        "landmarks": landmarks_list,
        "score": score_data
    }

    return jsonify(response_data), 200

@parking_bp.route('/<int:event_id>', methods=['PUT'])  # Corresponds to PUT /parking/<id>
@jwt_required()
def update_parking_event(event_id):
    current_user_id = get_jwt_identity()

    # Find the specific event and ensure it belongs to the current user
    event = ParkingEvent.query.filter_by(
        parking_events_id=event_id,
        user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"message": "Parking event not found"}), 404

    data = request.get_json()

    # Update fields if they are provided in the request body
    if 'status' in data:
        new_status = data['status']
        event.status = new_status

        # If user starts navigating, set the navigation start time
        if new_status == 'retrieving':
            event.navigation_started_at = datetime.datetime.now(datetime.timezone.utc)
            print(f" retrieving - navigation_started_at: {event.navigation_started_at}")
            if 'estimated_time' in data:
                try:
                    event.estimated_time = int(data['estimated_time'])
                    print(f" retrieving - estimated_time: {event.estimated_time}")
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid format for estimated_time"}), 400

            # -- End Navigation (Retrieved or Expired) --
        elif new_status in ['retrieved', 'expired']:
            # Set end time only if not already set (important for idempotency)
            if not event.ended_at:
                event.ended_at = datetime.datetime.now(datetime.timezone.utc)

            # --- Save Final Metrics ---
            if 'finalScreenTime' in data:
                try:
                    screen_time_ms = int(data['finalScreenTime'])
                    event.finalScreenTime = screen_time_ms // 1000  # Convert ms to seconds
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid format for finalScreenTime"}), 400

            if 'finalMapViewCount' in data:
                try:
                    event.finalMapViewCount = int(data['finalMapViewCount'])
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid format for finalMapViewCount"}), 400

            # ===== HANDLE 'RETRIEVED' STATUS =====
            if new_status == 'retrieved':

                # Calculate Score (Only if no score exists)
                if not event.score:
                    try:
                        # ===== 1. LANDMARK SCORE =====
                        total_landmarks = len(event.landmarks)
                        achieved_landmarks = sum(1 for lm in event.landmarks if lm.is_achieved)
                        has_landmarks = total_landmarks > 0

                        landmark_factor = 0.0
                        if total_landmarks > 0:
                            landmark_factor = (float(achieved_landmarks) / float(total_landmarks)) * 100.0
                        else:
                            landmark_factor = 100.0

                        # ===== 2. TIME SCORE =====
                        actual_duration = None
                        if event.ended_at and event.navigation_started_at:
                            ended_at_aware = event.ended_at
                            if ended_at_aware.tzinfo is None:
                                ended_at_aware = ended_at_aware.replace(tzinfo=datetime.timezone.utc)

                            nav_started_at_aware = event.navigation_started_at
                            if nav_started_at_aware.tzinfo is None:
                                nav_started_at_aware = nav_started_at_aware.replace(tzinfo=datetime.timezone.utc)

                            actual_duration = (ended_at_aware - nav_started_at_aware).total_seconds()

                        estimated_duration = event.estimated_time

                        time_factor = 0.0
                        if actual_duration and estimated_duration and estimated_duration > 0:
                            if actual_duration <= estimated_duration:
                                time_factor = 100.0
                            else:
                                overtime_ratio = (actual_duration - float(estimated_duration)) / float(
                                    estimated_duration)
                                time_factor = max(0.0, 100.0 - (overtime_ratio * 100.0))

                        # ===== 3. PENALTIES =====
                        map_view_count = event.finalMapViewCount or 0

                        # Peek penalty
                        if map_view_count == 0:
                            peek_penalty_points = 0.0
                        elif map_view_count <= 3:
                            peek_penalty_points = float(map_view_count * 1)
                        elif map_view_count <= 7:
                            peek_penalty_points = 3.0 + float((map_view_count - 3) * 1.5)
                        else:
                            peek_penalty_points = min(10.0, 9.0 + float((map_view_count - 7)) * 0.5)

                        # CRITICAL FIX: Cap screen time at actual duration
                        screen_time_raw = float(event.finalScreenTime or 0)
                        screen_time = screen_time_raw
                        assist_percentage = 0.0

                        if actual_duration and actual_duration > 0:
                            # Cap screen time - it cannot exceed navigation time!
                            if screen_time_raw > actual_duration:
                                print(
                                    f"⚠️ WARNING: Screen time {screen_time_raw}s exceeds navigation {actual_duration}s")
                                screen_time = actual_duration
                                print(f"⚠️ Screen time capped to {screen_time}s (100% of navigation)")

                            # Calculate percentage using CAPPED screen time
                            assist_percentage = (screen_time / float(actual_duration)) * 100.0
                            assist_penalty_points = min(15.0, (assist_percentage / 5.0))
                        else:
                            # Fallback if no duration available
                            assist_penalty_points = min(15.0, screen_time / 20.0)
                            if screen_time > 0:
                                assist_percentage = 100.0  # Assume worst case

                        # ===== 4. PATH PERFORMANCE =====
                        path_performance = 100.0 - (peek_penalty_points * 1.0) - (assist_penalty_points * 0.2)
                        path_performance = max(0.0, min(100.0, path_performance))

                        # ===== 5. CALCULATE FINAL SCORE =====
                        if has_landmarks:
                            base_score = (
                                    (landmark_factor * 0.50) +
                                    (time_factor * 0.30) +
                                    (path_performance * 0.20)
                            )
                        else:
                            base_score = (
                                    (time_factor * 0.60) +
                                    (path_performance * 0.40)
                            )

                        # Apply penalties
                        total_penalty = peek_penalty_points
                        final_task_score = max(0.0, base_score - total_penalty)

                        # Enhanced Debug logging
                        print("=== SCORE CALCULATION DEBUG ===")
                        print(f"Has Landmarks: {has_landmarks}")
                        print(f"Achieved Landmarks: {achieved_landmarks}/{total_landmarks}")
                        print(f"Actual Duration: {actual_duration}s vs Estimated: {estimated_duration}s")
                        print(f"---")
                        print(f"Map View Count: {map_view_count}")
                        print(f"Screen Time (raw): {screen_time_raw}s")
                        print(f"Screen Time (used): {screen_time}s")
                        print(f"Screen Time %: {round(assist_percentage, 1)}%")
                        print(f"---")

                        if has_landmarks:
                            print(f"Landmark Factor: {round(landmark_factor, 2)}% (Weight: 50%)")
                            print(f"Time Factor: {round(time_factor, 2)}% (Weight: 30%)")
                            print(f"Path Performance: {round(path_performance, 2)}% (Weight: 20%)")
                            print(
                                f"Base Score: {round(base_score, 2)} = ({round(landmark_factor, 2)} × 0.5) + ({round(time_factor, 2)} × 0.3) + ({round(path_performance, 2)} × 0.2)")
                        else:
                            print(f"Landmark Factor: N/A (No landmarks on this route)")
                            print(f"Time Factor: {round(time_factor, 2)}% (Weight: 60%)")
                            print(f"Path Performance: {round(path_performance, 2)}% (Weight: 40%)")
                            print(
                                f"Base Score: {round(base_score, 2)} = ({round(time_factor, 2)} × 0.6) + ({round(path_performance, 2)} × 0.4)")

                        print(f"---")
                        print(f"Peek Penalty: {round(peek_penalty_points, 2)} pts (max 10)")
                        print(f"Assist Penalty: {round(assist_penalty_points, 2)} pts (max 15)")
                        print(f"Total Penalty: {round(total_penalty, 2)} pts")
                        print(f"---")
                        print(f"FINAL SCORE: {round(final_task_score, 2)}")
                        print("================================")

                        # ===== 6. CREATE SCORE OBJECT =====
                        new_score = Score(
                            parking_events_id=event_id,
                            time_factor=round(time_factor, 2),
                            landmark_factor=round(landmark_factor, 2),
                            landmarks_recalled=achieved_landmarks,
                            no_of_landmarks=total_landmarks,
                            path_performance=round(path_performance, 2),
                            peek_penalty=int(map_view_count),
                            assist_penalty=int(screen_time),  # Use CAPPED value
                            task_score=round(final_task_score, 2),
                            assistance_points=int(event.finalMapViewCount or 0),
                        )
                        db.session.add(new_score)

                        # ✅ Score calculated successfully
                        event.status = 'active'
                        print("✅ Score calculated successfully. Status set to 'active'.")

                    except Exception as e:
                        print(f"❌ Error calculating score: {str(e)}")
                        # Don't set status to 'active' if calculation failed
                        return jsonify({"message": f"Error calculating score: {str(e)}"}), 500

                else:
                    # Score already exists - user wants to view it again
                    # event.status = 'active'
                    print("ℹ️ Score already exists.")

            # ===== HANDLE 'EXPIRED' STATUS =====
            elif new_status == 'expired':
                event.status = 'expired'
                print("⏰ Navigation expired. Status set to 'expired'.")

    if 'notes' in data:
        event.notes = data['notes']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error during commit: {e}")
        return jsonify({"message": "Database error occurred"}), 500

    return jsonify({"message": f"Event {event_id} updated successfully"}), 200

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
            landmark_longitude=landmark_data.get('landmark_longitude'),
            distance_from_parking=landmark_data.get('distance_from_parking')
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


@parking_bp.route('/<int:event_id>/photo', methods=['POST'])
@jwt_required()
def upload_photo_to_event(event_id):
    current_user_id = get_jwt_identity()

    if 'photo' not in request.files:
        return jsonify({"message": "No photo file found in the request"}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    event = ParkingEvent.query.filter_by(parking_events_id=event_id, user_id=current_user_id).first()
    if not event:
        return jsonify({"message": "Parking event not found"}), 404

    s3_key = f"user_{current_user_id}/parking_{int(time.time())}_{file.filename}"

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

    try:
        s3_client.upload_fileobj(
            file,
            current_app.config['S3_BUCKET'],
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

    # --- CHANGES START HERE ---

    # We no longer save a static photo_url. We only need the key.
    event.photo_s3_key = s3_key
    db.session.commit()

    return jsonify({
        "message": "Photo uploaded successfully",
        "s3_key": s3_key # Return the key instead of the URL
    }), 200

@parking_bp.route('/latest-active', methods=['GET'])
@jwt_required()
def get_latest_active_parking_event():
    current_user_id = get_jwt_identity()

    event = ParkingEvent.query.filter_by(
        user_id=current_user_id
    ).order_by(ParkingEvent.started_at.desc()).first()

    if not event or event.status.name not in ['active', 'retrieving']:
        return jsonify({}), 200

    # --- S3 Client Setup (to be used for all pre-signed URLs) ---
    s3_client = boto3.client(
       "s3",
       aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
       aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
       region_name=current_app.config['AWS_REGION']
    )

    # --- Generate Pre-signed URL for the main parking event photo ---
    main_photo_url = None
    if event.photo_s3_key:
        try:
            main_photo_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': current_app.config['S3_BUCKET'], 'Key': event.photo_s3_key},
                ExpiresIn=3600
            )
        except Exception as e:
            print(f"Error generating pre-signed URL for event: {e}")

    # --- Fully Serialize related landmarks ---
    landmarks_list = []
    for landmark in event.landmarks:
        landmark_photo_url = None
        if landmark.photo_s3_key:
            try:
                landmark_photo_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': current_app.config['S3_BUCKET'], 'Key': landmark.photo_s3_key},
                    ExpiresIn=3600
                )
            except Exception as e:
                print(f"Error generating pre-signed URL for landmark: {e}")

        landmarks_list.append({
            "landmarks_id": landmark.landmarks_id,
            "parking_events_id": landmark.parking_events_id,
            "landmark_latitude": float(landmark.landmark_latitude) if landmark.landmark_latitude else None,
            "landmark_longitude": float(landmark.landmark_longitude) if landmark.landmark_longitude else None,
            "location_name": landmark.location_name,
            "distance_from_parking": landmark.distance_from_parking,
            "photo_url": landmark_photo_url,
            "is_achieved": landmark.is_achieved,
            "created_at": landmark.created_at.isoformat()
        })

    # --- Fully Serialize related score ---
    score_data = None
    if event.score:
        score = event.score
        score_data = {
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
        }

    # --- Build the final response object ---
    response_data = {
        "parking_events_id": event.parking_events_id,
        "user_id": event.user_id,
        "parking_latitude": float(event.parking_latitude),
        "parking_longitude": float(event.parking_longitude),
        "parking_location_name": event.parking_location_name,
        "parking_type": event.parking_type.name,  # Use .name for enums
        "level_floor": event.level_floor,
        "notes": event.notes,
        "photo_url": main_photo_url,
        "started_at": event.started_at.isoformat(),
        "status": event.status.name,
        "landmarks": landmarks_list,
        "score": score_data
    }

    return jsonify(response_data), 200


@parking_bp.route('/<int:event_id>/landmarks/<int:landmark_id>', methods=['PATCH'])
@jwt_required()
def update_landmark(event_id, landmark_id):
    current_user_id = get_jwt_identity()

    # First, verify the user owns the parent parking event
    event = ParkingEvent.query.filter_by(
        parking_events_id=event_id,
        user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"message": "Parking event not found"}), 404

    # Now, find the specific landmark
    landmark = Landmark.query.get(landmark_id)

    # Check that the landmark exists AND belongs to the correct event
    if not landmark or landmark.parking_events_id != event.parking_events_id:
        return jsonify({"message": "Landmark not found for this event"}), 404

    data = request.get_json()

    # Check for the 'is_achieved' key in the request body
    if 'is_achieved' in data:
        is_achieved_value = data.get('is_achieved')

        # Ensure the value is a boolean
        if isinstance(is_achieved_value, bool):
            landmark.is_achieved = is_achieved_value
        else:
            return jsonify({"message": "Invalid data type for 'is_achieved', boolean expected"}), 400

    # You could add other fields to update here as well
    # if 'location_name' in data:
    #     landmark.location_name = data.get('location_name')

    db.session.commit()

    # Return the updated landmark
    return jsonify({
        "message": "Landmark updated successfully",
        "landmarks_id": landmark.landmarks_id,
        "is_achieved": landmark.is_achieved
    }), 200