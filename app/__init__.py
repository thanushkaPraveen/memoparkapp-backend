from flask import Flask
from .extensions import db, bcrypt, jwt, migrate


def create_app(config_object='config.Config'):

    """An application factory."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)  # <-- Initialize migrate here

    # --- JWT Blocklist Checker ---
    # This callback function will be called every time a protected endpoint is
    # accessed, and will check if the JWT has been revoked.
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        # This import must be inside the function to avoid circular imports
        from .models.token_blocklist import TokenBlocklist
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    # --- Register Blueprints ---
    # We use an app context to avoid circular import issues.
    with app.app_context():
        # Import the blueprints
        from .routes.auth import auth_bp
        from .routes.parking_routes import parking_bp
        from .routes.score_routes import score_bp

        # Register the blueprints with the app
        app.register_blueprint(auth_bp)
        app.register_blueprint(parking_bp)
        app.register_blueprint(score_bp)

    return app