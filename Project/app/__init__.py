# app/__init__.py
from flask import Flask
from .extensions import db, login_manager, bcrypt, cache
from .config import Config  # Make sure 'Config' is defined in 'config.py'
from .models import User  # This line ensures models are imported and recognized by SQLAlchemy
from .routes import configure_routes  # This function will set up your routes
from werkzeug.security import generate_password_hash

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['CACHE_TYPE'] = 'simple'  # You can choose 'simple', 'memcached', 'redis', etc.


    cache.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Inside the app context, create the database and users
    with app.app_context():
        db.create_all()  # Create database tables
        # Create predefined users
        if not User.query.filter_by(username='marko').first():
            user1 = User(username='marko', password=generate_password_hash('svalerka1'))
            db.session.add(user1)
        if not User.query.filter_by(username='milos').first():
            user2 = User(username='milos', password=generate_password_hash('svalerka2'))
            db.session.add(user2)
        if not User.query.filter_by(username='rale').first():
            user3 = User(username='rale', password=generate_password_hash('svalerka3'))
            db.session.add(user3)
        db.session.commit()

    # Import and register your application's routes
    from . import routes
    routes.configure_routes(app)

    return app