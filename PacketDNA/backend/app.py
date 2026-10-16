"""
PacketDNA - Flask Application Entry Point
============================================
Main application factory and server startup.
"""

import os
import sys

from flask import Flask, send_from_directory
from flask_cors import CORS

from config.settings import get_config
from api.routes import api_bp


def create_app(config_name: str = None) -> Flask:
    """
    Application factory for creating the Flask app.

    Args:
        config_name: Configuration environment name.

    Returns:
        Configured Flask application instance.
    """
    config = get_config(config_name)

    # Create Flask app with frontend as static folder
    frontend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend")
    )

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path="",
    )

    # Load configuration
    app.config.from_object(config)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

    # Register blueprints
    app.register_blueprint(api_bp)

    # Ensure required directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.SAMPLE_DIR, exist_ok=True)
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.ML_MODELS_DIR, exist_ok=True)

    # Serve frontend
    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        if os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"\n{'='*60}")
    print(f"  PacketDNA v{get_config().APP_VERSION}")
    print(f"  Intelligent Network Traffic Classification")
    print(f"{'='*60}")
    print(f"  Dashboard:  http://127.0.0.1:5000")
    print(f"  API:        http://127.0.0.1:5000/api/v1")
    print(f"  Health:     http://127.0.0.1:5000/api/v1/health")
    print(f"{'='*60}\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
