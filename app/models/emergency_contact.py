from app.extensions import db

class EmergencyContact(db.Model):
    __tablename__ = 'EmergencyContact'

    emergency_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    emergency_contact_name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50))
    emergency_email = db.Column(db.String(255))
    emergency_phone_number = db.Column(db.String(20))
    is_allow_alerts = db.Column(db.Boolean, default=False)
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship to User
    user = db.relationship('User', back_populates='emergency_contacts')