#sql_statement.py

CREATE_USER_TYPE_TABLE  = """
CREATE TABLE IF NOT EXISTS UserType (
  user_type_id INT AUTO_INCREMENT PRIMARY KEY,
  user_type VARCHAR(45) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""

CREATE_USER_TABLE  = """
CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_type_id INT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    user_email VARCHAR(255) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    text_size ENUM('small', 'medium', 'large') DEFAULT 'medium',
    icon_size ENUM('default', 'medium', 'large') DEFAULT 'default',
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_type_id) REFERENCES UserType(user_type_id)
);
"""

CREATE_EMERGENCY_CONTACT_TABLE  = """
CREATE TABLE IF NOT EXISTS EmergencyContact (
    emergency_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    emergency_contact_name VARCHAR(100) NOT NULL,
    relation VARCHAR(50),
    emergency_email VARCHAR(255),
    emergency_phone_number VARCHAR(20),
    is_allow_alerts BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);
"""

CREATE_PARKING_EVENT_TABLE  = """
CREATE TABLE IF NOT EXISTS ParkingEvent (
    parking_events_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    parking_latitude DECIMAL(9, 6) NOT NULL,
    parking_longitude DECIMAL(9, 6) NOT NULL,
    parking_location_name VARCHAR(255),
    parking_address TEXT,
    parking_type ENUM('outside', 'inside_building') DEFAULT 'outside',
    level_floor VARCHAR(20),
    parking_slot VARCHAR(20),
    notes TEXT,
    photo_url VARCHAR(2048),
    photo_s3_key VARCHAR(1024),
    started_at TIMESTAMP NULL,
    estimated_time INT,
    ended_at TIMESTAMP NULL,
    status ENUM('active', 'retrieved', 'expired') DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);
"""

CREATE_LANDMARK_TABLE  = """
CREATE TABLE IF NOT EXISTS Landmark (
    landmarks_id INT AUTO_INCREMENT PRIMARY KEY,
    parking_events_id INT NOT NULL,
    landmark_latitude DECIMAL(9, 6),
    landmark_longitude DECIMAL(9, 6),
    location_name VARCHAR(255),
    distance_from_parking FLOAT,
    photo_url VARCHAR(2048),
    photo_s3_key VARCHAR(1024),
    is_achieved BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parking_events_id) REFERENCES ParkingEvent(parking_events_id) ON DELETE CASCADE
);
"""

CREATE_SCORE_TABLE  = """
CREATE TABLE IF NOT EXISTS Score (
    scores_id INT AUTO_INCREMENT PRIMARY KEY,
    parking_events_id INT NOT NULL UNIQUE,
    time_factor FLOAT,
    landmark_factor FLOAT,
    path_performance FLOAT,
    assistance_points INT,
    no_of_landmarks INT,
    landmarks_recalled INT,
    task_score FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parking_events_id) REFERENCES ParkingEvent(parking_events_id) ON DELETE CASCADE
);
"""

CREATE_DB = "CREATE DATABASE IF NOT EXISTS"
DEFAULT_OB_NAME = "memopark_db"

