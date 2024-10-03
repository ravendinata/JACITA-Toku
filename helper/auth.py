import bcrypt
from functools import wraps

from flask import session, redirect, request, session, url_for

def generate_password_hash(password):
    """
    Generate a password hash from a password.

    :params password: The password to hash.
    :returns: The hashed password.
    """

    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    
    return bcrypt.hashpw(password, salt).decode('utf-8')

def check_password_hash(hashed_password, raw_password):
    """
    Check if a password matches a hashed password.

    :param hashed_password: The hashed password.
    :param raw_password: The raw password to check.
    :returns: True if the password matches, False otherwise.
    """

    hashed_password = hashed_password.encode('utf-8')
    raw_password = raw_password.encode('utf-8')
    
    return bcrypt.checkpw(raw_password, hashed_password)

def is_authenticated():
    """
    Check if a user is authenticated.

    :param session: The session object to check.
    :returns: True if the user is authenticated, False otherwise.
    """

    return 'user' in session and session['user'] is not None

def check_login(func):
    """
    A decorator that checks if the user is logged in.

    :param func: The function to decorate.
    :returns: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            print('User not authenticated, redirecting to login page')
            session['next'] = request.url
            return redirect(url_for('web.page_login'))
        else:
            return func(*args, **kwargs)
        
    return wrapper