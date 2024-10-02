class OrderStatus:
    PENDING = 0             # Order is pending submission i.e. draft.
    SUBMITTED = 1           # Order has been submitted. Pending approval on division level.
    DIVISION_REJECTED = 2   # Order has been rejected on division level i.e. not approved. Submitter must revise and resubmit or cancel the order.
    DIVISION_APPROVED = 3   # Order has been approved on division level. Pending approval on finance level.
    FINANCE_REJECTED = 6    # Order has been rejected on finance level i.e. not approved. Division must revise and resubmit or cancel the order.
    FINANCE_APPROVED = 7    # Order has been approved on finance level. Pending fulfillment.
    FULFILLED = 10          # Order has been fulfilled by procurement. No further action required.
    CANCELLED = 99          # Order has been cancelled and is no longer valid.

class OrderStatusText:
    PENDING = 'Pending'
    SUBMITTED = 'Submitted'
    DIVISION_REJECTED = 'Division Rejected'
    DIVISION_APPROVED = 'Division Approved'
    FINANCE_REJECTED = 'Finance Rejected'
    FINANCE_APPROVED = 'Finance Approved'
    FULFILLED = 'Fulfilled'
    CANCELLED = 'Cancelled'

class OrderStatusTransitionError(Exception):
    """
    Exception raised when an invalid status transition is attempted.
    
    Attributes:
    message : str
        The error message.
    """
    def __init__(self, current, new):
        self.message = get_status_error_message(current, new)
        super().__init__(self.message)

required_transition_states = {
    OrderStatus.SUBMITTED: [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED],
    OrderStatus.DIVISION_REJECTED: [OrderStatus.SUBMITTED, OrderStatus.FINANCE_REJECTED],
    OrderStatus.DIVISION_APPROVED: [OrderStatus.SUBMITTED, OrderStatus.FINANCE_REJECTED],
    OrderStatus.FINANCE_REJECTED: [OrderStatus.DIVISION_APPROVED],
    OrderStatus.FINANCE_APPROVED: [OrderStatus.DIVISION_APPROVED],
    OrderStatus.FULFILLED: [OrderStatus.FINANCE_APPROVED],
    OrderStatus.CANCELLED: [OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_REJECTED]
}

def get_order_status_text(status):
    """
    Get the text representation of an order status.

    Parameters:
    status : int
        The order status.

    Returns:
    str
        The text representation of the order status.
    """
    return {
        OrderStatus.PENDING: OrderStatusText.PENDING,
        OrderStatus.SUBMITTED: OrderStatusText.SUBMITTED,
        OrderStatus.DIVISION_REJECTED: OrderStatusText.DIVISION_REJECTED,
        OrderStatus.DIVISION_APPROVED: OrderStatusText.DIVISION_APPROVED,
        OrderStatus.FINANCE_REJECTED: OrderStatusText.FINANCE_REJECTED,
        OrderStatus.FINANCE_APPROVED: OrderStatusText.FINANCE_APPROVED,
        OrderStatus.FULFILLED: OrderStatusText.FULFILLED,
        OrderStatus.CANCELLED: OrderStatusText.CANCELLED
    }.get(status, 'Unknown')

def can_transition(current, new):
    """
    Test if the new status is valid based on the current status.

    Parameters:
    current : int
        The current status of the order.

    new : int
        The new status of the order.

    Returns:
    bool
        True if the new status is valid, False otherwise.
    """
    return current in required_transition_states.get(new, [])

def get_status_error_message(current, new):
    """
    Get the error message for an invalid status transition.

    Parameters:
    current : int
        The current status of the order.

    new : int
        The new status of the order.

    Returns:
    str
        The error message for the status transition.
    """
    if current == new:
        return f"Invalid status transition: Order is already in {get_order_status_text(current)} state"
    else:
        return f"Invalid status transition: To enter {get_order_status_text(new)}, the order must be in one of the following states: {', '.join([get_order_status_text(status) for status in required_transition_states.get(new, [])])}"
