from api.ma import ma
from marshmallow.fields import String
from marshmallow import validates_schema
from marshmallow.exceptions import ValidationError
from api.models.user import UserModel
from marshmallow import fields

fields.Field.default_error_messages["required"] = "해당 필드를 입력해 주세요."
fields.Field.default_error_messages[
    "validator_failed"
] = "해당 필드에 대한 검증이 실패했습니다."
fields.Field.default_error_messages["null"] = "해당 필드는 null 이 될 수 없습니다."


class UserRegisterSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        load_instance = True
        model = UserModel
        load_only = [
            "username",
            "email",
            "password",
        ]