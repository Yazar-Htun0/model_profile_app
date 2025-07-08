import pytest
from app import app as flask_app, db, User # Adjust 'app' if your main file is named differently

@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    flask_app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms
    flask_app.config['LOGIN_DISABLED'] = False # Ensure login is enabled for auth tests

    with flask_app.app_context():
        db.drop_all() # Ensure clean slate before creating
        db.create_all()
        yield flask_app # provide the app first
        db.session.remove()
        db.drop_all() # Clean up after module tests

@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function') # Use function scope for db interactions to ensure clean slate
def init_database(app):
    """Clear and recreate database tables for each test function if needed,
       or manage transactions."""
    with app.app_context():
        # db.session.remove()
        # db.drop_all() # This might be too slow if run for every function.
        # db.create_all() # Consider using transactions or specific cleanup.
        pass # Using in-memory DB means it's fresh per module.
             # If tests modify db and need reset per test, more specific cleanup needed.

@pytest.fixture(scope='function')
def new_user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }

@pytest.fixture(scope='function')
def registered_user(client, new_user_data, app):
    """Register and return a new user."""
    client.post('/register', data={
        'username': new_user_data['username'],
        'email': new_user_data['email'],
        'password': new_user_data['password'],
        'confirm_password': new_user_data['password']
    })
    with app.app_context():
        user = User.query.filter_by(email=new_user_data['email']).first()
        return user

@pytest.fixture(scope='function')
def logged_in_client(client, registered_user, new_user_data):
    """A test client that is logged in as the registered_user."""
    client.post('/login', data={
        'email': new_user_data['email'],
        'password': new_user_data['password']
    }, follow_redirects=True)
    return client
