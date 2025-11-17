# MemoParkApp Backend

This repository contains the backend server for the **MemoParkApp** mobile application. This Python-Flask API is designed to support users with memory impairments by providing a reliable system to save, retrieve, and get assistance for finding their parked vehicle.

The API handles user authentication, data storage, a cognitive scoring system, and secure file uploads to AWS S3.

## Features

* **User Authentication**: Secure user registration, login, and logout using JSON Web Tokens (JWT) with a token blocklist.
* **Parking Event Management**: Full CRUD (Create, Read, Update, Delete) functionality for parking sessions.
* **Active Session Retrieval**: A dedicated endpoint (`/parking/latest-active`) to fetch the user's most recent active or retrieving session.
* **Landmark Support**: Users can add multiple landmarks to any parking event.
* **Cognitive Scoring**: A scoring system that calculates a user's performance based on time, landmarks recalled, and assistance used.
* **Secure File Uploads**: Direct uploads to a private AWS S3 bucket, with file access provided via temporary, pre-signed URLs.
* **Production Deployed**: Fully deployed on AWS using EC2, RDS, Gunicorn, and Nginx.

---
## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Framework** | [Flask](https://flask.palletsprojects.com/) |
| **Database** | [MySQL](https://www.mysql.com/) (Deployed on [AWS RDS](https://aws.amazon.com/rds/)) |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Migrations** | [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/) (Alembic) |
| **Authentication** | [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/en/stable/) |
| **File Storage** | [AWS S3](https://aws.amazon.com/s3/) (using `boto3`) |
| **Deployment** | [AWS EC2](https://aws.amazon.com/ec2/) (Ubuntu) |
| **WSGI Server** | [Gunicorn](https://gunicorn.org/) |
| **Reverse Proxy** | [Nginx](https://www.nginx.com/) |

---
## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing.

### Prerequisites

* Python 3.10+
* A running MySQL server (local or remote)
* An AWS S3 Bucket and IAM user (for local testing) or an IAM Role (for production)

### Local Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/thanushkaPraveen/memoparkapp-backend.git
    cd memoparkapp-backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.flaskenv` file in the root directory and add your secret keys and AWS credentials:
    ```ini
    FLASK_APP=run.py
    FLASK_ENV=development
    
    # Generate a random 32-byte hex string
    JWT_SECRET_KEY=your_very_strong_jwt_secret_key
    
    # Your AWS Credentials for local testing
    S3_BUCKET=your-s3-bucket-name
    AWS_REGION=your-bucket-region (e.g., ap-southeast-2)
    AWS_ACCESS_KEY_ID=your_aws_access_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret_key
    ```

5.  **Configure the Database:**
    Create a `config.ini` file in the root directory and add your MySQL database details:
    ```ini
    [mysql]
    host = localhost
    user = your_mysql_user
    password = your_mysql_password
    database = memopark_db
    ```

6.  **Set up the Database:**
    * Manually create the database in your MySQL client: `CREATE DATABASE memopark_db;`
    * Run the database migrations to create all tables:
        ```bash
        flask db upgrade
        ```
    * Seed the database with initial data (e.g., user types):
        ```bash
        flask seed run
        ```

7.  **Run the application:**
    ```bash
    flask run
    ```
    The server will be running at `http://127.0.0.1:5000`.

---
## Deployment

This application is deployed on an **AWS EC2 (Ubuntu)** instance.
* **Nginx** is used as a reverse proxy to handle public HTTP requests on port 80.
* **Gunicorn** runs the Flask application as a persistent service, managed by `systemd`.
* The EC2 instance uses an **IAM Role** for secure, key-less access to the S3 bucket.
* The **MySQL database** is hosted on **AWS RDS** and is only accessible from the EC2 instance's security group.

To deploy updates to the server:
```bash
# SSH into the server
ssh -i /path/to/key.pem ubuntu@<your_ip_address>

# Navigate to the app directory and pull changes
cd memoparkapp-backend
git pull

# Restart the Gunicorn service
sudo systemctl restart memopark

# (If database models changed)
source venv/bin/activate
flask db upgrade