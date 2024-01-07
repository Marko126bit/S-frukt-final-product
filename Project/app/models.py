
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

    def adjust_quantity(self, quantity):
        self.total_quantity += quantity

class MainStorageTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'add', 'subtract', 'delete', 'delete_all'
    entity_type = db.Column(db.String(50), nullable=False)  # 'partner' or 'small_storage'
    entity_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)

    def give_to_main(self, main_storage, quantity):
        if self.quantity >= quantity:
            self.quantity -= quantity
            main_storage.adjust_quantity(quantity)
        else:
            raise ValueError('Not enough quantity to give')

    def take_from_main(self, main_storage, quantity):
        if main_storage.total_quantity >= quantity:
            self.quantity += quantity
            main_storage.adjust_quantity(-quantity)
        else:
            raise ValueError('Not enough quantity in main storage to take')

class SmallStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)