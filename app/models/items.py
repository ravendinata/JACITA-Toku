from sqlalchemy import func

from app.extensions import db
from app.models.misc import Category, QuantityUnit
from app.models.user import User

# =====================
# VALIDATED ITEM MODELS
# =====================

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
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, db.ForeignKey(User.username), nullable = False)
    description = db.Column(db.String, nullable = True)
    modification_date = db.Column(db.DateTime, nullable = True, onupdate = func.current_timestamp())
    modification_by = db.Column(db.String, db.ForeignKey(User.username), nullable = True)

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
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, db.ForeignKey(User.username), nullable = False)
    modification_date = db.Column(db.DateTime, nullable = True)
    modification_by = db.Column(db.String, db.ForeignKey(User.username), nullable = True)
    description = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<ViewItems: {self.brand} {self.name} {self.variant} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
# =========================
# NON-VALIDATED ITEM MODELS
# =========================

class NonvalItems(db.Model):
    __tablename__ = 'nonval_items'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, primary_key = True)
    category_id = db.Column(db.Integer, db.ForeignKey(Category.id), nullable = False, default = 99)
    brand = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    variant = db.Column(db.String, nullable = True)
    base_price = db.Column(db.Float, nullable = False)
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, db.ForeignKey(User.username), nullable = False)
    description = db.Column(db.String, nullable = True)
    modification_date = db.Column(db.DateTime, nullable = True, onupdate = func.current_timestamp())
    modification_by = db.Column(db.String, db.ForeignKey(User.username), nullable = True)

    def __repr__(self):
        return f'<NonvalItems: {self.brand} {self.name} {self.variant} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
class ViewNonvalItems(db.Model):
    __tablename__ = 'view_nonval_items'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.String, primary_key = True)
    category = db.Column(db.String, nullable = False, default = 99)
    brand = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    variant = db.Column(db.String, nullable = True)
    base_price = db.Column(db.Float, nullable = False)
    created_date = db.Column(db.DateTime, nullable = False, default = func.current_timestamp())
    created_by = db.Column(db.String, nullable = False)
    modification_date = db.Column(db.DateTime, nullable = True)
    modification_by = db.Column(db.String, nullable = True)
    description = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<ViewNonvalItems: {self.brand} {self.name} {self.variant} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }