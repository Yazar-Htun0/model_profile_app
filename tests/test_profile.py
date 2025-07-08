import pytest
from flask import url_for
from app import ModelProfile, PortfolioImage, db # Assuming these are available
import os
from io import BytesIO

def test_edit_profile_page_loads_authenticated(logged_in_client):
    response = logged_in_client.get(url_for('edit_profile'))
    assert response.status_code == 200
    assert b"Edit Your Model Profile" in response.data

def test_edit_profile_page_redirects_unauthenticated(client):
    response = client.get(url_for('edit_profile'), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('login') in response.request.path
    assert b"Please log in to access this page." in response.data

def test_create_and_update_model_profile(logged_in_client, registered_user, app):
    # Initial profile creation
    profile_data = {
        'full_name': 'Test User Full Name',
        'age': 30,
        'height': 175.0,
        'weight': 65.0,
        'bust': 90.0,
        'waist': 60.0,
        'hips': 90.0,
        'shoe_size': '8',
        'phone_number': '123-456-7890',
        'instagram_handle': '@testuserinsta',
        'work_experience_summary': 'Experienced model.',
        'skills_summary': 'Acting, Dancing.',
        'based_in_city': 'Testville',
        'willing_to_travel': True,
        'availability_status': 'Available',
    }
    response = logged_in_client.post(url_for('edit_profile'), data=profile_data,
                                     query_string={'submit_profile': 'True'}, # Simulate clicking the profile submit
                                     follow_redirects=True)
    assert response.status_code == 200
    assert b"Your profile has been updated!" in response.data

    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        assert profile is not None
        assert profile.full_name == profile_data['full_name']
        assert profile.age == profile_data['age']
        assert profile.willing_to_travel == profile_data['willing_to_travel']

    # Update profile
    updated_profile_data = {
        'full_name': 'Test User Updated Name',
        'age': 31,
        'height': 176.0, # Changed
        # ... include all fields as the form populates the object
        'weight': profile.weight,
        'bust': profile.bust,
        'waist': profile.waist,
        'hips': profile.hips,
        'shoe_size': profile.shoe_size,
        'phone_number': profile.phone_number,
        'instagram_handle': profile.instagram_handle,
        'work_experience_summary': 'Very experienced model.', # Changed
        'skills_summary': profile.skills_summary,
        'based_in_city': profile.based_in_city,
        'willing_to_travel': False, # Changed
        'availability_status': profile.availability_status,
    }
    response = logged_in_client.post(url_for('edit_profile'), data=updated_profile_data,
                                     query_string={'submit_profile': 'True'},
                                     follow_redirects=True)
    assert response.status_code == 200
    assert b"Your profile has been updated!" in response.data

    with app.app_context():
        updated_profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        assert updated_profile.full_name == updated_profile_data['full_name']
        assert updated_profile.age == updated_profile_data['age']
        assert updated_profile.height == updated_profile_data['height']
        assert updated_profile.work_experience_summary == updated_profile_data['work_experience_summary']
        assert updated_profile.willing_to_travel == updated_profile_data['willing_to_travel']


def test_upload_portfolio_image(logged_in_client, registered_user, app):
    # Ensure user has a profile first
    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        if not profile:
            profile = ModelProfile(user_id=registered_user.id, full_name="Temp Profile for Image Test")
            db.session.add(profile)
            db.session.commit()

    image_data = {
        'image': (BytesIO(b"someimagedata"), 'test.jpg'),
        'caption': 'Test image caption'
    }
    response = logged_in_client.post(url_for('edit_profile'), data=image_data,
                                     content_type='multipart/form-data',
                                     query_string={'submit_image': 'True'}, # Simulate image upload submit
                                     follow_redirects=True)

    assert response.status_code == 200
    assert b"New image added to your portfolio!" in response.data

    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        assert profile is not None
        portfolio_image = PortfolioImage.query.filter_by(model_profile_id=profile.id).first()
        assert portfolio_image is not None
        assert portfolio_image.caption == image_data['caption']
        assert 'test.jpg' in portfolio_image.image_filename

        # Check if file exists (adjust path as per app.config['UPLOAD_FOLDER'])
        upload_folder = app.config['UPLOAD_FOLDER']
        expected_path = os.path.join(upload_folder, portfolio_image.image_filename)
        assert os.path.exists(expected_path)

        # Cleanup: remove the test image file
        os.remove(expected_path)


def test_delete_portfolio_image(logged_in_client, registered_user, app):
    # 1. Create a profile if it doesn't exist
    # 2. Upload an image
    # 3. Delete the image
    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        if not profile:
            profile = ModelProfile(user_id=registered_user.id, full_name="Temp Profile for Delete Test")
            db.session.add(profile)
            db.session.commit()

        # Upload an image directly via model for simplicity in setting up delete test
        # (or reuse the upload test logic if preferred)
        unique_filename = "delete_test_image.jpg" # Ensure this is unique if running multiple times or use uuid
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        with open(image_path, 'wb') as f: # Create dummy file
            f.write(b"dummy image data for delete test")

        image_to_delete = PortfolioImage(
            model_profile_id=profile.id,
            image_filename=unique_filename,
            caption="Image to be deleted"
        )
        db.session.add(image_to_delete)
        db.session.commit()
        image_id_to_delete = image_to_delete.id
        assert os.path.exists(image_path) # Verify file exists before delete

    # Perform delete request
    response = logged_in_client.post(url_for('delete_portfolio_image', image_id=image_id_to_delete),
                                     follow_redirects=True)
    assert response.status_code == 200
    assert b"Image has been deleted" in response.data

    with app.app_context():
        deleted_image_check = PortfolioImage.query.get(image_id_to_delete)
        assert deleted_image_check is None
        assert not os.path.exists(image_path) # Verify file is removed


def test_public_profile_view(client, registered_user, app):
    # Ensure user has a profile and some data
    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        if not profile:
            profile = ModelProfile(user_id=registered_user.id, full_name="Public Test User", age=25)
            db.session.add(profile)
            db.session.commit()
        else: # Ensure some data is there
            profile.full_name = "Public Test User"
            profile.age = 25
            db.session.commit()

    response = client.get(url_for('public_profile', username=registered_user.username))
    assert response.status_code == 200
    assert b"Public Test User" in response.data
    assert b"Age: 25" in response.data # Check for specific data points

def test_public_profile_not_found(client):
    response = client.get(url_for('public_profile', username="nonexistentuser"))
    assert response.status_code == 404

def test_public_profile_user_exists_no_modelprofile(client, registered_user, app):
    # Scenario: User is registered, but ModelProfile record doesn't exist or is empty.
    # The `registered_user` fixture creates a user. We need to ensure no ModelProfile.
    with app.app_context():
        profile = ModelProfile.query.filter_by(user_id=registered_user.id).first()
        if profile:
            db.session.delete(profile) # Remove any existing profile
            db.session.commit()

    response = client.get(url_for('public_profile', username=registered_user.username))
    assert response.status_code == 200 # Page should load
    assert registered_user.username.encode() in response.data # Username should be there
    assert b"This user has not created a detailed model profile yet." in response.data
    # Check that profile-specific fields are NOT there or handled gracefully
    assert b"Full Name:" not in response.data # Assuming this label only appears if data exists
    assert b"Age:" not in response.data

# It might be good to also test that a user cannot delete another user's image,
# or edit another user's profile. Flask-Login's @login_required and checking current_user.id
# should handle this, but dedicated tests can confirm.
# For example:
# def test_cannot_delete_others_image(logged_in_client, app, registered_user):
#     # 1. Create another_user and their image
#     # 2. Try to delete other_user's image as logged_in_client (who is registered_user)
#     # 3. Assert failure (e.g., flash message, redirect, 403/404)
#     pass
