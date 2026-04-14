# -*- coding: utf-8 -*-
from flask_peewee.db import MySQLDatabase, Model
import json
from common.config import config
import os

cfg = config[os.getenv('FLASK_CONFIG') or 'default']

db = MySQLDatabase(host=cfg.DB_HOST, user=cfg.DB_USER, passwd=cfg.DB_PASSWD, database=cfg.DB_DATABASE)


class BaseModel(Model):
    class Meta:
        database = db

    def __str__(self):
        r = {}
        for k in self._data.keys():
            try:
                r[k] = str(getattr(self, k))
            except:
                r[k] = json.dumps(getattr(self, k))
        # return str(r)
        return json.dumps(r, ensure_ascii=False)


if __name__ == '__main__':
    from models.signal import Signal
    from models.choice import Choice
    from models.ticket import Ticket
    from models.component import Component
    from models.candle import Trade

    db.connect()
    db.create_tables([Signal, Choice, Ticket, Component, Trade])
