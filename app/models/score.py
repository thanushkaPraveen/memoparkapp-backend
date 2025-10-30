from app.extensions import db


class Score(db.Model):
    __tablename__ = 'Score'

    scores_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parking_events_id = db.Column(db.Integer, db.ForeignKey('ParkingEvent.parking_events_id'), unique=True,
                                  nullable=False)
    # Performance factors
    time_factor = db.Column(db.Float)
    landmark_factor = db.Column(db.Float)
    path_performance = db.Column(db.Float)
    assistance_points = db.Column(db.Integer)
    no_of_landmarks = db.Column(db.Integer)
    landmarks_recalled = db.Column(db.Integer)
    task_score = db.Column(db.Float)
    peek_penalty = db.Column(db.Integer, default=0)
    assist_penalty = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship
    parking_event = db.relationship("ParkingEvent", back_populates='score')