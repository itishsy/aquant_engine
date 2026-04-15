from models.base import BaseModel, db
from peewee import CharField, DateTimeField, IntegerField
from datetime import datetime, timedelta


# 盘面
class Pan(BaseModel):
    class Meta:
        table_name = 'rev_pan'

    date = CharField()  # 日期
    cjl = CharField()   # 1.成交量
    zs = CharField()    # 2.指数
    szl = CharField()   # 3.上涨率
    zts = CharField()   # 4.涨停数
    dts = CharField()   # 5.跌停数
    fbl = CharField()   # 6.封板率
    zgb = CharField()   # 7.最高板

    review = CharField(null=True)    # 8.每日收评
    concept = CharField(null=True)   # 9.最强题材
    chance = CharField(null=True)    # 10.今日机会
    tuyere = CharField(null=True)    # 11.今日风口
    topic = CharField(null=True)     # 12.今日话题 (同花顺)
    subject = CharField(null=True)   # 13.热门题材 (同花顺)
    fund = CharField(null=True)      # 14.资金动向
    latent = CharField()    # 15.短期潜伏

    notify = IntegerField(null=True)  # 通知 0 待通知， 1 已通知
    created = DateTimeField()


# 人气股
class Hot(BaseModel):
    class Meta:
        table_name = 'rev_hot'

    date = CharField()  # 日期
    code = CharField()  # 票据
    name = CharField()  # 名称
    price = CharField()  # 价格
    change = CharField()  # 幅度
    reason = CharField()  # 上榜理由
    score = IntegerField()  # 排名得分
    rank1 = IntegerField(null=True)  # 财联社cls
    rank2 = IntegerField(null=True)  # 同花顺ths
    rank3 = IntegerField(null=True)  # 淘股吧tgb
    comment = CharField(null=True)   # 备注
    created = DateTimeField()

    @staticmethod
    def find_hot_codes(days=35):
        limit_day = datetime.now() - timedelta(days=days)
        hots = Hot.select().where(Hot.date > limit_day).group_by(Hot.code)
        return [hot.code for hot in hots]


# 涨停板
class Ztb(BaseModel):
    class Meta:
        table_name = 'rev_ztb'

    date = CharField()  # 日期
    code = CharField()  # 票据
    name = CharField()  # 名称
    change = CharField()  # 幅度
    time = CharField()  # 时间
    price = CharField()  # 价格
    strong = CharField(null=True)  # 强度
    reason = CharField(null=True)   # 原因
    bk1 = CharField(null=True)   # 板块-财联社
    comment1 = CharField(null=True)   # 原因备注-财联社
    bk2 = CharField(null=True)   # 板块-韭研社
    comment2 = CharField(null=True)   # 原因备注-韭研社
    created = DateTimeField()


if __name__ == '__main__':
    db.connect()
    db.create_tables([Pan, Hot, Ztb])
    # Pan.select()
