from itertools import chain

from sqlalchemy.sql import func

from app.extensions import db
from app.models.user import User, Division
from app.models.items import Items, NonvalItems
from app.models.order_items import OrderItems, OrderNonvalItems
from helper.status import OrderStatus, OrderStatusTransitionError, can_transition, get_order_status_text

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
        data = { c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'status' and c.name != 'division_id' }
        data['status'] = { 'code': self.status, 'text': get_order_status_text(self.status) }
        data['division'] = { 'id': self.division_id, 'name': Division.query.get(self.division_id).full_name }
        # Dates in ISO 8601 format
        data['created_date'] = self.created_date.isoformat()
        data['last_modification_date'] = self.last_modification_date.isoformat()
        return data
    
    def __fix_data(self):
        if self.status != OrderStatus.FULFILLED:
            self.fulfillment_date = None

        if self.status < OrderStatus.FINANCE_APPROVED:
            self.approval_finance_date = None
            self.approval_finance_by = None

        if self.status < OrderStatus.DIVISION_APPROVED:
            self.approval_division_date = None
            self.approval_division_by = None

    def is_approved(self, by):
        if by == 'division':
            return self.approval_division_date is not None and self.status == OrderStatus.DIVISION_APPROVED
        elif by == 'finance':
            return self.approval_finance_date is not None and self.status == OrderStatus.FINANCE_APPROVED
        else:
            return False
        
    def is_fulfilled(self):
        return self.fulfillment_date is not None and self.status == OrderStatus.FULFILLED
    
    def get_status(self):
        return get_order_status_text(self.status)
    
    def get_division(self):
        return Division.query.get(self.division_id).full_name
    
    # Status Transition Methods
    def transition(self, new):
        if can_transition(self.status, new):
            self.status = new
            self.__fix_data()
        else:
            raise OrderStatusTransitionError(self.status, new)
    
    def submit(self):
        self.transition(OrderStatus.SUBMITTED)
    
    def cancel(self):
        self.transition(OrderStatus.CANCELLED)
        
    def approve(self, by, username):
        if by == 'division':
            self.transition(OrderStatus.DIVISION_APPROVED)
            self.approval_division_date = func.current_timestamp()
            self.approval_division_by = username
            self.approval_finance_by = None
            self.approval_finance_date = None
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
            self.approval_division_by = None
            self.approval_division_date = None
    
    def fulfill(self):
        self.transition(OrderStatus.FULFILLED)
        self.fulfillment_date = func.current_timestamp()

    # Extra Properties and Methods
    @property
    def total_price(self):
        return self._get_total_price()
    
    @property
    def item_count(self):
        return sum([ item.quantity for item in self.items ])
    
    @property
    def sku_count(self):
        return len(self.items)
    
    @property
    def items(self):
        return list(chain(self._get_items(), self._get_nonval_items()))
    
    @property
    def created_date_iso(self):
        return self.created_date.isoformat()
    
    @property
    def last_modification_date_iso(self):
        return self.last_modification_date.isoformat()
    
    @property
    def approval_division_date_iso(self):
        return self.approval_division_date.isoformat() if self.approval_division_date else None
    
    @property
    def approval_finance_date_iso(self):
        return self.approval_finance_date.isoformat() if self.approval_finance_date else None
    
    @property
    def fulfillment_date_iso(self):
        return self.fulfillment_date.isoformat() if self.fulfillment_date else None
    
    def _get_items(self):
        return OrderItems.query.filter_by(order_id = self.id).all()
    
    def _get_nonval_items(self):
        return OrderNonvalItems.query.filter_by(order_id = self.id).all()
    
    def _get_total_price(self):
        total = 0
        for order_item in self.items:
            item = Items.query.get(order_item.item_id) or NonvalItems.query.get(order_item.item_id)
            total += item.base_price * float(order_item.quantity)
        return total