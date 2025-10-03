from app import create_app
from seed import seed_cli  # Import the seed command group

# Create the Flask app instance
app = create_app()

# Register the seed command with the app's CLI
app.cli.add_command(seed_cli)

if __name__ == '__main__':
    app.run(debug=True)