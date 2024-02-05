# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from sqlalchemy import event
from sqlalchemy import case
from sqlalchemy.orm.session import Session

cache = Cache()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


