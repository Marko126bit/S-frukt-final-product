# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache

cache = Cache()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

