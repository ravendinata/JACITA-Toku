from functools import wraps

from flask import jsonify, render_template, session, request

import helper.trail as trail
from app.models.user import User
from helper.role import InsufficientPermissionError

class HTTPStatus:
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

required_fields = {
    'order/create': [ 'period', 'division_id', 'created_by' ],
    'order/approve': [ 'username' ],
    'order/reject': [ 'username', 'reason' ],
    'item_validated/create': [ 'category_id', 'brand', 'name', 'base_price', 'qty_unit_id', 'created_by' ],
    'item_validated/create_bulk': [ 'category_id[]', 'brand[]', 'name[]', 'base_price[]', 'qty_unit_id[]', 'created_by' ],
    'item_nonvalidated/validate': [ 'validator' ],
    'item_nonvalidated/create': [ 'category_id', 'brand', 'name', 'base_price', 'created_by' ],
    'orderitem/create': [ 'item_id', 'quantity' ],
    'user/create': [ 'username', 'first_name', 'division_id', 'role', 'password' ],
    'auth/login': [ 'username', 'password' ],
}

modifiable_fields = {
    'order/update': [ 'period', 'division_id' ],
    'user/update': [ 'first_name', 'last_name', 'email', 'division_id' ],
    'item_validated/update': [ 'brand', 'name', 'variant', 'base_price', 'category_id', 'qty_unit_id', 'description' ],
    'item_nonvalidated/update': [ 'brand', 'name', 'variant', 'base_price', 'category_id', 'description' ],
    'orderitem/update': [ 'quantity', 'remarks' ],
}

def get_endpoint_fields(endpoint):
    """
    Get the required and modifiable fields for an endpoint.
    
    :param endpoint: The endpoint name to get the fields for. Refer to the required_fields and modifiable_fields dictionaries in this module.
    :returns: The list of required and/or modifiable fields for the endpoint.
    """
    return { 'required': required_fields.get(endpoint, []), 'modifiable': modifiable_fields.get(endpoint, []) }

def get_missing_fields(endpoint):
    """
    Get the missing required fields in the request.
    
    :param endpoint: The endpoint name to check the fields for. Refer to the required_fields and modifiable_fields dictionaries in this module.
    :returns: The list of missing required fields in the request.
    """
    if endpoint in required_fields:
        required = required_fields[endpoint]
        missing_required = [ field for field in required if field not in request.form ]
    else:
        missing_required = []

    return missing_required

def check_fields(endpoint):
    """
    [Decorator] Check if the required fields are present in the request.

    :param endpoint: The endpoint name to check the fields for. Refer to the required_fields and modifiable_fields dictionaries in this module.
    :returns: The decorated function if the required fields are present, an error response otherwise.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if endpoint in required_fields:
                required = required_fields[endpoint]
                if not all([ field in request.form for field in required ]):
                    return jsonify({ 'error': 'Required fields not provided',
                                     'fields': get_endpoint_fields(endpoint),
                                     'missing': get_missing_fields(endpoint) }), HTTPStatus.BAD_REQUEST
                
            if endpoint in modifiable_fields:
                modifiable = modifiable_fields[endpoint]
                if not any([ field in request.form for field in modifiable ]):
                    return jsonify({ 'error': 'No modifiable fields provided', 'available_fields': modifiable }), HTTPStatus.BAD_REQUEST

            return func(*args, **kwargs)
        return wrapper
    return decorator    

def check_page_permission(permission: str):
    """
    [Decorator] Check if the user has the permission to access the page.
    
    :param permission: The permission name to check. Refer to the role module for the list of permissions.
    :returns: The decorated function if the user has the permission, a redirect to the error page otherwise.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = User.query.get(session['user'])
            try:
                user.can_do(permission)
            except InsufficientPermissionError as e:
                return render_template('error/standard.html', title = "Forbidden", code = 403, message = e.message), HTTPStatus.FORBIDDEN
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_api_permission(permission: str):
    """
    [Decorator] Check if the user has the permission to access the API endpoint.

    :param permission: The permission name to check. Refer to the role module for the list of permissions.
    :returns: The decorated function if the user has the permission, an error response otherwise.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user = User.query.get(session['user'])
                if user.can_do(permission):
                    return func(*args, **kwargs)
            except InsufficientPermissionError as e:
                return jsonify({ 'error': e.error, 'details': e.message }), HTTPStatus.FORBIDDEN
            except KeyError as e:
                return jsonify({ 'error': 'Unauthorized' }), HTTPStatus.UNAUTHORIZED
        return wrapper
    return decorator

def check_page_permissions(permissions: list):
    """
    [Decorator] Check if the user has the permissions to access the page.

    :param permissions: The list of permission names to check. Refer to the role module for the list of permissions.
    :returns: The decorated function if the user has the permissions, an redirect to the error page otherwise.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = User.query.get(session['user'])
            try:
                for permission in permissions:
                    try:
                        if user.can_do(permission):
                            return func(*args, **kwargs)
                    except InsufficientPermissionError:
                        continue
                raise InsufficientPermissionError(user, permissions)
            except InsufficientPermissionError as e:
                return render_template('error/standard.html', title = "Forbidden", code = 403, message = e.message), HTTPStatus.FORBIDDEN
        return wrapper
    return decorator

def check_api_permissions(permissions: list):
    """
    [Decorator] Check if the user has the permissions to access the API endpoint.

    :param permissions: The list of permission names to check. Refer to the role module for the list of permissions.
    :returns: The decorated function if the user has the permissions, an error response otherwise.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user = User.query.get(session['user'])
                for permission in permissions:
                    try:
                        if user.can_do(permission):
                            return func(*args, **kwargs)
                    except InsufficientPermissionError:
                        continue
                raise InsufficientPermissionError(user, permissions)
            except InsufficientPermissionError as e:
                return jsonify({ 'error': e.error, 'details': e.message }), HTTPStatus.FORBIDDEN
            except KeyError as e:
                return jsonify({ 'error': 'Unauthorized' }), HTTPStatus.UNAUTHORIZED
        return wrapper
    return decorator

def inject_allowed_operations(func):
    """
    [Decorator] Inject the allowed operations of the user to the function.
    
    *Pre-requisite: The decorated function must have a user_operations parameter.*
    
    :param func: The function to decorate.
    :returns: The decorated function regardless of the pre-requisite. When the pre-requisite is not met, an error is logged but the function is still executed.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = User.query.get(session['user'])
        operations = user.allowed_operations()

        try:
            return func(*args, user_operations = operations, **kwargs)
        except TypeError:
            module = "endpoint.inject_allowed_operations"
            error_text = f"Pre-requisite not met: Function {func.__name__} does not have a user_operations parameter. Please add the parameter to the function to use this decorator."
            
            print(f"[{module}] {error_text}")
            trail.log_system_event(module, error_text)
            
            return func(*args, **kwargs)
    
    return wrapper