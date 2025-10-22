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
            if 'estimated_time' in data:
                try:
                    event.estimated_time = int(data['estimated_time'])
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
                    event.finalScreenTime = int(data['finalScreenTime'])
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid format for finalScreenTime"}), 400
            if 'finalMapViewCount' in data:
                try:
                    event.finalMapViewCount = int(data['finalMapViewCount'])
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid format for finalMapViewCount"}), 400

            # --- Calculate and Save Score (Only if Retrieved and no score exists) ---
            if new_status == 'retrieved' and not event.score:

                # 1. Get Landmark Counts
                total_landmarks = len(event.landmarks)
                achieved_landmarks = sum(1 for lm in event.landmarks if lm.is_achieved)

                # 2. Get Time Data (Handle potential None values)
                actual_duration_seconds = None
                if event.ended_at and event.navigation_started_at:

                    # Make ended_at timezone-aware (assume UTC if naive)
                    ended_at_aware = event.ended_at
                    if ended_at_aware.tzinfo is None:
                        ended_at_aware = ended_at_aware.replace(tzinfo=datetime.timezone.utc)

                    # Make navigation_started_at timezone-aware (assume UTC if naive)
                    nav_started_at_aware = event.navigation_started_at
                    if nav_started_at_aware.tzinfo is None:
                        nav_started_at_aware = nav_started_at_aware.replace(tzinfo=datetime.timezone.utc)

                    # Now subtraction will work
                    actual_duration_seconds = (ended_at_aware - nav_started_at_aware).total_seconds()

                estimated_duration_seconds = event.estimated_time # Already saved as int (seconds)

                # 3. Calculate Score Components (Placeholder Logic - need to add FORMULA)
                # Example: Simple calculation fot this time
                landmark_factor_score = 0
                if total_landmarks > 0:
                    landmark_factor_score = (achieved_landmarks / total_landmarks) * 100  # Percentage

                time_factor_score = 0
                if actual_duration_seconds and estimated_duration_seconds and estimated_duration_seconds > 0:
                    # Score based on how close actual time was to estimate (higher is better if faster)
                    time_factor_score = max(0.0, 100 - abs(actual_duration_seconds - estimated_duration_seconds) / estimated_duration_seconds * 100)

                    # Example final score (simple average) - REPLACE WITH YOUR FORMULA
                final_task_score = (landmark_factor_score + time_factor_score) / 2
                time_factor_score_rounded = round(time_factor_score, 2)
                final_task_score_rounded = round(final_task_score, 2)

                path_performance = 12.9

                # 4. Create Score Object
                new_score = Score(
                    parking_events_id=event_id,
                    time_factor=time_factor_score_rounded,
                    landmark_factor=round(landmark_factor_score, 2),
                    path_performance= path_performance, # Add if needed
                    assistance_points=event.finalMapViewCount,  #  map views as assistance points
                    no_of_landmarks=total_landmarks,
                    landmarks_recalled=achieved_landmarks,
                    task_score=final_task_score_rounded
                )
                db.session.add(new_score)

                event.status = 'active'

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