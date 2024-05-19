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



class PartnerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Create Partner')

class SmallStorageForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    partner_id = SelectField('Partner', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Small Storage')

class DeletePartnerForm(FlaskForm):
    partner_id = SelectField('Partner', coerce=int)

class TransactionForm(FlaskForm):
    from_small_storage_id = SelectField('From Small Storage', coerce=int)
    to_small_storage_id = SelectField('To Small Storage', coerce=int)
    amount = IntegerField('Amount', validators=[DataRequired()])
