import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user_type import UserType

# Create a new Click command group
seed_cli = click.Group("seed", help="Commands to seed the database with initial data.")


@seed_cli.command("run", help="Seeds the database with initial user types.")
@with_appcontext
def run():
    """Seeds the database with admin and user types."""

    # Check if the user types already exist
    admin_type = UserType.query.filter_by(user_type='admin').first()
    user_type = UserType.query.filter_by(user_type='user').first()

    if not admin_type:
        print("Creating admin user type...")
        admin = UserType(user_type='admin')
        db.session.add(admin)
    else:
        print("Admin user type already exists.")

    if not user_type:
        print("Creating standard user type...")
        user = UserType(user_type='user')
        db.session.add(user)
    else:
        print("Standard user type already exists.")

    db.session.commit()
    print("User types seeding complete.")