import sys
sys.path.append("/Users/yo/Desktop/medicinal_herbs")
from db import db
from resources.category import blp as Category_Blueprint


class HerbModel(db.Model):
    __tablename__ = "herbs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    properties = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    category = db.relationship("CategoryModel", back_populates="herbs")

class CategoryModel(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    herbs = db.relationship("HerbModel", back_populates="category")
