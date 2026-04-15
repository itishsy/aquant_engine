from models.base import BaseModel
from peewee import CharField, DateTimeField, FloatField, IntegerField
import pandas as pd
import numpy as np
from datetime import datetime


class Candle(BaseModel):

    class Meta:
        table_name = 'candle'

    def __init__(self, code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code
        self.freq = 101

    code = CharField()
    dt = CharField()
    close = FloatField()
    open = FloatField()
    high = FloatField()
    low = FloatField()
    volume = IntegerField()
    chg = FloatField()
    percent = FloatField()
    turn = FloatField()
    turnover = FloatField()
    created = DateTimeField()

    # ma5 = None
    # ma10 = None
    # ma20 = None
    # ema12 = None
    # ema26 = None
    # dea9 = None
    # mark = 0

    # def diff(self):
    #     return round(self.ema12 - self.ema26, 4)
    #
    # def bar(self):
    #     return round(self.diff() - self.dea9, 4)

    @staticmethod
    def new(code, freq=101):
        if freq == 101:
            return Candle(code)
        else:
            return CandlePlus(code, freq)
        # if freq == 30:
        #     return Candle30(code)
        # elif freq == 60:
        #     return Candle60(code)
        # elif freq == 120:
        #     return Candle120(code)
        # elif freq == 15:
        #     return Candle15(code)
        # elif freq == 5:
        #     return Candle5(code)
        # return Candle(code)

    @staticmethod
    def latest(code, freq=101):
        if freq == 101:
            if Candle(code).exists():
                return Candle.select().where(Candle.code == code).order_by(Candle.dt.desc()).limit(1).get()
        elif CandlePlus(code, freq).exists():
            return CandlePlus.select().where(CandlePlus.code == code, CandlePlus.freq == freq).order_by(CandlePlus.dt.desc()).limit(1).get()

        # if freq == 30:
        #     if Candle30(code).exists():
        #         fields = [Candle30.code, Candle30.dt, Candle30.close, Candle30.open, Candle30.high, Candle30.low]
        #         return Candle30.select(*fields).where(Candle30.code == code).order_by(Candle30.dt.desc()).limit(1).get()
        # elif freq == 60:
        #     if Candle60(code).exists():
        #         fields = [Candle60.code, Candle60.dt, Candle60.close, Candle60.open, Candle60.high, Candle60.low]
        #         return Candle60.select(*fields).where(Candle60.code == code).order_by(Candle60.dt.desc()).limit(1).get()
        # elif freq == 120:
        #     if Candle120(code).exists():
        #         fields = [Candle120.code, Candle120.dt, Candle120.close, Candle120.open, Candle120.high, Candle120.low]
        #         return Candle120.select(*fields).where(Candle120.code == code).order_by(Candle120.dt.desc()).limit(1).get()
        # elif freq == 15:
        #     if Candle15(code).exists():
        #         fields = [Candle15.code, Candle15.dt, Candle15.close, Candle15.open, Candle15.high, Candle15.low]
        #         return Candle15.select(*fields).where(Candle15.code == code).order_by(Candle15.dt.desc()).limit(1).get()
        # elif freq == 5:
        #     if Candle5(code).exists():
        #         fields = [Candle5.code, Candle5.dt, Candle5.close, Candle5.open, Candle5.high, Candle5.low]
        #         return Candle5.select(*fields).where(Candle5.code == code).order_by(Candle5.dt.desc()).limit(1).get()
        # else:
        #     if Candle(code).exists():
        #         return Candle.select().where(Candle.code == code).order_by(Candle.dt.desc()).limit(1).get()

    def exists(self):
        conditions = [Candle.code == self.code]
        if self.dt is not None:
            conditions.append(Candle.dt == self.dt)
        return Candle.select().where(*conditions).exists()
        # if self.freq == 30:
        #     conditions = [Candle30.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle30.dt == self.dt)
        #     return Candle30.select().where(*conditions).exists()
        # elif self.freq == 60:
        #     conditions = [Candle60.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle60.dt == self.dt)
        #     return Candle60.select().where(*conditions).exists()
        # elif self.freq == 120:
        #     conditions = [Candle120.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle120.dt == self.dt)
        #     return Candle120.select().where(*conditions).exists()
        # elif self.freq == 15:
        #     conditions = [Candle15.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle15.dt == self.dt)
        #     return Candle15.select().where(*conditions).exists()
        # elif self.freq == 5:
        #     conditions = [Candle5.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle5.dt == self.dt)
        #     return Candle5.select().where(*conditions).exists()
        # else:
        #     conditions = [Candle.code == self.code]
        #     if self.dt is not None:
        #         conditions.append(Candle.dt == self.dt)
        #     return Candle.select().where(*conditions).exists()

    @staticmethod
    def find(code, freq=101, begin=None, end=None, limit=150, ma=False):
        lim = max(160, limit + 60)
        if freq == 101:
            conditions = [Candle.code == code]
            if begin is not None:
                conditions.append(Candle.dt >= begin)
            if end is not None:
                conditions.append(Candle.dt <= end)
            query = Candle.select().where(*conditions).order_by(Candle.dt.desc()).limit(lim)
        else:
            conditions = [CandlePlus.code == code, CandlePlus.freq == freq]
            if begin is not None:
                conditions.append(CandlePlus.dt >= begin)
            if end is not None:
                conditions.append(CandlePlus.dt <= end)
            query = CandlePlus.select().where(*conditions).order_by(CandlePlus.dt.desc()).limit(lim)
        # if freq == 5:
        #     fields = [Candle5.code, Candle5.dt, Candle5.close, Candle5.open, Candle5.high, Candle5.low]
        #     conditions = [Candle5.code == code]
        #     if begin is not None:
        #         conditions.append(Candle5.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle5.dt <= end)
        #     query = Candle5.select(*fields).where(*conditions).order_by(Candle5.dt.desc()).limit(lim)
        # elif freq == 15:
        #     fields = [Candle15.code, Candle15.dt, Candle15.close, Candle15.open, Candle15.high, Candle15.low]
        #     conditions = [Candle15.code == code]
        #     if begin is not None:
        #         conditions.append(Candle15.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle15.dt <= end)
        #     query = Candle15.select(*fields).where(*conditions).order_by(Candle15.dt.desc()).limit(lim)
        # elif freq == 30:
        #     fields = [Candle30.code, Candle30.dt, Candle30.close, Candle30.open, Candle30.high, Candle30.low]
        #     conditions = [Candle30.code == code]
        #     if begin is not None:
        #         conditions.append(Candle30.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle30.dt <= end)
        #     query = Candle30.select(*fields).where(*conditions).order_by(Candle30.dt.desc()).limit(lim)
        # elif freq == 60:
        #     fields = [Candle60.code, Candle60.dt, Candle60.close, Candle60.open, Candle60.high, Candle60.low]
        #     conditions = [Candle60.code == code]
        #     if begin is not None:
        #         conditions.append(Candle60.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle60.dt <= end)
        #     query = Candle60.select(*fields).where(*conditions).order_by(Candle60.dt.desc()).limit(lim)
        # elif freq == 120:
        #     fields = [Candle120.code, Candle120.dt, Candle120.close, Candle120.open, Candle120.high, Candle120.low]
        #     conditions = [Candle120.code == code]
        #     if begin is not None:
        #         conditions.append(Candle120.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle120.dt <= end)
        #     query = Candle120.select(*fields).where(*conditions).order_by(Candle120.dt.desc()).limit(lim)
        # else:
        #     conditions = [Candle.code == code]
        #     if begin is not None:
        #         conditions.append(Candle.dt >= begin)
        #     if end is not None:
        #         conditions.append(Candle.dt <= end)
        #     query = Candle.select().where(*conditions).order_by(Candle.dt.desc()).limit(lim)
        cds = list(query)[::-1]
        if ma:
            close_vals = [round(c.close, 2) for c in cds]
            df = pd.DataFrame({'close': close_vals})
            df['ma5'] = df['close'].rolling(5).mean()  # MA5（至少1个点即可计算）
            df['ma10'] = df['close'].rolling(10).mean()  # MA10（需满10个数据）
            df['ma20'] = df['close'].rolling(20).mean()  # MA20（需满20个数据）
            df['ma60'] = df['close'].rolling(60).mean()  # MA20（需满20个数据）
            for i, c in enumerate(cds):
                c.ma5 = round(float(df['ma5'].iloc[i]), 4)
                c.ma10 = round(float(df['ma10'].iloc[i]), 4)
                c.ma20 = round(float(df['ma20'].iloc[i]), 4)
                c.ma60 = round(float(df['ma60'].iloc[i]), 4)
        return cds


class CandlePlus(BaseModel):

    class Meta:
        table_name = 'candle_plus'

    def __init__(self, code, freq, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code
        self.freq = freq

    code = CharField()
    freq = CharField()
    dt = CharField()
    close = FloatField()
    open = FloatField()
    high = FloatField()
    low = FloatField()

    def exists(self):
        conditions = [CandlePlus.code == self.code, CandlePlus.freq == self.freq]
        if self.dt is not None:
            conditions.append(CandlePlus.dt == self.dt)
        return CandlePlus.select().where(*conditions).exists()


# class Candle15(Candle):
#     class Meta:
#         table_name = 'candle_15'
#
#     def __init__(self, code, *args, **kwargs):
#         super().__init__(code, *args, **kwargs)
#         self.freq = 15
#
#
# class Candle5(Candle):
#     class Meta:
#         table_name = 'candle_5'
#
#     def __init__(self, code, *args, **kwargs):
#         super().__init__(code, *args, **kwargs)
#         self.freq = 5
#
#
# class Candle30(Candle):
#     class Meta:
#         table_name = 'candle_30'
#
#     def __init__(self, code, *args, **kwargs):
#         super().__init__(code, *args, **kwargs)
#         self.freq = 30
#
#
# class Candle60(Candle):
#     class Meta:
#         table_name = 'candle_60'
#
#     def __init__(self, code, *args, **kwargs):
#         super().__init__(code, *args, **kwargs)
#         self.freq = 60
#
#
# class Candle120(Candle):
#     class Meta:
#         table_name = 'candle_120'
#
#     def __init__(self, code, *args, **kwargs):
#         super().__init__(code, *args, **kwargs)
#         self.freq = 120


# def divergence(candles, bottom=True):
#     size = len(candles)
#     if size < 35:
#         return candles
#     # calculate_macd(candles)
#
#     # close_vals = [round(c.close, 2) for c in candles]
#     # df = pd.DataFrame({'close': close_vals})
#     # 计算EMA12、EMA26（注意adjust=False保持公式一致性）、DIF、DEA9（DIF的9日EMA）
#     # df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
#     # df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
#     # df['dif'] = df['ema12'] - df['ema26']
#     # df['dea9'] = df['dif'].ewm(span=9, adjust=False).mean()
#     # df['bar'] = df['dif'] - df['dea9']
#
#     if bottom:
#         bottom_candle = None
#         m1_dif, m2_dif, up_bar = [], [], 0
#         for i, c in enumerate(candles):
#             fast_period, slow_period, signal_period = 12, 26, 9
#             c.ema12 = c.close if i == 0 else (candles[i - 1].ema12*(fast_period-1)/(fast_period+1)+c.close*2/(fast_period+1))
#             c.ema26 = c.close if i == 0 else (candles[i - 1].ema26*(slow_period-1)/(slow_period+1)+c.close*2/(slow_period+1))
#             c.dea9 = c.close if i == 0 else (candles[i - 1].dea9*(signal_period-1)/(signal_period+1)+(c.ema12-c.ema26)*2/(signal_period+1))
#             c.dif = round(c.ema12 - c.ema26, 4)
#             c.bar = round(c.dif - c.dea9, 4)
#
#             if c.dif > 0:
#                 m1_dif, m2_dif, up_bar = [], [], 0
#             else:
#                 if up_bar == 0:
#                     if c.bar < 0:
#                         m1_dif.append(c)
#                     elif m1_dif:
#                         up_bar = up_bar + 1
#                 else:
#                     if c.bar > 0:
#                         if m2_dif:
#                             min_low1 = min(m1_dif, key=lambda ml: ml.low)
#                             min_dif1 = min(m1_dif, key=lambda md: md.dif)
#                             min_low2 = min(m2_dif, key=lambda ml: ml.low)
#                             min_dif2 = min(m2_dif, key=lambda md: md.dif)
#                             if min_low1.low < min_low2.low and min_dif1.dif > min_dif2.dif:
#                                 bottom_candle = min_low2
#                             m1_dif, m2_dif, up_bar = m2_dif, [], 0
#                         else:
#                             up_bar = up_bar + 1
#                     else:
#                         m2_dif.append(c)
#         return bottom_candle
#
#
# def macd(candles):
#     size = len(candles)
#     if size == 0:
#         return candles
#
#     close_vals = [round(c.close, 2) for c in candles]
#     df = pd.DataFrame({'close': close_vals})
#     df['ma5'] = df['close'].rolling(5).mean()  # MA5（至少1个点即可计算）
#     df['ma10'] = df['close'].rolling(10).mean()  # MA10（需满10个数据）
#     df['ma20'] = df['close'].rolling(20).mean()  # MA20（需满20个数据）
#
#     # 计算EMA12、EMA26（注意adjust=False保持公式一致性）
#     df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
#     df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
#     # 计算DIF
#     df['dif'] = df['ema12'] - df['ema26']
#     # 计算DEA9（DIF的9日EMA）
#     df['dea9'] = df['dif'].ewm(span=9, adjust=False).mean()
#     df['bar'] = df['dif'] - df['dea9']
#     for i, c in enumerate(candles):
#         c.ma5 = round(float(df['ma5'].iloc[i]), 4)
#         c.ma10 = round(float(df['ma10'].iloc[i]), 4)
#         c.ma20 = round(float(df['ma20'].iloc[i]), 4)
#         if i == 0:
#             c.ema12 = c.close
#             c.ema26 = c.close
#             c.dea9 = 0.0
#         else:
#             c.ema12 = round(candles[i-1].ema12 * 11 / 13 + c.close * 2 / 13, 4)
#             c.ema26 = round(candles[i - 1].ema26 * 25 / 27 + c.close * 2 / 27, 4)
#             c.dea9 = round(candles[i - 1].dea9 * 8 / 10 + (c.ema12 - c.ema26) * 2 / 10, 4)
#         c.mark = 1 if c.bar() > 0 else -1
#         c.mark2 = 1 if c.bar > 0 else -1
#
#     for i in range(2, size - 1):
#         c_2 = candles[i - 2]
#         c_1 = candles[i - 1]
#         c_0 = candles[i]
#         c_01 = candles[i + 1]
#         if c_2.mark == c_01.mark == c_1.mark == -1 and c_0.mark == 1:
#             c_0.mark = -1
#         if c_2.mark == c_01.mark == c_1.mark == 1 and c_0.mark == -1:
#             c_0.mark = 1
#
#     for i in range(2, size):
#         c_2 = candles[i - 2]
#         c_1 = candles[i - 1]
#         c_0 = candles[i]
#         if c_2.mark == c_0.mark == c_1.mark == -1:
#             if c_2.diff() > c_1.diff() < c_0.diff():
#                 c_1.mark = -3
#         if c_2.mark == c_0.mark == c_1.mark == 1:
#             if c_2.diff() < c_1.diff() > c_0.diff():
#                 c_1.mark = 3
#
#     i = 2
#     while i < size:
#         if abs(candles[i].mark) < 3:
#             i = i + 1
#             continue
#
#         if candles[i].mark == -3:
#             min_diff = candles[i].diff()
#             j = i + 1
#             while j < size:
#                 if candles[j].mark > 0:
#                     break
#                 if candles[j].mark == -3:
#                     if min_diff > candles[j].diff():
#                         candles[i].mark = -2
#                         min_diff = candles[j].diff()
#                         i = j
#                     else:
#                         candles[j].mark = -2
#                 j = j + 1
#             i = j
#
#         if i < size and candles[i].mark == 3:
#             max_diff = candles[i].diff()
#             j = i + 1
#             while j < size:
#                 if candles[j].mark < 0:
#                     break
#                 if candles[j].mark == 3:
#                     if max_diff < candles[j].diff():
#                         candles[i].mark = 2
#                         max_diff = candles[j].diff()
#                         i = j
#                     else:
#                         candles[j].mark = 2
#                 j = j + 1
#             i = j
#     return candles


if __name__ == '__main__':
    # db.connect()
    # db.create_tables([Candle])
    cd3 = Candle.latest('301389', 60)
    dt3 = datetime.strptime(cd3.dt, "%Y-%m-%d %H:%M:%S")
    # dt3 = datetime.strptime(cd3.dt, "%Y-%m-%d")
    print(cd3.dt, dt3.timestamp(), int(dt3.timestamp()*1000))
    print(datetime.fromtimestamp(1749950690081 / 1000).strftime("%Y-%m-%d %H:%M:%S"))
    # table_name = 'candle_60'

    # candle = Candle('300875', 101)
    # candle.fetch_and_save()
    # print(cd.code, cd.freq)
    # Candle.fetch_and_save('300875', 101)


