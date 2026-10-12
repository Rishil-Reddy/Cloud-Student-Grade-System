```python
import os

from flask import Flask, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from routes import api_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    app.config.from_object(Config)

    # CORS configuration
    # Restrict API access to configured frontend origins in production.
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    origin.strip()
                    for origin in allowed_origins
                    if origin.strip()
                ]
            }
        }
    )

    # Rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # Apply a specific rate limit to API routes
    limiter.limit("20 per minute")(api_bp)

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = (
            "strict-origin-when-cross-origin"
        )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' "
            "https://www.gstatic.com "
            "https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' "
            "http://127.0.0.1:* "
            "http://localhost:* "
            "https://identitytoolkit.googleapis.com "
            "https://securetoken.googleapis.com "
            "https://firestore.googleapis.com "
            "https://*.googleapis.com; "
            "img-src 'self' data: https:;"
        )

        return response

    # Frontend entry point
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )
```
