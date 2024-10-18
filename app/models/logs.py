from uuid import uuid4
from sqlalchemy import func

from app.extensions import db

class OrderRejectLog(db.Model):
    __tablename__ = 'order_reject_log'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, primary_key = True, default = str(uuid4()))
    order_id = db.Column(db.String, db.ForeignKey('toku.orders.id'), nullable = False)
    reason = db.Column(db.String, nullable = False)
    date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    user = db.Column(db.String, db.ForeignKey('toku.user.username'), nullable = False)
    level = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'<OrderRejectLog: {self.order_id} on {self.date} by {self.user} [Correlation ID: {self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
    def to_string(self):
        return f"{self.user} rejected {self.order_id} at {self.level} level on {self.date} with reason: {self.reason}"
    
class ItemPriceUpdateLog(db.Model):
    __tablename__ = 'item_price_update_log'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, primary_key = True)
    item_id = db.Column(db.String, db.ForeignKey('toku.items.id'), nullable = False)
    price_original = db.Column(db.Float, nullable = False)
    price_new = db.Column(db.Float, nullable = False)
    date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    user = db.Column(db.String, db.ForeignKey('toku.user.username'), nullable = False)

    def __repr__(self):
        return f'<ItemPriceUpdateLog: {self.item_id} on {self.date} by {self.user} [Correlation ID: {self.id}]>'
    
    def to_dict(self):
        data = { c.name: getattr(self, c.name) for c in self.__table__.columns }
        data['diff'] = self.diff
        data['percent_change'] = self.percent_change
        data['current_position'] = self.current_position
        return data
    
    def to_string(self):
        return f"{self.user} updated price of {self.item_id} from {self.price_original} to {self.price_new} on {self.date}"
    
    @property
    def diff(self):
        return self.price_new - self.price_original
    
    @property
    def percent_change(self):
        return (self.diff / self.price_original) * 100
    
    @property
    def current_position(self):
        return (self.price_new / self.price_original) * 100