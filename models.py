from extensions import db # Import db instance from extensions.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for stronger hashes

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class ModelProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True) # One-to-one with User
    user = db.relationship('User', backref=db.backref('profile', uselist=False)) # Establishes the relationship

    # Basic Information
    full_name = db.Column(db.String(120), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Float, nullable=True) # Store in cm or inches, be consistent
    weight = db.Column(db.Float, nullable=True) # Store in kg or lbs
    bust = db.Column(db.Float, nullable=True)
    waist = db.Column(db.Float, nullable=True)
    hips = db.Column(db.Float, nullable=True)
    shoe_size = db.Column(db.String(10), nullable=True) # Can be numeric or include half sizes like "7.5"

    # Contact Details - Email is already in User model. Phone can be here.
    phone_number = db.Column(db.String(20), nullable=True)
    instagram_handle = db.Column(db.String(50), nullable=True)
    # Other social media can be added similarly

    # Work Experience - This might be better as a separate related table if complex (e.g., multiple entries)
    # For simplicity now, a text field. Consider normalization later.
    work_experience_summary = db.Column(db.Text, nullable=True)

    # Skills - Similar to work experience, could be a separate table for multiple skills or a comma-separated string.
    skills_summary = db.Column(db.Text, nullable=True) # e.g., "acting, dancing, fluent in Spanish"

    # Location
    based_in_city = db.Column(db.String(100), nullable=True)
    willing_to_travel = db.Column(db.Boolean, default=False)

    # Availability
    availability_status = db.Column(db.String(255), nullable=True) # e.g., "Available for bookings", "On contract until YYYY-MM-DD"

    # Portfolio - Handled by a separate PortfolioImage model later

    def __repr__(self):
        return f'<ModelProfile for {self.user.username}>'

class PortfolioImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_profile_id = db.Column(db.Integer, db.ForeignKey('model_profile.id'), nullable=False)
    model_profile = db.relationship('ModelProfile', backref=db.backref('portfolio_images', lazy=True, cascade="all, delete-orphan"))

    image_filename = db.Column(db.String(255), nullable=False) # Stores filename, path will be constructed
    caption = db.Column(db.String(255), nullable=True) # Optional caption for the image
    uploaded_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<PortfolioImage {self.image_filename} for profile {self.model_profile_id}>'
