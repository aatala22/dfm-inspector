"""Flask application factory."""

import os
import tempfile

from flask import Flask

from .config import MAX_FILE_SIZE_MB


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"))
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(tempfile.gettempdir(), "dfm_uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from .routes import bp
    app.register_blueprint(bp)

    return app
