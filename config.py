import os
import configparser

def load_db_config(filename='config.ini', section='mysql'):
    """ Read database configuration file and return a dictionary object """
    # Create a parser
    parser = configparser.ConfigParser()
    # Read config file
    if not parser.read(filename):
        raise Exception(f'{filename} not found.')

    # Get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception(f'{section} not found in the {filename} file.')

    return db

class Config:
    """Base configuration."""

    # Load database configuration from config.ini
    db_config = load_db_config()

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_secret_key_you_should_change')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'a_different_very_secret_key')

    # Database Config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://"
        f"{db_config.get('user')}:{db_config.get('password')}"
        f"@{db_config.get('host')}/{db_config.get('database')}"
    )