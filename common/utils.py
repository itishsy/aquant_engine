from datetime import datetime


def dt_format(dt, fm='%Y-%m-%d'):
    try:
        if dt.find(':') > 0:
            sdt = datetime.strptime(dt, '%Y-%m-%d %H:%M')
        else:
            sdt = datetime.strptime(dt, '%Y-%m-%d')
        return sdt.strftime(fm)
    except:
        return dt


def now_ymd():
    now = datetime.now()
    ymd = datetime(year=now.year, month=now.month, day=now.day)
    return ymd


def now_ymd_str():
    ymd = now_ymd()
    return ymd.strftime('%Y-%m-%d')


def now_val():
    now = datetime.now()
    hm = now.hour * 100 + now.minute
    return hm


def is_trade_day():
    now = datetime.now()
    return now.weekday() < 5


def is_trade_time():
    return is_trade_day() and 930 < now_val() < 1510
