#Read data from INI file
import configparser
import time
from sys import flags
import mysql.connector
from mysql.connector import Error
from .sql_statement import *


class Database:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.config_filename = 'config.ini'  # Initialize here
            cls._instance._init_database()
        return cls._instance

    def _init_database(self):
        """Initialize the database connection."""
        self.connection = None
        try:
            config = self.load_config()
            self.connection = mysql.connector.connect(**config, autocommit=True)
            if self.connection.is_connected():
                print("✅ Database connected successfully.")
                self._check_database_exist()
                self._check_table_exist()
        except Error as e:
            self._check_database_exist_if_db_error_occur()
            self._check_table_exist()


    def create_connection_parser(self):

        config = self.load_config()

        self.connection = mysql.connector.connect(**config, autocommit=True)
        if self.connection.is_connected:
            return self.connection.cursor()
        else:
            raise Exception

    def _check_database_exist(self):
        config = self.load_config()
        if not config.get("database") or config['database'] != DEFAULT_OB_NAME:
            config['database'] = DEFAULT_OB_NAME
            cursor = self.create_connection_parser()
            cursor.execute(f"{CREATE_DB} {config['database']};")
            self.save_config(config)
        return

    def _check_table_exist(self):
        cursor = self.create_connection_parser()
        cursor.execute(CREATE_USER_TYPE_TABLE)
        cursor.execute(CREATE_USER_TABLE)
        cursor.execute(CREATE_EMERGENCY_CONTACT_TABLE)
        cursor.execute(CREATE_PARKING_EVENT_TABLE)
        cursor.execute(CREATE_LANDMARK_TABLE)
        cursor.execute(CREATE_SCORE_TABLE)

    def load_config(self):
        # Load database configurations
        config = configparser.ConfigParser()
        config.read(self.config_filename)
        return {key: value for key, value in config['mysql'].items()}

    def save_config(self, config):
        # Save database configurations to the INI file (local)
        config_parser = configparser.ConfigParser()
        config_parser['mysql'] = config
        # Write the configuration to the file
        with open(self.config_filename, 'w') as configfile:
            config_parser.write(configfile)

    def add_to_database(self, sql, values):
        try:
            cursor = self.create_connection_parser()
            cursor.execute(sql, values)
            added_id = cursor.lastrowid
            # print(f"added ID: {sql, values, added_id}")
            return added_id

        except Error as e:
            print(f"Error: {e}")

    def update_database(self, sql, values):
        """
        Update records in the database.
        :param sql: SQL update query
        :param values: Tuple of values to be updated
        """
        try:
            cursor = self.create_connection_parser()
            cursor.execute(sql, values)
            self.connection.commit()
            # print(f"Updated rows: {sql, values, cursor.rowcount}")
        except Error as e:
            print(f"Error: {e}")

    def delete_from_database(self, sql, values):
        """
        Delete records from the database.
        :param sql: SQL delete query
        :param values: Tuple of values for the condition
        """
        try:
            cursor = self.create_connection_parser()
            cursor.execute(sql, values)
            self.connection.commit()
            print(f"Deleted rows: {cursor.rowcount}")
        except Error as e:
            print(f"Error: {e}")

    def select_from_database(self, sql, values=None):
        """
        Select records from the database.
        :param sql: SQL select query
        :param values: Optional tuple of values for the condition
        :return: List of rows
        """
        try:
            cursor = self.create_connection_parser()
            cursor.execute(sql, values or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error: {e}")
            return []

    def _check_database_exist_if_db_error_occur(self):
        config = self.load_config()

        # Create a temporary connection without specifying a database
        temp_config = config.copy()
        temp_config.pop("database", None)  # Remove database from config to connect to MySQL server

        try:
            temp_connection = mysql.connector.connect(**temp_config, autocommit=True)
            temp_cursor = temp_connection.cursor()

            # Check if the database exists
            temp_cursor.execute("SHOW DATABASES;")
            databases = [db[0] for db in temp_cursor.fetchall()]

            if DEFAULT_OB_NAME not in databases:
                print(f"Database {DEFAULT_OB_NAME} not found. Creating...")
                temp_cursor.execute(f"CREATE DATABASE {DEFAULT_OB_NAME};")

            # Close the temporary connection
            temp_cursor.close()
            temp_connection.close()

            # Update the config with the correct database name and reconnect
            config['database'] = DEFAULT_OB_NAME
            self.save_config(config)  # Save the updated config

        except Error as e:
            print(f"Error while checking/creating database: {e}")





