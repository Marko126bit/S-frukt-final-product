
from .extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class MainStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_quantity = db.Column(db.Integer, default=0)
    

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    main_storage_id = db.Column(db.Integer, db.ForeignKey('main_storage.id'))

# In your SmallStorage model
class SmallStorage(db.Model):
 id = db.Column(db.Integer, primary_key=True)
 name = db.Column(db.String(100), nullable=False)
 quantity = db.Column(db.Integer, default=0)
 main_storage_id = db.Column(db.Integer, db.ForeignKey('main_storage.id'))

# In your MainStorageTransaction model
class MainStorageTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # 'partner' or 'small_storage'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys pointing to the 'id' field in Partner and SmallStorage models
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))  # Ensure partner table name is correct
    small_storage_id = db.Column(db.Integer, db.ForeignKey('small_storage.id'))  # Ensure small_storage table name is correct
