import bcrypt

def generate_password_hash(password):
    """
    Generate a password hash from a password.

    Parameters:
    password : str
        The password to hash.

    Returns:
    str
        The hashed password.
    """

    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    
    return bcrypt.hashpw(password, salt).decode('utf-8')

def check_password_hash(hashed_password, raw_password):
    """
    Check if a password matches a hashed password.

    Parameters:
    hashed_password : str
        The hashed password to check against.

    password : str
        The password to check.

    Returns:
    bool
        True if the password matches the hashed password, False otherwise.
    """

    hashed_password = hashed_password.encode('utf-8')
    raw_password = raw_password.encode('utf-8')
    
    return bcrypt.checkpw(raw_password, hashed_password)

def is_authenticated(session):
    """
    Check if a user is authenticated.

    Parameters:
    session : dict
        The session object.

    Returns:
    bool
        True if the user is authenticated, False otherwise.
    """

    return 'user' in session and session['user'] is not None