from models.base import BaseModel, db
from models.signal import Signal
from peewee import AutoField, CharField, DateTimeField
from datetime import datetime


# 入选池
class Choice(BaseModel):
    id = AutoField()
    code = CharField()  # 编码
    name = CharField()  # 名称
    searcher = CharField()
    watcher = CharField()
    created = DateTimeField()
    updated = DateTimeField()


if __name__ == '__main__':
    db.connect()
    db.create_tables([Choice])
