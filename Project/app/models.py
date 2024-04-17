from socket import SO_EXCLUSIVEADDRUSE
from xml.sax import SAXException
from flask import jsonify
from .extensions import db, event, Session
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


class TransactionLog(db.Model):
    __tablename__ = 'transaction_log'
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50))  # 'add' or 'subtract'
    source_type = db.Column(db.String(50))  # 'partner' or 'small_storage'
    source_id = db.Column(db.Integer, nullable=True)  # ID of the source, if applicable
    destination_type = db.Column(db.String(50))  # 'main_storage'
    destination_id = db.Column(db.Integer, nullable=True)  # ID of the destination, if applicable
    quantity = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Use datetime.utcnow without ()
    transaction_logs = []
    
    def __repr__(self):
        return (f"TransactionLog(action_type={self.action_type}, quantity={self.quantity}, "
                f"source_type={self.source_type}, source_id={self.source_id}, "
                f"destination_type={self.destination_type}, destination_id={self.destination_id}, "
                f"timestamp={self.timestamp.isoformat()})")

def log_transaction(mapper, connection, target):
    action_type = 'add' if target.quantity > 0 else 'subtract'
    source_type = destination_type = source_id = destination_id = None

    if isinstance(target, Partner) or isinstance(target, SmallStorage):
        source_type = target.__tablename__
        source_id = target.id
        destination_type = 'main_storage'
    elif isinstance(target, MainStorage):
        destination_type = 'partner' if target.quantity < 0 else 'small_storage'
        source_type = 'main_storage'

    utc_time = datetime.utcnow()  # Get the current UTC time

    transaction_log = TransactionLog(
        action_type=action_type,
        source_type=source_type,
        source_id=source_id,
        destination_type=destination_type,
        destination_id=destination_id,
        quantity=abs(target.quantity),
        timestamp=utc_time
    )

    db.session.add(transaction_log)
    # Ensure that the transaction log is added to the session, but don't commit here
    # Commit will occur when the original transaction is committed

# Set up event listeners for the models
from sqlalchemy import Transaction, event
event.listen(MainStorage, 'after_insert', log_transaction)
event.listen(MainStorage, 'after_update', log_transaction)
event.listen(Partner, 'after_insert', log_transaction)
event.listen(Partner, 'after_update', log_transaction)
event.listen(SmallStorage, 'after_insert', log_transaction)
event.listen(SmallStorage, 'after_update', log_transaction)