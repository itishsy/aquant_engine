from engines.engine import Watcher, job_engine
from models.candle import Candle
from models.signal import Signal
from components.indicator import bottom_divergence
from datetime import datetime, timedelta


@job_engine
class B5(Watcher):

    def watch(self, code):
        self.cf.fetch_candles(code, 5)
        candles = Candle.find(code, freq=5)
        cd = bottom_divergence(candles)
        if cd and cd is not None and get_dtime(cd.dt) > (datetime.now() - timedelta(days=get_days(1))):
            print(f'signal： code={cd.code}, dt={cd.dt}, freq={cd.freq}')
            return Signal(freq=5, dt=cd.dt, price=cd.low, type=0)


@job_engine
class B15(Watcher):

    def watch(self, code):
        self.cf.fetch_candles(code, 15)
        candles = Candle.find(code, freq=15)
        cd = bottom_divergence(candles)
        if cd and cd is not None and get_dtime(cd.dt) > (datetime.now() - timedelta(days=get_days(3))):
            print(f'signal： code={cd.code}, dt={cd.dt}, freq={cd.freq}')
            return Signal(freq=15, dt=cd.dt, price=cd.low, type=0)


@job_engine
class B30(Watcher):

    def watch(self, code):
        self.cf.fetch_candles(code, 30)
        candles = Candle.find(code, freq=30)
        cd = bottom_divergence(candles)
        if cd and cd is not None and get_dtime(cd.dt) > (datetime.now() - timedelta(days=get_days(6))):
            candles2 = Candle.find(code, freq=5)
            cd2 = bottom_divergence(candles2)
            if cd2 and cd2 is not None and cd2.dt > cd.dt and cd2.low > cd.low:
                print(f'signal： code={cd.code}, dt={cd2.dt}, freq={cd.freq}')
                return Signal(freq=30, dt=cd2.dt, price=cd2.low, type=0)


def get_dtime(dt):
    if len(dt) == 16:
        return datetime.strptime(dt, '%Y-%m-%d %H:%M')
    elif len(dt) == 19:
        return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    else:
        return datetime.strptime(dt, '%Y-%m-%d')


def get_days(days):
    if datetime.now().weekday() >= 5:
        days = days + datetime.now().weekday() - 4
    return days
