from candles.candle import Candle
from models.signal import Signal, SIGNAL_TYPE
from typing import List
import signals.utils as utl
from signals.signaler import Signaler


class Divergence(Signaler):

    def search(self, candles: List[Candle]) -> List[Signal]:
        signals = []
        tbs = utl.get_top_bottom(candles)
        size = len(tbs)
        for i in range(2, size):
            c_2 = tbs[i - 2]
            c_1 = tbs[i - 1]
            c_0 = tbs[i]
            if c_2.mark == 3 and c_1.mark == -3 and c_0.mark == 3 and c_2.diff() > 0 and c_1.diff() > 0 and c_0.diff() > 0:
                is_cross = True
                if i + 1 == size:
                    cs = utl.get_section(candles, c_0.dt, candles[-1])
                    if utl.has_cross(cs) != -1:
                        is_cross = False
                if is_cross:
                    up_stage1 = utl.get_stage(candles, c_2.dt)
                    up_stage2 = utl.get_stage(candles, c_0.dt)
                    high2 = utl.get_highest(up_stage1).high
                    high0 = utl.get_highest(up_stage2).high
                    if c_2.diff() > c_0.diff() and high2 < high0:
                        signals.append(
                            Signal(freq=c_0.freq, dt=c_0.dt, price=c_0.high, type=SIGNAL_TYPE.TOP_DIVERGENCE))
            elif c_2.mark == -3 and c_1.mark == 3 and c_0.mark == -3 and c_2.diff() < 0 and c_1.diff() < 0 and c_0.diff() < 0:
                is_cross = True
                if i + 1 == size:
                    cs = utl.get_section(candles, c_0.dt, candles[-1].dt)
                    if utl.has_cross(cs) != 1:
                        is_cross = False
                if is_cross:
                    down_stage1 = utl.get_stage(candles, c_2.dt)
                    down_stage2 = utl.get_stage(candles, c_0.dt)
                    if utl.has_trend(down_stage1) > -2 and utl.has_trend(down_stage2) > -2:
                        low1 = utl.get_lowest(down_stage1)
                        low2 = utl.get_lowest(down_stage2)
                        lowest = utl.get_lowest(utl.get_section(candles, low1.dt))
                        if c_2.diff() < c_0.diff() and low1.low > low2.low == lowest.low:
                            signals.append(
                                Signal(freq=c_0.freq, dt=low2.dt, price=low2.low, type=SIGNAL_TYPE.BOTTOM_DIVERGENCE))
        return signals

    def analyze(self, sig: Signal) -> Signal:
        return sig


def diver_top(candles: List[Candle]) -> List[Signal]:
    """
    顶背离
    :param candles:
    :return:
    """
    signals = []
    tbs = utl.get_top_bottom(candles)
    size = len(tbs)
    for i in range(2, size):
        c_2 = tbs[i - 2]
        c_1 = tbs[i - 1]
        c_0 = tbs[i]
        if c_2.mark == 3 and c_1.mark == -3 and c_0.mark == 3 and c_2.diff() > 0 and c_1.diff() > 0 and c_0.diff() > 0:
            is_cross = True
            if i + 1 == size:
                cs = utl.get_section(candles, c_0.dt, candles[-1])
                if utl.has_cross(cs) != -1:
                    is_cross = False
            if is_cross:
                up_stage1 = utl.get_stage(candles, c_2.dt)
                up_stage2 = utl.get_stage(candles, c_0.dt)
                high2 = utl.get_highest(up_stage1).high
                high0 = utl.get_highest(up_stage2).high
                if c_2.diff() > c_0.diff() and high2 < high0:
                    signals.append(
                        Signal(freq=c_0.freq, dt=c_0.dt, price=c_0.high, type=SIGNAL_TYPE.TOP_DIVERGENCE))
    return signals


def diver_bottom(candles: List[Candle]) -> List[Signal]:
    """
    底背离
    :param candles:
    :return: 返回形成底背离的最底那一根
    """
    signals = []
    tbs = utl.get_top_bottom(candles)
    size = len(tbs)
    for i in range(2, size):
        c_2 = tbs[i - 2]
        c_1 = tbs[i - 1]
        c_0 = tbs[i]
        if c_2.mark == -3 and c_1.mark == 3 and c_0.mark == -3 and c_2.diff() < 0 and c_1.diff() < 0 and c_0.diff() < 0:
            is_cross = True
            if i + 1 == size:
                cs = utl.get_section(candles, c_0.dt, candles[-1].dt)
                if utl.has_cross(cs) != 1:
                    is_cross = False
            if is_cross:
                down_stage1 = utl.get_stage(candles, c_2.dt)
                down_stage2 = utl.get_stage(candles, c_0.dt)
                if utl.has_trend(down_stage1) > -2 and utl.has_trend(down_stage2) > -2:
                    low1 = utl.get_lowest(down_stage1)
                    low2 = utl.get_lowest(down_stage2)
                    sect = utl.get_section(candles, low1.dt, low2.dt)
                    lowest = utl.get_lowest(utl.get_section(candles, low1.dt))
                    if c_2.diff() < c_0.diff() and low1.low > low2.low == lowest.low and len(sect) > 7:
                        signals.append(
                            Signal(freq=c_0.freq, dt=low2.dt, price=low2.low, type=SIGNAL_TYPE.BOTTOM_DIVERGENCE))
    return signals


def driver_bottom_plus(sig, cds):
    sec = utl.get_section(cds, sig.dt)
    sec_lowest = utl.get_lowest(sec)
    if sec_lowest.dt == sig.dt:
        tbs = utl.get_top_bottom(cds)
        if tbs[-1].dt == sig.dt:
            sec_lowest2 = tbs[-3]
        else:
            sec_lowest2 = tbs[-4]
        if (sec_lowest.diff() / sec_lowest2.diff()) < 0.8:
            return sig


def shape_top(candles: List[Candle]) -> List[Signal]:
    """
    顶分型
    :param candles: stage candles
    :return:
    """
    signals = []
    highest = utl.get_highest()
    size = len(candles)
    for i in range(1, size):
        if candles[i].dt == highest.dt:
            if i + 1 < size:
                top = candles[i]
                l1 = candles[i - 1]
                r1 = candles[i + 1]
                if l1.high < top.high < r1.high and l1.low < top.low < r1.low:
                    signals.append(Signal(dt=top.dt, freq=top.freq, type='shape_top', value=top.mark))
            break
    return signals


def shape_bottom(candles: List[Candle]) -> List[Signal]:
    """
    底分型
    :param candles:
    :return:
    """
    signals = []
    lowest = utl.get_lowest()
    size = len(candles)
    for i in range(1, size):
        if candles[i].dt == lowest.dt:
            if i + 1 < size:
                bot = candles[i]
                l1 = candles[i - 1]
                r1 = candles[i + 1]
                if l1.low > bot.low > r1.low and l1.high > bot.high > r1.high:
                    signals.append(Signal(dt=bot.dt, freq=bot.freq, type='shape_bottom', value=bot.mark))
            break
    return signals


if __name__ == '__main__':
    Divergence().start()
