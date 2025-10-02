from app.extensions import db, bcrypt
import enum


class TextSizeEnum(enum.Enum):
    small = 'small'
    medium = 'medium'
    large = 'large'


class IconSizeEnum(enum.Enum):
    default = 'default'
    medium = 'medium'
    large = 'large'


class User(db.Model):
    __tablename__ = 'User'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_type_id = db.Column(db.Integer, db.ForeignKey('UserType.user_type_id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default='en')
    text_size = db.Column(db.Enum(TextSizeEnum), default=TextSizeEnum.medium)
    icon_size = db.Column(db.Enum(IconSizeEnum), default=IconSizeEnum.default)
    high_contrast_mode = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    user_type = db.relationship('UserType', back_populates='users')
    emergency_contacts = db.relationship('EmergencyContact', back_populates='user', cascade="all, delete-orphan")
    parking_events = db.relationship('ParkingEvent', back_populates='user', cascade="all, delete-orphan")

    def __init__(self, user_password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.user_password = bcrypt.generate_password_hash(user_password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.user_password, password)