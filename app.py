# app.py

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    """
    This is the main route for our application.
    It renders the 'index.html' template.
    """
    return render_template('index.html')

if __name__ == '__main__':
    # Run the Flask application in debug mode.
    # Debug mode allows for automatic reloading on code changes
    # and provides a debugger in the browser.
    app.run(debug=True)


