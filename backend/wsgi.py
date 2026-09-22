"""
WSGI Entry Point for Production Deployment (Gunicorn / uWSGI)
Used by hosting platforms such as Render, Railway, Fly.io, and AWS Elastic Beanstalk.
"""

import os
from app import create_app

# Instantiate Flask application in production mode by default if not set
env_name = os.getenv("FLASK_ENV", "production")
app = create_app(env_name)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
