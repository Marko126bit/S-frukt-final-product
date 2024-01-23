
from .extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class MainStorage(db.Model):
    __tablename__ = 'main_storage'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=0)
    
    
    
class Partner(db.Model):
    __tablename__ = 'partner'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contribution_amount = db.Column(db.Integer)
    quantity = db.Column(db.Integer, default=0)
    main_storage_id = db.Column(db.Integer, db.ForeignKey('main_storage.id'))

# In your SmallStorage model
class SmallStorage(db.Model):
 __tablename__ = 'small_storage'
 id = db.Column(db.Integer, primary_key=True)
 name = db.Column(db.String(100), nullable=False)
 quantity = db.Column(db.Integer, default=0)
 main_storage_id = db.Column(db.Integer, db.ForeignKey('main_storage.id'))
