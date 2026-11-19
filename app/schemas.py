
from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )


class CategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )


class RecordSchema(Schema):
    user_id = fields.Integer(required=True)
    category_id = fields.Integer(required=True)
    amount = fields.Decimal(
        required=True,
        as_string=True,
        validate=validate.Range(min=0.01),
    )


class DepositSchema(Schema):
    amount = fields.Decimal(
        required=True,
        as_string=True,
        validate=validate.Range(min=0.01),
    )
