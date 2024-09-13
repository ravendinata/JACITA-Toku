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
    'user/create': [ 'username', 'first_name', 'division_id', 'role', 'password' ],
    'orderitem/create': [ 'item_id', 'quantity' ],
}

modifiable_fields = {
    'order/update': [ 'period', 'division_id' ],
    'user/update': [ 'first_name', 'last_name', 'email', 'division_id' ],
    'item_validated/update': [ 'brand', 'name', 'variant', 'base_price', 'category_id', 'qty_unit_id' ],
    'item_nonvalidated/update': [ 'brand', 'name', 'variant', 'base_price', 'category_id' ],
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