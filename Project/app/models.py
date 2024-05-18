
from pytz import timezone
import pytz
from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


# Define models
class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)
    small_storages = db.relationship('SmallStorage', backref='partner', lazy=True)

class SmallStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    def return_quantity(self, quantity):
        if quantity <= 0:
            return False  # Invalid quantity

        if quantity > self.quantity:
            return False  # Quantity to return exceeds available quantity

        # Update small storage quantity and partner balance
        self.quantity -= quantity
        self.partner.balance += quantity
        db.session.commit()
        return True

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(64), unique=True, nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    partner = db.relationship('Partner', backref=db.backref('cards', lazy=True))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    small_storage_id = db.Column(db.Integer, db.ForeignKey('small_storage.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    small_storage = db.relationship('SmallStorage', backref=db.backref('transactions', lazy=True))
    partner = db.relationship('Partner', backref=db.backref('transactions', lazy=True))
    card = db.relationship('Card', backref=db.backref('transactions', lazy=True))

 


