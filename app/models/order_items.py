from app.extensions import db
from app.models.orders import Orders
from app.models.items import Items, NonvalItems

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = { 'schema': 'toku' }

    order_id = db.Column(db.String, db.ForeignKey(Orders.id), nullable = False, primary_key = True)
    item_id = db.Column(db.String, db.ForeignKey(Items.id), nullable = False, primary_key = True)
    quantity = db.Column(db.Integer, nullable = False)
    remarks = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<OrderItem: Item {self.item_id} on Order {self.order_id}>'

    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
class OrderNonvalItems(db.Model):
    __tablename__ = 'order_nonval_items'
    __table_args__ = { 'schema': 'toku' }

    order_id = db.Column(db.String, db.ForeignKey(Orders.id), nullable = False, primary_key = True)
    item_id = db.Column(db.String, db.ForeignKey(NonvalItems.id), nullable = False, primary_key = True)
    quantity = db.Column(db.Integer, nullable = False)
    remarks = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<OrderItem: Non-Validated Item {self.item_id} on Order {self.order_id}>'

    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }