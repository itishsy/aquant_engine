from engines.engine import Searcher, job_engine
from models.candle import Candle
from models.symbol import Symbol
from models.choice import Choice
from models.review import Hot
import components.indicator as idt


@job_engine
class U20(Searcher):

    def search(self):
        chs = []
        symbols = Symbol.select()
        for sym in symbols:
            try:
                candles = Candle.find(sym.code, ma=True)
                if (len(candles) > 100 and
                        idt.beyond_ma(candles[-20:], 20, ma_ratio=0.9) and
                        idt.is_active(candles[-30:], up_size=1) and
                        not idt.top_divergence(candles) and
                        not idt.top_volume(candles, pre_ratio=0.7, nxt_ratio=0.9, limit=20) and
                        not idt.is_big_a(candles[-20:], down_ratio=0.5)):
                    cho = Choice()
                    cho.code = sym.code
                    cho.name = sym.name
                    cho.watcher = 'b15'
                    chs.append(cho)
            except Exception as e:
                print(e)
        return chs


@job_engine
class U10(Searcher):

    def search(self):
        chs = []
        symbols = Symbol.select()
        for sym in symbols:
            try:
                candles = Candle.find(sym.code, ma=True)
                if (len(candles) > 100 and
                        idt.is_red3(candles[-12:]) and
                        idt.is_active(candles[-20:], up_size=1) and
                        idt.beyond_ma(candles[-12:], 10, ma_ratio=0.9) and
                        not idt.top_volume(candles[-50:], pre_ratio=0.9, nxt_ratio=0.9, limit=15) and
                        not idt.top_divergence(candles)):
                    cho = Choice()
                    cho.code = sym.code
                    cho.name = sym.name
                    cho.searcher = 'u10'
                    cho.watcher = 'b5'
                    chs.append(cho)
            except Exception as e:
                print(e)
        return chs


@job_engine
class H10(Searcher):

    def search(self):
        chs = []
        codes = Hot.find_hot_codes(35)
        symbols = Symbol.select()
        for sym in symbols:
            try:
                if sym.code not in codes:
                    continue
                candles = Candle.find(sym.code, ma=True)
                if (len(candles) > 100 and
                        idt.beyond_ma(candles[-20:], 60, ma_ratio=0.8) and
                        not idt.top_divergence(candles)):
                    cho = Choice()
                    cho.code = sym.code
                    cho.name = sym.name
                    cho.watcher = 'b15'
                    chs.append(cho)
                if (len(candles) > 100 and
                        idt.beyond_ma(candles[-20:], 20, ma_ratio=0.8) and
                        not idt.top_divergence(candles)):
                    cho = Choice()
                    cho.code = sym.code
                    cho.name = sym.name
                    cho.watcher = 'b5'
                    chs.append(cho)
            except Exception as e:
                print(e)
        return chs


@job_engine
class U60(Searcher):

    def search(self):
        chs = []
        symbols = Symbol.select()
        for sym in symbols:
            try:
                candles = Candle.find(sym.code, ma=True)
                # 在ma60线之上\活跃度不足\日級別顶背离\高位放量\大A形态
                if (len(candles) > 100 and
                        idt.is_active(candles[-50:], up_size=2, down_size=1) and
                        idt.beyond_ma(candles[-50:], 60, ma_ratio=0.85) and
                        not idt.top_divergence(candles)):
                    cho = Choice()
                    cho.code = sym.code
                    cho.name = sym.name
                    cho.watcher = 'b30'
                    chs.append(cho)
            except Exception as e:
                print(e)
        return chs

