from app.extensions import db


class UserType(db.Model):
    __tablename__ = 'UserType'

    user_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_type = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship to User
    users = db.relationship('User', back_populates='user_type')