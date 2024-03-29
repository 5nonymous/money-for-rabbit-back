import hashlib

from flask import current_app, render_template, request, url_for
from flask_login import UserMixin
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash

from api.db import db
from api.models.message import MessageModel


class UserModel(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=False)
    password = db.Column(db.String(102), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    date_joined = db.Column(db.DateTime, server_default=db.func.now())
    message_set = db.relationship(
        "MessageModel",
        backref="user",
        passive_deletes=True,
        lazy="dynamic",
        foreign_keys=MessageModel.user_id,
    )
    email_confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def create_user(self):
        self.password = generate_password_hash(self.password)
        self.save_to_db()
        return self

    def send_email(self):
        msg = Message(
            f"[Money For Rabbit] - {self.username} 님, 인증을 완료해 주세요.",
            sender="moneyforrabbit@5nonymous.tk",
            recipients=[self.email],
        )
        hashed_email = hashlib.sha256(self.email.encode()).hexdigest()
        msg.html = render_template(
            "email-confirmation-template.html",
            hashed_email=hashed_email,
            user_id=self.id,
        )
        with current_app.app_context():
            mail = Mail()
            mail.send(msg)

    @property
    def total_amount(self):
        """
        사용자가 받은 금액의 합계
        """
        money_list = [message.amount for message in self.message_set]
        return sum(money_list)

    @property
    def message_set_count(self):
        """
        사용자가 받은 메시지 개수
        """
        return len(self.message_set.all())

    @classmethod
    def find_by_username(cls, username):
        """
        데이터베이스에서 이름으로 특정 사용자 찾기
        """
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email):
        """
        데이터베이스에서 이메일로 특정 사용자 찾기
        """
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, id):
        """
        데이터베이스에서 id 로 특정 사용자 찾기
        """
        return cls.query.filter_by(id=id).first()

    def save_to_db(self):
        """
        사용자를 데이터베이스에 저장
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        사용자를 데이터베이스에서 삭제
        """
        db.session.delete(self)
        db.session.commit()

    def update_user_info(self, data):
        """
        사용자의 닉네임을 변경
        """
        self.username = data
        self.save_to_db()

    def __repr__(self):
        return f"<User Object : {self.username}>"


class RefreshTokenModel(db.Model):
    __tablename__ = "RefreshToken"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("User.id", ondelete="CASCADE"),
        nullable=True,
    )
    user = db.relationship(
        "UserModel",
        backref=db.backref("token", cascade="all, delete-orphan"),
    )
    refresh_token_value = db.Column(db.String(512), nullable=False, unique=True)

    def save_to_db(self):
        """
        토큰을 데이터베이스에 저장
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        토큰을 데이터베이스에서 삭제
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_user_by_token(cls, token):
        """
        리프레시 토큰 값으로 user 객체를 얻어옴
        """
        try:
            user_id = cls.query.filter_by(refresh_token_value=token).first().user_id
        except AttributeError:
            return None
        user = UserModel.find_by_id(id=user_id)
        return user
