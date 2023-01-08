from flask import redirect
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_restful import Resource, request
from werkzeug.security import check_password_hash

from api.services.user import UserService

from api.models.user import RefreshTokenModel, UserModel
from api.schemas.user import UserRegisterSchema, UserInformationSchema
from api.utils.confrimation import NotValidConfrimationException, check_user
from api.utils.response import (
    ACCOUNT_INFORMATION_NOT_MATCH,
    NOT_FOUND,
    EMAIL_DUPLICATED,
    EMAIL_NOT_CONFIRMED,
    REFRESH_TOKEN_ERROR,
    WELCOME_NEWBIE,
    FORBIDDEN,
    get_response,
)

register_schema = UserRegisterSchema()


class UserInformation(Resource):
    @classmethod
    def get(cls, user_id):
        """마이페이지 정보조회를 수행합니다."""
        user = UserModel.find_by_id(user_id)
        if not user:
            return get_response(False, NOT_FOUND.format("사용자"), 404)
        return UserService(user).get_info()

    @classmethod
    @jwt_required()
    def put(cls, user_id):
        """닉네임 변경을 수행합니다."""
        if get_jwt_identity() != user_id:
            return get_response(False, FORBIDDEN, 403)
        data = request.get_json()
        user = UserModel.find_by_id(user_id)
        return UserService(user).update_info(data)


class UserLogin(MethodView):
    """
    Access Token, Refresh Token 을 발급하고,
    Refresh Token Rotation 을 수행합니다.
    """

    @classmethod
    def post(cls):
        data = request.get_json()
        user = UserModel.find_by_email(data["email"])
        if not user:
            return get_response(False, NOT_FOUND.format("사용자"), 404)
        return UserService(user).login(data)
        # if user and check_password_hash(user.password, data["password"]):
        #     if user.is_active:
        #         # TOKEN 발급
        #
        #         access_token = create_username_access_token
        #         refresh_token = create_refresh_token(
        #             identity=user.id,
        #         )
        #         if user.token:
        #             token = user.token[0]
        #             token.refresh_token_value = refresh_token
        #             token.save_to_db()
        #         else:
        #             new_token = RefreshTokenModel(
        #                 user_id=user.id, refresh_token_value=refresh_token
        #             )
        #             new_token.save_to_db()
        #         return {
        #             "access_token": access_token,
        #             "refresh_token": refresh_token,
        #         }, 200
        #     return get_response(False, EMAIL_NOT_CONFIRMED, 400)
        # return get_response(False, ACCOUNT_INFORMATION_NOT_MATCH, 401)


class RefreshToken(MethodView):
    """
    리프레시 토큰으로 새로운 액세스 토큰을 발급합니다.
    """

    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        identity = get_jwt_identity()
        token = dict(request.headers)["Authorization"][7:]
        user = RefreshTokenModel.get_user_by_token(token)
        if not user:
            return get_response(False, REFRESH_TOKEN_ERROR, 401)
        # access token, refresh token 발급

        access_token = create_access_token(
            identity=user.id,
            fresh=True,
        )
        refresh_token = create_refresh_token(
            identity=user.id,
        )
        if user:
            token = user.token[0]
            token.refresh_token_value = refresh_token
            token.save_to_db()
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }, 200


class UserRegister(Resource):
    """회원가입을 처리합니다."""

    @classmethod
    def post(cls):
        data = request.get_json()
        return UserService().register(data)


class UserWithdraw(Resource):
    """
    회원탈퇴를 처리합니다.
    본인만 회원탈퇴를 진행할 수 있습니다.
    """

    @classmethod
    @jwt_required()
    def delete(cls):
        """
        클라이언트 -> email, password (로그인과 동일)
        """
        data = request.get_json()
        if not data.get("username"):
            return get_response(False, "잘못된 데이터 입력입니다.", 400)
        user = UserModel.find_by_id(get_jwt_identity())
        if user:
            if user.username == data["username"]:
                user.delete_from_db()
                return "", 204
            else:
                return get_response(False, "잘못된 접근입니다.", 400)
        else:
            return get_response(False, NOT_FOUND.format("사용자"), 400)


class UserConfirm(Resource):
    """
    이메일 인증을 처리합니다.
    """

    @classmethod
    def get(cls, user_id, hashed_email):
        user = UserModel.find_by_id(user_id)
        if not user:
            return redirect("https://money-for-rabbit.netlify.app/signup/fail")
        if user.is_active:
            return redirect("https://money-for-rabbit.netlify.app/")
        try:
            check_user(user.email, hashed_email)
        except NotValidConfrimationException as e:
            return redirect("https://money-for-rabbit.netlify.app/signup/fail")
        user.is_active = True
        user.save_to_db()
        return redirect("https://money-for-rabbit.netlify.app/signup/done")
