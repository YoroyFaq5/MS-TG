import os

from bot import create_app

app = create_app(os.environ.get("FLASK_ENV", "default"))

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
