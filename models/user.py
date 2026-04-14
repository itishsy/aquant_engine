from models.base import BaseModel, db
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask_peewee.db import CharField, BooleanField
from app import login_manager


# 用户
class User(UserMixin, BaseModel):
    username = CharField()  # 用户名
    password = CharField()  # 密码
    fullname = CharField()  # 真实性名
    email = CharField()  # 邮箱
    phone = CharField()  # 电话
    status = BooleanField(default=True)  # 生效失效标识

    def verify_password(self, raw_password):
        return check_password_hash(self.password, raw_password)


@login_manager.user_loader
def load_user(user_id):
    return User.get(User.id == int(user_id))


def generate_pwd(ori_password):
    print(generate_password_hash(ori_password))


if __name__ == '__main__':
    db.connect()
    db.create_tables([User])
