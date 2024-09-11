from sqlalchemy.sql import func

from app.extensions import db
from app.models.user import User, Division
from helper.core import OrderStatus

class Orders(db.Model):
    __tablename__ = 'orders'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, nullable = False, primary_key = True)

    # Meta Attributes
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, db.ForeignKey(User.username), nullable = False)
    last_modification_date = db.Column(db.DateTime, nullable = False, default = db.func.current_timestamp(), on_update = func.current_timestamp())

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
    
    def submit(self):
        self.status = OrderStatus.SUBMITTED
    
    def cancel(self):
        self.status = OrderStatus.CANCELLED
    
    def approve(self, by, username):
        if by == 'division':
            self.approval_division_date = func.current_timestamp()
            self.approval_division_by = username
            self.status = OrderStatus.DIVISION_APPROVED
        elif by == 'finance':
            self.approval_finance_date = func.current_timestamp()
            self.approval_finance_by = username
            self.status = OrderStatus.FINANCE_APPROVED

    def reject(self, by, username):
        if by == 'division':
            self.approval_division_date = func.current_timestamp()
            self.approval_division_by = username
            self.status = OrderStatus.DIVISION_REJECTED
        elif by == 'finance':
            self.approval_finance_date = func.current_timestamp()
            self.approval_finance_by = username
            self.status = OrderStatus.FINANCE_REJECTED
    
    def fulfill(self):
        self.fulfillment_date = func.current_timestamp()
        self.status = OrderStatus.FULFILLED