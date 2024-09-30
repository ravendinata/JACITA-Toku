class Role:
    ADMINISTRATOR = 1
    DIVISION_LEADER = 10
    DIVISION_USER = 11
    FINANCE_MANAGER = 20
    PROCUREMENT_MANAGER = 30
    SYSTEM = 99

    def get_roles():
        return [
            { 'id': Role.ADMINISTRATOR, 'text': RoleText.ADMINISTRATOR },
            { 'id': Role.DIVISION_LEADER, 'text': RoleText.DIVISION_LEADER },
            { 'id': Role.DIVISION_USER, 'text': RoleText.DIVISION_USER },
            { 'id': Role.FINANCE_MANAGER, 'text': RoleText.FINANCE_MANAGER },
            { 'id': Role.PROCUREMENT_MANAGER, 'text': RoleText.PROCUREMENT_MANAGER },
            { 'id': Role.SYSTEM, 'text': RoleText.SYSTEM }
        ]

class RoleText:
    ADMINISTRATOR = 'Administrator'
    DIVISION_LEADER = 'Division Leader'
    DIVISION_USER = 'Division User'
    FINANCE_MANAGER = 'Finance Manager'
    PROCUREMENT_MANAGER = 'Procurement Manager'
    SYSTEM = 'System'

class InsufficientPermissionError(Exception):
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
    def __init__(self, operation):
        self.message = f'The operation {operation} does not have a rule defined. Please contact the system administrator.'
        super().__init__(self.message)

required_role = {
    # Validated Item Related
    'item_validated/create': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/create_bulk': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/update': [ Role.PROCUREMENT_MANAGER ],
    'item_validated/delete': [ Role.PROCUREMENT_MANAGER ],
    # Non-Validated Item Related
    'item_nonvalidated/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'item_nonvalidated/update': [ Role.PROCUREMENT_MANAGER, Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'item_nonvalidated/delete': [ Role.PROCUREMENT_MANAGER ],
    'item_nonvalidated/validate': [ Role.PROCUREMENT_MANAGER ],
    # Order Related
    'order/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/update': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/delete': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'order/administer': [ Role.DIVISION_LEADER, Role.FINANCE_MANAGER, Role.PROCUREMENT_MANAGER ],
    'order/approve_division': [ Role.DIVISION_LEADER ],
    'order/reject_division': [ Role.DIVISION_LEADER ],
    'order/approve_finance': [Role.FINANCE_MANAGER ],
    'order/reject_finance': [ Role.FINANCE_MANAGER ],
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
    'item_validated/create': 'Insufficient permission to create validated item',
    'item_validated/update': 'Insufficient permission to update validated item',
    'item_validated/delete': 'Insufficient permission to delete validated item',
    'item_nonvalidated/create': 'Insufficient permission to create non-validated item',
    'item_nonvalidated/update': 'Insufficient permission to update non-validated item',
    'item_nonvalidated/delete': 'Insufficient permission to delete non-validated item',
    'item_nonvalidated/validate': 'Insufficient permission to validate non-validated item',
    'order/create': 'Insufficient permission to create order',
    'order/update': 'Insufficient permission to update order',
    'order/delete': 'Insufficient permission to delete order',
    'order/approve_division': 'Insufficient permission to approve or reject order (Division)',
    'order/approve_finance': 'Insufficient permission to approve or reject order (Finance)',
    'order/fulfill': 'Insufficient permission to fulfill order',
    'order/cancel': 'Insufficient permission to cancel order',
    'orderitem/create': 'Insufficient permission to create order item',
    'orderitem/update': 'Insufficient permission to update order item',
    'orderitem/delete': 'Insufficient permission to delete order item'
}

def get_role_text(role):
    """
    Get the text representation of a role.
    
    Parameters:
    role : int
        The role code/id.
        
    Returns:
    str
        The text representation of the role.
    """
    return {
        Role.ADMINISTRATOR: RoleText.ADMINISTRATOR,
        Role.DIVISION_LEADER: RoleText.DIVISION_LEADER,
        Role.DIVISION_USER: RoleText.DIVISION_USER,
        Role.FINANCE_MANAGER: RoleText.FINANCE_MANAGER,
        Role.PROCUREMENT_MANAGER: RoleText.PROCUREMENT_MANAGER,
        Role.SYSTEM: RoleText.SYSTEM
    }.get(role, 'Unknown')

def check_permission(user, operation):
    """
    Check if the user has permission to perform the operation.
    
    Parameters:
    user : User
        The user object.
        
    operation : str
        The operation to be performed.
        
    Returns:
    bool
        True if the user has permission, False otherwise
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
    
    Parameters:
    operation : str
        The operation to be performed.
        
    Returns:
    list
        The list of roles required to perform the operation.
    """
    return required_role.get(operation, [])

def get_deny_string(operation):
    """
    Get the deny string for the operation.
    
    Parameters:
    operation : str
        The operation to be performed.
        
    Returns:
    str
        The deny string for the operation.
    """
    return deny_string.get(operation, 'Unknown operation')
  
def get_allowed_operations(user):
    """
    Get the operations that the user is allowed to perform.
    
    Parameters:
    user : User
        The user object.

    Returns:
    list
        The list of operations that the user is allowed to perform.
    """

    operations = []
    
    for operation, roles in required_role.items():
        if user.role in roles or user.role == Role.SYSTEM or user.role == Role.ADMINISTRATOR:
            operations.append(operation)
    
    return operations