# app/forms.py
from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField, StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length
 
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StorageForm(FlaskForm):
    name = StringField('Storage Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    action = RadioField('Action', choices=[('give', 'Give'), ('take', 'Take')], default='give')
    submit = SubmitField('Update Storage')

    def validate_quantity(form, field):
        if field.data < 0:
            raise ValidationError('Quantity must be a non-negative integer.')
