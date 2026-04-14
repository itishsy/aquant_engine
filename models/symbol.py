from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, FloatField, DateTimeField
from datetime import datetime


class Symbol(BaseModel):
    code = CharField()  
    name = CharField()  
    price = FloatField()    # 最新价
    zdf = FloatField()      # 涨幅
    ltd = CharField()       # 最新交易日
    zsz = FloatField()      # 总市值
    tsz = FloatField()      # 流通市值
    hsl = FloatField()      # 换手率
    roe = FloatField()      # 动态市盈率
    remark = CharField()    # 标注
    created = DateTimeField()
    updated = DateTimeField()

    @staticmethod
    def upset(row):
        if row['市场类型'] not in ['沪A', '深A']:
            return
        code = row['代码']
        symbols = Symbol.select().where(Symbol.code == code)
        if len(symbols) > 0:
            symbol = symbols[0]
            symbol.price = row['最新价']
            symbol.zdf = row['涨跌幅']
            symbol.roe = row['动态市盈率']
            symbol.hsl = row['换手率']
            symbol.ltd = row['最新交易日']
            symbol.zsz = row['总市值']
            symbol.tsz = row['流通市值']
            print(f'update symbol: {symbol.name}（{code}）')
        else:
            symbol = Symbol()
            symbol.code = code
            symbol.name = row['名称']
            symbol.price = row['最新价']
            symbol.zdf = row['涨跌幅']
            symbol.roe = row['动态市盈率']
            symbol.hsl = row['换手率']
            symbol.ltd = row['最新交易日']
            symbol.zsz = row['总市值']
            symbol.tsz = row['流通市值']
            symbol.created = datetime.now()
            print(f'create symbol: {symbol.name}（{code}）')
        symbol.remark = ''
        symbol.updated = datetime.now()
        symbol.save()


if __name__ == '__main__':
    db.connect()
    db.create_tables([Symbol])


