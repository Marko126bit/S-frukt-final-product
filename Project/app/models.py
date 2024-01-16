
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
    total_quantity = db.Column(db.Integer, default=0)
    @staticmethod
    def get_main_storage():
    # This method returns the first MainStorage instance found in the database.
    # It assumes that there is only one main storage record, i.e., a singleton pattern.
     main_storage = MainStorage.query.first()
     if main_storage is None:
        # If no main storage exists, create one and set its total quantity to zero.
        main_storage = MainStorage(total_quantity=0)
        db.session.add(main_storage)
        db.session.commit()
     return main_storage

    def adjust_quantity(self, amount, partner_id):
    # This method adjusts the total quantity of the main storage.
    # It also updates the contributing partner's quantity accordingly.

    # Check if the partner exists and has enough quantity to give.
     partner = Partner.query.get(partner_id)
     if partner is None or partner.quantity < amount:
        raise ValueError('Invalid partner or not enough quantity to contribute.')

    # Update the quantities for both main storage and partner.
     self.total_quantity += amount
     partner.quantity -= amount

    # Persist changes to the database.
     db.session.add(self)
     db.session.add(partner)
     db.session.commit()

class Partner(db.Model):
    __tablename__ = 'partner'
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
