from flask_smorest import Blueprint
from flask.views import MethodView
from flask import abort
from models import CategoryModel  # Ensure you have a corresponding model for categories
from schemas import CategorySchema  # Ensure you have a schema for categories
from db import db

blp = Blueprint("Categories", __name__, description="Operations on categories")

@blp.route("/category/<int:category_id>")
class Category(MethodView):
    @blp.response(200, CategorySchema)
    def get(self, category_id):
        category = CategoryModel.query.get_or_404(category_id)
        return category

    @blp.arguments(CategorySchema)
    @blp.response(201, CategorySchema)
    def post(self, category_data):
        category = CategoryModel(**category_data)
        db.session.add(category)
        db.session.commit()
        return category

    def delete(self, category_id):
        category = CategoryModel.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return {"message": "Category deleted"}
