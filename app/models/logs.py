from sqlalchemy import func

from app.extensions import db

class OrderRejectLog(db.Model):
    __tablename__ = 'order_reject_log'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, primary_key = True)
    order_id = db.Column(db.String, db.ForeignKey('toku.orders.id'), nullable = False)
    reason = db.Column(db.String, nullable = False)
    date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    user = db.Column(db.String, db.ForeignKey('toku.user.username'), nullable = False)
    level = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'<OrderRejectLog: {self.order_id} on {self.date} by {self.user} [Correlation ID: {self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }