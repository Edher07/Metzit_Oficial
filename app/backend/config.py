import os

# app/backend/  ->  app/
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BACKEND_DIR)

STATIC_DIR = os.path.join(APP_DIR, "static")
VIEWS_DIR = os.path.join(APP_DIR, "views")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "metzit-dev-secret-cambiar-en-produccion")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(APP_DIR, "metzit.sqlite3"))
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB
