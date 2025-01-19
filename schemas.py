from marshmallow import Schema, fields

class PlainHerbSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    properties = fields.Str(required=True)

class PlainCategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class HerbSchema(PlainHerbSchema):
    category_id = fields.Int(required=True, load_only=True)
    category = fields.Nested(PlainCategorySchema(), dump_only=True)

class CategorySchema(PlainCategorySchema):
    herbs = fields.List(fields.Nested(PlainHerbSchema()), dump_only=True)
