import pandas as pd


def macd(candles, fast_period=12, slow_period=26, signal_period=9):
    closes = pd.Series([candle.close for candle in candles])
    # 计算双EMA
    ema_fast = closes.ewm(span=fast_period, min_periods=fast_period, adjust=False).mean()
    ema_slow = closes.ewm(span=slow_period, min_periods=slow_period, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal_period, min_periods=signal_period, adjust=False).mean()
    bar = 2 * (dif - dea)
    for i, c in enumerate(candles):
        c.dif = round(float(dif[i]), 4)
        c.dea = round(float(dea[i]), 4)
        c.bar = round(float(bar[i]), 4)
    # for i, c in enumerate(candles):
    #     c.ema12 = c.close if i == 0 else (
    #                 candles[i - 1].ema12 * (fast_period - 1) / (fast_period + 1) + c.close * 2 / (fast_period + 1))
    #     c.ema26 = c.close if i == 0 else (
    #                 candles[i - 1].ema26 * (slow_period - 1) / (slow_period + 1) + c.close * 2 / (slow_period + 1))
    #     c.dea9 = c.close if i == 0 else (
    #                 candles[i - 1].dea9 * (signal_period - 1) / (signal_period + 1) + (c.ema12 - c.ema26) * 2 / (
    #                     signal_period + 1))
    #     c.dif = round(c.ema12 - c.ema26, 4)
    #     c.bar = round(c.dif - c.dea9, 4)
    return candles


# 底背离
def bottom_divergence(candles):
    cds = macd(candles)
    bottom_candle = None
    m1_dif, m2_dif, up_bar = [], [], []
    for i, c in enumerate(cds):
        if c.dif > 0 or c.dea > 0:
            m1_dif, m2_dif, up_bar = [], [], []
        else:
            if not up_bar:
                if c.bar < 0:
                    m1_dif.append(c)
                elif m1_dif:
                    up_bar.append(c)
                else:
                    m1_dif, m2_dif, up_bar = [], [], []
            else:
                if c.bar > 0:
                    if m2_dif and up_bar:
                        min_low1 = min(m1_dif, key=lambda ml: ml.low)
                        min_dif1 = min(m1_dif, key=lambda md: md.dif)
                        min_low2 = min(m2_dif, key=lambda ml: ml.low)
                        min_dif2 = min(m2_dif, key=lambda md: md.dif)
                        min_bar = min(up_bar, key=lambda md: md.low)
                        if (min_bar.low > min_low1.low > min_low2.low and
                                min_dif1.dif < min_dif2.dif):
                            bottom_candle = min_low2
                        m1_dif, m2_dif, up_bar = m2_dif, [], []
                    else:
                        up_bar.append(c)
                else:
                    m2_dif.append(c)
    if bottom_candle is not None:
        sec = CandlesUtil.get_section(candles, bottom_candle.dt)
        lowest = CandlesUtil.get_lowest(sec)
        if lowest.low < bottom_candle.low:
            bottom_candle = None
    return bottom_candle


# 顶背离
def top_divergence(candles):
    cds = macd(candles)
    top_candle = None
    m1_dif, m2_dif, down_bar = [], [], 0
    for i, c in enumerate(cds):
        if c.dif < 0 or c.dea < 0:
            m1_dif, m2_dif, down_bar = [], [], 0
        else:
            if down_bar == 0:
                if c.bar > 0:
                    m1_dif.append(c)
                elif m1_dif:
                    down_bar = down_bar + 1
                else:
                    m1_dif, m2_dif, up_bar = [], [], []
            else:
                if c.bar < 0:
                    if m2_dif:
                        max_high1 = max(m1_dif, key=lambda ml: ml.high)
                        max_dif1 = max(m1_dif, key=lambda md: md.dif)
                        max_high2 = max(m2_dif, key=lambda ml: ml.high)
                        max_dif2 = max(m2_dif, key=lambda md: md.dif)
                        if max_high1.high < max_high2.high and max_dif1.dif > max_dif2.dif:
                            top_candle = max_dif2
                        m1_dif, m2_dif, down_bar = m2_dif, [], 0
                    else:
                        down_bar = down_bar + 1
                else:
                    m2_dif.append(c)
    return top_candle


# 高位放量
def top_volume(candles, pre_ratio=0.8, nxt_ratio=0.9, limit=20):
    highest = CandlesUtil.get_highest(candles)
    if highest.dt == candles[-1].dt:
        return False
    v_highest = CandlesUtil.get_highest_volume(candles)
    hdt = None
    if highest.dt == v_highest.dt:
        c_size = len(candles)
        idx = 0
        for c in candles:
            if (0 < idx < (c_size-1) and
                    highest.dt == c.dt and
                    candles[idx - 1].volume / c.volume <= pre_ratio and
                    candles[idx + 1].volume / c.volume <= nxt_ratio):
                hdt = highest.dt
            idx = idx + 1
    if hdt and len(CandlesUtil.get_section(candles, hdt)) <= limit:
        return highest


# 是否活跃的
def is_active(candles, up_size=1, down_size=0):
    zf = 0.19 if candles[0].code.startswith('3') else 0.09
    df = 0.1 if candles[0].code.startswith('3') else 0.06
    zt_counter = 0  # 大涨
    dt_counter = 0  # 大跌
    close = 0
    for c in candles:
        if c.close > close > 0 and (c.close - close) / close >= zf:
            zt_counter = zt_counter + 1
        if down_size > 0:
            if close > 0 and c.close < close and (close - c.close) / c.close >= df:
                dt_counter = dt_counter + 1
        close = c.close
    if zt_counter >= up_size and (down_size == 0 or dt_counter >= down_size):
        return True
    return False


# 在ma线之上
def beyond_ma(candles, ma, ma_ratio=1, above=True):
    beyond_ma_counter = 0
    for c in candles:
        ma_val = eval('c.ma' + str(ma))
        if above:
            if c.close > ma_val:
                beyond_ma_counter = beyond_ma_counter + 1
        else:
            if c.close < ma_val:
                beyond_ma_counter = beyond_ma_counter + 1
    if beyond_ma_counter/len(candles) >= ma_ratio:
        return True
    return False


# 是否存在红三兵
def is_red3(candles):
    size = len(candles)
    for i in range(1, size-2):
        cd1 = candles[i - 1]
        cd2 = candles[i]
        cd3 = candles[i + 1]
        if (cd1.open < cd1.close < cd2.open < cd2.close < cd3.open < cd3.close
                and cd1.high < cd2.high < cd3.high
                and (cd2.close / cd1.close) > 0.01
                and (cd3.close / cd2.close) > 0.01
                and cd1.low < cd2.low < cd3.low):
            return True
    return False


# 是否在0軸线之上
def is_beyond_x(candles, x_ratio=0.9):
    beyond_x_counter = 0
    for c in candles:
        if c.dea9 > 0:
            beyond_x_counter = beyond_x_counter + 1
    if beyond_x_counter / len(candles) >= x_ratio:
        return True
    return False


# 是否大A形态
def is_big_a(candles, down_ratio=0.618):
    highest = CandlesUtil.get_highest(candles)
    lowest = CandlesUtil.get_lowest(candles)
    lower_sec = CandlesUtil.get_section(candles, highest.dt)
    if len(lower_sec) < len(candles)/2:
        lower = CandlesUtil.get_lowest(lower_sec)
        if (highest.high - lower.low) / (highest.high - lowest.low) >= down_ratio:
            return True
    return False


def cal_limit(freq, day):
    return day*240/freq


class CandlesUtil:

    @staticmethod
    def get_top_bottom(candles):
        """
        获取diff的顶和底
        :param candles:
        :return: 所有顶底集合
        """
        tbc = []
        for cd in candles:
            if cd.mark is None:
                return tbc
            if abs(cd.mark) == 3:
                tbc.append(cd)
        return tbc

    @staticmethod
    def get_lowest(candles):
        """
        取最低的那一根
        :param candles:
        :return: 最低的一根
        """
        if candles is None or len(candles) == 0:
            return None
        lowest = candles[0]
        i = 1
        while i < len(candles):
            if candles[i].low < lowest.low:
                lowest = candles[i]
            i = i + 1
        return lowest

    @staticmethod
    def get_highest(candles):
        """
        取最高的那一根
        :param candles:
        :return: 最高点的一根
        """
        if candles is None or len(candles) == 0:
            return None
        highest = candles[0]
        i = 1
        while i < len(candles):
            if candles[i].high > highest.high:
                highest = candles[i]
            i = i + 1
        return highest

    @staticmethod
    def get_highest_volume(candles):
        """
        集合同取最高成交量的那一根
        :param candles:
        :return: 最高成交量的一根
        """
        if candles is None or len(candles) == 0:
            return None
        highest = candles[0]
        i = 1
        while i < len(candles):
            if candles[i].volume > highest.volume:
                highest = candles[i]
            i = i + 1
        return highest

    @staticmethod
    def get_average_volume(candles):
        """
        集合平均量
        :param candles:
        :return: 平均值
        """
        size = len(candles)
        if candles is None or size == 0:
            return None

        s = 0
        for c in candles:
            s = s + c.volume

        return round(s / size, 2)

    @staticmethod
    def get_candle(candles, dt):
        """
        集合中获取一根candle
        :param candles:
        :param dt: 按时间定位
        :return: candle
        """
        i = 0
        while i < len(candles):
            if candles[i].dt == dt:
                return candles[i]
            i = i + 1
        return None

    @staticmethod
    def get_stage(candles, dt):
        """
        获取同向相邻的candle集合
        :param candles:
        :param dt: 定位时间
        :return: 与定位时间bar同向相临的candle集合
        """
        i = 0
        if candles is None:
            return []
        s = len(candles)
        stage = []
        while i < s:
            if candles[i].dt == dt:
                stage.append(candles[i])
                j = i - 1
                k = i + 1
                while j > 0:
                    if (candles[j].mark > 0) == (candles[i].mark > 0):
                        stage.insert(0, candles[j])
                    else:
                        break
                    j = j - 1
                while k < s:
                    if candles[k].mark is None:
                        return []
                    if (candles[k].mark > 0) == (candles[i].mark > 0):
                        stage.append(candles[k])
                    else:
                        break
                    k = k + 1
                break
            i = i + 1
        return stage

    @staticmethod
    def get_section(candles, sdt, edt=None):
        """
        获取起始区间的部分
        :param candles:
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: candle集合，包含起止两根
        """
        cs = []
        if candles is None:
            return cs
        flag = False
        for c in candles:
            if c.dt == sdt:
                flag = True
            if flag:
                cs.append(c)
            if c.dt == edt:
                break
        return cs

    @staticmethod
    def get_between(candles, dt, left, length):
        """
        指定日期所在左右集合
        :param candles:
        :param dt: 时间
        :param left: 左边
        :param length: 集合长度
        :return: candle集合，包含起止两根
        """
        cs = []
        if candles is None:
            return cs
        s = len(candles)
        i = 0
        sti = -1
        while i < s:
            if candles[i].dt == dt:
                sti = i
                break
            i = i + 1

        if sti > 0:
            j = 0
            while j < s:
                if j >= sti and len(cs) <= length:
                    cs.append(candles[i])
                j = j + 1
        return cs

    @staticmethod
    def get_cross(candles):
        """ 获取形成交叉的Candle
        -1 为下叉
        1 为上叉
        """
        cs = []
        if candles is None:
            return cs
        i = len(candles) - 1
        while i > 1:
            if candles[i].mark == 1 and candles[i - 1].mark == -1:
                cs.append(candles[i])
            elif candles[i].mark == -1 and candles[i - 1].mark == 1:
                cs.append(candles[i])
            i = i - 1
        return cs

    @staticmethod
    def contains(candles, dt):
        """
        是否包含
        :param candles:
        :param dt:
        :return:
        """
        for c in candles:
            if c.dt == dt:
                return True
        return False

    @staticmethod
    def has_trend(candles):
        """
        是否包含有趋势
        :param candles:
        :return: -1 存在向下趋势，1 存在向上趋势，0 不存在趋势
        """
        if candles is None or len(candles) < 3:
            return -2
        i = 2
        while i < len(candles):
            if candles[i - 2].bar() > candles[i - 1].bar() > candles[i].bar():
                return -1
            if candles[i - 2].bar() < candles[i - 1].bar() < candles[i].bar():
                return 1
            i = i + 1
        return 0

    @staticmethod
    def has_cross(candles):
        """
        是否包含快慢线交叉
        :param candles:
        :return: 1 上叉 -1 下叉 0 无或同时存在
        """
        if candles is None:
            return 0
        u_flag, d_flag = False, False
        i = 1
        while i < len(candles):
            if candles[i - 1].bar() < 0 < candles[i].bar():
                u_flag = True
            if candles[i - 1].bar() > 0 > candles[i].bar():
                d_flag = True
            if u_flag and d_flag:
                return 0
            i = i + 1
        if u_flag:
            return 1
        if d_flag:
            return -1
        return 0
