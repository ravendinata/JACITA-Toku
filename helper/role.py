class Role:
    ADMINISTRATOR = 1
    DIVISION_LEADER = 10
    DIVISION_USER = 11
    FINANCE_MANAGER = 20
    PROCUREMENT_MANAGER = 30
    SYSTEM = 99

class RoleText:
    ADMINISTRATOR = 'Administrator'
    DIVISION_LEADER = 'Division Leader'
    DIVISION_USER = 'Division User'
    FINANCE_MANAGER = 'Finance Manager'
    PROCUREMENT_MANAGER = 'Procurement Manager'
    SYSTEM = 'System'

class InsufficientPermissionError(Exception):
    def __init__(self, user, required):
        roles = ', '.join([get_role_text(role) for role in required])
        if "Unknown" in roles:
            roles = "n/a"
        self.message = f'Your role of {get_role_text(user.role)} does not have enough permission to perform this operation. Required role: {roles}'
        super().__init__(self.message)

class NonExistentRuleError(Exception):
    def __init__(self, operation):
        self.message = f'The operation {operation} does not have a rule defined. Please contact the system administrator.'
        super().__init__(self.message)

required_role = {
    # Validated Item Related
    'item_validated/create': [ Role.PROCUREMENT_MANAGER ],
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
    'order/approve_division': [ Role.DIVISION_LEADER ],
    'order/reject_division': [ Role.DIVISION_LEADER ],
    'order/approve_finance': [Role.FINANCE_MANAGER ],
    'order/reject_finance': [ Role.FINANCE_MANAGER ],
    'order/fulfill': [ Role.PROCUREMENT_MANAGER ],
    'order/cancel': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    # Order Item Related
    'orderitem/create': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'orderitem/update': [ Role.DIVISION_LEADER, Role.DIVISION_USER ],
    'orderitem/delete': [ Role.DIVISION_LEADER, Role.DIVISION_USER ]
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
            raise InsufficientPermissionError(user, required)
    else:
        raise NonExistentRuleError(operation)
  
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