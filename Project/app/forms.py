# app/forms.py
from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField, SelectField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from app.models import Partner, SmallStorage

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StorageForm(FlaskForm):
    name = StringField('Storage Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    action = RadioField('Action', choices=[('give', 'Give'), ('take', 'Take')], default='give')
    submit = SubmitField('Update Storage')

        
class SmallStorageForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Create Small Storage')

class PartnerForm(FlaskForm):
 name = StringField('Name', validators=[DataRequired()])
 quantity = IntegerField('Quantity', validators=[DataRequired()])
 submit = SubmitField('Create Small Storage')


def get_partner_choices():
    return Partner.query

def get_small_storage_choices():
    return SmallStorage.query

class TransactionForm(FlaskForm):
    partner_id = SelectField('Partner', coerce=int, validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    submit = SubmitField('Update Balance')

class AdjustMainStorageForm(FlaskForm):
    entity_type = SelectField('Entity Type', choices=[('partner', 'Partner'), ('small_storage', 'Small Storage')])
    entity_id = SelectField('Entity ID', coerce=int, choices=[])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    action = SelectField('Action', choices=[('add', 'Add'), ('subtract', 'Subtract')])
    submit = SubmitField('Submit')