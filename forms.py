from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User # To check if username/email already exists

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Import necessary field types and validators for ModelProfileForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import Optional, Length, NumberRange

class ModelProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Optional(), Length(max=120)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=0, max=150)])
    height = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=0)])
    weight = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    bust = FloatField('Bust (cm)', validators=[Optional(), NumberRange(min=0)])
    waist = FloatField('Waist (cm)', validators=[Optional(), NumberRange(min=0)])
    hips = FloatField('Hips (cm)', validators=[Optional(), NumberRange(min=0)])
    shoe_size = StringField('Shoe Size', validators=[Optional(), Length(max=10)])

    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    instagram_handle = StringField('Instagram Handle', validators=[Optional(), Length(max=50)])

    work_experience_summary = TextAreaField('Work Experience Summary', validators=[Optional(), Length(max=5000)])
    skills_summary = TextAreaField('Skills Summary (e.g., acting, dancing)', validators=[Optional(), Length(max=2000)])

    based_in_city = StringField('City You Are Based In', validators=[Optional(), Length(max=100)])
    willing_to_travel = BooleanField('Willing to Travel')
    availability_status = StringField('Availability Status (e.g., "Available for immediate bookings")', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Save Profile')

# For PortfolioImageForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField # SubmitField is already imported

class PortfolioImageForm(FlaskForm):
    image = FileField('Upload Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    caption = StringField('Optional Caption', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Image to Portfolio')
