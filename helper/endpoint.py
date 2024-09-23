from functools import wraps

from flask import current_app, render_template, session

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
    'order/reject': [ 'username' ],
    'item/create': [ 'category_id', 'brand', 'name', 'base_price', 'qty_unit_id', 'created_by' ],
    'nonvalitem/create': [ 'category_id', 'brand', 'name', 'base_price', 'created_by' ],
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
    return required_fields.get(endpoint, []) + modifiable_fields.get(endpoint, [])

def check_fields(request, endpoint):
    if endpoint in required_fields:
        required = required_fields[endpoint]
        
        if not all([ field in request.form for field in required ]):
            return { 'pass': False, 'error': 'Missing required fields', 'available_fields': required }
        
    if endpoint in modifiable_fields:
        modifiable = modifiable_fields[endpoint]
        
        if not any([ field in request.form for field in modifiable ]):
            return { 'pass': False, 'error': 'No modifiable fields provided', 'available_fields': modifiable }

    return { 'pass': True }

def check_page_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = User.query.get(session['user'])
            try:
                user.can_do(permission)
            except InsufficientPermissionError as e:
                return render_template('error/standard.html', title = "Forbidden", code = 403, message = e.message, data = { 'username': session['user'] }), HTTPStatus.FORBIDDEN
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_page_permissions(permissions: list):
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
                return render_template('error/standard.html', title = "Forbidden", code = 403, message = e.message, data = { 'username': session['user'] }), HTTPStatus.FORBIDDEN
        return wrapper
    return decorator

def inject_allowed_operations(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = User.query.get(session['user'])
        operations = user.allowed_operations()
        
        return func(*args, user_operations = operations, **kwargs)
    
    return wrapper