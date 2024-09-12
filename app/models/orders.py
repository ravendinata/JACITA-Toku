from sqlalchemy.sql import func

from app.extensions import db
from app.models.user import User, Division
from helper.status import OrderStatus, OrderStatusTransitionException, can_transition, get_order_status_text

class Orders(db.Model):
    __tablename__ = 'orders'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, nullable = False, primary_key = True)

    # Meta Attributes
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, db.ForeignKey(User.username), nullable = False)
    last_modification_date = db.Column(db.DateTime, nullable = False, default = db.func.current_timestamp(), onupdate = func.current_timestamp())

    # Order Attributes
    period = db.Column(db.String(7), nullable = False)
    division_id = db.Column(db.Integer, db.ForeignKey(Division.id), nullable = False, default = 0)
    status = db.Column(db.Integer, nullable = False, default = OrderStatus.PENDING)

    # Approval Attributes
    approval_division_date = db.Column(db.DateTime, nullable = True)
    approval_finance_date = db.Column(db.DateTime, nullable = True)
    approval_division_by = db.Column(db.String, db.ForeignKey(User.username), nullable = True)
    approval_finance_by = db.Column(db.String, db.ForeignKey(User.username), nullable = True)

    # Delivery Attributes
    fulfillment_date = db.Column(db.DateTime, nullable = True)

    def __repr__(self):
        return f'<Order: {self.id} @ {self.created_date} by {self.created_by}>'

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def is_approved(self, by):
        if by == 'division':
            return self.approval_division_date is not None
        elif by == 'finance':
            return self.approval_finance_date is not None
        else:
            return False
        
    def is_fulfilled(self):
        return self.fulfillment_date is not None
    
    def get_status(self):
        return OrderStatus(self.status)
    
    def clear_approval(self):
            self.approval_division_date = None
            self.approval_division_by = None
            self.approval_finance_date = None
            self.approval_finance_by = None
    
    def transition(self, new):
        if can_transition(self.status, new):
            self.status = new
        else:
            raise OrderStatusTransitionException(self.status, new)
    
    def submit(self):
        self.clear_approval()
        self.transition(OrderStatus.SUBMITTED)
    
    def cancel(self):
        self.transition(OrderStatus.CANCELLED)
        
    def approve(self, by, username):
        if by == 'division':
            self.transition(OrderStatus.DIVISION_APPROVED)
            self.approval_division_date = func.current_timestamp()
            self.approval_division_by = username
        elif by == 'finance':
            self.transition(OrderStatus.FINANCE_APPROVED)
            self.approval_finance_date = func.current_timestamp()
            self.approval_finance_by = username

    def reject(self, by, username):
        if by == 'division':
            self.transition(OrderStatus.DIVISION_REJECTED)
            self.approval_division_date = func.current_timestamp()
            self.approval_division_by = username
        elif by == 'finance':
            self.transition(OrderStatus.FINANCE_REJECTED)
            self.approval_finance_date = func.current_timestamp()
            self.approval_finance_by = username
    
    def fulfill(self):
        self.transition(OrderStatus.FULFILLED)
        self.fulfillment_date = func.current_timestamp()