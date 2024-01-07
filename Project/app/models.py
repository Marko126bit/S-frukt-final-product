from .extensions import db
from flask_login import UserMixin
from datetime import datetime

def get_main_storage_data():
    # Hypothetical function to retrieve data from the database
    data = Storage.query.all()  # This is just an example query
    return data

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Storage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)  # Storing the quantity of items
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class MainStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_quantity = db.Column(db.Integer, default=0)

    def adjust_quantity(self, quantity):
        self.total_quantity += quantity

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