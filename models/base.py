# -*- coding: utf-8 -*-
import json
import os

from peewee import Model, MySQLDatabase

from common.config import config

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
    from models.choice import Choice
    from models.engine import Engine
    from models.review import Hot, Pan, Ztb
    from models.signal import Signal
    from models.symbol import Symbol

    db.connect()
    db.create_tables([Signal, Choice, Engine, Symbol, Pan, Hot, Ztb])
