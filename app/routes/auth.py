from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.models.emergency_contact import EmergencyContact
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_email = data.get('user_email')
    user_password = data.get('user_password')

    if not user_email or not user_password:
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(user_email=user_email).first():
        return jsonify({"message": "User with this email already exists"}), 409

    # Create the user object
    new_user = User(
        user_name=data.get('user_name'),
        user_email=user_email,
        user_password=user_password,
        user_type_id=2  # Assuming 2 is the 'user' type
    )
    db.session.add(new_user)

    # IMPORTANT: Commit the user first to generate their primary key (user_id)
    db.session.commit()

    # Check for optional emergency contact data
    emergency_data = data.get('emergency_contact')
    if emergency_data and emergency_data.get('emergency_contact_name'):
        new_contact = EmergencyContact(
            user_id=new_user.user_id,  # Link to the newly created user
            emergency_contact_name=emergency_data.get('emergency_contact_name'),
            relation=emergency_data.get('relation'),
            emergency_phone_number=emergency_data.get('emergency_phone_number'),
            emergency_email = emergency_data.get('emergency_email'),
            is_allow_alerts=emergency_data.get('is_allow_alerts')
        )
        db.session.add(new_contact)
        # Commit again to save the new contact
        db.session.commit()

    # Generate an access token for the new user
    access_token = create_access_token(identity=new_user.user_id)

    # Return the access token
    return jsonify(access_token=access_token), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_email = data.get('user_email')
    user_password = data.get('user_password')

    if not user_email or not user_password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(user_email=user_email).first()

    if user and user.check_password(user_password):
        # Create a new token with the user's ID as the identity
        access_token = create_access_token(identity=user.user_id)
        return jsonify(access_token=access_token), 200

    return jsonify({"message": "Invalid credentials"}), 401


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()  # This decorator protects the endpoint
def get_profile():
    # Get the identity of the user from the access token (we stored user_id in it)
    current_user_id = get_jwt_identity()

    # Query the database to get the user object
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Prepare a list for the emergency contacts
    emergency_contacts_list = []
    # Loop through the contacts found via the relationship and format them
    for contact in user.emergency_contacts:
        emergency_contacts_list.append({
            "emergency_id": contact.emergency_id,
            "name": contact.emergency_contact_name,
            "relation": contact.relation,
            "emergency_phone_number": contact.emergency_phone_number,
            "emergency_email": contact.emergency_email,
            "is_allow_alerts": contact.is_allow_alerts
        })

    # Return the user's public information, including the list of contacts
    return jsonify({
        "user_id": user.user_id,
        "user_name": user.user_name,
        "user_email": user.user_email,
        "emergency_contacts": emergency_contacts_list  # Add the list to the response
    }), 200
