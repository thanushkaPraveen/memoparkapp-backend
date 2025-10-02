from flask import Flask
# Make sure to import the new migrate object
from .extensions import db, bcrypt, jwt, migrate

# Import all your models so that Flask-Migrate can see them
from .models.user_type import UserType
from .models.user import User
from .models.emergency_contact import EmergencyContact
from .models.parking_event import ParkingEvent
from .models.landmark import Landmark
from .models.score import Score


def create_app(config_object='config.Config'):
    """An application factory."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)  # <-- Initialize migrate here

    return app