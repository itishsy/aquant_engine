from candles.candle import Candle
from typing import List


def get_top_bottom(candles: List[Candle]):
    """
    获取diff的顶和底
    :param candles:
    :return:
    """
    tbc = []
    for cd in candles:
        if cd.mark is None:
            return tbc
        if abs(cd.mark) == 3:
            tbc.append(cd)
    return tbc


def get_lowest_bottom(tbc: List[Candle], idx):
    if abs(idx) > len(tbc):
        return
    elif tbc[idx].mark == -3 and tbc[idx].dea9 < 0:
        return tbc[idx]
    else:
        idx = idx - 1
        return get_lowest_bottom(tbc, idx)


def get_next_top(candles: List[Candle], dt):
    flag = False
    for cd in candles:
        if cd.mark is None:
            return None
        if cd.dt == dt:
            flag = True
        if flag and cd.mark == 3:
            return cd
    return None


def get_next_bottom(candles: List[Candle], dt):
    flag = False
    for cd in candles:
        if cd.mark is None:
            return None
        if cd.dt == dt:
            flag = True
        if flag and cd.mark == -3:
            return cd
    return None


def get_lowest(candles: List[Candle]):
    """
    集合同取最低的那一根
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


def get_highest(candles: List[Candle]):
    """
    集合同取最高的那一根
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


def get_highest_volume(candles: List[Candle]):
    """
    集合同取最高的那一根
    :param candles:
    :return: 最高点的一根
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


def get_average_volume(candles: List[Candle]):
    """
    集合同取最高的那一根
    :param candles:
    :return: 最高点的一根
    """
    size = len(candles)
    if candles is None or size == 0:
        return None

    s = 0
    for c in candles:
        s = s + c.volume

    return s/size


def is_upper_shadow(candle: Candle):
    """
    长上影线
    """
    if candle.open > candle.close:
        if (candle.high - candle.open) / (candle.high - candle.low) > 0.4:
            return True
    else:
        if (candle.high - candle.close) / (candle.high - candle.low) > 0.6:
            return True
    return False


def get_highest_close(candles: List[Candle]):
    """
    集合同取最高的那一根
    :param candles:
    :return: 最高点的一根
    """
    if candles is None or len(candles) == 0:
        return None
    highest = candles[0]
    i = 1
    while i < len(candles):
        if candles[i].close > highest.close:
            highest = candles[i]
        i = i + 1
    return highest


def get_candle(candles: List[Candle], dt):
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


def get_stage(candles: List[Candle], dt) -> List[Candle]:
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


def get_section(candles: List[Candle], sdt, edt=None):
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


def get_between(candles: List[Candle], dt, left, length):
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


def get_cross(candles: List[Candle]):
    """ 获取形成交叉的Candle
    -1 为下叉
    1 为上叉
    """
    cs = []
    if candles is None:
        return cs
    i = len(candles) - 1
    while i > 1:
        if candles[i].mark == 1 and candles[i-1].mark == -1:
            cs.append(candles[i])
        elif candles[i].mark == -1 and candles[i-1].mark == 1:
            cs.append(candles[i])
        i = i - 1
    return cs


def contains(candles: List[Candle], dt):
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


def has_trend(candles: List[Candle]):
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


def has_cross(candles: List[Candle]):
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


def get_dabrc(candles: List[Candle], b3_dt):
    """
    底部形态5段
    :param candles: 存在背离的
    :param b3_dt: 背离时间
    :return: 高低位五段
    """
    d, a, b, r, c = None, None, None, None, None

    if candles is None:
        return d, a, b, r, c

    d3_dt, a3_dt, r3_dt, c3_dt = None, None, None, None

    m3 = [x for x in candles if abs(x.mark) == 3]

    i = len(m3) - 1
    while i > 1:
        if m3[i].dt == b3_dt:
            if i + 1 < len(m3):
                r_s = get_stage(candles, m3[i + 1].dt)
                r3_dt = get_highest(r_s).dt
                if i + 2 < len(m3):
                    c_s = get_stage(candles, m3[i + 2].dt)
                    c3_dt = get_lowest(c_s).dt
                else:
                    c3_dt = candles[-1].dt
            if i - 1 > 0:
                a_s = get_stage(candles, m3[i - 1].dt)
                a3_dt = get_highest(a_s).dt
            if i - 2 > 0:
                d_s = get_stage(candles, m3[i - 2].dt)
                d3_dt = get_lowest(d_s).dt
                d = get_section(candles, d_s[0].dt, d3_dt)
            break
        i = i - 1

    if d3_dt is None or a3_dt is None or b3_dt is None:
        return None, None, None, None, None

    a = get_section(candles, d3_dt, a3_dt)
    b = get_section(candles, a3_dt, b3_dt)
    r = get_section(candles, b3_dt, r3_dt)
    if c3_dt is not None:
        c = get_section(candles, r3_dt, c3_dt)
    return d, a, b, r, c


def average(candles: List[Candle]):
    size = len(candles)
    total = 0
    for c in candles:
        total = total + (c.open + c.close) / 2
    return total / size

# if __name__ == '__main__':
#     cds = fetch_data('300002', 5, '20230517')
#     cds = mark(cds)
#     sis = diver_bottom(cds)
#     for si in sis:
#         print(si.dt)
# for cd in cds:
#     print(cd)
