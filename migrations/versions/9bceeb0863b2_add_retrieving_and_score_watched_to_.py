"""Add retrieving and score_watched to StatusEnum

Revision ID: 9bceeb0863b2
Revises: d31c031b5d67
Create Date: 2025-10-20 20:21:39.186245

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql  # <-- IMPORTANT: Import mysql dialect

# revision identifiers, used by Alembic.
revision = '9bceeb0863b2'
down_revision = 'd31c031b5d67'
branch_labels = None
depends_on = None


def upgrade():
    # We alter the 'status' column in the 'ParkingEvent' table
    op.alter_column('ParkingEvent', 'status',
                    # This is the OLD list of values
                    existing_type=mysql.ENUM('active', 'retrieved', 'expired'),

                    # This is the NEW list with both values added
                    type_=mysql.ENUM('active', 'retrieving', 'retrieved', 'score_watched', 'expired'),

                    existing_nullable=False,
                    server_default=sa.text("'active'"))


def downgrade():
    # This reverses the process
    op.alter_column('ParkingEvent', 'status',
                    # This is the NEW list
                    existing_type=mysql.ENUM('active', 'retrieving', 'retrieved', 'score_watched', 'expired'),

                    # This is the OLD list
                    type_=mysql.ENUM('active', 'retrieved', 'expired'),

                    existing_nullable=False,
                    server_default=sa.text("'active'"))