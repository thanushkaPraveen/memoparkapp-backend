from app.extensions import db
import enum


class ParkingTypeEnum(enum.Enum):
    outside = 'outside'
    inside_building = 'inside_building'


class StatusEnum(enum.Enum):
    active = 'active'
    retrieved = 'retrieved'
    expired = 'expired'
    retrieving = 'retrieving'
    score_watched = 'score_watched'


class ParkingEvent(db.Model):
    __tablename__ = 'ParkingEvent'

    parking_events_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    parking_latitude = db.Column(db.Numeric(9, 6), nullable=False)
    parking_longitude = db.Column(db.Numeric(9, 6), nullable=False)
    parking_location_name = db.Column(db.String(255))
    parking_address = db.Column(db.Text)
    parking_type = db.Column(db.Enum(ParkingTypeEnum), default=ParkingTypeEnum.outside, nullable=False)
    level_floor = db.Column(db.String(20))
    parking_slot = db.Column(db.String(20))
    notes = db.Column(db.Text)
    photo_url = db.Column(db.String(2048))
    photo_s3_key = db.Column(db.String(1024))
    started_at = db.Column(db.TIMESTAMP, nullable=True)
    navigation_started_at = db.Column(db.TIMESTAMP, nullable=True)
    ended_at = db.Column(db.TIMESTAMP, nullable=True)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.active, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    user = db.relationship('User', back_populates='parking_events')
    landmarks = db.relationship("Landmark", back_populates='parking_event', cascade="all, delete-orphan")
    score = db.relationship("Score", back_populates='parking_event', uselist=False, cascade="all, delete-orphan")