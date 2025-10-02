from app.extensions import db


class Landmark(db.Model):
    __tablename__ = 'Landmark'

    landmarks_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parking_events_id = db.Column(db.Integer, db.ForeignKey('ParkingEvent.parking_events_id'), nullable=False)
    landmark_latitude = db.Column(db.Numeric(9, 6))
    landmark_longitude = db.Column(db.Numeric(9, 6))
    location_name = db.Column(db.String(255))
    distance_from_parking = db.Column(db.Float)
    photo_url = db.Column(db.String(2048))
    photo_s3_key = db.Column(db.String(1024))
    is_achieved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship
    parking_event = db.relationship("ParkingEvent", back_populates='landmarks')