class OrderStatus:
    PENDING = 0             # Order is pending submission i.e. draft.
    SUBMITTED = 1           # Order has been submitted. Pending approval on division level.
    DIVISION_REJECTED = 2   # Order has been rejected on division level i.e. not approved. Submitter must revise and resubmit or cancel the order.
    DIVISION_APPROVED = 3   # Order has been approved on division level. Pending approval on finance level.
    FINANCE_REJECTED = 6    # Order has been rejected on finance level i.e. not approved. Division must revise and resubmit or cancel the order.
    FINANCE_APPROVED = 7    # Order has been approved on finance level. Pending fulfillment.
    FULFILLED = 10          # Order has been fulfilled by procurement. No further action required.
    CANCELLED = 99          # Order has been cancelled and is no longer valid.

OrderStatusText = {
    OrderStatus.PENDING: 'Pending',
    OrderStatus.SUBMITTED: 'Submitted',
    OrderStatus.DIVISION_REJECTED: 'Division Rejected',
    OrderStatus.DIVISION_APPROVED: 'Division Approved',
    OrderStatus.FINANCE_REJECTED: 'Finance Rejected',
    OrderStatus.FINANCE_APPROVED: 'Finance Approved',
    OrderStatus.FULFILLED: 'Fulfilled',
    OrderStatus.CANCELLED: 'Cancelled'
}

class OrderStatusTransitionError(Exception):
    """
    Exception raised when an invalid status transition is attempted.
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
    OrderStatus.CANCELLED: [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_APPROVED]
}

def get_order_status_text(status):
    """
    Get the text representation of an order status.

    :param status: The status name to get the text representation of.
    :returns: The text representation of the status.
    """
    return OrderStatusText.get(status, 'Unknown')

def can_transition(current, new):
    """
    Test if the new status is valid based on the current status.

    :param current: The current status of the order.
    :param new: The new status of the order.
    :returns: True if the transition is valid, False otherwise.
    """
    return current in required_transition_states.get(new, [])

def get_status_error_message(current, new):
    """
    Get the error message for an invalid status transition.

    :param current: The current status of the order.
    :param new: The new status of the order.
    :returns: The error message for the invalid status transition
    """
    if current == new:
        return f"Invalid status transition: Order is already in {get_order_status_text(current)} state"
    else:
        return f"Invalid status transition: To enter {get_order_status_text(new)}, the order must be in one of the following states: {', '.join([get_order_status_text(status) for status in required_transition_states.get(new, [])])}"
