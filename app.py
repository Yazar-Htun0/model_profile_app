# app.py

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os

from extensions import db # Import db from extensions

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # Needed for session management and CSRF protection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app) # Initialize db with app

login_manager = LoginManager(app)
login_manager.login_view = 'login' # The route to redirect to if login is required
login_manager.login_message_category = 'info' # Flash message category

from models import User, ModelProfile, PortfolioImage # Import models here

@login_manager.user_loader
def load_user(user_id):
    # This callback is used to reload the user object from the user ID stored in the session
    return User.query.get(int(user_id))

@app.route('/')
def home():
    """
    This is the main route for our application.
    It renders the 'index.html' template.
    """
    return render_template('index.html')

# Import forms
from forms import RegistrationForm, LoginForm, ModelProfileForm, PortfolioImageForm
from werkzeug.utils import secure_filename
import uuid # For generating unique filenames

# Configuration for uploads
UPLOAD_FOLDER = 'static/uploads/portfolio_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Example: 16MB upload limit - consider adding

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Placeholder for a protected route - to test login
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

@app.route("/profile/edit", methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile  # Assuming current_user has a 'profile' backref
    if not profile:
        # If no profile exists, create one
        profile = ModelProfile(user_id=current_user.id)
        # db.session.add(profile) # Add later if form is submitted and valid
        # db.session.commit() # Commit later

    form = ModelProfileForm(obj=profile) # For editing text profile data
    image_form = PortfolioImageForm() # For uploading new images

    if 'submit_profile' in request.form and form.validate_on_submit():
        form.populate_obj(profile)
        if not current_user.profile:
            db.session.add(profile)
        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('edit_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    if 'submit_image' in request.form and image_form.validate_on_submit():
        if not profile.id: # Ensure profile is saved and has an ID before adding images
            flash('Please save your main profile information first before adding images.', 'warning')
            # Potentially, we could save the profile here if it's partially filled and valid
            # For now, require existing profile.
        else:
            image_file = image_form.image.data
            filename = secure_filename(image_file.filename)
            # Generate a unique filename to prevent overwrites and ensure security
            unique_filename = str(uuid.uuid4()) + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            try:
                image_file.save(file_path)
                new_image = PortfolioImage(
                    model_profile_id=profile.id,
                    image_filename=unique_filename,
                    caption=image_form.caption.data
                )
                db.session.add(new_image)
                db.session.commit()
                flash('New image added to your portfolio!', 'success')
                return redirect(url_for('edit_profile'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error uploading image: {str(e)}', 'danger')

    portfolio_images = []
    if profile and profile.id:
        portfolio_images = PortfolioImage.query.filter_by(model_profile_id=profile.id).order_by(PortfolioImage.uploaded_at.desc()).all()

    return render_template('edit_profile.html', title='Edit Profile',
                           form=form, image_form=image_form, portfolio_images=portfolio_images)


# Route to delete a portfolio image
@app.route('/portfolio/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_portfolio_image(image_id):
    image = PortfolioImage.query.get_or_404(image_id)
    profile = current_user.profile

    if not profile or image.model_profile_id != profile.id:
        flash('You are not authorized to delete this image.', 'danger')
        return redirect(url_for('edit_profile'))

    try:
        # Construct path and delete file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(image)
        db.session.commit()
        flash('Image has been deleted from your portfolio.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'danger')

    return redirect(url_for('edit_profile'))

@app.route('/profile/<string:username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    profile = user.profile # Relies on the backref from User to ModelProfile

    if not profile:
        # Or handle differently, e.g., show a "profile not created" message
        # For now, if a user exists but has no profile, it's a 404 on the profile itself.
        # However, the prompt implies we show what IS there.
        # Let's allow viewing a user even if their ModelProfile part is minimal/None.
        # The template will have to handle a potentially None `profile`.
        pass

    portfolio_images = []
    if profile:
        portfolio_images = PortfolioImage.query.filter_by(model_profile_id=profile.id)\
                                           .order_by(PortfolioImage.uploaded_at.asc())\
                                           .all()

    return render_template('public_profile.html', title=f"{user.username}'s Profile",
                           user=user, profile=profile, portfolio_images=portfolio_images)


if __name__ == '__main__':
    # Run the Flask application in debug mode.
    # Debug mode allows for automatic reloading on code changes
    # and provides a debugger in the browser.
    # Consider creating DB tables here if they don't exist, or using Flask-Migrate
    with app.app_context():
        db.create_all() # Creates database tables based on models
    app.run(debug=True)


