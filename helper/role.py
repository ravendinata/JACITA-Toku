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

required_role = {
    # Validated Item Related
    'item_validated/create': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/create_bulk': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/update': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/update_bulk': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/delete': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/delete_bulk': [ Role.ADMINISTRATOR ],
    # Non-Validated Item Related
    'item_nonvalidated/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'item_nonvalidated/update': [ Role.PROCUREMENT_MANAGER, Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'item_nonvalidated/delete': [ Role.PROCUREMENT_MANAGER ],
    'item_nonvalidated/validate': [ Role.PROCUREMENT_MANAGER ],
    # Order Related
    'order/administer': [ Role.DIVISION_LEADER, Role.FINANCE_MANAGER, Role.PROCUREMENT_MANAGER ],
    'order/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/update': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/delete': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/submit': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/approve_division': [ Role.DIVISION_LEADER ],
    'order/approve_finance': [Role.FINANCE_MANAGER ],
    'order/fulfill': [ Role.PROCUREMENT_MANAGER ],
    'order/cancel': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    # Order Item Related
    'orderitem/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'orderitem/update': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'orderitem/delete': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    # User Related
    'user/administer': [ Role.ADMINISTRATOR ]
}

deny_string = {
    # Validated Item Related
    'item_validated/create': 'Insufficient permission to create validated item',
    'item_validated/create_bulk': 'Insufficient permission to create validated item in bulk',
    'item_validated/update': 'Insufficient permission to update validated item',
    'item_validated/update_bulk': 'Insufficient permission to update validated item in bulk',
    'item_validated/delete': 'Insufficient permission to delete validated item',
    'item_validated/delete_bulk': 'Insufficient permission to delete validated item in bulk',
    # Non-Validated Item Related
    'item_nonvalidated/create': 'Insufficient permission to create non-validated item',
    'item_nonvalidated/update': 'Insufficient permission to update non-validated item',
    'item_nonvalidated/delete': 'Insufficient permission to delete non-validated item',
    'item_nonvalidated/validate': 'Insufficient permission to validate non-validated item',
    # Order Related
    'order/create': 'Insufficient permission to create order',
    'order/update': 'Insufficient permission to update order',
    'order/delete': 'Insufficient permission to delete order',
    'order/submit': 'Insufficient permission to submit order',
    'order/approve_division': 'Insufficient permission to approve or reject order (Division)',
    'order/approve_finance': 'Insufficient permission to approve or reject order (Finance)',
    'order/fulfill': 'Insufficient permission to fulfill order',
    'order/cancel': 'Insufficient permission to cancel order',
    # Order Item Related
    'orderitem/create': 'Insufficient permission to create order item',
    'orderitem/update': 'Insufficient permission to update order item',
    'orderitem/delete': 'Insufficient permission to delete order item'
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
    :param operation: The operation to perform. Refer to the required_role dictionary in this module.
    :returns: True if the user has permission, raises an exception otherwise.
    """
    if user.role == Role.SYSTEM or user.role == Role.ADMINISTRATOR:
        return True

    if operation in required_role:
        required = required_role[operation]

        if user.role in required:
            return True
        else:
            raise InsufficientPermissionError(user, operation)
    else:
        raise NonExistentRuleError(operation)
    
def get_required_role(operation):
    """
    Get the required role for the operation.
    
    :param operation: The operation to get the required role for. Refer to the required_role dictionary in this module.
    :returns: The required role for the operation.
    """
    return required_role.get(operation, [])

def get_deny_string(operation):
    """
    Get the deny string for the operation.
    
    :param operation: The operation to get the deny string for. Refer to the deny_string dictionary in this module.
    :returns: The deny string for the operation.
    """
    return deny_string.get(operation, 'Unknown operation')
  
def get_allowed_operations(user):
    """
    Get the operations that the user is allowed to perform.
    
    :param user: The user object.
    :returns: The list of operations that the user is allowed to perform.
    """
    operations = []
    
    for operation, roles in required_role.items():
        if user.role in roles or user.role == Role.SYSTEM or user.role == Role.ADMINISTRATOR:
            operations.append(operation)
    
    return operations