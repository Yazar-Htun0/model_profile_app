import pytest
from flask import url_for, session
from app import User # Assuming User model is in app.py or models.py imported into app's namespace

def test_register_page_loads(client):
    response = client.get(url_for('register'))
    assert response.status_code == 200
    assert b"Join Today" in response.data

def test_login_page_loads(client):
    response = client.get(url_for('login'))
    assert response.status_code == 200
    assert b"Log In" in response.data

def test_register_new_user(client, new_user_data, app):
    response = client.post(url_for('register'), data={
        'username': new_user_data['username'],
        'email': new_user_data['email'],
        'password': new_user_data['password'],
        'confirm_password': new_user_data['password']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your account has been created!" in response.data # Flash message
    assert url_for('login') in response.request.path # Should redirect to login

    with app.app_context():
        user = User.query.filter_by(email=new_user_data['email']).first()
        assert user is not None
        assert user.username == new_user_data['username']

def test_register_existing_user(client, registered_user, new_user_data):
    # 'registered_user' fixture already creates a user. Try to register again.
    response = client.post(url_for('register'), data={
        'username': new_user_data['username'] + "_new", # Different username
        'email': new_user_data['email'], # Same email
        'password': new_user_data['password'],
        'confirm_password': new_user_data['password']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"That email is taken." in response.data # Validation error

    response = client.post(url_for('register'), data={
        'username': new_user_data['username'], # Same username
        'email': new_user_data['email'] + "_new@example.com", # Different email
        'password': new_user_data['password'],
        'confirm_password': new_user_data['password']
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"That username is taken." in response.data # Validation error


def test_login_valid_user(client, registered_user, new_user_data):
    response = client.post(url_for('login'), data={
        'email': new_user_data['email'],
        'password': new_user_data['password']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login successful!" in response.data
    assert url_for('home') in response.request.path # Should redirect to home/dashboard

    with client.session_transaction() as sess:
        assert sess['_user_id'] == str(registered_user.id) # Flask-Login stores user_id in session
        assert sess['user_id'] == str(registered_user.id) # Flask-Login also stores user_id directly

def test_login_invalid_password(client, registered_user, new_user_data):
    response = client.post(url_for('login'), data={
        'email': new_user_data['email'],
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login Unsuccessful." in response.data
    with client.session_transaction() as sess:
        assert '_user_id' not in sess

def test_logout(logged_in_client): # uses the client that is already logged in
    response = logged_in_client.get(url_for('logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data
    assert url_for('home') in response.request.path

    with logged_in_client.session_transaction() as sess:
        assert '_user_id' not in sess

def test_access_protected_route_unauthenticated(client):
    response = client.get(url_for('dashboard'), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('login') in response.request.path # Should redirect to login
    assert b"Please log in to access this page." in response.data # Flash message from LoginManager

def test_access_protected_route_authenticated(logged_in_client):
    response = logged_in_client.get(url_for('dashboard'))
    assert response.status_code == 200
    assert b"Dashboard" in response.data # Assuming "Dashboard" is in the dashboard template title/header
    assert b"Welcome to your dashboard" in response.data
    assert url_for('login') not in response.request.path
