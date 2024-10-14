class Role:
    ADMINISTRATOR = 1
    DIVISION_LEADER = 10
    DIVISION_USER = 11
    FINANCE_MANAGER = 20
    PROCUREMENT_MANAGER = 30
    SYSTEM = 99

    @staticmethod
    def get_roles():
        roles = []

        for attr in dir(Role):
            if not attr.startswith('__') and not callable(getattr(Role, attr)):
                roles.append({ "id": getattr(Role, attr), "text": get_role_text(getattr(Role, attr)) })
        
        return roles

RoleText = {
    Role.ADMINISTRATOR: 'Administrator',
    Role.DIVISION_LEADER: 'Division Leader',
    Role.DIVISION_USER: 'Division User',
    Role.FINANCE_MANAGER: 'Finance Manager',
    Role.PROCUREMENT_MANAGER: 'Procurement Manager',
    Role.SYSTEM: 'System'
}

class InsufficientPermissionError(Exception):
    """
    Exception raised when the user does not have enough permission to perform the operation.
    """
    def __init__(self, user, operation):
        if type(operation) is list:
            required = []
            for op in operation:
                required += get_required_role(op)
        else:
            required = get_required_role(operation)
        
        roles = ', '.join([get_role_text(role) for role in required])
        if "Unknown" in roles:
            roles = "n/a"
        else:
            # Remove duplicates
            roles = ', '.join(set(roles.split(', ')))
        
        if type(operation) is list:
            self.error = get_deny_string(operation[0])
        else:
            self.error = get_deny_string(operation)

        self.message = f'Your role of {get_role_text(user.role)} does not have enough permission to perform this operation. Required role: {roles}'
        
        super().__init__(self.message)

class NonExistentRuleError(Exception):
    """
    Exception raised when the operation does not have a rule defined.
    """
    def __init__(self, operation):
        self.message = f'The operation {operation} does not have a rule defined. Please contact the system administrator.'
        super().__init__(self.message)

permission_rules = {
    # Validated Item Related
    'item_validated/create': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'create validated item' },
    'item_validated/create_bulk': { 'required': [ Role.ADMINISTRATOR ], 'operation': 'create validated item in bulk' },
    'item_validated/update': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'update validated item' },
    'item_validated/update_bulk': { 'required': [ Role.ADMINISTRATOR ], 'operation': 'update validated item in bulk' },
    'item_validated/delete': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'delete validated item' },
    'item_validated/delete_bulk': { 'required': [ Role.ADMINISTRATOR ], 'operation': 'delete validated item in bulk' },
    # Non-Validated Item Related
    'item_nonvalidated/create': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'create non-validated item' },
    'item_nonvalidated/update': { 
        'required': [ Role.PROCUREMENT_MANAGER, Role.DIVISION_LEADER, Role.DIVISION_USER ], 
        'operation': 'update non-validated item'
    },
    'item_nonvalidated/delete': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'delete non-validated item' },
    'item_nonvalidated/validate': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'validate non-validated item' },
    # Order Related
    'order/administer': { 
        'required': [ Role.DIVISION_LEADER, Role.FINANCE_MANAGER, Role.PROCUREMENT_MANAGER ], 
        'operation': 'administer orders'
    },
    'order/create': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'create order' },
    'order/update': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'update order' },
    'order/delete': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'delete order' },
    'order/submit': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'submit order' },
    'order/approve_division': { 'required': [ Role.DIVISION_LEADER ], 'operation': 'approve or reject order (Division)' },
    'order/approve_finance': { 'required': [ Role.FINANCE_MANAGER ], 'operation': 'approve or reject order (Finance)' },
    'order/fulfill': { 'required': [ Role.PROCUREMENT_MANAGER ], 'operation': 'fulfill order' },
    'order/cancel': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER, Role.PROCUREMENT_MANAGER ], 'operation': 'cancel order' },
    # Order Item Related
    'orderitem/create': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'create order item' },
    'orderitem/update': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'update order item' },
    'orderitem/delete': { 'required': [ Role.DIVISION_LEADER, Role.DIVISION_USER ], 'operation': 'delete order item' },
    # User Related
    'user/administer': { 'required': [ Role.ADMINISTRATOR ], 'operation': 'administer users' },
}

def get_role_text(role):
    """
    Get the text representation of a role.
    
    :param role: The role to get the text representation of.
    :returns: The text representation of the role.
    """
    return RoleText.get(role, 'Unknown')

def check_permission(user, operation):
    """
    Check if the user has permission to perform the operation.
    
    :param user: The user object.
    :param operation: The operation to perform. Refer to the permission_rules dictionary in this module.
    :returns: True if the user has permission, raises an exception otherwise.
    """
    if user.role == Role.SYSTEM or user.role == Role.ADMINISTRATOR:
        return True

    if operation in permission_rules:
        required = permission_rules[operation]['required']

        if user.role in required:
            return True
        else:
            raise InsufficientPermissionError(user, operation)
    else:
        raise NonExistentRuleError(operation)
    
def get_required_role(operation):
    """
    Get the required role for the operation.
    
    :param operation: The operation to get the required role for. Refer to the permission_rules dictionary in this module.
    :returns: The required role for the operation.
    """
    return permission_rules.get(operation, {}).get('required', [])

def get_deny_string(operation):
    """
    Get the deny string for the operation.
    
    :param operation: The operation to get the deny string for. Refer to the pemission_rules dictionary in this module.
    :returns: The deny string for the operation.
    """
    operation_name = permission_rules.get(operation, {}).get('operation', 'Unknown')
    return f"Insufficient permission to {operation_name}"
  
def get_allowed_operations(user):
    """
    Get the operations that the user is allowed to perform.
    
    :param user: The user object.
    :returns: The list of operations that the user is allowed to perform.
    """
    operations = []
    
    for operation in permission_rules:
        roles = permission_rules[operation]['required']
        if user.role in roles or user.role == Role.SYSTEM or user.role == Role.ADMINISTRATOR:
            operations.append(operation)
    
    return operations