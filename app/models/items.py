from app.extensions import db
from app.models.misc import Category, QuantityUnit

class Items(db.Model):
    __tablename__ = 'items'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, primary_key = True)
    category_id = db.Column(db.Integer, db.ForeignKey(Category.id), nullable = False, default = 0)
    brand = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    variant = db.Column(db.String, nullable = True)
    base_price = db.Column(db.Float, nullable = False)
    qty_unit_id = db.Column(db.Integer, db.ForeignKey(QuantityUnit.id), nullable = False, default = 0)

    def __repr__(self):
        return f'<Items: {self.brand} {self.name} {self.variant} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
class ViewItems(db.Model):
    __tablename__ = 'view_items'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, primary_key = True)
    category = db.Column(db.String, nullable = False, default = 0)
    brand = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    variant = db.Column(db.String, nullable = True)
    base_price = db.Column(db.Float, nullable = False)
    qty_unit = db.Column(db.String, nullable = False, default = 0)

    def __repr__(self):
        return f'<ViewItems: {self.brand} {self.name} {self.variant} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }