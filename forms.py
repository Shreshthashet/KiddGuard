from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms import TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ParentSignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Parent Account')

class ChildSignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    parent_id = SelectField('Parent Account', coerce=int, validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=5, max=17)])
    submit = SubmitField('Create Child Account')

class EmergencyForm(FlaskForm):
    message = TextAreaField('Emergency Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Send Emergency Alert')

class ContentFilterForm(FlaskForm):
    block_adult = BooleanField('Block Adult Content', default=True)
    block_violence = BooleanField('Block Violent Content', default=True)
    block_gambling = BooleanField('Block Gambling Sites', default=True)
    block_social_media = BooleanField('Block Social Media', default=False)
    custom_keywords = TextAreaField('Custom Keywords to Block', 
                                   validators=[Optional()],
                                   description='Enter keywords separated by commas')
    submit = SubmitField('Save Filter Settings')
